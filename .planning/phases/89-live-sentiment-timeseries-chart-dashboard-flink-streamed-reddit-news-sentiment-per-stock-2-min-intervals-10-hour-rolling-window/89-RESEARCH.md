# Phase 89: Live Sentiment Timeseries Chart + Promtail K8s SD Fix — Research

**Researched:** 2026-04-03
**Domain:** React/Recharts timeseries charting, PyFlink windowing, TimescaleDB/PostgreSQL timeseries persistence, Promtail Kubernetes service discovery
**Confidence:** HIGH (all findings verified against live codebase)

---

## Summary

Phase 89 has two independent deliverables that do not share code paths.

**Deliverable A — Live sentiment timeseries chart:** The Dashboard stock-detail section currently contains a `SentimentPanel` component that shows only the *latest* `avg_sentiment` scalar from the Feast Redis online store (via `/ws/sentiment/{ticker}` WebSocket). When data is unavailable it renders a static "Sentiment data unavailable — pipeline may be starting" placeholder. The requirement is to replace this with a live `LineChart` (recharts) showing `avg_sentiment` over a 10-hour rolling window sampled at 2-minute intervals. This requires: (1) a new `sentiment_timeseries` PostgreSQL/TimescaleDB hypertable persisted by a new or extended Flink sink, (2) a new REST endpoint `GET /market/sentiment/{ticker}/timeseries`, and (3) a new `SentimentTimeseriesChart` React component using recharts, replacing (or extending) `SentimentPanel`.

**Deliverable B — Promtail Kubernetes SD fix:** The existing `promtail-configmap.yaml` uses `separator: /` and only two source labels (`pod_uid` + `container_name`) to build the `__path__` glob. The real Kubernetes pod log directory layout is `{namespace}_{pod-name}_{uid}/{container}/*.log`. This means the current Promtail discovery glob never matches any actual log files, producing zero active targets. The fix is already fully specified by the existing `test_loki_alerting.py::test_promtail_path_uses_underscore_separator` test (from Phase 84, which was planned but not applied). The fix is: change source labels to `[namespace, pod_name, container]`, separator to `_`, and replacement to `/var/log/pods/*$1_$2_*/$3/*.log`.

**Primary recommendation:** Two-plan structure — Plan 01: Promtail fix (K8s YAML only, very small) + sentiment timeseries DB/API backend; Plan 02: SentimentTimeseriesChart frontend component. The Promtail fix should be Plan 01 Wave 1 (zero test to write, existing test already RED).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| recharts | ^3.8.0 | Timeseries LineChart in Dashboard | Already installed, used by HistoricalChart, DashboardTAPanel |
| @mui/material | (existing) | Layout, Typography, Skeleton, Paper | Project-wide MUI design system |
| PyFlink Table API | 1.19 | Flink windowing in sentiment_stream.py | Existing pattern, FlinkDeployment already deployed |
| TimescaleDB/PostgreSQL | (existing) | sentiment_timeseries hypertable | Existing storage namespace pattern |
| Alembic | (existing) | Migration for new table | Established migration pattern (005 is latest) |
| FastAPI | (existing) | New GET endpoint | Project-wide API framework |
| pytest | 8.3.3 | YAML + API unit tests | Project test framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg2 / asyncpg | (existing) | DB query from new API endpoint | Use same pattern as market_service.py |
| Redis cache | (existing) | Optional short TTL cache for timeseries | Use MARKET_INDICATORS_TTL pattern; 120s TTL for sentiment history |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New DB table | Feast Redis (extend online store) | Redis cannot retain 10-hour rolling window economically; DB with TimescaleDB is the right fit for timeseries history |
| recharts LineChart | recharts AreaChart | Both work; LineChart matches the design requirement (simple line, not filled area) — use AreaChart if aesthetics require it |
| New Flink JDBC sink | Kafka consumer reading sentiment-aggregated topic | Kafka consumer is simpler but adds another K8s service; Flink JDBC sink stays inside the existing FlinkDeployment |

