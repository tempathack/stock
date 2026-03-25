---
phase: 61-playwright-e2e-tests-full-frontend-coverage
plan: 02
subsystem: testing
tags: [playwright, e2e, dashboard, navigation, react, vite, route-stubbing]

requires:
  - phase: 61-01
    provides: Playwright infrastructure, playwright.config.ts, stub specs for all 5 pages, fixtures/api.ts

provides:
  - Full Dashboard page E2E tests (treemap, ticker selection, TA panel toggle, close button)
  - Navigation tests for all 4 sidebar links (Forecasts, Models, Drift, Backtest)
  - stubAllRoutes helper function with correct LIFO route ordering
  - test.describe.configure({ mode: "serial" }) pattern for Vite dev server stability

affects:
  - 61-03 and later plans (LIFO route ordering pattern should be used in all specs that navigate across pages)

tech-stack:
  added: []
  patterns:
    - "LIFO route registration: register broad catch-alls (predict/**) FIRST, specific routes (predict/bulk, predict/horizons) LAST — Playwright evaluates routes in reverse registration order"
    - "Serial test mode: test.describe.configure({ mode: 'serial' }) prevents Vite dev server overload from 8 parallel page.goto() calls"
    - "Specific-origin backtest route: http://localhost:8000/backtest/** avoids intercepting Vite page navigation at localhost:3000"
    - "fixture_ prefix sentinel: model_name: 'fixture_stacking_ensemble_meta_ridge' distinguishes fixture data from mock fallback"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/e2e/dashboard.spec.ts

key-decisions:
  - "Playwright LIFO route matching: routes registered LAST match FIRST; broad catch-alls must be registered before specific routes so specific ones win"
  - "Serial mode for dashboard.spec.ts: 8 parallel browser instances overwhelm the single Vite dev server; page.goto() times out without serialization"
  - "Backtest route uses specific origin (http://localhost:8000/backtest/**) not glob (**) to prevent intercepting Vite app navigation"
  - "Drift page heading is 'Drift Monitoring', Backtest page heading is 'Backtest' — corrected from plan template which had wrong values"

patterns-established:
  - "stubAllRoutes helper: register predict/** first (catch-all), then specific routes last (predict/horizons, predict/bulk**)"
  - "Serial describe for file with 8+ tests sharing single Vite dev server"

requirements-completed: [TEST-PW-02]

duration: 15min
completed: 2026-03-25
---

# Phase 61 Plan 02: Dashboard + Navigation E2E Tests Summary

**8 Playwright tests covering Dashboard treemap interactions and sidebar navigation to all 4 pages, all using fixture-sentinel values to confirm real data paths over mock fallbacks**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-25T12:45:29Z
- **Completed:** 2026-03-25T12:58:47Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced the 1-test stub in dashboard.spec.ts with 8 full tests (4 navigation + 4 dashboard)
- Discovered and fixed Playwright LIFO route matching behavior that was silently swallowing predict/bulk and predict/horizons requests
- Resolved Vite dev server overload flakiness via test.describe.configure({ mode: 'serial' })
- All 8 tests pass consistently across 3 consecutive runs

## Task Commits

Each task was committed atomically:

1. **Task 1: Write full navigation tests** - `dbe2a6a` (feat)
2. **Task 1 stability fix** - `2c580eb` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `stock-prediction-platform/services/frontend/e2e/dashboard.spec.ts` - Full test suite: stubAllRoutes helper, 4 navigation tests, 4 dashboard tests with LIFO route order and serial execution mode

## Decisions Made

- **Playwright LIFO route matching:** After debugging showed `**/predict/**` was catching all predict requests despite `**/predict/bulk**` being registered first, discovered Playwright evaluates routes in LAST-IN-FIRST-OUT order. Fixed by registering broad catch-alls first, specific routes last.
- **Serial execution mode:** `test.describe.configure({ mode: 'serial' })` prevents 8 parallel browser instances from overloading the single Vite dev server (page.goto times out after 30s under load).
- **Corrected page headings:** Plan template had "Drift Monitor" and "Backtesting"; actual PageHeader titles are "Drift Monitoring" and "Backtest".
- **Backtest route specificity:** Used `http://localhost:8000/backtest/**` instead of `**/backtest/**` to avoid intercepting Vite page navigation to `localhost:3000/backtest`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed LIFO route order causing predict/bulk and predict/horizons to be shadowed**
- **Found during:** Task 1 (Write full navigation tests) — debugging flaky Forecasts navigation test
- **Issue:** `**/predict/**` was registered last in stubAllRoutes helper; since Playwright matches in LIFO order, it matched all `/predict/*` requests before `**/predict/bulk**` and `**/predict/horizons**` could match. Forecasts page stayed in loading state indefinitely.
- **Fix:** Reordered stubAllRoutes to register `**/predict/**` (catch-all) FIRST and specific routes (`predict/horizons`, `predict/bulk**`) LAST so they take priority
- **Files modified:** e2e/dashboard.spec.ts
- **Verification:** Forecasts page heading "Stock Forecasts" appeared after navigation; 8/8 tests pass
- **Committed in:** dbe2a6a (initial task commit), 2c580eb (stability fix)

**2. [Rule 1 - Bug] Fixed Vite dev server overload flakiness via serial execution**
- **Found during:** Task 1 verification — tests passed 1/3 runs under parallel load
- **Issue:** With 8 parallel workers all calling page.goto("/dashboard") simultaneously, the single Vite dev server timed out after 30s
- **Fix:** Added `test.describe.configure({ mode: 'serial' })` at file level to serialize all 8 tests
- **Files modified:** e2e/dashboard.spec.ts
- **Verification:** 3/3 consecutive runs pass (5.7s each)
- **Committed in:** 2c580eb

---

**Total deviations:** 2 auto-fixed (both Rule 1 - bugs in test infrastructure)
**Impact on plan:** Both fixes required for correct test behavior. No scope creep. The LIFO ordering insight is a critical pattern for all future specs that use stubAllRoutes-style helpers.

## Issues Encountered

- Playwright route matching is LIFO (not FIFO as documented examples suggest) — investigated with request interception logging before identifying root cause
- Vite dev server single-instance bottleneck with 8 parallel browsers — discovered via debug spec that all 8 page.goto() calls time out simultaneously

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Dashboard and Navigation tests complete with 8 passing tests
- LIFO route ordering pattern established — subsequent plans (61-03+) should register broad catch-alls before specific routes
- Serial execution mode pattern available for any spec file with many tests sharing the Vite dev server

---
*Phase: 61-playwright-e2e-tests-full-frontend-coverage*
*Completed: 2026-03-25*
