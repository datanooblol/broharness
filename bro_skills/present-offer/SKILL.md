---
name: present-offer
description: Recommend a specific plan and price once a lead understands the product and is evaluating options. Use this while a lead is in the present_offer stage of the funnel.
stage: present_offer
---

# Present Offer

Recommend the plan (`starter`, `pro`, or `enterprise`) that best fits what
you know about this lead.

1. Always call `get_pricing` for the plan you're about to recommend before
   stating a price. Never state a price from memory or invent a discount —
   if `get_pricing` doesn't have what the customer is asking for (e.g. a
   custom discount), say so plainly and defer to a human rather than
   making up a number.
2. If the customer pushes back on price or fit, propose moving to
   `handle_objection`.
3. If the customer clearly agrees to move forward, propose moving to
   `close_handoff` — you cannot close the deal yourself, only hand off to a
   human rep.
4. Otherwise stay in `present_offer`.
