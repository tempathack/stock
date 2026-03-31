---
phase: 70-display-flink-computed-streaming-features-in-the-dashboard
plan: 01
subsystem: api
tags: [feast, flink, redis, fastapi, pydantic, streaming-features]

# Dependency graph
requires:
  - phase: 67-apache-flink-real-time-stream-processing
    provides: feast_writer Flink job writing technical_indicators_fv to Redis online store
  - phase: 69-frontend-analytics-page
    provides: feast_online_service.py with get_sentiment_features pattern to extend
provides:
  - GET /market/streaming-features/{ticker} FastAPI endpoint returning EMA-20, RSI-14, MACD signal
  - StreamingFeaturesResponse Pydantic schema with available/source/sampled_at fields
  - get_streaming_features() async service function reading from Feast Redis online store
  - 5-second Redis cache for streaming features (separate TTL from 30s indicators cache)
affects:
  - 70-02: frontend Panel polling this endpoint at 5s intervals

# Tech tracking
tech-stack:
  added: []
  patterns:
    - run_in_threadpool wrapping synchronous Feast call to avoid blocking event loop
    - lazy import of feast inside function to avoid slow startup registry init
    - available=True only when at least one feature value is non-None
    - sys.modules patch.dict pattern for mocking feast in unit tests with importlib.reload

key-files:
  created:
    - stock-prediction-platform/services/api/app/services/feast_online_service.py (get_streaming_features added)
    - stock-prediction-platform/services/api/tests/test_streaming_features.py
  modified:
    - stock-prediction-platform/services/api/app/models/schemas.py (StreamingFeaturesResponse added)
    - stock-prediction-platform/services/api/app/routers/market.py (streaming_features route added)

key-decisions:
  - "run_in_threadpool wraps synchronous Feast Redis client to avoid blocking the async event loop"
  - "available=True only when at least one of ema_20/rsi_14/macd_signal is non-None (Flink job may not be running)"
  - "STREAMING_FEATURES_TTL=5 declared locally in market.py since cache.py has no streaming-features TTL constant"
  - "feast_online_service.py extended (not replaced) to add get_streaming_features alongside existing get_sentiment_features"

patterns-established:
  - "Lazy feast import inside _fetch_from_feast() avoids package-level registry init at startup"
  - "TDD: write failing tests first, verify RED, then implement, verify GREEN"

requirements-completed: [TBD-01]

# Metrics
duration: 4min
completed: 2026-03-31
---

# Phase 70 Plan 01: Streaming Features API Endpoint Summary

**FastAPI GET /market/streaming-features/{ticker} endpoint reading EMA-20, RSI-14, MACD signal from Feast Redis online store with 5s cache and graceful degradation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T11:55:13Z
- **Completed:** 2026-03-31T11:58:58Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `StreamingFeaturesResponse` Pydantic model to schemas.py with ticker, ema_20, rsi_14, macd_signal, available, source, sampled_at fields
- Created `get_streaming_features()` async service in feast_online_service.py using run_in_threadpool for safe Feast Redis access
- Added `GET /market/streaming-features/{ticker}` route in market.py with 5s cache TTL and uppercase ticker normalisation
- All 5 unit tests pass: 3 service tests (happy path, unavailable, all-None) + 2 router tests (happy path, lowercase normalisation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add StreamingFeaturesResponse schema and feast_online_service module** - `9a69a2a` (feat)
2. **Task 2: Add GET /market/streaming-features/{ticker} route to market.py** - `8e22ae3` (feat)

**Plan metadata:** (docs commit below)

_Note: Both tasks used TDD (RED then GREEN)_

## Files Created/Modified
- `stock-prediction-platform/services/api/app/models/schemas.py` - Added StreamingFeaturesResponse Pydantic model
- `stock-prediction-platform/services/api/app/services/feast_online_service.py` - Added get_streaming_features() async wrapper + _fetch_from_feast() sync function
- `stock-prediction-platform/services/api/app/routers/market.py` - Added streaming_features route with STREAMING_FEATURES_TTL=5
- `stock-prediction-platform/services/api/tests/test_streaming_features.py` - 5 unit tests for service and router

## Decisions Made
- Feast call wrapped in run_in_threadpool because Feast 0.61.0 uses synchronous Redis client internally — calling directly in an async handler would block the event loop
- available=True only when at least one feature has a non-None value (not just when the call succeeded); this handles the case where the Flink job hasn't produced data yet
- STREAMING_FEATURES_TTL=5 declared locally in market.py (cache.py has no streaming-features TTL constant)
- feast_online_service.py was extended with the new function, not replaced, preserving get_sentiment_features() from Phase 71

## Deviations from Plan

None - plan executed exactly as written.

Note: FEAST_STORE_PATH was already present in config.py (Group 15, line 79) from a prior phase, so no config.py change was needed despite the plan specifying one.

## Issues Encountered
- test_metrics.py::test_metrics_contains_default_http_metrics is a pre-existing failure unrelated to this plan (verified by stash check — fails before our changes).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend endpoint fully implemented and tested; ready for Plan 02 (frontend Panel polling /market/streaming-features at 5s intervals)
- Endpoint returns graceful available=False response when Feast/Redis is unavailable — frontend can handle both states

---
*Phase: 70-display-flink-computed-streaming-features-in-the-dashboard*
*Completed: 2026-03-31*

## Self-Check: PASSED

All files verified present. Both commits (9a69a2a, 8e22ae3) confirmed in git log.
