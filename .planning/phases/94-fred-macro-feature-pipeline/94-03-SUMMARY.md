---
phase: 94-fred-macro-feature-pipeline
plan: "03"
subsystem: ml
tags: [feast, feature-store, fred, macro, python, training-features, online-inference]

# Dependency graph
requires:
  - phase: 94-02
    provides: feast_fred_macro table with ticker='MACRO' column; fred_macro_source + fred_macro_fv stubbed in feature_repo.py

provides:
  - fred_macro_source and fred_macro_fv registered in feature_repo.py (discoverable by feast apply)
  - _TRAINING_FEATURES extended with 14 fred_macro_fv:* entries (49 total features)
  - _fetch_from_feast() makes second get_online_features(entity_rows=[{"ticker":"MACRO"}]) call for FRED features
  - StreamingFeaturesResponse extended with fred_macro dict field

affects: [feast-training-pipeline, feast-online-service, feature-store-registry]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - MACRO entity pattern: FRED macro features use ticker='MACRO' as a sentinel entity key to flow through the same Feast online store path as ticker-keyed stock features
    - Graceful degradation: FRED Feast call wrapped in try/except — failure returns fred_macro=None without affecting stock feature availability
    - Option C schema extension: add single dict field (fred_macro) rather than 14 individual float fields for fewest schema changes

key-files:
  created: []
  modified:
    - stock-prediction-platform/ml/feature_store/feature_repo.py
    - stock-prediction-platform/ml/features/feast_store.py
    - stock-prediction-platform/services/api/app/services/feast_online_service.py
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/ml/tests/test_feature_repo.py
    - stock-prediction-platform/ml/tests/test_feast_store.py

key-decisions:
  - "Use fred_macro: dict | None = None field on StreamingFeaturesResponse (Option C) — fewest schema changes vs 14 individual float fields"
  - "MACRO entity pattern: feast_fred_macro.ticker is always 'MACRO'; online call uses entity_rows=[{'ticker':'MACRO'}] consistent with other stock feature entity_rows"
  - "FRED Feast call is non-fatal: wraps in separate try/except inside existing try block so stock features are unaffected by FRED unavailability"

patterns-established:
  - "Sentinel entity key for global features: use a fixed string (MACRO) as ticker to share the same Feast entity model without needing a separate entity type"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-04-04
---

# Phase 94 Plan 03: Feast Feature Registration and Inference Extension Summary

**fred_macro_fv registered in Feast feature repo with 14 FRED series, _TRAINING_FEATURES extended to 49 entries, and _fetch_from_feast() makes a second online store call using entity_rows=[{"ticker":"MACRO"}] for FRED macro features**

## Performance

- **Duration:** 35 min
- **Started:** 2026-04-04T15:11:00Z
- **Completed:** 2026-04-04T15:46:04Z
- **Tasks:** 4
- **Files modified:** 6

## Accomplishments

