---
phase: 76-ux-polish
plan: "02"
subsystem: frontend-analytics
tags: [analytics, feature-freshness, olap, ticker-selector, ux]
dependency_graph:
  requires: []
  provides:
    - FeatureFreshnessPanel null staleness display fix
    - OLAPCandleChart dynamic ticker selector
  affects:
    - stock-prediction-platform/services/frontend/src/components/analytics/FeatureFreshnessPanel.tsx
    - stock-prediction-platform/services/frontend/src/components/analytics/OLAPCandleChart.tsx
tech_stack:
  added: []
  patterns:
    - Conditional rendering based on null data
    - Autocomplete driven by existing query hook
key_files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/components/analytics/FeatureFreshnessPanel.tsx
    - stock-prediction-platform/services/frontend/src/components/analytics/OLAPCandleChart.tsx
decisions:
  - "OLAPCandleChart uses disableClearable Autocomplete to prevent 404s from unknown tickers; freeSolo excluded"
  - "LinearProgress conditionally rendered only when staleness_seconds is non-null; uses type cast to satisfy MUI color prop constraint"
  - "Null staleness rows greyed out at 0.45 opacity rather than hidden to preserve context"
metrics:
  duration: "2m 4s"
  completed_date: "2026-04-02"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 76 Plan 02: Analytics null staleness display fix and OLAP ticker selector Summary

**One-liner:** Fixed null staleness em-dash + 0.45 opacity display in FeatureFreshnessPanel and added useMarketOverview-driven Autocomplete ticker selector to OLAPCandleChart.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix FeatureFreshnessPanel null staleness display | eca8784 | FeatureFreshnessPanel.tsx |
| 2 | Add ticker Autocomplete to OLAPCandleChart | 106cb75 | OLAPCandleChart.tsx |

## What Was Built

### Task 1: FeatureFreshnessPanel null staleness display

Three targeted changes to `FeatureFreshnessPanel.tsx`:

1. `getStalenessColor(null)` now returns `"inherit"` instead of `"warning"` — null staleness no longer renders amber
2. `formatStaleness(null)` now returns `"—"` (em-dash) instead of `"unknown"`
3. Row content wrapped in `<Box sx={{ opacity: view.staleness_seconds === null ? 0.45 : 1 }}>` — null rows visually greyed out; `LinearProgress` conditionally rendered only when `staleness_seconds !== null`

The `color` prop cast (`as "success" | "warning" | "error"`) on the conditional `LinearProgress` is safe: the branch only executes when `staleness_seconds` is non-null, so `getStalenessColor` never returns `"inherit"` there.

### Task 2: OLAPCandleChart ticker Autocomplete

Five changes to `OLAPCandleChart.tsx`:

1. Added `Autocomplete`, `TextField` to MUI imports; added `useMarketOverview` to queries import
2. Removed `DEFAULT_TICKER = "AAPL"` constant; added `useState("AAPL")` ticker state
3. Added `useMarketOverview()` call + `useMemo` to derive sorted tickers list with fallback to 5 known tickers
4. Changed `useAnalyticsCandles(DEFAULT_TICKER, interval)` to `useAnalyticsCandles(ticker, interval)`
5. Added `Autocomplete` (size=small, disableClearable, width=120) in panel header between title and interval toggle; updated aria-label to reference `ticker` state

## Decisions Made

- **disableClearable on Autocomplete:** Prevents user from clearing the ticker to empty string which would cause 404 from backend
- **No freeSolo:** Unlike Backtest.tsx which uses freeSolo, OLAP chart forces selection from known tickers only to avoid 404s on unknown tickers
- **Fallback ticker list:** `["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]` used when `marketQuery.data` is unavailable so the dropdown is never empty

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

- Project has no unit test framework (no vitest/jest — only Playwright E2E). Plan's `tdd="true"` and `npm test -- --run` verification adapted to TypeScript compilation (`npm run lint`) as the available correctness check.
- Pre-existing TypeScript errors in `MetricCards.tsx` and `Dashboard.tsx` are out-of-scope and not caused by these changes.
- `Backtest.tsx` has an unrelated pre-existing TS error (`string | null` vs `string`) from other in-progress stash work — out of scope, logged as deferred.

## Self-Check: PASSED

- FeatureFreshnessPanel.tsx: FOUND
- OLAPCandleChart.tsx: FOUND
- Commit eca8784 (Task 1): FOUND
- Commit 106cb75 (Task 2): FOUND
