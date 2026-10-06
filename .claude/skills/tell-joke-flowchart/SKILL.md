---
name: tell-joke-flowchart
description: Tell a joke on request or when detecting that users feel bad/upset or ask to lighten their moods -- dad jokes, puns, knock-knock jokes, one-liners, riddles, or a mix of any of these. Use when the user asks for a joke, wants to be entertained, or needs a laugh. (flowchart diagram variant, for format comparison testing)
---

# Tell Joke (flowchart variant)

## Instructions

```mermaid
flowchart TD
    Start([Joke requested]) --> TypeGiven{Type stated<br/>in the request?}
    TypeGiven -->|no| AskType[Ask: which kind of joke?<br/>dad joke / pun / knock-knock /<br/>one-liner / riddle / a mix]
    TypeGiven -->|yes| TopicGiven
    AskType --> TopicGiven{Topic stated<br/>in the request?}
    TopicGiven -->|no| AskTopic[Ask: what topic? separate question,<br/>not bundled with the type question --<br/>no preference is a fine answer, don't force a pick]
    TopicGiven -->|yes| Clear
    AskTopic --> Clear{Answer unclear?}
    Clear -->|yes| AskClarify[Ask a short clarifying question]
    AskClarify --> Clear
    Clear -->|no| HowMany{How many types<br/>does the request need?}
    HowMany -->|one specific type| LoadOne[Read that one reference file]
    HowMany -->|explicit both / all /<br/>names more than one type| LoadMany[Read every matching<br/>reference file]
    HowMany -->|unspecified mix,<br/>e.g. surprise me| LoadPick[Read any one reference file]
    LoadOne --> Write
    LoadMany --> Write
    LoadPick --> Write
    Write[Write exactly ONE fresh joke,<br/>in your own words --<br/>never paste a reference file back verbatim,<br/>use it as a style guide]
    Write --> Fuse{More than one<br/>reference read?}
    Fuse -->|yes| FuseStyles[Fuse every loaded style's characteristics<br/>into that single joke -- e.g. a pun's wordplay<br/>delivered with a dad joke's deadpan literalism --<br/>not one joke per style, not several jokes back to back]
    Fuse -->|no| OneStyle[Write in that one<br/>reference's style]
    FuseStyles --> Final
    OneStyle --> Final
    Final[Keep it short.<br/>Don't explain the joke afterward --<br/>a joke that needs explaining isn't funny.]
```

Notes that don't fit as graph nodes:

- If the user already stated the type and/or topic in their request, that
  answers the `TypeGiven`/`TopicGiven` checks directly -- don't ask again
  for whichever part they already gave.

## References

- `references/dad-joke.md` -- dad joke
- `references/pun-joke.md` -- pun
- `references/knock-knock.md` -- knock-knock joke
- `references/one-liner.md` -- one-liner / observational joke
- `references/riddle.md` -- riddle
