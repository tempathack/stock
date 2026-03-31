# Phase 75: Data Quality Fixes — Research

**Researched:** 2026-03-31
**Domain:** Bug fixing — FastAPI backend services, React/TypeScript frontend, PostgreSQL schema diagnostics
**Confidence:** HIGH (all findings verified directly from source code, no external library research needed)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**OOS Metrics Missing**
- Root cause is unknown — phase must start with a diagnostic: query the DB (`model_registry`) directly to check whether `oos_metrics` is populated for existing trained models
- Fix wherever the gap is found: if DB is empty (ML pipeline never wrote them), write a backfill script; if API mapping is wrong, fix the endpoint; if frontend rendering is broken, fix the display
- All 5 metrics must be present: RMSE, MAE, R², MAPE, Directional Accuracy

**Forecast Constant Bias**
- Root cause is unknown — phase must investigate: check what the `/predict/bulk` or `/forecasts` API endpoint actually returns, and whether the DB `predictions` table has varied values per ticker or a single repeated row
- If the model is producing constant predictions (degenerate model): fix the confidence calculation formula — do NOT retrain the model in this phase
- If the API has a bug (returning one ticker's prediction for all): fix the query/mapping in `prediction_service.py`
- Frontend mock fallback should remain as-is (seeded RNG producing varied values)

**Analytics Integrations (N/A → real values)**
- All three services are confirmed running in Minikube: ArgoCD, Feast, TimescaleDB continuous aggregates
- **ArgoCD sync status**: Read from K8s Application CRD `.status.sync.status` — the `flink_service.py` backend already calls the K8s API, extend that pattern. Do NOT call the ArgoCD REST API directly.
- **Feast Latency p99**: Measure by timing a live `get_online_features()` call from the API. Do NOT scrape Prometheus. Return the round-trip time in ms.
- **CA Last Refresh**: Already partially wired in `flink_service.py:85` — verify it reads from TimescaleDB's continuous aggregate materialization timestamp. Fix if broken.

**Drift RMSE null→0**
- Change `?? 0` to `?? null` in `Drift.tsx:75` (previous model RMSE fallback)
- Display `—` (em-dash) in the UI when previous model RMSE is null
- Also verify the DB: check `drift_logs` table to confirm whether `previous_model` RMSE is actually stored there. If it's not being written by the drift detection service, fix the writer too.

### Claude's Discretion
- Exact SQL diagnostic queries for the OOS metrics investigation
- Whether to use a migration script or a one-off backfill approach for OOS data
- Caching strategy for the Feast latency measurement (avoid timing on every request)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 75 fixes four distinct data quality bugs. None require new pages, new models, or schema changes — they are display/pipeline/mapping bugs in existing code. Two bugs (OOS metrics, forecast bias) require a diagnostic step before the fix can be written; two bugs (Drift RMSE null, Analytics N/A) have fully understood root causes with prescribed fixes.

**Bug 1 — OOS Metrics Missing:** The API mapping at `prediction_service.py:157` strips the `oos_` prefix when building the `oos_metrics` dict. The frontend tables (`ModelComparisonTable.tsx`) then look for keys `rmse`, `mae`, `r2`, `mape`, `directional_accuracy` inside `oos_metrics`. If the `metrics_json` column in `model_registry` does not contain `oos_rmse`, `oos_mae`, etc., the dict will be empty after stripping. The diagnostic must check whether the ML pipeline actually writes those keys.

**Bug 2 — Forecast Constant Bias:** The DB `predictions` table has a single `confidence NUMERIC(5,4)` column — no per-ticker variation is enforced at the schema level. The `load_db_predictions` function reads it directly from the DB. The investigation must check whether all rows in the latest batch have identical `confidence` and `predicted_price` values.

**Bug 3 — Drift RMSE null→0:** The `drift_logs` table schema (`details_json JSONB`) does not have a dedicated `previous_model_rmse` column — any previous-model RMSE must live inside `details_json`. The `Drift.tsx` line 75 reads from `d.oos_metrics?.oos_rmse` (current model) with `?? 0`, not from previous-model RMSE. The frontend at line 70 hard-codes `rmse: 0` for the old model regardless. Two separate fixes needed: frontend `?? 0` → `?? null` and a check on whether drift detector writes previous-model RMSE to `details_json`.

**Bug 4 — Analytics N/A:** `flink_service.py` has the ArgoCD branch using `ARGOCD_TOKEN` (currently empty `""`), making it always skip. The decision is to switch to reading the K8s Application CRD instead. Feast latency is hard-coded to `None` at line 93 (`feast_online_latency_ms=None`). CA last refresh is wired at lines 73–87 but may fail silently if the TimescaleDB view name differs.

**Primary recommendation:** Execute diagnostics for bugs 1 and 2 first (SQL queries), then apply fixes in dependency order: (1) drift display fix — 1 line, (2) analytics integrations — 3 additions to `flink_service.py`, (3) OOS metrics — depends on diagnostic outcome, (4) forecast bias — depends on diagnostic outcome.

---

## Standard Stack

### Core (already in the project — no new dependencies)
| Library | Purpose | Location |
|---------|---------|---------|
| SQLAlchemy async | DB queries | `app/models/database.py` |
| FastAPI / httpx | API layer | `app/routers/`, `app/services/` |
| kubernetes Python client | K8s API access | needs verification — see below |
| React Query / MUI | Frontend display | `src/api/queries.ts`, MUI components |
| pytest / pytest-asyncio | Test framework | `services/api/tests/` |

### New Dependency: kubernetes Python client
The CONTEXT.md decision says to read ArgoCD status from the K8s Application CRD (not the ArgoCD REST API). The current `flink_service.py` does NOT use the kubernetes Python client — it calls the ArgoCD REST API via `httpx`. The new implementation must either:

1. Use the `kubernetes` Python client (`pip install kubernetes`) to call the K8s API server directly for the ArgoCD Application CRD, OR
2. Change the environment: inject an `ARGOCD_TOKEN` into the API pod so the existing REST-API branch works.

**Recommended (per CONTEXT.md decision):** Use the kubernetes Python client to read the CRD. The `kubernetes` package supports in-cluster config (`kubernetes.config.load_incluster_config()`) for pods running inside Minikube. It can list custom resources via `client.CustomObjectsApi().list_namespaced_custom_object(group="argoproj.io", version="v1alpha1", namespace="argocd", plural="applications")`.

Check if already installed:
```bash
grep -r "kubernetes" stock-prediction-platform/services/api/requirements*.txt
```

### Supporting Libraries (already in project)
| Library | Purpose |
|---------|---------|
| `time` (stdlib) | Feast latency timing — `time.perf_counter()` |
| `asyncio` (stdlib) | Async execution in `flink_service.py` |
| `sqlalchemy.text` | Raw SQL queries for diagnostic steps |

---

## Architecture Patterns

### Established Patterns (from codebase — HIGH confidence)

#### Pattern 1: DB-first with file fallback
```python
# From prediction_service.py — used everywhere
raw = await load_X_from_db()
if raw is None:
    raw = load_X_from_file(...)
```

#### Pattern 2: Cache wrapping analytics endpoints
```python
# From analytics.py — use same pattern for Feast latency
key = build_key("analytics", "summary")
cached = await cache_get(key)
if cached is not None:
    return AnalyticsSummaryResponse(**cached)
result = await get_analytics_summary()
await cache_set(key, result.model_dump(), ANALYTICS_SUMMARY_TTL)  # 30s
```
For Feast latency: cache for ~60 seconds. Use `build_key("analytics", "feast", "latency")`.

#### Pattern 3: OOS metrics key mapping
```python
# prediction_service.py line 157-159 — strips "oos_" prefix
"oos_metrics": {
    k[4:]: v for k, v in metrics.items()
    if k.startswith("oos_")
},
```
This means `model_registry.metrics_json` must contain: `oos_rmse`, `oos_mae`, `oos_r2`, `oos_mape`, `oos_directional_accuracy`. The frontend tables expect the stripped form: `rmse`, `mae`, `r2`, `mape`, `directional_accuracy`.

The frontend sort also uses `metrics_json->>'oos_rmse'` in the SQL ORDER BY — consistent with this key naming.

#### Pattern 4: Null display
- `ModelComparisonTable.tsx` and `ModelDetailPanel.tsx` both use `fmt(value, N)` which returns `"—"` when `!Number.isFinite(n)` — already handles null correctly once the data arrives
- `SystemHealthSummary.tsx` uses `?? "N/A"` for string fields
- `Drift.tsx` must change `?? 0` → `?? null` for the numeric RMSE field

#### Pattern 5: Feast latency measurement
The `feast_service.py` has `get_online_features` available via import from `ml.features.feast_store`. To measure p99 latency, time a single call:
```python
import time
start = time.perf_counter()
get_online_features(some_ticker)
elapsed_ms = (time.perf_counter() - start) * 1000
```
This is a point measurement (single call), not a true p99. The CONTEXT.md decision accepts this — "return the round-trip time in ms". The result should be cached ~60s to avoid adding latency on every page load.

#### Pattern 6: K8s CRD access (new for Phase 75)
```python
from kubernetes import client as k8s_client, config as k8s_config

def _get_argocd_sync_via_k8s() -> str | None:
    try:
        try:
            k8s_config.load_incluster_config()  # inside K8s pod
        except k8s_config.ConfigException:
            k8s_config.load_kube_config()       # local dev / tests
        api = k8s_client.CustomObjectsApi()
        apps = api.list_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="argocd",
            plural="applications",
        )
        statuses = [
            item.get("status", {}).get("sync", {}).get("status", "Unknown")
            for item in apps.get("items", [])
        ]
        return "OutOfSync" if "OutOfSync" in statuses else "Synced"
    except Exception:
        return None
```
This replaces the `httpx` + `ARGOCD_TOKEN` branch. The function should be sync (kubernetes client is sync by default) and called with `asyncio.to_thread()` from the async `get_analytics_summary`.

### Anti-Patterns to Avoid
- **Scraping Prometheus for Feast latency:** CONTEXT.md explicitly forbids this. Use `time.perf_counter()`.
- **Calling the ArgoCD REST API directly:** CONTEXT.md explicitly forbids this. Use the K8s CRD.
- **Retraining models to fix constant bias:** Out of scope. Only fix the confidence calculation or the query mapping.
- **Fixing just the display for OOS/drift without checking the DB write path:** Both bugs require DB verification, not display-only fixes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| K8s CRD reading | Custom HTTP client to K8s API | `kubernetes` Python package |
| Async timing | Complex wrapper | `time.perf_counter()` — stdlib, 1 line |
| Feast online fetch | New Feast client | Existing `feast_service.py` `get_online_features` |
| Cache TTL management | Custom expiry logic | Existing `cache_get`/`cache_set`/`build_key` in `app/cache.py` |

---

## Common Pitfalls

### Pitfall 1: OOS metrics key name mismatch
**What goes wrong:** The ML pipeline might write keys like `rmse`, `mae` (no `oos_` prefix) to `metrics_json`. The API strips the `oos_` prefix and filters by `k.startswith("oos_")` — so unprefixed keys yield an empty dict.
**Why it happens:** The ML training code may have been written before the `oos_` prefix convention was established.
**How to avoid:** Run the diagnostic query first: `SELECT metrics_json FROM model_registry LIMIT 3` and inspect actual key names.
**Warning signs:** Empty `oos_metrics` dict in the API response but non-empty `metrics_json` in the DB.

### Pitfall 2: Forecast constant bias — wrong layer
**What goes wrong:** Assuming the bug is in the frontend when it's actually in the DB/pipeline, or vice versa.
**Why it happens:** The API reads directly from the DB (`load_db_predictions`), so if the DB has a single repeated row or all-identical confidence values, the API will faithfully reproduce them.
**How to avoid:** Run `SELECT DISTINCT ticker, confidence, predicted_price FROM predictions WHERE prediction_date = (SELECT MAX(prediction_date) FROM predictions) LIMIT 20` before touching any code.
**Warning signs:** All rows return the same ticker name (indicates a JOIN bug), or all confidence values are exactly 0.9300 (indicates the model wrote a constant).

### Pitfall 3: ArgoCD K8s RBAC
**What goes wrong:** The API pod's service account doesn't have `get`/`list` permission on `argoproj.io/v1alpha1/applications` in the `argocd` namespace.
**Why it happens:** K8s RBAC requires explicit ClusterRole binding for cross-namespace CRD access.
**How to avoid:** Add a ClusterRole + ClusterRoleBinding for the API service account. In Minikube dev, may not be required if running with default permissive RBAC.
**Warning signs:** `kubernetes.client.exceptions.ApiException: 403 Forbidden` in logs.

### Pitfall 4: Feast latency — import guard
**What goes wrong:** `get_online_features` is `None` when Feast is unavailable (import guard at `prediction_service.py:14-16`). Same pattern applies in `feast_service.py`.
**Why it happens:** Feast has optional import: `_FEAST_AVAILABLE = False` fallback.
**How to avoid:** Check `if _FEAST_AVAILABLE and get_online_features is not None:` before timing. Return `None` for latency when Feast is unavailable.

### Pitfall 5: Drift.tsx — two separate `?? 0` problems
**What goes wrong:** Fixing only line 75 (`oos_rmse` for new model) but missing line 70 where old model RMSE is hard-coded to `0` unconditionally.
**Root cause (line 70):** `{ name: d.previous_model, rmse: 0, mae: 0 }` — the previous-model RMSE is always 0, regardless of DB. This is a separate issue from line 75.
**Line 75:** `(d.oos_metrics?.oos_rmse as number) ?? 0` — current model RMSE defaults to 0 when null.
**How to avoid:** Fix both. For line 70 the previous-model RMSE must come from somewhere — check if `details_json` in `drift_logs` contains previous-model metrics.

### Pitfall 6: `drift_logs` has no previous-model RMSE column
**What goes wrong:** The `drift_logs` schema only has `details_json JSONB` — there is no dedicated `previous_model_rmse` column. Any previous-model RMSE must be stored inside `details_json`.
**How to avoid:** Inspect actual `drift_logs.details_json` content: `SELECT details_json FROM drift_logs LIMIT 5`. If `previous_rmse` or similar key is not present, the drift detection writer must be updated to populate it.

### Pitfall 7: CA Last Refresh — TimescaleDB view name
**What goes wrong:** The query at `flink_service.py:79` queries `timescaledb_information.continuous_aggregates` — this view exists in TimescaleDB >= 2.x. The column `last_updated_timestamp` may be named differently depending on the TimescaleDB version.
**How to avoid:** Verify the column names: `SELECT column_name FROM information_schema.columns WHERE table_name = 'continuous_aggregates'`.

---

## Code Examples

### Diagnostic SQL for OOS Metrics (Claude's Discretion)
```sql
-- Check actual key names in metrics_json
SELECT
    model_name,
    jsonb_object_keys(metrics_json) AS key
FROM model_registry
GROUP BY model_name, key
ORDER BY model_name, key;

-- Check if oos_ prefixed keys exist
SELECT model_name, metrics_json
FROM model_registry
WHERE metrics_json ? 'oos_rmse'
LIMIT 5;
```

### Diagnostic SQL for Forecast Bias
```sql
-- Check for constant confidence values in latest batch
SELECT
    COUNT(DISTINCT confidence) AS distinct_confidence,
    COUNT(DISTINCT predicted_price) AS distinct_prices,
    COUNT(DISTINCT ticker) AS distinct_tickers,
    MAX(prediction_date) AS latest_date
FROM predictions
WHERE prediction_date = (SELECT MAX(prediction_date) FROM predictions);

-- Spot-check individual rows
SELECT DISTINCT ticker, confidence, predicted_price
FROM predictions
WHERE prediction_date = (SELECT MAX(prediction_date) FROM predictions)
LIMIT 20;
```

### Drift Display Fix (Drift.tsx)
```typescript
// Line 70 — old model: replace hardcoded 0 with null (data must come from API)
oldModel: d.previous_model
  ? { name: d.previous_model, rmse: d.previous_rmse ?? null, mae: d.previous_mae ?? null }
  : null,

// Line 75 — new model: change ?? 0 to ?? null
rmse: (d.oos_metrics?.oos_rmse as number) ?? null,
mae: (d.oos_metrics?.oos_mae as number) ?? null,
```
Note: `d.previous_rmse` will require the API's `RetrainStatusResponse` to be extended with those fields, OR they come from `details_json` in drift_logs.

### Feast Latency Measurement Pattern
```python
# In feast_service.py — new function
import time

async def measure_feast_online_latency_ms(ticker: str = "AAPL") -> float | None:
    """Time a single get_online_features() call. Returns ms elapsed or None if Feast unavailable."""
    from app.services.prediction_service import _FEAST_AVAILABLE, get_online_features
    if not _FEAST_AVAILABLE or get_online_features is None:
        return None
    try:
        import asyncio
        start = time.perf_counter()
        await asyncio.to_thread(get_online_features, ticker)
        return (time.perf_counter() - start) * 1000.0
    except Exception:
        return None
```

### ArgoCD via K8s CRD Pattern
```python
# In flink_service.py — replace ARGOCD_TOKEN branch
import asyncio

async def _get_argocd_sync_status() -> str | None:
    """Read ArgoCD Application CRD sync status from K8s API."""
    try:
        from kubernetes import client as k8s_client, config as k8s_config
        def _sync():
            try:
                k8s_config.load_incluster_config()
            except k8s_config.ConfigException:
                k8s_config.load_kube_config()
            api = k8s_client.CustomObjectsApi()
            result = api.list_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace="argocd",
                plural="applications",
            )
            statuses = [
                item.get("status", {}).get("sync", {}).get("status", "Unknown")
                for item in result.get("items", [])
            ]
            return "OutOfSync" if "OutOfSync" in statuses else "Synced"
        return await asyncio.to_thread(_sync)
    except Exception:
        return None
```

### Caching Feast Latency (Claude's Discretion — 60s)
```python
# In get_analytics_summary() in flink_service.py
from app.cache import build_key, cache_get, cache_set

FEAST_LATENCY_TTL = 60  # seconds

async def get_feast_online_latency_cached() -> float | None:
    key = build_key("analytics", "feast", "latency")
    cached = await cache_get(key)
    if cached is not None:
        return cached.get("latency_ms")
    latency_ms = await measure_feast_online_latency_ms()
    await cache_set(key, {"latency_ms": latency_ms}, FEAST_LATENCY_TTL)
    return latency_ms
```

---

## Key Findings Per Bug

### Bug 1: OOS Metrics Missing — Root Cause Investigation Map

The API mapping (`prediction_service.py:157`) is correct — it strips `oos_` and filters. The frontend display is correct — `ModelComparisonTable.tsx` reads `row.oos_metrics?.rmse` etc. and `fmt()` renders `"—"` when missing.

**Most likely root cause: The ML pipeline wrote metrics without `oos_` prefix.**

Evidence: The file-based sort in `load_model_comparison` uses `.get("oos_metrics", {}).get("rmse")` (no prefix strip) while the DB sort uses `metrics_json->>'oos_rmse'` (with prefix). This inconsistency suggests the ML pipeline writes keys like `oos_rmse` to `metrics_json`, but the file-based registry may have them differently nested.

**Possible outcomes from diagnostic:**
1. `metrics_json` is empty or only has in-sample metrics → ML pipeline never computed OOS metrics → needs backfill script
2. `metrics_json` has `rmse`, `mae` etc. (no prefix) → API filter `k.startswith("oos_")` filters them all out → fix the filter or rename the keys
3. `metrics_json` has `oos_rmse` etc. correctly → API mapping works → bug must be in frontend or the data just doesn't exist for current models

### Bug 2: Forecast Constant Bias — Root Cause Investigation Map

**Possible outcomes from diagnostic:**
1. All rows have same `ticker` value → the `load_db_predictions` query has a JOIN bug returning one ticker for all rows (unlikely given the query structure)
2. All rows have identical `confidence` → the model wrote `confidence = 0.93` for every prediction (degenerate model output) → fix confidence calculation, which must NOT involve retraining
3. All rows have varied `confidence` but the API returns constant values → the cache has a stale single-value entry → invalidate cache and retry
4. `predictions` table is empty → `load_db_predictions` returns None → API falls back to `load_cached_predictions` from file → the file `latest.json` has constant values

The `confidence NUMERIC(5,4)` DB column stores up to 4 decimal places. If all are `0.9300`, the ML scoring function returned the same confidence for every ticker.

**Confidence formula note:** The predictions table stores `confidence` directly — whatever the ML pipeline wrote. There is no confidence recalculation in the API. If the model computed confidence as `model.score(X_test)` (a scalar, not per-ticker), every prediction would get the same value.

---

## State of the Art

| Component | Current State | Phase 75 Fix |
|-----------|--------------|-------------|
| ArgoCD analytics | REST API via httpx + ARGOCD_TOKEN (always empty, always returns None) | K8s CRD read via kubernetes Python client |
| Feast latency | Hard-coded `None` in get_analytics_summary (line 93) | Timed `get_online_features()` call, cached 60s |
| CA Last Refresh | Wired to TimescaleDB but may fail silently on column name mismatch | Verify and fix column name |
| OOS Metrics | Displayed as `"—"` (frontend handles null correctly) | Fix whatever layer is missing the data |
| Drift RMSE | `?? 0` renders 0.0000 for null previous-model RMSE | `?? null` + "—" display |

---

## Open Questions

1. **Does the kubernetes Python package already exist in the API service requirements?**
   - What we know: `flink_service.py` uses httpx, not the kubernetes client
   - What's unclear: Whether `kubernetes` is in `requirements.txt`
   - Recommendation: Check `requirements.txt` before planning — if not present, add it and update the Dockerfile

2. **Does `drift_logs.details_json` contain previous-model RMSE?**
   - What we know: Schema has only `details_json JSONB` — no dedicated column
   - What's unclear: What the drift detector actually writes inside `details_json`
   - Recommendation: Run `SELECT details_json FROM drift_logs LIMIT 5` as the first task in wave 1. If the key is absent, the drift detector writer needs updating.

3. **What is the exact `RetrainStatusResponse` schema for previous-model RMSE?**
   - What we know: `RetrainStatusResponse` has `previous_model` (name) and `previous_trained_at` but no `previous_rmse`
   - What's unclear: Whether previous-model RMSE should come from `retrain-status` endpoint or `drift` endpoint
   - Recommendation: The cleanest fix is to add `previous_oos_metrics` to `RetrainStatusResponse` and populate it from the second `model_registry` row in `get_retrain_status_from_db()`.

4. **Is the OOS metrics gap caused by missing data or a key naming mismatch?**
   - What we know: API filter uses `k.startswith("oos_")` and strips prefix
   - What's unclear: What keys the ML pipeline actually wrote
   - Recommendation: The diagnostic SQL must be task 1 of the OOS wave.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `stock-prediction-platform/services/api/pytest.ini` (or `pyproject.toml`) |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/test_analytics_argocd.py tests/test_analytics_feast.py -x -q` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Bug | Behavior | Test Type | Automated Command | File Exists? |
|-----|----------|-----------|-------------------|--------------|
| OOS Metrics | `load_model_comparison_from_db` returns `oos_metrics` with 5 keys when `metrics_json` has `oos_` keys | unit | `pytest tests/test_prediction_service.py -x -q` | ✅ |
| OOS Metrics | `/models/comparison` endpoint returns non-empty `oos_metrics` per model | unit | `pytest tests/test_models_router.py -x -q` | ✅ |
| Forecast Bias | `load_db_predictions` returns varied confidence per ticker | unit | `pytest tests/test_prediction_service.py -x -q` | ✅ |
| Drift RMSE | `Drift.tsx` renders `"—"` not `"0.0000"` for null previous-model RMSE | manual (no frontend tests) | N/A — visual check | N/A |
| ArgoCD K8s | `_get_argocd_sync_status()` returns `"Synced"` when CRD has all-Synced apps | unit | `pytest tests/test_analytics_argocd.py -x -q` | ✅ (needs update) |
| Feast Latency | `get_analytics_summary()` returns non-None `feast_online_latency_ms` when Feast available | unit | `pytest tests/test_analytics_feast.py -x -q` | ✅ (needs new test) |
| CA Last Refresh | `get_analytics_summary()` returns non-None `ca_last_refresh` when DB available | unit | `pytest tests/test_analytics_flink.py -x -q` | ✅ |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_analytics_argocd.py tests/test_analytics_feast.py tests/test_models_router.py tests/test_prediction_service.py -x -q`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New test for `measure_feast_online_latency_ms()` — covers Feast latency measurement (add to `tests/test_analytics_feast.py`)
- [ ] New test for `_get_argocd_sync_status()` K8s CRD path — update `tests/test_analytics_argocd.py` for kubernetes client mock
- [ ] New test for previous-model RMSE in `RetrainStatusResponse` (if schema extended)

---

## Sources

### Primary (HIGH confidence — direct source code inspection)
- `stock-prediction-platform/services/api/app/services/prediction_service.py` — OOS metrics mapping (lines 148–165), DB predictions query (lines 169–238), retrain status (lines 800–840)
- `stock-prediction-platform/services/api/app/services/flink_service.py` — ArgoCD REST API branch (lines 52–70), CA last refresh (lines 72–87), Feast latency hard-coded None (line 93)
- `stock-prediction-platform/services/api/app/services/feast_service.py` — Feast registry freshness pattern
- `stock-prediction-platform/services/api/app/routers/analytics.py` — cache TTL pattern (ANALYTICS_SUMMARY_TTL = 30)
- `stock-prediction-platform/services/api/app/routers/models.py` — `/models/comparison` endpoint
- `stock-prediction-platform/services/frontend/src/components/tables/ModelComparisonTable.tsx` — frontend OOS key access pattern (`row.oos_metrics?.rmse`)
- `stock-prediction-platform/services/frontend/src/components/tables/ModelDetailPanel.tsx` — `fmt()` null handling
- `stock-prediction-platform/services/frontend/src/pages/Drift.tsx` — `?? 0` bug at line 75, hardcoded `rmse: 0` at line 70
- `stock-prediction-platform/services/frontend/src/components/analytics/SystemHealthSummary.tsx` — N/A display logic
- `stock-prediction-platform/services/api/app/models/schemas.py` — `AnalyticsSummaryResponse` schema (feast_online_latency_ms: float | None)
- `stock-prediction-platform/db/init.sql` — drift_logs schema (JSONB only, no previous_model_rmse column), predictions schema (confidence NUMERIC)
- `stock-prediction-platform/services/api/app/config.py` — ARGOCD_TOKEN default = "", confirming why ArgoCD branch is always skipped
- `stock-prediction-platform/services/api/tests/test_analytics_argocd.py` — existing test patterns
- `stock-prediction-platform/services/api/tests/test_analytics_feast.py` — existing test patterns

### Secondary (MEDIUM confidence)
- kubernetes Python client CRD access pattern — standard library usage, verified against public kubernetes-client/python docs pattern

---

## Metadata

**Confidence breakdown:**
- Bug root causes: MEDIUM (diagnostics required for OOS + forecast bugs; drift and analytics bugs are clear)
- Code patterns: HIGH (read directly from source)
- Fix approach: HIGH (CONTEXT.md prescribes exact changes for drift and analytics; OOS and forecast depend on diagnostic)
- Test infrastructure: HIGH (existing test files confirmed present and follow established patterns)

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable codebase, no external library changes needed)
