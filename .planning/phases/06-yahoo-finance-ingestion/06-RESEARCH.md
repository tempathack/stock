# Phase 6: Yahoo Finance Ingestion Service - Research

**Researched:** 2026-03-19
**Domain:** Python data ingestion (yfinance + confluent-kafka + tenacity)
**Confidence:** HIGH

## Summary

This phase implements two Python service modules -- `yahoo_finance.py` (data fetching + validation) and `kafka_producer.py` (Kafka publishing) -- inside the existing FastAPI service at `services/api/app/services/`. The implementation uses three pinned libraries: yfinance==0.2.38 for Yahoo Finance OHLCV data, confluent-kafka==2.4.0 for Kafka producing, and tenacity==8.3.0 for retry logic.

Key technical consideration: yfinance 0.2.38 predates the `multi_level_index` parameter (added in v0.2.47). When downloading a single ticker, `yf.download()` returns a flat pandas DataFrame with columns `Open`, `High`, `Low`, `Close`, `Volume`. The safest pattern is per-ticker downloads (one `yf.download()` call per ticker), which avoids MultiIndex complexity entirely and aligns naturally with the per-ticker retry strategy.

The confluent-kafka Producer is used in its simplest form: manual `json.dumps().encode('utf-8')` serialization without Schema Registry. This is appropriate for an internal Kafka pipeline where the consumer is also under our control.

**Primary recommendation:** Download one ticker at a time with `yf.download(ticker, period=..., interval=...)`, validate each row, serialize to flat JSON, and produce to the correct Kafka topic with `ticker` as the message key. Flush after each ticker batch.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Intraday fetch:** `period="1d"`, `interval="1m"` (~390 bars/ticker)
- **Historical fetch:** `period="5y"`, `interval="1d"` (~1250 bars/ticker)
- Both modes produce the same record schema; `fetch_mode` field distinguishes them
- Default 20-stock dev subset hardcoded; overridable via `TICKER_SYMBOLS` env var in `config.py`
- Invalid records logged (structlog, WARNING) with ticker + timestamp + reason, then skipped
- Valid record count and skip count logged per ticker at INFO level
- Flat JSON Kafka message format (one message per OHLCV bar)
- Timestamps as ISO 8601 UTC strings
- Topic routing: `intraday` -> `intraday-data`; `historical` -> `historical-data`
- Kafka message key: `"{ticker}"` (string)
- Per-ticker retry with tenacity: 3 attempts, exponential backoff 2s/4s/8s on yfinance network errors
- If all retries exhausted for a ticker: log ERROR and continue to next ticker
- confluent-kafka producer flush after each ticker's batch is fully produced
- No dead letter queue (deferred to Phase 9)
- No FastAPI endpoint wiring (deferred to Phase 7)
- No K8s CronJob scheduling (deferred to Phase 8)

### Claude's Discretion
- Exact 20 tickers: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK-B, JPM, JNJ, V, PG, UNH, HD, MA, BAC, XOM, PFE, ABBV, CVX
- Validation: reject null/NaN open/high/low/close; reject null/NaN/negative volume; reject high < low
- Kafka message format: flat JSON as specified in CONTEXT.md
- structlog field names in log lines
- Internal data representation (list of dicts vs DataFrame) -- recommend DataFrame internally, convert to dicts for Kafka
- Producer `acks` setting -- recommend `acks=all` for reliability
- Class vs module-level functions -- recommend class-based `YahooFinanceService` for testability

