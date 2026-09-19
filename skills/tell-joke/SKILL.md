---
name: tell-joke
description: Tell a joke on request or when detecting that users feel bad/upset or ask to lighten their moods -- dad jokes, puns, knock-knock jokes, one-liners, riddles, or a mix of any of these. Use when the user asks for a joke, wants to be entertained, or needs a laugh.
version: v0.1.0
tags: [fun, entertainment]
status: experiment
---

# Tell Joke

## Instructions

- Ask the user which kind of joke they'd like: dad jokes, puns, knock-knock
  jokes, one-liners, riddles, or a mix of any of these.
- Also ask what topic the joke should be about (e.g. work, food, animals) -- as its
  own separate `ask_user_question` call, not bundled into the joke-type question.
  No topic preference is a fine answer too; don't force a pick.
- If they already said the type and/or topic in their request, don't ask again for
  whichever part they already gave.
- If their answer is unclear, ask a short clarifying question. Call `ask_user_question`.
- Tell exactly one joke at a time, in your own words. Don't paste a reference file's
  contents back verbatim -- use it as a style guide to write a fresh joke on the
  requested topic, not a script to copy.
- If more than one reference is loaded (a "both"/"all"/multi-type request), that's
  still one joke, not one per style -- fuse every loaded style's characteristics
  into a single joke (e.g. a pun's wordplay delivered with a dad joke's deadpan
  literalism, or a riddle's question-then-answer shape built around a pun),
  rather than picking just one style and ignoring the rest, or telling several
  jokes back to back.
- Keep it short, and don't explain the joke afterward -- a joke that needs explaining isn't funny.

## References

- `references/dad-joke.md` -- use when the user wants a dad joke.
- `references/pun-joke.md` -- use when the user wants a pun.
- `references/knock-knock.md` -- use when the user wants a knock-knock joke.
- `references/one-liner.md` -- use when the user wants a one-liner/observational joke.
- `references/riddle.md` -- use when the user wants a riddle joke.
- If the user's request implies more than one type at once (e.g. "both", "all of
  them", or naming more than one type by name), call `load_skill_extension` once
  per matching reference -- one call per type, all in the same response. This
  applies no matter how many reference files exist here in the future, not just
  these five.
- If the request is just an unspecified "mix" with no explicit "both"/"all" (e.g.
  "surprise me" or "a mix is fine"), one reference is enough for this turn -- pick
  any one, since only one joke gets told at a time anyway.
