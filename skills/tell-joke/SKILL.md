---
name: tell-joke
description: Tell a joke on request -- dad jokes, puns, or a mix of both. Use when the user asks for a joke, wants to be entertained, or needs a laugh.
version: v0.1.0
tags: [fun, entertainment]
status: experiment
---

# Tell Joke

## Instructions

- Ask the user which kind of joke they'd like: dad jokes, puns, or a mix of both.
- If they already said which kind in their request, don't ask again -- just tell one.
- If their answer is unclear, ask a short clarifying question directly in your reply. Call `ask_followup_question`.
- Tell exactly one joke at a time, in your own words. Don't paste a reference file's
  contents back verbatim.
- Keep it short, and don't explain the joke afterward -- a joke that needs explaining isn't funny.

## References

- `references/dad-joke.md` -- use when the user wants a dad joke.
- `references/pun-joke.md` -- use when the user wants a pun.
