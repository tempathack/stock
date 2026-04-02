# Phase 76: UX Polish — Research

**Researched:** 2026-04-02
**Domain:** React / MUI frontend polish, FastAPI backend data fix, K8s CronJob config
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Backtest Empty State (Idle)**
- Show an instructional prompt centered in the results area when no backtest has been run yet: a play icon + text "Configure parameters above and click Run Backtest to see results"
- No PlaceholderCard component — use a simple inline centered Box with muted text and a PlayArrow icon
- This is the idle state (no run yet), distinct from the error state (`ErrorFallback`) and loading state (`LinearProgress`)

**Backtest Loading Feedback**
- Keep top LinearProgress bar at fixed top as-is — no additional skeleton in the results area
- The top bar is sufficient; do not add skeleton loaders or circular spinners

**Multi-Horizon Selector (14D)**
- Scope: Forecasts page only — The Forecasts HorizonToggle already works correctly and reads from the DB
- Add 14D predictions to the DB: run a backfill for current tickers at horizon=14, then update the prediction CronJob to produce 14D predictions going forward alongside existing horizons
- The Backtest page horizon dropdown (1d/7d/30d) is NOT changed in this phase
- 3D is not a new horizon — only 14D is new; 1D/7D already exist; 3D is not required

**OLAP Chart Ticker Selector**
- Add a MUI Autocomplete dropdown inside the OLAPCandleChart panel header, to the right of the title
- Populates options from `useMarketOverview()` (same source as Backtest and Dashboard ticker selectors)
- Compact size (size="small"), replaces the hardcoded `DEFAULT_TICKER = "AAPL"` constant
- The interval toggle (1h/1d) stays where it is — ticker and interval are independent controls
- No page-level shared ticker state — the OLAP chart owns its own ticker state