### Deferred Ideas (OUT OF SCOPE)
- Dead-letter queue for failed records (Phase 9)
- K8s CronJob scheduling (Phase 8)
- FastAPI endpoint wiring (Phase 7)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INGEST-01 | yahoo_finance.py service -- fetches OHLCV for S&P 500 tickers via yfinance | yfinance 0.2.38 `yf.download()` API with per-ticker downloads; tenacity retry decorator |
| INGEST-02 | S&P 500 ticker list (dev: 20-stock subset, prod: full universe) | 20 hardcoded tickers in module; `TICKER_SYMBOLS` env var in config.py (comma-separated) |
| INGEST-03 | kafka_producer.py -- validates, normalizes, and publishes to Kafka topics | confluent-kafka Producer with json.dumps serialization; topic routing by fetch_mode |
| INGEST-06 | Data validation and normalization logic (schema enforcement, nulls, types) | Pandas-based validation: dropna on OHLC, filter NaN/negative volume, assert high >= low |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | 0.2.38 (pinned) | Fetch OHLCV data from Yahoo Finance | Only free Yahoo Finance Python client; already in requirements.txt |
| confluent-kafka | 2.4.0 (pinned) | Kafka producer client | Official Confluent Python client; librdkafka-based; already in requirements.txt |
| tenacity | 8.3.0 (pinned) | Retry with exponential backoff | De facto Python retry library; already in requirements.txt |
| pandas | 2.2.2 (pinned) | DataFrame manipulation for OHLCV data | yfinance returns DataFrames natively; already in requirements.txt |
| structlog | 24.2.0 (pinned) | Structured JSON logging | Project standard; `get_logger()` utility already exists |
| pydantic-settings | 2.2.1 (pinned) | Config management | Settings singleton pattern established in config.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | N/A | `math.isnan()` for NaN checks | Validation of float fields |
| json (stdlib) | N/A | `json.dumps()` for Kafka serialization | Serialize OHLCV records to bytes |
| datetime (stdlib) | N/A | ISO 8601 timestamp formatting | `ingested_at` field, timestamp conversion |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Per-ticker `yf.download()` | Multi-ticker batch download | Batch is faster but returns MultiIndex DataFrame, complicates error handling per ticker |
| `json.dumps()` serialization | confluent-kafka JSONSerializer + Schema Registry | Schema Registry adds operational complexity not needed for internal pipeline |
| Class-based service | Module-level functions | Functions are simpler but classes provide better testability via dependency injection |

**Installation:**
```bash
# All packages already in requirements.txt -- no new installs needed
pip install -r requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
services/api/app/
├── config.py              # Add TICKER_SYMBOLS setting
├── services/
│   ├── yahoo_finance.py   # YahooFinanceService class (fetch + validate)
│   └── kafka_producer.py  # OHLCVProducer class (serialize + produce)
└── utils/
    └── logging.py         # get_logger() -- already exists
```

### Pattern 1: Per-Ticker Download with Retry
**What:** Download OHLCV data one ticker at a time, wrapping each call in a tenacity retry decorator.
**When to use:** Always -- this is the core fetch pattern.
**Example:**
```python
# Source: tenacity docs + yfinance 0.2.38 API
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import yfinance as yf
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    reraise=True,
)
def _fetch_ticker(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV for a single ticker with retry."""
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    return df
```

### Pattern 2: DataFrame Validation Pipeline
**What:** Validate each row of the returned DataFrame against OHLC/volume rules before producing to Kafka.
**When to use:** After every fetch, before Kafka production.
**Example:**
```python
def validate_ohlcv(df: pd.DataFrame, ticker: str) -> tuple[list[dict], int]:
    """Validate DataFrame rows, return (valid_records, skip_count)."""
    valid = []
    skip_count = 0
    for idx, row in df.iterrows():
        # Check nulls/NaN on OHLC
        if any(pd.isna(row[col]) for col in ["Open", "High", "Low", "Close"]):
            logger.warning("invalid_record", ticker=ticker, timestamp=str(idx), reason="null_ohlc")
            skip_count += 1
            continue
        # Check volume
        if pd.isna(row["Volume"]) or row["Volume"] < 0:
            logger.warning("invalid_record", ticker=ticker, timestamp=str(idx), reason="invalid_volume")
            skip_count += 1
            continue
        # OHLC sanity
        if row["High"] < row["Low"]:
            logger.warning("invalid_record", ticker=ticker, timestamp=str(idx), reason="high_lt_low")
            skip_count += 1
            continue
        valid.append({...})  # build record dict
    return valid, skip_count
```

### Pattern 3: Kafka Producer with Delivery Callback
**What:** Produce JSON-serialized messages with a delivery report callback and per-ticker flush.
**When to use:** For all Kafka message production.
**Example:**
```python
from confluent_kafka import Producer
import json

def _delivery_report(err, msg):
    if err is not None:
        logger.error("kafka_delivery_failed", error=str(err), topic=msg.topic())

producer = Producer({
    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
    "acks": "all",
})

# Produce one message per record
for record in valid_records:
    producer.produce(
        topic=topic,
        key=record["ticker"].encode("utf-8"),
        value=json.dumps(record).encode("utf-8"),
        callback=_delivery_report,
    )
# Flush after entire ticker batch
producer.flush(timeout=30)
```

