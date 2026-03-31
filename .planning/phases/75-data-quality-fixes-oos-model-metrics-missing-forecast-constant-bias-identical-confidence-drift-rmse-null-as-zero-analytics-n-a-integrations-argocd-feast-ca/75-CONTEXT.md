# Phase 75: Data Quality Fixes — Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 4 data quality bugs across the existing platform — no new features, all existing pages showing wrong or missing data:
1. Models page OOS metrics (RMSE, MAE, R², MAPE, Directional Accuracy) are blank/missing
2. Forecasts page shows identical 0.93 confidence and ~-6.8% return for every stock
3. Drift page renders null previous-model RMSE as 0.0000
4. Analytics page SystemHealthSummary shows N/A for ArgoCD sync, Feast Latency p99, and CA Last Refresh

Retraining models, adding new pages, and adding new metrics are out of scope.

</domain>

<decisions>
## Implementation Decisions

### OOS Metrics Missing
- Root cause is unknown — phase must start with a diagnostic: query the DB (`model_registry`) directly to check whether `oos_metrics` is populated for existing trained models
- Fix wherever the gap is found: if DB is empty (ML pipeline never wrote them), write a backfill script; if API mapping is wrong, fix the endpoint; if frontend rendering is broken, fix the display
- All 5 metrics must be present: RMSE, MAE, R², MAPE, Directional Accuracy — these are the metrics defined in REQUIREMENTS.md

### Forecast Constant Bias
- Root cause is unknown — phase must investigate: check what the `/predict/bulk` or `/forecasts` API endpoint actually returns, and whether the DB `predictions` table has varied values per ticker or a single repeated row
- If the model is producing constant predictions (degenerate model): fix the confidence calculation formula — confidence is likely derived from model score and shouldn't be identical across all tickers. Do NOT retrain the model in this phase.
- If the API has a bug (returning one ticker's prediction for all): fix the query/mapping in `prediction_service.py`
- Frontend mock fallback should remain as-is (seeded RNG producing varied values) — it's already correct

### Analytics Integrations (N/A → real values)
- All three services are confirmed running in Minikube: ArgoCD, Feast, TimescaleDB continuous aggregates
- **ArgoCD sync status**: Read from K8s Application CRD `.status.sync.status` — the `flink_service.py` backend already calls the K8s API, extend that pattern. Do NOT call the ArgoCD REST API directly.
- **Feast Latency p99**: Measure by timing a live `get_online_features()` call from the API. Do NOT scrape Prometheus. Return the round-trip time in ms.
- **CA Last Refresh**: Already partially wired in `flink_service.py:85` — verify it reads from TimescaleDB's continuous aggregate materialization timestamp. Fix if broken.

### Drift RMSE null→0
- Change `?? 0` to `?? null` in `Drift.tsx:75` (previous model RMSE fallback)
- Display `—` (em-dash) in the UI when previous model RMSE is null — consistent with the pattern used elsewhere in the platform for missing numeric data
- Also verify the DB: check `drift_logs` table to confirm whether `previous_model` RMSE is actually stored there. If it's not being written by the drift detection service, fix the writer too.

### Claude's Discretion
- Exact SQL diagnostic queries for the OOS metrics investigation
- Whether to use a migration script or a one-off backfill approach for OOS data
- Caching strategy for the Feast latency measurement (avoid timing on every request)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Models / OOS metrics
- `stock-prediction-platform/services/api/app/services/prediction_service.py` — OOS metrics mapping, `oos_metrics` dict construction (lines ~818–830)
- `stock-prediction-platform/services/api/app/routers/models.py` — `/models/comparison` endpoint, OOS query (line ~137)
- `stock-prediction-platform/services/frontend/src/components/tables/ModelComparisonTable.tsx` — OOS metrics display in models table
- `stock-prediction-platform/services/frontend/src/components/tables/ModelDetailPanel.tsx` — OOS metrics display in detail panel
- `stock-prediction-platform/services/frontend/src/api/types.ts` — `oos_metrics` type definition (line 54, 104)

### Forecast bias
- `stock-prediction-platform/services/api/app/services/prediction_service.py` — prediction query and confidence calculation
- `stock-prediction-platform/services/frontend/src/utils/mockForecastData.ts` — mock data generator (seeded RNG, reference for expected varied output)
- `stock-prediction-platform/services/frontend/src/api/queries.ts` — forecast API query hooks

### Analytics integrations
- `stock-prediction-platform/services/api/app/routers/analytics.py` — `/analytics/summary` endpoint
- `stock-prediction-platform/services/api/app/services/flink_service.py` — existing ArgoCD K8s API call pattern (lines 53–94), CA last refresh query (line 73–87)
- `stock-prediction-platform/services/frontend/src/components/analytics/SystemHealthSummary.tsx` — renders ArgoCD, Feast, CA values
- `stock-prediction-platform/services/api/app/services/feast_service.py` — existing Feast service (extend for latency measurement)

### Drift RMSE fix
- `stock-prediction-platform/services/frontend/src/pages/Drift.tsx` — null fallback bug at line 75 (`?? 0`)
- `stock-prediction-platform/services/frontend/src/utils/mockDriftData.ts` — mock drift data reference

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `flink_service.py` K8s API call pattern: already calls Kubernetes API for ArgoCD CRD status — extend this for the ArgoCD fix rather than writing new K8s client code
- `feast_service.py`: existing Feast service — add a `measure_online_latency()` function here
- `mockForecastData.ts`: seeded RNG produces varied per-ticker values — useful as a reference for what "correct" varied output looks like
- `SystemHealthSummary.tsx`: already handles `null` gracefully with `?? "N/A"` — Feast and CA values just need real data from the API

### Established Patterns
- Null display: existing components use `?? "N/A"` (string) for missing data in SystemHealthSummary, and numeric displays should use `?? null` + `—` rendering (consistent with Phase 74 pattern)
- API caching: `analytics.py` uses a `build_key` cache pattern — Feast latency should use the same pattern (cache for ~60s to avoid timing every request)
- Diagnostic-first: Phase 75 has 2 unknown root causes (OOS metrics, forecast bias) — plans should include a diagnostic step before jumping to fixes

### Integration Points
- `prediction_service.py` → `model_registry` table: OOS metrics are stored in a `metrics_json` JSONB column
- `drift_logs` table: `previous_model` and associated RMSE fields — need to verify schema
- ArgoCD Application CRD: `status.sync.status` field in the `argocd` namespace

</code_context>

<specifics>
## Specific Ideas

- Drift null fix is a single-line change (`?? 0` → `?? null`) but also needs a DB verification step — don't just fix the display
- Forecast bias investigation: check if `predictions` table has rows per ticker or a single repeated row — `SELECT DISTINCT ticker, confidence, expected_return FROM predictions LIMIT 20` will reveal it quickly
- Analytics Feast latency: cache the timing result for ~60 seconds (same pattern as other analytics endpoints) so it doesn't add latency to every page load

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 75-data-quality-fixes*
*Context gathered: 2026-03-31*
