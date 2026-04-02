---
phase: 77-fix-flink-pipeline-health-and-forecasts-blank-screen
plan: 01
subsystem: ui
tags: [react, mui, skeleton, forecasts, error-handling]

# Dependency graph
requires:
  - phase: 27-frontend-forecasts-page
    provides: Forecasts.tsx with bulkQuery/marketQuery hooks
provides:
  - Skeleton loading layout for /forecasts page (10 rows, PageHeader visible immediately)
  - Correct partial-failure logic: bulkQuery failure shows ErrorFallback, marketQuery failure renders em-dash
affects: [frontend, forecasts, ux]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Skeleton loading via MUI Skeleton with Array.from({ length: N }).map() pattern"
    - "Partial-failure useMemo: lead query drives render, secondary query falls back to []"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/pages/Forecasts.tsx

key-decisions:
  - "Remove TableCell and TableRow from imports — skeleton uses Box/Skeleton only, unused imports broke TS build"
  - "marketQuery partial failure: pass empty array to joinForecastData rather than skipping render entirely"
  - "bulkQuery.isError alone gates ErrorFallback — marketQuery failure should not block the table"

patterns-established:
  - "Skeleton layout: always render PageHeader + primary controls first, fill table area with N=10 rectangular skeletons"
  - "Partial-failure: secondary data queries fall back to [] not mock data"

requirements-completed: [FFOR-FIX-01]

# Metrics
duration: 2min
completed: 2026-04-02
---

# Phase 77 Plan 01: Fix Forecasts Blank Screen Summary

**Skeleton loading layout replaces blank screen on /forecasts; generateMockForecasts removed; bulkQuery-only error gate implements correct partial-failure behavior**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-02T11:33:54Z
- **Completed:** 2026-04-02T11:35:23Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Replaced `if (isLoading) return null` with skeleton layout showing PageHeader, HorizonToggle, and 10 MUI Skeleton rows
- Removed `generateMockForecasts` import and call — no more silent mock data masking API failures
- Implemented correct partial-failure: bulkQuery failure shows ErrorFallback; marketQuery failure renders table with em-dash in company_name/sector columns
- TypeScript compiles clean (exit 0)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix loading state — replace return null with skeleton layout** - `99f25eb` (feat)
2. **Task 2: Fix partial-failure error logic — remove mock fallback** - `7b821dd` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `stock-prediction-platform/services/frontend/src/pages/Forecasts.tsx` - Skeleton loading layout, removed mock fallback, corrected error gates

## Decisions Made
- `TableCell` and `TableRow` were in the plan's import list but were not used in the skeleton implementation (skeleton uses `Box` and `Skeleton` only). Removed to fix TS6133 unused-import errors.
- `marketQuery` partial failure uses `marketQuery.data?.stocks ?? []` so `joinForecastData` runs with an empty stock list — rows still render with em-dash for company/sector columns via existing `fmt()` helper.
- `isError` combined variable removed entirely since it mixed two distinct failure modes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused TableCell and TableRow imports**
- **Found during:** Task 2 (TypeScript compilation check)
- **Issue:** Plan instructed adding `TableCell` and `TableRow` to MUI imports but the skeleton implementation never uses them, causing TS6133 "declared but never read" errors and a non-zero tsc exit code
- **Fix:** Removed `TableCell` and `TableRow` from the MUI import block
- **Files modified:** stock-prediction-platform/services/frontend/src/pages/Forecasts.tsx
- **Verification:** `npx tsc --noEmit` exits 0 after removal
- **Committed in:** `7b821dd` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix)
**Impact on plan:** Fix was required for TypeScript correctness. Unused imports cause TS errors in strict mode. No scope creep.

## Issues Encountered
None beyond the unused import TS error described above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- /forecasts page now shows a structured loading state (no more blank white screen)
- Error states are accurate: bulkQuery failure triggers ErrorFallback, marketQuery failure degrades gracefully
- generateMockForecasts is no longer in the production code path

---
*Phase: 77-fix-flink-pipeline-health-and-forecasts-blank-screen*
*Completed: 2026-04-02*
