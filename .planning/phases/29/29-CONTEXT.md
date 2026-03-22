# Phase 29 — Frontend /drift Page

## What This Phase Delivers

A fully functional `/drift` page replacing the placeholder card with:

1. **Active model info card** — name, scaler variant, version, trained date, active status badge
2. **Rolling performance chart** — RMSE, MAE, Directional Accuracy plotted over time from drift events
3. **Drift alert timeline** — chronological list of all drift events with type badge, severity indicator, timestamp, and affected features
4. **Retraining status panel** — last retrain date, in-progress indicator, old vs new model metric comparison
5. **Feature distribution charts** — training vs. recent data per feature with histogram overlays
6. **Auto-refresh** — drift data polled every 30 seconds
7. **Responsive layout** — mobile-first grid that stacks on small viewports

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| FDRFT-01 | Active model info card (name, version, trained date) | `ActiveModelCard` component |
| FDRFT-02 | Rolling performance chart (RMSE, MAE, Directional Accuracy over time) | `RollingPerformanceChart` component |
| FDRFT-03 | Drift alert timeline (type, severity, timestamp) | `DriftTimeline` component |
| FDRFT-04 | Retraining status panel (last date, in-progress indicator, old vs new metrics) | `RetrainStatusPanel` component |
| FDRFT-05 | Feature distribution charts (training vs. recent data) | `FeatureDistributionChart` component |

## Data Sources

### GET /models/drift → `DriftStatusResponse`

```typescript
interface DriftEventEntry {
  drift_type: string;       // "data_drift" | "prediction_drift" | "concept_drift"
  is_drifted: boolean;
  severity: string;         // "none" | "low" | "medium" | "high"
  details: Record<string, unknown>;  // per_feature stats, error metrics, etc.
  timestamp: string | null;
  features_affected: string[];
}

interface DriftStatusResponse {
  events: DriftEventEntry[];
  any_recent_drift: boolean;
  latest_event: DriftEventEntry | null;
  count: number;
}
```

- `events` sorted newest-first from backend
- `details` contains per-feature KS/PSI stats (data_drift), rolling error metrics (prediction_drift), or performance comparison (concept_drift)
- `features_affected` lists feature columns that drifted

### GET /models/comparison → `ModelComparisonResponse`

```typescript
interface ModelComparisonEntry {
  model_name: string;
  scaler_variant: string;
  version: number | null;
  is_winner: boolean;
  is_active: boolean;
  oos_metrics: Record<string, unknown>;  // rmse, mae, r2, mape, directional_accuracy
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

- Active model identified by `is_active: true`
- `saved_at` serves as the trained date
- `oos_metrics` contains all 6 evaluation metrics

## Existing Infrastructure

- **API hooks:** `useModelDrift()` and `useModelComparison()` already defined in `src/api/queries.ts`
- **Types:** `DriftEventEntry`, `DriftStatusResponse`, `ModelComparisonEntry`, `ModelComparisonResponse` in `src/api/types.ts`
- **Recharts 3.8.0** installed — `LineChart`, `BarChart`, `ComposedChart`, `ResponsiveContainer`, `Tooltip`, `Legend`
- **Shared UI:** `LoadingSpinner`, `ErrorFallback`, `PageHeader`, `PlaceholderCard`
- **Theme:** Bloomberg dark theme with CSS variables (`bg-primary`, `bg-surface`, `bg-card`, `accent`, `profit`, `loss`, `warning`, `border`)
- **Pattern:** Mock data fallback when API unavailable (consistent with Phases 26–28)

## Plan Breakdown

| Plan | Scope | Wave | Requirements |
|------|-------|------|-------------|
| 29-01 | Drift types, mock data, ActiveModelCard, DriftTimeline | 1 | FDRFT-01, FDRFT-03 |
| 29-02 | RollingPerformanceChart, RetrainStatusPanel | 2 | FDRFT-02, FDRFT-04 |
| 29-03 | FeatureDistributionChart, Drift.tsx wiring, build verification | 3 | FDRFT-05 |