---

## Architecture Patterns

### Recommended Project Structure
```
services/flink-jobs/sentiment_stream/
  sentiment_stream.py          # modify: change window from 5-min/1-min to 2-min/2-min
                               #         add JDBC sink to sentiment_timeseries table

services/api/app/
  routers/market.py            # add GET /market/sentiment/{ticker}/timeseries
  models/schemas.py            # add SentimentDataPoint, SentimentTimeseriesResponse
  services/market_service.py   # add get_sentiment_timeseries(ticker, hours=10)

services/api/alembic/versions/
  006_sentiment_timeseries.py  # new migration: CREATE TABLE sentiment_timeseries + hypertable

k8s/monitoring/
  promtail-configmap.yaml      # fix separator + source labels + replacement

services/frontend/src/
  components/dashboard/
    SentimentTimeseriesChart.tsx  # new: recharts LineChart for 10h rolling window
    SentimentPanel.tsx            # modify: replace unavailable placeholder with chart
    index.ts                      # export new component
  hooks/
    useSentimentTimeseries.ts     # new: REST polling hook (no WS needed for history)
```

### Pattern 1: Flink 2-minute tumbling/HOP window to JDBC PostgreSQL sink

**What:** Change the existing `sentiment_stream.py` from 1-min hop / 5-min window to 2-min tumbling (or 2-min hop / 2-min window = tumbling). Add a second sink that writes to PostgreSQL via the Flink JDBC connector using the Table API.

**Current window (to change):**
```python
# CURRENT in sentiment_stream.py (lines 219-239)
FROM TABLE(
    HOP(TABLE reddit_unnested, DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE, INTERVAL '5' MINUTE)  # 1-min hop, 5-min size
)
```

**New window (2-min tumble = HOP with equal slide and size):**
```python
# CHANGE TO: 2-min tumbling window
FROM TABLE(
    TUMBLE(TABLE reddit_unnested, DESCRIPTOR(event_time),
           INTERVAL '2' MINUTE)
)
```

**Why TUMBLE not HOP:** Tumbling window is the exact match for "2-min intervals" with no overlap. HOP windows produce overlapping windows that would write duplicate timestamps to the timeseries table. TUMBLE is cleaner for storage.

**JDBC sink pattern (Flink Table API):**
```python
# Source: Flink 1.19 JDBC connector documentation
t_env.execute_sql(f"""
    CREATE TABLE sentiment_timeseries_sink (
        ticker        STRING,
        window_start  TIMESTAMP(3),
        avg_sentiment DOUBLE,
        mention_count INT,
        positive_ratio DOUBLE,
        negative_ratio DOUBLE,
        PRIMARY KEY (ticker, window_start) NOT ENFORCED
    ) WITH (
        'connector' = 'jdbc',
        'url'       = 'jdbc:postgresql://{POSTGRES_HOST}:5432/{POSTGRES_DB}',
        'table-name' = 'sentiment_timeseries',
        'username'   = '{POSTGRES_USER}',
        'password'   = '{POSTGRES_PASSWORD}',
        'sink.buffer-flush.interval' = '0'
    )
""")
```

**Important:** The Flink JDBC connector JAR must be present in the Docker image. Check existing flink image Dockerfiles for JDBC jar presence. The `flink-config` ConfigMap already exposes `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`; `POSTGRES_PASSWORD` comes from `stock-platform-secrets` secretRef (already wired in `flinkdeployment-sentiment-stream.yaml`).

**CONFIDENCE: MEDIUM** — JDBC connector syntax is standard Flink 1.19 pattern but requires verifying that the JDBC JAR (`flink-connector-jdbc-3.2.x.jar` + `postgresql-42.x.jar`) is present in the sentiment_stream Docker image.

### Pattern 2: TimescaleDB hypertable for sentiment_timeseries

