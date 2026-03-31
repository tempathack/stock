---
phase: 75-data-quality-fixes-oos-model-metrics-missing-forecast-constant-bias-identical-confidence-drift-rmse-null-as-zero-analytics-n-a-integrations-argocd-feast-ca
plan: "03"
subsystem: api

tags: [argocd, feast, kubernetes, flink, analytics, timescaledb, caching]

requires:
  - phase: 75-data-quality-fixes
    provides: "Test scaffolding for ArgoCD K8s CRD and Feast latency tests (75-01)"

provides:
  - "_get_argocd_sync_status() in flink_service.py reading ArgoCD CRD from K8s API (no ARGOCD_TOKEN)"
  - "measure_feast_online_latency_ms() in feast_service.py using time.perf_counter() + asyncio.to_thread()"
  - "_get_feast_online_latency_cached() in flink_service.py with FEAST_LATENCY_TTL=60s cache"
  - "CA last refresh query with column-name fallback (last_updated_timestamp -> last_run_started_at)"

affects:
  - analytics-page
  - feast-service
  - flink-service
  - argocd-integration

tech-stack:
  added:
    - "kubernetes==29.0.0 Python client (added in 75-01)"
  patterns:
    - "K8s CRD reads via asyncio.to_thread() wrapping synchronous kubernetes.client.CustomObjectsApi"
    - "_FEAST_AVAILABLE module-level guard with try/except ImportError for optional ml.features dependency"
    - "Cache-aside pattern with build_key() for slow measurements (TTL=60s for Feast latency)"
    - "Column-name fallback in raw SQL: try primary column, except -> try alternate name"

key-files:
  created: []
  modified:
    - "stock-prediction-platform/services/api/app/services/flink_service.py"
    - "stock-prediction-platform/services/api/app/services/feast_service.py"

key-decisions:
  - "ArgoCD status reads from kubernetes.client.CustomObjectsApi (K8s CRD) instead of ARGOCD_TOKEN/httpx — works without a running ArgoCD HTTP API, uses RBAC from in-cluster service account"
  - "Feast latency cached 60s via build_key('analytics','feast','latency') to avoid timing overhead on every analytics summary request"
  - "measure_feast_online_latency_ms() added to feast_service.py (not flink_service.py) to keep Feast logic co-located"
  - "CA last refresh uses two-query fallback: last_updated_timestamp first, then last_run_started_at for TimescaleDB version differences"

patterns-established:
  - "asyncio.to_thread() pattern for K8s synchronous client calls in async FastAPI handlers"
  - "_FEAST_AVAILABLE guard: try import at module level, set bool flag, assign None sentinel"

requirements-completed: [DQ-75]

duration: 10min
completed: "2026-03-31"
---

# Phase 75 Plan 03: Analytics Integrations (ArgoCD + Feast + CA) Summary

**ArgoCD sync status wired to K8s CRD, Feast online latency measured and cached 60s, CA last refresh with column-name fallback — all three Analytics N/A fields now return real data**

## Performance

- **Duration:** ~10 min (verification pass)
- **Started:** 2026-03-31T18:17:19Z
- **Completed:** 2026-03-31T18:17:19Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Replaced hard-coded `None` Feast latency and ARGOCD_TOKEN-gated ArgoCD status with live measurements
- `_get_argocd_sync_status()` reads `argoproj.io/v1alpha1` Application CRDs from Kubernetes API using in-cluster config with kubeconfig fallback; returns "Synced", "OutOfSync", or None
- `measure_feast_online_latency_ms()` times a single `get_online_features()` call via `asyncio.to_thread()`, guarded by `_FEAST_AVAILABLE` flag set at module import time
- `_get_feast_online_latency_cached()` wraps the measurement with 60s Redis cache to prevent timing on every analytics summary request
- CA last refresh query now tries `last_updated_timestamp` first, falls back to `last_run_started_at` for TimescaleDB version compatibility
- All 15 analytics tests pass GREEN (test_analytics_argocd.py, test_analytics_feast.py, test_analytics_flink.py)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add measure_feast_online_latency_ms() to feast_service.py**
   - `a97e174` test(75-03): add failing tests for measure_feast_online_latency_ms()
   - `db0cf96` feat(75-03): add measure_feast_online_latency_ms() to feast_service.py

2. **Task 2: Replace ArgoCD REST branch with K8s CRD in flink_service.py + wire Feast latency + verify CA last refresh**
   - `eb0349c` test(75-03): add failing tests for K8s CRD ArgoCD and wired Feast latency
   - `b24160b` feat(75-03): replace ArgoCD REST branch with K8s CRD in flink_service.py + wire Feast latency

## Files Created/Modified

- `stock-prediction-platform/services/api/app/services/flink_service.py` — Added `_get_argocd_sync_status()`, `_get_feast_online_latency_cached()`, `FEAST_LATENCY_TTL=60`; rewrote `get_analytics_summary()` body; removed ARGOCD_TOKEN REST branch
- `stock-prediction-platform/services/api/app/services/feast_service.py` — Added `_FEAST_AVAILABLE` module-level guard, `get_online_features` binding, `measure_feast_online_latency_ms()` async function

## Decisions Made

- Used K8s CRD approach for ArgoCD (not ARGOCD_TOKEN) so it works inside the cluster via service account RBAC, with no token management required
- Feast latency cached separately from the main analytics summary (which has a 30s TTL) because measuring Feast is slow and worth a longer 60s cache
- `_FEAST_AVAILABLE` guard placed in `feast_service.py` (not imported from `prediction_service.py`) to keep the module self-contained

## Deviations from Plan

None — plan executed exactly as written. All acceptance criteria pass.

Note: The `grep "ARGOCD_TOKEN"` check showed 2 matches, but both are comment strings ("Does NOT use ARGOCD_TOKEN" and "does NOT require ARGOCD_TOKEN") — no functional code references `settings.ARGOCD_TOKEN`. The old REST branch is fully removed.

## Issues Encountered

None — all tests passed GREEN on first run.

## User Setup Required

None — no external service configuration required. ArgoCD status falls back to None gracefully if K8s RBAC denies the CRD read.

## Next Phase Readiness

- Analytics page SystemHealthSummary can now receive real ArgoCD sync status, Feast latency, and CA last refresh values from the API
- 75-04 (if any) can rely on all three integrations being wired and tested

---
*Phase: 75-data-quality-fixes*
*Completed: 2026-03-31*
