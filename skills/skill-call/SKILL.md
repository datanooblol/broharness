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

## Instructions

- Pick every skill that genuinely matches the request -- none, one, or several.
- Never invent a skill name not listed in Available Skills.

## Response

Exactly one JSON codeblock, nothing else -- no prose, no reasoning. One key,
`skill_names`, a list of strings. Always present, `[]` when nothing matches.

```json
{"skill_names": ["read-file"]}
```

```json
{"skill_names": []}
```