**What:** New Alembic migration `006_sentiment_timeseries.py` creates `sentiment_timeseries` table and converts it to a hypertable. The 10-hour rolling window means data older than 10 hours is not fetched by the API but can be retained longer for future use (retention policy at 7 days).

```python
# Alembic migration pattern (follows 005_timescaledb_olap.py conventions)
def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_timeseries (
            ticker         VARCHAR(10)      NOT NULL,
            window_start   TIMESTAMPTZ      NOT NULL,
            avg_sentiment  DOUBLE PRECISION,
            mention_count  INTEGER,
            positive_ratio DOUBLE PRECISION,
            negative_ratio DOUBLE PRECISION,
            PRIMARY KEY (ticker, window_start)
        )
    """)
    op.execute("""
        SELECT create_hypertable(
            'sentiment_timeseries', 'window_start',
            if_not_exists => TRUE
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sentiment_ts_ticker_time
        ON sentiment_timeseries (ticker, window_start DESC)
    """)
```

**10-hour window query:**
```sql
SELECT ticker, window_start, avg_sentiment, mention_count, positive_ratio, negative_ratio
FROM sentiment_timeseries
WHERE ticker = $1
  AND window_start >= NOW() - INTERVAL '10 hours'
ORDER BY window_start ASC
```

At 2-minute intervals, 10 hours = 300 data points maximum. This is well within safe API payload size.

### Pattern 3: FastAPI REST endpoint for sentiment timeseries

**What:** New `GET /market/sentiment/{ticker}/timeseries` endpoint following the existing `market_indicators` pattern in `market.py`.

```python
# Source: existing market.py pattern
@router.get("/sentiment/{ticker}/timeseries", response_model=SentimentTimeseriesResponse)
async def sentiment_timeseries(ticker: str, hours: int = 10) -> SentimentTimeseriesResponse:
    key = build_key("market", "sentiment-ts", ticker.upper(), str(hours))
    cached = await cache_get(key)
    if cached is not None:
        return SentimentTimeseriesResponse(**cached)
    data = await get_sentiment_timeseries(ticker=ticker, hours=hours)
    response = SentimentTimeseriesResponse(
        ticker=ticker.upper(),
        points=data,
        count=len(data),
        window_hours=hours,
    )
    await cache_set(key, response.model_dump(), 120)  # 2-min TTL matches window interval
    return response
```

**Schema:**
```python
class SentimentDataPoint(BaseModel):
    timestamp: str           # ISO8601 from window_start
    avg_sentiment: float | None
    mention_count: int | None
    positive_ratio: float | None
    negative_ratio: float | None

class SentimentTimeseriesResponse(BaseModel):
    ticker: str
    points: list[SentimentDataPoint]
    count: int
    window_hours: int
```

### Pattern 4: SentimentTimeseriesChart React component (recharts LineChart)

**What:** New component using recharts `LineChart` with `ResponsiveContainer`, following the exact pattern of `HistoricalChart.tsx`.

```typescript
// Source: existing HistoricalChart.tsx pattern + recharts 3.8 LineChart API
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

// Y-axis domain: VADER compound score range [-1, +1]
// Reference lines at -0.05 (bearish threshold) and +0.05 (bullish threshold)
// Color: green (#22c983) for positive, red (#e05454) for negative, amber for neutral
// X-axis: time labels formatted as HH:mm
// Dot: false (no dots — too many data points at 300 samples)
// strokeWidth: 2
// animate: false (reduces re-render jitter on frequent updates)
```

**useSentimentTimeseries hook:**
```typescript
// REST polling (not WebSocket) — 2-min refetch interval aligns with window emission rate
// Use existing useQuery pattern from @/api (React Query)
// Endpoint: GET /market/sentiment/{ticker}/timeseries
// Refetch interval: 120000ms (2 minutes)
// Returns: SentimentTimeseriesResponse | undefined
```