### Pattern 4: Config Extension
**What:** Add `TICKER_SYMBOLS` to the existing `Settings` class.
**When to use:** Single place to add the new env var.
**Example:**
```python
# In config.py, add to Settings class:
TICKER_SYMBOLS: str = "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,BRK-B,JPM,JNJ,V,PG,UNH,HD,MA,BAC,XOM,PFE,ABBV,CVX"
```

### Anti-Patterns to Avoid
- **Multi-ticker batch download with shared retry:** If one ticker fails in a batch of 20, the entire batch retries. Use per-ticker downloads instead.
- **`os.getenv()` in service code:** The project uses `settings` singleton from config.py. Never read env vars directly in service modules.
- **Blocking `producer.poll()` in a loop:** Use `flush()` after each ticker batch instead of manual polling.
- **Iterating with `df.iterrows()` on large DataFrames:** For ~390 or ~1250 rows this is acceptable, but for larger datasets consider vectorized validation. At this scale, `iterrows()` is fine.
- **Using `yf.Ticker().history()` instead of `yf.download()`:** Both work, but `yf.download()` is the canonical multi-purpose API and is what the project documentation references.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry with backoff | Custom while-loop retry | `tenacity` decorator | Edge cases: jitter, max attempts, exception filtering, logging |
| Kafka producer | Raw socket/HTTP to Kafka | `confluent_kafka.Producer` | librdkafka handles batching, compression, connection pooling |
| Yahoo Finance API | Direct HTTP to Yahoo endpoints | `yfinance` library | Handles cookies, crumb tokens, rate limiting, data parsing |
| JSON serialization for Kafka | Custom binary format | `json.dumps().encode('utf-8')` | Human-readable, debuggable, standard |
| Config management | `os.getenv()` calls | `pydantic-settings` `Settings` | Type coercion, validation, .env file support |

**Key insight:** All three core libraries (yfinance, confluent-kafka, tenacity) are already pinned in requirements.txt. This phase writes pure application logic using established project patterns -- no new dependencies.

## Common Pitfalls

### Pitfall 1: yfinance 0.2.38 MultiIndex Surprises
**What goes wrong:** Even for a single ticker, certain yfinance versions return MultiIndex columns. In v0.2.38, single-ticker download returns flat columns (`Open`, `High`, etc.) but this behavior changed in later versions.
**Why it happens:** The `multi_level_index` parameter was added in v0.2.47. In v0.2.38, multi-ticker downloads return MultiIndex; single-ticker downloads return flat columns.
**How to avoid:** Always download one ticker at a time. Access columns as `df["Open"]`, not `df[("Open", "AAPL")]`. If paranoid, add `if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)`.
**Warning signs:** `KeyError: 'Open'` when accessing DataFrame columns.

### Pitfall 2: yfinance Timezone Handling for Intraday Data
**What goes wrong:** Intraday (1m) data returns timestamps in the exchange's local timezone (US/Eastern for NYSE). Historical daily data returns timezone-naive dates.
**Why it happens:** Yahoo Finance returns intraday data with timezone info; daily data without.
**How to avoid:** Always convert timestamps to UTC before serialization: `idx.tz_convert("UTC")` for tz-aware or `idx.tz_localize("UTC")` for tz-naive. Use `.isoformat()` for ISO 8601 output.
**Warning signs:** Timestamps showing as "2026-03-19 09:30:00-04:00" instead of UTC.

### Pitfall 3: yfinance Returns Empty DataFrame
**What goes wrong:** `yf.download()` silently returns an empty DataFrame for invalid tickers, delisted stocks, or when Yahoo rate-limits.
**Why it happens:** yfinance catches HTTP errors internally and returns empty results rather than raising exceptions.
**How to avoid:** Check `df.empty` immediately after download. Log a WARNING and skip the ticker if empty. Do NOT retry on empty results -- it's usually not a transient error.
**Warning signs:** Zero valid records for a ticker that should have data.

