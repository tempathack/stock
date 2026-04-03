---
phase: 88-add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab
plan: "02"
subsystem: frontend-utils
tags: [typescript, vitest, pure-function, data-transform, tdd]
dependency_graph:
  requires: [88-01-types: MultiHorizonForecastRow + HorizonPrediction in api/types.ts]
  provides: [joinMultiHorizonForecastData pure function ready for Plan 03 import]
  affects: [services/frontend/src/utils/forecastUtils.ts]
tech_stack:
  added: [vitest@4.1.2]
  patterns: [TDD red-green, Map-based merge, noUncheckedIndexedAccess-safe tests]
key_files:
  created:
    - services/frontend/src/utils/forecastUtils.test.ts
  modified:
    - services/frontend/src/utils/forecastUtils.ts
    - services/frontend/src/api/types.ts
    - services/frontend/package.json
    - services/frontend/package-lock.json
decisions:
  - "Used relative imports in test file (../api/types) to avoid vitest alias configuration"
  - "Added MultiHorizonForecastRow and HorizonPrediction to api/types.ts as Rule 3 fix (blocking dependency from Plan 01 not yet present)"
  - "Used non-null assertions (!) in tests instead of optional chaining to satisfy noUncheckedIndexedAccess while keeping tests concise"
metrics:
  duration: "~4 minutes"
  completed: "2026-04-03"
  tasks_completed: 1
  files_modified: 5
---

# Phase 88 Plan 02: joinMultiHorizonForecastData Merge Function Summary

**One-liner:** Pure TypeScript merge function with 6 vitest unit tests that joins per-horizon BulkPredictionResponse arrays into one MultiHorizonForecastRow per ticker using a tickerHorizonMap pattern.

## What Was Built

Added `joinMultiHorizonForecastData` to `forecastUtils.ts` following a TDD workflow:
- RED: Wrote 6 failing unit tests in `forecastUtils.test.ts`
- GREEN: Implemented the merge function; all 6 tests pass
- TypeScript compilation clean (`npx tsc --noEmit` exits 0)

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| `export function joinMultiHorizonForecastData` exists in forecastUtils.ts | PASS |
| forecastUtils.test.ts has 6 describe-it test blocks | PASS |
| `npx vitest run src/utils/forecastUtils.test.ts` exits 0 (6/6 pass) | PASS |
| `npx tsc --noEmit` exits 0 (no errors) | PASS |
| JNJ case: ticker absent from all predictions excluded from output | PASS |
| Partial coverage: ticker missing from one horizon still appears | PASS |

## Key Design

The function builds a `tickerHorizonMap: Map<string, Record<number, PredictionResponse>>` from all horizon results, then iterates each ticker to compute `expected_return_pct = ((predicted_price - current_price) / current_price) * 100`, derive trend via `deriveTrend`, and emit one `MultiHorizonForecastRow` per ticker. Tickers with no predictions are excluded; tickers with missing market data get `current_price: null` and `expected_return_pct: 0`.

## Commits

| Hash | Description |
|------|-------------|
| 51ddbfd | test(88-02): add failing tests for joinMultiHorizonForecastData (RED) |
| bfd0bdb | feat(88-02): implement joinMultiHorizonForecastData merge function (GREEN) |

## Deviations from Plan

### Auto-fixed Issues (Rule 3 - Blocking)

**1. [Rule 3 - Blocking] Missing MultiHorizonForecastRow and HorizonPrediction types**
- **Found during:** Task 1, before writing tests
- **Issue:** Plan 02 depends on types added by Plan 01, but Plan 01's SUMMARY.md did not exist and `types.ts` lacked `MultiHorizonForecastRow` and `HorizonPrediction`. The function signature and test file would fail to compile without these types.
- **Fix:** Added the two interfaces to `api/types.ts` at the Phase 88 section (matching the definitions specified in Plan 01's must_haves)
- **Files modified:** services/frontend/src/api/types.ts
- **Commit:** 51ddbfd

**2. [Rule 3 - Blocking] vitest not installed**
- **Found during:** Task 1, RED phase setup
- **Issue:** `package.json` had no vitest dependency; `npx vitest` would fail
- **Fix:** Installed vitest@4.1.2 as devDependency via `npm install --save-dev vitest`
- **Files modified:** package.json, package-lock.json
- **Commit:** 51ddbfd

**3. [Rule 1 - Bug] Test file TypeScript errors from noUncheckedIndexedAccess**
- **Found during:** TypeScript compilation check after GREEN
- **Issue:** `rows[0].horizons[7]` is typed as `HorizonPrediction | undefined` under `noUncheckedIndexedAccess`; accessing `.expected_return_pct` on it caused TS2532 errors
- **Fix:** Added non-null assertions (`rows[0]!`, `row.horizons[7]!`) in tests where the test logic guarantees the value exists
- **Files modified:** services/frontend/src/utils/forecastUtils.test.ts
- **Commit:** bfd0bdb

## Self-Check

- [x] forecastUtils.ts exists: `/home/tempa/Desktop/priv-project/stock-prediction-platform/services/frontend/src/utils/forecastUtils.ts`
- [x] forecastUtils.test.ts exists: `/home/tempa/Desktop/priv-project/stock-prediction-platform/services/frontend/src/utils/forecastUtils.test.ts`
- [x] Commit 51ddbfd exists
- [x] Commit bfd0bdb exists
- [x] All 6 tests pass
- [x] TypeScript clean

## Self-Check: PASSED
