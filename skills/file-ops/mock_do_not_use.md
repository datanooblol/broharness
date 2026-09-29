---
name: file-ops
description: Create, read, update, delete, or list files in the project. Use when the user wants to see what's in a file, find files matching a pattern, write a new file, change a file's content, or remove a file.
version: v0.2.0
tags: [filesystem]
status: experiment
---

# File Operations

## Instructions

### Reading and listing

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

### Creating and updating

- `scripts/create_file.py` and `scripts/update_file.py` both take an exact `--path`,
  never a glob pattern -- there's nothing to disambiguate for a write. If you don't
  know the exact path yet, resolve it first (e.g. via `list_directory.py` or by asking)
  rather than guessing.
- Don't choose between create and update yourself when it's unclear whether the file
  already exists -- try the one that matches what the user described, and if it fails
  because the file already exists (or doesn't), switch to the other one rather than
  asking the user to pick between two tool names they don't know about.
- The content you write must come from the user's message or from something already
  shown in this conversation (e.g. under `## Tool Use and Result`) -- never invent or
  guess file content to fill the `--content` field. If you don't have real content to
  write, ask the user for it instead of making something plausible up.
- Before calling `update_file` in a way that would overwrite existing content the user
  didn't explicitly ask to replace, confirm first with `ask_user_question`, naming the
  file plainly (e.g. "This will replace the current content of `notes.md` -- go
  ahead?"). Skip the confirmation only when the user's request already made the intent
  to overwrite explicit (e.g. "replace the contents of notes.md with ...").

### Deleting

- `scripts/delete_file.py` takes an exact `--path` only -- it does not accept a glob
  pattern, on purpose, so it can never delete more than one file per call.
- Always confirm with `ask_user_question` before calling `delete_file`, naming the exact
  file (e.g. "Delete `scratch/note.md` -- are you sure?"). This is the real safety gate:
  the script itself has no undo and no interactive prompt, so the confirmation has to
  happen here, before the call is made. Never skip this even if the request sounds
  confident.
- `delete_file` refuses to delete a directory -- if the user wants to remove a whole
  folder, tell them that's out of scope for this tool rather than trying a workaround.

### General

- If the path or pattern the user gave is unclear or ambiguous for any reason, don't
  guess -- ask them to clarify. Call `ask_user_question`.
- Never try to work around a refusal from any of these scripts (e.g. by rewriting the
  path to escape the project) -- all of them refuse paths that leave the project root
  on purpose.

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

`scripts/create_file.py` fails in these ways:

- **already exists** (`file already exists: <path> -- use update_file to modify it`) --
  switch to `update_file` (after confirming the overwrite is wanted) instead of retrying
  create.
- **missing parent directory** (`parent directory does not exist: <dir>`) -- the folder
  the file would live in doesn't exist yet. Tell the user; this tool won't create
  directory structure on its own.
- **outside project** -- same refusal as above.
- **write failed** (`could not write <path>: <reason>`) -- a real I/O problem. Report it
  plainly.

`scripts/update_file.py` fails in these ways:

- **does not exist** (`file does not exist: <path> -- use create_file to make it first`)
  -- switch to `create_file` instead of retrying update.
- **not a file** (`path is a directory, not a file: <path>`) -- can't overwrite a
  directory. Tell the user.
- **outside project** -- same refusal as above.
- **write failed** (`could not write <path>: <reason>`) -- a real I/O problem. Report it
  plainly.

`scripts/delete_file.py` fails in these ways:

- **does not exist** (`file does not exist: <path>`) -- nothing to delete; tell the
  user, don't retry.
- **is a directory** (`will not delete a directory: <path>`) -- out of scope for this
  tool; tell the user.
- **outside project** -- same refusal as above.
- **delete failed** (`could not delete <path>: <reason>`) -- a real I/O problem
  (e.g. permissions). Report it plainly.

## Tools

- `scripts/read_file.py` -- reads exactly one file's content, given a pattern narrow
  enough to match just that one file.
- `scripts/list_directory.py` -- lists every file and folder matching a broader glob
  pattern (capped at 200 results); folders are marked with a trailing `/`.
- `scripts/create_file.py` -- creates a new file with given content at an exact path;
  refuses if the file already exists.
- `scripts/update_file.py` -- overwrites an existing file's full content at an exact
  path; refuses if the file doesn't exist.
- `scripts/delete_file.py` -- deletes exactly one existing file at an exact path; never
  accepts a pattern, never deletes a directory.
