---
phase: 76-ux-polish
plan: 03
subsystem: api
tags: [yfinance, horizons, fastapi, kafka-consumer, postgresql, config, cronjob]

# Dependency graph
requires:
  - phase: 34-k8s-ml-cronjobs
    provides: weekly-training CronJob manifest to extend
  - phase: 9-kafka-consumers-batch-writer
    provides: db_writer._ensure_tickers that needed enrichment
  - phase: 43-horizon-query-param
    provides: _validate_horizon and AVAILABLE_HORIZONS config pattern
provides:
  - 14D horizon accepted by /predict/bulk and /predict/{ticker} (AVAILABLE_HORIZONS='1,7,14,30')
  - horizons.json seed file so HorizonToggle shows 14D immediately on deployment
  - Training CronJob will produce 14D model artifacts on next weekly run
  - stocks table enriched with company_name and sector from yfinance on each consumer run
  - Forecasts page Company/Sector columns will show real names after next ingestion cycle
affects: [forecasts-page, horizon-toggle, weekly-training, kafka-consumer, market-overview]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "yfinance import guard (_YFINANCE_AVAILABLE) for optional dependency isolation"
    - "DO UPDATE SET with CASE WHEN for null-safe upsert backfill (preserves non-null values)"
    - "horizons.json seed file at serving/active/ to pre-populate toggle before first training run"

key-files:
  created:
    - stock-prediction-platform/services/api/serving/active/horizons.json
    - stock-prediction-platform/services/api/tests/test_predict_horizon.py (TestHorizon14Support class added)
    - stock-prediction-platform/services/kafka-consumer/tests/test_db_writer.py (TestEnsureTickersYfinanceEnrichment class added)
  modified:
    - stock-prediction-platform/services/api/app/config.py
    - stock-prediction-platform/k8s/ml/cronjob-training.yaml
    - stock-prediction-platform/services/kafka-consumer/consumer/db_writer.py

key-decisions:
  - "Used real-config RED test (no patch) for test_bulk_horizon_14_accepted so it fails on old config and passes after update"
  - "horizons.json seed file path is services/api/serving/active/ matching K8s SERVING_DIR override; operators must copy/mount to PVC in production"
  - "DO UPDATE SET with CASE WHEN preserves existing non-null company_name even if yfinance returns a fallback ticker symbol"
  - "yfinance import guard (_YFINANCE_AVAILABLE) allows kafka-consumer to start even if yfinance not installed"

patterns-established:
  - "Null-safe upsert: DO UPDATE SET ... CASE WHEN EXCLUDED.col IS NOT NULL THEN EXCLUDED.col ELSE table.col END"
  - "Optional-dependency guard: try/except ImportError with _AVAILABLE boolean flag"

requirements-completed: []

# Metrics
duration: 10min
completed: 2026-04-02
---

# Phase 76 Plan 03: Backend Data Gaps Summary

**14D horizon unblocked via AVAILABLE_HORIZONS config + horizons.json seed, and stocks table enriched with real company names and sectors from yfinance**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-02T07:50:00Z
- **Completed:** 2026-04-02T07:54:45Z
- **Tasks:** 3 (Task 0, Task 1, Task 2 — Task 0 and Task 2 were TDD)
- **Files modified:** 5

## Accomplishments

- `/predict/bulk?horizon=14` now returns HTTP 200 (was 400); AVAILABLE_HORIZONS changed from `"1,7,30"` to `"1,7,14,30"`
- horizons.json seed file (`{"horizons": [1, 7, 14, 30], "default": 7}`) deployed so HorizonToggle shows 14D immediately without waiting for a training run
- Weekly training CronJob will generate 14D model artifacts (`horizon_14d/`) on next scheduled run via `--horizons 1,7,14,30`
- `db_writer._ensure_tickers` now fetches `longName` and `sector` from yfinance; stocks table rows backfilled on next consumer message
- Forecasts page Company and Sector columns will show real names (e.g. "Apple Inc.", "Technology") after next ingestion cycle
- 13 API predict-horizon tests pass; 18 db_writer tests pass

## Task Commits

Each task was committed atomically:

1. **Task 0: Write failing test for horizon=14 acceptance (RED)** - `e063c96` (test)
2. **Task 1: Fix AVAILABLE_HORIZONS, update CronJob, seed horizons.json (GREEN)** - `437bccc` (feat)
3. **Task 2: Add failing tests for yfinance enrichment (RED)** - `50031ac` (test)
4. **Task 2: Implement yfinance enrichment in db_writer (GREEN)** - `df0a08e` (feat)

## Files Created/Modified

- `stock-prediction-platform/services/api/app/config.py` - AVAILABLE_HORIZONS changed to `"1,7,14,30"`
- `stock-prediction-platform/k8s/ml/cronjob-training.yaml` - Added `--horizons 1,7,14,30` args to training container
- `stock-prediction-platform/services/api/serving/active/horizons.json` - New seed file with `[1, 7, 14, 30]`
- `stock-prediction-platform/services/kafka-consumer/consumer/db_writer.py` - yfinance import guard, `_fetch_ticker_metadata()`, updated SQL with sector and DO UPDATE SET
- `stock-prediction-platform/services/api/tests/test_predict_horizon.py` - Added `TestHorizon14Support` class with 2 tests
- `stock-prediction-platform/services/kafka-consumer/tests/test_db_writer.py` - Added `TestEnsureTickersYfinanceEnrichment` class with 4 tests; updated DO NOTHING assertion to DO UPDATE

## Decisions Made

- Used real-config (no patch) for `test_bulk_horizon_14_accepted` to guarantee RED before config change and GREEN after
- `horizons.json` seed placed at `services/api/serving/active/` (matches K8s SERVING_DIR ConfigMap path); operators must copy/mount into PVC for production — documented in plan context
- `DO UPDATE SET` with `CASE WHEN ... IS NOT NULL` preserves existing good data — a yfinance failure returning `(None, None)` will not overwrite a previously-stored real company name
- `_YFINANCE_AVAILABLE` guard allows the consumer to run normally if yfinance is somehow not installed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test asserting DO NOTHING behavior**
- **Found during:** Task 2 implementation (GREEN phase)
- **Issue:** Existing test `test_ensure_tickers_on_conflict_do_nothing` asserted `"ON CONFLICT (ticker) DO NOTHING"` which is now incorrect after the SQL was changed to `DO UPDATE SET`
- **Fix:** Renamed to `test_ensure_tickers_on_conflict_do_update` and updated assertion to `"ON CONFLICT (ticker) DO UPDATE"`
- **Files modified:** `stock-prediction-platform/services/kafka-consumer/tests/test_db_writer.py`
- **Verification:** All 18 db_writer tests pass
- **Committed in:** `df0a08e` (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - existing test assertion stale after SQL change)
**Impact on plan:** Required update to keep test suite honest. No scope creep.

## Issues Encountered

None.

## User Setup Required

**Production deployment note:** The seed file `services/api/serving/active/horizons.json` must be copied or volume-mounted into the K8s PVC at the path `serving/active/horizons.json` (controlled by the `ml-pipeline-config` ConfigMap `SERVING_DIR`). The file will be regenerated by the next training run with the same content.

## Next Phase Readiness

- Forecasts page Company/Sector columns will populate after next kafka-consumer ingestion cycle processes at least one message per ticker
- 14D predictions will appear in the HorizonToggle immediately (horizons.json seeded); model artifacts will be generated on the next weekly Sunday training run
- All prediction endpoints accept horizon=14 without 400 errors

---
*Phase: 76-ux-polish*
*Completed: 2026-04-02*
