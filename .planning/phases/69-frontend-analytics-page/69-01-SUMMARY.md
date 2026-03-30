---
phase: 69-frontend-analytics-page
plan: "01"
subsystem: analytics-backend
tags: [fastapi, pydantic, redis, flink, feast, kafka, argocd, python]
dependency_graph:
  requires: []
  provides:
    - GET /analytics/flink/jobs (FlinkJobsResponse)
    - GET /analytics/feast/freshness (FeastFreshnessResponse)
    - GET /analytics/kafka/lag (KafkaLagResponse)
    - GET /analytics/summary (AnalyticsSummaryResponse)
  affects:
    - stock-prediction-platform/services/api/app/main.py
    - stock-prediction-platform/services/api/app/models/schemas.py
tech_stack:
  added:
    - flink_service.py (httpx multi-URL aggregation)
    - feast_service.py (SQLAlchemy async feast_metadata query)
    - kafka_lag_service.py (confluent-kafka AdminClient in run_in_executor)
  patterns:
    - Redis cache-aside pattern (build_key / cache_get / cache_set)
    - Graceful fallback: all service functions return empty-but-valid on exception
    - Lazy import pattern for DB session (feast_service)
key_files:
  created:
    - stock-prediction-platform/services/api/app/routers/analytics.py
    - stock-prediction-platform/services/api/app/services/flink_service.py
    - stock-prediction-platform/services/api/app/services/feast_service.py
    - stock-prediction-platform/services/api/app/services/kafka_lag_service.py
    - stock-prediction-platform/services/api/tests/test_analytics_flink.py
    - stock-prediction-platform/services/api/tests/test_analytics_feast.py
    - stock-prediction-platform/services/api/tests/test_analytics_kafka.py
    - stock-prediction-platform/services/api/tests/test_analytics_argocd.py
    - stock-prediction-platform/services/api/tests/test_analytics_router.py
  modified:
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/config.py
    - stock-prediction-platform/services/api/app/main.py
decisions:
  - "Move confluent_kafka imports to module level in kafka_lag_service.py so test patching works at app.services.kafka_lag_service.AdminClient path"
  - "Move get_engine/get_async_session imports to module level in feast_service.py for patchability"
  - "Use _dt_type alias (bound at import time) for isinstance checks in feast_service.py to survive datetime module mock in tests"
  - "Patch settings.FLINK_REST_URLS to single URL in flink tests to control exact job count (3 URLs x 1 job = 3 when using default config)"
metrics:
  duration_seconds: 319
  completed_date: "2026-03-30"
  tasks_completed: 2
  tasks_total: 2
  files_created: 9
  files_modified: 3
  tests_added: 14
---

# Phase 69 Plan 01: Analytics Backend — Four FastAPI Endpoints Summary

**One-liner:** Four `/analytics/*` FastAPI endpoints (Flink jobs, Feast freshness, Kafka lag, summary) with Redis cache-aside, httpx+SQLAlchemy+confluent-kafka service modules, and 14 passing tests.

## What Was Built

### Service Modules
- **flink_service.py** — async multi-URL Flink REST proxy (`/v1/jobs/overview`), aggregates jobs from all three FlinkDeployment REST services, graceful empty-list fallback on connection failure
- **feast_service.py** — async SQLAlchemy query of `feast_metadata` table for per-FeatureView `last_updated_timestamp`, computes staleness_seconds and fresh/stale status; returns `registry_available=False` on any DB error
- **kafka_lag_service.py** — synchronous AdminClient + Consumer wrapped in `asyncio.get_event_loop().run_in_executor(None, ...)` for thread-safe async usage; computes per-partition committed vs high-watermark offset lag

### Router
- **analytics.py** — four endpoints under `/analytics` prefix with Redis TTLs matching frontend poll intervals: Flink=10s, Feast=30s, Kafka=15s, Summary=30s

### Schemas (appended to schemas.py)
`FlinkJobEntry`, `FlinkJobsResponse`, `FeastViewFreshness`, `FeastFreshnessResponse`, `KafkaPartitionLag`, `KafkaLagResponse`, `AnalyticsSummaryResponse`

### Config (added to Settings)
`FLINK_REST_URLS`, `ARGOCD_URL`, `ARGOCD_TOKEN`, `KAFKA_CONSUMER_GROUP`, `FEAST_FEATURE_VIEWS`

## Tests
- 10 unit tests: 2 flink (success + unreachable), 2 feast (success + DB unavailable), 2 kafka (success + unreachable), 4 argocd (synced, out-of-sync, no token, unreachable)
- 4 integration tests: one per endpoint, cache bypassed via autouse fixture
- Full pytest suite: 172 pass, 3 pre-existing metrics failures (unrelated to analytics work)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Flink test expected `total_running == 1` but got 3**
- **Found during:** Task 1 verification
- **Issue:** Default `FLINK_REST_URLS` has 3 URLs; mock returned the same sample job for each, producing 3 total running
- **Fix:** Patched `settings.FLINK_REST_URLS` to a single URL within both flink unit tests
- **Files modified:** `tests/test_analytics_flink.py`
- **Commit:** 4cf8959

**2. [Rule 1 - Bug] `AttributeError: feast_service has no attribute 'get_engine'`**
- **Found during:** Task 1 verification
- **Issue:** `get_engine` and `get_async_session` were imported lazily inside the function body; test patches at module attribute path failed
- **Fix:** Moved imports to module level in `feast_service.py`
- **Files modified:** `app/services/feast_service.py`
- **Commit:** 4cf8959

**3. [Rule 1 - Bug] `TypeError: isinstance() arg 2 must be a type` in feast_service.py**
- **Found during:** Task 1 verification
- **Issue:** Test patches entire `datetime` module, making `datetime.datetime` a MagicMock; `isinstance(ts, datetime.datetime)` then receives a non-type as arg 2
- **Fix:** Added `from datetime import datetime as _dt_type` — a name bound at import time, immune to module-level mocking
- **Files modified:** `app/services/feast_service.py`
- **Commit:** 4cf8959

**4. [Rule 1 - Bug] `AttributeError: kafka_lag_service has no attribute 'AdminClient'`**
- **Found during:** Task 1 verification
- **Issue:** `AdminClient` and `Consumer` imported lazily inside `_sync_get_kafka_lag`; test patch paths were at module level
- **Fix:** Moved `from confluent_kafka import Consumer, KafkaException, TopicPartition` and `from confluent_kafka.admin import AdminClient` to module-level imports
- **Files modified:** `app/services/kafka_lag_service.py`
- **Commit:** 4cf8959

## Self-Check: PASSED

All 9 created files exist on disk. Both task commits found in git log (4cf8959, 6dbcdd5). 14 tests pass, no new regressions.
