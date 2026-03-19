# Phase 9: Kafka Consumers — Batch Writer - Research

**Researched:** 2026-03-19
**Domain:** Python Kafka consumer + PostgreSQL batch writes (confluent-kafka + psycopg2 + tenacity)
**Confidence:** HIGH

## Summary

This phase implements a standalone Python consumer service in `services/kafka-consumer/consumer/` that subscribes to both `intraday-data` and `historical-data` Kafka topics, accumulates messages into micro-batches, and performs idempotent upserts into PostgreSQL via `psycopg2`. The service runs as a K8s Deployment (2 replicas) in the `processing` namespace.

The three core modules are: `main.py` (consumer loop with graceful shutdown), `processor.py` (micro-batch accumulation and message deserialization), and `db_writer.py` (PostgreSQL batch upsert with retry and dead-letter logging). Configuration follows the established pydantic-settings pattern; logging follows the structlog JSON pattern from the API service.

**Primary recommendation:** Use confluent-kafka `Consumer` with manual offset commits, `psycopg2.extras.execute_values` for batch INSERT...ON CONFLICT DO UPDATE, and `tenacity` for retry logic on transient DB errors. Dead-letter handling via structlog ERROR logging (no separate DLQ topic for v1).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Consumer library:** confluent-kafka `Consumer` (not kafka-python)
- **Consumer group:** `stock-consumer-group` (from configmap)
- **Auto-offset-reset:** `earliest`
- **Manual offset commit:** `enable.auto.commit=false`, commit after successful batch write
- **Micro-batch:** `BATCH_SIZE=100` messages OR `BATCH_TIMEOUT_MS=5000` — whichever fires first
- **Idempotent upsert:** `INSERT ... ON CONFLICT DO UPDATE` on composite PKs
- **ohlcv_intraday PK:** (ticker, timestamp); **ohlcv_daily PK:** (ticker, date)
- **adj_close and vwap:** NULL (not in Kafka messages; populated by feature engineering later)
- **Stocks FK handling:** INSERT ticker into stocks ON CONFLICT DO NOTHING before OHLCV upsert
- **Retry:** tenacity, 3 attempts, exponential backoff 2s/4s/8s on psycopg2 transient errors
- **Dead-letter:** structlog ERROR logging with full record payload (no DLQ topic for v1)
- **Graceful shutdown:** SIGTERM/SIGINT handler, flush pending batch, close consumer + DB pool
- **Connection pool:** `SimpleConnectionPool(minconn=1, maxconn=5)`
- **Batch inserts:** `psycopg2.extras.execute_values` for performance
- **K8s configmap already exists:** `processing-config` with all required env vars
- **K8s deployment already exists:** `kafka-consumer-deployment.yaml` with 2 replicas

### Claude's Discretion
- Exact structlog field names in log lines
- Class vs function structure for processor.py (recommend class: `MessageProcessor`)
- `SimpleConnectionPool` vs `ThreadedConnectionPool` (recommend Simple — single consumer thread per process)
- Internal buffer data structure (recommend `list` — append is O(1) amortized)
- Poll timeout value (recommend 1.0s)
- Whether to split upsert into two methods or one generic method (recommend two: `upsert_intraday_batch` + `upsert_daily_batch` for clarity)

