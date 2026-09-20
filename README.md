# broharness

A small, prompt-based tool-calling harness for models without native
tool-calling — built from scratch to study the mechanism, modeled loosely
on how Claude Code discovers and runs its own skills. Users write their
own skills as plain folders (a `SKILL.md` plus optional bundled scripts);
`broharness` is just the fixed engine that discovers them, routes a
request to one, and runs a tool loop against it.

**This is a test version (`v0.0.0`)** — the mechanism works and is
exercised end to end against a real model, but it's a study project, not a
finished product. See [Known limitations](#known-limitations-honest-about-the-test-version)
before relying on it for anything beyond experimentation.

## What this is, in one shape

```python
from pathlib import Path
from broskill import SkillControl, ToolControl
from broharness import Harness
from broharness.data_model import State
from broharness.llms.bedrock import UserMessage

SKILL_DIR = Path("skills")
sc = SkillControl(SKILL_DIR)
tc = ToolControl(sc)

h = Harness()  # the fixed orchestration -- owns no config of its own
state = State(
    root=Path("."),
    skill_dir=SKILL_DIR,
    messages=[UserMessage("what's in skills/file-ops/SKILL.md?")],
    session_messages=[...],
    skill_control=sc,
    tool_control=tc,
    tools={"load_skill": sc.load_skill, "load_skill_extension": sc.load_skill_extension, "load_tool": tc.load_tool},
    session_tools={...},
    debug=[...],
)
state = h.run(state)   # one turn: State in, State out
print(state.messages[-1]["content"][0]["text"])
```

`Harness` is deliberately lean: it builds the fixed task flow once and
does nothing else. Everything about a run — which skills directory, which
model per role, the system prompt, whether to print step traces — lives on
`State`, built by the caller. This keeps the two testable and controllable
separately, and keeps `Harness` reusable across many independently-built
`State`s. See `notebooks/from_scratch.ipynb` for the fully hand-assembled
version (useful for understanding every moving part) and
`notebooks/recipe.ipynb` for the packaged, day-to-day usage shown above.

## Repo layout

```
src/broharness/
  data_model.py     Process enum, LLMUse (per-role model ids), State,
                     shared helpers (usage tracking, anti-hallucination
                     guards, debug tracing)
  harness.py         Harness -- builds the fixed TaskRegistry/Flow, run(state)
  codeblock.py        parses a model's response into a strict JSON contract
  toolblock.py         the harness's own meta-tools (load_skill,
                        load_skill_extension, load_tool, ask_user_question)
  flows/              the six tasks that make up the fixed orchestration
  llms/bedrock.py     the one supported LLM call today (AWS Bedrock)

skills/               one folder per skill -- see "What a skill is" below
notebooks/
  from_scratch.ipynb  hand-assembles everything, cell by cell -- the
                       teaching version
  recipe.ipynb         the packaged Harness API, mirrored from the above
  (bedrock.ipynb, dev.ipynb, flow_idea.ipynb, skill_tool_flow_idea.ipynb
   are earlier exploration drafts, superseded by the two above)
```

## What a skill is

A skill is a folder under `skills/` with a `SKILL.md`: YAML frontmatter
(`name`, `description`, ...) plus a free-form body of instructions, and
optionally a `scripts/` folder of executable Python scripts and/or a
`references/` folder of supporting documents.

```
---
name: file-ops
description: Create, read, update, delete, or list files in the project.
  Use when the user wants to see what's in a file, find files matching a
  pattern, write a new file, change a file's content, or remove a file.
version: v0.1.0
tags: [filesystem]
status: experiment
---

# File Operations

## Instructions
...
## Errors
...
## Tools
- `scripts/read_file.py` -- ...
```

The `description` is what a routing model reasons over when deciding
whether to trigger a skill — it's read for every skill, every turn; the
full body is only loaded for the one skill chosen. A vague description
means a skill that never gets picked, or gets picked for the wrong
request.

**Scripts are auto-registered.** The moment a skill loads, every
`scripts/*.py` file in it becomes directly callable by name — no separate
registration step needed (this used to require the model to call
`load_tool` first; it proved unreliable even after explicit corrective
errors, so it's now automatic and free). A script just needs a
`get_args()` returning an `argparse.ArgumentParser`; its help text becomes
the tool's description shown to the model.

**References are opt-in.** A `references/*.md` file (e.g. a style guide, a
detail doc) is *not* auto-loaded — a skill's instructions point to it, and
the model calls `load_skill_extension` to pull it in only when actually
needed. This is the progressive-disclosure half of the design: a skill's
`SKILL.md` should stay short, and reference files carry the detail that
isn't needed on every single call.

## How the fixed flow works

Every request runs through the same six tasks (`src/broharness/flows/`):

```
skill_call → tool_call → tool_use → answer
     ↑            ↑          ↓  ↑        ↓
     └──── fail_recovery ────┘  └── ask_user_question
```

- **`skill_call`** — given every skill's `(name, description)`, picks
  zero or more skills to load (or none, if the request needs no skill).
- **`tool_call`** — given the loaded skill's instructions and its
  auto-registered tools, picks which tool(s) to call, if any.
- **`tool_use`** — actually runs the chosen tool: a skill's own script (as
  a real subprocess, isolated from the harness process), one of the
  harness's own meta-tools (`load_skill`, `load_skill_extension`,
  `load_tool`), or `ask_user_question` (blocks on real `input()`).
