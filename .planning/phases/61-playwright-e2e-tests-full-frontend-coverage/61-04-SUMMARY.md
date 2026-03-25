---
phase: 61-playwright-e2e-tests-full-frontend-coverage
plan: 04
subsystem: testing
tags: [playwright, e2e, react, models, drift, fixtures]

# Dependency graph
requires:
  - phase: 61-01
    provides: "Playwright infrastructure, fixture helpers, stub specs for models and drift"
provides:
  - Full Models page E2E tests (6 tests covering winner card, auto-select, table, search, export)
  - Full Drift page E2E tests (6 tests covering heading, ActiveModelCard, RetrainStatusPanel, DriftTimeline, RollingPerformanceChart)
affects:
  - Phase 62 (infra E2E tests depend on same Playwright setup and fixture patterns)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "stubModelsRoutes/stubDriftRoutes helper functions encapsulate all page.route() calls before page.goto()"
    - "serial mode (test.describe.configure) required when multiple spec files run together against single Vite dev server"
    - "Assert on rendered label text (e.g. 'Data') not raw API key (e.g. 'data_drift') when component maps values"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/e2e/models.spec.ts
    - stock-prediction-platform/services/frontend/e2e/drift.spec.ts

key-decisions:
  - "DriftTimeline renders label 'Data' from DRIFT_TYPE_STYLES map, not raw 'data_drift' key — assert on 'Data'"
  - "RollingPerformanceChart heading is 'Rolling Model Performance' — use /Rolling.*Performance/i regex"
  - "Serial mode added to models.spec.ts (same pattern as dashboard.spec.ts) to prevent Vite server overload when running combined test suites"
  - "rolling-performance route must be registered before models/drift in stubDriftRoutes (Playwright LIFO matching)"

patterns-established:
  - "Route helper pattern: all page.route() stubs centralized in a stubXxxRoutes() async function before page.goto()"
  - "Fixture sentinel pattern: fixture_ prefix on model names distinguishes E2E fixtures from mock fallbacks"
  - "Serial mode pattern: use test.describe.configure({ mode: 'serial' }) for all frontend spec files sharing a single Vite dev server"

requirements-completed:
  - TEST-PW-04

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 61 Plan 04: Models and Drift E2E Tests Summary

**Full Playwright E2E tests for Models and Drift pages with 12 tests total asserting fixture sentinel values and component-rendered labels.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T13:07:07Z
- **Completed:** 2026-03-25T13:11:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Replaced models.spec.ts stub with 6 full tests: winner card fixture sentinel, auto-select detail panel, table row count, search filter, table row click, export buttons enabled
- Replaced drift.spec.ts stub with 6 full tests: page heading, ActiveModelCard fixture sentinel, RetrainStatusPanel both models, DriftTimeline event label, RollingPerformanceChart container, no loading spinner
- Added serial mode to both specs to prevent Vite dev server overload when running combined suites

## Task Commits

Each task was committed atomically:

1. **Task 1: Write full Models page tests** - `7101314` (feat)
2. **Task 2: Write full Drift page tests** - `56e6277` (feat)

## Files Created/Modified
- `stock-prediction-platform/services/frontend/e2e/models.spec.ts` - 6 tests with stubModelsRoutes helper, serial mode
- `stock-prediction-platform/services/frontend/e2e/drift.spec.ts` - 6 tests with stubDriftRoutes helper, serial mode

## Decisions Made
- DriftTimeline renders "Data" label (from DRIFT_TYPE_STYLES map), not the raw "data_drift" API key
- RollingPerformanceChart heading is "Rolling Model Performance" — plan spec had "Rolling Performance" which was incorrect
- Serial mode required for models.spec.ts as well (same root cause as dashboard.spec.ts parallel overload issue)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] DriftTimeline assertion corrected from raw API key to rendered label**
- **Found during:** Task 2 (Write full Drift page tests)
- **Issue:** Plan spec asserted `page.getByText("data_drift")` but DriftTimeline component renders label "Data" (from DRIFT_TYPE_STYLES[drift_type].label map), not the raw key
- **Fix:** Changed assertion to check for "Data" text and "Drift Event Timeline" heading instead
- **Files modified:** stock-prediction-platform/services/frontend/e2e/drift.spec.ts
- **Verification:** Test passes with "Data" assertion, confirmed by page snapshot showing rendered label
- **Committed in:** 56e6277 (Task 2 commit)

**2. [Rule 1 - Bug] RollingPerformanceChart regex updated to match actual heading**
- **Found during:** Task 2 (Write full Drift page tests)
- **Issue:** Plan spec regex `/Rolling Performance|Performance Over Time/i` did not match actual heading "Rolling Model Performance"
- **Fix:** Changed regex to `/Rolling.*Performance|Performance Over Time/i` to match "Rolling Model Performance"
- **Files modified:** stock-prediction-platform/services/frontend/e2e/drift.spec.ts
- **Verification:** Test passes, confirmed by page snapshot showing heading text
- **Committed in:** 56e6277 (Task 2 commit)

**3. [Rule 1 - Bug] Added serial mode to both specs to prevent parallel overload**
- **Found during:** Task 2 combined verification (models.spec.ts + drift.spec.ts together)
- **Issue:** 12 tests running in parallel with 7 workers overwhelmed single Vite dev server; individual files pass but combined run fails
- **Fix:** Added `test.describe.configure({ mode: "serial" })` to both models.spec.ts and drift.spec.ts
- **Files modified:** stock-prediction-platform/services/frontend/e2e/models.spec.ts, drift.spec.ts
- **Verification:** Combined run of 12 tests passes with 2 workers (serial within each describe block)
- **Committed in:** 56e6277 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 bugs — plan spec assertions did not match component-rendered output)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep. Tests still verify the intended behaviors via equivalent assertions.

## Issues Encountered
- The plan spec had incorrect text assertions for DriftTimeline and RollingPerformanceChart; corrected by inspecting component source and page snapshots from failed test artifacts

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Models and Drift page E2E coverage complete; TEST-PW-04 requirement satisfied
- All 12 tests (6 models + 6 drift) pass in chromium with serial mode
- Ready for Phase 62 infra E2E tests

---
*Phase: 61-playwright-e2e-tests-full-frontend-coverage*
*Completed: 2026-03-25*