**Feature Freshness Unknown State**
- Display fix only — the API returning null for staleness is correct behavior (Feast can't always determine it)
- Change display: null staleness → show `—` (em-dash) instead of the text "unknown"
- Grey out the row at reduced opacity when staleness is null (consistent with null numeric pattern from Phase 75)
- Remove the LinearProgress bar for null-staleness rows (no progress bar when value is unknown)
- Color function: null → no color chip / neutral grey, not amber warning

**Sector and Company Name in Forecasts**
- These fields already exist in `ForecastTable.tsx` columns and `joinForecastData()` — they come from `marketQuery.data.stocks`
- The fix is a data investigation: verify whether `MarketOverviewEntry` objects in the API response populate `company_name` and `sector` fields
- If the API `/market/overview` endpoint omits these fields, fix the endpoint and/or the DB query that populates `stocks` table rows
- Do NOT mock or hardcode company names

**Icon Tooltips**
- Audit all icon-only buttons across all pages
- Every button that renders only an icon must have a MUI `Tooltip` with a clear action description
- Backtest export buttons already have Tooltips — verify and add any missing ones

### Claude's Discretion
- Exact wording of the Backtest idle-state prompt
- Greyed-out row opacity value for null Feature Freshness rows
- Whether to use a Box or a styled Paper for the idle empty state in Backtest

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 76 is a pure polish sprint across 4 existing pages: Backtest, Forecasts, Analytics, and Dashboard. No new pages or API endpoints (except backfilling 14D predictions into the DB and updating one config value). All frontend changes are additive — adding states to existing conditional render chains, adding imports, and replacing hardcoded values.

The most substantive work is backend: (1) investigating why `company_name` and `sector` are null in Forecasts despite existing columns in the schema — the SQL in `market_service.py` selects these fields from the `stocks` table, so the root cause is likely missing data in the `stocks` table rather than a code bug; (2) adding horizon=14 to the prediction backfill and updating `AVAILABLE_HORIZONS` in config to include 14.

Frontend changes are all well-precedented in the existing codebase — every pattern needed is already in use elsewhere. Risk is LOW.

**Primary recommendation:** Tackle the `company_name`/`sector` data investigation first (it may reveal a DB seed gap), then make frontend changes in parallel per page. The 14D horizon work follows a proven pattern (`load_cached_predictions` already handles `latest_{h}d.json`).

---

## Standard Stack

### Core (already in use — no new installs)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| MUI `@mui/material` | ~5.x | Box, Tooltip, Autocomplete, LinearProgress | Project standard |
| MUI Icons `@mui/icons-material` | ~5.x | PlayArrowIcon, icon buttons | Project standard |
| React Query (via `@/api` hooks) | ~5.x | `useMarketOverview`, `useAvailableHorizons` | Project standard |
| FastAPI + SQLAlchemy async | — | API data fix for stocks table | Project standard |
| pytest | ~8.3 | API unit tests | Project standard |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended Project Structure
No new directories needed. All changes touch existing files in-place.

### Pattern 1: Three-State Conditional Render (Backtest idle state)

**What:** The existing Backtest.tsx has two render conditions — error and data. The idle state is a third condition that fires when none of: `isLoading`, `isError`, `data` are truthy.

**Current render structure (lines 203–246):**
```
{backtestQuery.isLoading && <LinearProgress ... />}  // top of component
{backtestQuery.isError && <ErrorFallback ... />}
{backtestQuery.data && <Box>...</Box>}
```

**Insertion point:** Add between the error block and the data block:
```tsx
{!backtestQuery.data && !backtestQuery.isError && !backtestQuery.isLoading && (
  <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", py: 8, gap: 2, color: "text.secondary" }}>
    <PlayArrowIcon sx={{ fontSize: 48, opacity: 0.3 }} />
    <Typography variant="body1">Configure parameters above and click Run Backtest to see results</Typography>
  </Box>
)}
```

Note: `backtestQuery.isLoading` is `false` on initial render (no fetch has been triggered). The `useBacktest` hook only fires when `activeTicker` is set and the component mounts — on mount it will fire immediately with the default `activeTicker = "AAPL"`. Research this: check whether the query fires on mount or only on `handleRun`. If it fires on mount, `isLoading` will be true on first render and the idle state will never show initially.

**Verification of behavior:** Looking at `Backtest.tsx` line 41: `const backtestQuery = useBacktest(activeTicker, start, end, horizon)` — this fires immediately on mount with `activeTicker = "AAPL"`. So on mount, the state is: `isLoading=true` → `isLoading=false, data={...}`. The idle state would only show between `isError=false` and `data=null`. To show an idle state before any run, the query would need to be lazy (not fire on mount). The CONTEXT.md decision is for "no run yet" — this means the component may need a `hasRunOnce` state boolean initialized to false, or the query needs to be enabled only when a run is triggered. This is the key implementation decision.

### Pattern 2: Null Display — em-dash (`—`)

**What:** The Phase 75 pattern for null numerics. Already used in `ForecastTable.tsx` (`fmt()` returns `"—"`) and `Drift.tsx`.

**Application to Feature Freshness:**
```tsx
// Before:
function formatStaleness(s: number | null): string {
  if (s === null) return "unknown";  // CHANGE to "—"
  ...
}

// After:
function formatStaleness(s: number | null): string {
  if (s === null) return "—";
  ...
}
```

Additionally: `getStalenessColor` currently returns `"warning"` for null — change to not return a color chip. Since `LinearProgress` `color` prop accepts `"success" | "warning" | "error" | "inherit" | "primary" | "secondary"`, either return `"inherit"` or conditionally hide the progress bar entirely.

**Null row greyed out:**
```tsx
<Box sx={{ opacity: view.staleness_seconds === null ? 0.45 : 1 }}>
  ...
  {view.staleness_seconds !== null && (
    <LinearProgress ... />
  )}
</Box>
```

### Pattern 3: Autocomplete Ticker Selector (OLAP Chart)

**What:** Replace hardcoded `DEFAULT_TICKER = "AAPL"` with local state driven by `useMarketOverview()`.

**Existing pattern** (from `Backtest.tsx` lines 108–116):
```tsx
<Autocomplete
  options={tickers}
  value={ticker}
  onChange={(_, v) => setTicker(v ?? "AAPL")}
  renderInput={(params) => (
    <TextField {...params} label="Ticker" size="small" fullWidth />
  )}
  freeSolo
/>
```

**OLAPCandleChart adaptation:** Add import for `useMarketOverview`, add state `const [ticker, setTicker] = useState("AAPL")`, derive `tickers` list, change `useAnalyticsCandles(DEFAULT_TICKER, interval)` to `useAnalyticsCandles(ticker, interval)`. Place Autocomplete in the existing header `Box` alongside the interval ToggleButtonGroup.

**Header structure change:**
```tsx
// Current header Box (line 125-141):
<Box sx={{ display: "flex", alignItems: "center", mb: 2, gap: 1 }}>
  <BarChartIcon ... />
  <Typography variant="h6">OLAP Candle Chart</Typography>
  <Box sx={{ ml: "auto", display: "flex", alignItems: "center", gap: 1 }}>
    {isLoading && <CircularProgress size={16} />}
    <ToggleButtonGroup ...>...</ToggleButtonGroup>
  </Box>
</Box>

// After: Add Autocomplete between title and ml-auto Box
<Autocomplete
  options={tickers}
  value={ticker}
  onChange={(_, v) => setTicker(v ?? "AAPL")}
  size="small"
  sx={{ width: 120 }}
  renderInput={(params) => <TextField {...params} label="Ticker" />}
  disableClearable
/>
```

Note: `useAnalyticsCandles` is imported from `../../api/queries` — confirm the path to `useMarketOverview` is `../../api/queries` as well (same module per CONTEXT.md).

### Pattern 4: 14D Horizon — Backend Changes

**What:** `prediction_service.py` already supports `horizon=14` — `load_cached_predictions(horizon=14)` reads `latest_14d.json`; `load_db_predictions(horizon=14)` filters the predictions table by 14-day interval; `generate_predictions(horizons=[1,7,14])` already handles multi-horizon. The blockers are:

1. **`AVAILABLE_HORIZONS` env var / config** — Currently `"1,7,30"`. Must change to `"1,7,14,30"` (or `"1,7,14"` if 30d is also to be kept). The `_validate_horizon` function in `predict.py` rejects horizon=14 if not in `settings.available_horizons_list`.

2. **`horizons.json`** — `load_available_horizons()` reads `{SERVING_DIR}/horizons.json`. If the file exists and doesn't list 14, the HorizonToggle won't show it. The file must be updated to include 14 in its `horizons` list.

3. **Prediction backfill** — Run the predictor with `horizon=14` for current tickers to populate `latest_14d.json` (file-based) and/or rows in the `predictions` DB table.

4. **No dedicated prediction CronJob found** — The training CronJob (`k8s/ml/cronjob-training.yaml`) runs `training_pipeline.py`, not a separate prediction generation job. The drift trigger (`ml/drift/trigger.py`) can trigger retraining but not standalone prediction generation. The 14D predictions are generated as part of the training pipeline when `--horizons 1,7,14` is passed. Either: (a) add `--horizons` arg to the training cronjob, or (b) create a separate backfill/generate script. The cleanest path: update the training pipeline args to include `horizon_14d` in the multi-horizon list.

### Pattern 5: Sector/Company Name Data Fix

**What:** The SQL in `market_service.py` (lines 26–41) already selects `s.company_name` and `s.sector` from the `stocks` table. The `MarketOverviewEntry` schema accepts both fields. The `joinForecastData()` function reads them from the API response. If they show as null in the UI, the stocks table rows have null values for those columns.

**Investigation steps:**
1. Query DB: `SELECT ticker, company_name, sector FROM stocks WHERE is_active = true LIMIT 10;`
2. If null, the fix is in the data seed — the yfinance ingestion or stocks table population script needs to fetch and store `longName` and `sector` from yfinance's `Ticker.info` dict.
3. No code changes needed in `joinForecastData()` or the router — the pipeline is correct.

**yfinance `Ticker.info` fields (HIGH confidence from established pattern):**
- `info['longName']` → company_name
- `info['sector']` → sector

These fields are populated by yfinance for S&P 500 stocks. The stocks table population (wherever it runs — likely a seed script or ingestion step) must be updated to include these.

### Pattern 6: MUI Tooltip on Icon Buttons

**What:** Wrap every icon-only Button/IconButton in a `<Tooltip title="...">`. The pattern is already used for Backtest export buttons.

**MUI Tooltip key rule:** When wrapping a disabled button, Tooltip must wrap a `<span>` not the Button directly (disabled elements don't fire events). Backtest.tsx already uses this pattern correctly.

**Audit scope:** All pages — check for `IconButton` components and icon-only `Button` components without visible text labels. The nav sidebar is a candidate — check for icon-only nav links.

### Anti-Patterns to Avoid

- **Don't show the idle state after data has loaded and then cleared.** The "idle" state is specifically "before any run has been initiated". If `backtestQuery` is refetched and temporarily has no data, don't flash the idle state. Use a `hasRunOnce` flag to prevent regression.
- **Don't add 3D horizon.** The decision is 14D only; 1D and 7D exist.
- **Don't mock company_name/sector.** Fix the data source.
- **Don't break the interval toggle on OLAP chart.** Ticker and interval are independent state variables — the `useAnalyticsCandles` hook receives both.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ticker dropdown options | Custom fetch/dedupe | `useMarketOverview()` already returns sorted tickers | Already used in Backtest and Dashboard |
| Available horizons list | Hardcode | `useAvailableHorizons()` reading `horizons.json` | The HorizonToggle already reads this |
| Empty state illustration | Custom SVG/animation | MUI `Box` + MUI icon | Decision explicitly says no PlaceholderCard |
| Null display formatting | Custom function | `"—"` (em-dash) pattern from Phase 75 | Consistent with existing pattern |

---

## Common Pitfalls

### Pitfall 1: Backtest Idle State Never Shows (Query Fires on Mount)

**What goes wrong:** `useBacktest("AAPL", start, end, undefined)` fires immediately on mount — the component never has `!data && !isLoading && !isError` as its first render state because `isLoading` is `true` on mount.

**Why it happens:** React Query runs the query immediately when the component mounts with a non-null query key.

**How to avoid:** Track a `hasRunOnce` or `isQueryEnabled` boolean in component state. Initialize to `false`. Set to `true` when `handleRun` is called. Pass `enabled: hasRunOnce` to the `useBacktest` hook (if the hook supports it) or initialize `activeTicker` to `""` and only set it in `handleRun`.

**Current state:** `activeTicker` is initialized to `"AAPL"` — query fires immediately. The simplest fix: initialize `activeTicker` to `null | string`, don't pass it to `useBacktest` until `handleRun` is called, or add `enabled` param to the hook.

**Warning signs:** Unit test for idle state never passes because data loads before the idle render.

### Pitfall 2: `AVAILABLE_HORIZONS` Mismatch Between Config and horizons.json

**What goes wrong:** Add `14` to `AVAILABLE_HORIZONS` env var in config, but forget to update `horizons.json` in the serving directory — `useAvailableHorizons()` returns `[7]` (fallback) and the HorizonToggle never shows 14D.

**How to avoid:** Both must be updated: (1) config default `AVAILABLE_HORIZONS = "1,7,14,30"`, (2) `horizons.json` file updated to `{"horizons": [1, 7, 14, 30], "default": 7}` or created if absent.

### Pitfall 3: Autocomplete `freeSolo` Drift in OLAP Chart

**What goes wrong:** Using `freeSolo` allows typing arbitrary tickers that may not exist in the DB, breaking the candle chart with a 404/empty state.

**How to avoid:** Since the OLAP chart should only show known tickers, either omit `freeSolo` (force selection from the list) or handle the empty candle state gracefully (the chart already has `PlaceholderCard` for empty candle data).

### Pitfall 4: `getStalenessColor` Return Type Mismatch

**What goes wrong:** `LinearProgress` `color` prop type is `"success" | "warning" | "error" | "inherit" | "primary" | "secondary"`. If `getStalenessColor` returns `null` or `undefined` for the null case, TypeScript will complain.

**How to avoid:** Change the function signature to `"success" | "warning" | "error" | "inherit"` and return `"inherit"` for null. Then conditionally skip rendering the LinearProgress when `staleness_seconds === null`.

### Pitfall 5: Company Name / Sector Null in stocks Table

**What goes wrong:** The SQL and frontend are correct, but `stocks.company_name` and `stocks.sector` are null for all rows — they were never populated during DB seeding.

**How to avoid:** Before implementing any frontend change, run a quick DB query to verify. If null, the fix is in the seed/ingestion layer — locate where `stocks` table rows are inserted and ensure `company_name` and `sector` are populated from yfinance `Ticker.info`.

---

## Code Examples

### Backtest Idle State (with `hasRunOnce` guard)

```tsx
// In Backtest.tsx component state:
const [activeTicker, setActiveTicker] = useState<string | null>(null);

// handleRun:
const handleRun = () => {
  const cleaned = ticker.trim().toUpperCase();
  if (cleaned) setActiveTicker(cleaned);
};

// useBacktest — pass null as ticker when not yet run:
const backtestQuery = useBacktest(activeTicker ?? "", start, end, horizon);
// Ensure the query hook handles empty string as disabled (check useBacktest implementation)

// Render:
{!activeTicker && (
  <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", py: 8, gap: 2, color: "text.secondary" }}>
    <PlayArrowIcon sx={{ fontSize: 48, opacity: 0.3 }} />
    <Typography variant="body1" sx={{ opacity: 0.6 }}>
      Configure parameters above and click Run Backtest to see results
    </Typography>
  </Box>
)}
```

### Feature Freshness Null Fix

```tsx
// getStalenessColor — return "inherit" (not amber "warning") for null:
function getStalenessColor(s: number | null): "success" | "warning" | "error" | "inherit" {
  if (s === null) return "inherit";
  if (s < 15 * 60) return "success";
  if (s < 60 * 60) return "warning";
  return "error";
}

// formatStaleness — em-dash for null:
function formatStaleness(s: number | null): string {
  if (s === null) return "—";
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

// Row render — grey out and skip progress bar:
<Tooltip ...>
  <Box sx={{ opacity: view.staleness_seconds === null ? 0.45 : 1 }}>
    <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
      <Typography variant="body2">{view.view_name}</Typography>
      <Typography variant="body2" color="text.secondary">
        {formatStaleness(view.staleness_seconds)}
      </Typography>
    </Box>
    {view.staleness_seconds !== null && (
      <LinearProgress
        variant="determinate"
        value={getStalenessProgress(view.staleness_seconds)}
        color={getStalenessColor(view.staleness_seconds) as "success" | "warning" | "error"}
        sx={{ height: 6, borderRadius: 1 }}
      />
    )}
  </Box>
</Tooltip>
```

### 14D Horizon Config

```python
# services/api/app/config.py — update default:
AVAILABLE_HORIZONS: str = "1,7,14,30"
```

```json
// /models/active/horizons.json — update or create:
{"horizons": [1, 7, 14, 30], "default": 7}
```

```python
# Backfill command (run once via exec into the API pod or a Job):
# generate_predictions(data_dict, serving_dir, horizons=[14])
# then write to model_registry/predictions/latest_14d.json
```

---

## Canonical File Inventory

All files that must be read/modified by implementing agents:

### Frontend (read + modify)
| File | Change |
|------|--------|
| `services/frontend/src/pages/Backtest.tsx` | Add idle state, verify existing Tooltips |
| `services/frontend/src/components/analytics/OLAPCandleChart.tsx` | Add ticker Autocomplete, remove `DEFAULT_TICKER` constant |
| `services/frontend/src/components/analytics/FeatureFreshnessPanel.tsx` | Fix `formatStaleness`, `getStalenessColor`, conditional LinearProgress |

### Backend (read + modify)
| File | Change |
|------|--------|
| `services/api/app/config.py` | Add `14` to `AVAILABLE_HORIZONS` default |
| `services/api/app/services/market_service.py` | Verify SQL selects company_name/sector correctly (likely no change needed) |

### Data (investigate + fix)
| Target | Investigation |
|--------|--------------|
| `stocks` table in PostgreSQL | Query to confirm company_name/sector are null |
| Seed/ingestion script | Find where stocks rows are inserted; add yfinance `Ticker.info` fields |
| `horizons.json` in serving dir | Update to include 14 |
| `model_registry/predictions/` | Run backfill for `latest_14d.json` |

### Already Correct (read only, no changes)
| File | Reason |
|------|--------|
| `services/frontend/src/utils/forecastUtils.ts` | `joinForecastData` already maps `company_name`/`sector` correctly |
| `services/frontend/src/components/forecasts/ForecastTable.tsx` | `company_name`/`sector` columns already exist |
| `services/frontend/src/pages/Forecasts.tsx` | `HorizonToggle` already reads `availableHorizons` from API |
| `services/api/app/routers/market.py` | Already maps `company_name`/`sector` from DB result |
| `services/api/app/services/prediction_service.py` | Already supports `horizon=14` in all three data paths |

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `return "unknown"` for null staleness | `return "—"` + grey row + no progress bar | Consistent null treatment across all panels |
| Hardcoded `DEFAULT_TICKER = "AAPL"` in OLAP chart | Autocomplete driven by `useMarketOverview()` | Users can select any tracked ticker |
| `AVAILABLE_HORIZONS = "1,7,30"` | `AVAILABLE_HORIZONS = "1,7,14,30"` | 14D horizon visible in Forecasts toggle |
| No idle state in Backtest | Centered prompt with PlayArrow icon | Clear affordance before first run |

---

## Open Questions

1. **Does `useBacktest` support an `enabled` flag or skip when ticker is empty string?**
   - What we know: The hook calls `useBacktest(activeTicker, start, end, horizon)`. React Query's `useQuery` supports `enabled: !!activeTicker`.
   - What's unclear: Whether the custom `useBacktest` wrapper in `@/api` passes through an `enabled` option.
   - Recommendation: Read `services/frontend/src/api/queries.ts` before implementing. If it doesn't expose `enabled`, initialize `activeTicker` to `null` and add a guard inside the hook or use a `skip` pattern.

2. **Are company_name and sector null in the stocks table?**
   - What we know: The SQL and frontend are correct end-to-end.
   - What's unclear: Whether the stocks table was ever seeded with these fields. Must be verified before the planning agent assigns effort to this task.
   - Recommendation: The implementing agent should `SELECT company_name, sector FROM stocks LIMIT 5` as the very first step. If populated, the UI bug has another cause (type mismatch, empty string vs null, etc.).

3. **Where is the 14D prediction backfill run?**
   - What we know: `generate_predictions()` supports `horizons=[14]`. No standalone prediction CronJob exists — predictions are generated as part of training.
   - What's unclear: Whether the backfill should be a one-time K8s Job, a manual exec, or added to the training pipeline CLI args.
   - Recommendation: Add `14` to the `horizons` list in the training pipeline CronJob args so future runs produce 14D predictions. For the initial backfill, create a one-shot K8s Job or run via `kubectl exec`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.3 |
| Config file | `services/api/pytest.ini` or pyproject.toml (check conftest.py location) |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/test_prediction_service.py -x -q` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `load_db_predictions(horizon=14)` returns predictions filtered to 14d | unit | `pytest tests/test_prediction_service.py -k "horizon_14" -x` | ❌ Wave 0 |
| `/predict/bulk?horizon=14` returns 200 when 14 in AVAILABLE_HORIZONS | unit | `pytest tests/test_predict_horizon.py -k "14" -x` | ❌ Wave 0 |
| `formatStaleness(null)` returns `"—"` | manual/visual | — | manual-only |
| `getStalenessColor(null)` returns `"inherit"` | unit | (add to analytics test) | ❌ Wave 0 |
| Backtest idle state renders when `activeTicker` is null | manual/visual | — | manual-only |
| OLAP chart uses selected ticker in API call | manual/visual | — | manual-only |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_prediction_service.py tests/test_predict_horizon.py -x -q`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_prediction_service.py` — add `test_load_db_predictions_horizon_14` — covers 14D filtering
- [ ] `tests/test_predict_horizon.py` — add `test_bulk_horizon_14_accepted` — covers AVAILABLE_HORIZONS config
- [ ] `tests/test_analytics_router.py` — add `test_feature_freshness_null_staleness_display` — covers getStalenessColor null path

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `services/frontend/src/pages/Backtest.tsx` — confirmed three-state render structure and existing Tooltip usage
- Direct code inspection: `services/frontend/src/components/analytics/OLAPCandleChart.tsx` — confirmed hardcoded `DEFAULT_TICKER`, header Box structure, interval state
- Direct code inspection: `services/frontend/src/components/analytics/FeatureFreshnessPanel.tsx` — confirmed `getStalenessColor` returning `"warning"` for null, `formatStaleness` returning `"unknown"` for null
- Direct code inspection: `services/api/app/services/prediction_service.py` — confirmed `load_db_predictions` supports horizon=14, `generate_predictions` supports `horizons=[14]`
- Direct code inspection: `services/api/app/config.py` — confirmed `AVAILABLE_HORIZONS = "1,7,30"` must be extended
- Direct code inspection: `services/api/app/routers/market.py` + `services/api/app/services/market_service.py` — confirmed SQL selects `company_name` and `sector` correctly; data gap likely in DB

### Secondary (MEDIUM confidence)
- Inferred from code structure: `useBacktest` query fires on mount with default `activeTicker = "AAPL"` — may need `enabled` guard for idle state
- Inferred from schema: `stocks` table must have non-null `company_name`/`sector` for the UI to show them

### Tertiary (LOW confidence — requires verification)
- No dedicated prediction CronJob found for 14D backfill — inferred from training pipeline structure

---

## Metadata

**Confidence breakdown:**
- Frontend patterns: HIGH — all patterns directly observed in existing code
- Backend data flow: HIGH — SQL, schemas, and service code confirmed correct
- 14D horizon mechanics: HIGH — `generate_predictions` and `load_db_predictions` explicitly support it
- Root cause of company_name/sector null: MEDIUM — SQL is correct, data gap suspected but not DB-confirmed
- Backtest idle state guard pattern: MEDIUM — depends on `useBacktest` hook's `enabled` support (unread)

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable codebase)
