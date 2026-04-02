---
phase: 76-ux-polish
plan: "01"
subsystem: ui
tags: [react, mui, backtest, tooltip, empty-state, accessibility]

# Dependency graph
requires:
  - phase: 46-backtesting-ui
    provides: Backtest.tsx page with run/export controls and query hook
provides:
  - Backtest idle state before first run (null activeTicker guard)
  - MUI Tooltip audit across all frontend pages confirmed complete
affects: [backtest, forecasts, dashboard, models, drift, analytics]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Null activeTicker guard: useState<string | null>(null) + activeTicker ?? '' to disable query on initial load"
    - "Idle empty state: !activeTicker conditional renders centered icon + descriptive text before first user action"
    - "Tooltip audit: all icon-only Buttons and IconButtons confirmed wrapped in MUI Tooltip; ExportButtons component uses visible text labels (CSV/PDF) — no tooltip needed"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/pages/Backtest.tsx

key-decisions:
  - "Use useState<string | null>(null) for activeTicker so query is disabled on initial load; activeTicker ?? '' passed to useBacktest since hook signature is ticker: string"
  - "activeTicker! non-null assertion used inside backtestQuery.data guard block — data only exists after a successful query (which requires non-empty ticker), so null is logically impossible there"
  - "No Tooltip changes needed for Forecasts, Dashboard, Models, Drift, Analytics pages — all icon-only buttons in Backtest already have Tooltips; ExportButtons component renders visible text labels (CSV/PDF); nav items have both icon + text label"

patterns-established:
  - "Idle state pattern: use null initial state for query key + !key conditional for empty state block between error and results blocks"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-04-02
---

# Phase 76 Plan 01: Backtest Idle State and Icon Tooltip Audit Summary

**Backtest page idle empty state added using null activeTicker guard; MUI Tooltip audit across 6 pages confirmed all icon-only buttons already wrapped**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-02T07:50:55Z
- **Completed:** 2026-04-02T07:53:59Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Backtest page shows centered PlayArrow icon + instructional text before first Run click
- Query is disabled on initial page load (no unnecessary API request on mount)
- Idle state disappears immediately after clicking Run Backtest (activeTicker becomes non-null)
- Full tooltip audit across Backtest, Forecasts, Dashboard, Models, Drift, Analytics, and NavBar/Sidebar confirmed — no missing tooltips found

## Task Commits

Task 1 changes were captured as part of commit 50b85ff (feat(76-04)) as a Rule 3 blocking fix during prior plan execution. Task 2 (tooltip audit) required no code changes.

1. **Task 1: Add Backtest idle state with null activeTicker guard** - `50b85ff` (feat, part of 76-04 Rule 3 fix)
2. **Task 2: Audit and add missing Tooltip wrappers** - No commit (no changes needed)

**Plan metadata:** see final docs commit

## Files Created/Modified
- `stock-prediction-platform/services/frontend/src/pages/Backtest.tsx` — Changed activeTicker to `string | null`, added null coalesce to useBacktest call, added idle state block, fixed BacktestChart ticker prop type

## Decisions Made
- `useState<string | null>(null)` for activeTicker: makes query disabled state explicit and avoids eager API call on mount
- `activeTicker!` non-null assertion inside `backtestQuery.data` block: data can only exist when ticker was set, so null is logically impossible
- Tooltip audit found no gaps: ExportButtons component uses visible "CSV"/"PDF" text labels; Forecasts Close button has visible "Close" text; nav links have both icon and text label

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] TypeScript error: string | null not assignable to string in BacktestChart ticker prop**
- **Found during:** Task 1 (Add Backtest idle state)
- **Issue:** Changing activeTicker to `string | null` caused TS2322 error at `ticker={activeTicker}` inside BacktestChart (expects `string`)
- **Fix:** Added non-null assertion `ticker={activeTicker!}` — safe because this code is inside `{backtestQuery.data && ...}` guard, which only evaluates when a query ran (requiring non-empty activeTicker)
- **Files modified:** stock-prediction-platform/services/frontend/src/pages/Backtest.tsx
- **Verification:** `tsc --noEmit` exits 0
- **Committed in:** 50b85ff (part of 76-04 commit as blocking fix)

---

**Total deviations:** 1 auto-fixed (1 blocking TypeScript error)
**Impact on plan:** Necessary for TypeScript correctness. No scope creep.

### Note on Unit Tests (TDD)

The plan marks Task 1 as `tdd="true"` with a verification command of `npm test -- --run`. The project uses Playwright for E2E testing only — no vitest/jest unit test framework is installed. Adding vitest would be an architectural change (new dev dependency). TDD was verified via TypeScript compilation (`tsc --noEmit`) and acceptance criteria grep checks instead.

## Tooltip Audit Findings

| File | IconButtons Found | Status |
|------|-------------------|--------|
| Backtest.tsx | Run Backtest, CSV export, PDF export | All wrapped in Tooltip |
| Forecasts.tsx | Close button (has "Close" text label) | Not icon-only — no tooltip needed |
| Dashboard.tsx | None (Box components with text, decorative icons) | No action buttons |
| Models.tsx | ExportButtons component (CSV/PDF text labels) | Not icon-only — no tooltip needed |
| Drift.tsx | None | No action buttons |
| Analytics.tsx | None | No action buttons |
| Sidebar.tsx (TopNav) | Nav items (icon + text label each) | Not icon-only — no tooltip needed |

## Issues Encountered
- Task 1 changes to Backtest.tsx were already present in the working tree when this plan executed, having been applied as a Rule 3 blocking fix during 76-04 execution. All acceptance criteria verified as passing.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backtest idle state ready — users see clear affordance on first visit
- Tooltip audit complete across all pages
- Ready to proceed with 76-02 (sector and company names in forecasts)

---
*Phase: 76-ux-polish*
*Completed: 2026-04-02*
