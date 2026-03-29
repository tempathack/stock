# Phase 64: TimescaleDB OLAP — Continuous Aggregates & Compression - Research

**Researched:** 2026-03-29
**Domain:** TimescaleDB continuous aggregates, compression policies, retention policies, FastAPI endpoint integration
**Confidence:** HIGH (primary findings verified against official TimescaleDB docs and GitHub source; critical DATE-type pitfall verified via GitHub issue tracker)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TSDB-01 | `ohlcv_daily_1h_agg` continuous aggregate materializes 1-hour OHLCV rollups from `ohlcv_intraday` (auto-refresh every 30 min) | TIMESTAMP partition on `ohlcv_intraday` fully supports continuous aggregates; FIRST()/LAST() functions provide open/close; time_bucket('1 hour', timestamp) is the standard pattern |
| TSDB-02 | `ohlcv_daily_agg` continuous aggregate materializes daily summaries from `ohlcv_daily` (auto-refresh every 1 hour) | CRITICAL: `ohlcv_daily` uses DATE partition column — continuous aggregates require TIMESTAMPTZ; Alembic migration must cast DATE to TIMESTAMPTZ or add a computed column before creating the aggregate |
| TSDB-03 | Compression policy on `ohlcv_daily`: chunks older than 7 days compressed (segmentby ticker, orderby date) | `ALTER TABLE ohlcv_daily SET (timescaledb.compress, timescaledb.compress_segmentby='ticker', timescaledb.compress_orderby='date DESC')` then `add_compression_policy` |
| TSDB-04 | Compression policy on `ohlcv_intraday`: chunks older than 3 days compressed | Same pattern; compress_after must be > start_offset of continuous aggregate refresh to prevent refresh failures on compressed chunks |
| TSDB-05 | Retention policy: `ohlcv_intraday` drops data older than 90 days; `ohlcv_daily` keeps 5 years | `add_retention_policy('ohlcv_intraday', INTERVAL '90 days')` and `add_retention_policy('ohlcv_daily', INTERVAL '5 years')`; raw table retention must be longer than continuous aggregate start_offset to prevent aggregate data loss |
| TSDB-06 | New API endpoint `GET /market/candles?ticker=AAPL&interval=1h` queries continuous aggregate and returns ≤50ms p99 | Query against `ohlcv_daily_1h_agg` view with WHERE ticker = :ticker ORDER BY bucket DESC LIMIT :n; Redis cache with 30s TTL expected to achieve p99 target; SQLAlchemy async session already in place |
</phase_requirements>

---

## Summary

Phase 64 unlocks TimescaleDB's OLAP capabilities on top of the existing hypertables (`ohlcv_daily` and `ohlcv_intraday`). The work has three layers: (1) continuous aggregates that pre-materialize OHLCV rollups into named views, (2) compression and retention policies that manage storage lifecycle automatically, and (3) a new FastAPI `GET /market/candles` endpoint that queries the aggregates and returns candle data in under 50ms.