### Pitfall 4: confluent-kafka Producer Buffering
**What goes wrong:** Messages appear to be sent but never arrive at Kafka. No errors are raised.
**Why it happens:** `produce()` is asynchronous -- it buffers messages locally. Without `flush()` or `poll()`, the delivery callback never fires and messages may be lost on process exit.
**How to avoid:** Call `producer.flush(timeout=30)` after each ticker batch. Use a delivery callback to catch per-message errors.
**Warning signs:** Messages "sent" but Kafka topic is empty.

### Pitfall 5: BRK-B Ticker Symbol
**What goes wrong:** Ticker `BRK-B` (Berkshire Hathaway Class B) uses a hyphen, which some systems interpret as a minus sign.
**Why it happens:** Yahoo Finance uses `BRK-B` as the canonical symbol, but URL encoding or string splitting on `-` can cause issues.
**How to avoid:** Treat ticker symbols as opaque strings. Split `TICKER_SYMBOLS` only on commas, never on hyphens.
**Warning signs:** `BRK` appearing without `-B`, or download returning empty for `BRK-B`.

### Pitfall 6: Volume=0 vs Volume=NaN
**What goes wrong:** Some OHLCV rows have `Volume=0` (legitimate for pre-market or after-hours bars in 1m data). Rejecting `Volume=0` would discard valid data.
**Why it happens:** Not all 1-minute intervals have trades, but the bar still exists with OHLC values from the last trade.
**How to avoid:** Only reject `Volume` when it is NaN or negative. `Volume=0` is valid and should pass validation.
**Warning signs:** Large numbers of skipped records during intraday fetch.

## Code Examples

### Complete Kafka Message Record
```python
# Source: CONTEXT.md locked format
record = {
    "ticker": "AAPL",
    "timestamp": "2026-03-19T14:30:00+00:00",  # UTC ISO 8601
    "open": 172.50,
    "high": 173.20,
    "low": 172.10,
    "close": 172.80,
    "volume": 1234567,
    "fetch_mode": "intraday",  # or "historical"
    "ingested_at": "2026-03-19T15:01:00+00:00",  # UTC ISO 8601
}
```

### Tenacity Retry Configuration
```python
# Source: tenacity docs, CONTEXT.md spec (3 attempts, 2s/4s/8s)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import requests
import logging

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type((
        requests.ConnectionError,
        requests.Timeout,
        requests.HTTPError,
    )),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)
def _fetch_ticker_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    return df
```

### Timestamp Normalization
```python
# Source: pandas docs -- converting yfinance index to UTC ISO 8601
from datetime import datetime, timezone

def _normalize_timestamp(idx_value) -> str:
    """Convert pandas Timestamp to UTC ISO 8601 string."""
    ts = pd.Timestamp(idx_value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC")
    else:
        ts = ts.tz_localize("UTC")
    return ts.isoformat()

def _get_ingested_at() -> str:
    """Return current UTC time as ISO 8601."""
    return datetime.now(timezone.utc).isoformat()
```

### Producer Configuration
```python
# Source: confluent-kafka docs
from confluent_kafka import Producer
from app.config import settings

producer_config = {
    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
    "acks": "all",
    "retries": 3,
    "retry.backoff.ms": 100,
    "linger.ms": 5,           # small batch window for throughput
    "batch.num.messages": 100, # batch up to 100 messages
}
producer = Producer(producer_config)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yf.Ticker(t).history()` | `yf.download(t, ...)` | yfinance 0.2.x | `download()` is preferred for bulk data; `history()` remains valid |
| `kafka-python` library | `confluent-kafka` (librdkafka) | 2020+ | confluent-kafka is 5-10x faster, officially supported by Confluent |
| Manual retry loops | `tenacity` decorators | 2018+ | Declarative retry with backoff, jitter, exception filtering |
| `multi_level_index` param | Not available in 0.2.38 | Added in 0.2.47 | Must use single-ticker downloads to avoid MultiIndex handling |

