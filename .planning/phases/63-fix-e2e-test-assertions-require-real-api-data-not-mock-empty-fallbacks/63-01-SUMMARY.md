---
phase: 63-fix-e2e-test-assertions-require-real-api-data-not-mock-empty-fallbacks
plan: 01
subsystem: testing
tags: [playwright, e2e, frontend, typescript, api-guards]

# Dependency graph
requires:
  - phase: 61-playwright-e2e-tests-full-frontend-coverage
    provides: "Playwright E2E spec files for all 4 frontend pages"
provides:
  - "dashboard.spec.ts with beforeAll health + GET /market/overview guards (2 describe blocks)"
  - "models.spec.ts with beforeAll health + GET /models/comparison guard"
  - "drift.spec.ts with beforeAll health + GET /models/comparison + GET /models/drift guards"
  - "forecasts.spec.ts with beforeAll health + GET /predict/bulk guard"
affects: [e2e-testing, playwright, ci-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "beforeAll API guard pattern: request.newContext() + health check + data endpoint check + test.skip() on failure"
    - "Layered skip guards: health first, then endpoint-specific data count check"
    - "finally { await ctx.dispose() } for resource cleanup in all beforeAll blocks"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/e2e/dashboard.spec.ts
    - stock-prediction-platform/services/frontend/e2e/models.spec.ts
    - stock-prediction-platform/services/frontend/e2e/drift.spec.ts
    - stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts

key-decisions:
  - "beforeAll blocks placed inside each test.describe block (not file top-level) so test.skip() scopes correctly to that suite"
  - "Both describe blocks in dashboard.spec.ts (Navigation + Dashboard page) each get their own beforeAll — Navigation tests navigate between pages and need data too"
  - "drift.spec.ts guards both /models/comparison and /models/drift — ActiveModelCard needs comparison data, DriftTimeline needs drift events"
  - "request imported from @playwright/test at file top alongside test and expect — avoids { request } parameter anti-pattern"
  - "5_000ms timeout on all ctx.get() calls matches infra spec pattern established in Phase 62"

patterns-established:
  - "API health gate pattern: check /health first, then check data endpoint, skip on either failure or empty data"
  - "Use absolute URLs (http://localhost:8000/...) in beforeAll API calls — no baseURL for backend calls from test setup"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-25
---

# Phase 63 Plan 01: Fix E2E Test Assertions — Require Real API Data Summary

**Added beforeAll API health + real-data guards to all 4 Playwright spec files so tests skip (not fail) when backend has no live seeded data, eliminating false-positive passes via mock/empty fallbacks**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T15:37:07Z
- **Completed:** 2026-03-25T15:39:30Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Added `request` import from `@playwright/test` to all 4 spec files
- Added `test.beforeAll` inside every `test.describe` block (2 in dashboard.spec.ts, 1 each in models/drift/forecasts)
- Each beforeAll checks `/health` first then endpoint-specific data: `/market/overview` stocks.length, `/models/comparison` models.length, `/models/drift` events.length, `/predict/bulk` predictions.length
- All 4 files compile cleanly with TypeScript (`tsc --noEmit` exits 0)
- Playwright `--list` dry-run confirms 53 tests parse correctly across 10 spec files

## Task Commits

Each task was committed atomically:

1. **Task 1: Add beforeAll health + market data guard to dashboard.spec.ts** - `8596d0d` (feat)
2. **Task 2: Add beforeAll health + models data guard to models.spec.ts** - `5611516` (feat)
3. **Task 3: Add beforeAll health + drift data guard to drift.spec.ts** - `0ec6f10` (feat)
4. **Task 4: Add beforeAll health + predictions data guard to forecasts.spec.ts** - `c882af4` (feat)

## Files Created/Modified

- `stock-prediction-platform/services/frontend/e2e/dashboard.spec.ts` — Added `request` import + 2 `test.beforeAll` blocks (one per describe block) with health + /market/overview stocks.length guard
- `stock-prediction-platform/services/frontend/e2e/models.spec.ts` — Added `request` import + 1 `test.beforeAll` with health + /models/comparison models.length guard; `rows.toHaveCount(2)` fixture contract preserved
- `stock-prediction-platform/services/frontend/e2e/drift.spec.ts` — Added `request` import + 1 `test.beforeAll` with health + /models/comparison + /models/drift events.length dual guard
- `stock-prediction-platform/services/frontend/e2e/forecasts.spec.ts` — Added `request` import + 1 `test.beforeAll` with health + /predict/bulk predictions.length guard

## Decisions Made

- Both describe blocks in `dashboard.spec.ts` get separate `beforeAll` blocks. The Navigation tests navigate from `/dashboard` to other pages — they also depend on the backend being live and seeded, so both suites need the guard independently.
- `drift.spec.ts` checks both `/models/comparison` and `/models/drift` because the Drift page renders `ActiveModelCard` (uses comparison data) and `DriftTimeline` (uses drift events) — either missing means a broken page.
- `test.skip(true, message)` inside `beforeAll` skips the entire containing describe suite gracefully — no test failure, just a skip with an actionable message pointing to the seed/training pipeline script.
- `models.spec.ts` `rows.toHaveCount(2)` assertion left unchanged — it's a fixture contract assertion (fixture always returns exactly 2 models via `page.route()` stub), not a live API assertion.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 4 spec files now require a live, seeded backend — tests that previously silently passed via mock fallbacks will now skip with actionable messages
- CI pipelines that run E2E tests without a seeded backend will see skipped (not failed) suites
- The seed data script (`stock-prediction-platform/scripts/seed-data.sh`) and training pipeline must be run before E2E tests will execute

---
*Phase: 63-fix-e2e-test-assertions-require-real-api-data-not-mock-empty-fallbacks*
*Completed: 2026-03-25*
