# Phase 76: UX Polish — Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Polish UX across 4 existing pages — no new pages, no new API endpoints (data fixes only):
1. Backtest page: add idle empty state and confirm loading feedback is sufficient
2. Forecasts page: populate Sector and Company name fields (data fix), add 14D horizon to DB and CronJob
3. Analytics page: add ticker selector to OLAP Candle Chart, fix Feature Freshness null display
4. Dashboard: add content below treemap fold (deferred from Phase 74)
5. All pages: add tooltips to any remaining icon-only buttons

Retraining models, adding new pages, and changes to data pipeline architecture are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Backtest Empty State (Idle)
- Show an instructional prompt centered in the results area when no backtest has been run yet: a play icon + text "Configure parameters above and click Run Backtest to see results"
- No PlaceholderCard component — use a simple inline centered Box with muted text and a PlayArrow icon
- This is the idle state (no run yet), distinct from the error state (`ErrorFallback`) and loading state (`LinearProgress`)

### Backtest Loading Feedback
- Keep top LinearProgress bar at fixed top as-is — no additional skeleton in the results area
- The top bar is sufficient; do not add skeleton loaders or circular spinners

### Multi-Horizon Selector (14D)
- **Scope: Forecasts page only** — The Forecasts HorizonToggle already works correctly and reads from the DB
- Add 14D predictions to the DB: run a backfill for current tickers at horizon=14, then update the prediction CronJob to produce 14D predictions going forward alongside existing horizons
- The Backtest page horizon dropdown (1d/7d/30d) is **not changed** in this phase
- 3D is not a new horizon — the phase goal of "1D/3D/7D/14D" was clarified: only 14D is new; 1D/7D already exist; 3D is not required

### OLAP Chart Ticker Selector
- Add a MUI Autocomplete dropdown inside the OLAPCandleChart panel header, to the right of the title
- Populates options from `useMarketOverview()` (same source as Backtest and Dashboard ticker selectors)
- Compact size (size="small"), replaces the hardcoded `DEFAULT_TICKER = "AAPL"` constant
- The interval toggle (1h/1d) stays where it is — ticker and interval are independent controls
- No page-level shared ticker state — the OLAP chart owns its own ticker state