The most significant finding is a **critical schema constraint**: `ohlcv_daily` uses a `DATE` column as its hypertable partition key. TimescaleDB continuous aggregates require a `TIMESTAMPTZ` or `TIMESTAMP` partition column — `DATE` is not supported (GitHub issue #6042, open as of 2026). An Alembic migration must either cast the DATE column to TIMESTAMPTZ or the aggregate must be defined using `time_bucket('1 day', date::timestamptz)` with an explicit cast inside the view. The continuous aggregate for intraday data (`ohlcv_daily_1h_agg` off `ohlcv_intraday`) is unaffected because `ohlcv_intraday.timestamp` is already `TIMESTAMPTZ`.

A second critical pitfall: `compress_after` intervals must be strictly greater than the `start_offset` of any refresh policy on the same table to prevent the refresh job from trying to update already-compressed chunks (which would fail).

**Primary recommendation:** Deliver all policies via a single Alembic migration (new `005_timescaledb_olap.py`), add the `/market/candles` router to the existing FastAPI app, add a schema Pydantic model, and wire Redis caching using the existing `cache.py` infrastructure.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| timescale/timescaledb (PostgreSQL image) | latest-pg15 (currently 2.22+ in production) | All continuous aggregate / compression SQL functions | Already deployed in K8s storage namespace |
| Alembic | 1.13.x (already in project) | SQL migration delivery — single `005_timescaledb_olap.py` | Already configured with env.py and versions/ directory |
| SQLAlchemy async (`sqlalchemy[asyncio]`) | 2.x (already in project) | Candles endpoint query | Already used in `market_service.py` |
| FastAPI | 0.115.x (already in project) | `GET /market/candles` endpoint | Already used for all market routes |
| redis.asyncio | 5.x (already in project) | 30s TTL cache for candle responses | Already used in `cache.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest + pytest-asyncio | already in project | Unit tests for candle service and router | Required by nyquist_validation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Alembic migration for policies | Raw SQL in init.sql | init.sql only runs on first container start — Alembic upgrade head runs on every deploy, so idempotent |
| SQLAlchemy async for candles | psycopg2 direct | Async is already the project standard; psycopg2 sync path is deprecated in this codebase |

---

## Architecture Patterns

### Recommended Project Structure

New files this phase adds to the existing tree:

```
stock-prediction-platform/
├── services/api/
│   ├── alembic/versions/
│   │   └── 005_timescaledb_olap.py          # Compression, aggregates, retention, policies
│   ├── app/
│   │   ├── routers/
│   │   │   └── market.py                    # ADD: GET /market/candles endpoint
│   │   ├── services/
│   │   │   └── market_service.py            # ADD: get_candles() async function
│   │   └── models/
│   │       └── schemas.py                   # ADD: CandleBar, CandlesResponse schemas
│   └── tests/
│       └── test_candles_router.py           # ADD: unit tests for candle endpoint
```

### Pattern 1: Continuous Aggregate for Intraday (TSDB-01)

`ohlcv_intraday` already has a `TIMESTAMPTZ` partition column — works without modification.

```sql
-- Source: TimescaleDB official docs / GitHub timescale/docs
CREATE MATERIALIZED VIEW ohlcv_daily_1h_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    ticker,
    FIRST(open, timestamp)           AS open,
    MAX(high)                        AS high,
    MIN(low)                         AS low,
    LAST(close, timestamp)           AS close,
    SUM(volume)                      AS volume,
    LAST(vwap, timestamp)            AS vwap
FROM ohlcv_intraday
GROUP BY bucket, ticker
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'ohlcv_daily_1h_agg',
    start_offset    => INTERVAL '2 hours',
    end_offset      => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists   => TRUE
);
```

`FIRST(col, time)` and `LAST(col, time)` are TimescaleDB-specific aggregate functions that return the value of `col` associated with the minimum/maximum `time` within the group. They are the canonical OHLCV pattern.

### Pattern 2: Continuous Aggregate for Daily (TSDB-02) — DATE Column Workaround

`ohlcv_daily.date` is `DATE`, not `TIMESTAMPTZ`. TimescaleDB continuous aggregates cannot operate on `DATE` partition columns directly (issue #6042, open). The workaround is to cast inside the `time_bucket` call:

```sql
-- Source: GitHub issue #6042 workaround — cast DATE to TIMESTAMPTZ inside time_bucket
CREATE MATERIALIZED VIEW ohlcv_daily_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', date::timestamptz) AS bucket,
    ticker,
    FIRST(open,      date::timestamptz)     AS open,
    MAX(high)                               AS high,
    MIN(low)                                AS low,
    LAST(close,      date::timestamptz)     AS close,
    SUM(volume)                             AS volume,
    LAST(vwap,       date::timestamptz)     AS vwap,
    LAST(adj_close,  date::timestamptz)     AS adj_close
