# Common Pitfalls

Practical mistakes that produce a model that looks good in development and
fails in the real world -- the symptoms and their usual causes, as opposed
to the underlying theory (see `model-basics.md` for that).

## Data leakage

- Information that wouldn't actually be available at prediction time
  leaks into training, making the model look far better than it really
  is. Classic sign: suspiciously high accuracy that doesn't hold up once
  deployed.
- Common sources: scaling/normalizing using statistics computed on the
  full dataset (including test data) instead of only training data;
  a feature that's a proxy for the target (e.g. "was this loan ever
  marked overdue" as a feature for predicting default); duplicate or
  near-duplicate rows ending up split across train and test.
- The fix is always the same shape: anything derived from data (scalers,
  encoders, imputers, feature selection) must be fit only on the training
  fold, then applied to test/validation -- never fit on the full dataset
  before splitting.

## Bad train/test splits

- **Not splitting before any data-dependent step** -- see leakage above.
- **Random splits on time-dependent data** -- if the real use case is
  predicting the future from the past, a random split lets the model
  "see" future information during training. Use a time-based split
  instead (train on earlier data, test on later data).
- **Splitting after grouping is ignored** -- if multiple rows belong to
  the same entity (e.g. many transactions from one customer), a random
  row-level split can put that entity's data in both train and test,
  inflating apparent performance. Split by entity/group, not by row.

## Imbalanced classes

- When one class is much rarer than the other (e.g. 1% fraud), a model
  can get high accuracy by mostly predicting the majority class and
  barely learning the minority class at all.
- Accuracy is the wrong metric here -- use precision/recall/F1 (see
  `metrics.md`) instead, since they don't hide poor performance on the
  rare class the way accuracy does.
- Techniques like resampling (oversampling the rare class, undersampling
  the common one) or class weighting can help, but changing the metric
  used to judge the model matters more than any resampling trick.

## Train-great, test-terrible

- The headline symptom of overfitting (see `model-basics.md` for the
  theory). Before reaching for regularization, check the boring causes
  first: is the split actually random/representative, is there leakage
  making training look artificially good, is there simply not enough
  training data for how complex the model is.
