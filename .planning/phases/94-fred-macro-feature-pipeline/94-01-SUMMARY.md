---
phase: 94-fred-macro-feature-pipeline
plan: "01"
subsystem: ml-tests
tags: [tdd, red-state, fred, feast, data-loader, feature-repo]
dependency_graph:
  requires: []
  provides: [94-01-test-scaffolds]
  affects: [94-02-implementation]
tech_stack:
  added: []
  patterns: [tdd-red-state, mock-fredapi, mock-psycopg2]
key_files:
  created:
    - stock-prediction-platform/ml/tests/test_feature_repo.py
  modified:
    - stock-prediction-platform/ml/tests/test_data_loader.py
    - stock-prediction-platform/ml/tests/test_feast_store.py
decisions:
  - "Used monkeypatch.setenv for FRED_API_KEY isolation across all fetch_fred_macro tests"
  - "TestCreateFredMacroTable uses explicit MagicMock context manager protocol (not psycopg2 fixture) for clean isolation"
  - "test_feature_repo.py tests ImportError — fred_macro_source and fred_macro_fv not yet in feature_repo.py"
metrics:
  duration_seconds: 126
  completed_date: "2026-04-04"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
---

# Phase 94 Plan 01: FRED Macro TDD — RED State Scaffolds Summary

**One-liner:** Failing test scaffolds for FRED collector functions and Feast FeatureView wiring — 18 tests fail RED because fetch_fred_macro, create_fred_macro_table, write_fred_macro_to_db, and fred_macro_fv are not yet implemented.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Failing tests for fetch_fred_macro, create_fred_macro_table, write_fred_macro_to_db | 14a0177 | test_data_loader.py |
| 2 | Failing tests for _TRAINING_FEATURES membership and fred_macro_fv import | 6a9012d | test_feast_store.py, test_feature_repo.py (new) |

## RED State Summary

All 18 new tests fail as required:

- **test_data_loader.py** — 10 tests across 4 classes:
  - `TestFetchFredMacro` (4 tests): fail with `ImportError: cannot import name 'fetch_fred_macro'`
  - `TestFetchFredMacroMissingKey` (1 test): fails with `ImportError`
  - `TestCreateFredMacroTable` (3 tests): fail with `ImportError`
  - `TestWriteFredMacroToDB` (2 tests): fail with `ImportError`

- **test_feast_store.py** — 2 tests in `TestTrainingFeatures`:
  - `test_contains_all_14_fred_entries`: fails `AssertionError` (fred_macro_fv:dgs2 missing from _TRAINING_FEATURES)
  - `test_total_feature_count_is_49`: fails `AssertionError` (currently 35, expected 49)

- **test_feature_repo.py** — 6 tests in `TestFredMacroFeatureView`:
  - All fail with `ImportError: cannot import name 'fred_macro_source'`

**Existing tests:** 23 pre-existing tests unaffected — still pass.

## Test Contracts Established

The tests define the following contracts for Plan 02 to implement:

1. `fetch_fred_macro(start_date, end_date)` returns a DataFrame with 14 columns (dgs2...pcepilfe), ffill applied, index.name="date", uses FRED_API_KEY from env, raises KeyError if missing
2. `create_fred_macro_table()` executes DDL containing "feast_fred_macro", "create_hypertable", "IF NOT EXISTS"
3. `write_fred_macro_to_db(df)` returns row count, uses ON CONFLICT upsert SQL
4. `fred_macro_source` — PostgreSQLSource with query referencing "feast_fred_macro"
5. `fred_macro_fv` — FeatureView named "fred_macro_fv" with 14 schema fields (all 14 FRED series names)
6. `_TRAINING_FEATURES` must grow from 35 to 49 entries with all 14 fred_macro_fv:* strings

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] test_data_loader.py modified (230 lines appended)
- [x] test_feast_store.py modified (TestTrainingFeatures appended)
- [x] test_feature_repo.py created (6-test class)
- [x] Commit 14a0177 exists
- [x] Commit 6a9012d exists
- [x] 18 new tests fail RED, 23 existing tests still pass
