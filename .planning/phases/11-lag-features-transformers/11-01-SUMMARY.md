# Plan 11-01 Summary: Lag Features, Rolling Stats, Target & Drop

**Status:** Complete
**Tests:** 27 passed

## What was built

### `ml/features/lag_features.py`
- `compute_lag_features(df, lags=None)` — adds `lag_close_{n}` columns for t-1, t-2, t-3, t-5, t-7, t-14, t-21
- `compute_rolling_stats(df, windows=None)` — adds `rolling_{mean,std,min,max}_{w}` for windows 5, 10, 21
- `generate_target(df, horizon=7)` — adds `target_7d` as percentage return: `(close_{t+7} - close_t) / close_t`
- `drop_incomplete_rows(df)` — drops all NaN rows (warm-up + tail), returns copy

### `ml/tests/test_lag_features.py`
- TestLagFeatures: 7 tests (columns, shift correctness, custom lags, warm-up NaNs, no look-ahead)
- TestRollingStats: 8 tests (columns, manual verification, min/max bounds, custom windows, no center bias)
- TestTarget: 7 tests (column, percentage return correctness, tail NaNs, custom horizon, no-leakage)
- TestDropIncomplete: 5 tests (no NaNs, row count, returns copy, preserves complete rows, full pipeline)

## Decisions
- Target is percentage return, not raw future close price
- Lags and rolling stats computed on `close` column only
- `dropna()` removes all NaN rows (both warm-up and forward-target tail)
