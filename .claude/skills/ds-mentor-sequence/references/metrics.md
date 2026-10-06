# Metrics

How to pick and interpret the metrics used to judge a model. The right
metric depends on the problem, not personal preference -- the wrong choice
can make a bad model look good.

## Classification

- **Accuracy** -- fraction of predictions that were correct. Misleading on
  imbalanced data: a model that always predicts "not fraud" can be 99%
  accurate if fraud is rare, while being useless.
- **Precision** -- of everything predicted positive, how much actually was.
  Matters when a false positive is costly (e.g. flagging a legitimate
  transaction as fraud and blocking a real customer).
- **Recall** -- of everything actually positive, how much was caught.
  Matters when a false negative is costly (e.g. missing an actual fraud
  case, or a cancer diagnosis).
- **Precision and recall trade off against each other** -- making a model
  more cautious about predicting positive raises precision but usually
  lowers recall, and vice versa. There's rarely a free win on both.
- **F1 score** -- the harmonic mean of precision and recall, used when both
  matter and neither should be optimized at the other's expense.
- **AUC-ROC** -- measures how well a model ranks positives above negatives
  across every possible decision threshold, not just one. Useful for
  comparing models independent of where the threshold ends up being set.
  Less meaningful on severely imbalanced data than precision/recall.

## Regression

- **MAE (mean absolute error)** -- average size of the error, in the
  original units. Easy to explain to a non-technical audience, treats
  every error the same size regardless of direction.
- **RMSE (root mean squared error)** -- also in the original units, but
  squares errors before averaging, so large errors are punished
  disproportionately more than small ones. Use when big mistakes are much
  worse than small ones (e.g. wildly underpricing a house is worse than
  being off by a little on many houses).
- **R^2** -- fraction of the variance in the target the model explains.
  Useful for a quick sense of overall fit, but doesn't say anything about
  whether errors are evenly spread or concentrated in a few bad cases.

## Picking one

Ask what a wrong prediction actually costs in the real situation -- that
determines whether false positives or false negatives matter more (for
classification) or whether large errors should be punished harder than
small ones (for regression). The "best" metric is the one that reflects
that cost, not the one with the highest number.