FROM ohlcv_daily
GROUP BY bucket, ticker
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'ohlcv_daily_agg',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists   => TRUE
);
```

**NOTE:** If the cast workaround does not work in the deployed TimescaleDB version, the fallback is a regular PostgreSQL `MATERIALIZED VIEW` (non-continuous) that is manually refreshed via a K8s CronJob. This is lower value (no auto-refresh) but avoids a schema migration to change the column type. The planner should treat the cast approach as primary and the manual materialized view as fallback.

### Pattern 3: Compression Policy (TSDB-03, TSDB-04)

```sql
-- ohlcv_daily compression
ALTER TABLE ohlcv_daily SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker',
    timescaledb.compress_orderby   = 'date DESC'
);
SELECT add_compression_policy(
    'ohlcv_daily',
    after => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ohlcv_intraday compression
ALTER TABLE ohlcv_intraday SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker',
    timescaledb.compress_orderby   = 'timestamp DESC'
);
SELECT add_compression_policy(
    'ohlcv_intraday',
    after => INTERVAL '3 days',
    if_not_exists => TRUE
);
```

**Overlap rule (CRITICAL):** The `compress_after` on `ohlcv_intraday` (3 days) must be greater than the `start_offset` of `ohlcv_daily_1h_agg` policy (2 hours). This is satisfied — no conflict. Similarly, the `compress_after` on `ohlcv_daily` (7 days) must be greater than the `start_offset` of `ohlcv_daily_agg` policy (3 days). This is satisfied.

### Pattern 4: Retention Policy (TSDB-05)

```sql
-- Source: timescale/docs - add_retention_policy
SELECT add_retention_policy(
    'ohlcv_intraday',
    drop_after    => INTERVAL '90 days',
    if_not_exists => TRUE
);
SELECT add_retention_policy(
    'ohlcv_daily',
    drop_after    => INTERVAL '5 years',
    if_not_exists => TRUE
);
```

**Aggregate preservation rule (CRITICAL):** The raw table retention interval (90 days for intraday, 5 years for daily) must be longer than the continuous aggregate's `start_offset`. Since `ohlcv_daily_1h_agg` has `start_offset => '2 hours'` and raw intraday data is kept 90 days, there is no risk. However, if data is dropped from the raw table and then a refresh runs over that window, the aggregate data for that window will also be deleted. The 90-day intraday retention is safely longer than the 2-hour start_offset.

### Pattern 5: Candles API Endpoint (TSDB-06)

```python
# services/api/app/services/market_service.py — new function
async def get_candles(
    ticker: str,
    interval: str,
    limit: int = 200,
) -> list[dict] | None:
    """Query continuous aggregate for OHLCV candles."""
    view_map = {
        "1h": "ohlcv_daily_1h_agg",
        "1d": "ohlcv_daily_agg",
    }
    view = view_map.get(interval)
    if view is None or get_engine() is None:
        return None

    query = text(f"""
        SELECT
            bucket AS ts,
            ticker,
            open, high, low, close, volume, vwap
        FROM {view}
        WHERE ticker = :ticker
        ORDER BY bucket DESC
        LIMIT :limit
    """)
    # ... async session execute, return list[dict]
```

```python
# services/api/app/routers/market.py — new endpoint added to existing router
@router.get("/candles", response_model=CandlesResponse)
async def market_candles(
    ticker: str,
    interval: str = "1h",
    limit: int = 200,
) -> CandlesResponse:
    key = build_key("market", "candles", ticker.upper(), interval)
    cached = await cache_get(key)
    if cached is not None:
        return CandlesResponse(**cached)
    ...
    await cache_set(key, response.model_dump(), MARKET_CANDLES_TTL)
    return response
```

### Pattern 6: Alembic Migration Structure

All TimescaleDB DDL must be delivered in a single Alembic migration file `005_timescaledb_olap.py`. The migration uses `op.execute()` for every TimescaleDB-specific SQL statement since SQLAlchemy has no native models for hypertable policies.

```python
# alembic/versions/005_timescaledb_olap.py
def upgrade() -> None:
    # 1. Enable compression on ohlcv_daily
    op.execute("ALTER TABLE ohlcv_daily SET (...)")
    op.execute("SELECT add_compression_policy('ohlcv_daily', ...)")
    # 2. Enable compression on ohlcv_intraday
    op.execute("ALTER TABLE ohlcv_intraday SET (...)")
    op.execute("SELECT add_compression_policy('ohlcv_intraday', ...)")
    # 3. Create continuous aggregate for intraday → hourly
    op.execute("CREATE MATERIALIZED VIEW ohlcv_daily_1h_agg ...")
    op.execute("SELECT add_continuous_aggregate_policy('ohlcv_daily_1h_agg', ...)")
    # 4. Create continuous aggregate for daily → daily summary
    op.execute("CREATE MATERIALIZED VIEW ohlcv_daily_agg ...")
    op.execute("SELECT add_continuous_aggregate_policy('ohlcv_daily_agg', ...)")
    # 5. Retention policies
    op.execute("SELECT add_retention_policy('ohlcv_intraday', ...)")
    op.execute("SELECT add_retention_policy('ohlcv_daily', ...)")

