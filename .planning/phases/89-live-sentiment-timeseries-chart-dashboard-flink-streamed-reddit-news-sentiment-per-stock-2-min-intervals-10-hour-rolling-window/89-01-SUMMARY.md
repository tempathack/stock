---
phase: 89-live-sentiment-timeseries-chart-dashboard-flink-streamed-reddit-news-sentiment-per-stock-2-min-intervals-10-hour-rolling-window
plan: "01"
subsystem: api, infra, streaming
tags: [flink, timescaledb, alembic, fastapi, promtail, loki, jdbc, sentiment]

requires:
  - phase: 67-apache-flink-real-time-stream-processing
    provides: Flink sentiment_stream job that this plan extends with TUMBLE window + JDBC sink
  - phase: 64-timescaledb-olap
    provides: TimescaleDB setup that sentiment_timeseries hypertable depends on
  - phase: 71-sentiment-features
    provides: Kafka sentiment-aggregated sink that Flink job already writes to

provides:
  - Promtail K8s SD __path__ relabel fixed (separator _ with 3 source labels)
  - sentiment_timeseries TimescaleDB hypertable migration (006sentimentts)
  - SentimentDataPoint + SentimentTimeseriesResponse Pydantic schemas
  - get_sentiment_timeseries() async service function
  - GET /market/sentiment/{ticker}/timeseries FastAPI endpoint with 120s cache TTL
  - Flink TUMBLE(2-min) window aggregation replacing HOP(1min, 5min)
  - Flink JDBC sink writing 2-min windows to sentiment_timeseries TimescaleDB table

affects:
  - 89-02-frontend-sentiment-chart (consumes the API endpoint and sentiment_timeseries data)
  - monitoring-loki-log-collection (Promtail fix enables log scraping to work correctly)

tech-stack:
  added: [flink-connector-jdbc-3.2.0-1.19, postgresql-42.7.3]
  patterns:
    - TimescaleDB hypertable migration with best-effort create_hypertable (wraps in try/except)
    - Flink StatementSet for multi-sink jobs (Kafka + JDBC in single Flink execution)
    - Timestamp isoformat with hasattr guard for str/datetime compatibility in service layer

key-files:
  created:
    - stock-prediction-platform/services/api/alembic/versions/006_sentiment_timeseries.py
    - stock-prediction-platform/services/api/tests/test_sentiment_timeseries.py
  modified:
    - stock-prediction-platform/k8s/monitoring/promtail-configmap.yaml
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/services/market_service.py
    - stock-prediction-platform/services/api/app/routers/market.py
    - stock-prediction-platform/services/flink-jobs/sentiment_stream/sentiment_stream.py
    - stock-prediction-platform/services/flink-jobs/sentiment_stream/Dockerfile

key-decisions:
  - "Use StatementSet for dual-sink Flink job so Kafka and JDBC inserts run as a single Flink job (single execution graph)"
  - "Timestamp handling in service uses hasattr(isoformat) guard to handle both datetime (from DB) and str (from tests/mocks)"
  - "TUMBLE(2-min) chosen over HOP to produce non-overlapping windows matching sentiment_timeseries TimescaleDB schema primary key (ticker, window_start)"
  - "migration 006 wraps create_hypertable in try/except for portability when TimescaleDB extension not available"

patterns-established:
  - "Flink multi-sink: use create_statement_set() + add_insert_sql() for running multiple sinks in one job"
  - "Service timestamp isoformat: hasattr guard pattern for DB datetime vs str mock compatibility"

requirements-completed: []

duration: 7min
completed: "2026-04-03"
---

# Phase 89 Plan 01: Sentiment Timeseries Backend Summary

**Promtail log-path fix + TimescaleDB sentiment_timeseries hypertable + FastAPI /market/sentiment/{ticker}/timeseries endpoint + Flink TUMBLE(2-min) JDBC sink delivering 10h rolling window data**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-03T09:06:50Z
- **Completed:** 2026-04-03T09:14:15Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Fixed Promtail K8s SD `__path__` relabel: changed source_labels from pod_uid+container to namespace+pod_name+container with `separator: _`, enabling log collection to work in Kubernetes
- Created migration 006 with `sentiment_timeseries` TimescaleDB hypertable, Alembic-chained from `005timescaleolap`, with ticker/window_start composite primary key and descending index
- Added FastAPI GET `/market/sentiment/{ticker}/timeseries` endpoint returning `SentimentTimeseriesResponse` with 120s cache TTL, backed by async service function querying 10h rolling window
- Upgraded Flink sentiment_stream from HOP(1min, 5min) to TUMBLE(2min) and added JDBC sink writing to TimescaleDB via `StatementSet` dual-sink execution
- All 8 `test_sentiment_timeseries.py` tests GREEN; `test_promtail_path_uses_underscore_separator` GREEN; 230 tests pass (1 pre-existing unrelated failure in test_metrics.py)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix Promtail configmap + scaffold Wave 0 tests** - `6a3aa27` (feat)
2. **Task 2: DB migration 006 + schemas + market_service + API endpoint** - `17128ef` (feat)
3. **Task 3: Flink sentiment_stream TUMBLE(2-min) + JDBC sink + Docker JARs** - `574bdd2` (feat)