**Key design decision:** Use REST polling (React Query with `refetchInterval: 120_000`) NOT WebSocket for the timeseries. The WebSocket (`/ws/sentiment/{ticker}`) delivers only the latest scalar; history requires REST. The existing `useSentimentSocket` hook remains for the scalar display; the new `useSentimentTimeseries` hook adds history.

### Pattern 5: Promtail Kubernetes SD fix

**What:** Three changes to `promtail-configmap.yaml` — the `__path__` relabel block:

```yaml
# BEFORE (broken — only pod_uid + container, separator: /)
- source_labels:
    - __meta_kubernetes_pod_uid
    - __meta_kubernetes_pod_container_name
  separator: /
  regex: (.+)/(.+)
  target_label: __path__
  replacement: /var/log/pods/*$1/$2/*.log

# AFTER (correct — namespace + pod_name + container, separator: _)
- source_labels:
    - __meta_kubernetes_namespace
    - __meta_kubernetes_pod_name
    - __meta_kubernetes_pod_container_name
  separator: _
  regex: (.+)_(.+)_(.+)
  target_label: __path__
  replacement: /var/log/pods/*$1_$2_*/$3/*.log
```

**Why this works:** Kubernetes writes pod logs to `/var/log/pods/{namespace}_{pod-name}_{uid}/{container}/X.log`. The `_` separator joins namespace + pod-name to form the first two parts of the directory prefix; `*` wildcards the uid suffix; `$3` is the container name. The current config joins `pod_uid + container_name` with `/` which produces a path like `/var/log/pods/*abc-uid/my-container/*.log` — this never matches the real layout.

**Test verification (existing test from Phase 84):**
```bash
cd stock-prediction-platform/services/api && python -m pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -x -q
```
This test is currently RED (confirmed by running it). After the fix it must go GREEN.

### Anti-Patterns to Avoid

- **DO NOT change the existing `/ws/sentiment/{ticker}` WebSocket** — it serves the scalar display and is used by `SentimentPanel`. Keep it as-is; only add the new REST endpoint for timeseries history.
- **DO NOT use WebSocket for timeseries history** — WebSocket push is for low-latency scalars; REST polling is appropriate for 300-point history payloads.
- **DO NOT skip the Alembic migration** — the Flink JDBC sink will crash if `sentiment_timeseries` table doesn't exist. Migration must run before the FlinkDeployment upgrade.
- **DO NOT use the sentiment-aggregated Kafka topic retention as storage** — Kafka is not a timeseries database. PostgreSQL + TimescaleDB is the right layer.
- **DO NOT change the Promtail DaemonSet or RBAC** — only the ConfigMap needs updating. RBAC already grants `get/list/watch` on pods/nodes/namespaces.
- **DO NOT modify the sentiment_stream job's Feast/Kafka output** — the `sentiment-aggregated` topic and Feast Redis writes must remain unchanged because `SentimentPanel` and `sentiment_writer` depend on them.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timeseries storage | Custom ring buffer / Redis sorted set | TimescaleDB hypertable `sentiment_timeseries` | TimescaleDB handles chunking, indexing, and retention natively |
| Chart animation | CSS keyframes / canvas | recharts `<Line animate={false}>` | Already in project; `animate={false}` prevents jitter |
| Time formatting | Custom date logic | `new Date(ts).toLocaleTimeString("en-US", {hour: "2-digit", minute: "2-digit"})` | Consistent with existing chart formatters |
| Promtail path building | Custom relabel regex | Standard 3-label pattern with `separator: _` | Documented K8s log directory layout |

---

## Common Pitfalls

### Pitfall 1: Flink JDBC connector JAR not in Docker image
**What goes wrong:** `sentiment_stream` FlinkDeployment fails to restart with `ClassNotFoundException: org.apache.flink.connector.jdbc.JdbcSink` or similar.
**Why it happens:** The JDBC connector is not bundled in the base Flink image; it must be added explicitly to the Dockerfile.
**How to avoid:** Before adding the JDBC sink, verify the Dockerfile for `stock-flink-sentiment-stream:latest` includes `flink-connector-jdbc` and `postgresql` JAR. Check `services/flink-jobs/sentiment_stream/Dockerfile`. If absent, add them to the image build.
**Warning signs:** FlinkDeployment `status.jobManagerDeploymentStatus` shows `DEPLOYING` or `ERROR` after applying.

