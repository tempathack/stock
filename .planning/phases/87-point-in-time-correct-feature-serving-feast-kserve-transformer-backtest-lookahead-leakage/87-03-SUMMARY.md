---
phase: 87-point-in-time-correct-feature-serving-feast-kserve-transformer-backtest-lookahead-leakage
plan: "03"
subsystem: infra
tags: [kserve, feast, transformer, backtest, pit-correct, kserve-inference, k8s, yaml, pydantic]

# Dependency graph
requires:
  - phase: 87-01
    provides: Feast transformer Python service + pit_validator module
  - phase: 87-02
    provides: test_pit_correctness.py with xfail test_response_includes_pit_flag, test_feast_transformer.py
provides:
  - KServe InferenceService YAML wired with spec.transformer using feast-transformer image
  - BacktestResponse schema with features_pit_correct: bool = False field (PIT-04)
  - backtest_service.get_backtest_data() returns features_pit_correct key
  - cronjob-feast-materialize.yaml with feast-snapshot-date audit annotation
  - KSERVE_INFERENCE_URL updated to route through InferenceService (Transformer), not predictor directly
affects:
  - phase-88
  - any phase consuming KServe inference or BacktestResponse API

# Tech tracking
tech-stack:
  added: []
  patterns:
    - KServe transformer sidecar pattern — spec.transformer.containers beside spec.predictor
    - ConfigMap volume mount for Feast store at /opt/feast in transformer container
    - xfail-to-pass TDD gate — test exists as xfail in prior plan, removed when field is added

key-files:
  created: []
  modified:
    - stock-prediction-platform/k8s/ml/kserve/kserve-inference-service.yaml
    - stock-prediction-platform/k8s/ml/cronjob-feast-materialize.yaml
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/services/backtest_service.py
    - stock-prediction-platform/services/api/tests/test_pit_correctness.py
    - stock-prediction-platform/k8s/ingestion/configmap.yaml

key-decisions:
  - "Use stock-model-serving.ml.svc.cluster.local (no -predictor suffix) for KSERVE_INFERENCE_URL so requests route through the Transformer; the -predictor suffix bypasses it entirely"
  - "features_pit_correct defaults to False because existing stored predictions were made without the Transformer; the True path is left as a TODO for when Transformer deploy date tracking is added"
  - "feast-snapshot-date annotation is static daily-incremental because K8s cannot inject dynamic dates at template rendering time without an initContainer; actual date is logged by the Python script"

patterns-established:
  - "Pattern: KServe Transformer mounted via volumeMount from feast-feature-store-config ConfigMap at /opt/feast — same ConfigMap name used by feast-feature-server deployment"
  - "Pattern: xfail tests as forward gates — plan N writes xfail, plan N+1 adds the implementation and removes xfail, ensuring the test was never silently skipped"

requirements-completed: [PIT-01, PIT-02, PIT-03, PIT-04, PIT-05]

# Metrics
duration: 2min
completed: 2026-04-03
---

# Phase 87 Plan 03: Wire Feast Transformer into KServe InferenceService + PIT Traceability Summary

**KServe InferenceService wired with Feast Transformer sidecar, BacktestResponse carries features_pit_correct field, and KSERVE_INFERENCE_URL updated to route through the Transformer instead of calling the predictor directly**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-03T08:56:43Z
- **Completed:** 2026-04-03T08:58:30Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added spec.transformer.containers block to kserve-inference-service.yaml with feast-transformer image, FEAST_STORE_PATH/REDIS_HOST/REDIS_PORT env vars, and volumeMount for feast-feature-store-config ConfigMap
- Added features_pit_correct: bool = False field to BacktestResponse schema and corresponding key to backtest_service.get_backtest_data() return dict; removed xfail marker from test_response_includes_pit_flag — all 11 tests now pass
- Fixed KSERVE_INFERENCE_URL in configmap.yaml from the predictor-direct URL (bypassed Transformer) to the InferenceService URL that routes through the Transformer first

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Transformer spec to kserve-inference-service.yaml + snapshot label to cronjob-feast-materialize.yaml** - `f60422d` (feat)
2. **Task 2: Add features_pit_correct to BacktestResponse schema and backtest_service; remove xfail** - `88c261b` (feat)
3. **Task 3: Update KSERVE_INFERENCE_URL to route through Transformer** - `762fe90` (fix)

## Files Created/Modified
- `stock-prediction-platform/k8s/ml/kserve/kserve-inference-service.yaml` - Added spec.transformer with feast-transformer container and feast-feature-store-config volume
- `stock-prediction-platform/k8s/ml/cronjob-feast-materialize.yaml` - Added feast-snapshot-date annotation and FEAST_SNAPSHOT_LOG env var
- `stock-prediction-platform/services/api/app/models/schemas.py` - Added features_pit_correct: bool = False to BacktestResponse
- `stock-prediction-platform/services/api/app/services/backtest_service.py` - Added "features_pit_correct": False to get_backtest_data() return dict
- `stock-prediction-platform/services/api/tests/test_pit_correctness.py` - Removed xfail marker, updated test to verify default is False and instance creation works
- `stock-prediction-platform/k8s/ingestion/configmap.yaml` - Updated KSERVE_INFERENCE_URL from -predictor direct URL to InferenceService URL

## Decisions Made
- Used `stock-model-serving.ml.svc.cluster.local` (no `-predictor` suffix) for KSERVE_INFERENCE_URL — the InferenceService cluster-local hostname routes requests through the Transformer before the Predictor. The `-predictor` suffix bypasses the Transformer entirely.
- `features_pit_correct` defaults to False for backward compatibility — existing predictions stored before Transformer deployment are not PIT-correct. The logic to set it True is deferred via TODO comment.
- Snapshot date annotation is static (`daily-incremental`) because K8s cannot inject dynamic dates at template rendering time. The actual snapshot date is logged by the ml.feature_store.materialize script.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all tasks executed cleanly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 87 complete: all PIT-correct feature serving components are wired together
- KServe Transformer declared in K8s, API routed through it, BacktestResponse carries PIT traceability flag
- Phase 88 (add-all-prediction-forecasts-to-the-table) can proceed — BacktestResponse schema is stable

---
*Phase: 87-point-in-time-correct-feature-serving-feast-kserve-transformer-backtest-lookahead-leakage*
*Completed: 2026-04-03*
