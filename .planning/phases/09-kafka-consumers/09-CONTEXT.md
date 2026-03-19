# Phase 9: Kafka Consumers — Batch Writer - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the Kafka consumer service that reads from both `intraday-data` and `historical-data` Kafka topics in micro-batches and performs idempotent upserts into PostgreSQL (`ohlcv_intraday` and `ohlcv_daily` tables). The service lives in `services/kafka-consumer/consumer/` with its own Dockerfile, requirements.txt, and K8s Deployment in the `processing` namespace. K8s manifests (`configmap.yaml`, `kafka-consumer-deployment.yaml`) already exist from Phase 1 — this phase fills the stub Python files and Dockerfile.

Phase 6 (producer) and Phase 8 (CronJobs) are upstream dependencies. Phase 10+ (feature engineering) is the downstream consumer of the data this service writes.

</domain>

<decisions>
## Implementation Decisions

### Consumer Library
- **confluent-kafka** `Consumer` class (same vendor as the producer in Phase 6) — NOT kafka-python
- Consumer group ID: `stock-consumer-group` (from configmap `KAFKA_GROUP_ID`)
- Auto-offset-reset: `earliest` — ensures no data loss on first deployment
- Manual offset commit after successful batch write (enable.auto.commit=false)

### Micro-Batch Strategy
- Accumulate up to `BATCH_SIZE` (default 100, from configmap) messages OR wait `BATCH_TIMEOUT_MS` (default 5000ms) — whichever triggers first
- One batch may contain records for multiple tickers and multiple fetch_modes
- Route records to the correct upsert method based on `fetch_mode` field in each message

### Message Format (from Phase 6 OHLCVProducer)
```json
{
    "ticker": "AAPL",
    "timestamp": "2026-03-19T14:30:00+00:00",
    "open": 172.50,
    "high": 173.20,
    "low": 172.10,
    "close": 172.80,
    "volume": 1234567,
    "fetch_mode": "intraday",
    "ingested_at": "2026-03-19T15:01:00+00:00"
}
```
- `fetch_mode="intraday"` → upsert into `ohlcv_intraday` (PK: ticker, timestamp)
- `fetch_mode="historical"` → upsert into `ohlcv_daily` (PK: ticker, date parsed from timestamp)

### Idempotent Upserts
- `INSERT INTO ohlcv_intraday (...) VALUES ... ON CONFLICT (ticker, timestamp) DO UPDATE SET open=EXCLUDED.open, high=EXCLUDED.high, ...`
- `INSERT INTO ohlcv_daily (...) VALUES ... ON CONFLICT (ticker, date) DO UPDATE SET open=EXCLUDED.open, high=EXCLUDED.high, ...`
- `adj_close` and `vwap` columns set to NULL (not available from Yahoo Finance; populated by feature engineering in Phase 10+)
- Batch upserts use `psycopg2.extras.execute_values` for performance

### Foreign Key: stocks Table
- `ohlcv_daily` and `ohlcv_intraday` have FK references to `stocks(ticker)`
- Before upserting OHLCV records, ensure each ticker exists in `stocks` table:
  `INSERT INTO stocks (ticker, company_name) VALUES (%s, %s) ON CONFLICT (ticker) DO NOTHING`
- Uses ticker as placeholder `company_name` — Phase 30 (seed data) will fill in the full entity

### Retry Logic
- Claude's Discretion: `tenacity` retry decorator on batch write operations
- Retry on `psycopg2.OperationalError` and `psycopg2.InterfaceError` (transient DB errors)
- 3 attempts, exponential backoff (2s/4s/8s)
- After all retries exhausted: records are dead-lettered (logged, not re-queued)

### Dead-Letter Handling
- Failed records (after retry exhaustion) are logged at ERROR level via structlog with full record payload, error message, and failure reason
- No separate Kafka dead-letter topic for v1 — structured logging is the dead-letter queue
- Claude's Discretion: exact structlog field names for dead-letter log entries

### Graceful Shutdown
- Consumer loop handles SIGTERM/SIGINT for clean K8s pod shutdown
- Flushes any pending batch before exiting
- Closes consumer connection and DB pool

### Connection Pooling
- `psycopg2.pool.SimpleConnectionPool` with `minconn=1`, `maxconn=5`
- `DATABASE_URL` from environment (secretRef: `stock-platform-secrets`)

