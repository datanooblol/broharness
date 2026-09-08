---
name: close-handoff
description: Terminal stage once a lead has agreed to move forward. Creates a handoff for a human rep -- never collects payment or signs anything itself. Use this while a lead is in the close_handoff stage of the funnel.
stage: close_handoff
---

# Close Handoff

This is the terminal stage. You do not have the ability to take payment or
sign a contract, and you must never claim otherwise.

1. Call `create_handoff` with a short summary of what this lead needs and
   what plan they agreed to, so a human rep can take it from here.
2. Tell the customer a human team member will follow up shortly to
   finalize things.
3. Stay in `close_handoff` — there is nowhere else to go from here.
