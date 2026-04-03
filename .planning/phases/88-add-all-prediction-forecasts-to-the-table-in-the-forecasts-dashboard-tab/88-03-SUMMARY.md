---
phase: 88-add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab
plan: 03
subsystem: ui
tags: [react, mui, datagrid, forecast, multi-horizon, typescript]

# Dependency graph
requires:
  - phase: 88-01
    provides: "MultiHorizonForecastRow interface, useAllHorizonsPredictions hook in queries.ts"
  - phase: 88-02
    provides: "joinMultiHorizonForecastData utility function in forecastUtils.ts"
provides:
  - "ForecastTable.tsx renders 8 horizon columns across 4 MUI DataGrid column groups"
  - "Forecasts.tsx fetches all 4 horizons in parallel using useAllHorizonsPredictions"
  - "CSV/PDF export flattens all 4 horizons into 13-column flat format"
  - "HorizonToggle removed from main table header, retained in detail drawer"
affects: [forecasts-page, forecast-export, forecast-table]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "MUI DataGrid columnGroupingModel for nested column group headers"
    - "Flatten nested horizons map to flat fields before passing to DataGrid renderCell"
    - "Dual-query pattern: useAllHorizonsPredictions for main table + useBulkPredictions(7) for ForecastRow consumers"

key-files:
  created: []
  modified:
    - "services/frontend/src/components/forecasts/ForecastTable.tsx"
    - "services/frontend/src/pages/Forecasts.tsx"

key-decisions:
  - "Flatten MultiHorizonForecastRow.horizons map to flat DataGrid fields (price_1d, return_1d, ...) — DataGrid renderCell params.row loses TypeScript access to nested objects without this"
  - "Keep useBulkPredictions(7) alongside useAllHorizonsPredictions — comparison panel and detail drawer still consume ForecastRow[], so a separate 7d query is simpler than refactoring those components"
  - "minReturn/maxReturn filters apply to horizons[7] (the 7d return) — matches default sort column return_7d"

patterns-established:
  - "columnGroupingModel pattern: define groupId + children fields + headerName, pass as prop to DataGrid alongside columns"
  - "Multi-query refetch: allHorizonsQuery.results.forEach((r) => { void r.refetch(); }) for parallel query invalidation"

requirements-completed:
  - FCST-TABLE-01
  - FCST-EXPORT-01
  - FCST-UI-01

# Metrics
duration: 15min
completed: 2026-04-03
---

# Phase 88 Plan 03: Multi-Horizon Forecast Table Summary

**MUI DataGrid with 4 horizon column groups (1-Day, 7-Day, 14-Day, 30-Day Forecast), green/red return coloring, and flattened CSV/PDF export across all horizons**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-03T09:00:00Z
- **Completed:** 2026-04-03T09:15:00Z
- **Tasks:** 2 of 3 auto tasks complete (Task 3 is human-verify checkpoint)
- **Files modified:** 2

## Accomplishments
- Rewrote ForecastTable.tsx to accept MultiHorizonForecastRow[] and render 8 horizon data columns in 4 column groups (1-Day, 7-Day, 14-Day, 30-Day Forecast) using MUI DataGrid columnGroupingModel
- Rewired Forecasts.tsx to use useAllHorizonsPredictions for the main table, removed HorizonToggle from page header, added partial error Alert, and updated CSV/PDF export to flatten all 4 horizons
- TypeScript compiles cleanly with zero errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite ForecastTable.tsx for multi-horizon column groups** - `e65ed34` (feat)
2. **Task 2: Rewire Forecasts.tsx — use useAllHorizonsPredictions, update loading/error/export** - `c9052c6` (feat)
3. **Task 3: Playwright verification — multi-horizon table visual check** - checkpoint:human-verify (pending)

## Files Created/Modified
- `services/frontend/src/components/forecasts/ForecastTable.tsx` - Full replacement: MultiHorizonForecastRow[] rows, columnGroupingModel with 4 groups, 8 horizon columns with green/red return coloring and Tooltip predicted dates, default sort return_7d desc
- `services/frontend/src/pages/Forecasts.tsx` - Full replacement: useAllHorizonsPredictions for main table, separate useBulkPredictions(7) for ForecastRow consumers, HorizonToggle removed from header (kept in drawer), partial error Alert, CSV/PDF export updated

## Decisions Made
- Flatten MultiHorizonForecastRow.horizons map to flat fields (price_1d, return_1d, etc.) before passing to DataGrid — required for TypeScript to resolve types correctly in renderCell
- Keep separate useBulkPredictions(7) for comparison panel and detail drawer since those components use ForecastRow[] — simpler than refactoring
- Filter minReturn/maxReturn uses horizons[7] as reference column (matches default sort)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None — TypeScript compiled cleanly on first attempt after rewrite.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Multi-horizon forecast table is fully implemented and TypeScript-verified
- Awaiting visual confirmation via Playwright that column groups render in browser (Task 3 checkpoint)
- Once approved, Phase 88 is complete

---
*Phase: 88-add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab*
*Completed: 2026-04-03*
