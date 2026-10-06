# broharness — request flow (v2, scenario-by-scenario)

Same idea as v1, broken into smaller scenarios per your request, each
covering every real branch in that part of the flow as exhaustively as
possible. `Fail Recovery` is now included — it's load-bearing in practice,
not an edge case (it fired in nearly every real test run this session).

**`Guard Rail` is still a proposed addition, not yet implemented** in
`src/broharness/flows/`. Everything else below is read directly from the
current source (`skill_call.py`, `tool_call.py`, `tool_use.py`,
`answer.py`, `fail_recovery.py`).

Every diagram declares the same participants, in the same order:
`User`, `Guard Rail`, `Skill Call`, `Tool Call`, `Tool Use`, `Answer`,
`Fail Recovery` — even where a scenario doesn't exercise all of them, for
easy side-by-side comparison.

## Scenario 1 — request vs. Guard Rail

```mermaid
sequenceDiagram
    actor User
    participant GuardRail as Guard Rail
    participant SkillCall as Skill Call
    participant ToolCall as Tool Call
    participant ToolUse as Tool Use
    participant Answer
    participant FailRecovery as Fail Recovery

    User->>GuardRail: submit request (+ chat history)

    alt request fails the guardrail check
        GuardRail-->>User: reject
    else request passes
        GuardRail->>SkillCall: forward request
    end
```

## Scenario 2 — Skill Call

```mermaid
sequenceDiagram
    actor User
    participant GuardRail as Guard Rail
    participant SkillCall as Skill Call
    participant ToolCall as Tool Call
    participant ToolUse as Tool Use
    participant Answer
    participant FailRecovery as Fail Recovery

    GuardRail->>SkillCall: forward request
    SkillCall->>SkillCall: decide -- match a skill? ask? or none?

    alt response isn't valid JSON, but reads like a question
        SkillCall->>ToolUse: ask_user_question
        ToolUse->>User: ask the question
        User-->>ToolUse: answer
        ToolUse->>SkillCall: resume -- re-decide with the answer

    else response isn't valid JSON, and isn't a question either
        SkillCall->>FailRecovery: malformed response
        alt retries remaining
            FailRecovery->>SkillCall: retry
        else retries exhausted
            FailRecovery->>Answer: give up, answer anyway
        end

    else valid response -- no skill matches at all
        SkillCall->>Answer: forward directly -- no skill needed

    else valid response -- same request already satisfied
        SkillCall->>Answer: nothing new to do -- answer with what's already loaded

    else valid response -- intent is ambiguous, model asks
        SkillCall->>ToolUse: ask_user_question
        ToolUse->>User: ask the question
        User-->>ToolUse: answer
        ToolUse->>ToolCall: resume
        note over ToolUse,ToolCall: resumes via Tool Call, not back at Skill Call --<br/>the success path always sets the resume point<br/>to Tool Call, even when the chosen action<br/>was ask_user_question, not load_skill

    else valid response -- picks a real, existing skill
        SkillCall->>ToolUse: load_skill(name)
        ToolUse->>ToolUse: load its instructions,<br/>auto-register its scripts
        ToolUse->>ToolCall: loaded -- proceed

    else valid response -- picks a skill name that doesn't exist
        SkillCall->>ToolUse: load_skill(name)
        ToolUse->>FailRecovery: "not a real skill" error
        alt retries remaining
            FailRecovery->>ToolCall: retry -- resumes via Tool Call,<br/>since that was already the planned<br/>next step for this attempt
        else retries exhausted
            FailRecovery->>Answer: give up, answer anyway
        end
    end
```

**Worth knowing:** the "intent is ambiguous, model asks" branch and the
"picks a skill name that doesn't exist" branch both resume via `Tool Call`
after recovering, not back at `Skill Call`. That's correct for the second
case (loading was already the planned next step), but the first case means
a clarification the model asked *to help pick a skill* gets answered inside
`Tool Call`'s context, not re-run through `Skill Call`'s own matching logic
— a real asymmetry in the current code, not a diagramming simplification.

## Scenario 3 — Tool Call ↔ Tool Use

