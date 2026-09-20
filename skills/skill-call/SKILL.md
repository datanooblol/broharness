---
name: skill-call
description: Gives skill-selection ability to models that don't natively support tool-calling, by defining a strict prompt-and-parse contract -- available skills listed as name/description pairs, response forced into a single-key JSON codeblock. Use first, before tool-call, to decide which skill(s), if any, match the request.
default: true
version: v0.1.0
tags: [meta, routing]
status: experiment
---

# Skill Call

Pick skills only -- never a tool. This runs before `tool-call`; only skill names
and one-line descriptions are visible here, not tools. The caller appends an
`## Available Skills` section below, built fresh each call from registered skills.

A skill is never called directly -- it's loaded via the fixed `load_skill` tool,
one call per matching skill. This is why the response shape below is identical to
`tool-call`'s: both are "pick from a list of callable things," so the same parsing
function handles either response.

## Instructions

- For every skill that genuinely matches the request, call `load_skill` with that
  skill's name -- none, one, or several calls.
- Never invent a skill name not listed in Available Skills.
- If the request is general and doesn't belong to any listed skill's domain at all
  (e.g. a plain factual or conversational question with nothing file-, joke-, or
  tool-shaped about it), that's not ambiguity -- return `tool_use: []` directly.
  Don't ask a clarifying question just to confirm that no skill is needed; answering
  from general knowledge with no skill loaded is a normal, expected outcome.
- If it's genuinely unclear which skill (or none) the request needs, don't guess --
  call `ask_user_question`. This is about *which domain* the request belongs to,
  e.g. "did you mean the file on disk, or a joke about files?" -- not about any
  specific tool's input, that's `tool-call`'s job once a skill is loaded.
- Ask about exactly one thing per `ask_user_question` call, prefer a closed-ended
  question over an open one, and keep it to one short sentence -- put it in
  `question`, not as separate reply text. Don't ask about anything already stated
  or reasonably inferable.
- If `ask_user_question` is picked, it must be the **only** entry in `tool_use` --
  never mixed with `load_skill` calls in the same response. Don't act on a guess
  while something still needs clarifying.
- If more than one thing needs clarifying, return one `ask_user_question` call per
  question rather than combining them into one `question` string -- each stays a
  single, focused ask. They're put to the user one at a time, waiting for each
  reply before asking the next, not all at once.

## Response

Exactly one JSON codeblock, nothing else -- no prose, no reasoning, nothing
before or after the fence, not even a trailing question. One key, `tool_use`,
a list of `{"name": ..., "input": {...}}`. Always present, `[]` when nothing
matches.

Why this matters: the parser only ever reads what's inside the fence -- it
never sees anything written outside it. If you ask a question outside the
fence, that question is never asked; if you write an answer outside it, that
answer never reaches the user. Nothing about the fence being present and
correct saves you if there's text before or after it -- the whole response is
treated as broken, not just the extra part. If you need to ask something, put
it in an `ask_user_question` call inside `tool_use`; if you're done, use
`tool_use: []`. There is no valid reason for anything to exist outside the
fence.

```json
{
  "tool_use": [
    { "name": "load_skill", "input": { "skill_name": "file-ops" } }
  ]
}
```

```json
{
  "tool_use": [
    { "name": "ask_user_question", "input": { "question": "Did you mean an actual file, or do you want a joke about files?" } }
  ]
}
```

```json
{ "tool_use": [] }
```
