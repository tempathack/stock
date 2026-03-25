---
phase: 61-playwright-e2e-tests-full-frontend-coverage
plan: 01
subsystem: testing
tags: [playwright, typescript, e2e, react, vite, chromium]

# Dependency graph
requires:
  - phase: 25-50-frontend-pages
    provides: "Dashboard, Forecasts, Models, Drift, Backtest React pages with PageHeader h1 elements"
  - phase: 46-backtesting-ui
    provides: "Backtest page at /backtest route"
provides:
  - "@playwright/test 1.58.2 installed with chromium browser downloaded"
  - "playwright.config.ts with webServer pointing to npm run dev on port 3000"
  - "e2e/fixtures/api.ts with 10 typed factory functions (all API response shapes)"
  - "5 stub spec files: dashboard, forecasts, models, drift, backtest — all passing"
affects:
  - 61-02-dashboard-spec
  - 61-03-forecasts-spec
  - 61-04-models-drift-spec
  - 61-05-backtest-spec

# Tech tracking
tech-stack:
  added: ["@playwright/test@1.58.2", "chromium headless shell v1208"]
  patterns:
    - "page.route() registered BEFORE page.goto() for reliable API interception"
    - "Fixture model names use fixture_ prefix to distinguish from mock fallback values"
    - "Specific origin URL (http://localhost:8000/backtest/**) required when glob pattern would match Vite source modules"
    - "Rolling-performance route registered BEFORE models/drift due to path prefix matching"

key-files:
  created:
    - stock-prediction-platform/services/frontend/playwright.config.ts
    - stock-prediction-platform/services/frontend/e2e/fixtures/api.ts
    - stock-prediction-platform/services/frontend/e2e/dashboard.spec.ts
    - stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts
    - stock-prediction-platform/services/frontend/e2e/models.spec.ts
    - stock-prediction-platform/services/frontend/e2e/drift.spec.ts
    - stock-prediction-platform/services/frontend/e2e/backtest.spec.ts
  modified:
    - stock-prediction-platform/services/frontend/package.json
    - .gitignore

key-decisions:
  - "Drift page heading is Drift Monitoring not Drift Monitor — spec corrected to match actual page"
  - "Backtest page heading is Backtest not Backtesting — spec corrected to match actual page"
  - "backtest.spec.ts uses http://localhost:8000/backtest/** not **/backtest/** to avoid intercepting Vite source file http://localhost:3000/src/pages/Backtest.tsx"
  - "playwright-report/ and test-results/ added to .gitignore as generated artifacts"

patterns-established:
  - "Pattern 1: All route mocks registered before page.goto() — required by Playwright for reliable interception"
  - "Pattern 2: Use specific origin prefix for backend routes that share path segments with source file names"
  - "Pattern 3: fixture_ prefix in model_name fields distinguishes fixture data from mock fallback data"

requirements-completed: [TEST-PW-01]

# Metrics
duration: 8min
completed: 2026-03-25
---

# Phase 61 Plan 01: Playwright Infrastructure and Stub Specs Summary

**@playwright/test 1.58.2 installed with chromium, playwright.config.ts configured, 10-factory fixture file typed against src/api/types.ts, and 5 passing stub specs establishing the Wave 1 test gate**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-25T12:34:01Z
- **Completed:** 2026-03-25T12:41:47Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Playwright 1.58.2 installed with Chromium headless shell, 4 npm test scripts added
- playwright.config.ts created with webServer pointing to `npm run dev` on port 3000
- e2e/fixtures/api.ts exports 10 typed factory functions covering all API response shapes
- All 5 stub spec files pass: `npx playwright test --project=chromium` exits 0 with 5 tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Playwright, create playwright.config.ts and add npm scripts** - `904111d` (feat)
2. **Task 2: Create e2e/fixtures/api.ts and all 5 stub spec files** - `66f3bf2` (feat)

## Files Created/Modified