## Files Created/Modified

- `stock-prediction-platform/k8s/monitoring/promtail-configmap.yaml` - Fixed __path__ relabel_config (separator: _, 3 source_labels, new replacement glob)
- `stock-prediction-platform/services/api/alembic/versions/006_sentiment_timeseries.py` - TimescaleDB hypertable migration chained from 005timescaleolap
- `stock-prediction-platform/services/api/app/models/schemas.py` - Added SentimentDataPoint + SentimentTimeseriesResponse Pydantic models
- `stock-prediction-platform/services/api/app/services/market_service.py` - Added get_sentiment_timeseries() async function
- `stock-prediction-platform/services/api/app/routers/market.py` - Added GET /sentiment/{ticker}/timeseries endpoint with cache
- `stock-prediction-platform/services/api/tests/test_sentiment_timeseries.py` - 8-test scaffold for migration, schemas, service, endpoint
- `stock-prediction-platform/services/flink-jobs/sentiment_stream/sentiment_stream.py` - TUMBLE(2-min) window, JDBC sink CREATE TABLE + INSERT, StatementSet dual-sink
- `stock-prediction-platform/services/flink-jobs/sentiment_stream/Dockerfile` - Added flink-connector-jdbc + postgresql JDBC driver JARs

## Decisions Made

- **StatementSet for dual-sink**: Used `create_statement_set()` so Kafka and JDBC sinks run as a single Flink execution graph, avoiding two separate job submissions
- **hasattr isoformat guard**: Service function uses `hasattr(ts, "isoformat")` to handle datetime objects from PostgreSQL and string values from test mocks
- **TUMBLE not HOP**: TUMBLE produces non-overlapping windows matching the `(ticker, window_start)` primary key in `sentiment_timeseries` — no duplicate window_start values per ticker
- **try/except around create_hypertable**: Migration degrades gracefully when TimescaleDB extension is not available (e.g., vanilla PostgreSQL in CI)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed AsyncMock/MagicMock mismatch in test scaffold**
- **Found during:** Task 2 (sentiment timeseries tests execution)
- **Issue:** Test scaffold (written in Task 1) used `AsyncMock` for `mock_result`, causing `fetchall()` to return a coroutine instead of a list — TypeError when iterating rows
- **Fix:** Changed `mock_result` to `MagicMock()` so `fetchall()` returns synchronously as expected by the service code; added `MagicMock` to imports
- **Files modified:** `stock-prediction-platform/services/api/tests/test_sentiment_timeseries.py`
- **Verification:** All 8 tests GREEN after fix
- **Committed in:** `17128ef` (Task 2 commit)

**2. [Rule 1 - Bug] Added isoformat guard in service for str/datetime compatibility**
- **Found during:** Task 2 (test execution)
- **Issue:** Service code called `.isoformat()` on `row._mapping["timestamp"]` — works for PostgreSQL datetime objects but fails with string mock data (AttributeError: 'str' has no attribute 'isoformat')
- **Fix:** Added `hasattr(ts, "isoformat")` guard — uses `.isoformat()` for datetime objects, `str()` for strings
- **Files modified:** `stock-prediction-platform/services/api/app/services/market_service.py`
- **Verification:** All 8 tests GREEN; real DB datetime path remains correct
- **Committed in:** `17128ef` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs in mock setup and type handling)
**Impact on plan:** Both fixes required for test correctness. No scope creep.

## Issues Encountered

- Pre-existing test failure in `test_metrics.py::test_prediction_latency_histogram_exists` (unrelated to Phase 89 changes — confirmed by reverting and re-running). Logged as out-of-scope per deviation rules.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Backend data pipeline complete: migration, API endpoint, Flink JDBC sink all ready
- Phase 89-02 can now implement the frontend sentiment timeseries chart consuming `GET /market/sentiment/{ticker}/timeseries`
- Flink Docker image requires rebuild to include new JDBC JARs before deployment

---
*Phase: 89-01*
*Completed: 2026-04-03*