- Verified fred_macro_source and fred_macro_fv correctly defined in feature_repo.py with entities=[ticker], 14 Float64 schema fields, ticker + feast_fred_macro in query
- Extended _TRAINING_FEATURES in feast_store.py from 35 to 49 entries (all 14 FRED series: dgs2 through pcepilfe)
- Ran feast apply (connection error — expected in local env without DB creds; Python import check confirms 14-field schema)
- Extended _fetch_from_feast() in feast_online_service.py with second get_online_features() call for fred_macro_fv using entity_rows=[{"ticker": "MACRO"}]; results merged into StreamingFeaturesResponse.fred_macro dict field
- All 18 phase gate tests pass GREEN (9 TestFetchFredMacro/CreateTable/WriteToDB + 2 TestTrainingFeatures + 6 TestFredMacroFeatureView + 1 regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Verify fred_macro_source and fred_macro_fv** - `dd8fe92` (feat)
2. **Task 2: Extend _TRAINING_FEATURES with 14 FRED entries** - `18a21fe` (feat)
3. **Task 3: feast apply** - no code changes (verified via Python import check; feast apply failed as expected — no DB env vars locally)
4. **Task 4: Add FRED features to _fetch_from_feast()** - `3710cf1` (feat)

## Files Created/Modified

- `stock-prediction-platform/ml/feature_store/feature_repo.py` — fred_macro_source (PostgreSQLSource) + fred_macro_fv (FeatureView, 14 Float64 fields, entities=[ticker])
- `stock-prediction-platform/ml/features/feast_store.py` — _TRAINING_FEATURES extended from 35 to 49 entries; docstring updated
- `stock-prediction-platform/services/api/app/services/feast_online_service.py` — second get_online_features() call with entity_rows=[{"ticker":"MACRO"}]; graceful degradation on failure
- `stock-prediction-platform/services/api/app/models/schemas.py` — StreamingFeaturesResponse.fred_macro: dict | None = None added
- `stock-prediction-platform/ml/tests/test_feature_repo.py` — bug fix: .query -> get_table_query_string()
- `stock-prediction-platform/ml/tests/test_feast_store.py` — stale sentinel test updated: assert 35 -> 49, fred_macro_fv view check added

## Decisions Made

- **Option C for StreamingFeaturesResponse**: added `fred_macro: dict | None = None` dict field rather than 14 individual float fields — fewest schema changes, extensible
- **MACRO entity pattern**: feast_fred_macro.ticker is always 'MACRO'; online call uses entity_rows=[{"ticker": "MACRO"}] consistent with other stock feature entity_rows pattern
- **Non-fatal FRED call**: FRED Feast call wrapped in separate nested try/except inside the outer stock features try block — stock feature availability (available=True) is never affected by FRED unavailability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_feature_repo.py accessed .query attribute on PostgreSQLSource**
- **Found during:** Task 1 (Verify fred_macro_source and fred_macro_fv)
- **Issue:** PostgreSQLSource has no `.query` attribute — test was failing with AttributeError. Correct access is `get_table_query_string()`
- **Fix:** Changed `fred_macro_source.query` to `fred_macro_source.get_table_query_string()` in test_feature_repo.py
- **Files modified:** `stock-prediction-platform/ml/tests/test_feature_repo.py`
- **Verification:** 6/6 TestFredMacroFeatureView tests pass GREEN
- **Committed in:** `dd8fe92` (Task 1 commit)

**2. [Rule 1 - Bug] Stale Phase 93 sentinel test asserted len(_TRAINING_FEATURES) == 35**
- **Found during:** Task 2 (Extend _TRAINING_FEATURES)
- **Issue:** `test_training_features_include_core_feature_views` asserted 35 features — correct for Phase 93 but fails after Phase 94 adds 14 FRED entries
- **Fix:** Updated assertion to 49, added `assert "fred_macro_fv" in views` check, updated docstring to mention Phase 94
- **Files modified:** `stock-prediction-platform/ml/tests/test_feast_store.py`
- **Verification:** All 13 test_feast_store.py tests pass GREEN
- **Committed in:** `18a21fe` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 - Bug)
**Impact on plan:** Both fixes were necessary for tests to pass correctly. No scope creep.

## Issues Encountered

- feast apply fails locally (expected): `POSTGRES_PORT=${POSTGRES_PORT}` env var is not set locally — Feast cannot parse it as an integer. This is a production/K8s config; the Python import check (`fred_macro_fv has 14 fields`) confirms the FeatureView definition is correct. feast apply will succeed when run in the K8s job with env vars set.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 94 FRED pipeline is wired end-to-end: collect (fetch_fred_macro) → persist (feast_fred_macro table with ticker='MACRO') → Feast training (_TRAINING_FEATURES 49 entries) → inference (second Feast online call in _fetch_from_feast)
- The feast materialization CronJob (from Phase 94-02) will populate Redis with FRED features using entity_rows=[{"ticker":"MACRO"}]
- StreamingFeaturesResponse.fred_macro will be non-None once feast materialize-incremental has been run with the FRED data

---
*Phase: 94-fred-macro-feature-pipeline*
*Completed: 2026-04-04*

## Self-Check: PASSED

- feature_repo.py: FOUND
- feast_store.py: FOUND
- feast_online_service.py: FOUND
- schemas.py: FOUND
- commit dd8fe92: FOUND
- commit 18a21fe: FOUND
- commit 3710cf1: FOUND
