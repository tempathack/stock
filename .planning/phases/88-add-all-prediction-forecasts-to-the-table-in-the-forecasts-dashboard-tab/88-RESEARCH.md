# Phase 88: Add All Prediction Forecasts to the Table in the Forecasts Dashboard Tab — Research

**Researched:** 2026-04-03
**Domain:** React frontend (MUI DataGrid), FastAPI prediction endpoints, multi-horizon KServe inference
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TBD | All available prediction horizons (1d, 7d, 14d, 30d) exposed in the Forecasts table | horizons.json is missing from /models/active/ — must be created; KServe already serves all horizons |
| TBD | Forecast table shows multi-horizon columns (1d Return %, 7d Return %, 14d Return %, 30d Return %) per stock row | Requires parallel useBulkPredictions calls for all horizons, merge into per-ticker row shape |
| TBD | HorizonToggle shows all four options (1D / 7D / 14D / 30D) | /predict/horizons falls back to [7] when horizons.json absent; creating the file fixes this |
| TBD | All 159+ tickers with predictions are visible in the table | Already works via /predict/bulk; the joinForecastData utility handles the market overview join |
</phase_requirements>

---

## Summary

The Forecasts page already uses `/predict/bulk?horizon=N` and renders a MUI DataGrid with one row per ticker for the selected horizon. **The core problem is twofold:**

1. `/models/active/horizons.json` is absent from the model-serving ConfigMap volume, causing `/predict/horizons` to fall back to `{"horizons":[7],"default":7}`. The HorizonToggle therefore only shows a single 7-day option — the three other horizons (1d, 14d, 30d) are invisible to users even though KServe happily returns predictions for all of them.

2. "All prediction forecasts" most naturally means **showing all four horizon predictions simultaneously as columns** in the same table row, so a user can see the 1d, 7d, 14d, and 30d forecasts for every stock at a glance without toggling. This supersedes or augments the current toggle-based approach.

**Primary recommendation:** Create `horizons.json` in the serving ConfigMap to advertise [1, 7, 14, 30], and redesign the ForecastTable to show all four horizons as grouped columns per stock row, fetching all four horizons in parallel with React Query.

---

## Current State (Verified Against Live Cluster)

| Fact | Verified Value |
|------|---------------|
| `/predict/bulk?horizon=7` count | 159 predictions |
| `/predict/bulk?horizon=1` count | 159 predictions |
| `/predict/bulk?horizon=14` count | 159 predictions |
| `/predict/bulk?horizon=30` count | 159 predictions |
| `/predict/horizons` response | `{"horizons":[7],"default":7}` (fallback — horizons.json missing) |
| `/models/active/` contents | Only `features.json` (horizons.json absent) |
| Market overview count | 160 stocks |
| Predictions DB table | 0 rows (all predictions come from KServe live inference) |
| Prediction source | KServe (`stacking_ensemble_meta_ridge`) |
| Missing ticker (no prediction) | `JNJ` (in market overview but KServe inference failed) |
| `AVAILABLE_HORIZONS` env var | `1,7,14,30` (API config already supports all) |

**Critical observation:** KServe returns the same `predicted_price` value regardless of the `horizon` parameter, because only a single model is deployed (not separate models per horizon). The `horizon` parameter only affects the `predicted_date` field (today + N days). This is expected for Phase 88 — the table will show correctly differentiated predicted dates even if price values are the same model output.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@mui/x-data-grid` | 7.x (already in use) | Forecast table rendering | Project standard — already in ForecastTable.tsx |
| `@tanstack/react-query` | 5.x (already in use) | Parallel horizon fetching | Project standard — all API hooks use this |
| `axios` | 1.x (already in use) | HTTP API client | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `json` (stdlib) | N/A | Write horizons.json to serving dir | Creating horizons.json ConfigMap or init script |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Parallel React Query calls (one per horizon) | Single endpoint returning all horizons | Single endpoint would be cleaner but requires API change; parallel calls reuse existing infrastructure with zero backend work |
| Multi-column table (all horizons as columns) | Keep toggle + show single horizon | Toggle approach is simpler but requires switching to see each horizon — all-columns approach shows the complete picture at once |

---

## Architecture Patterns

### Recommended Project Structure
No new files needed beyond modifications to existing components:
```
services/frontend/src/
├── components/forecasts/
│   └── ForecastTable.tsx         # ADD multi-horizon columns
├── api/
│   ├── queries.ts                # ADD useAllHorizonsBulkPredictions hook
│   └── types.ts                  # ADD MultiHorizonForecastRow type
└── utils/
    └── forecastUtils.ts          # UPDATE joinForecastData for multi-horizon

