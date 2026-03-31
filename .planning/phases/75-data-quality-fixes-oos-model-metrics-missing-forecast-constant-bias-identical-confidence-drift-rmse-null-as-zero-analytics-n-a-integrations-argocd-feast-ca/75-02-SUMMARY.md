---
phase: 75-data-quality-fixes-oos-model-metrics-missing-forecast-constant-bias-identical-confidence-drift-rmse-null-as-zero-analytics-n-a-integrations-argocd-feast-ca
plan: "02"
subsystem: ui
tags: [react, typescript, fastapi, pydantic, drift, rmse, oos-metrics]

# Dependency graph
requires:
  - phase: 75-01
    provides: Wave 0 test scaffolding for analytics/argocd/feast
provides:
  - RetrainStatusResponse.previous_oos_metrics field in API schema
  - Drift.tsx renders null RMSE as em-dash instead of 0.0000
  - DriftLogger.log_event() persists previous_model_rmse in drift event details
  - seed-data.sh includes previous_model_rmse in prediction_drift and concept_drift entries
affects: [drift-page, retrain-status-api, drift-detection-service]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Null-safe numeric rendering: use ?? null + conditional .toFixed() rather than ?? 0"
    - "Previous model OOS metrics flow from model_registry rows[1].metrics_json through RetrainStatusResponse.previous_oos_metrics to Drift.tsx"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/services/prediction_service.py
    - stock-prediction-platform/services/frontend/src/pages/Drift.tsx
    - stock-prediction-platform/services/frontend/src/api/types.ts
    - stock-prediction-platform/services/frontend/src/components/drift/RetrainStatusPanel.tsx
    - stock-prediction-platform/ml/drift/trigger.py
    - stock-prediction-platform/scripts/seed-data.sh

key-decisions:
  - "previous_model_rmse stored as key in DriftResult.details dict (not a separate column) - matches existing JSONB schema"
  - "historical_rmse from evaluate_and_trigger() is used as previous_model_rmse value since it represents baseline model RMSE"
  - "RetrainStatusPanel null RMSE renders as em-dash via conditional .toFixed() since number|null type requires null check"

patterns-established:
  - "Null-safe pattern for optional numeric fields: (field as number) ?? null, then conditional .toFixed(4) or em-dash"

requirements-completed: [DQ-75]

# Metrics
duration: 35min
completed: 2026-03-31
---

# Phase 75 Plan 02: Drift RMSE Null Fix Summary

**RetrainStatusResponse extended with previous_oos_metrics; Drift.tsx ?? null replaces ?? 0; DriftLogger now persists previous_model_rmse in drift event details**

## Performance

- **Duration:** 35 min
- **Started:** 2026-03-31T20:00:00Z
- **Completed:** 2026-03-31T20:35:00Z
- **Tasks:** 4 (Task 0 diagnostic + fix, Task 1 API schema, Task 2 frontend fix, Task 3 visual verification approved)
- **Files modified:** 7

## Accomplishments
- SQL diagnostic confirmed drift_logs.details_json had no previous_model_rmse in any of 15 DB rows; writer fixed
- RetrainStatusResponse schema extended with previous_oos_metrics: dict = {} field
- get_retrain_status_from_db() now populates previous_oos_metrics from rows[1].metrics_json filtered by oos_ prefix
- Drift.tsx old-model and new-model RMSE/MAE now use ?? null instead of hardcoded 0 or ?? 0
- RetrainStatusPanel renders null RMSE/MAE as em-dash instead of calling .toFixed(4) on null
- types.ts updated: previous_oos_metrics added to RetrainStatusResponse, rmse/mae types changed to number | null

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend RetrainStatusResponse schema and DB query** - `688f432` (feat)
2. **Task 0: Inspect and fix drift_logs.details_json writer** - `f11ef73` (fix)
3. **Task 2: Fix Drift.tsx null RMSE rendering** - `3901d55` (fix)

## Files Created/Modified
- `stock-prediction-platform/services/api/app/models/schemas.py` - Added previous_oos_metrics: dict = {} to RetrainStatusResponse
- `stock-prediction-platform/services/api/app/services/prediction_service.py` - Populated previous_oos_metrics from rows[1].metrics_json in get_retrain_status_from_db()
- `stock-prediction-platform/services/frontend/src/pages/Drift.tsx` - Replaced hardcoded rmse: 0 and ?? 0 with ?? null using previous_oos_metrics
- `stock-prediction-platform/services/frontend/src/api/types.ts` - Added previous_oos_metrics to RetrainStatusResponse type; changed rmse/mae to number | null
- `stock-prediction-platform/services/frontend/src/components/drift/RetrainStatusPanel.tsx` - Conditional null check for .toFixed(4) vs em-dash
- `stock-prediction-platform/ml/drift/trigger.py` - DriftLogger.log_event/log_check accept previous_model_rmse; evaluate_and_trigger passes historical_rmse
- `stock-prediction-platform/scripts/seed-data.sh` - Added previous_model_rmse to prediction_drift and concept_drift seed entries

## Decisions Made
- `previous_model_rmse` stored inside `details_json` JSONB dict (not a new column) — matches existing schema design
- `historical_rmse` from `evaluate_and_trigger()` used as `previous_model_rmse` since it represents the previous model's baseline RMSE
- RetrainStatusPanel uses conditional `rmse != null ? rmse.toFixed(4) : "—"` rather than optional chaining — clearer and TypeScript-clean

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] RetrainStatusPanel was calling .toFixed(4) on potentially null rmse/mae**
- **Found during:** Task 2 (Drift.tsx null RMSE fix)
- **Issue:** After changing types to number | null, RetrainStatusPanel.tsx would call .toFixed(4) on null values, throwing TypeError at runtime
- **Fix:** Added null checks — `rmse != null ? rmse.toFixed(4) : "—"` for both old and new model RMSE and MAE
- **Files modified:** stock-prediction-platform/services/frontend/src/components/drift/RetrainStatusPanel.tsx
- **Verification:** TypeScript compiles clean with no Drift.tsx errors
- **Committed in:** 3901d55 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical null-safety)
**Impact on plan:** Required fix — without it the panel would crash at runtime when displaying null metrics.

## Issues Encountered
- Task 0 diagnostic found drift_logs DB rows were seeded via seed-data.sh (not from the real drift detection pipeline). The DriftLogger writes to JSONL/S3, not the DB directly. Fixed both the JSONL writer (DriftLogger) and the seed script.
- Task 1 was already committed by a prior agent run (688f432) — verified and continued from Task 0.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Drift page RMSE null rendering verified by human — em-dash displays correctly for null RMSE values
- RetrainStatusResponse.previous_oos_metrics is live in the API schema
- DriftLogger will persist previous_model_rmse in future drift detection runs
- All 11 drift trigger tests and 11 prediction service tests pass

---
*Phase: 75-data-quality-fixes*
*Completed: 2026-03-31*
