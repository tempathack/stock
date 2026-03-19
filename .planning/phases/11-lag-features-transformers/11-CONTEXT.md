# Phase 11: Lag Features & Transformer Pipelines - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement lag features, rolling window statistics, target label generation, row cleanup, and three sklearn scaler pipeline variants. All code lives in `ml/features/lag_features.py` and `ml/features/transformations.py` (both currently stubs). Phase 10 (technical indicators) is the upstream dependency — it provides `compute_all_indicators()`. Phase 12+ (model training) is the downstream consumer.

This phase touches:
- `ml/features/lag_features.py` — lag features, rolling stats, target generation, row dropping
- `ml/features/transformations.py` — scaler pipeline factory
- `ml/features/__init__.py` — export new public functions
- `ml/tests/test_lag_features.py` — new test file
- `ml/tests/test_transformations.py` — new test file

</domain>

<decisions>
## Implementation Decisions

### Lag Features (FEAT-15)
- Lags on `close` column only: t-1, t-2, t-3, t-5, t-7, t-14, t-21
- Column naming: `lag_close_1`, `lag_close_2`, ..., `lag_close_21`
- Implementation: `df["close"].shift(n)` — no look-ahead by construction

### Rolling Window Stats (FEAT-16)
- Stats: mean, std, min, max over 5, 10, 21-day windows
- Applied to `close` column only (consistent with requirements)
- Column naming: `rolling_mean_5`, `rolling_std_5`, `rolling_min_5`, `rolling_max_5`, etc.
- No `center=True` — only trailing windows to prevent look-ahead

### Scaler Pipelines (FEAT-17/18/19)
- Factory function `build_scaler_pipeline(variant: str) -> sklearn.pipeline.Pipeline`
- Three variants: "standard", "quantile", "minmax"
- Each returns `Pipeline([("scaler", ScalerInstance)])`
- QuantileTransformer uses `output_distribution="normal"` for regression compatibility
- Model step appended later in Phase 12 — pipeline here is scaler-only
- Target column excluded from scaling (caller responsibility enforced by convention)

### Target Label (FEAT-20)
- **Percentage return** target: `target_7d = (close_t+7 - close_t) / close_t`
- Implementation: `df["close"].pct_change(7).shift(-7)` or equivalent
- Strict no-leakage: target uses `.shift(-7)` (future data), never leaks into features

### Row Dropping (FEAT-21)
- `df.dropna()` after all features + target computed
- Drops both warm-up NaN rows (first ~21 from lag/rolling) and tail NaN rows (last 7 from target)
- Returns clean, fully-populated DataFrame ready for model training

### NaN Handling
- Individual functions (lag, rolling) do NOT drop NaNs — consistent with Phase 10 pattern
- Only the explicit `drop_incomplete_rows()` function performs the final cleanup

### Function Signatures
- `compute_lag_features(df, lags=None) -> pd.DataFrame`
- `compute_rolling_stats(df, windows=None) -> pd.DataFrame`
- `generate_target(df, horizon=7) -> pd.DataFrame`
- `drop_incomplete_rows(df) -> pd.DataFrame`
- `build_scaler_pipeline(variant) -> Pipeline`

</decisions>

<canonical_refs>
## Canonical References

### Target files (stubs to implement)
- `stock-prediction-platform/ml/features/lag_features.py`
- `stock-prediction-platform/ml/features/transformations.py`

### Upstream (Phase 10, complete)
- `stock-prediction-platform/ml/features/indicators.py` — all 14 indicator functions
- `stock-prediction-platform/ml/features/__init__.py` — exports `compute_all_indicators`

### Test infrastructure
- `stock-prediction-platform/ml/tests/conftest.py` — `sample_ohlcv_df` fixture (250 rows)
- `stock-prediction-platform/ml/tests/pytest.ini` — test config

### Downstream consumers (future phases)
- `stock-prediction-platform/ml/pipelines/components/feature_engineer.py` — Kubeflow component
- `stock-prediction-platform/ml/pipelines/components/label_generator.py` — Kubeflow component

</canonical_refs>
