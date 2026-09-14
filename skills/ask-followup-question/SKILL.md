---
name: ask-followup-question
description: Ask the user a clarifying question when you don't have enough information to proceed safely or correctly. Use only when something is genuinely missing or ambiguous -- never speculatively, and never for something you could reasonably infer from context already given.
version: v0.1.0
tags: [meta, clarification]
default: true
status: experiment
---

# Ask Followup Question

This skill is cross-cutting -- any other skill can reach for it mid-task, not just
one routed to by matching a user request. Follow it whenever you're about to guess
instead of ask.

## Instructions

- Ask about exactly ONE thing at a time. Never bundle two questions into one turn --
  it forces the user to answer both at once or pick which to address.
- Prefer closed-ended questions when the possible answers are already known (e.g.
  "dad joke or pun?"), not open-ended ones ("what kind of joke do you like?"). A
  closed question is faster to answer and easier to act on.
- Keep it to one short sentence. No lengthy preamble justifying why you're asking --
  just ask.
- Don't ask about anything you could reasonably infer, or that the user already
  stated earlier in the conversation. Re-asking a known answer reads as not having
  listened.
- If you have a reasonable default, say what it is and ask for a correction instead
  of an open question (e.g. "I'll assume the `pro` plan unless you'd rather go with
  something else?") -- this is often faster than a bare open question.

## Mechanics

1. Write the question as your normal reply content, following the rules above.
2. Call `ask_followup_question` to pause and wait for the user's actual reply --
   never guess an answer in its place, even a plausible one.
3. Once the reply comes back, continue with whatever you were doing before you
   needed to ask -- don't re-ask the same thing again this turn.