def downgrade() -> None:
    op.execute("SELECT remove_retention_policy('ohlcv_daily', if_not_exists => TRUE)")
    op.execute("SELECT remove_retention_policy('ohlcv_intraday', if_not_exists => TRUE)")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_daily_agg")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_daily_1h_agg")
    op.execute("SELECT remove_compression_policy('ohlcv_intraday', if_not_exists => TRUE)")
    op.execute("SELECT remove_compression_policy('ohlcv_daily', if_not_exists => TRUE)")
    op.execute("ALTER TABLE ohlcv_intraday RESET (timescaledb.compress)")
    op.execute("ALTER TABLE ohlcv_daily RESET (timescaledb.compress)")
```

### Anti-Patterns to Avoid

- **Using `timescaledb.compress` without segmentby on a multi-ticker table:** Without `compress_segmentby='ticker'`, all tickers are merged into one segment, destroying ticker-level query performance on compressed data.
- **Setting `compress_after` less than or equal to `start_offset`:** The refresh policy will try to update already-compressed regions, failing with an error. Always ensure compress_after > start_offset.
- **Applying retention policy on the aggregate view instead of the raw table:** Retention policies target hypertables. The aggregate view is a separate hypertable internally. Applying retention to the raw table when a continuous aggregate exists will delete aggregate data if the aggregate refreshed that window after deletion.
- **Modifying the aggregate query after creation:** To change columns or time_bucket size, you must DROP and recreate the view. Schema evolution of continuous aggregates has no ALTER path.
- **ON CONFLICT upserts into compressed chunks:** The project already uses `ON CONFLICT DO UPDATE` in Kafka consumer writes. Because compression only applies to chunks older than 3/7 days and consumers write current data, there is no conflict. However, any backfill of old data (older than compress_after) would fail on conflict into compressed chunks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Time-bucketed OHLCV rollups | Python aggregation job | TimescaleDB `CREATE MATERIALIZED VIEW ... WITH (timescaledb.continuous)` | Auto-refreshes, stores on disk, skips re-computation on unchanged data |
| Column store compression | Custom archiver | `ALTER TABLE SET (timescaledb.compress)` + `add_compression_policy` | 90%+ reduction, integrated with query planner, no application changes needed |
| Data expiry | Application-level DELETE rows | `add_retention_policy` | Drops whole chunks (O(1) file removal vs O(n) row delete), no VACUUM overhead |
| OHLCV candle queries from raw data | Raw SQL on ohlcv_intraday with GROUP BY | Query `ohlcv_daily_1h_agg` view | Pre-materialized: sub-millisecond vs seconds on raw hypertable |
| Refresh scheduling | K8s CronJob calling REFRESH | `add_continuous_aggregate_policy` | Background job runs inside Postgres, handles incremental refresh and partial windows automatically |

**Key insight:** Every problem in this phase has a native TimescaleDB function. The planner should never propose application-layer alternatives to these built-in capabilities.

---

## Common Pitfalls

### Pitfall 1: DATE Column Cannot Be Used as Continuous Aggregate Time Dimension Directly

**What goes wrong:** `CREATE MATERIALIZED VIEW ohlcv_daily_agg WITH (timescaledb.continuous) AS SELECT time_bucket('1 day', date) ...` fails with "continuous aggregate view must include a valid time bucket function" because `date` is `DATE` type, not `TIMESTAMPTZ`.

**Why it happens:** TimescaleDB continuous aggregates validate that the `time_bucket` column is a timestamp type. `DATE` is not accepted as a valid time dimension for continuous aggregates (GitHub issue #6042, open as of 2026-03).

**How to avoid:** Use `date::timestamptz` in the `time_bucket` call: `time_bucket('1 day', date::timestamptz)`. Also pass `date::timestamptz` as the ordering argument to `FIRST()` and `LAST()`.

**Warning signs:** Error message containing "continuous aggregate view must include a valid time bucket function."

### Pitfall 2: Compression Invalidates Refresh Windows

**What goes wrong:** Compression policy runs before the refresh policy interval window. The refresh job tries to invalidate compressed chunks, failing silently or with an error depending on TimescaleDB version.

**Why it happens:** Compressed chunks are read-only from the perspective of aggregate invalidation tracking. If a compressed chunk falls inside the `start_offset` window of the refresh policy, the refresh job cannot process it.

**How to avoid:** Always set `compress_after > start_offset`. For `ohlcv_intraday`: `compress_after=3 days`, `start_offset=2 hours` — safe. For `ohlcv_daily`: `compress_after=7 days`, `start_offset=3 days` — safe.

**Warning signs:** Continuous aggregate refresh job fails or stops materializing new data while the background policy job shows errors in `timescaledb_information.job_errors`.

### Pitfall 3: Retention Policy Deletes Raw Data That Continuous Aggregate Relies On

**What goes wrong:** The retention policy drops chunks from the raw hypertable. On the next refresh, the continuous aggregate detects the deleted raw data and also deletes the corresponding aggregate data.

**Why it happens:** Continuous aggregate refresh is based on changes to the raw table. Deletion counts as a change, and the aggregate reflects that deletion.

**How to avoid:** Set retention intervals longer than the aggregate's `start_offset`. Since retention for intraday is 90 days and `start_offset` is 2 hours, the risk window is the final 2 hours before a chunk is dropped. In practice, the refresh runs every 30 minutes and will have already materialized data well before it reaches the retention boundary.

**Warning signs:** Historical aggregate data disappears after a retention job runs.

### Pitfall 4: ON CONFLICT Fails on Compressed Chunks During Backfill

**What goes wrong:** The Kafka consumer uses `ON CONFLICT DO UPDATE` upserts. If a backfill operation targets rows in chunks already compressed (older than compress_after), the upsert fails.

**Why it happens:** Compressed chunks are immutable by default. Conflict resolution requires modifying existing rows, which is not possible in a compressed chunk without full decompression.

**How to avoid:** Backfills of data older than `compress_after` must decompress affected chunks first, then upsert, then optionally recompress. For normal real-time writes (last few hours), there is no issue.

**Warning signs:** Kafka consumer errors during historical data ingestion, `ERROR: could not write to compressed chunk` or similar.

### Pitfall 5: Migration Must Not Drop and Recreate Existing Hypertables

**What goes wrong:** A migration that drops and recreates `ohlcv_daily` or `ohlcv_intraday` to change the partition column type would lose all production data.

**Why it happens:** The DATE-to-TIMESTAMPTZ concern might prompt a schema refactor. That is not needed — the cast workaround inside the aggregate view definition handles it without touching the base table.

**How to avoid:** The Alembic migration uses `ALTER TABLE SET (timescaledb.compress...)` and `CREATE MATERIALIZED VIEW` only. No DROP TABLE or structural changes to existing hypertables.

---

## Code Examples

Verified patterns from official TimescaleDB docs and community sources:

### OHLCV Continuous Aggregate (Intraday → Hourly)

```sql
-- Source: TimescaleDB financial tick data tutorial, timescale/docs GitHub
CREATE MATERIALIZED VIEW ohlcv_daily_1h_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    ticker,
    FIRST(open,  timestamp)          AS open,
    MAX(high)                        AS high,
    MIN(low)                         AS low,
    LAST(close,  timestamp)          AS close,
    SUM(volume)                      AS volume,
    LAST(vwap,   timestamp)          AS vwap
