---
phase: 93-macro-feature-enrichment-vix-sector-etf-spy-return-52wk-highlow-remove-sentiment
plan: 01
subsystem: testing
tags: [tdd, pytest, feast, yfinance, macro-features, sentiment]

# Dependency graph
requires: []
provides:
  - "RED-state sentinel tests asserting sentiment columns are removed from _TRAINING_FEATURES"
  - "RED-state sentinel tests asserting yfinance_macro_fv columns are added to _TRAINING_FEATURES"
  - "RED-state stub test for load_yfinance_macro() function existence and return contract"
affects:
  - "93-02 (must make these tests GREEN by implementing macro feature changes)"
  - "93-03 (depends on macro feature columns established in 93-02)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wave-0 RED sentinel tests encode behavioral contracts before implementation"
    - "TDD RED phase: write failing tests first, implementation follows in later plans"

key-files:
  created: []
  modified:
    - "stock-prediction-platform/ml/tests/test_feast_store.py"
    - "stock-prediction-platform/ml/tests/test_data_loader.py"

key-decisions:
  - "Sentinel tests placed at module level (not inside class) for consistency with existing Phase 92 sentinels in test_feast_store.py"
  - "load_yfinance_macro() test triggers ImportError RED via module-level import (expected cascade through data_loader.py import chain)"
  - "TestYfinanceMacroLoader uses no mocking — raw import failure is the correct RED signal for a non-existent function"

patterns-established:
  - "Phase 93 feature columns: yfinance_macro_fv:{vix,spy_return,sector_return,high52w_pct,low52w_pct}"
  - "Sentiment columns to remove: reddit_sentiment_fv:{avg_sentiment,mention_count,positive_ratio,negative_ratio}"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 93 Plan 01: Macro Feature Enrichment RED-State TDD Tests Summary

**RED-state sentinel tests encoding sentiment removal and yfinance macro feature addition contracts for Phase 93 implementation plans**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-04T12:01:56Z
- **Completed:** 2026-04-04T12:03:35Z
- **Tasks:** 3 (tasks 1+2 combined into single atomic commit, task 3 = pytest verification)
- **Files modified:** 2

## Accomplishments
- Added `test_sentiment_removed_from_training_features` asserting all 4 `reddit_sentiment_fv:*` columns are absent from `_TRAINING_FEATURES` (currently FAILS RED)
- Added `test_yfinance_macro_features_present` asserting all 5 `yfinance_macro_fv:*` columns are present in `_TRAINING_FEATURES` (currently FAILS RED)
- Added `TestYfinanceMacroLoader.test_load_yfinance_macro_returns_dataframe` asserting `load_yfinance_macro()` exists, returns DataFrame with DatetimeIndex and required macro columns (currently FAILS RED via ImportError)
- Verified existing tests (`test_training_features_include_sentiment_columns`, `test_online_feature_key_format_no_view_prefix`) still PASS GREEN

## Task Commits

Each task was committed atomically:

1. **Tasks 1-2-3: RED sentinel tests + pytest verification** - `f0b1e14` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `stock-prediction-platform/ml/tests/test_feast_store.py` - Added 2 RED sentinel tests for sentiment removal and macro feature presence
- `stock-prediction-platform/ml/tests/test_data_loader.py` - Added `TestYfinanceMacroLoader` class with 1 RED stub test for `load_yfinance_macro()`

## Decisions Made
- Placed new sentinel tests at module level in `test_feast_store.py` (consistent with existing Phase 92 sentinel pattern)
- `TestYfinanceMacroLoader` uses no mocking — ImportError RED is the correct signal when function doesn't exist yet
- The `test_load_yfinance_macro_returns_dataframe` test will need mocking in GREEN phase (93-02) since it will call real yfinance; for RED phase, no mock is needed because import fails first

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

During `pytest` run, many pre-existing tests fail with `ModuleNotFoundError: No module named 'app'` (a known environment issue unrelated to this plan). The three specific new tests fail for the correct RED reasons:
- `test_sentiment_removed_from_training_features`: `AssertionError` — sentiment columns are still present
- `test_yfinance_macro_features_present`: `AssertionError` — macro columns not yet in `_TRAINING_FEATURES`
- `test_load_yfinance_macro_returns_dataframe`: `ModuleNotFoundError` cascade — function doesn't exist

Pre-existing failures are out of scope for this plan per deviation rules (scope boundary).

## Next Phase Readiness
- RED tests encoded, behavioral contracts defined for Phase 93 implementation
- Plan 93-02 must implement: remove sentiment from `_TRAINING_FEATURES`, add 5 `yfinance_macro_fv:*` columns, implement `load_yfinance_macro()` function
- When 93-02 completes, all 3 RED tests should turn GREEN and the old `test_training_features_include_sentiment_columns` will turn RED (expected — it encodes the old Phase 92 contract)

## Self-Check: PASSED

- `stock-prediction-platform/ml/tests/test_feast_store.py` - EXISTS (modified)
- `stock-prediction-platform/ml/tests/test_data_loader.py` - EXISTS (modified)
- Commit `f0b1e14` - FOUND in git log

---
*Phase: 93-macro-feature-enrichment-vix-sector-etf-spy-return-52wk-highlow-remove-sentiment*
*Completed: 2026-04-04*