### Deferred Ideas (OUT OF SCOPE)
- Separate Kafka dead-letter topic (v2)
- Consumer lag Prometheus metrics (future observability)
- Schema Registry (internal pipeline, JSON sufficient)
- Horizontal auto-scaling (future phase)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONS-01 | Python Kafka consumer service for intraday-data topic | confluent-kafka `Consumer` subscribing to `intraday-data`, routing to `upsert_intraday_batch` |
| CONS-02 | Python Kafka consumer service for historical-data topic | Same consumer subscribing to `historical-data`, routing to `upsert_daily_batch` |
| CONS-03 | Micro-batch processing (configurable batch size and interval) | `MessageProcessor` accumulates up to `BATCH_SIZE` or `BATCH_TIMEOUT_MS`, then flushes |
| CONS-04 | Idempotent upsert writes (ON CONFLICT DO UPDATE) for ohlcv tables | `execute_values` with `INSERT ... ON CONFLICT (ticker, date/timestamp) DO UPDATE` |
| CONS-05 | Retry logic with exponential backoff | tenacity `@retry` decorator on batch write methods |
| CONS-06 | Dead-letter queue handling for failed records | structlog ERROR logging with full record payload after retry exhaustion |
| CONS-07 | Dockerfile + K8s Deployment for consumer service | Multi-stage Dockerfile; K8s manifests already exist, just need deploy-all.sh update |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| confluent-kafka | 2.4.0 | Kafka consumer client | Official Confluent Python client; same as producer in Phase 6 |
| psycopg2-binary | 2.9.9 | PostgreSQL adapter | De facto Python PostgreSQL driver; binary variant for easy install |
| tenacity | 8.3.0 | Retry with exponential backoff | Same as Phase 6; de facto Python retry library |
| pydantic-settings | 2.2.1 | Config management | Same pattern as API service |
| structlog | 24.2.0 | Structured JSON logging | Project standard from Phase 1 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | N/A | `json.loads()` for Kafka message deserialization | Every consumed message |
| signal (stdlib) | N/A | SIGTERM/SIGINT handling | Graceful shutdown in main.py |
| datetime (stdlib) | N/A | Timestamp parsing and date extraction | Converting message timestamps to DB types |
| time (stdlib) | N/A | `time.monotonic()` for batch timeout tracking | Micro-batch timeout logic |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg2-binary | asyncpg | asyncpg is async-only; consumer is synchronous poll loop — psycopg2 is simpler |
| SimpleConnectionPool | ThreadedConnectionPool | Only one thread per consumer process; Simple is sufficient and lighter |
| execute_values batch | Individual INSERTs | execute_values is 2-10x faster for batch operations |
| tenacity retry | Manual try/except loop | tenacity is declarative, configurable, and already in the project |

**Installation:**
```bash
# New requirements.txt for kafka-consumer service
confluent-kafka==2.4.0
psycopg2-binary==2.9.9
tenacity==8.3.0
pydantic-settings==2.2.1
structlog==24.2.0
```

## Architecture Patterns

### Recommended Project Structure
```
services/kafka-consumer/
├── Dockerfile
├── requirements.txt
├── consumer/
│   ├── __init__.py
│   ├── config.py          # pydantic-settings for consumer env vars
│   ├── logging.py         # structlog JSON setup (replicate API pattern)
│   ├── main.py            # Consumer loop entry point
│   ├── processor.py       # MessageProcessor: micro-batch accumulation
│   └── db_writer.py       # BatchWriter: PostgreSQL upsert + retry
└── tests/
    ├── __init__.py
    ├── conftest.py         # Shared fixtures (mock consumer, mock DB)
    ├── test_processor.py   # Unit tests for MessageProcessor
    ├── test_db_writer.py   # Unit tests for BatchWriter
    └── test_main.py        # Tests for consumer loop
```

### Pattern 1: Kafka Consumer with Manual Commit
**What:** confluent-kafka Consumer that polls, processes, and commits offsets only after successful batch write.
**When to use:** Always — ensures at-least-once delivery semantics.
**Example:**
```python
from confluent_kafka import Consumer, KafkaError

consumer = Consumer({
    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
    "group.id": settings.KAFKA_GROUP_ID,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})
consumer.subscribe([settings.INTRADAY_TOPIC, settings.HISTORICAL_TOPIC])

while running:
    msg = consumer.poll(timeout=1.0)
    if msg is None:
        continue
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        logger.error("consumer_error", error=str(msg.error()))
        continue
    processor.add_message(msg)
    if processor.should_flush():
        processor.flush()
        consumer.commit(asynchronous=False)
```

