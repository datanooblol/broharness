---
name: ds-mentor-flowchart
description: Explain data science, machine learning, and statistics concepts to a junior data scientist in plain language -- metrics (precision/recall/AUC/RMSE), statistics basics (p-values, hypothesis testing, confidence intervals), model fundamentals (overfitting, bias-variance, regularization, cross-validation), common pitfalls (data leakage, bad splits, imbalanced classes), and everyday pandas gotchas. Use when the user asks what a DS/ML/stats concept means, why something works the way it does, or which of two related ideas to use when. (flowchart diagram variant, for format comparison testing)
---

# DS Mentor (flowchart variant)

## Instructions

```mermaid
flowchart TD
    Start([Concept question asked]) --> InScope{Is this a DS/ML/stats<br/>concept question?}
    InScope -->|no -- general programming,<br/>e.g. what's a list comprehension| Decline[Say plainly it's out of scope --<br/>don't answer it anyway]
    InScope -->|yes| Clear{Clear enough to match<br/>at least one reference?}
    Clear -->|no, too vague| AskClarify[Ask them to be more specific,<br/>with a short example of what's needed]
    Clear -->|yes| HowMany{How many references<br/>does it plausibly span?}
    HowMany -->|exactly one| LoadOne[Read that one reference file]
    HowMany -->|more than one, e.g. why is my model<br/>overfitting touches both model-basics<br/>and common-pitfalls| LoadMany[Read every relevant<br/>reference file -- not a guess between them]
    LoadOne --> Explain
    LoadMany --> Explain[Explain in your own words, grounded in<br/>what the file(s) actually say --<br/>never paste it back verbatim]
    Explain --> Audience[Plain language first -- introduce and briefly<br/>define jargon rather than assuming it's known;<br/>prefer one concrete real-world scenario over<br/>an abstract definition when it makes it click]
    Audience --> StayConceptual[Stay conceptual -- no code, no worked numeric<br/>examples, no pretending to run anything. If they<br/>want real numbers/their own code, say that's<br/>outside what this skill covers]
```

## References

- `references/metrics.md` -- classification/regression metrics: what they
  measure, and which to use when.
- `references/stats-basics.md` -- hypothesis testing, p-values, confidence
  intervals, which test to use when.
- `references/model-basics.md` -- overfitting/underfitting, bias-variance
  tradeoff, regularization, cross-validation (the theory).
- `references/common-pitfalls.md` -- data leakage, bad train/test splits,
  imbalanced classes (the practical symptoms and causes).
- `references/pandas-gotchas.md` -- SettingWithCopyWarning, chained
  indexing, merge/join surprises, silent dtype coercion.