### Feature Freshness Unknown State
- Display fix only — the API returning null for staleness is correct behavior (Feast can't always determine it)
- Change display: null staleness → show `—` (em-dash) instead of the text "unknown"
- Grey out the row at reduced opacity when staleness is null (consistent with null numeric pattern from Phase 75)
- Remove the LinearProgress bar for null-staleness rows (no progress bar when value is unknown)
- Color function: null → no color chip / neutral grey, not amber warning

### Sector and Company Name in Forecasts
- These fields already exist in `ForecastTable.tsx` columns and `joinForecastData()` — they come from `marketQuery.data.stocks`
- The fix is a data investigation: verify whether `MarketOverviewEntry` objects in the API response populate `company_name` and `sector` fields
- If the API `/market/overview` endpoint omits these fields, fix the endpoint and/or the DB query that populates `stocks` table rows
- Do NOT mock or hardcode company names

### Icon Tooltips
- Audit all icon-only buttons across all pages (Backtest export buttons, any icon buttons in the nav or panels)
- Every button that renders only an icon (no visible label) must have a MUI `Tooltip` with a clear action description
- Backtest export buttons already have Tooltips — verify and add any missing ones

### Claude's Discretion
- Exact wording of the Backtest idle-state prompt
- Greyed-out row opacity value for null Feature Freshness rows
- Whether to use a Box or a styled Paper for the idle empty state in Backtest

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backtest page
- `stock-prediction-platform/services/frontend/src/pages/Backtest.tsx` — Current page implementation; idle state goes after the error state block and before the results block
- `stock-prediction-platform/services/frontend/src/components/backtest/BacktestChart.tsx` — Chart component
- `stock-prediction-platform/services/frontend/src/components/backtest/BacktestMetricsSummary.tsx` — Metrics component

### Forecasts / Horizon
- `stock-prediction-platform/services/frontend/src/pages/Forecasts.tsx` — HorizonToggle usage; `availableHorizons` from `useAvailableHorizons()`
- `stock-prediction-platform/services/frontend/src/utils/forecastUtils.ts` — `joinForecastData()` — where sector/company_name come from
- `stock-prediction-platform/services/frontend/src/components/forecasts/ForecastTable.tsx` — Column definitions for company_name and sector
- `stock-prediction-platform/services/api/app/routers/forecasts.py` — `/forecasts/bulk` endpoint (check if it joins market data)
- `stock-prediction-platform/services/api/app/routers/market.py` — `/market/overview` endpoint (check company_name/sector fields)

### OLAP Chart
- `stock-prediction-platform/services/frontend/src/components/analytics/OLAPCandleChart.tsx` — Current hardcoded AAPL ticker; add Autocomplete here
- `stock-prediction-platform/services/api/queries.ts` — `useMarketOverview()` hook for ticker list source

### Feature Freshness
- `stock-prediction-platform/services/frontend/src/components/analytics/FeatureFreshnessPanel.tsx` — `formatStaleness()` and `getStalenessColor()` functions; null handling
- `stock-prediction-platform/services/api/app/routers/analytics.py` — Feature freshness endpoint (confirm null is intentional API behavior)

### 14D Predictions
- `stock-prediction-platform/services/api/app/services/prediction_service.py` — Prediction generation; extend to support horizon=14
- Check for K8s CronJob manifest that triggers prediction runs (look in `k8s/` or `manifests/` directory)

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MUI Autocomplete` (size="small"): already used in `Backtest.tsx` (ticker selector) and `Dashboard.tsx` (StockSelector) — same pattern for OLAP chart
- `useMarketOverview()` hook: available in both Backtest and Dashboard pages; import in OLAPCandleChart for ticker list
- `PlaceholderCard` component in `src/components/ui/`: used in FeatureFreshnessPanel and OLAPCandleChart for empty/missing states — available if needed elsewhere
- `ErrorFallback` component: already handles the error state in Backtest; idle state is a separate third state

### Established Patterns
- Null numeric display: `—` (em-dash) for null values, established in Phase 75 (`Drift.tsx` fix)
- Tooltip on icon buttons: already applied to Backtest export buttons (`Tooltip` wrapping `Button`) — use same pattern for any missing tooltips
- Greyed-out opacity for unavailable data: check `ModelComparisonTable.tsx` or `SystemHealthSummary.tsx` for opacity patterns
- Horizon toggle: `HorizonToggle` component in `src/components/forecasts/` — reads `availableHorizons` from API; no frontend change needed if DB has 14D rows

### Integration Points
- OLAPCandleChart: Currently self-contained with hardcoded ticker; adding `useMarketOverview()` import is the main change
- Backtest idle state: Render between existing `{backtestQuery.isError && ...}` block and `{backtestQuery.data && ...}` block — add `{!backtestQuery.data && !backtestQuery.isError && !backtestQuery.isLoading && <IdleState />}`
- 14D CronJob: Find prediction CronJob manifest and add `--horizon 14` (or equivalent) to the job spec

</code_context>

<specifics>
## Specific Ideas

- Backtest idle state: Use a PlayArrowIcon next to the prompt text — matches the existing "Run Backtest" button icon for visual consistency
- Feature freshness null rows: Reduced opacity (e.g., `opacity: 0.5`) on the entire row stack item, same approach as disabled states elsewhere in MUI
- OLAP ticker autocomplete: Position it inline with the title using `display: flex, justifyContent: space-between` on the panel header Box — mirrors how FeatureFreshnessPanel header is structured

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 76-ux-polish*
*Context gathered: 2026-04-02*
