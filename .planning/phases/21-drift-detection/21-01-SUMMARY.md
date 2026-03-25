---
phase: 21-drift-detection
plan: "01"
subsystem: ml
tags: [drift-detection, scipy, ks-test, psi, python, testing]

# Dependency graph
requires:
  - phase: 20-kubeflow-pipeline-definition
    provides: trigger_retraining() with reason param in drift_pipeline.py
  - phase: 19-kubeflow-selection-deploy
    provides: ModelRegistry with activate_model/get_active_model
provides:
  - DataDriftDetector class with KS-test and PSI statistical tests
  - PredictionDriftDetector class with rolling error multiplier
  - ConceptDriftDetector class with RMSE degradation ratio
  - DriftResult dataclass (common return type, severity levels, to_dict())
  - 20 unit tests covering all detector behaviors
affects:
  - 21-02 (monitor.py and trigger.py depend on detector.py)
  - 22-drift-auto-retrain

# Tech tracking
tech-stack:
  added: [scipy.stats.ks_2samp]
  patterns:
    - Stateless detector classes instantiated with threshold params
    - Quantile-based PSI binning with clipping to avoid log(0)
    - DriftResult dataclass as common return type across all detectors
    - Severity levels (none/low/medium/high) based on feature fraction drifted

key-files:
  created:
    - stock-prediction-platform/ml/drift/detector.py
    - stock-prediction-platform/ml/tests/test_detector.py
  modified: []

key-decisions:
  - "PSI hand-rolled with quantile-based binning — no external drift library needed"
  - "DataDriftDetector severity based on fraction of features drifted (not ratio to threshold)"
  - "All detectors are stateless — instantiated with thresholds, no internal state"
  - "DriftResult.features_affected defaults to empty list (not None) for safe iteration"

patterns-established:
  - "Detector pattern: __init__(thresholds), detect(data) -> DriftResult"
  - "PSI uses np.quantile breakpoints + np.unique dedup for constant-feature safety"

requirements-completed: [DRIFT-01, DRIFT-02, DRIFT-03]

# Metrics
duration: 15min
completed: 2026-03-20
---

# Phase 21 Plan 01: Drift Detectors Summary

**Three stateless drift detector classes (KS-test+PSI for data, error multiplier for prediction, RMSE ratio for concept) with shared DriftResult dataclass and 20 unit tests — all passing**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-20T00:00:00Z
- **Completed:** 2026-03-20T00:15:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Implemented DataDriftDetector with two-sample KS-test (scipy) and hand-rolled PSI with quantile-based binning
- Implemented PredictionDriftDetector comparing recent vs baseline MAE via configurable error multiplier
- Implemented ConceptDriftDetector comparing recent vs historical RMSE via degradation ratio
- DriftResult dataclass with drift_type, is_drifted, severity (none/low/medium/high), details, timestamp, features_affected
- 20 unit tests covering all detector classes, PSI computation, severity scaling, custom thresholds

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement drift detectors (RED → GREEN)** - `fbc1e78` (feat)

**Plan metadata:** Created as part of bulk phases 15-23 commit

## Files Created/Modified
- `stock-prediction-platform/ml/drift/detector.py` - Three drift detector classes + DriftResult dataclass
- `stock-prediction-platform/ml/tests/test_detector.py` - 20 unit tests for all detectors

## Decisions Made
- PSI hand-rolled with quantile-based binning (no external drift library needed)
- DataDriftDetector severity based on fraction of features drifted rather than a single global ratio
- Stateless detector pattern — thresholds set at instantiation, no mutable internal state
- np.unique deduplication of PSI breakpoints handles constant-feature edge case safely

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- detector.py fully importable and tested — ready for monitor.py orchestration in Plan 21-02
- DriftResult.to_dict() ready for JSON serialization in logger/trigger

## Self-Check: PASSED

---
*Phase: 21-drift-detection*
*Completed: 2026-03-20*
