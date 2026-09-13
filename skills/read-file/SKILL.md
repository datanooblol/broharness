---
name: read-file
description: Read the contents of a specific file, or list files matching a pattern. Use when the user wants to see what's in a file, or wants to find files matching a pattern.
version: v0.1.0
tags: [filesystem]
status: experiment
---

# Read File

## Instructions

- If you already know the exact file the user means, use `scripts/read_file.py` with a
  glob pattern narrow enough to match exactly that one file.
- If the user wants to see many files at once, or you aren't sure which single file they
  mean, use `scripts/list_files.py` first to see what matches a broader pattern, then
  narrow down before reading.
- If the path or pattern the user gave is unclear or ambiguous, don't guess -- ask them to
  clarify. Call `ask_followup_question`.
- Never try to work around a refusal from either script (e.g. by rewriting the pattern to
  escape the project) -- both refuse patterns that leave the project root on purpose.

## Errors

`scripts/read_file.py` fails in exactly these ways -- react to each differently, don't
just apologize generically:

- **no match** (`no file matches pattern: <pattern>`) -- the pattern found nothing. Suggest
  `scripts/list_files.py` with a broader pattern to see what's actually there, or ask the
  user to clarify the path.
- **ambiguous match** (`pattern matches N files, expected exactly one: ...`) -- the pattern
  found more than one file. Show the user the listed candidates and ask which one they
  meant, or narrow the pattern yourself if it's obvious from context.
- **not a file** (`matched path is a directory, not a file: <path>`) -- the pattern matched
  a directory, not a file. Use `scripts/list_files.py` on that directory instead, or ask
  the user for a specific file within it.
- **outside project** (`pattern resolves outside the project root: <pattern>`) -- refuse to
  retry with a workaround; tell the user this is out of scope.
- **unreadable** (`could not read <path>: <reason>`) -- a real I/O problem (bad encoding,
  permissions). Report it plainly; don't retry silently.

`scripts/list_files.py` fails in these ways:

- **no match** -- not treated as an error; it prints an empty-result message and exits
  normally. Suggest a broader pattern to the user.
- **too many matches** -- it lists up to 200 and tells you how many more were truncated.
  Ask the user to narrow the pattern rather than trying to read everything it found.
- **outside project** -- same refusal as `read_file.py`, same reasoning.

## Tools

- `scripts/read_file.py` -- reads exactly one file's content, given a pattern narrow
  enough to match just that one file.
- `scripts/list_files.py` -- lists every path matching a broader glob pattern (capped at
  200 results).
