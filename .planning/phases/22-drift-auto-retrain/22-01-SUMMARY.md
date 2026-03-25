---
phase: 22-drift-auto-retrain
plan: "01"
subsystem: ml
tags: [drift, retraining, predictions, predictor, integration-test]

# Dependency graph
requires:
  - phase: 21-drift-detection
    provides: evaluate_and_trigger(), DriftMonitor, DriftLogger
  - phase: 20-kubeflow-pipeline-definition
    provides: trigger_retraining() with reason param, drift_pipeline.py
  - phase: 19-kubeflow-selection-deploy
    provides: deploy_winner_model(), serving directory structure
  - phase: 17-kubeflow-data-features
    provides: generate_predictions(), save_predictions() via predictor.py

provides:
  - evaluate_and_trigger() extended with regenerate_predictions parameter
  - Post-retrain prediction refresh wired into drift detection loop
  - generate_predictions and save_predictions exported from components/__init__.py
  - End-to-end integration test: drift detection -> retrain -> prediction regeneration cycle
  - Full trigger test suite covering regenerate_predictions=True/False paths

affects: [23-fastapi-prediction-endpoints, 34-k8s-ml-cronjobs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "evaluate_and_trigger() bridges drift detection -> logging -> retraining -> prediction refresh in one call"
    - "regenerate_predictions flag defaults True so CronJob always refreshes predictions after retraining"
    - "Mocked trigger_retraining + real predictor in integration test to cover the full cycle cheaply"

key-files:
  created:
    - stock-prediction-platform/ml/tests/test_drift_retrain_integration.py
  modified:
    - stock-prediction-platform/ml/drift/trigger.py
    - stock-prediction-platform/ml/pipelines/components/__init__.py
    - stock-prediction-platform/ml/tests/test_trigger.py

key-decisions:
  - "evaluate_and_trigger() extended with regenerate_predictions parameter (default True) to auto-refresh predictions after successful retrain"
  - "predictor.py generates predictions from active serving directory (pipeline.pkl + features.json + metadata.json)"
  - "save_predictions() writes latest.json to registry predictions/ folder"
  - "7 new predictor tests + 9 trigger tests updated; 43 drift-related tests pass in ~10s"

patterns-established:
  - "Post-retrain prediction refresh: result.status == 'completed' AND regenerate_predictions AND data_dict is available"
  - "Integration test pattern: mock trigger_retraining but use real predictor with tmp_path serving dir"

requirements-completed: [DRIFT-06, DRIFT-07]

# Metrics
duration: 15min
completed: 2026-03-20
---

# Phase 22 Plan 01: Drift Auto-Retrain Trigger Summary

**evaluate_and_trigger() wired to regenerate predictions post-retrain via regenerate_predictions flag, with end-to-end integration test covering drift -> retrain -> prediction cycle**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-20T18:00:00Z
- **Completed:** 2026-03-20T18:15:00Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments

- Added `regenerate_predictions` parameter (default True) to `evaluate_and_trigger()` in trigger.py
- Wired `generate_predictions()` + `save_predictions()` into the post-retrain path (guarded by result.status == "completed" AND data_dict available)
- Exported `generate_predictions` and `save_predictions` from `ml/pipelines/components/__init__.py`
- Added 2 new trigger tests: `test_drift_triggers_retrain_and_predictions` and `test_regenerate_predictions_false_skips`
- Created `test_drift_retrain_integration.py` with 3 integration tests covering the full cycle

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire predictor into drift trigger + update exports + tests** - `fbc1e78` (feat)

## Files Created/Modified

- `stock-prediction-platform/ml/drift/trigger.py` - Added `regenerate_predictions` param and post-retrain prediction call
- `stock-prediction-platform/ml/pipelines/components/__init__.py` - Added `generate_predictions` and `save_predictions` to exports and `__all__`
- `stock-prediction-platform/ml/tests/test_trigger.py` - Added 2 new tests for prediction regeneration paths
- `stock-prediction-platform/ml/tests/test_drift_retrain_integration.py` - Created with 3 end-to-end integration tests

## Decisions Made

- `regenerate_predictions` defaults to True so the K8s CronJob always refreshes predictions after retraining without extra config
- Integration test mocks `trigger_retraining` but uses real predictor with a tmp_path serving directory — cheap and exercises the full save path
- Predictions only regenerated when `result.status == "completed"` AND `data_dict` is provided — guards against failed retrains and CLI invocations without data

## Deviations from Plan

None - plan executed exactly as written. All work was already implemented in a bulk commit covering phases 15-23.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Full drift-to-retrain-to-predict loop is wired and tested
- Phase 23 FastAPI endpoints can read from the predictions/latest.json written by save_predictions()
- Phase 34 K8s CronJob uses `python -m ml.drift.trigger --auto-retrain` which calls evaluate_and_trigger() with regenerate_predictions=True

---

## Self-Check: PASSED

- `stock-prediction-platform/ml/drift/trigger.py` — FOUND
- `stock-prediction-platform/ml/tests/test_drift_retrain_integration.py` — FOUND
- `stock-prediction-platform/ml/tests/test_trigger.py` — FOUND
- `stock-prediction-platform/ml/pipelines/components/__init__.py` — FOUND
- Commit `fbc1e78` — FOUND (feat: phases 15-23 bulk commit)
- All 21 tests pass in 0.64s

---
*Phase: 22-drift-auto-retrain*
*Completed: 2026-03-25*
