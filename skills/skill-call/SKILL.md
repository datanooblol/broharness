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
- If it's genuinely unclear which skill (or none) the request needs, don't guess --
  call `ask_user_question`. This is about *which domain* the request belongs to,
  e.g. "did you mean the file on disk, or a joke about files?" -- not about any
  specific tool's input, that's `tool-call`'s job once a skill is loaded.
- Ask about exactly one thing, prefer a closed-ended question over an open one, and
  keep it to one short sentence -- put it in `question`, not as separate reply text.
  Don't ask about anything already stated or reasonably inferable.

## Response

Exactly one JSON codeblock, nothing else -- no prose, no reasoning. One key,
`tool_use`, a list of `{"name": ..., "input": {...}}`. Always present, `[]` when
nothing matches.

```json
{
  "tool_use": [
    { "name": "load_skill", "input": { "skill_name": "read-file" } }
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