### Pitfall 2: Flink window change breaks Feast online store writes
**What goes wrong:** Changing from HOP(1-min, 5-min) to TUMBLE(2-min) changes the output frequency of `sentiment-aggregated` topic. `sentiment_writer.py` consumes this topic and pushes to Feast. If the window change is not coordinated, the SentimentPanel (scalar display) gets data 5x less frequently than before.
**Why it happens:** HOP(1-min, 5-min) emits every 1 minute (5 overlapping windows); TUMBLE(2-min) emits every 2 minutes. This is acceptable — 2-min staleness is fine for the scalar display.
**How to avoid:** Document the frequency change in the plan. Do not attempt to maintain the old cadence by keeping HOP.

### Pitfall 3: Promtail phase field pod phase filter drops all pods
**What goes wrong:** After the Promtail fix, still zero active targets because the `__meta_kubernetes_pod_phase` keep filter excludes all pods.
**Why it happens:** In Minikube, pods in `Completed` state (like CronJob pods) or pods where the phase label is empty may not match `regex: Running`.
**How to avoid:** The `action: keep / regex: Running` filter is correct — Running pods should appear. The root cause of zero targets in the current config is the wrong `__path__`, not the phase filter. After the path fix, targets should appear. If still zero, check if Minikube writes logs in a different path structure.
**Warning signs:** Promtail targets page at `:9080/targets` shows targets but all in `dropped` state (means path is right but phase filter is dropping them) vs completely empty (means SD finds nothing).

### Pitfall 4: SentimentTimeseriesChart renders empty with no graceful state
**What goes wrong:** Chart shows blank white area when `points.length === 0` (pipeline just started, no data yet).
**Why it happens:** recharts LineChart with empty `data` array renders an empty chart without any message.
**How to avoid:** Add explicit empty-state guard: if `points.length === 0`, render the existing `SentimentPanel` unavailable placeholder (reuse exact MUI Paper + Typography from current `SentimentPanel.tsx` lines 52-63).

### Pitfall 5: Wrong path for Alembic migration head
**What goes wrong:** `alembic upgrade head` during API startup fails because migration references wrong `down_revision`.
**Why it happens:** Latest revision is `005_timescaledb_olap.py`. New migration must set `down_revision = "005"` (or whatever the revision ID of 005 is).
**How to avoid:** Check the `revision` ID of `005_timescaledb_olap.py` and use it as `down_revision` in `006_sentiment_timeseries.py`.
**Warning signs:** API pod crashes on startup with `alembic.util.exc.CommandError: Can't locate revision`.

---

## Code Examples

### Recharts LineChart with VADER [-1, +1] Y-axis

```typescript
// Source: recharts 3.8 documentation + existing HistoricalChart.tsx pattern
<ResponsiveContainer width="100%" height={200}>
  <LineChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
    <XAxis
      dataKey="timestamp"
      tickFormatter={(t: string) =>
        new Date(t).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
      }
      tick={{ fill: "rgba(107,122,159,0.8)", fontSize: 10 }}
      interval="preserveStartEnd"
    />
    <YAxis
      domain={[-1, 1]}
      tick={{ fill: "rgba(107,122,159,0.8)", fontSize: 10 }}
      tickFormatter={(v: number) => v.toFixed(1)}
      width={36}
    />
    <ReferenceLine y={0.05} stroke="#22c983" strokeDasharray="4 2" strokeOpacity={0.4} />
    <ReferenceLine y={-0.05} stroke="#e05454" strokeDasharray="4 2" strokeOpacity={0.4} />
    <Tooltip
      formatter={(v: number) => [v.toFixed(3), "Sentiment"]}
      labelFormatter={(t: string) => new Date(t).toLocaleTimeString()}
      contentStyle={{ backgroundColor: "#0f1c2e", border: "1px solid rgba(124,58,237,0.3)", fontSize: 11 }}
    />
    <Line
      type="monotone"
      dataKey="avg_sentiment"
      stroke="#BF5AF2"
      strokeWidth={2}
      dot={false}
      isAnimationActive={false}
    />
  </LineChart>
</ResponsiveContainer>
```