FROM ohlcv_intraday
GROUP BY bucket, ticker
WITH NO DATA;
```

### Refresh Policy

```sql
-- Source: add_continuous_aggregate_policy() API docs, timescale/docs GitHub
SELECT add_continuous_aggregate_policy(
    'ohlcv_daily_1h_agg',
    start_offset      => INTERVAL '2 hours',
    end_offset        => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists     => TRUE
);
```

### Compression Enable + Policy

```sql
-- Source: deepwiki.com/timescale/timescaledb/3.1-compression-configuration-and-policies
ALTER TABLE ohlcv_intraday SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker',
    timescaledb.compress_orderby   = 'timestamp DESC'
);
SELECT add_compression_policy(
    'ohlcv_intraday',
    after         => INTERVAL '3 days',
    if_not_exists => TRUE
);
```

### Retention Policy

```sql
-- Source: timescale/docs - create-a-retention-policy
SELECT add_retention_policy(
    'ohlcv_intraday',
    drop_after    => INTERVAL '90 days',
    if_not_exists => TRUE
);
```

### Query Continuous Aggregate

```sql
-- Source: TimescaleDB tutorial pattern for candle queries
SELECT bucket AS ts, ticker, open, high, low, close, volume, vwap
FROM ohlcv_daily_1h_agg
WHERE ticker = 'AAPL'
ORDER BY bucket DESC
LIMIT 200;
```

### Verify Policies in Effect

```sql
-- Source: timescaledb_information views (standard TimescaleDB system catalog)
SELECT * FROM timescaledb_information.continuous_aggregates;
SELECT * FROM timescaledb_information.jobs WHERE proc_name IN (
    'policy_refresh_continuous_aggregate',
    'policy_compression',
    'policy_retention'
);
SELECT * FROM timescaledb_information.compression_settings;
```

### CandleBar Pydantic Schema

```python
# services/api/app/models/schemas.py — additions
class CandleBar(BaseModel):
    ts: str            # ISO-8601 timestamp of the bucket
    ticker: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    vwap: float | None = None

