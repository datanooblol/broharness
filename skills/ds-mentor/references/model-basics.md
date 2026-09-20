# Model Basics

The core ideas behind why models fail to generalize, and the standard
tools for controlling that -- the theory side; see `common-pitfalls.md` for
the practical, "why is my model doing this" symptoms.

## Overfitting and underfitting

- **Overfitting** -- the model learned the training data too specifically,
  including its noise and quirks, so it performs well on training data but
  poorly on new data. Usually caused by a model too complex for the amount
  of data available.
- **Underfitting** -- the model is too simple to capture the real pattern
  in the data, so it performs poorly on both training and new data.
- The goal isn't "make the model as accurate as possible on training data"
  -- it's making it generalize well to data it hasn't seen. A model that's
  perfect on training data and bad on everything else has learned the
  wrong thing.

## Bias-variance tradeoff

- **Bias** -- error from a model being too simple to capture the true
  pattern (systematically wrong in the same way). High bias looks like
  underfitting.
- **Variance** -- error from a model being too sensitive to the specific
  training data it happened to see (different training sets would produce
  very different models). High variance looks like overfitting.
- These trade off against each other: making a model more flexible
  (reducing bias) usually increases variance, and vice versa. There's no
  single setting that minimizes both at once -- the goal is the best
  balance for the amount and quality of data available.

## Regularization

- A family of techniques that intentionally constrain a model to be
  simpler than it "wants" to be, to fight overfitting -- e.g. penalizing
  large coefficients in a linear model, or limiting how deep a tree can
  grow.
- More regularization pushes toward higher bias, lower variance; less
  regularization does the opposite. It's a knob, not a fix applied once
  and forgotten -- the right amount depends on the data.

## Cross-validation

- Instead of one train/test split, the data is split into several folds;
  the model trains on all but one fold and evaluates on the held-out one,
  repeated so every fold gets used for evaluation once.
- Gives a more reliable estimate of how a model will perform on new data
  than a single split, since a single split's result can be misleadingly
  good or bad just from how the data happened to be divided.
- Used to compare models/hyperparameters fairly -- picking a model because
  it happened to score well on one particular split is a common way to
  accidentally overfit to that split itself.