k8s/
└── model-serving-configmap.yaml  # ADD horizons.json data entry
```

### Pattern 1: Parallel Horizon Queries
**What:** Fetch all four horizons simultaneously using React Query's `useQueries`
**When to use:** When multiple API calls return independent data that must be combined in the UI

```typescript
// Source: React Query official docs — parallel queries pattern
import { useQueries } from "@tanstack/react-query";

const HORIZONS = [1, 7, 14, 30];

export function useAllHorizonsPredictions() {
  const results = useQueries({
    queries: HORIZONS.map((h) => ({
      queryKey: ["predictions", "bulk", h],
      queryFn: async () => {
        const { data } = await apiClient.get<BulkPredictionResponse>(
          "/predict/bulk",
          { params: { horizon: h } },
        );
        return { horizon: h, data };
      },
    })),
  });
  const isLoading = results.some((r) => r.isLoading);
  const isError = results.every((r) => r.isError);
  return { results, isLoading, isError };
}
```

### Pattern 2: Multi-Horizon Row Merge
**What:** Merge per-horizon prediction data into a single row per ticker
**When to use:** Displaying forecasts for all horizons in one table row

```typescript
// Merge predictions from all horizons into per-ticker rows
export interface MultiHorizonForecastRow {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  current_price: number | null;
  daily_change_pct: number | null;
  // Per-horizon columns
  horizons: {
    [horizonDays: number]: {
      predicted_price: number;
      expected_return_pct: number;
      confidence: number | null;
      predicted_date: string;
      trend: TrendDirection;
    };
  };
  model_name: string;
}

export function joinMultiHorizonForecastData(
  horizonResults: Array<{ horizon: number; predictions: PredictionResponse[] }>,
  stocks: MarketOverviewEntry[],
): MultiHorizonForecastRow[] {
  const stockMap = new Map(stocks.map((s) => [s.ticker, s]));
  // Build ticker → { horizon → prediction } map
  const tickerHorizonMap = new Map<string, Record<number, PredictionResponse>>();
  for (const { horizon, predictions } of horizonResults) {
    for (const pred of predictions) {
      if (!tickerHorizonMap.has(pred.ticker)) {
        tickerHorizonMap.set(pred.ticker, {});
      }
      tickerHorizonMap.get(pred.ticker)![horizon] = pred;
    }
  }
  // Emit one row per ticker that has at least one horizon prediction
  const rows: MultiHorizonForecastRow[] = [];
  for (const [ticker, horizonPreds] of tickerHorizonMap) {
    const stock = stockMap.get(ticker);
    const currentPrice = stock?.last_close ?? null;
    const horizons: MultiHorizonForecastRow["horizons"] = {};
    for (const [h, pred] of Object.entries(horizonPreds)) {
      const hNum = Number(h);
      const expectedReturn = currentPrice != null && currentPrice > 0
        ? ((pred.predicted_price - currentPrice) / currentPrice) * 100
        : 0;
      horizons[hNum] = {
        predicted_price: pred.predicted_price,
        expected_return_pct: expectedReturn,
        confidence: pred.confidence,
        predicted_date: pred.predicted_date,
        trend: deriveTrend(expectedReturn),
      };
    }
    rows.push({
      ticker,
      company_name: stock?.company_name ?? null,
      sector: stock?.sector ?? null,
      current_price: currentPrice,
      daily_change_pct: stock?.daily_change_pct ?? null,
      horizons,
      model_name: Object.values(horizonPreds)[0]?.model_name ?? "unknown",
    });
  }
  return rows;
}
```

### Pattern 3: horizons.json ConfigMap Entry
**What:** Patch the model-serving ConfigMap to include `horizons.json`
**When to use:** Fixing `/predict/horizons` to return all four options

```yaml
# In the ConfigMap data:
horizons.json: |
  {"horizons": [1, 7, 14, 30], "default": 7}
