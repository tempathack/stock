---
phase: 92-feast-powered-prediction-pipeline
plan: 02
subsystem: ml
tags: [feast, ml, training-pipeline, feature-store, sentiment, reddit, data-loader, tdd]

# Dependency graph
requires:
  - phase: 92-feast-powered-prediction-pipeline
    provides: "92-01: Wave 0 TDD RED stubs — TestFeastDataLoader, test_training_features_include_sentiment_columns"
  - phase: 92-feast-powered-prediction-pipeline
    provides: "92-CONTEXT.md — Feast pipeline design and feature contracts"
provides:
  - "_TRAINING_FEATURES extended to 34 items including 4 reddit_sentiment_fv columns"
  - "load_feast_data(tickers, start_date, end_date) in data_loader.py"
  - "run_training_pipeline(use_feast_data=True) branching step 1 to Feast and step 2 to passthrough"
affects: ["92-03", "92-04"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD GREEN wave — implementing against pre-written RED stubs from Wave 0"
    - "Feast offline training path: entity_df with business-day timestamps, flat DataFrame output"
    - "_feast_mode flag for step 2 passthrough (data already enriched, skip engineer_features)"
    - "Pre-loaded data_dict always appends load_data step for consistent 12-step count"

key-files:
  created: []
  modified:
    - stock-prediction-platform/ml/features/feast_store.py
    - stock-prediction-platform/ml/pipelines/components/data_loader.py
    - stock-prediction-platform/ml/pipelines/training_pipeline.py
    - stock-prediction-platform/ml/tests/test_data_loader.py

key-decisions:
  - "top_subreddit excluded from _TRAINING_FEATURES: String type incompatible with numeric model input"
  - "load_feast_data returns flat DataFrame (not dict) — training_pipeline converts to per-ticker dict at step 1"
  - "Feast mode sets _feast_mode=True and skips engineer_features at step 2 — data already contains all 34 columns"
  - "Sentinel fill: sentiment columns filled 0.0 first (sparse Reddit), then full fillna(0.0) for lag warmup NaN"
  - "Pre-loaded data_dict case appends load_data to steps_completed to preserve consistent 12-step count expected by tests"

patterns-established:
  - "Feast training path: load_feast_data() replaces load_data() + engineer_features() when use_feast_data=True"
  - "TDD fix pattern: Boolean truth-value ambiguity on DataFrame in or-chain — use 'is not None' instead"

requirements-completed: []

# Metrics
duration: 15min
completed: 2026-04-03
---

# Phase 92 Plan 02: ML Training Pipeline Extended with Feast Offline Features Summary

**34-feature training pipeline with Feast offline store support: load_feast_data() function, use_feast_data=True branching in run_training_pipeline(), and 4 reddit_sentiment_fv columns added to _TRAINING_FEATURES**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-03T14:48:40Z
- **Completed:** 2026-04-03T15:03:28Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Extended `_TRAINING_FEATURES` from 30 to 34 columns by adding `avg_sentiment`, `mention_count`, `positive_ratio`, `negative_ratio` from `reddit_sentiment_fv`
- Implemented `load_feast_data(tickers, start_date, end_date)` in data_loader.py — builds entity_df with business-day UTC timestamps, retrieves 34-column Feast offline DataFrame, fills sparse sentiment NaN with 0.0
- Wired `use_feast_data: bool = False` parameter into `run_training_pipeline()` — step 1 branches to Feast or Postgres, step 2 passes through when Feast mode active (features already enriched)
- All 4 TestFeastDataLoader tests GREEN; both feast_store sentinel tests GREEN (31 total passed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend _TRAINING_FEATURES with 4 sentiment columns** - `b917507` (feat)
2. **Task 2: Add load_feast_data() and wire use_feast_data** - `e0619f7` (feat)

## Files Created/Modified

- `stock-prediction-platform/ml/features/feast_store.py` — Added 4 reddit_sentiment_fv entries to _TRAINING_FEATURES (30 → 34)
- `stock-prediction-platform/ml/pipelines/components/data_loader.py` — Added Feast import, _SENTIMENT_COLS constant, load_feast_data() function
- `stock-prediction-platform/ml/pipelines/training_pipeline.py` — Added use_feast_data param, _feast_mode flag, branched step 1 and step 2
- `stock-prediction-platform/ml/tests/test_data_loader.py` — Fixed pre-existing DataFrame truth-value bug in test_load_feast_data_entity_df_structure

## Decisions Made

- `top_subreddit` excluded from training features — String type is incompatible with numeric model inputs
- `load_feast_data()` returns a flat DataFrame (not a dict like `load_data()`) — training_pipeline converts with per-ticker groupby at step 1
- `_feast_mode=True` causes step 2 to use passthrough (`enriched = data_dict`) — Feast data already has all 34 columns, re-running `engineer_features` would be redundant
- Pre-loaded `data_dict` path now explicitly appends `"load_data"` to `steps_completed` to maintain 12-step consistency expected by test suite

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed DataFrame truth-value ambiguity in test_load_feast_data_entity_df_structure**
- **Found during:** Task 2 (TestFeastDataLoader GREEN verification)
- **Issue:** Test line `entity_df = call_args.kwargs.get("entity_df") or call_args[1].get("entity_df") or call_args[0][0]` raises `ValueError: The truth value of a DataFrame is ambiguous` when `kwargs.get("entity_df")` returns a non-None DataFrame
- **Fix:** Replaced or-chain with explicit `is not None` guard
- **Files modified:** `ml/tests/test_data_loader.py`
- **Verification:** test_load_feast_data_entity_df_structure now PASSES
- **Committed in:** e0619f7 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed steps_completed regression in pre-loaded data_dict path**
- **Found during:** Task 2 (training_pipeline existing tests verification)
- **Issue:** Moving `steps_completed.append("load_data")` inside the `if data_dict is None` block broke 3 existing tests expecting exactly 12 steps (pre-loaded data_dict skipped the append entirely)
- **Fix:** Added `else` clause to pre-loaded path that still appends `"load_data"` for consistent step count
- **Files modified:** `ml/pipelines/training_pipeline.py`
- **Verification:** test_full_pipeline_completes and related tests PASS
- **Committed in:** e0619f7 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes required for correctness. No scope creep.

## Issues Encountered

Two pre-existing test failures in `test_training_pipeline.py` (`test_pipeline_with_feature_store`, `test_pipeline_feature_store_fallback`) were confirmed to exist before plan 92-02 changes — these patch `feature_engineer.read_features` which does not exist. Documented in `deferred-items.md`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `_TRAINING_FEATURES` has 34 columns — the `use_feast` path in `engineer_features` automatically benefits (plan 92 context)
- `run_training_pipeline(use_feast_data=True)` ready for end-to-end training with Feast offline store
- Plan 92-04 can implement `_feast_inference()` which will use the inference path aligned to 34-feature `features.json`

---
*Phase: 92-feast-powered-prediction-pipeline*
*Completed: 2026-04-03*

## Self-Check: PASSED

All claimed files exist and all task commits verified in git history.
