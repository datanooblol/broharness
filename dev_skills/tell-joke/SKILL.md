---
name: tell-joke
description: Tell a joke. Use when the user asks for a joke, wants to be entertained, or needs a laugh.
---

# Tell Joke

This skill's own `references/` folder holds a few joke categories, one file
each. When asking the read-file action to load one, use the full path
from the repo root, exactly as written here:

- `dev_skills/tell-joke/references/dad-jokes.md`
- `dev_skills/tell-joke/references/puns.md`
- `dev_skills/tell-joke/references/knock-knock.md`

When invoked:

1. Pick whichever category best matches what the user asked for ("tell me
   a pun" -> puns; "got a dad joke?" -> dad-jokes; nothing specific ->
   pick one at random).
2. Read that one reference file (via the read-file action, using its full
   path exactly as listed above) to see what's available in it. Don't
   read all three -- only the one you picked.
3. Tell exactly ONE joke from that file, in your own words. Don't paste
   the whole file back.
4. Keep it short and don't explain the joke afterward -- a joke that needs
   explaining isn't funny.