```

The ConfigMap is projected as a volume into the model-serving pod at `/models/active/`.

### Anti-Patterns to Avoid
- **Loading all four horizons sequentially:** Use `useQueries` (parallel), not sequential `await` chains — adds latency
- **Storing all horizon data in a single piece of React state:** Each horizon query should have its own cache entry for independent refetching
- **Re-using the existing `ForecastRow` type for multi-horizon:** Define a new `MultiHorizonForecastRow` type to avoid confusion
- **Removing the single-horizon path entirely:** Keep `useBulkPredictions(horizon)` intact — it's used elsewhere (export CSV, comparison panel)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parallel async fetching | Custom Promise.all wrapper | `useQueries` from React Query | Cache, loading states, error handling built in |
| Multi-column table | Custom grid component | MUI DataGrid `GridColDef[]` | Already in use; column groups feature handles horizon grouping |
| Horizon config file | Custom env var parsing | JSON file in ConfigMap volume | Existing `load_available_horizons()` already reads from file path |

---

## Common Pitfalls

### Pitfall 1: horizons.json in ConfigMap is Not Reflected at Runtime
**What goes wrong:** ConfigMap is updated but the pod still serves the old value
**Why it happens:** K8s ConfigMap projected volumes update asynchronously (up to sync period delay); pods may cache the old file
**How to avoid:** Roll the model-serving deployment after patching the ConfigMap: `kubectl rollout restart deployment/stock-model-serving-predictor -n ml`
**Warning signs:** `/predict/horizons` still returns `{"horizons":[7]}` after ConfigMap patch

### Pitfall 2: MUI DataGrid Row ID Collision with Multi-Horizon
**What goes wrong:** If `getRowId` returns `row.ticker`, and the same ticker appears in multiple horizon datasets, DataGrid throws a duplicate key warning
**Why it happens:** The current `getRowId = (row: ForecastRow) => row.ticker` — fine for single-horizon but breaks if rows are duplicated
**How to avoid:** With multi-horizon columns (one row per ticker), ticker remains the unique ID — no collision. But if multiple rows per ticker are kept, use `${row.ticker}-${row.horizon_days}` as the ID.

### Pitfall 3: Skeleton Loading State for Four Parallel Queries
**What goes wrong:** Page shows partial data (some horizons loaded, others not), causing layout shifts
**Why it happens:** `useQueries` resolves each query independently
**How to avoid:** Gate rendering on `results.every(r => !r.isLoading)` — show a single loading skeleton until all four horizons are ready

### Pitfall 4: KServe Returns Identical Prices Across Horizons
**What goes wrong:** Users are confused seeing identical predicted_price in 1d, 7d, 14d, 30d columns
**Why it happens:** Single model produces same output regardless of horizon parameter (horizon only affects `predicted_date`)
**How to avoid:** Show `predicted_date` next to price, not just price alone. Consider labeling columns "Pred. Price (as of {date})" rather than just a number. This is a data limitation, not a bug.

### Pitfall 5: Export CSV/PDF breaks with Multi-Horizon Shape
**What goes wrong:** The existing CSV/PDF export logic iterates over `ForecastRow[]` which doesn't have per-horizon sub-objects
**Why it happens:** Export logic in `Forecasts.tsx` uses `filteredRows.map(r => [r.ticker, ..., r.predicted_price, ...])` — hard-coded single horizon
**How to avoid:** Update the export functions to flatten `MultiHorizonForecastRow.horizons` into a sequence of columns per horizon

---

## Code Examples

### Verify horizons.json is the Issue
```bash
# In the API pod — confirm load_available_horizons() fallback path:
kubectl exec -n ingestion deployment/stock-api -- \
  python3 -c "from app.services.prediction_service import load_available_horizons; print(load_available_horizons('/models/active'))"
# Returns: {'horizons': [7], 'default': 7}  ← fallback because horizons.json absent
```

### Create horizons.json via kubectl patch
```bash
# Option A: Patch ConfigMap that mounts to /models/active/
kubectl get configmap -n ml -o name | grep model-serving | head -1
# Then patch with:
kubectl patch configmap <name> -n ml --type merge \
  -p '{"data": {"horizons.json": "{\"horizons\": [1, 7, 14, 30], \"default\": 7}"}}'
kubectl rollout restart deployment/stock-model-serving-predictor -n ml
```

### MUI DataGrid Column Groups (Multi-Horizon)
```typescript
// Source: MUI X Data Grid docs — column grouping
// https://mui.com/x/react-data-grid/column-groups/
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef, GridColumnGroupingModel } from "@mui/x-data-grid";

