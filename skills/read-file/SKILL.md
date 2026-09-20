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
- If the user names just a filename with no path (e.g. "what's in one-liner.md"), don't
  guess its directory -- search for it anywhere in the project with `**/<filename>`
  (e.g. `**/one-liner.md`). This isn't a guess, it's an exact-name search; if more than
  one file shares that name, `read_file.py`'s normal ambiguous-match handling applies.
- If `scripts/read_file.py`'s pattern matches more than one file, don't pick one
  yourself even if it looks obvious -- call `ask_user_question` with the candidate
  list from the error message and let the user choose.
- If the user wants to see many files at once, or you aren't sure which single file they
  mean, use `scripts/list_directory.py` first to see what matches a broader pattern, then
  narrow down before reading.
- `scripts/list_directory.py` lists both folders and files -- a folder entry is marked
  with a trailing `/`. For a bare, depth-unspecified request ("what's in skills/",
  "what folders are under X"), use a shallow pattern (`skills/*`) to show just the
  immediate contents. For "list everything" / "show me all files" requests, use a
  recursive pattern (`skills/**/*`) instead. Don't default to recursive for a plain
  "what's in this folder" question -- that usually means one level, not a full tree.
- `scripts/list_directory.py` only accepts one pattern per call. If the request is
  unclear about which location/pattern is meant, or genuinely names more than one
  distinct location (e.g. "files in both skills and notebooks"), call
  `ask_user_question` to clarify first. Once it's clear, it's fine to call
  `list_directory` more than once in the same response -- one call per location --
  rather than forcing everything into a single combined pattern.
- If the path or pattern the user gave is unclear or ambiguous for any other reason,
  don't guess -- ask them to clarify. Call `ask_user_question`.
- Never try to work around a refusal from either script (e.g. by rewriting the pattern to
  escape the project) -- both refuse patterns that leave the project root on purpose.

## Errors

`scripts/read_file.py` fails in exactly these ways -- react to each differently, don't
just apologize generically:

- **no match** (`no file matches pattern: <pattern>`) -- the pattern found nothing. Suggest
  `scripts/list_directory.py` with a broader pattern to see what's actually there, or ask
  the user to clarify the path.
- **ambiguous match** (`pattern matches N files, expected exactly one: ...`) -- the pattern
  found more than one file. Call `ask_user_question` with the listed candidates rather
  than picking one yourself, even if it looks obvious.
- **not a file** (`matched path is a directory, not a file: <path>`) -- the pattern matched
  a directory, not a file. Use `scripts/list_directory.py` on that directory instead, or
  ask the user for a specific file within it.
- **outside project** (`pattern resolves outside the project root: <pattern>`) -- refuse to
  retry with a workaround; tell the user this is out of scope.
- **unreadable** (`could not read <path>: <reason>`) -- a real I/O problem (bad encoding,
  permissions). Report it plainly; don't retry silently.

`scripts/list_directory.py` fails in these ways:

- **no match** (`nothing matches pattern: <pattern>`) -- not treated as an error; it
  prints an empty-result message and exits normally. Suggest a broader pattern to the
  user.
- **too many matches** -- it lists up to 200 and tells you how many more were truncated.
  Ask the user to narrow the pattern rather than trying to read everything it found.
- **outside project** -- same refusal as `read_file.py`, same reasoning.
- **unclear or multi-location pattern** -- not something the script detects (it only ever
  takes one pattern per call); catch this before calling it at all. See Instructions.

## Tools

- `scripts/read_file.py` -- reads exactly one file's content, given a pattern narrow
  enough to match just that one file.
- `scripts/list_directory.py` -- lists every file and folder matching a broader glob
  pattern (capped at 200 results); folders are marked with a trailing `/`.
