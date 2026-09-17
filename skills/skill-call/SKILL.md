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
- Missing or ambiguous request: use `ask_user_question` instead of guessing.

## Response

Exactly one JSON codeblock, nothing else -- no prose, no reasoning. One key,
`tool_use`, a list of `{"name": "load_skill", "input": {"skill_name": ...}}`.
Always present, `[]` when nothing matches.

```json
{
  "tool_use": [
    { "name": "load_skill", "input": { "skill_name": "read-file" } }
  ]
}
```

```json
{ "tool_use": [] }
```
