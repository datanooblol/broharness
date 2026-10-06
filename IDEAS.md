# Diagram-as-prompt mockups — tell-joke, three ways

Same `tell-joke` logic (the live `SKILL.md`'s current flowchart), redrawn
as a state diagram and a sequence diagram, so the three can be compared
side by side before picking one to actually test. **Nothing here is live**
-- this is a review document, not a skill.

## 1. Flowchart (what's already live in `SKILL.md`)

```mermaid
flowchart TD
    Start([Joke requested]) --> TypeGiven{Type stated<br/>in the request?}
    TypeGiven -->|no| AskType[ask_user_question:<br/>which kind of joke?<br/>dad joke / pun / knock-knock /<br/>one-liner / riddle / a mix]
    TypeGiven -->|yes| TopicGiven
    AskType --> TopicGiven{Topic stated<br/>in the request?}
    TopicGiven -->|no| AskTopic[ask_user_question:<br/>what topic? separate call,<br/>not bundled with the type question --<br/>no preference is a fine answer, don't force a pick]
    TopicGiven -->|yes| Clear
    AskTopic --> Clear{Answer unclear?}
    Clear -->|yes| AskClarify[ask_user_question:<br/>short clarifying question]
    AskClarify --> Clear
    Clear -->|no| HowMany{How many types<br/>does the request need?}
    HowMany -->|one specific type| LoadOne[load_skill_extension:<br/>that one reference]
    HowMany -->|explicit both / all /<br/>names more than one type| LoadMany[load_skill_extension:<br/>one call per matching<br/>reference, same turn]
    HowMany -->|unspecified mix,<br/>e.g. surprise me| LoadPick[load_skill_extension:<br/>pick any one reference]
    LoadOne --> Write
    LoadMany --> Write
    LoadPick --> Write
    Write[Write exactly ONE fresh joke,<br/>in your own words --<br/>never paste a reference file back verbatim,<br/>use it as a style guide]
    Write --> Fuse{More than one<br/>reference loaded?}
    Fuse -->|yes| FuseStyles[Fuse every loaded style's characteristics<br/>into that single joke -- e.g. a pun's wordplay<br/>delivered with a dad joke's deadpan literalism --<br/>not one joke per style, not several jokes back to back]
    Fuse -->|no| OneStyle[Write in that one<br/>reference's style]
    FuseStyles --> Final
    OneStyle --> Final
    Final[Keep it short.<br/>Don't explain the joke afterward --<br/>a joke that needs explaining isn't funny.]
```

**Syntax notes:** `flowchart TD` (top-down). Rounded `([...])` for
start/end, diamond `{...}` for a yes/no or multi-way question, rectangle
`[...]` for an action/instruction. Branches are labeled edges
(`-->|label|`). Reads as "what do I check, what do I do" -- closest to how
the prose instructions were already structured (one bullet per decision).

## 2. State diagram

```mermaid
stateDiagram-v2
    [*] --> CheckType

    state CheckType <<choice>>
    CheckType --> AskingType: type not stated
    CheckType --> CheckTopic: type stated

    AskingType --> CheckTopic: user answers

    state CheckTopic <<choice>>
    CheckTopic --> AskingTopic: topic not stated
    CheckTopic --> CheckClear: topic stated (or no preference)

    AskingTopic --> CheckClear: user answers

    state CheckClear <<choice>>
    CheckClear --> Clarifying: answer still unclear
    CheckClear --> Loading: clear

    Clarifying --> CheckClear: user answers

    state Loading {
        [*] --> LoadOne: one specific type requested
        [*] --> LoadMany: explicit both/all/names more than one type
        [*] --> LoadPick: unspecified mix, e.g. surprise me -- pick any one
        LoadOne --> [*]
        LoadMany --> [*]
        LoadPick --> [*]
    }

    Loading --> Writing

    state Writing <<choice>>
    Writing --> Fuse: more than one reference loaded
    Writing --> SingleStyle: exactly one reference loaded

    Fuse --> Done: fuse every loaded style into one joke
    SingleStyle --> Done: write in that one style

    Done --> [*]: deliver -- short, no explanation after
```

**Syntax notes:** `stateDiagram-v2`. `[*]` is the start/end pseudostate.
`state X <<choice>>` marks a decision point (same role as a flowchart
diamond, drawn as a small diamond node). `state Loading { ... }` is a
*composite state* -- a sub-machine nested inside one named state, used
here to group the three loading variants without flattening them into the
top-level flow. Edges carry the triggering event as a label
(`A --> B: event`), not a question -- the diagram describes what the
*system's situation* is at each point ("AskingType", "Loading"), not just
what to check next.

## 3. Sequence diagram

```mermaid
sequenceDiagram
    actor User
    participant Assistant

    User->>Assistant: joke requested

    alt type not stated
        Assistant->>User: which kind of joke?
        User-->>Assistant: answer
    end

    alt topic not stated
        Assistant->>User: what topic? (no preference is fine)
        User-->>Assistant: answer
    end

    loop while answer is unclear
        Assistant->>User: short clarifying question
        User-->>Assistant: answer
    end

    alt one specific type requested
        Assistant->>Assistant: load_skill_extension: that one reference
    else explicit both/all/names more than one type
        Assistant->>Assistant: load_skill_extension: one call per reference
    else unspecified mix, e.g. surprise me
        Assistant->>Assistant: load_skill_extension: pick any one reference
    end

    alt more than one reference loaded
        Assistant->>Assistant: fuse every loaded style into one joke
    else exactly one reference loaded
        Assistant->>Assistant: write in that one style
    end

    Assistant-->>User: exactly one fresh joke, short, no explanation after
```

**Syntax notes:** `sequenceDiagram`. Two lanes only (`User`, `Assistant`)
-- no third party exists in this skill's own logic, so no extra
participant was added just to fill the format. `->>`/`-->>` are
message arrows (solid = request, dashed = reply); a self-arrow
(`Assistant->>Assistant`) represents an internal decision with no real
back-and-forth. `alt`/`else`/`end` for branches, `loop`/`end` for the
repeat-until-clear step. Reads as a *conversation transcript* -- turn by
turn -- rather than a map of decisions.

## At a glance

| | Reads most like... | Where it's weakest |
|---|---|---|
| Flowchart | A checklist: "check this, then do that" | Doesn't show *who* is being talked to at each step -- `ask_user_question` is just another box |
| State diagram | "What situation am I in right now" | The choice/composite-state vocabulary (`<<choice>>`, nested `state {}`) is the least self-explanatory of the three at a glance |
| Sequence diagram | A back-and-forth transcript with the user | Internal decisions (which reference(s) to load, whether to fuse) have to be drawn as self-arrows, which reads oddly for something that isn't really a "message" |