const columnGroupingModel: GridColumnGroupingModel = [
  {
    groupId: "1d",
    headerName: "1-Day Forecast",
    children: [{ field: "return_1d" }, { field: "price_1d" }],
  },
  {
    groupId: "7d",
    headerName: "7-Day Forecast",
    children: [{ field: "return_7d" }, { field: "price_7d" }],
  },
  // ... 14d, 30d
];

<DataGrid
  columnGroupingModel={columnGroupingModel}
  experimentalFeatures={{ columnGrouping: true }}
  rows={multiHorizonRows}
  columns={columns}
  getRowId={(row) => row.ticker}
/>
```

---

## State of the Art

| Old Approach | Current Approach | Status |
|--------------|------------------|--------|
| Single-horizon table (toggle to switch) | Multi-horizon columns (all visible at once) | This phase implements |
| horizons.json missing → only 7d option | horizons.json present → all 4 options | This phase fixes |
| `ForecastRow` (single horizon shape) | `MultiHorizonForecastRow` (horizon map) | This phase adds |

---

## Open Questions

1. **Should the HorizonToggle be removed or kept alongside the multi-column view?**
   - What we know: The toggle currently controls which horizon is fetched; multi-horizon columns make the toggle redundant for the main table
   - What's unclear: Should the detail view (stock drawer) still use a horizon toggle?
   - Recommendation: Keep the toggle for the detail drawer (StockDetailChart uses a single horizon for the time-series chart); remove it from the main table header once multi-horizon columns are implemented

2. **Should the existing `ForecastRow` type be replaced or kept in parallel?**
   - What we know: `ForecastRow` is used in StockComparisonPanel, StockDetailSection, export functions, and filter logic
   - Recommendation: Keep `ForecastRow` for those consumers; add `MultiHorizonForecastRow` as a new type for the main table only

3. **What happens to JNJ (the one ticker without a prediction)?**
   - What we know: JNJ has market overview data but no KServe prediction (inference failure)
   - Recommendation: JNJ row simply won't appear in the table — this is correct behavior. No special handling needed.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x + vitest (frontend) |
| Config file | `pytest.ini` (backend), `vitest.config.ts` (frontend — if present) |
| Quick run command | `cd stock-prediction-platform && python -m pytest services/api/tests/ -x -q` |
| Full suite command | `cd stock-prediction-platform && python -m pytest services/api/tests/ ml/tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TBD | `/predict/horizons` returns all 4 horizons after ConfigMap fix | unit | `pytest services/api/tests/test_predict.py -x -k horizon` | ✅ |
| TBD | `joinMultiHorizonForecastData()` merges 4 horizons into one row per ticker | unit | Vitest unit test for forecastUtils | ❌ Wave 0 |
| TBD | ForecastTable renders columns for 1d, 7d, 14d, 30d | smoke | Playwright snapshot of `/forecasts` | N/A (manual) |

### Sampling Rate
- **Per task commit:** `python -m pytest services/api/tests/test_predict.py -x -q`
- **Per wave merge:** `python -m pytest services/api/tests/ -q`
- **Phase gate:** Full suite green + Playwright screenshot of Forecasts page showing multi-horizon columns

### Wave 0 Gaps
- [ ] `services/frontend/src/utils/forecastUtils.test.ts` — covers `joinMultiHorizonForecastData` merge logic
- [ ] Vitest config setup if not already present in frontend package.json

---

## Sources

### Primary (HIGH confidence)
- Live cluster verification — all API responses above were captured via `kubectl exec` against the running ingestion/stock-api deployment
- `ForecastTable.tsx`, `Forecasts.tsx`, `forecastUtils.ts` — direct source code inspection
- `predict.py`, `prediction_service.py`, `schemas.py` — direct source code inspection
- `config.py` — `AVAILABLE_HORIZONS = "1,7,14,30"` and `TICKER_SYMBOLS` confirmed

### Secondary (MEDIUM confidence)
- MUI X Data Grid column grouping pattern — standard MUI feature, verified via docs structure in codebase
- React Query `useQueries` parallel pattern — standard documented pattern

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Current state diagnosis: HIGH — verified against live cluster, all API responses confirmed
- Standard stack: HIGH — all libraries already in use, no new dependencies needed
- Architecture patterns: HIGH — uses existing project conventions (React Query, MUI DataGrid)
- Pitfalls: HIGH — derived from direct code and live system inspection

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable domain — no fast-moving dependencies)
