# Phase 92: Feast-Powered Prediction Pipeline - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Retrain the ML model on Feast-materialized features (OHLCV technical indicators + Flink real-time indicators + Reddit sentiment scores) and replace the current `_legacy_inference()` path (Postgres → local indicator compute) with Feast online store feature retrieval at prediction time. This makes sentiment and streaming features available at inference for the first time.

Scope is limited to: training pipeline Feast integration, model retraining, inference path switchover via feature flag, and fallback strategy. No new frontend pages. No new Feast feature views — use existing push sources from `feast_writer` and `sentiment_writer`.

</domain>

<decisions>
## Implementation Decisions

### Feature Set Scope
- Use **all available Feast features**: OHLCV technical indicators (from `feast_writer` Flink job) + Reddit sentiment scores (`positive_ratio`, `negative_ratio`, `avg_sentiment`, `mention_count` from `sentiment_writer`)
- Horizon target unchanged: t+7 price return
- **Entity key**: ticker-only for online inference (latest features); ticker + date for offline training (historical point-in-time joins)
- At inference time, use latest available online features regardless of staleness — add `feature_freshness_seconds` field to `PredictionResponse` for observability
- Point-in-time join at training time uses existing `pit_validator.py` logic

### Training Pipeline Feast Integration
- Replace **`data_loader` step (step 1)** of the 11-step Kubeflow pipeline — instead of querying `ohlcv_daily` and computing indicators locally, pull historical feature dataset from Feast offline store via `get_historical_features()`
- Offline store: **PostgreSQL** (already configured in `ml/feature_store/feature_repo.py`)
- All downstream pipeline steps (label generation, CV, training, evaluation, winner selection) remain unchanged
- **Retrain from scratch** — do not fine-tune existing winner; the new feature distribution (with sentiment) warrants full retraining across all model families
- After winner selection, serialize Feast feature view column names to `features.json` alongside `pipeline.pkl` — this becomes the canonical feature list for inference

### Inference Path Switchover
- Add **`FEAST_INFERENCE_ENABLED: bool = False`** to `config.py`
- When `True`: call Feast online store via the existing `get_online_features_for_ticker()` stub (rewritten — see below), align to `features.json`, pass to `pipeline.predict()`
- When `False`: fall back to current `_legacy_inference()` — existing behavior unchanged
- **Rewrite `get_online_features_for_ticker()`** (currently at `prediction_service.py:943`, defined but never called) to pull all Feast feature view columns, handle missing features gracefully, and return a DataFrame aligned to `features.json`
- Do NOT call KServe in this path — `FEAST_INFERENCE_ENABLED` and `KSERVE_ENABLED` are independent flags

### Fallback Strategy
- If Feast online store is unavailable OR feature timestamp is older than **10 minutes**: fall back to `_legacy_inference()` automatically
- 10-minute threshold matches Flink checkpoint interval
- Log fallback reason (`feast_unavailable` / `feast_stale`) and emit `feast_stale_features_total` Prometheus counter
- Fallback must be silent to the caller — `PredictionResponse` format unchanged

### Claude's Discretion
- Exact Feast SDK call pattern (`get_online_features` vs `store.get_online_features` vs entity rows format)
- How to handle tickers with no sentiment data in Feast (fill with 0.0 or feature mean)
- Alembic migration needs (if any new tables required)
- Whether to add Feast feature freshness to Grafana dashboard

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Feast infrastructure
- `ml/feature_store/feature_repo.py` — Feast feature repo definition, push sources, feature views, entity definitions
- `ml/feature_store/pit_validator.py` — Point-in-time join validation logic (used in training)
- `services/api/app/services/feast_service.py` — Existing Feast read patterns used in /market route
- `services/api/app/services/feast_online_service.py` — `get_sentiment_features()` and other Feast online read helpers

### Current prediction path (what we're replacing)
- `services/api/app/services/prediction_service.py` — `_legacy_inference()` (lines ~556-719), `get_online_features_for_ticker()` stub (line ~943)
- `services/api/app/routers/predict.py` — Router entry point, fallback chain, response model
- `services/api/app/config.py` — Existing feature flags (`KSERVE_ENABLED`, `AB_TESTING_ENABLED`)

### Training pipeline (what we're modifying)
- `ml/pipelines/training_pipeline.py` — 11-step pipeline, step 1 is `data_loader`
- `ml/pipelines/components/data_loader.py` — Current Postgres-based data loading (to be replaced with Feast offline)
- `ml/pipelines/components/deployer.py` — Writes `pipeline.pkl` and `features.json` to serving dir

### Flink feature producers (what feeds Feast)
- `services/flink-jobs/feast_writer/feast_writer.py` — OHLCV indicator features pushed to Feast
- `services/flink-jobs/sentiment_writer/sentiment_writer.py` — Reddit sentiment features pushed to Feast

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_online_features_for_ticker()` at `prediction_service.py:943` — already defined, never called; rewrite this rather than adding a new function
- `feast_online_service.py:get_sentiment_features()` — pattern for reading Feast online store; reuse call pattern in the prediction path
- `pit_validator.py` — use for training-time point-in-time join validation
- `ml/pipelines/components/deployer.py` — already writes `features.json`; extend to write Feast feature names

### Established Patterns
- Feature flag pattern: `settings.KSERVE_ENABLED` in `prediction_service.py` → mirror exactly for `FEAST_INFERENCE_ENABLED`
- Fallback chain in `routers/predict.py`: live inference → file cache → DB predictions; Feast fallback should happen inside `_legacy_inference` replacement, not as a new chain layer
- Prometheus metrics in `services/api/app/metrics.py` — add `feast_stale_features_total` counter here
- `features.json` is written by `deployer.py` and read in `_legacy_inference` at line ~617; same read pattern works for Feast-trained model

### Integration Points
- `prediction_service.py:get_live_prediction()` — branch point; add third branch for `FEAST_INFERENCE_ENABLED`
- `ml/pipelines/components/data_loader.py` — step 1 of training pipeline; replace Postgres query with Feast `get_historical_features()` call
- `services/api/app/config.py` — add `FEAST_INFERENCE_ENABLED: bool = False`
- `k8s/ml/configmap.yaml` — add `FEAST_INFERENCE_ENABLED` env var (default `"false"`)

</code_context>

<specifics>
## Specific Ideas

- The audit revealed `get_online_features_for_ticker()` at `prediction_service.py:943` was built for exactly this purpose but never wired in — the phase is essentially completing the intended architecture
- Feast is already receiving features from both Flink writers; no new feature engineering required, just consume what's already materializing
- `feature_freshness_seconds` in the response gives the frontend (future phase) visibility into how fresh the prediction features are

</specifics>

<deferred>
## Deferred Ideas

- Surfacing `feature_freshness_seconds` in the frontend prediction UI — future phase
- Adding Feast feature staleness panel to Grafana — could be a small add-on phase or done within phase 92 at Claude's discretion
- Extending Feast feature set with new feature views (e.g., fundamentals, earnings) — separate phase
- A/B testing old vs new model (OHLCV-only vs OHLCV+sentiment) — could use existing `AB_TESTING_ENABLED` flag in a future phase

</deferred>

---

*Phase: 92-feast-powered-prediction-pipeline*
*Context gathered: 2026-04-03*
