---
phase: 78-fix-frontend-broken-page-error-states
plan: "03"
subsystem: frontend
tags: [error-states, dashboard, mock-removal, ux]
dependency_graph:
  requires: [78-01]
  provides: [DASHBOARD-ERROR-STATE, DASHBOARD-MOCK-REMOVAL, DASHBOARD-INTRADAY-PLACEHOLDER]
  affects: [Dashboard.tsx]
tech_stack:
  added: []
  patterns: [per-panel-error-isolation, structured-page-error-with-header, empty-state-dashed-border]
key_files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx
  deleted:
    - stock-prediction-platform/services/frontend/src/utils/mockDashboardData.ts
decisions:
  - Removed CandlestickChart component entirely from Dashboard (intraday data is mock-only; replaced with dashed-border empty state)
  - Used void livePrices to suppress unused variable TS error (WebSocket hook kept for wsStatus badge)
  - Per-panel indicator error only wraps DashboardTAPanel (HistoricalChart uses indicatorSeries indirectly and gracefully handles empty array)
metrics:
  duration_seconds: 121
  completed_date: "2026-04-02"
  tasks_completed: 2
  files_modified: 1
  files_deleted: 1
---

# Phase 78 Plan 03: Dashboard Mock Removal and Error States Summary

Dashboard.tsx mock data fallbacks removed, page-level error wrapped in PageHeader + centered ErrorFallback, CandlestickChart replaced with dashed-border "Intraday candle data unavailable" empty state, per-panel indicator error isolation added, and mockDashboardData.ts deleted (161 lines removed).

## Tasks Completed

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Remove mock imports and mock fallback usages from Dashboard.tsx | a50aad1 | Done |
| 2 | Delete mockDashboardData.ts (no remaining callers) | f4cf384 | Done |

## What Was Built

Dashboard.tsx no longer silently falls back to stale mock data on query failure. Instead:

- **Market query failure** renders a full-page layout with the custom "Market Dashboard" gradient header followed by a centered `ErrorFallback` with a retry button — not a floating error box in a void.
- **Indicator query failure** renders `ErrorFallback` inside the Technical Indicators panel only — other panels (Metric Cards, Streaming Features, Reddit Sentiment) remain functional.
- **Intraday candle area** renders a dashed-border `Box` with `Typography` "Intraday candle data unavailable" instead of mock-generated candles.
- `mockDashboardData.ts` (161 lines, 2 functions) deleted permanently.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused CandlestickChart import and livePrice variable**
- **Found during:** Task 1 — TypeScript compile check after edits
- **Issue:** Replacing CandlestickChart with inline empty state left the import unused; removing the intradayCandles memo left `livePrice` (which was only passed as a prop to CandlestickChart) unused
- **Fix:** Removed `CandlestickChart` from dashboard component imports; replaced `livePrice` with `void livePrices` to suppress the TS6133 unused variable error while retaining the WebSocket hook (needed for wsStatus badge)
- **Files modified:** Dashboard.tsx
- **Commit:** a50aad1

## Self-Check: PASSED

- FOUND: Dashboard.tsx (modified, exists)
- CONFIRMED DELETED: mockDashboardData.ts
- FOUND commit a50aad1: fix(78-03): remove mock fallbacks and fix error states in Dashboard.tsx
- FOUND commit f4cf384: fix(78-03): delete mockDashboardData.ts (no remaining callers)
