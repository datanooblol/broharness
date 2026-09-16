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
- Never invent a tool name or input field not listed in Available Tools.
- Missing or ambiguous input: use `ask_followup_question` instead of guessing.

## Response

Exactly one JSON codeblock, nothing else -- no prose, no reasoning. One key,
`tool_use`, a list of `{"name": ..., "input": {...}}`. Always present, `[]` when
nothing matches.

```json
{"tool_use": [{"name": "read_file", "input": {"pattern": "skills/read-file/SKILL.md"}}]}
```

```json
{"tool_use": []}
```
