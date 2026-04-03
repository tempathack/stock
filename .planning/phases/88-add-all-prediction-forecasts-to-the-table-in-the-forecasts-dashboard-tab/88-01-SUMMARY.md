---
phase: 88-add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab
plan: "01"
subsystem: api
tags: [kubernetes, configmap, react-query, typescript, multi-horizon, forecasts]

# Dependency graph
requires:
  - phase: 88-add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab
    provides: Research and UI-SPEC defining multi-horizon table requirements
provides:
  - horizons.json ConfigMap entry enabling /predict/horizons to return all four horizons [1,7,14,30]
  - MultiHorizonForecastRow TypeScript interface with per-horizon predictions map
  - HorizonPrediction TypeScript interface with predicted_price, expected_return_pct, confidence, predicted_date, trend
  - useAllHorizonsPredictions React Query hook issuing 4 parallel useQueries calls
affects:
  - 88-02-PLAN (multi-horizon table UI - consumes these types and hook)
  - 88-03-PLAN (if exists - depends on data layer contracts)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - useQueries parallel fetching pattern for multi-horizon data aggregation
    - Shared queryKeys.bulkPredictions(h) cache key across useBulkPredictions and useAllHorizonsPredictions

key-files:
  created:
    - stock-prediction-platform/k8s/ingestion/model-features-configmap.yaml
  modified:
    - stock-prediction-platform/services/frontend/src/api/types.ts
    - stock-prediction-platform/services/frontend/src/api/queries.ts

key-decisions:
  - "Used useQueries (not individual useQuery calls) for parallel horizon fetching — enables single isLoading/isError aggregate state"
  - "Shared queryKeys.bulkPredictions(h) so caches are shared with useBulkPredictions(h) in detail drawer"
  - "Used isPending (React Query v5 semantics) for useQueries loading state"
  - "isError = ALL queries failed; isPartialError = some failed while others succeeded"

patterns-established:
  - "Multi-horizon data pattern: ALL_HORIZONS constant + useQueries map + aggregate state booleans"
  - "ConfigMap source YAML tracked in k8s/ingestion/ alongside other k8s resources"

requirements-completed: [FCST-HORIZONS-01, FCST-HOOK-01]

# Metrics
duration: 2min
completed: 2026-04-03
---

# Phase 88 Plan 01: Multi-Horizon Data Layer Summary

**Patched model-features-config ConfigMap to serve all four forecast horizons [1,7,14,30] and added MultiHorizonForecastRow type + useAllHorizonsPredictions parallel hook as the data layer for the multi-horizon forecast table**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-03T08:49:53Z
- **Completed:** 2026-04-03T08:52:14Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Patched live `model-features-config` ConfigMap with `horizons.json: '{"horizons": [1, 7, 14, 30], "default": 7}'` and restarted stock-api — `/predict/horizons` now returns all four horizons
- Created `k8s/ingestion/model-features-configmap.yaml` source file with both `features.json` and `horizons.json` entries tracked in git
- Added `HorizonPrediction` and `MultiHorizonForecastRow` interfaces to `types.ts` (Phase 88 section)
- Added `useAllHorizonsPredictions` hook to `queries.ts` using `useQueries` for parallel fetching across horizons 1, 7, 14, 30

## Task Commits

Each task was committed atomically:

1. **Task 1: Add horizons.json to model-features-config ConfigMap** - `f454536` (feat)
2. **Task 2: Add MultiHorizonForecastRow type and useAllHorizonsPredictions hook** - `971999c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `stock-prediction-platform/k8s/ingestion/model-features-configmap.yaml` - Full ConfigMap source YAML with both features.json and horizons.json entries
- `stock-prediction-platform/services/frontend/src/api/types.ts` - HorizonPrediction and MultiHorizonForecastRow interfaces appended (Phase 88 section)
- `stock-prediction-platform/services/frontend/src/api/queries.ts` - useQueries import added; ALL_HORIZONS constant and useAllHorizonsPredictions hook appended

## Decisions Made
- Used `useQueries` (React Query v5 parallel queries) rather than four separate `useQuery` hooks — provides single aggregate `isLoading`/`isError` state and keeps all four horizon requests in a single logical unit
- Reused `queryKeys.bulkPredictions(h)` so the multi-horizon hook shares cache entries with the existing `useBulkPredictions(h)` hook used in the detail drawer
- Used `isPending` (not `isLoading`) for `useQueries` result state — correct React Query v5 semantics for non-initial-load pending state
- Defined `isPartialError` flag to allow UI to show partial results when some horizons fail while others succeed

## Deviations from Plan

None — plan executed exactly as written. The `HorizonPrediction` and `MultiHorizonForecastRow` types were already present as uncommitted working-tree changes from a previous partial session; they were staged and included in the Task 2 commit.

## Issues Encountered
- `forecastUtils.test.ts` (pre-existing untracked file) had TypeScript strictness errors (`Object is possibly 'undefined'`) unrelated to Phase 88 changes — logged as out of scope, not fixed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `/predict/horizons` returns `{"horizons":[1,7,14,30],"default":7}` — Plan 02/03 can rely on all four horizons being available
- `MultiHorizonForecastRow` and `HorizonPrediction` types exported from `api/types.ts` — ready for table component consumption
- `useAllHorizonsPredictions` hook exported from `api/queries.ts` — ready for Plan 03 table component

## Self-Check: PASSED

- FOUND: `stock-prediction-platform/k8s/ingestion/model-features-configmap.yaml`
- FOUND: `.planning/phases/88-.../88-01-SUMMARY.md`
- FOUND: commit `f454536` (Task 1)
- FOUND: commit `971999c` (Task 2)

---
*Phase: 88-add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab*
*Completed: 2026-04-03*