**Deprecated/outdated:**
- `kafka-python`: Unmaintained; project correctly uses `confluent-kafka` instead
- `yfinance` `auto_adjust` default changed across versions; in 0.2.38 it defaults to `True` (adjusted OHLC prices)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via requirements.txt) |
| Config file | `stock-prediction-platform/services/api/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INGEST-01 | yfinance fetch returns OHLCV DataFrame for intraday and historical modes | unit (mock yf.download) | `python -m pytest tests/test_yahoo_finance.py -x -q` | No -- Wave 0 |
| INGEST-02 | Ticker list loaded from config; overridable via TICKER_SYMBOLS env var | unit | `python -m pytest tests/test_yahoo_finance.py::test_ticker_list -x` | No -- Wave 0 |
| INGEST-03 | Valid records published to correct Kafka topics with correct key/value | unit (mock Producer) | `python -m pytest tests/test_kafka_producer.py -x -q` | No -- Wave 0 |
| INGEST-06 | Validation rejects null OHLC, null/negative volume, high < low | unit | `python -m pytest tests/test_yahoo_finance.py::test_validation -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_yahoo_finance.py` -- covers INGEST-01, INGEST-02, INGEST-06
- [ ] `tests/test_kafka_producer.py` -- covers INGEST-03
- [ ] `tests/conftest.py` -- shared fixtures (mock yf.download DataFrame, mock confluent_kafka.Producer)
- [ ] No new framework install needed -- pytest already configured

### Test Strategy Notes

**Mocking approach:** Both yfinance and confluent-kafka require external services. Tests MUST mock:
- `yfinance.download` -- return a fixture DataFrame with known OHLCV data (including edge cases: NaN values, zero volume, high < low)
- `confluent_kafka.Producer` -- mock `produce()` and `flush()` to capture messages in memory; verify topic, key, value structure
- `tenacity` retry -- optionally mock to avoid actual delays in tests; or use `tenacity.stop_after_attempt(1)` in test overrides

**Edge case fixtures:**
- Empty DataFrame (ticker not found)
- DataFrame with NaN in `Open` column
- DataFrame with negative `Volume`
- DataFrame with `High` < `Low`
- DataFrame with `Volume` = 0 (should pass validation)
- Intraday DataFrame with timezone-aware index (US/Eastern)
- Historical DataFrame with timezone-naive index

## Open Questions

1. **yfinance rate limiting behavior at 20 tickers**
   - What we know: Yahoo Finance applies rate limiting, especially for 1m intraday data
   - What's unclear: Whether 20 sequential per-ticker downloads trigger rate limits in v0.2.38
   - Recommendation: Add a small sleep (0.5-1s) between ticker downloads as a defensive measure; make it configurable

2. **confluent-kafka Producer error propagation**
   - What we know: `produce()` is async; errors surface via delivery callback or `flush()`
   - What's unclear: Whether `flush()` raises on partial delivery failure or silently drops
   - Recommendation: Always check delivery callback errors; log failed deliveries; do not treat flush timeout as success

3. **yfinance `auto_adjust` behavior in 0.2.38**
   - What we know: `auto_adjust=True` is the default in 0.2.38, meaning OHLC values are adjusted for splits/dividends
   - What's unclear: Whether adjusted values are what downstream consumers expect
   - Recommendation: Keep default `auto_adjust=True` -- adjusted prices are standard for ML pipelines

## Sources

### Primary (HIGH confidence)
- [yfinance official docs](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) -- download() API signature, parameter defaults
- [confluent-kafka Python docs](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html) -- Producer API, configuration options
- [tenacity docs](https://tenacity.readthedocs.io/) -- retry decorators, wait strategies
- [yfinance CHANGELOG.rst](https://github.com/ranaroussi/yfinance/blob/main/CHANGELOG.rst) -- multi_level_index added in v0.2.47 (not available in pinned 0.2.38)

### Secondary (MEDIUM confidence)
- [confluent-kafka json_producer.py example](https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/json_producer.py) -- JSON serialization pattern
- [yfinance GitHub repo](https://github.com/ranaroussi/yfinance) -- general usage patterns, issue tracker

### Tertiary (LOW confidence)
- Web search results on yfinance rate limiting -- anecdotal, varies by time period

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries pinned in requirements.txt; APIs verified against official docs
- Architecture: HIGH -- per-ticker download + flat JSON + flush-per-batch is well-established pattern
- Pitfalls: HIGH -- yfinance MultiIndex and timezone issues verified against changelog and docs
- Validation: HIGH -- test strategy uses standard pytest mocking patterns

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable -- all library versions are pinned)
