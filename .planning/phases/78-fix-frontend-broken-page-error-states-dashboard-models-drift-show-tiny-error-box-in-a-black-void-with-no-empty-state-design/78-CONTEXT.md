# Phase 78: Fix Frontend Broken-Page Error States — Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix three pages (Dashboard, Models, Drift) where API failures produce a tiny `ErrorFallback` box in a
black void with no page structure, and loading states return `null` (also a black void). Specific fixes:

1. **Models** — `return null` on loading → black void; `return <ErrorFallback>` standalone → tiny box in void
2. **Dashboard** — Standalone `return <ErrorFallback>` on marketQuery failure; mock data fallbacks silently hiding errors
3. **Drift** — Four mock data fallbacks masking real failures; standalone `return <ErrorFallback>` on driftQuery failure

No new pages, no new API endpoints, no data pipeline changes.

</domain>

<decisions>
## Implementation Decisions

### Error State Design
- **Page-level errors**: Always render `PageHeader` first, then center an error block in the content area below — page title/nav context remains visible
- **ErrorFallback component**: Enhance in-place (not a new component) — add an `ErrorOutline` icon above the message text, keep the Retry button below. All existing callers automatically get the improved design
- **Panel-level errors**: Same enhanced `ErrorFallback` used inline inside failing panels — small icon + message + Retry, sized for the panel not the full page

### Loading Skeletons
- **Models**: Remove `if (isLoading) return null`. Render `PageHeader` immediately + skeleton table rows (8–10 MUI Skeleton rows matching the model comparison table columns) while `useModelComparison()` loads
- **Dashboard**: Render `PageHeader` immediately + skeleton cards matching the layout sections (treemap area placeholder, metric cards row skeletons, chart panel skeleton) while `marketQuery` loads
- **Drift**: Render `PageHeader` immediately + skeleton panels for each of the 4 grid sections (active model panel, drift timeline, rolling perf chart, retrain status) while initial load completes. Replace the current `isAllLoading` early return

### Mock Data Removal
- **Remove all mock fallbacks** from Dashboard and Drift — no fake data displayed on API failure
- Dashboard mocks to remove: `generateMockMarketOverview()`, `generateMockIndicatorSeries()`, `generateMockIntradayCandles()`
- Drift mocks to remove: `generateMockDriftData` (used for activeModel, events, rollingPerformance, retrainStatus)
- **`generateMockIntradayCandles`**: Replace with `PlaceholderCard` (already exists) shown when intraday candle data is unavailable — no fake candles
- If mock utility files (`mockDriftData.ts`, etc.) become unused after removal, delete them

### Per-Panel vs Full-Page Errors
- **Primary query failure** (marketQuery on Dashboard, driftQuery on Drift, useModelComparison on Models): full-page error — `PageHeader` + centered error block
- **Secondary query failure** (indicatorQuery on Dashboard, modelsQuery/rollingPerfQuery/retrainQuery on Drift): per-panel error — show inline `ErrorFallback` inside that specific panel only; other panels with working data render normally
- Each panel is independently resilient — one failing API doesn't take down the whole page

### Carrying Forward (Phase 75/76/77 patterns)
- Null/unavailable values → `—` (em-dash), not "unknown" or empty
- `PlaceholderCard` component exists for empty-but-not-error states
- `PageHeader` + content-below structure for all pages (established by Phase 77 Forecasts fix)

### Claude's Discretion
- Exact Skeleton component props (variant, height, animation) for each page's skeleton layout
- Whether to extract skeleton layouts into named components or inline them
- Exact mock utility files to delete vs keep (check if any are still used elsewhere before deleting)
- Ordering and wording of per-panel error messages (e.g., "Failed to load indicators" vs generic "Failed to load")

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Shared UI components
- `stock-prediction-platform/services/frontend/src/components/ui/ErrorFallback.tsx` — Current implementation to enhance; all callers automatically updated
- `stock-prediction-platform/services/frontend/src/components/ui/PlaceholderCard.tsx` — Reuse for intraday candle empty state (replace mock candles)
- `stock-prediction-platform/services/frontend/src/components/layout/PageHeader.tsx` — Must render first in every page error/loading state

### Models page
- `stock-prediction-platform/services/frontend/src/pages/Models.tsx` — Line 36: `return null` on loading; Line 37: standalone `return <ErrorFallback>` on error; fix both

### Dashboard page
- `stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx` — Line 418: standalone `return <ErrorFallback>` on marketQuery error; Lines 383/390/401: mock fallbacks to remove
- `stock-prediction-platform/services/frontend/src/utils/` — Find and check `generateMockMarketOverview`, `generateMockIndicatorSeries`, `generateMockIntradayCandles` — remove if no other callers

### Drift page
- `stock-prediction-platform/services/frontend/src/pages/Drift.tsx` — Lines 34/48/59/86–87: mock fallbacks for all 4 queries; Lines 92–103: loading/error early returns to restructure
- `stock-prediction-platform/services/frontend/src/utils/mockDriftData.ts` — Mock data source; delete if no other callers after removal

### App structure (for context)
- `stock-prediction-platform/services/frontend/src/App.tsx` — Layout wraps all pages; `<Outlet />` renders page content; confirms PageHeader is NOT rendered by Layout itself

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ErrorFallback` (`src/components/ui/ErrorFallback.tsx`): small bordered Box — enhance in-place with icon + center fill
- `PlaceholderCard` (`src/components/ui/`): used in FeatureFreshnessPanel and OLAPCandleChart for empty states — use for intraday candle no-data state
- `PageHeader` (`src/components/layout/PageHeader.tsx`): used in Models (line 42/69), Forecasts — must be rendered before any loading/error return
- MUI `Skeleton`: already used in Forecasts after Phase 77 — same import pattern for Models/Dashboard/Drift

### Established Patterns
- Phase 77 Forecasts fix: `PageHeader` + 10 MUI Skeleton rows during loading → same pattern for Models
- Phase 77 Forecasts fix: `bulkQuery.isError` → `ErrorFallback` inside page structure → apply to Models/Dashboard/Drift
- Null display: `—` (em-dash) for missing values (Phase 75); opacity reduction for unavailable rows (Phase 75/76)
- `PlaceholderCard` for "no data yet" states: used in OLAPCandleChart and FeatureFreshnessPanel — model for intraday candle empty state

### Integration Points
- Models: early returns (lines 36–37) are before the main `return (...)` JSX — fix both at once
- Dashboard: `if (marketQuery.isError && !marketQuery.data)` (line 418) is the page-level error gate; inline mocks (lines 383/390/401) are inside `useMemo` hooks
- Drift: early loading return (lines 92–96) and early error return (lines 103–120) both need restructuring; per-panel mock removal happens inside `useMemo` callbacks

</code_context>

<specifics>
## Specific Ideas

- ErrorFallback enhancement: add `ErrorOutline` MUI icon (from `@mui/icons-material/ErrorOutline`) above the Typography message text — same visual pattern as other MUI error states
- Dashboard skeleton: match the actual layout — a wide skeleton for the treemap area (full width, ~300px tall), then a row of 4 narrow skeletons for metric cards, then a wide skeleton for the chart panel below
- Drift skeleton: match the grid — 2 skeletons in the top row (active model + timeline), 2 in the bottom row (rolling perf chart + retrain status)
- Per-panel error for Dashboard indicator panel: render `ErrorFallback` inside the TA/indicator chart container Box, same size as the chart would be

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 78-fix-frontend-broken-page-error-states*
*Context gathered: 2026-04-02*
