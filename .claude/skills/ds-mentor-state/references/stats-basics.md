# Statistics Basics

The core ideas behind hypothesis testing and uncertainty -- the part of
statistics most junior data scientists learned once, mechanically, without
the intuition sticking.

## Hypothesis testing

- **Null hypothesis (H0)** -- the boring, default explanation: "there's no
  real effect/difference, what we're seeing is just random noise."
- **Alternative hypothesis (H1)** -- the thing you're actually trying to
  find evidence for: "there is a real effect/difference."
- **A test doesn't prove H1 true** -- it only measures how surprising the
  observed data would be *if H0 were true*. A test can reject H0 (evidence
  against "just noise") or fail to reject it (not enough evidence either
  way) -- it never "proves" the alternative.

## p-values

- A p-value is the probability of seeing a result at least this extreme
  *if the null hypothesis were actually true*. It is not the probability
  that H0 is true, and it is not the probability the result is due to
  chance -- both are common misreadings.
- A small p-value means the observed data would be unlikely under H0 --
  conventionally "significant" below some threshold (often 0.05), but that
  threshold is a convention, not a law of nature.
- **Statistical significance is not the same as practical significance.**
  With enough data, even a tiny, meaningless difference can produce a very
  small p-value. Always ask how big the effect actually is, not just
  whether it's "significant."

## Confidence intervals

- A confidence interval gives a range of plausible values for the true
  effect, not just a single number -- it communicates uncertainty that a
  bare estimate hides.
- A 95% confidence interval does **not** mean "95% probability the true
  value is in this range." It means: if you repeated the whole sampling
  process many times, about 95% of the intervals constructed that way
  would contain the true value. Subtle, but a common source of confusion.

## Choosing a test

- **t-test** -- comparing the means of two groups (e.g. does group A spend
  more than group B).
- **chi-square test** -- comparing categorical/count data (e.g. is
  purchase rate different across three marketing channels).
- **ANOVA** -- comparing means across more than two groups at once, instead
  of running many pairwise t-tests (which inflates the chance of a false
  positive somewhere just from doing many tests).

The right test depends on what kind of data you have (continuous vs
categorical) and how many groups you're comparing -- not which test sounds
most sophisticated.
