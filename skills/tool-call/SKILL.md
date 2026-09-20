---
name: tool-call
description: Gives tool-call ability to models that don't natively support it, by defining a strict prompt-and-parse contract -- available tools listed in YAML, response forced into a single-key JSON codeblock. Use once a skill's own tools are in scope; for choosing which skill to load in the first place, use skill-call instead.
default: true
version: v0.1.0
tags: [meta, tool-calling]
status: experiment
---

# Tool Call

Pick tools only -- never a skill name. Skill selection already happened in an
earlier `skill-call` step; the caller appends an `## Available Tools` section
below, built fresh each call from the currently-loaded skill's own tools.

## Instructions

- Pick every tool that matches the request -- none, one, or several.
- Never invent a tool name or input field not listed in Available Tools. A
  skill's own `scripts/*.py` are already registered and directly callable by
  their own name the moment the skill is loaded -- you don't need to call
  `load_tool` first for them. A reference or asset (`references/*.md`,
  `assets/*.*`) is different: that's content, not code, and only becomes
  available by calling `load_skill_extension` with that path -- don't try to
  read it any other way. `load_tool` still exists for the rare case a script
  isn't already showing up in Available Tools, but reach for it only then,
  not as a routine first step.
- Before calling `load_skill_extension`, check whether that path's content
  already appears above (in the loaded skill's own section). If it's already
  there, don't call it again -- use what you already have instead of
  re-fetching the same path.
- If a tool clearly applies but one of its required inputs is missing or
  ambiguous, don't guess a value -- call `ask_user_question` instead. This is
  about *filling in a specific input*, e.g. "which file did you mean?" -- not
  about which skill or domain the request belongs to, that was already settled
  by `skill-call` before this step ever ran.
- Ask about exactly one thing per `ask_user_question` call, prefer a closed-ended
  question over an open one, and keep it to one short sentence -- put it in
  `question`, not as separate reply text. Don't ask about anything already stated
  or reasonably inferable.
- If `ask_user_question` is picked, it must be the **only** entry in `tool_use` --
  never mixed with real tool calls in the same response. Don't act on a guess
  while something still needs clarifying.
- If more than one input needs clarifying, return one `ask_user_question` call per
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
    { "name": "load_skill_extension", "input": { "skill_name": "file-ops", "path": "references/errors.md" } }
  ]
}
```

```json
{
  "tool_use": [
    { "name": "read_file", "input": { "pattern": "skills/file-ops/SKILL.md" } }
  ]
}
```

```json
{
  "tool_use": [
    { "name": "ask_user_question", "input": { "question": "Which file did you mean?" } }
  ]
}
```

```json
{ "tool_use": [] }
```
