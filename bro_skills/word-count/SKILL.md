---
name: word-count
description: Count words per line in a text file using the bundled count_words.py script. Use this when the user asks how many words are on each line, or wants a per-line word count, of a specific file.
---

# Word Count

This skill bundles a script instead of relying on in-process tools:
`count_words.py`, sitting next to this file.

When invoked:

1. Identify the file path from the request.
2. Run the tool call `{"tool": "run_script", "args": {"script": "count_words.py", "args": ["<path>"]}}`.
3. The script prints one `line_number: word_count` line per line of the
   file. Report those results back to the user.