class CandlesResponse(BaseModel):
    ticker: str
    interval: str
    candles: list[CandleBar]
    count: int
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regular PostgreSQL `MATERIALIZED VIEW` with manual `REFRESH` | `CREATE MATERIALIZED VIEW WITH (timescaledb.continuous)` + policy | TimescaleDB 1.7+ (2019) | Incremental refresh — only updated data re-materialized |
| Manually dropping old rows with `DELETE WHERE date < now() - interval` | `add_retention_policy` | TimescaleDB 1.7+ | O(1) chunk drop vs O(n) row delete; no VACUUM bloat |
| No native compression — rely on pg_partman + pg_compress | `timescaledb.compress` with background policy | TimescaleDB 2.0+ | 90%+ storage reduction with no application-layer changes |
| Non-finalized aggregates (partial state, can use `combine`) | Finalized aggregates (default since TimescaleDB 2.7) | 2022 | More aggregate functions supported; `timescaledb.finalized=true` is the default |
| `timescaledb.materialized_only=false` always includes real-time tail | Tunable per aggregate (default false in 2.12, true in 2.13+) | 2.13 (2023) | Real-time aggregation disabled by default — tail data not included unless opt-in |

**Deprecated/outdated:**
- `refresh_continuous_aggregate(view, start, end)` manual call: Still valid for one-off backfills, but `add_continuous_aggregate_policy` is the operational approach.
- Non-finalized aggregates (`timescaledb.finalized=false`): Deprecated — use default finalized mode.

---

## Open Questions

1. **DATE cast workaround stability across TimescaleDB versions**
   - What we know: `date::timestamptz` inside `time_bucket` is the community-documented workaround for issue #6042; the image is `latest-pg15` (likely TimescaleDB 2.22+)
   - What's unclear: Whether the cast workaround was officially fixed/accepted in 2.22 or remains a workaround
   - Recommendation: Attempt the cast workaround first in the migration; if it fails in the deployed version, fall back to a standard PostgreSQL `MATERIALIZED VIEW` with a manual refresh CronJob. The planner should include a fallback plan note.

2. **`timescaledb.materialized_only` default behavior**
   - What we know: Since TimescaleDB 2.13, real-time aggregation is disabled by default (materialized_only=true is the default)
   - What's unclear: The deployed image version — if it is pre-2.13, newly inserted intraday data will automatically appear in the aggregate without a refresh; if 2.13+, it will not appear until the refresh runs
   - Recommendation: Always set `timescaledb.materialized_only=false` explicitly in the CREATE VIEW to ensure real-time tail data is included regardless of TimescaleDB version

