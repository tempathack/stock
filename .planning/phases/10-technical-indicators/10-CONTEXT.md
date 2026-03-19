# Phase 10: Technical Indicators - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement all 14 technical indicator families (FEAT-01 through FEAT-14) as pure, testable functions in `ml/features/indicators.py`. Each function takes a pandas DataFrame with columns `open, high, low, close, volume` (single-ticker, DatetimeIndex) and returns the same DataFrame with new indicator columns appended.

Phase 9 (Kafka consumers writing OHLCV to PostgreSQL) is the upstream dependency — it provides the raw data. Phase 11 (lag features, transformers) and Phase 17 (Kubeflow pipeline) are downstream consumers.

This phase touches only `ml/features/indicators.py` (currently a stub). No database tables are created or modified. Features are computed on-the-fly from OHLCV DataFrames during the Kubeflow pipeline — no feature persistence layer for v1.

</domain>

<decisions>
## Implementation Decisions

### Library Choice
- **Hand-rolled pandas** — zero external dependencies beyond pandas/numpy (already in project)
- Standard indicator formulas are well-known and straightforward to implement with pandas rolling/ewm
- Avoids pandas-ta or TA-Lib dependency overhead
- Full control over edge case behavior and testability

### Function Signatures
- Each function: `compute_X(df: pd.DataFrame, **params) -> pd.DataFrame`
- Input: DataFrame with columns `open, high, low, close, volume` and DatetimeIndex, for a single ticker
- Output: Same DataFrame with new columns appended (mutate-and-return pattern)
- Orchestrator: `compute_all_indicators(df) -> pd.DataFrame` calls all individual functions

### Column Naming Convention
- `rsi_14` — RSI with 14-period
- `macd_line`, `macd_signal`, `macd_hist` — MACD components
- `stoch_k`, `stoch_d` — Stochastic %K and %D
- `sma_20`, `sma_50`, `sma_200` — Simple moving averages
- `ema_12`, `ema_26` — Exponential moving averages
- `adx` — Average Directional Index
- `bb_upper`, `bb_lower`, `bb_bandwidth` — Bollinger Bands
- `atr` — Average True Range
- `rolling_vol_21` — 21-day rolling volatility
- `obv` — On-Balance Volume
- `vwap` — Volume-Weighted Average Price
- `volume_sma_20` — Volume SMA
- `ad_line` — Accumulation/Distribution line
- `return_1d`, `return_5d`, `return_21d` — Percentage returns
- `log_return_1d`, `log_return_5d`, `log_return_21d` — Log returns

### NaN Handling
- Functions do NOT drop NaN rows — warm-up period NaNs are expected (e.g., RSI-14 → first 13 rows NaN)
- Downstream phases (Phase 11 FEAT-21) handle NaN dropping after target generation
- No `fillna(0)` or forward-fill applied — NaNs propagate naturally

### Input Data Source
- `ohlcv_daily` table: columns `ticker, date, open, high, low, close, volume`
- `adj_close` and `vwap` DB columns are NULL (not populated by consumer)
- VWAP indicator (FEAT-11) is computed from OHLCV data, not read from DB column
- `close` is the working price column (not `adj_close`)

### Compute Strategy
- On-the-fly computation from `ohlcv_daily` DataFrames during Kubeflow pipeline
- No feature persistence table for v1
- Each function is idempotent — calling it twice on the same DataFrame appends the same columns

### Claude's Discretion
- Exact formula variations for edge cases (e.g., Wilder's vs standard EMA smoothing for RSI)
- Whether to use `pd.Series` return type for individual indicators or always return full DataFrame
- Internal helper functions for shared computations (e.g., true range shared by ATR and ADX)
- Test data generation strategy (synthetic or hardcoded reference values)
- Whether `compute_all_indicators` validates input columns before proceeding

</decisions>

<canonical_refs>
## Canonical References

### Target file (stub to implement)
- `stock-prediction-platform/ml/features/indicators.py` — all indicator functions go here

### Input schema (from db/init.sql)
```sql
CREATE TABLE IF NOT EXISTS ohlcv_daily (
    ticker     VARCHAR(10)   NOT NULL REFERENCES stocks(ticker),
    date       DATE          NOT NULL,
    open       NUMERIC(12,4),
    high       NUMERIC(12,4),
    low        NUMERIC(12,4),
    close      NUMERIC(12,4),
    adj_close  NUMERIC(12,4),
    volume     BIGINT,
    vwap       NUMERIC(12,4),
    PRIMARY KEY (ticker, date)
);
```

### Related stubs (Phase 11, not this phase)
- `stock-prediction-platform/ml/features/lag_features.py` — lag features (Phase 11)
- `stock-prediction-platform/ml/features/transformations.py` — scaler pipelines (Phase 11)

### Downstream consumer (Phase 17)
- `stock-prediction-platform/ml/pipelines/components/feature_engineer.py` — calls `compute_all_indicators()`

</canonical_refs>
