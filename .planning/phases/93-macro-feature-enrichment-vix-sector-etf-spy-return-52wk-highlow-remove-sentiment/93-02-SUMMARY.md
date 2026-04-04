---
phase: 93-macro-feature-enrichment-vix-sector-etf-spy-return-52wk-highlow-remove-sentiment
plan: 02
subsystem: ml
tags: [yfinance, macro-features, vix, spy, sector-etf, 52-week-high-low, data-loader]

# Dependency graph
requires:
  - phase: 93-01
    provides: RED-state TDD tests for load_yfinance_macro and feast_store macro/sentiment contracts
provides:
  - fetch_yfinance_macro() in yahoo_finance.py — downloads VIX, SPY, 11 sector ETFs from yfinance
  - load_yfinance_macro() in data_loader.py — joins macro features with per-ticker 52w high/low pct
  - SECTOR_ETF_MAP and TICKER_TO_SECTOR_ETF lookup dicts in yahoo_finance.py
affects:
  - 93-03 (removes sentiment, wires macro features into Feast and training pipeline)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sector ETF mapping via hardcoded GICS dict — TICKER_TO_SECTOR_ETF lookup for per-ticker sector return"
    - "52-week high/low pct computed from 252-day rolling window on ohlcv_daily close prices"
    - "yfinance batch download of macro symbols — ^VIX + SPY + 11 ETFs in one call"
    - "Log-return formula: np.log(close / close.shift(1)) for both SPY and sector ETFs"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/api/app/services/yahoo_finance.py
    - stock-prediction-platform/ml/pipelines/components/data_loader.py
    - stock-prediction-platform/ml/tests/test_data_loader.py

key-decisions:
  - "fetch_yfinance_macro placed in API yahoo_finance.py; ML data_loader.py contains its own _fetch_yfinance_macro_wide helper to avoid cross-service imports (ML Dockerfile only copies ml/ directory)"
  - "load_yfinance_macro returns DatetimeIndex (not MultiIndex) to match test contract from plan 01"
  - "52-week rolling uses 252 trading days with min_periods=20 to handle warm-up period"

patterns-established:
  - "Macro features are market-wide (broadcast to all tickers on same date) — fetched once then joined per ticker"
  - "sector_return column: uses TICKER_TO_SECTOR_ETF to pick the right ETF return column; falls back to DEFAULT_SECTOR_ETF=SPY for unlisted tickers"

requirements-completed: []

# Metrics
duration: 4min
completed: 2026-04-04
---

# Phase 93 Plan 02: yfinance Macro Fetcher Summary

**yfinance macro pipeline: fetch_yfinance_macro fetches VIX/SPY/11 sector ETFs; load_yfinance_macro joins per-ticker 52w high/low pct from OHLCV rolling window**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-04T12:02:11Z
- **Completed:** 2026-04-04T12:06:24Z
- **Tasks:** 3 (implement yahoo_finance.py, implement data_loader.py, confirm GREEN test)
- **Files modified:** 3

## Accomplishments
- Added `SECTOR_ETF_MAP`, `TICKER_TO_SECTOR_ETF`, and `fetch_yfinance_macro()` to yahoo_finance.py
- Added `load_yfinance_macro()` to data_loader.py with 52-week rolling high/low pct computation
- `test_load_yfinance_macro_returns_dataframe` test now GREEN (was RED in plan 01)

## Task Commits

Each task was committed atomically:

1. **Tasks 1-3: implement yahoo_finance + data_loader + confirm GREEN** - `52a583c` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `stock-prediction-platform/services/api/app/services/yahoo_finance.py` - Added SECTOR_ETF_MAP, TICKER_TO_SECTOR_ETF, DEFAULT_SECTOR_ETF, fetch_yfinance_macro()
- `stock-prediction-platform/ml/pipelines/components/data_loader.py` - Added _SECTOR_ETF_MAP, _TICKER_TO_SECTOR_ETF, _fetch_yfinance_macro_wide(), load_yfinance_macro()
- `stock-prediction-platform/ml/tests/test_data_loader.py` - Updated TestYfinanceMacroLoader with mocks so test passes GREEN

## Decisions Made
- ML Dockerfile only copies `ml/` — cannot import from `services/api/`. The constants (SECTOR_ETF_MAP etc.) and macro download logic are mirrored inside `data_loader.py` as private underscore-prefixed names to avoid the cross-service import problem.
- `load_yfinance_macro` returns a DatetimeIndex (not MultiIndex) as specified by the plan 01 test contract.
- The plan 01 RED test (`test_load_yfinance_macro_returns_dataframe`) needed mocking added — updated to mock `_fetch_yfinance_macro_wide` and `psycopg2.connect` so it can run without network/DB access.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added mocking to test_load_yfinance_macro_returns_dataframe**
- **Found during:** Task 3 (run test — confirm GREEN)
- **Issue:** Test called `load_yfinance_macro` without mocks, which requires live PostgreSQL + yfinance network access. Would fail in CI.
- **Fix:** Added `@patch` decorators for `_fetch_yfinance_macro_wide` and `psycopg2` with synthetic data fixtures.
- **Files modified:** `ml/tests/test_data_loader.py`
- **Verification:** `pytest ml/tests/test_data_loader.py::TestYfinanceMacroLoader` — 1 passed
- **Committed in:** 52a583c

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for CI-safe test execution. No scope creep.

## Issues Encountered
- Cross-service import issue: `data_loader.py` initially tried to import from `services.api.app.services.yahoo_finance` which doesn't exist inside the ML container. Fixed by mirroring the sector ETF constants and yfinance download logic inside the ML module.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `load_yfinance_macro()` is implemented and tested — ready for plan 93-03 to wire it into the training pipeline
- Plan 93-03 will: remove sentiment from `_TRAINING_FEATURES`, add yfinance macro features to Feast, update `training_pipeline.py` to call `load_yfinance_macro()`
- The 2 RED feast_store tests (`test_sentiment_removed_from_training_features`, `test_yfinance_macro_features_present`) will become GREEN in plan 93-03

---
*Phase: 93-macro-feature-enrichment-vix-sector-etf-spy-return-52wk-highlow-remove-sentiment*
*Completed: 2026-04-04*
