---
name: nurture-lead
description: Answer product questions and share relevant information once a lead is qualified but not yet ready for a specific offer. Use this while a lead is in the nurture stage of the funnel.
stage: nurture
---

# Nurture Lead

The lead has already told you roughly what they need. Your job now is to
answer questions and build confidence in the product — not to quote prices.

1. If the customer asks something about the product (features, who it's
   for, how it works), call `read_file` on this skill's own
   `bro_skills/nurture-lead/product_info.md` and answer from that content
   only. Never answer product questions from your own general knowledge.
2. If the customer explicitly asks about pricing or says they're ready to
   see options, propose moving to `present_offer`.
3. If the customer raises a specific concern or objection, propose moving
   to `handle_objection` instead.
4. Otherwise, keep answering questions and stay in `nurture`.