- **`answer`** — writes the final natural-language reply, grounded in
  whatever was actually fetched. It has no tool-calling ability of its
  own on purpose — this is where a small model is most tempted to
  hallucinate a plausible-sounding answer instead of admitting something
  wasn't found, so its prompt is the most heavily guarded part of the
  harness (see below).
- **`fail_recovery`** — a bounded retry (`state.max_retries`, default 3)
  for any task that errors, falling through to `answer` once exhausted
  rather than looping forever.

Both the model's response format (a single JSON codeblock, nothing else)
and this task graph are a fixed contract — a skill only ever supplies
*content* (instructions, scripts, references), never orchestration logic.

## Guardrails this harness actually enforces

Built in response to specific, reproduced failures against a real (small,
12B) model — not speculative hardening:

- **Anti-hallucination in `answer`** — its prompt explicitly forbids
  stating a fact/file content not actually present in what was fetched,
  and a separate check (`tool_results_are_empty`) calls out a "nothing
  found" result explicitly, since a quiet empty-result message read enough
  like content that the model would sometimes invent a plausible answer
  around it anyway.
- **Real-question detection, not "ends in `?`"** — a naive
  `text.endswith('?')` check misfires on a persona whose sentences
  habitually end in a rhetorical tag ("...you know?", "...right?"),
  derailing a complete answer into an unwanted clarification loop.
  `looks_like_a_question()` requires the final sentence to actually start
  like a question (a WH-word or auxiliary verb).
- **Per-conversation skill-loaded checks** — `load_skill_extension` is
  checked against *this conversation's* `state.registered_skills`, not
  delegated straight to the skill-loading library's own internal
  tracking, which turned out to persist across unrelated runs sharing the
  same `SkillControl` instance and could let a wrong `skill_name` silently
  succeed instead of failing loudly.
- **Per-turn state flushing** — `State.flush_turn()` clears everything
  only valid for the turn that just finished (`tool_results`,
  `candidated_tools`, `executed_calls`, ...) before a new turn starts,
  since a previous turn's fetched content sitting in `State` was answering
  the *next*, unrelated question.

## Skills included

- **`skill-call` / `tool-call`** — the meta-skills that carry the
  tool-calling contract prompt itself (`default: true`, always loaded).
  Not something you'd normally touch when adding a new skill.
- **`file-ops`** — create/read/update/delete/list files in the project.
  Destructive actions (`update_file`, `delete_file`) require confirming
  with the user first; `delete_file` never accepts a glob pattern.
- **`tell-joke`** — dad jokes, puns, knock-knock jokes, one-liners,
  riddles — reference-driven style guides, not canned joke lists.
- **`ds-mentor`** — explains data science/ML/statistics concepts to a
  junior data scientist (metrics, stats basics, model fundamentals, common
  pitfalls, pandas gotchas), grounded in curated reference material.

## Running it

Needs AWS credentials resolvable by `boto3` (env vars,
`~/.aws/credentials`, SSO profile, ...) with Bedrock model access granted
for `google.gemma-3-12b-it` in `us-east-1` — the only LLM backend wired up
today (`src/broharness/llms/bedrock.py`).

```
uv sync
```

`uv sync` installs this repo's own `src/broharness` package in editable
mode. Then open `notebooks/recipe.ipynb` (packaged `Harness` usage) or
`notebooks/from_scratch.ipynb` (every piece assembled by hand) and run it
top to bottom in your own kernel.

## Building your own skill

1. `skills/<your-skill>/SKILL.md` with frontmatter (`name`, `description`,
   `version`, `tags`, `status`) and an `## Instructions` section written
   for a model that can only act through the tool-call contract — assume
   nothing carries over between calls except what's in `State`.
2. Optional `skills/<your-skill>/scripts/*.py` — any script with a
   `get_args()` returning an `argparse.ArgumentParser` is auto-registered
   as a callable tool the moment the skill loads. Runs as a real
   subprocess; only stdout/stderr comes back, never its source.
3. Optional `skills/<your-skill>/references/*.md` — loaded on demand via
   `load_skill_extension`, not automatically. Good for detail that
   shouldn't bloat the main `SKILL.md` (error taxonomies, style guides,
   longer reference docs).
4. Add an `## Errors` section if your scripts can fail in more than one
   way — spell out each distinct error message and what the model should
   do in response, rather than one generic "something went wrong."
   `file-ops/SKILL.md` is the fullest example of this pattern.
5. Test it directly (`uv run skills/<your-skill>/scripts/foo.py --arg ...`)
   before testing it through the harness — isolates a script bug from a
   prompting/routing issue.

## Known limitations (honest, about the test version)

- **Meta-skills aren't cleanly separated from user skills.** `skill-call`
  and `tool-call` currently live in the same `skills/` folder a user would
  put their own skills in, and are referenced by hardcoded name in
  `flows/skill_call.py`/`flows/tool_call.py` rather than via the `default`
  flag the underlying skill library already exposes. A `skills/` folder
  missing those two will break.
- **Single LLM backend.** Only AWS Bedrock (`llms/bedrock.py`) is wired
  up; `Harness(llm=...)` accepts any compatible callable, but nothing else
  has been tested against it yet.
- **Small-model retry stubbornness.** The harness bounds failures with
  retries and a graceful fallback (see Guardrails above), but a small
  model sometimes repeats the exact same wrong tool call verbatim across
  every retry rather than self-correcting — this is a capability limit of
  the model tested against, not something further prompt tuning reliably
  fixes.
- **No cross-skill tool sharing.** A skill's auto-registered tools are
  only visible while that skill is loaded; a second skill can't reuse the
  first one's scripts without duplicating them.