### Claude's Discretion
- Exact structlog field names in log lines
- Whether `processor.py` uses a class or module-level functions (recommend class for testability)
- Whether to use `ThreadedConnectionPool` or `SimpleConnectionPool` (recommend Simple — single consumer thread)
- Internal buffer data structure for micro-batch accumulation (list or deque)
- Poll timeout value for Kafka consumer loop (recommend 1.0s)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stubs to implement
- `stock-prediction-platform/services/kafka-consumer/consumer/main.py` — consumer entry point stub
- `stock-prediction-platform/services/kafka-consumer/consumer/processor.py` — message processor stub
- `stock-prediction-platform/services/kafka-consumer/consumer/db_writer.py` — database writer stub
- `stock-prediction-platform/services/kafka-consumer/consumer/__init__.py` — package init stub

### Config and deployment already created
- `stock-prediction-platform/k8s/processing/configmap.yaml` — `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_GROUP_ID`, `INTRADAY_TOPIC`, `HISTORICAL_TOPIC`, `BATCH_SIZE`, `BATCH_TIMEOUT_MS`, `LOG_LEVEL`
- `stock-prediction-platform/k8s/processing/kafka-consumer-deployment.yaml` — K8s Deployment spec (2 replicas, resource limits, liveness/readiness probes)

### Database schema
- `stock-prediction-platform/db/init.sql` — full schema for `stocks`, `ohlcv_daily`, `ohlcv_intraday` tables with PKs, indexes, and hypertables

### Kafka topics
- `stock-prediction-platform/k8s/kafka/kafka-topics.yaml` — `intraday-data` (3 partitions, 7-day retention) and `historical-data` (3 partitions, 30-day retention)

### Requirements
- `.planning/REQUIREMENTS.md` §CONS-01 through CONS-07 — acceptance criteria for this phase

### Upstream message format
- `stock-prediction-platform/services/api/app/services/kafka_producer.py` — `OHLCVProducer` produces flat JSON messages with keys: `ticker`, `timestamp`, `open`, `high`, `low`, `close`, `volume`, `fetch_mode`, `ingested_at`

### Established patterns (read and follow)
- `stock-prediction-platform/services/api/app/utils/logging.py` — structlog JSON logging utility; replicate `get_logger()` pattern in consumer service
- `stock-prediction-platform/services/api/app/config.py` — pydantic-settings `Settings` class pattern; replicate for consumer config

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Patterns
- `app/utils/logging.py` — structlog JSON logging with `get_logger()` helper; replicate this pattern in the consumer service (new logging.py inside `consumer/`)
- `app/config.py` — pydantic-settings `Settings` class; replicate for consumer with env vars from configmap
- Phase 6 `kafka_producer.py` — same JSON message format consumed here; key=ticker bytes, value=JSON bytes

### Established Patterns
- All Python files: `from __future__ import annotations` + module docstring
- Config via pydantic-settings `Settings` class — never `os.getenv()` in service logic
- Structlog JSON logging is the project standard
- TDD approach: test stubs first, then implementation (RED → GREEN)

### Integration Points
- Kafka messages produced by Phase 6 `OHLCVProducer` are consumed here
- PostgreSQL tables (`ohlcv_daily`, `ohlcv_intraday`) are the write targets
- `stocks` table must have the ticker before FK-constrained inserts
- K8s configmap provides all consumer configuration via env vars
- K8s secret `stock-platform-secrets` provides `DATABASE_URL`

### New Files Needed
- `consumer/config.py` — pydantic-settings for consumer
- `consumer/logging.py` — structlog setup (follow api service pattern)
- `consumer/main.py` — consumer loop entry point
- `consumer/processor.py` — micro-batch message processor
- `consumer/db_writer.py` — PostgreSQL batch writer with retry
- `requirements.txt` — dependencies
- `Dockerfile` — multi-stage build
- `tests/` — test directory (new, inside services/kafka-consumer/)

</code_context>

<specifics>
## Specific Ideas

- `psycopg2.extras.execute_values` is significantly faster than individual INSERT statements for batch operations — use it for all upserts
- The consumer must handle messages from both topics in a single consumer instance (subscribe to both topics in one group)
- Partition assignment: confluent-kafka handles this via consumer group protocol; no manual partition management needed
- The `fetch_mode` field in each message determines the target table routing — this is per-message, not per-topic (though in practice intraday-data messages always have fetch_mode=intraday)

</specifics>

<deferred>
## Deferred Ideas

- Separate Kafka dead-letter topic — v1 uses structured logging as DLQ
- Consumer lag monitoring with Prometheus metrics — future observability phase
- Schema Registry for message validation — internal pipeline, JSON sufficient for v1
- Horizontal auto-scaling based on consumer lag — future phase

</deferred>

---

*Phase: 09-kafka-consumers*
*Context gathered: 2026-03-19*
