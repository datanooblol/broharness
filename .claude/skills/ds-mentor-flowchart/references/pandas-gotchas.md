# Pandas Gotchas

Everyday pandas mistakes that aren't covered by a stats or ML course but
trip up almost every junior data scientist at some point.

## SettingWithCopyWarning

- Happens when you modify a DataFrame that pandas can't be sure is an
  independent copy vs. a view into another DataFrame -- often from
  chained indexing like `df[df.x > 0]['y'] = 1`.
- The danger isn't just the warning -- the assignment may silently fail to
  change the DataFrame you meant to change, because it modified a
  temporary view instead.
- Fix: avoid chaining; do the filter and assignment as one step with
  `.loc`, e.g. `df.loc[df.x > 0, 'y'] = 1`. If you intentionally want an
  independent copy to modify separately, make that explicit with
  `.copy()`.

## Chained indexing in general

- `df['a']['b'] = value` or `df[cond]['col']` -- each bracket access can
  return either a view or a copy depending on the DataFrame's internal
  layout, and pandas doesn't guarantee which, so the same-looking code can
  behave differently on different data.
- Prefer a single `.loc[row_selector, col_selector]` call over stacking
  multiple bracket accesses -- it's both more reliable and usually clearer
  about intent.

## Merge/join surprises

- **Row count changing unexpectedly after a merge** -- almost always means
  the join key wasn't as unique as assumed on one side, so rows fan out
  (a one-to-many or many-to-many join where one-to-one was expected).
  Check `.duplicated()` on the join key before merging if row count
  matters.
- **Silent data loss with an inner join** -- an inner join drops any row
  whose key doesn't match on the other side, with no warning. If every
  row should be kept, use `how='left'` (or `'outer'`) instead of the
  default, and check for unexpected NaNs afterward.
- **Type mismatches on the join key** (e.g. one side is a string `"1"`,
  the other an int `1`) silently produce zero matches instead of an
  error -- worth checking dtypes on both sides before merging if a join
  matches far fewer rows than expected.

## Modifying while iterating

- Looping over `.iterrows()` to build up a new column, or modifying a
  DataFrame while iterating over it, is both slow and error-prone compared
  to a vectorized operation (`df['new'] = df['a'] + df['b']`, or
  `.apply()` if the logic genuinely can't be vectorized). If code loops
  row by row to compute something, that's usually a sign there's a
  vectorized way to do the same thing.

## Silent dtype coercion

- Mixing types in a column (e.g. a numeric column that has one stray
  string value) silently turns the whole column into `object` dtype,
  which can break downstream numeric operations without an obvious error
  at the point it happened. Worth checking `.dtypes` after loading data
  from an external source, not just assuming it matches expectations.
