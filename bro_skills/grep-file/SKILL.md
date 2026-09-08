---
name: grep-file
description: Search for a text pattern inside a specific file and return matching lines with their line numbers. Use this when the user names a file and a pattern/word/string to find within it.
---

# Grep File

When invoked, you have access to two tools: `read_file(path)` and
`grep_file(pattern, path)`.

1. Identify the file path and the pattern from the request.
2. Call `grep_file(pattern, path)`.
3. Report each match as `line_number: line_text`. If there are no matches,
   say so plainly.

Do not read the whole file unless the user also asks for that.
