---
phase: 95-dashboard-macro-panel
plan: 02
subsystem: ui
tags: [react, typescript, mui, react-query, dashboard, macro-indicators]

# Dependency graph
requires:
  - phase: 95-01
    provides: /api/macro/latest (GET /market/macro/latest) returning MacroLatestResponse

provides:
  - MacroPanel.tsx — 9-card macro environment grid component
  - useMacroLatest() React Query hook (60s auto-refresh)
  - MacroLatest TypeScript interface
  - fetchMacroLatest() fetch function
  - Dashboard integration: Macro Environment section below Market Sentiment

affects: [dashboard, macro-panel, fred-features, phase-94]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useQuery hook with retry=false and refetchInterval for background data refresh"
    - "Indicator card grid: 3-col desktop / 2-col tablet / 1-col mobile via MUI Grid breakpoints"
    - "Color-coded status icons: TrendingUp (green) / TrendingDown (red) / Remove (gray neutral)"

key-files:
  created:
    - stock-prediction-platform/services/frontend/src/components/dashboard/MacroPanel.tsx
  modified:
    - stock-prediction-platform/services/frontend/src/api/client.ts
    - stock-prediction-platform/services/frontend/src/api/types.ts
    - stock-prediction-platform/services/frontend/src/api/queries.ts
    - stock-prediction-platform/services/frontend/src/components/dashboard/index.ts
    - stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx

key-decisions:
  - "Used native fetch() in fetchMacroLatest() rather than axios apiClient — the macro endpoint requires no auth headers and native fetch is simpler for a standalone function"
  - "API path is /market/macro/latest not /macro/latest — the backend router registers under /market prefix; fixed during Task 1 verification"
  - "MacroPanel placed between Market Sentiment and Stock Selector in Dashboard.tsx — logical flow from macro environment context to individual stock analysis"
  - "Null values show — placeholder not a crash; API returns all-null when FRED/yfinance data not yet collected (Phase 93/94 pipeline)"

patterns-established:
  - "Macro indicator card: label (JetBrains Mono uppercase), large value (bold 1.2rem), description (small muted), colored icon top-right"
  - "FormatSpec enum: 0.2f | +0.2% | 0.1f | +0.2f | 0,0 | 0.3f — covers all numeric formats needed for financial indicators"
  - "Color logic extracted to per-indicator colorFn: returns 'green' | 'red' | 'gray' — deterministic and testable"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-04-04
---

# Phase 95 Plan 02: Dashboard Macro Panel Summary

**9-card Macro Environment panel added to Dashboard: VIX, SPY Return, 10Y Yield, 2-10 Spread, HY Spread, WTI, USD Index, Initial Claims, Core PCE with color-coded signals and 60s auto-refresh**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-04T16:13:14Z
- **Completed:** 2026-04-04T16:21:30Z
- **Tasks:** 4 (3 code + 1 Playwright verification)
- **Files modified:** 6

## Accomplishments

- Created `MacroPanel.tsx` — responsive 3/2/1 column grid of 9 indicator cards with loading skeleton, error state, and null-safe formatting
- Added `useMacroLatest()` React Query hook with 60s auto-refresh and `fetchMacroLatest()` using native fetch
- Integrated `<MacroPanel />` into Dashboard.tsx below Market Sentiment section with "Macro Environment" section label
- Playwright confirmed all 9 indicators render correctly (VIX, SPY Return, 10Y Yield, 2-10 Spread, HY Spread, WTI Crude, USD Index, Initial Claims, Core PCE)

## Task Commits

1. **Task 1: API type, fetch function, and useMacroLatest hook** - `92ec85b` (feat)
2. **Task 2: MacroPanel.tsx component + dashboard/index.ts export** - `7787092` (feat)
3. **Task 3: Dashboard.tsx integration** - `2c83a8a` (feat)
4. **Deviation fix: Correct API path** - `d9f8a9f` (fix)

## Files Created/Modified

- `services/frontend/src/components/dashboard/MacroPanel.tsx` — New component: 9-card macro indicator grid
- `services/frontend/src/api/client.ts` — Added `fetchMacroLatest()` function (native fetch, `/market/macro/latest`)
- `services/frontend/src/api/types.ts` — Added `MacroLatest` TypeScript interface
- `services/frontend/src/api/queries.ts` — Added `useMacroLatest()` React Query hook
- `services/frontend/src/components/dashboard/index.ts` — Added MacroPanel export
- `services/frontend/src/pages/Dashboard.tsx` — Imported MacroPanel, added Macro Environment section

## Decisions Made

- Used native `fetch()` in `fetchMacroLatest()` rather than axios `apiClient` — macro endpoint needs no auth headers and native fetch is simpler for a standalone helper
- API path is `/market/macro/latest` (not `/macro/latest`) — backend router mounts under `/market` prefix; discovered during verification
- MacroPanel placed between Market Sentiment and Stock Selector — natural flow from macro context → individual stock analysis
- Null values display "—" placeholder safely; expected until Phase 93/94 data pipeline populates FRED/yfinance tables

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong API endpoint path in fetchMacroLatest()**
- **Found during:** Task 4 (Playwright verification)
- **Issue:** `fetchMacroLatest()` was calling `/macro/latest` but the backend router registers the endpoint as `/market/macro/latest`; caused 404 from the deployed API
- **Fix:** Updated path in `client.ts` to `/market/macro/latest`, rebuilt Docker image, and re-rolled the deployment
- **Files modified:** `services/frontend/src/api/client.ts`
- **Verification:** `curl http://localhost:18000/market/macro/latest` returned 200 JSON; Playwright confirmed all 9 indicator cards rendered
- **Committed in:** `d9f8a9f`

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug)
**Impact on plan:** Essential fix to prevent runtime 404. Wrong path would have shown error state permanently. No scope creep.

## Issues Encountered

- Frontend was showing "Failed to load market data" when accessed via NodePort (`192.168.49.2:30080`) because `VITE_API_URL` bakes to `localhost:8000` at build time. Switched to port-forward approach (`localhost:3000` + `localhost:8000`) matching the existing production test setup — this is the standard verified approach for this cluster.

## User Setup Required

None — no external service configuration required. MacroPanel displays "—" for all values until FRED/yfinance data is collected by the Phase 94 pipeline.

## Next Phase Readiness

- MacroPanel fully integrated and verified rendering in Dashboard
- Shows "—" placeholders until FRED/yfinance collectors (Phase 94) populate `macro_fred_daily` and `feast_yfinance_macro` tables
- Once Phase 94 CronJobs run, cards will auto-populate on next 60s refresh cycle

---
*Phase: 95-dashboard-macro-panel*
*Completed: 2026-04-04*