### Promtail configmap fix (complete replacement block)

```yaml
# Source: Kubernetes documentation on pod log directory layout
# Replace the existing __path__ relabel block in promtail-configmap.yaml
- source_labels:
    - __meta_kubernetes_namespace
    - __meta_kubernetes_pod_name
    - __meta_kubernetes_pod_container_name
  separator: _
  regex: (.+)_(.+)_(.+)
  target_label: __path__
  replacement: /var/log/pods/*$1_$2_*/$3/*.log
```

### market_service.py — get_sentiment_timeseries

```python
# Source: existing get_ticker_indicators pattern in market_service.py
async def get_sentiment_timeseries(ticker: str, hours: int = 10) -> list[dict]:
    """Query sentiment_timeseries table for rolling window history."""
    async with get_db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                window_start AT TIME ZONE 'UTC' AS ts,
                avg_sentiment,
                mention_count,
                positive_ratio,
                negative_ratio
            FROM sentiment_timeseries
            WHERE ticker = $1
              AND window_start >= NOW() - ($2 * INTERVAL '1 hour')
            ORDER BY window_start ASC
            """,
            ticker.upper(),
            hours,
        )
    return [
        {
            "timestamp": row["ts"].isoformat(),
            "avg_sentiment": row["avg_sentiment"],
            "mention_count": row["mention_count"],
            "positive_ratio": row["positive_ratio"],
            "negative_ratio": row["negative_ratio"],
        }
        for row in rows
    ]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Scalar-only sentiment via WS | Add timeseries REST endpoint + LineChart | Phase 89 | Users can see sentiment trend not just current value |
| HOP(1-min, 5-min) in sentiment_stream | TUMBLE(2-min) in sentiment_stream | Phase 89 | Cleaner 2-min intervals, no overlap, matches timeseries storage key |
| Promtail uses pod_uid+container (separator /) | Promtail uses namespace+pod_name+container (separator _) | Phase 89 (Phase 84 planned but not applied) | Logs actually reach Loki — zero active targets becomes active targets |
| sentiment_timeseries stored only in Redis (online store, no history) | sentiment_timeseries in PostgreSQL TimescaleDB | Phase 89 | Enables 10h window queries |

**Deprecated/outdated:**
- Phase 84 Plan 02 claimed to fix Promtail separator but the change was NOT committed to the main codebase (the configmap still has `separator: /`). Phase 89 must apply the fix.

---

## Open Questions

1. **Flink JDBC JAR availability in sentiment_stream Docker image**
   - What we know: The `flink-connector-jdbc` JAR is required for the JDBC sink; the base PyFlink image may not include it
   - What's unclear: Whether the existing sentiment_stream Dockerfile already includes this JAR (check `services/flink-jobs/sentiment_stream/Dockerfile`)
   - Recommendation: Plan 01 task should first check the Dockerfile; if absent, add the JAR download step before writing the sink code. Alternative: write a separate Kafka consumer that reads `sentiment-aggregated` and writes to PostgreSQL (avoids Flink JDBC complexity).

2. **TUMBLE vs HOP for the Kafka output (sentiment_writer compatibility)**
   - What we know: `sentiment_writer.py` reads `sentiment-aggregated` topic which currently gets HOP window output
   - What's unclear: Whether changing to TUMBLE affects the `sentiment_writer` or `SentimentPanel` behavior
   - Recommendation: Changing to TUMBLE is safe — TUMBLE produces one row per ticker per 2 minutes (vs HOP's one row per ticker per minute). The WS `/ws/sentiment/{ticker}` sends data every 60s; with TUMBLE, Feast gets new data every 2 minutes. The 60s polling means some pushes will repeat the same value — acceptable.

3. **Whether to keep SentimentPanel scalar display alongside the new chart**
   - What we know: The requirement says "replaces static unavailable placeholder" — it replaces the placeholder, not the whole SentimentPanel
   - What's unclear: Whether the scalar gauge (LinearProgress) + new timeseries chart should coexist or if the chart replaces everything
   - Recommendation: Keep the scalar gauge (LinearProgress) from `SentimentPanel` for "current state" and add the timeseries chart below it as a new section. The planner can refine this.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.3 |
| Config file | `stock-prediction-platform/services/api/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/test_loki_alerting.py tests/test_sentiment_timeseries.py -x -q` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| Promtail __path__ uses underscore separator | unit (YAML parse) | `pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -x -q` | YES (currently RED) |
| Promtail source_labels has namespace+pod_name+container | unit (YAML parse) | `pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -x -q` | YES |
| sentiment_timeseries endpoint returns list of points | unit (FastAPI TestClient) | `pytest tests/test_sentiment_timeseries.py -x -q` | NO — Wave 0 |
| SentimentTimeseriesResponse schema has required fields | unit (pydantic) | `pytest tests/test_sentiment_timeseries.py::test_schema -x -q` | NO — Wave 0 |
| Alembic migration 006 creates sentiment_timeseries table | manual (requires DB) | manual-only | N/A |
| Flink TUMBLE window emits at 2-min intervals | manual (requires cluster) | manual-only | N/A |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator tests/test_sentiment_timeseries.py -x -q 2>/dev/null || python -m pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -x -q`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work` + Playwright visual check of SentimentPanel section in Dashboard

### Wave 0 Gaps
- [ ] `stock-prediction-platform/services/api/tests/test_sentiment_timeseries.py` — unit tests for: endpoint schema (SentimentDataPoint + SentimentTimeseriesResponse fields), `get_sentiment_timeseries` returns list[dict] with correct keys, migration 006 file exists with expected SQL fragments
- [ ] `stock-prediction-platform/services/api/alembic/versions/006_sentiment_timeseries.py` — migration creating `sentiment_timeseries` hypertable

---

## Sources

### Primary (HIGH confidence)
- Live codebase inspection — `services/flink-jobs/sentiment_stream/sentiment_stream.py` (current window config)
- Live codebase inspection — `k8s/monitoring/promtail-configmap.yaml` (current broken separator)
- Live codebase inspection — `services/frontend/src/components/dashboard/SentimentPanel.tsx` (current placeholder)
- Live codebase inspection — `services/frontend/src/components/dashboard/HistoricalChart.tsx` (recharts pattern)
- Live codebase inspection — `services/api/app/routers/market.py` (endpoint + cache pattern)
- Live codebase inspection — `services/api/tests/test_loki_alerting.py` (existing RED test)
- Test run confirmation — `test_promtail_path_uses_underscore_separator` is RED against current configmap

### Secondary (MEDIUM confidence)
- Flink 1.19 Table API JDBC connector documentation (JDBC sink syntax standard for Flink 1.19)
- Kubernetes pod log directory layout `{namespace}_{pod-name}_{uid}/{container}/*.log` — documented K8s standard

### Tertiary (LOW confidence)
- JDBC JAR availability in existing sentiment_stream Docker image — NOT verified, requires Dockerfile inspection in Plan 01

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed present in codebase
- Architecture (Promtail fix): HIGH — existing failing test exactly specifies the fix
- Architecture (sentiment timeseries DB + API): HIGH — follows established patterns
- Architecture (Flink window change + JDBC sink): MEDIUM — JDBC JAR presence unverified
- Architecture (frontend chart): HIGH — recharts LineChart is the standard project pattern
- Pitfalls: HIGH — all pitfalls derived from reading live code

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable stack)
