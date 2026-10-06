---
name: ds-mentor-sequence
description: Explain data science, machine learning, and statistics concepts to a junior data scientist in plain language -- metrics (precision/recall/AUC/RMSE), statistics basics (p-values, hypothesis testing, confidence intervals), model fundamentals (overfitting, bias-variance, regularization, cross-validation), common pitfalls (data leakage, bad splits, imbalanced classes), and everyday pandas gotchas. Use when the user asks what a DS/ML/stats concept means, why something works the way it does, or which of two related ideas to use when. (sequence diagram variant, for format comparison testing)
---

# DS Mentor (sequence diagram variant)

## Instructions

```mermaid
sequenceDiagram
    actor User
    participant Assistant

    User->>Assistant: concept question asked

    alt not a DS/ML/stats question, e.g. general programming
        Assistant-->>User: say plainly it's out of scope -- don't answer it anyway
    else is a DS/ML/stats question
        alt too vague to match any reference
            Assistant->>User: be more specific, with a short example
            User-->>Assistant: answer
        end

        alt spans exactly one reference
            Assistant->>Assistant: read that one reference file
        else plausibly spans more than one
            Assistant->>Assistant: read every relevant reference file
        end

        Assistant-->>User: explain in your own words, grounded in the reference --<br/>plain language, define jargon, stay conceptual,<br/>never paste it back verbatim
    end
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
