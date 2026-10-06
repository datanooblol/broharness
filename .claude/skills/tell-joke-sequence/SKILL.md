---
name: tell-joke-sequence
description: Tell a joke on request or when detecting that users feel bad/upset or ask to lighten their moods -- dad jokes, puns, knock-knock jokes, one-liners, riddles, or a mix of any of these. Use when the user asks for a joke, wants to be entertained, or needs a laugh. (sequence diagram variant, for format comparison testing)
---

# Tell Joke (sequence diagram variant)

## Instructions

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
        Assistant->>Assistant: read that one reference file
    else explicit both/all/names more than one type
        Assistant->>Assistant: read every matching reference file
    else unspecified mix, e.g. surprise me
        Assistant->>Assistant: read any one reference file
    end

    alt more than one reference read
        Assistant->>Assistant: fuse every loaded style into one joke
    else exactly one reference read
        Assistant->>Assistant: write in that one style
    end

    Assistant-->>User: exactly one fresh joke, short, no explanation after
```

Notes that don't fit as graph nodes:

- Each `Assistant->>User` question above is its own separate question
  (never bundled into another), and never paste a loaded reference back
  verbatim -- use it as a style guide to write a fresh joke.
- If the user already stated the type and/or topic in their request, skip
  straight past that `alt` block -- don't ask again for what's already given.

## References

- `references/dad-joke.md` -- dad joke
- `references/pun-joke.md` -- pun
- `references/knock-knock.md` -- knock-knock joke
- `references/one-liner.md` -- one-liner / observational joke
- `references/riddle.md` -- riddle
