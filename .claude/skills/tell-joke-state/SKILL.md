---
name: tell-joke-state
description: Tell a joke on request or when detecting that users feel bad/upset or ask to lighten their moods -- dad jokes, puns, knock-knock jokes, one-liners, riddles, or a mix of any of these. Use when the user asks for a joke, wants to be entertained, or needs a laugh. (state diagram variant, for format comparison testing)
---

# Tell Joke (state diagram variant)

## Instructions

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
    Writing --> Fuse: more than one reference read
    Writing --> SingleStyle: exactly one reference read

    Fuse --> Done: fuse every loaded style into one joke
    SingleStyle --> Done: write in that one style

    Done --> [*]: deliver -- short, no explanation after
```

Notes that don't fit as graph nodes:

- Each question above ("which kind of joke", "what topic") should be its
  own separate question, never bundled -- and never paste a reference
  file back verbatim, use it as a style guide to write a fresh joke.
- "AskingType"/"AskingTopic" only fire when that part is genuinely missing
  from the request -- if the user already stated it, go straight to
  `CheckTopic`/`CheckClear`.

## References

- `references/dad-joke.md` -- dad joke
- `references/pun-joke.md` -- pun
- `references/knock-knock.md` -- knock-knock joke
- `references/one-liner.md` -- one-liner / observational joke
- `references/riddle.md` -- riddle
