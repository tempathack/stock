---
phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard
plan: 03
subsystem: api
tags: [fastapi, websocket, feast, redis, pydantic, pytest]

# Dependency graph
requires:
  - phase: 71-02
    provides: Flink sentiment_writer job that materializes reddit_sentiment_fv features into Feast Redis

provides:
  - "/ws/sentiment/{ticker} WebSocket endpoint in ws.py pushing Feast sentiment every 60s"
  - "get_sentiment_features(ticker) service reading 5 fields from reddit_sentiment_fv"
  - "SentimentFeaturesResponse Pydantic schema with 7 fields"
  - "FEAST_STORE_PATH config setting (defaults /opt/feast)"
  - "5 unit tests covering service success/failure and WS endpoint smoke tests"
affects:
  - 71-04  # frontend SentimentPanel that consumes this WebSocket

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "run_in_threadpool pattern for synchronous Feast reads inside async WebSocket handlers"
    - "Local import inside _get_sentiment_sync to avoid circular imports (feast_online_service)"
    - "autouse monkeypatch fixture to mock asyncio.sleep + _get_sentiment_sync in WS tests"

key-files:
  created:
    - stock-prediction-platform/services/api/app/services/feast_online_service.py
    - stock-prediction-platform/services/api/tests/test_sentiment_ws.py
  modified:
    - stock-prediction-platform/services/api/app/routers/ws.py
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/config.py

key-decisions:
  - "Used run_in_threadpool from starlette.concurrency for blocking Feast reads inside async WS handler"
  - "feast_online_service.py is new file (not feast_service.py which does SQL registry freshness checks)"
  - "Added FEAST_STORE_PATH to Group 15 in config.py (was missing, needed for FeatureStore instantiation)"
  - "autouse fixture patches both _get_sentiment_sync and asyncio.sleep to prevent 60s hang in WS smoke tests"

patterns-established:
  - "Sentiment WS endpoint: accept -> recv_task -> push loop (60s) -> finally cancel recv_task"
  - "get_sentiment_features: try Feast, except any Exception return available=False (never crash)"

requirements-completed:
  - ALT-07
  - ALT-08

# Metrics
duration: 15min
completed: 2026-03-31
---

# Phase 71 Plan 03: FastAPI WebSocket Sentiment Endpoint and Feast Service Summary

**Per-ticker /ws/sentiment/{ticker} WebSocket endpoint backed by Feast Redis online store (reddit_sentiment_fv), with graceful fallback and 5 unit tests covering success, failure, and smoke paths**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-31T09:00:00Z
- **Completed:** 2026-03-31T09:15:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- WebSocket endpoint /ws/sentiment/{ticker} registered in ws.py, pushes sentiment JSON every 60s using run_in_threadpool pattern
- feast_online_service.get_sentiment_features() reads 5 fields from reddit_sentiment_fv, returns available=False on any exception (no crash)
- SentimentFeaturesResponse Pydantic schema added to schemas.py with 7 fields (ticker, 5 features, available, sampled_at)
- 5 unit tests created: 3 service tests (Feast raises, valid data, None avg_sentiment) + 2 WS smoke tests (endpoint registration, case normalization)
- All 176 tests pass (no regressions; 3 pre-existing test_metrics.py failures confirmed pre-existing)

## Task Commits

Each task was committed atomically:

1. **Task 1: FastAPI WebSocket endpoint + feast_online_service extension + Pydantic schema** - `8463738` (feat)
2. **Task 2: Unit tests for WebSocket sentiment endpoint and service** - `d76ae8b` (test)

**Plan metadata:** `ea08786` (docs: complete plan)

## Files Created/Modified

- `stock-prediction-platform/services/api/app/routers/ws.py` - Added ws_sentiment endpoint and _get_sentiment_sync helper
- `stock-prediction-platform/services/api/app/services/feast_online_service.py` - Created with get_sentiment_features() reading reddit_sentiment_fv
- `stock-prediction-platform/services/api/app/models/schemas.py` - Appended SentimentFeaturesResponse schema
- `stock-prediction-platform/services/api/app/config.py` - Added FEAST_STORE_PATH setting (Group 15)
- `stock-prediction-platform/services/api/tests/test_sentiment_ws.py` - Created with 5 unit tests

## Decisions Made

- Used `run_in_threadpool` from `starlette.concurrency` for synchronous Feast reads inside the async WS handler — consistent with FastAPI convention for blocking I/O in async context
- `feast_online_service.py` is a new file separate from `feast_service.py` (which handles SQL registry freshness checks) — clear responsibility separation
- Added `FEAST_STORE_PATH` to config.py (Group 15) because the existing settings object lacked this field required by Phase 70+ Feast usage
- Local import in `_get_sentiment_sync` to avoid circular imports at module load time

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added FEAST_STORE_PATH to config.py**
- **Found during:** Task 1 (feast_online_service.py creation)
- **Issue:** Plan mentioned `settings.FEAST_STORE_PATH` but this attribute was absent from app/config.py Settings class
- **Fix:** Added `FEAST_STORE_PATH: str = "/opt/feast"` to Group 15 of the Settings class
- **Files modified:** stock-prediction-platform/services/api/app/config.py
- **Verification:** Import succeeds, feast_online_service.py references `settings.FEAST_STORE_PATH` correctly
- **Committed in:** 8463738 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical setting)
**Impact on plan:** Required for feast_online_service to instantiate FeatureStore. No scope creep.

## Issues Encountered

- `test_metrics.py` has 3 pre-existing failures (not caused by this plan) — verified by running tests on clean branch before applying changes. These are out of scope.

## User Setup Required

None - no external service configuration required. FEAST_STORE_PATH defaults to /opt/feast and is configurable via environment variable.

## Next Phase Readiness

- WebSocket endpoint ready for frontend SentimentPanel consumption (Phase 71-04)
- Feast service handles unavailable Redis gracefully (returns available=false) so frontend can show loading state during pipeline startup
- Tests confirm no regressions in existing API test suite

---
*Phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard*
*Completed: 2026-03-31*
