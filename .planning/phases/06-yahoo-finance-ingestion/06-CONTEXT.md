# Phase 6: Yahoo Finance Ingestion Service - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement `yahoo_finance.py` and `kafka_producer.py` as working service modules inside `services/api/app/services/`. Fetch OHLCV from yfinance for a configurable ticker list, validate records, and publish to the correct Kafka topic. Phase 7 wires these to FastAPI endpoints; Phase 8 adds CronJobs — both are out of scope here.

</domain>

<decisions>
## Implementation Decisions

### Fetch Modes
- **Intraday:** `period="1d"`, `interval="1m"` — today's 1-minute bars (~390 per ticker)
- **Historical:** `period="5y"`, `interval="1d"` — 5 years of daily OHLCV bars (~1250 per ticker)
- Both modes produce the same record schema; `fetch_mode` field distinguishes them in the Kafka message

### Ticker List
- Default 20-stock dev subset hardcoded in the module (well-known S&P 500 blue chips)
- Overridable via env var `TICKER_SYMBOLS` (comma-separated string) in `config.py`
- Claude's Discretion: exact 20 tickers chosen (standard S&P 500 large-caps — AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK-B, JPM, JNJ, V, PG, UNH, HD, MA, BAC, XOM, PFE, ABBV, CVX)

### Validation Rules
- Claude's Discretion: reject records where any of open/high/low/close is null or NaN
- Claude's Discretion: reject records where volume is null, NaN, or negative
- Claude's Discretion: reject records where high < low (OHLC sanity)
- Invalid records are logged (structlog, WARNING level) with ticker + timestamp + reason — then skipped (no dead letter queue at this phase; that's Phase 9)
- Valid record count and skip count logged per ticker at INFO level

### Kafka Message Format
- Claude's Discretion: flat JSON, one message per OHLCV bar:
  ```json
  {
    "ticker": "AAPL",
    "timestamp": "2026-03-19T14:30:00Z",
    "open": 172.50,
    "high": 173.20,
    "low": 172.10,
    "close": 172.80,
    "volume": 1234567,
    "fetch_mode": "intraday",
    "ingested_at": "2026-03-19T15:01:00Z"
  }
  ```
- Timestamps as ISO 8601 UTC strings
- Topic routing: `fetch_mode="intraday"` → `intraday-data`; `fetch_mode="historical"` → `historical-data`
- Kafka message key: `"{ticker}"` (string) — enables topic partitioning by ticker

### Error Handling
- Claude's Discretion: per-ticker retry with `tenacity` (3 attempts, exponential backoff 2s/4s/8s) on yfinance network errors
- If all retries exhausted for a ticker: log ERROR and continue to next ticker (don't abort the full batch)
- confluent-kafka producer flush after each ticker's batch is fully produced

### Claude's Discretion
- Exact structlog field names in log lines
- Whether `yahoo_finance.py` returns a list of dicts or a pandas DataFrame internally (Claude picks cleaner option)
- Producer `acks` setting (recommend `acks="all"` for reliability)
- Whether to add a `YahooFinanceService` class or use module-level functions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stubs to implement
- `stock-prediction-platform/services/api/app/services/yahoo_finance.py` — empty stub to implement
- `stock-prediction-platform/services/api/app/services/kafka_producer.py` — empty stub to implement

### Config already wired
- `stock-prediction-platform/services/api/app/config.py` — `KAFKA_BOOTSTRAP_SERVERS`, `INTRADAY_TOPIC`, `HISTORICAL_TOPIC` already defined; add `TICKER_SYMBOLS` here

### Requirements
- `.planning/REQUIREMENTS.md` §INGEST-01, INGEST-02, INGEST-03, INGEST-06 — acceptance criteria for this phase

### Established patterns (read and follow)
- `stock-prediction-platform/services/api/app/utils/logging.py` — structlog JSON logging utility; use `get_logger()` in service modules
- `stock-prediction-platform/services/api/app/config.py` — `settings` singleton pattern; no `os.getenv()` in service code

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/utils/logging.py` — `get_logger()` helper for structlog JSON logging; import and use in both service modules
- `app/config.py` — `Settings` class with `KAFKA_BOOTSTRAP_SERVERS`, `INTRADAY_TOPIC`, `HISTORICAL_TOPIC` already defined
- `tenacity==8.3.0` — already in requirements; use for per-ticker retry logic
- `confluent-kafka==2.4.0` — already in requirements; use `Producer` class (not kafka-python)
- `yfinance==0.2.38` — already in requirements; use `yf.download()` or `yf.Ticker().history()`
- `pandas==2.2.2` — available for DataFrame → dict conversion

### Established Patterns
- All Python files: `from __future__ import annotations` + module docstring (Phase 1 pattern)
- Config via `settings = Settings()` singleton — never `os.getenv()` in service logic
- Structlog JSON logging is the project standard — every service module uses `get_logger()`

### Integration Points
- Phase 7 will import and call functions from `yahoo_finance.py` and `kafka_producer.py` via FastAPI endpoints
- `config.py` must be extended with `TICKER_SYMBOLS: str = "AAPL,MSFT,..."` (comma-separated, overridable)
- No new Dockerfile or K8s manifests needed — these are modules inside the existing `stock-api` service

</code_context>

<specifics>
## Specific Ideas

- No specific external references — standard yfinance + confluent-kafka patterns apply
- Phase 7 (FastAPI endpoints) will call these modules directly, so the public API of `yahoo_finance.py` should be clean functions (not CLI scripts)

</specifics>

<deferred>
## Deferred Ideas

- Dead-letter queue for failed records — Phase 9 (Kafka Consumers)
- K8s CronJob scheduling — Phase 8
- FastAPI endpoint wiring — Phase 7

</deferred>

---

*Phase: 06-yahoo-finance-ingestion*
*Context gathered: 2026-03-19*
