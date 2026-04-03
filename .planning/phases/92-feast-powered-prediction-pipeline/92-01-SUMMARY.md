---
phase: 92-feast-powered-prediction-pipeline
plan: 01
subsystem: testing
tags: [feast, pytest, tdd, ml, prediction-service, feature-store, sentiment]

# Dependency graph
requires:
  - phase: 92-feast-powered-prediction-pipeline
    provides: "92-CONTEXT.md — Feast pipeline design and feature contracts"
provides:
  - "TestFeastDataLoader class (4 RED tests) in ml/tests/test_data_loader.py"
  - "TestFeastInference class (6 RED tests) in services/api/tests/test_prediction_service.py"
  - "Sentinel coverage tests (2 RED tests) in ml/tests/test_feast_store.py"
affects: ["92-02", "92-03", "92-04"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wave 0 TDD RED scaffold — test stubs written before any implementation"
    - "Inner-function imports to defer ImportError until test runs (not collection time)"

key-files:
  created: []
  modified:
    - stock-prediction-platform/ml/tests/test_data_loader.py
    - stock-prediction-platform/services/api/tests/test_prediction_service.py
    - stock-prediction-platform/ml/tests/test_feast_store.py

key-decisions:
  - "Inner-function imports (import inside test methods) used to ensure tests fail at run time with ImportError rather than collection time — aligns with TDD RED contract"
  - "TestFeastInference tests accept AttributeError on feast module patch as valid RED signal since prediction_service does not import feast yet"

patterns-established:
  - "Wave 0 stub header comment: '# ── Wave 0 stub — tests will be RED until Plan NN implements ...' placed above each new class"
  - "Sentinel tests appended as module-level functions to test_feast_store.py rather than inside a class to match existing style"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-04-03
---

# Phase 92 Plan 01: Wave 0 TDD Test Scaffolds Summary

**Failing test stubs for load_feast_data(), get_online_features_for_ticker(), _feast_inference(), and sentiment feature coverage — 12 RED tests establishing behavioral contracts before implementation**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-03T14:44:33Z
- **Completed:** 2026-04-03T14:46:53Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- TestFeastDataLoader (4 tests) appended to ml/tests/test_data_loader.py — all fail with ImportError since load_feast_data() does not exist yet
- TestFeastInference (6 tests) appended to services/api/tests/test_prediction_service.py — fail with AttributeError since feast is not imported in prediction_service
- Two sentinel tests appended to ml/tests/test_feast_store.py — test_training_features_include_sentiment_columns fails with AssertionError (30 != 34 features)
- All 36 pre-existing tests in the three files continue to pass unmodified

## Task Commits

Each task was committed atomically:

1. **Task 1: TestFeastDataLoader tests** - `d0a259a` (test)
2. **Task 2: TestFeastInference + feast_store sentinel tests** - `5ed067f` (test)

_Note: TDD plan — all commits are test commits. No feat commits in Wave 0._

## Files Created/Modified

- `stock-prediction-platform/ml/tests/test_data_loader.py` — Appended TestFeastDataLoader class (4 RED tests for load_feast_data())
- `stock-prediction-platform/services/api/tests/test_prediction_service.py` — Appended TestFeastInference class (6 RED tests for online features and inference path)
- `stock-prediction-platform/ml/tests/test_feast_store.py` — Appended 2 sentinel tests for _TRAINING_FEATURES sentiment column coverage

## Decisions Made

- Inner-function imports (import inside each test method body) used throughout so the ImportError surfaces at test run time, not pytest collection time. This keeps collection clean while satisfying the TDD RED contract.
- TestFeastInference tests patch `app.services.prediction_service.feast` — this deliberately fails with AttributeError since the module does not import feast yet, confirming the correct RED signal for Wave 4.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All Wave 0 test stubs are in place and in RED state
- Plan 92-02 can immediately start implementing load_feast_data() and use TestFeastDataLoader as its verification step
- Plan 92-03 will extend feast_store.py _TRAINING_FEATURES and will be verified by test_training_features_include_sentiment_columns
- Plan 92-04 will implement _feast_inference() and will be verified by TestFeastInference

---
*Phase: 92-feast-powered-prediction-pipeline*
*Completed: 2026-04-03*