### Pattern 2: Micro-Batch Processor
**What:** Accumulate messages in a buffer; flush when batch_size or timeout is reached.
**When to use:** Core batch processing pattern.
**Example:**
```python
import time

class MessageProcessor:
    def __init__(self, batch_size: int, batch_timeout_ms: int, writer: BatchWriter):
        self._buffer: list[dict] = []
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._writer = writer
        self._batch_start: float = time.monotonic()

    def add_message(self, msg) -> None:
        record = json.loads(msg.value().decode("utf-8"))
        self._buffer.append(record)

    def should_flush(self) -> bool:
        if not self._buffer:
            return False
        if len(self._buffer) >= self._batch_size:
            return True
        elapsed_ms = (time.monotonic() - self._batch_start) * 1000
        return elapsed_ms >= self._batch_timeout_ms

    def flush(self) -> int:
        if not self._buffer:
            return 0
        intraday = [r for r in self._buffer if r["fetch_mode"] == "intraday"]
        daily = [r for r in self._buffer if r["fetch_mode"] == "historical"]
        count = 0
        if intraday:
            count += self._writer.upsert_intraday_batch(intraday)
        if daily:
            count += self._writer.upsert_daily_batch(daily)
        self._buffer.clear()
        self._batch_start = time.monotonic()
        return count
```

### Pattern 3: Idempotent Batch Upsert with execute_values
**What:** PostgreSQL INSERT...ON CONFLICT DO UPDATE using psycopg2.extras.execute_values for batch performance.
**When to use:** All OHLCV writes.
**Example:**
```python
from psycopg2.extras import execute_values

def upsert_intraday_batch(self, records: list[dict]) -> int:
    sql = """
        INSERT INTO ohlcv_intraday (ticker, timestamp, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (ticker, timestamp) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
    """
    values = [
        (r["ticker"], r["timestamp"], r["open"], r["high"], r["low"], r["close"], r["volume"])
        for r in records
    ]
    conn = self._pool.getconn()
    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, values)
        conn.commit()
    finally:
        self._pool.putconn(conn)
    return len(records)
```

### Pattern 4: Retry with Dead-Letter Logging
**What:** tenacity retry on batch writes; dead-letter logging after exhaustion.
**When to use:** All database operations.
**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import psycopg2

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type((psycopg2.OperationalError, psycopg2.InterfaceError)),
    reraise=True,
)
def _execute_upsert(self, sql, values, conn):
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()

def _dead_letter(self, records: list[dict], error: Exception) -> None:
    for record in records:
        logger.error(
            "dead_letter_record",
            ticker=record.get("ticker"),
            timestamp=record.get("timestamp"),
            fetch_mode=record.get("fetch_mode"),
            error=str(error),
            record=record,
        )
```

### Pattern 5: Stocks FK Ensure
**What:** Ensure ticker exists in stocks table before OHLCV upsert.
**When to use:** Before every batch write.
**Example:**
```python
def _ensure_tickers(self, tickers: set[str], conn) -> None:
    sql = """
        INSERT INTO stocks (ticker, company_name)
        VALUES %s
        ON CONFLICT (ticker) DO NOTHING
    """
    values = [(t, t) for t in tickers]
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
```

### Pattern 6: Consumer Config (pydantic-settings)
**What:** Replicate the API service config pattern for the consumer.
**When to use:** All configuration access.
**Example:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class ConsumerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
    KAFKA_GROUP_ID: str = "stock-consumer-group"
    INTRADAY_TOPIC: str = "intraday-data"
    HISTORICAL_TOPIC: str = "historical-data"

    # Batching
    BATCH_SIZE: int = 100
    BATCH_TIMEOUT_MS: int = 5000

    # Database
    DATABASE_URL: str = "postgresql://stockuser:devpassword123@localhost:5432/stockdb"

    # Logging
    LOG_LEVEL: str = "INFO"

settings = ConsumerSettings()
```
