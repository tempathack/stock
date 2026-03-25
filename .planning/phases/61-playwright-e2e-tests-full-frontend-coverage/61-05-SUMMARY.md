---
phase: 61-playwright-e2e-tests-full-frontend-coverage
plan: 05
subsystem: testing
tags: [playwright, e2e, backtest, frontend, react, vite]

# Dependency graph
requires:
  - phase: 61-01
    provides: Playwright infrastructure, fixture helpers, spec stubs for all 5 pages
  - phase: 61-03
    provides: forecasts.spec.ts with 7 tests (missing serial mode)
  - phase: 61-04
    provides: models.spec.ts and drift.spec.ts with serial mode pattern
provides:
  - Full Backtest page E2E test suite (7 tests, 110 lines)
  - All 5 spec files passing (34 total tests) with npm run test:e2e --project=chromium
affects: [phase-62-playwright-e2e-infra]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Serial mode required for all spec files sharing a single Vite dev server
    - Use specific origin http://localhost:8000/backtest/** instead of **/backtest/** to avoid intercepting Vite HMR source modules
    - stubHelper pattern: register all routes before page.goto()
    - Horizon span assertion: page.locator("span").filter({ hasText: /^7d$/ }) avoids matching hidden select options

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/e2e/backtest.spec.ts
    - stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts

key-decisions:
  - "backtest.spec.ts uses http://localhost:8000/backtest/** (specific origin) — **/backtest/** intercepts Vite source module requests and prevents page render"
  - "test.describe.configure({ mode: 'serial' }) added to backtest.spec.ts — parallel workers overwhelm single Vite dev server"
  - "forecasts.spec.ts needed serial mode added (auto-fix Rule 1) — was causing TimeoutError 180000ms in full suite parallel run"
  - "Horizon 7d asserted via page.locator('span').filter({ hasText: /^7d$/ }) — getByText(/7d/).first() resolved to hidden select option"

patterns-established:
  - "Pattern: All spec files use test.describe.configure({ mode: 'serial' }) for Vite dev server stability"
  - "Pattern: API routes using specific paths (localhost:8000) prevent Vite source module interception"

requirements-completed: [TEST-PW-05]

# Metrics
duration: 15min
completed: 2026-03-25
---

# Phase 61 Plan 05: Backtest Page E2E Tests Summary

**7 Backtest E2E tests covering initial load, ticker select, date inputs, horizon options, Run Backtest button, metrics summary, and export buttons — full 34-test suite passes across all 5 spec files**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-25T13:15:00Z
- **Completed:** 2026-03-25T13:30:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Replaced backtest.spec.ts stub with 7 complete tests covering all TEST-PW-05 acceptance criteria
- Fixed forecasts.spec.ts missing serial mode that caused full suite TimeoutError 180000ms
- Full suite of 34 tests across 5 spec files now passes: dashboard (8) + forecasts (7) + models (6) + drift (6) + backtest (7)
- Confirmed fixture sentinel values: fixture_stacking_ensemble_meta_ridge in model banner, RMSE 3.45 and MAE 2.87 in BacktestMetricsSummary

## Task Commits

Each task was committed atomically:

1. **Task 1: Write full Backtest page tests** - `20bf6cb` (feat)
2. **Task 2: Verify full suite passes (all 5 spec files)** - `bf39a85` (fix)

## Files Created/Modified
- `stock-prediction-platform/services/frontend/e2e/backtest.spec.ts` - Full Backtest page tests (110 lines, 7 tests, serial mode, http://localhost:8000 origin pattern)
- `stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts` - Added missing serial mode (auto-fix)

## Decisions Made
- Used `http://localhost:8000/backtest/**` instead of `**/backtest/**` because the broad glob intercepted Vite's source module serving, causing the Backtest page component to never render (empty `<main>` element)
- Added `test.describe.configure({ mode: "serial" })` to backtest.spec.ts — same pattern as models.spec.ts and drift.spec.ts
- For horizon "7d" assertion: `page.getByText(/7d/).first()` resolved to a hidden `<option>` element; used `page.locator("span").filter({ hasText: /^7d$/ }).first()` to target the visible model banner span

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed forecasts.spec.ts missing serial mode causing full suite TimeoutError**
- **Found during:** Task 2 (full suite verification)
- **Issue:** forecasts.spec.ts lacked `test.describe.configure({ mode: "serial" })`. When running all 5 spec files in parallel, the 7 Forecasts tests launched parallel browser instances that caused `TimeoutError: browserType.launch: Timeout 180000ms exceeded` — 8 total test failures
- **Fix:** Added `test.describe.configure({ mode: "serial" })` to the Forecasts page describe block
- **Files modified:** stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts
- **Verification:** Full suite runs 34 tests, all pass in 12.2s
- **Committed in:** bf39a85 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** Essential fix — without it the full suite acceptance criteria could not be met. No scope creep.

## Issues Encountered
- `**/backtest/**` glob intercepted Vite source module HMR requests, preventing the Backtest component from mounting (empty `<main>`). Resolved by switching to the specific origin `http://localhost:8000/backtest/**` per prior STATE.md decision.
- `page.getByText(/7d/).first()` matched a hidden `<option value="7">7d</option>` element instead of the visible model banner span. Resolved using `page.locator("span").filter({ hasText: /^7d$/ }).first()`.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 Playwright spec files complete and green (34 tests total)
- Phase 61 Playwright E2E coverage complete: Dashboard, Forecasts, Models, Drift, Backtest
- Ready for Phase 62: playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard

---
*Phase: 61-playwright-e2e-tests-full-frontend-coverage*
*Completed: 2026-03-25*
