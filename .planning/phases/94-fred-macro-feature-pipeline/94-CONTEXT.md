# Phase 94: FRED Macro Feature Pipeline - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a FRED API data collector that fetches 14 economic time series daily, stores them in a new `feast_fred_macro` TimescaleDB table, and joins them to the per-stock training DataFrame by date. Wire into Feast as a new `fred_macro_fv` FeatureView alongside the existing `yfinance_macro_fv`. Add all 14 FRED features to `_TRAINING_FEATURES` so training and inference use the full macro context.

VIXCLS is excluded from FRED (already covered by yfinance VIX). All other 14 series from the phase goal are in scope.

</domain>

<decisions>
## Implementation Decisions

### Table Schema
- **Separate table:** `feast_fred_macro` — do not extend `feast_yfinance_macro`
- **Wide format:** one row per date, one column per FRED series (14 columns) — same pattern as `feast_yfinance_macro`
- **TimescaleDB hypertable** on `timestamp` column, same as existing macro table
- VIXCLS **dropped** from the fetch list — VIX already covered by `yfinance_macro_fv`
- 14 series to collect: DGS2, DGS10, T10Y2Y, T10Y3M, BAMLH0A0HYM2, DBAA, T10YIE, DCOILWTICO, DTWEXBGS, DEXJPUS, ICSA, NFCI, CPIAUCSL, PCEPILFE

### Gap Handling (Low-Frequency Series)
- **Forward-fill with no limit** — carry last known value indefinitely until a new reading arrives
- Applies to all series but is especially relevant for ICSA (weekly), NFCI (weekly), CPIAUCSL (monthly), PCEPILFE (monthly)
- The last macro reading IS the current reading until FRED publishes a revision — no artificial cap
- Implementation: `pandas.DataFrame.ffill()` after upserting into `feast_fred_macro` on the daily date spine

### Feast FeatureView Design
- **New `fred_macro_fv`** FeatureView registered in `feature_repo.py` alongside existing `yfinance_macro_fv`
- `PostgreSQLSource` pointing to `feast_fred_macro`, same pattern as `yfinance_macro_source`
- No entity key — date-keyed only (same as `yfinance_macro_fv`)
- **All 14 FRED features added to `_TRAINING_FEATURES`** in `data_loader.py`
- Training join pulls both `yfinance_macro_fv` and `fred_macro_fv` — combined macro context of 19 features (5 yfinance + 14 FRED)
- Inference path updated to also pull `fred_macro_fv` features from Feast online store

### CronJob + Secret Wiring
- **Add FRED fetch to existing ingestion CronJob** — no new K8s CronJob object
- **FRED_API_KEY** added to existing `stock-platform-secrets` K8s Secret, referenced via `secretKeyRef` in the CronJob pod spec
- CronJob reads `FRED_API_KEY` the same way `DATABASE_URL` and `POSTGRES_PASSWORD` are read today

### Claude's Discretion
- Exact FRED API client library (e.g. `fredapi` Python package vs direct HTTP)
- Retry/backoff strategy for FRED API rate limits
- Column naming convention for FRED series in the wide table (e.g. `dgs2`, `t10y2y`, `bamlh0a0hym2`)
- Test fixtures / mock FRED responses for RED-state TDD plan

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing macro feature pattern (Phase 93)
- `stock-prediction-platform/ml/feature_store/feature_repo.py` — Feast Entity, FeatureView, PushSource definitions; `yfinance_macro_fv` is the direct template for `fred_macro_fv`
- `stock-prediction-platform/ml/pipelines/components/data_loader.py` — `create_macro_table()`, `upsert_macro_rows()`, `_TRAINING_FEATURES` list; FRED collector must follow this exact pattern
- `stock-prediction-platform/services/api/app/services/yahoo_finance.py` — `fetch_yfinance_macro()` is the reference implementation for the FRED collector

### K8s ingestion wiring
- `stock-prediction-platform/k8s/ingestion/configmap.yaml` — existing ConfigMap for ingestion jobs; FRED env vars go here
- `stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml` — CronJob pattern reference for adding FRED fetch step
- `stock-prediction-platform/k8s/ml/cronjob-training.yaml` — shows `secretKeyRef` pattern for `DATABASE_URL`; `FRED_API_KEY` follows same pattern

### Feast offline store config
- `stock-prediction-platform/ml/feature_store/feature_store.yaml` — offline/online store backend config

### Existing tests to extend
- `stock-prediction-platform/ml/tests/test_feast_store.py` — existing Feast test patterns
- `stock-prediction-platform/ml/tests/test_data_loader.py` — existing data_loader test patterns

No external specs — requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fetch_yfinance_macro()` in `yahoo_finance.py`: direct template for `fetch_fred_macro()` — same signature, same return shape (wide DataFrame with date index)
- `create_macro_table()` + `upsert_macro_rows()` in `data_loader.py`: reuse verbatim, changing only table name and column list
- `yfinance_macro_source` + `yfinance_macro_fv` in `feature_repo.py`: copy-paste template for `fred_macro_source` + `fred_macro_fv`

### Established Patterns
- Wide-format TimescaleDB hypertable per feature group (no long/EAV format)
- `PostgreSQLSource` with raw SQL `SELECT * FROM table` for Feast offline store
- `_TRAINING_FEATURES` list in `data_loader.py` is the canonical feature registry — add `fred_macro_fv:*` columns here
- `secretKeyRef` in pod spec for secrets (see `cronjob-training.yaml`)

### Integration Points
- `data_loader.py` Step 1 already pulls `yfinance_macro_fv` via `get_historical_features()` — FRED features join at the same point
- `feast_online_service.py` → `get_online_features()` — add `fred_macro_fv` features to the online fetch for inference
- Ingestion CronJob YAML — add FRED fetch as a new step or side-effect of historical job run

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard approaches for FRED API client and column naming.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 94-fred-macro-feature-pipeline*
*Context gathered: 2026-04-04*
