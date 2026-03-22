# Phase 26 — Frontend /models Page

## What This Phase Delivers

A fully functional `/models` page replacing the placeholder card with:

1. **Sortable/filterable model comparison table** showing all trained models with in-sample and OOS metrics side-by-side
2. **Winner model highlight** with visual distinction and reasoning text
3. **SHAP feature importance bar charts** for the top 5 models
4. **SHAP beeswarm-style plots** showing feature value ↔ SHAP impact relationships
5. **Fold-by-fold performance charts** per model (CV fold metrics visualization)

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| FMOD-01 | Sortable, filterable table of all trained models | `ModelComparisonTable` component with column sorting + model name filter |
| FMOD-02 | In-sample vs OOS metrics side-by-side columns | Dual metric columns in table (R², MAE, RMSE, MAPE, Dir. Accuracy) |
| FMOD-03 | Winner model highlighted with reasoning | Visual badge + explanation card |
| FMOD-04 | SHAP feature importance bar charts | `ShapBarChart` component (horizontal bars) |
| FMOD-05 | SHAP beeswarm plots | `ShapBeeswarmPlot` component (dot scatter by feature) |
| FMOD-06 | Fold-by-fold performance charts per model | `FoldPerformanceChart` component (multi-fold line/bar chart) |

## Data Sources

### GET /models/comparison → `ModelComparisonResponse`

```typescript
interface ModelComparisonEntry {
  model_name: string;          // e.g. "Ridge", "XGBoost"
  scaler_variant: string;      // e.g. "standard", "quantile"
  version: number | null;
  is_winner: boolean;
  is_active: boolean;
  oos_metrics: Record<string, unknown>;  // { rmse, mae, r2, mape, directional_accuracy }
  fold_stability: number | null;
  best_params: Record<string, unknown>;
  saved_at: string | null;
}

interface ModelComparisonResponse {
  models: ModelComparisonEntry[];
  winner: ModelComparisonEntry | null;
  count: number;
}
```

### SHAP Data

SHAP data was computed in Phase 16 and stored in the model registry. The current API does not expose a dedicated SHAP endpoint — data is embedded in model metadata files (`metadata.json` per model). For Phase 26, SHAP visualizations will use mock/sample data shapes and render client-side. A future API extension can serve SHAP data directly.

**SHAP data shape (from the SHAP analysis module):**
- Feature importance: `{ feature_name: mean_abs_shap_value }` — sorted descending
- Beeswarm: `{ feature_name: { values: number[], shap_values: number[] } }` — per-sample SHAP vs feature value

### Fold Performance Data

Fold-level metrics are stored within `oos_metrics` or alongside model metadata. For visualization purposes:
- `fold_metrics: { fold_N: { rmse, mae, r2 } }` — per-fold breakdown

## Existing Infrastructure (from Phase 25)

| Asset | Path | Status |
|-------|------|--------|
| Models page skeleton | `src/pages/Models.tsx` | Exists — placeholder, will be replaced |
| API query hook | `src/api/queries.ts` → `useModelComparison()` | Ready to use |
| API types | `src/api/types.ts` → `ModelComparisonEntry`, `ModelComparisonResponse` | Ready to use |
| UI components | `src/components/ui/` → LoadingSpinner, ErrorFallback, PlaceholderCard | Reusable |
| Layout | `src/components/layout/` → PageHeader | Reusable |
| Charts dir | `src/components/charts/` | Empty — will be populated |
| Tables dir | `src/components/tables/` | Empty — will be populated |
| Tailwind theme | `src/styles/globals.css` | Dark theme colors available |
| Package.json | No charting library installed yet | Need to add Recharts |

## Charting Library Decision

**Recharts** (built on D3 + React) — chosen because:
- Native React components (no imperative API)
- Lightweight (~100KB gzipped vs 500KB+ for full D3)
- Built-in responsive containers
- Good TypeScript support
- Supports bar, line, scatter (needed for all 3 chart types)
- Bloomberg-style dark theme achievable via `stroke`, `fill` props

## API Type Extensions Needed

The existing `ModelComparisonEntry` type needs extension to support SHAP and fold data:

```typescript
// Additional fields to add to types.ts
interface ShapFeatureImportance {
  feature: string;
  importance: number;
}

interface ShapBeeswarmPoint {
  feature: string;
  feature_value: number;
  shap_value: number;
}

interface FoldMetric {
  fold: number;
  rmse: number;
  mae: number;
  r2: number;
}

interface ModelDetailData {
  model_name: string;
  shap_importance: ShapFeatureImportance[];
  shap_beeswarm: ShapBeeswarmPoint[];
  fold_metrics: FoldMetric[];
}
```

## Visual Design Notes

- **Table**: Dark rows with alternating `bg-bg-surface` / `bg-bg-primary`, sticky header with `bg-bg-card`
- **Winner row**: Left border `border-l-4 border-accent`, subtle glow background
- **Sort indicators**: ▲/▼ arrows on column headers, accent color for active sort
- **Metric formatting**: R² to 4 decimals, RMSE/MAE to 6 decimals, percentage metrics with % sign
- **SHAP bar chart**: Horizontal bars, accent gradient, top 15 features, Bloomberg dark styling
- **Beeswarm**: Scatter dots colored by feature value (blue → red gradient), centered on y=0
- **Fold chart**: Small multiples or grouped bar chart showing metric per fold

## Page Layout (Desktop)

```
┌──────────────────────────────────────────────┐
│  Model Comparison (PageHeader)               │
│  Compare ML model performance...             │
├──────────────────────────────────────────────┤
│  🏆 Winner Card: [Model Name] — [Reasoning] │
├──────────────────────────────────────────────┤
│  [Filter: ___] [Sort by: ▼ OOS RMSE]        │
│  ┌──────────────────────────────────────┐    │
│  │  Model Table (full width)             │    │
│  │  Name | Scaler | R² IS|OOS | ...     │    │
│  └──────────────────────────────────────┘    │
├──────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐    │
│  │ SHAP Bar Chart  │ │ SHAP Beeswarm   │    │
│  │ (top features)  │ │ (value scatter)  │    │
│  └─────────────────┘ └─────────────────┘    │
├──────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐    │
│  │  Fold Performance Chart              │    │
│  │  (per selected model)                │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```
