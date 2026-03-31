---
phase: 74-frontend-rendering-bug-fixes-models-duplicate-rows-react-key-collision-treemap-aapl-contrast-stock-drawer-wrong-selection
plan: 01
subsystem: ui
tags: [react, mui, datagrid, recharts, useCallback, getRowId, stale-closure]

# Dependency graph
requires:
  - phase: 28-frontend-dashboard
    provides: Dashboard.tsx and MarketTreemap wiring
  - phase: 26-frontend-models
    provides: ModelComparisonTable.tsx DataGrid component
provides:
  - Collision-proof getRowId using saved_at as secondary key for ModelComparisonTable
  - Stable handleSelect reference via useCallback preventing stale closure in Recharts Treemap
affects: [dashboard, models, treemap, stock-drawer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Use saved_at ISO timestamp as secondary unique key when version is nullable"
    - "Wrap event callbacks passed to child component props in useCallback to prevent stale closures in Recharts content renderers"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/components/tables/ModelComparisonTable.tsx
    - stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx

key-decisions:
  - "Use row.saved_at as secondary fallback in getRowId — ISO timestamp is unique per training run even when version is null"
  - "Use double-underscore separator in getRowId to avoid false collisions from model names containing hyphens"
  - "useCallback deps array is empty because setSelected is stable from useState and detailRef is a mutable ref, neither triggers re-renders"

patterns-established:
  - "Pattern: getRowId with nullable fields — always provide non-empty stable fallback, prefer saved_at over Math.random()"
  - "Pattern: callbacks passed as props to components with their own useCallback — always stabilise with useCallback at call site"

requirements-completed: [FDASH-01, FDASH-02, FMOD-01]

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 74 Plan 01: Frontend Rendering Bug Fixes — Duplicate Rows & Stale Closure Summary

**Fixed null-version DataGrid key collision in ModelComparisonTable and stale-closure wrong-stock bug in Dashboard treemap via saved_at fallback and useCallback memoisation**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-31T14:35:00Z
- **Completed:** 2026-03-31T14:38:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Replaced empty-string version fallback in getRowId with saved_at ISO timestamp — unique per training run, prevents DataGrid row deduplication hiding trained models
- Wrapped handleSelect in useCallback with stable empty-deps array — Recharts Treemap content renderer always fires the current callback for the actually-clicked ticker
- No new TypeScript errors introduced (pre-existing errors in MetricCards.tsx and unused Chip import are out of scope)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix ModelComparisonTable duplicate row key collision** - `2ea3213` (fix)
2. **Task 2: Fix Dashboard stale closure in handleSelect** - `cb4e453` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `stock-prediction-platform/services/frontend/src/components/tables/ModelComparisonTable.tsx` - getRowId now uses `model_name__scaler_variant__${version ?? saved_at ?? "nv"}` pattern
- `stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx` - useCallback added to imports; handleSelect wrapped with useCallback and empty deps array

## Decisions Made

- Used `row.saved_at` as secondary fallback (not `Math.random()`) — DataGrid reconciliation requires stable IDs across re-renders; Math.random() would cause every render to assign new IDs
- Double-underscore separator chosen to avoid false collision with model names or scaler variants that contain hyphens
- Empty deps array `[]` for handleSelect useCallback is correct: `setSelected` is referentially stable from useState, and `detailRef.current` is a ref accessed imperatively — not a reactive dependency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both fixes were straightforward targeted edits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Models table will now show all trained models without hidden rows when multiple rows share the same model_name + scaler_variant but have null version
- Dashboard treemap click-to-open-drawer will now consistently open the clicked stock's detail panel, not a previously rendered stock
- Ready for Phase 74 Plan 02 (next plan in phase)

---
*Phase: 74-frontend-rendering-bug-fixes-models-duplicate-rows-react-key-collision-treemap-aapl-contrast-stock-drawer-wrong-selection*
*Completed: 2026-03-31*