- `stock-prediction-platform/services/frontend/playwright.config.ts` - Playwright config with webServer, chromium project, baseURL
- `stock-prediction-platform/services/frontend/package.json` - Added @playwright/test devDep + 4 test scripts
- `stock-prediction-platform/services/frontend/e2e/fixtures/api.ts` - 10 factory functions typed against src/api/types.ts, sentinel fixture_ prefix
- `stock-prediction-platform/services/frontend/e2e/dashboard.spec.ts` - Stub for /dashboard (Market Dashboard h1)
- `stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts` - Stub for /forecasts (Stock Forecasts h1)
- `stock-prediction-platform/services/frontend/e2e/models.spec.ts` - Stub for /models (Model Comparison h1)
- `stock-prediction-platform/services/frontend/e2e/drift.spec.ts` - Stub for /drift (Drift Monitoring h1)
- `stock-prediction-platform/services/frontend/e2e/backtest.spec.ts` - Stub for /backtest (Backtest h1)
- `.gitignore` - Added playwright-report/ and test-results/ exclusions

## Decisions Made

- Drift page heading is "Drift Monitoring" not "Drift Monitor" as the plan specified — corrected to match actual PageHeader title in src/pages/Drift.tsx
- Backtest page heading is "Backtest" not "Backtesting" as the plan specified — corrected to match actual PageHeader title in src/pages/Backtest.tsx
- backtest.spec.ts uses `http://localhost:8000/backtest/**` (specific origin) instead of `**/backtest/**` (glob) to avoid intercepting Vite module requests to `http://localhost:3000/src/pages/Backtest.tsx`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected spec heading names to match actual page titles**
- **Found during:** Task 2 (running npx playwright test --project=chromium)
- **Issue:** Plan specified "Drift Monitor" and "Backtesting" but actual pages render "Drift Monitoring" and "Backtest" respectively
- **Fix:** Updated drift.spec.ts `toBeVisible({ name: "Drift Monitoring" })` and backtest.spec.ts `toBeVisible({ name: "Backtest" })`
- **Files modified:** e2e/drift.spec.ts, e2e/backtest.spec.ts
- **Verification:** All 5 tests pass after correction
- **Committed in:** 66f3bf2 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed backtest route pattern to avoid intercepting Vite source files**
- **Found during:** Task 2 (npx playwright test e2e/backtest.spec.ts - page error in console)
- **Issue:** `**/backtest/**` glob intercepted `http://localhost:3000/src/pages/Backtest.tsx` Vite module request, returning application/json MIME type causing "Failed to load module script" error — page never rendered
- **Fix:** Changed pattern to `http://localhost:8000/backtest/**` with explicit origin to only intercept backend API calls
- **Files modified:** e2e/backtest.spec.ts
- **Verification:** Backtest page renders and "Backtest" h1 is visible
- **Committed in:** 66f3bf2 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - bugs where spec content mismatched actual behavior)
**Impact on plan:** Both fixes essential for tests to pass. No scope creep. Spec content corrected to match reality.

## Issues Encountered

- Stale Vite process on port 3000 (returning 404) from a prior test run caused intermittent blank page renders. Playwright's `reuseExistingServer: true` picked up the stale server. Resolved by killing port 3000 before each test run during development. In CI (`process.env.CI`), `reuseExistingServer: false` prevents this issue.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 1 gate complete: all 5 stub spec files exist and pass
- Wave 2 plans (61-02 through 61-05) can now fill in full test implementations
- The fixture_ sentinel prefix pattern is established for use in all Wave 2 route mocks
- Note for Wave 2: use specific origin patterns (e.g., `http://localhost:8000/...`) for any API path that shares a name with a source file in the frontend

---
*Phase: 61-playwright-e2e-tests-full-frontend-coverage*
*Completed: 2026-03-25*

## Self-Check: PASSED

- All 7 artifact files confirmed on disk
- Commits 904111d and 66f3bf2 confirmed in git history
- SUMMARY.md present at .planning/phases/61-playwright-e2e-tests-full-frontend-coverage/61-01-SUMMARY.md