```mermaid
sequenceDiagram
    actor User
    participant GuardRail as Guard Rail
    participant SkillCall as Skill Call
    participant ToolCall as Tool Call
    participant ToolUse as Tool Use
    participant Answer
    participant FailRecovery as Fail Recovery

    SkillCall->>ToolCall: skill loaded -- proceed
    ToolCall->>ToolCall: decide which tool(s) to call, if any

    alt response isn't valid JSON, but reads like a question
        ToolCall->>ToolUse: ask_user_question
        ToolUse->>User: ask the question
        User-->>ToolUse: answer
        ToolUse->>ToolCall: resume -- decide again

    else response isn't valid JSON, and isn't a question either
        ToolCall->>FailRecovery: malformed response
        alt retries remaining
            FailRecovery->>ToolCall: retry
        else retries exhausted
            FailRecovery->>Answer: give up, answer anyway
        end

    else valid response -- nothing more needed
        ToolCall->>Answer: done -- forward result(s)

    else valid response -- repeats something already done
        ToolCall->>Answer: nothing new to do -- answer with what's already fetched

    else valid response -- one or more actions queued
        loop for each queued action, in order
            alt action is ask_user_question
                ToolCall->>ToolUse: ask_user_question
                ToolUse->>User: ask the question
                User-->>ToolUse: answer
                ToolUse->>ToolCall: resume -- decide again
                note over ToolCall: stops processing the rest of this<br/>batch early -- the loop restarts fresh

            else action is load_skill_extension
                ToolCall->>ToolUse: load_skill_extension(skill, path)
                alt skill was never loaded this conversation
                    ToolUse->>FailRecovery: "not a loaded skill" error
                    alt retries remaining
                        FailRecovery->>ToolCall: retry
                    else retries exhausted
                        FailRecovery->>Answer: give up, answer anyway
                    end
                else skill is loaded -- fetch succeeds
                    ToolUse->>ToolUse: record the reference content
                end

            else action is a registered script
                ToolCall->>ToolUse: run the script (subprocess)
                alt script runs cleanly
                    ToolUse->>ToolUse: record its output
                else script fails, or isn't registered
                    ToolUse->>FailRecovery: error (exit code, or<br/>"not registered -- call load_tool first")
                    alt retries remaining
                        FailRecovery->>ToolCall: retry
                    else retries exhausted
                        FailRecovery->>Answer: give up, answer anyway
                    end
                end
            end
        end
        ToolUse->>ToolCall: batch done, no failures -- decide again
    end
```

**Not drawn separately, to keep this readable:** `load_skill` (re-loading
a different skill mid-batch) and `load_tool` (the rare manual-registration
fallback, superseded by auto-registration) can also appear in a queued
batch. Both follow the same two-way shape as the branches above — success
continues the batch, failure reports to `Fail Recovery` with the same
bounded-retry/give-up pattern.

## Scenario 4 — Tool Call done → Answer

```mermaid
sequenceDiagram
    actor User
    participant GuardRail as Guard Rail
    participant SkillCall as Skill Call
    participant ToolCall as Tool Call
    participant ToolUse as Tool Use
    participant Answer
    participant FailRecovery as Fail Recovery

    ToolCall->>Answer: forward result(s) / no more tools needed

    alt grounded in real tool result(s)
        Answer->>Answer: write the final answer from what was actually fetched
        Answer-->>User: final response

    else no tool result -- genuine general-knowledge question
        Answer->>Answer: answer directly from general knowledge
        Answer-->>User: final response

    else no tool result -- something project-specific was needed<br/>and never fetched (Fail Recovery gave up earlier)
        Answer->>Answer: say plainly it couldn't be checked --<br/>never invent a plausible-sounding answer
        Answer-->>User: honest "can't check that" response

    else Answer itself needs to ask something
        Answer->>ToolUse: ask_user_question
        ToolUse->>User: ask the question
        User-->>ToolUse: answer
        ToolUse->>Answer: resume -- write the real final answer now

    else Answer's own call fails
        Answer->>FailRecovery: error
        alt retries remaining
            FailRecovery->>Answer: retry
        else retries exhausted
            note over FailRecovery,User: special case -- Answer is what kept failing, so Fail<br/>Recovery does not route back to Answer again (that<br/>would loop forever). It messages the user directly.
            FailRecovery-->>User: "sorry, I ran into a problem" fallback message
        end
    end
```