3. **ON CONFLICT compatibility with compressed chunks in project's Kafka consumer**
   - What we know: The Kafka consumer uses ON CONFLICT DO UPDATE; compressed chunks reject upserts; compress_after is set to 3+ days so normal writes are unaffected
   - What's unclear: Whether any historical backfill paths exist that could write into compressed time ranges
   - Recommendation: Document the limitation in a code comment in the migration; no action needed for normal operation

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (pytest.ini at `services/api/pytest.ini`) |
| Config file | `services/api/pytest.ini` (`testpaths = tests`, `-p no:logfire`) |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/test_candles_router.py -x` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TSDB-01 | `ohlcv_daily_1h_agg` view query returns OHLCV rows per ticker | unit (mock DB) | `pytest tests/test_candles_router.py::test_candles_1h -x` | Wave 0 |
| TSDB-02 | `ohlcv_daily_agg` view query returns daily rows per ticker | unit (mock DB) | `pytest tests/test_candles_router.py::test_candles_daily -x` | Wave 0 |
| TSDB-03 | compression policy config visible in timescaledb_information | manual-only (requires live DB) | Manual: `SELECT * FROM timescaledb_information.compression_settings` | N/A |
| TSDB-04 | intraday compression policy config visible | manual-only (requires live DB) | Manual: verify `show_chunks()` returns compressed chunks after 3 days | N/A |
| TSDB-05 | Retention policy registered for both tables | manual-only (requires live DB) | Manual: `SELECT * FROM timescaledb_information.jobs WHERE proc_name='policy_retention'` | N/A |
| TSDB-06 | GET /market/candles?ticker=AAPL&interval=1h returns 200 with candles list | unit (mock DB) | `pytest tests/test_candles_router.py::test_candles_endpoint_200 -x` | Wave 0 |
| TSDB-06 | GET /market/candles with unsupported interval returns 400 | unit | `pytest tests/test_candles_router.py::test_candles_bad_interval -x` | Wave 0 |
| TSDB-06 | GET /market/candles returns cached response on second call | unit (mock Redis) | `pytest tests/test_candles_router.py::test_candles_cache_hit -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_candles_router.py -x`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `stock-prediction-platform/services/api/tests/test_candles_router.py` — covers TSDB-01, TSDB-02, TSDB-06 (unit tests with mocked DB/Redis)

*(Migration correctness for TSDB-03, TSDB-04, TSDB-05 is verified manually against live DB since it requires running TimescaleDB background jobs)*

---

## Sources

### Primary (HIGH confidence)
- `timescale/docs` GitHub raw markdown — `add_continuous_aggregate_policy.md` — complete function signature with all parameters
- `deepwiki.com/timescale/timescaledb/3.1-compression-configuration-and-policies` — verified ALTER TABLE compression syntax and policy setup
- `timescale/docs` GitHub — `data-retention-with-continuous-aggregates.md` — retention + aggregate ordering critical rule

### Secondary (MEDIUM confidence)
- `oneuptime.com/blog/post/2026-01-27-timescaledb-continuous-aggregates` — refresh policy example with financial data patterns; confirmed against primary source
- `oneuptime.com/blog/post/2026-02-02-timescaledb-compression` — compression segmentby/orderby examples; confirmed against deepwiki primary
- `tradermade.com/tutorials` — OHLCV candlestick continuous aggregate FIRST()/LAST() pattern
- TimescaleDB GitHub releases page — confirms 2.22+ is the current release for latest-pg15

### Tertiary (LOW confidence)
- `github.com/timescale/timescaledb/issues/6042` — DATE column type limitation in continuous aggregates; confirmed as OPEN issue; workaround `::timestamptz` cast is community-documented but not officially endorsed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already deployed in project; no new dependencies needed
- Continuous aggregate syntax: HIGH — verified against official GitHub docs markdown
- DATE column workaround: MEDIUM — GitHub issue + community workaround; not officially closed/fixed
- Compression/retention syntax: HIGH — verified against deepwiki source derived from timescaledb codebase
- Policy interaction rules (compress_after > start_offset): HIGH — multiple sources agree
- p99 latency claim for aggregate queries: MEDIUM — aggregate queries are pre-materialized and indexed; Redis cache adds ~1ms; 50ms p99 is consistent with TimescaleDB literature but not benchmarked against this specific schema

**Research date:** 2026-03-29
**Valid until:** 2026-06-01 (TimescaleDB 2.x API is stable; continuous aggregate DDL rarely changes between patch versions)
