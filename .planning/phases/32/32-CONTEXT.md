# Phase 32 — Frontend Live Data Integration

## What This Phase Delivers

Refactor all four frontend pages from "mock-as-primary" or "mock-as-equal" patterns to API-first loading with mock data as error-only fallback. Add two new React Query hooks for the Phase 31 backend endpoints.

1. **Dashboard.tsx** — Already mostly API-first; tighten fallback so mock data only appears after API error (not on null/undefined)
2. **Forecasts.tsx** — Replace full-mock fallback when either query is missing with per-query error fallback; show `LoadingSpinner` until both resolve
3. **Drift.tsx** — Wire `rollingPerformance`, `retrainStatus`, and `featureDistributions` to live API (currently hard-wired to mock); add `useRollingPerformance` and `useRetrainStatus` hooks
4. **Models.tsx** — Already API-only for comparison data; no fallback changes needed (SHAP detail viz mock is intentional — no API for that yet)

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| LIVE-06 | Frontend shows loading spinner during API fetch (no flash of mock data) | All pages guard render behind `isLoading` check; mock data never rendered before API resolves |
| LIVE-07 | Frontend uses API as primary data source; mock data only on error | `?? mock()` pattern only in `isError` branches; remove from happy path |
| LIVE-08 | New API endpoints: /models/drift/rolling-performance and /models/retrain-status | ✅ (Phase 31 delivered backend) — Phase 32 adds matching frontend hooks |
| LIVE-09 | Drift page powered by live API data (rolling perf, retrain status, feature dists) | `useRollingPerformance` + `useRetrainStatus` hooks; Drift.tsx consumes live data |

## Architecture

### Current State (Phase 31 — Backend Done, Frontend Unchanged)

```
┌─────────────────────────────────────────────────────┐
│ Frontend Pages                                       │
│                                                      │
│  Dashboard:   marketQuery.data ?? mock()             │
│  Forecasts:   if (bulk && market) join() else mock() │
│  Models:      pure API (except SHAP detail)          │
│  Drift:       events from API, rest from mock()      │
│                                                      │
│  Hooks:       7 hooks (no rolling-perf, retrain-st)  │
└─────────────────────────────┬───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│ FastAPI Backend (Phase 31)                           │
│  /predict/{ticker}         — live inference + DB     │
│  /predict/bulk             — live inference + DB     │
│  /models/comparison        — DB-first + file fallback│
│  /models/drift             — DB-first + file fallback│
│  /models/drift/rolling-performance  — NEW            │
│  /models/retrain-status             — NEW            │
│  /market/overview          — Yahoo Finance + DB      │
│  /market/indicators/{t}    — indicators from DB      │
└─────────────────────────────────────────────────────┘
```

### Target State (Phase 32)

```
┌─────────────────────────────────────────────────────┐
│ Frontend Pages                                       │
│                                                      │
│  Dashboard:   LoadingSpinner → data | ErrorFallback  │
│  Forecasts:   LoadingSpinner → data | ErrorFallback  │
│  Models:      LoadingSpinner → data | ErrorFallback  │
│  Drift:       LoadingSpinner → data | ErrorFallback  │
│               (all charts wired to API hooks)        │
│                                                      │
│  Hooks:       9 hooks (+useRollingPerformance,       │
│                         +useRetrainStatus)           │
│                                                      │
│  Mock usage:  Error fallback only (never primary)    │
└─────────────────────────────┬───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│ FastAPI Backend (unchanged)                          │
│  All 8 endpoints returning live DB data              │
└─────────────────────────────────────────────────────┘
```

### Data Loading Pattern (Standard for All Pages)

```tsx
const query = useXxx();

if (query.isLoading) return <LoadingSpinner />;
if (query.isError && !query.data) {
  return <ErrorFallback message="..." onRetry={() => query.refetch()} />;
}

// Happy path: use query.data with ?? mock() ONLY for sub-sections that
// have no dedicated API endpoint yet (e.g., SHAP detail, intrday candles)
```

## Key Frontend Files

| File | Role |
|------|------|
| `src/api/queries.ts` | All React Query hooks — adding 2 new |
| `src/api/types.ts` | TypeScript interfaces — adding 2 new response types |
| `src/api/index.ts` | Re-exports — adding new hooks + types |
| `src/pages/Dashboard.tsx` | Dashboard page — tighten fallback pattern |
| `src/pages/Forecasts.tsx` | Forecasts page — per-query error fallback |
| `src/pages/Drift.tsx` | Drift page — major refactor to API-first |
| `src/utils/mockDriftData.ts` | Mock — kept for error fallback only |
| `src/utils/mockDashboardData.ts` | Mock — kept for error fallback only |
| `src/utils/mockForecastData.ts` | Mock — kept for error fallback only |
| `src/utils/mockIndicatorData.ts` | Mock — kept for error fallback only |

## Backend Endpoint Contracts (Phase 31)

### GET /models/drift/rolling-performance?days=30

```json
{
  "entries": [
    { "date": "2026-03-01", "rmse": 0.023, "mae": 0.018, "directional_accuracy": 0.62, "n_predictions": 5 }
  ],
  "model_name": "CatBoost_standard",
  "period_days": 30,
  "count": 30
}
```

### GET /models/retrain-status

```json
{
  "model_name": "CatBoost_standard",
  "version": "3",
  "trained_at": "2026-03-20T08:30:00Z",
  "is_active": true,
  "oos_metrics": { "oos_rmse": 0.023, "oos_mae": 0.019 },
  "previous_model": "Ridge_quantile",
  "previous_trained_at": "2026-03-15T10:00:00Z"
}
```

## Dependencies

- Phase 31 (Live Model Inference API) — delivers the /rolling-performance and /retrain-status endpoints
- Phase 25–29 React components — already exist, just need data source changes
