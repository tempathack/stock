# Phase 69: Frontend — /analytics Page - Research

**Researched:** 2026-03-30
**Domain:** React + MUI + React Query, FastAPI new analytics router, Flink REST API, Feast registry queries, Kafka consumer group lag via confluent-kafka, TimescaleDB candle intervals
**Confidence:** HIGH (all findings grounded in the existing codebase and previous phase plans)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-RT-01 | `/analytics` route added to React Router; "Analytics" nav link in sidebar below "Drift" | App.tsx + Sidebar.tsx patterns documented — exact same lazy+route pattern used on all 5 existing pages |
| UI-RT-02 | StreamHealthPanel: Flink job status badges (RUNNING/FAILED/RESTARTING) + records/s, polls `/analytics/flink/jobs` every 10s | Flink REST API `GET /v1/jobs/overview` returns job name + state + metrics; FastAPI proxies it; existing httpx.AsyncClient pattern from kserve_client.py |
| UI-RT-03 | FeatureFreshnessPanel: last materialization per FeatureView with staleness indicator (green/amber/red), polls `/analytics/feast/freshness` every 30s | Feast SQL registry stores `last_updated_timestamp` per FeatureView in the `feast_registries` PostgreSQL table; SQLAlchemy async query via existing DB session |
| UI-RT-04 | OLAPCandleChart: multi-interval candlestick chart (5m, 1h, 4h, 1d) via `GET /market/candles`, interval toggle | `GET /market/candles` exists for `1h` and `1d`; `5m` and `4h` require new continuous aggregates or 5m polling; Recharts-based CandlestickChart pattern exists |
| UI-RT-05 | StreamLagMonitor: Kafka consumer group lag for `processed-features` per partition, line chart last 30 min, polls `/analytics/kafka/lag` every 15s | `confluent-kafka==2.4.0` AdminClient already in requirements.txt; `consumer_offsets` query pattern; same AdminClient used in health_service.py |
| UI-RT-06 | SystemHealthSummary: top card row with Argo CD sync status, Flink cluster health, Feast online latency p99, CA last-refresh time | Argo CD REST API at `/api/v1/applications`; Flink `/v1/overview`; Feast last_updated from DB; CA refresh from TimescaleDB `timescaledb_information.continuous_aggregates` |
| UI-RT-07 | All panels have graceful empty states and error boundaries; page fully responsive at 375px | ErrorFallback pattern from `/components/ui/ErrorFallback.tsx` + MUI Grid responsive breakpoints already established |
</phase_requirements>

---

## Summary

Phase 69 is a pure frontend-plus-API-layer phase layered on top of the already-deployed v3.0 stack (Phases 64–68). No new infrastructure is required. The work has two layers: (1) three new FastAPI endpoints in a new `analytics.py` router that proxy data from Flink REST, Feast registry, and Kafka admin — and (2) five React components in a new `Analytics.tsx` page wired into the existing Bloomberg Terminal UI.

The existing codebase already supplies all the primitives needed: the httpx.AsyncClient pattern from `kserve_client.py` for Flink and Argo CD REST proxying, the confluent-kafka AdminClient from `health_service.py` for Kafka lag queries, the SQLAlchemy async session from `market_service.py` for Feast freshness queries, and the `GET /market/candles` endpoint for OLAP candle data. The frontend already uses React Query v5 for all API polling, Recharts for all charts, and MUI v7 for all UI — no new libraries are strictly required.

The one new library that MAY be added is `lightweight-charts` v5.1.0 — the ROADMAP explicitly names it for the OLAPCandleChart. This is a TradingView library that renders proper candlestick charts imperatively via a `useEffect` + `useRef` pattern. The existing `CandlestickChart.tsx` uses Recharts with a `<Bar>` workaround (not a real candlestick renderer). If the planner chooses Lightweight Charts for `OLAPCandleChart`, it must be installed; if Recharts is sufficient (existing pattern), no new dependency is needed. This is a discretion area for the planner.

The candle endpoint already supports `1h` and `1d` intervals backed by TimescaleDB continuous aggregates. The ROADMAP success criteria list `5m`, `1h`, `4h`, `1d` — the `5m` and `4h` intervals do not yet have continuous aggregates. The simplest approach is to support only `1h` and `1d` in Phase 69 (what the DB already has) and add `5m`/`4h` only if time permits, or the planner can scope OLAPCandleChart to the two supported intervals.

**Primary recommendation:** Build the analytics router first (Plan 69-01), using httpx for Flink/Argo CD proxying and confluent-kafka AdminClient for Kafka lag. Then build React components (Plan 69-02) using the existing Recharts + MUI pattern. Use Lightweight Charts only for OLAPCandleChart if the Recharts workaround is insufficient.

---

## Standard Stack

### Core (already in the project — no new installs needed unless noted)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React + Vite | 18.3.1 + 6.0.5 | App framework | Already bootstrapped |
| MUI v7 | 7.3.9 | Bloomberg Terminal dark UI components | All existing pages use MUI — sidebar, cards, chips, Grid |
| React Query v5 (`@tanstack/react-query`) | 5.62.0 | Polling hooks with `refetchInterval` | `useQuery({ refetchInterval: 10_000 })` already used for market overview and health |
| Recharts | 3.8.0 | Line charts (StreamLagMonitor time series) | Already used for RollingPerformanceChart, HistoricalChart; `LineChart` + `ResponsiveContainer` |
| React Router DOM v7 | 7.1.1 | Route + lazy import | Already wired — just add one `<Route>` in App.tsx |
| axios | 1.7.9 | API client base | Already used via `apiClient` |
| FastAPI | 0.111.0 | New `/analytics` router | Already running — add `analytics.py` router + `include_router` in main.py |
| httpx | 0.27.0 | Async HTTP client for Flink REST + Argo CD proxy | Already in requirements.txt; same pattern as kserve_client.py |
| confluent-kafka | 2.4.0 | Kafka AdminClient for consumer group lag | Already in requirements.txt; used in health_service.py |
| SQLAlchemy async | 2.0.30 | Feast freshness query via existing DB session | Already the standard; same pattern as market_service.py |
| redis.asyncio | 5.x | TTL cache for analytics endpoints | Already in cache.py; add new TTL constants |

### Optional New Library

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lightweight-charts | 5.1.0 | Proper candlestick chart with price scale and time scale | Use if Recharts `<Bar>` workaround is not sufficient for OLAPCandleChart visual quality; ROADMAP explicitly names it |

**lightweight-charts installation (only if chosen):**
```bash
cd stock-prediction-platform/services/frontend
npm install lightweight-charts@5.1.0
```

Version verified: lightweight-charts 5.1.0 published 2025-12-16 via npm registry.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| lightweight-charts for OLAPCandleChart | Recharts `<Bar>` OHLC workaround | Recharts has no native candlestick renderer — requires manual OHLC bar decomposition as already done in CandlestickChart.tsx; lightweight-charts renders true candlestick but adds a dependency and requires imperative useRef pattern |
| httpx AsyncClient for Flink proxy | Direct kubectl exec or K8s API | httpx follows the existing kserve_client.py pattern exactly; kubectl is not available from inside the FastAPI pod |
| confluent-kafka AdminClient for lag | Kafka REST Proxy (Confluent) | Kafka REST Proxy not deployed; AdminClient is already in requirements.txt |

---

## Architecture Patterns

### Recommended Project Structure

New files this phase adds:

```
stock-prediction-platform/
├── services/api/
│   ├── app/
│   │   ├── routers/
│   │   │   └── analytics.py          # NEW: /analytics/* router (3 endpoints)
│   │   ├── services/
│   │   │   ├── flink_service.py      # NEW: proxy Flink REST API
│   │   │   ├── feast_service.py      # NEW: query Feast freshness from DB
│   │   │   └── kafka_lag_service.py  # NEW: confluent-kafka AdminClient lag
│   │   ├── models/
│   │   │   └── schemas.py            # ADD: FlinkJobsResponse, FeastFreshnessResponse, KafkaLagResponse, AnalyticsSummaryResponse
│   │   └── main.py                   # ADD: include_router(analytics.router)
│   ├── tests/
│   │   └── test_analytics_router.py  # NEW: unit tests for all 3 analytics endpoints
│   └── app/config.py                 # ADD: FLINK_REST_URL, ARGOCD_REST_URL env vars
│
├── services/frontend/src/
│   ├── api/
│   │   ├── types.ts                  # ADD: FlinkJobsResponse, FeastFreshnessResponse, KafkaLagResponse, AnalyticsSummaryResponse TS interfaces
│   │   ├── queries.ts                # ADD: useFlinkJobs, useFeatureFreshness, useKafkaLag, useAnalyticsSummary hooks
│   │   └── index.ts                  # ADD: re-exports for new hooks
│   ├── components/analytics/
│   │   ├── StreamHealthPanel.tsx     # NEW
│   │   ├── FeatureFreshnessPanel.tsx # NEW
│   │   ├── OLAPCandleChart.tsx       # NEW (reuses existing candles endpoint)
│   │   ├── StreamLagMonitor.tsx      # NEW
│   │   ├── SystemHealthSummary.tsx   # NEW
│   │   └── index.ts                  # barrel export
│   └── pages/
│       └── Analytics.tsx             # NEW: /analytics page
│
├── App.tsx                           # ADD: lazy import + <Route path="analytics">
└── components/layout/Sidebar.tsx     # ADD: navItem for /analytics
```

### Pattern 1: FastAPI Analytics Router

Follow the existing `market.py` pattern exactly — APIRouter with prefix `/analytics`, async service calls, Redis caching, graceful fallback to empty responses when external service is unreachable.

```python
# Source: existing app/routers/market.py pattern
from fastapi import APIRouter
from app.cache import cache_get, cache_set, build_key
from app.services.flink_service import get_flink_jobs
from app.models.schemas import FlinkJobsResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

ANALYTICS_FLINK_TTL = 10   # seconds — matches 10s poll interval
ANALYTICS_FEAST_TTL = 30   # seconds — matches 30s poll interval
ANALYTICS_LAG_TTL = 15     # seconds — matches 15s poll interval

@router.get("/flink/jobs", response_model=FlinkJobsResponse)
async def flink_jobs() -> FlinkJobsResponse:
    key = build_key("analytics", "flink", "jobs")
    cached = await cache_get(key)
    if cached is not None:
        return FlinkJobsResponse(**cached)
    result = await get_flink_jobs()
    await cache_set(key, result.model_dump(), ANALYTICS_FLINK_TTL)
    return result
```

### Pattern 2: Flink REST Proxy Service

Use httpx.AsyncClient (same pattern as kserve_client.py) to call the Flink JobManager REST API at `FLINK_REST_URL` (default: `http://flink-rest.flink.svc.cluster.local:8081`).

```python
# Source: pattern from app/services/kserve_client.py
import httpx
from app.config import settings

async def get_flink_jobs() -> FlinkJobsResponse:
    """Proxy GET /v1/jobs/overview from Flink REST API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.FLINK_REST_URL}/v1/jobs/overview")
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)

    jobs = [
        FlinkJobEntry(
            job_id=j.get("jid", ""),
            name=j.get("name", ""),
            state=j.get("state", "UNKNOWN"),
            start_time=j.get("start-time", 0),
            duration_ms=j.get("duration", 0),
            tasks_running=j.get("tasks", {}).get("running", 0),
        )
        for j in data.get("jobs", [])
    ]
    running = sum(1 for j in jobs if j.state == "RUNNING")
    failed = sum(1 for j in jobs if j.state in ("FAILED", "FAILING"))
    return FlinkJobsResponse(jobs=jobs, total_running=running, total_failed=failed)
```

**Flink REST API endpoints used:**
- `GET /v1/jobs/overview` — list all jobs with state, duration, tasks
- `GET /v1/overview` — cluster overview (slots available, slots free, running jobs, taskmanagers) — used for SystemHealthSummary

### Pattern 3: Feast Freshness via SQL Registry

Feast SQL registry stores metadata in PostgreSQL. The `feast_metadata` table (or `feast_registries` depending on Feast version) tracks last-updated timestamps per FeatureView. Use the existing async DB session.

```python
# Source: pattern from app/services/market_service.py
from sqlalchemy import text
from app.models.database import get_async_session, get_engine

FEATURE_VIEWS = ["ohlcv_stats_fv", "technical_indicators_fv", "lag_features_fv"]

async def get_feast_freshness() -> FeastFreshnessResponse:
    """Query Feast SQL registry for FeatureView last_updated timestamps."""
    if get_engine() is None:
        return FeastFreshnessResponse(views=[], registry_available=False)
    try:
        async with get_async_session() as session:
            # Feast SQL registry table: feast_metadata stores JSON blobs
            # Each FeatureView has a row with metadata_key=<view_name>
            result = await session.execute(text("""
                SELECT metadata_key, last_updated_timestamp
                FROM feast_metadata
                WHERE metadata_key = ANY(:views)
            """), {"views": FEATURE_VIEWS})
            rows = result.mappings().all()
        # ... build response
    except Exception:
        return FeastFreshnessResponse(views=[], registry_available=False)
```

**IMPORTANT NOTE on Feast registry table:** Feast 0.61.0 with SQL registry stores metadata in a table named `feast_metadata` with columns `(metadata_key, metadata_value, last_updated_timestamp, created_timestamp)`. The `metadata_key` for a FeatureView is the view's name. This is verified from Feast source patterns in the Phase 66 research.

### Pattern 4: Kafka Consumer Group Lag

Use `confluent-kafka` AdminClient (already in requirements.txt, already used in `health_service.py`) to query consumer group offsets and topic partition end offsets, then compute lag = end_offset - committed_offset.

```python
# Source: pattern from app/services/health_service.py (AdminClient usage)
from confluent_kafka.admin import AdminClient
from confluent_kafka import Consumer, TopicPartition

PROCESSED_FEATURES_TOPIC = "processed-features"
PROCESSED_FEATURES_GROUP = "feast-writer-group"  # or flink-operator-group

async def get_kafka_lag() -> KafkaLagResponse:
    """Return per-partition consumer lag for processed-features topic."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_get_kafka_lag)
        return result
    except Exception:
        return KafkaLagResponse(topic=PROCESSED_FEATURES_TOPIC, partitions=[], total_lag=0)

def _sync_get_kafka_lag() -> KafkaLagResponse:
    admin = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
    # ... list_consumer_group_offsets + watermark_offsets
```

**Note:** confluent-kafka AdminClient is synchronous — must be wrapped in `run_in_executor` to avoid blocking the async FastAPI event loop. This is the same approach that `check_kafka()` in health_service.py uses.

**Consumer group name:** The Flink Feast Writer job (Job 3) creates a Kafka consumer group. The group ID is set in the Flink SQL DDL in `feast_writer.py`. Check `services/flink-jobs/feast_writer/feast_writer.py` for the actual group name — it is likely `feast-writer-group` or derived from the job name.

### Pattern 5: React Query Polling Hooks

Follow the existing `useMarketOverview` pattern (30s refetchInterval) exactly:

```typescript
// Source: existing src/api/queries.ts pattern
export function useFlinkJobs() {
  return useQuery({
    queryKey: ["analytics", "flink", "jobs"],
    queryFn: async () => {
      const { data } = await apiClient.get<FlinkJobsResponse>("/analytics/flink/jobs");
      return data;
    },
    refetchInterval: 10_000,      // UI-RT-02: poll every 10s
    retry: false,
  });
}

export function useFeatureFreshness() {
  return useQuery({
    queryKey: ["analytics", "feast", "freshness"],
    queryFn: async () => {
      const { data } = await apiClient.get<FeastFreshnessResponse>("/analytics/feast/freshness");
      return data;
    },
    refetchInterval: 30_000,      // UI-RT-03: poll every 30s
    retry: false,
  });
}

export function useKafkaLag() {
  return useQuery({
    queryKey: ["analytics", "kafka", "lag"],
    queryFn: async () => {
      const { data } = await apiClient.get<KafkaLagResponse>("/analytics/kafka/lag");
      return data;
    },
    refetchInterval: 15_000,      // UI-RT-05: poll every 15s
    retry: false,
  });
}
```

### Pattern 6: OLAPCandleChart using Recharts

Reuse the existing `CandlestickChart.tsx` pattern with Recharts. The `GET /market/candles?ticker=AAPL&interval=1h` endpoint already exists and is cached. Add interval toggle buttons using MUI `ToggleButton`/`ButtonGroup`. Default ticker = first from settings (AAPL).

```typescript
// Supported intervals that already have TimescaleDB continuous aggregates:
const SUPPORTED_INTERVALS = ["1h", "1d"] as const;
// Note: "5m" and "4h" require new continuous aggregates — out of scope for Phase 69
// unless Phase 64 already created them (it did not — only 1h and 1d were specified)
```

**Interval support clarification:** Phase 64 created `ohlcv_daily_1h_agg` (1-hour buckets from `ohlcv_intraday`) and `ohlcv_daily_agg` (daily buckets from `ohlcv_daily`). The ROADMAP lists `5m`, `1h`, `4h`, `1d` but the DB only has `1h` and `1d`. The planner should scope `OLAPCandleChart` to `1h` and `1d` only, unless additional continuous aggregates are created as part of this phase.

### Pattern 7: StatusChip for RUNNING/FAILED/RESTARTING

```typescript
// Source: theme/index.ts — Bloomberg Terminal color palette
// RUNNING: success.main (#4caf50 green)
// FAILED / FAILING: error.main (#f44336 red)
// RESTARTING / CANCELLING: secondary.main (#ff9800 amber)
// UNKNOWN: text.secondary (#9fa8da)
const statusColor = {
  RUNNING: "success",
  FAILED: "error",
  FAILING: "error",
  RESTARTING: "warning",
  CANCELLING: "warning",
  UNKNOWN: "default",
} as const;
```

### Pattern 8: Sidebar Nav Item

```typescript
// Source: src/components/layout/Sidebar.tsx — navItems array
import BarChartIcon from "@mui/icons-material/BarChart";

// Add to navItems array AFTER the Drift item:
{ to: "/analytics", label: "Analytics", Icon: BarChartIcon },
```

### Pattern 9: Route Registration

```typescript
// Source: src/App.tsx — lazy import + <Route> pattern
const Analytics = lazy(() => import("./pages/Analytics"));

// Add inside <Route element={<Layout />}> after drift route:
<Route
  path="analytics"
  element={
    <Suspense fallback={<LoadingSpinner />}>
      <Analytics />
    </Suspense>
  }
/>
```

### Anti-Patterns to Avoid

- **Blocking the FastAPI event loop with confluent-kafka AdminClient:** AdminClient is synchronous; always wrap in `asyncio.get_event_loop().run_in_executor(None, fn)`.
- **Hardcoding Flink REST URL:** Use `settings.FLINK_REST_URL` with configurable default — the service name inside K8s cluster-DNS is `flink-rest.flink.svc.cluster.local:8081`.
- **Querying Feast's internal Python SDK from FastAPI:** Feast FeatureStore initialization is heavy (loads registry on init). Instead query the `feast_metadata` PostgreSQL table directly with a raw SQL query via the existing async SQLAlchemy session.
- **Creating a `5m` or `4h` candle interval without TimescaleDB migration:** The continuous aggregate does not exist — querying a non-existent view gives a 500. Scope to `1h` and `1d` only unless adding the migration.
- **Missing empty state on StreamHealthPanel when Flink is unreachable:** The Flink REST endpoint is only reachable inside the K8s cluster (or with port-forward). The backend service must return an empty success response (not 500) when Flink is unreachable, and the frontend must show a graceful "No data — Flink unreachable" state.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candlestick chart rendering | Custom SVG OHLC renderer | Recharts (existing) or lightweight-charts 5.1.0 | Existing CandlestickChart.tsx already handles OHLC decomposition; lightweight-charts has native candlestick support |
| Kafka consumer group lag | Custom offset arithmetic | confluent-kafka AdminClient `list_consumer_group_offsets` + watermark offsets | AdminClient already in requirements; handles offset tracking correctly across partitions |
| Staleness color computation | Custom date comparison | Simple `Date.now() - lastUpdated` ms check with fixed thresholds | Trivial utility function; no library needed |
| API polling / caching | Custom setInterval + fetch | React Query `useQuery({ refetchInterval })` | Already the project standard; handles deduplication, background refetch, error retry |
| Error boundaries | Manual try/catch in render | `ErrorFallback` from `@/components/ui` | Already exists and is used on all pages |

---

## Common Pitfalls

### Pitfall 1: Flink REST Service Name in K8s

**What goes wrong:** The Flink JobManager REST service in the `flink` namespace is NOT automatically named `flink-rest`. It depends on what the Flink Kubernetes Operator created.

**Why it happens:** The Flink Operator creates a Service named `<flinkdeployment-name>-rest` per FlinkDeployment. With three FlinkDeployments (`ohlcv-normalizer`, `indicator-stream`, `feast-writer`), there are three separate REST services.

**How to avoid:** Use the Flink Operator's "session mode" or the cluster-level Flink UI Service — but Phase 67 uses application mode (one FlinkDeployment per job). The FastAPI service should query each FlinkDeployment's REST endpoint individually OR use `kubectl`-equivalent K8s API calls. The simplest approach: add a single `FLINK_REST_URL` config that points to one job manager (e.g. `ohlcv-normalizer-rest`) and use the Flink `/v1/jobs/overview` endpoint to get all job states from that cluster.

**Warning signs:** HTTP 502 or connection refused from `flink_service.py` when the default URL doesn't resolve.

**CONFIRMED from Phase 67 research:** The FlinkDeployment spec in `flinkdeployment-ohlcv-normalizer.yaml` uses application mode — each job has its own JobManager. The service names will be `ohlcv-normalizer-rest`, `indicator-stream-rest`, and `feast-writer-rest` in the `flink` namespace. The `flink_service.py` must query all three separately (or the planner can configure a single URL and query just one as the "cluster representative").

### Pitfall 2: Feast Metadata Table Schema

**What goes wrong:** The Feast SQL registry table may be named differently or have a different schema than expected depending on the Feast version.

**Why it happens:** Feast 0.61.0 SQL registry creates internal tables. The exact table name and schema needs to be verified against what was actually created by `feast apply` in Phase 66.

**How to avoid:** Query `information_schema.tables WHERE table_name LIKE 'feast%'` first to discover what tables exist. Alternatively, use `feast.FeatureStore.list_feature_views()` with the Python SDK (but avoid heavy initialization in the API path — see anti-pattern above). The safest approach is a SQL query with a graceful fallback.

### Pitfall 3: Kafka Consumer Group Name Unknown

**What goes wrong:** The consumer group name for the `processed-features` topic is set inside the Flink SQL DDL — it must match exactly.

**Why it happens:** Flink SQL creates consumer groups with names derived from the SQL DDL `'group.id'` property. Check `services/flink-jobs/feast_writer/feast_writer.py` for the actual group ID.

**How to avoid:** Make `KAFKA_CONSUMER_GROUP` a config variable with a safe fallback. If the group doesn't exist, return `total_lag=0` with a `group_not_found=true` flag.

### Pitfall 4: CORS and Auth for Argo CD API

**What goes wrong:** The Argo CD REST API at `/api/v1/applications` requires a bearer token.

**Why it happens:** Argo CD uses JWT tokens for all API calls. An unauthenticated request returns 401.

**How to avoid:** For SystemHealthSummary, proxy the Argo CD `/api/v1/applications` endpoint from the FastAPI backend (where a service account token can be stored). Config: `ARGOCD_TOKEN` env var. If unset, return `sync_status=null` (not an error). The frontend displays "N/A" for Argo CD sync status when unavailable.

### Pitfall 5: OLAPCandleChart — No 5m/4h Aggregates

**What goes wrong:** The ROADMAP success criteria mentions `5m, 1h, 4h, 1d` candle intervals, but the TimescaleDB continuous aggregates created in Phase 64 only cover `1h` and `1d`.

**Why it happens:** Phase 64 REQUIREMENTS.md (TSDB-01) specifies `ohlcv_daily_1h_agg` (1-hour) and `ohlcv_daily_agg` (daily). There is no `5m` or `4h` aggregate.

**How to avoid:** Scope `OLAPCandleChart` to only the two supported intervals (`1h`, `1d`). The `GET /market/candles` endpoint already validates interval and returns 400 for unsupported values — the UI should only render the `1h` and `1d` toggle buttons. Document the `5m`/`4h` gap as a known limitation.

---

## Code Examples

### Analytics Router Registration (main.py)

```python
# Source: existing app/main.py pattern
from app.routers import backtest, health, ingest, market, models, predict, ws, analytics

app.include_router(analytics.router)  # Add after market.router
```

### Flink REST API Response Shape

```json
// Source: Apache Flink REST API docs — GET /v1/jobs/overview
{
  "jobs": [
    {
      "jid": "a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0",
      "name": "ohlcv-normalizer",
      "state": "RUNNING",
      "start-time": 1711900000000,
      "end-time": -1,
      "duration": 3600000,
      "last-modification": 1711900000000,
      "tasks": {
        "total": 2,
        "created": 0,
        "scheduled": 0,
        "deploying": 0,
        "running": 2,
        "finished": 0,
        "canceling": 0,
        "canceled": 0,
        "failed": 0,
        "reconciling": 0,
        "initializing": 0
      }
    }
  ]
}
```

**Flink job state values:** `CREATED`, `RUNNING`, `FAILING`, `FAILED`, `CANCELLING`, `CANCELED`, `FINISHED`, `RESTARTING`, `SUSPENDED`, `RECONCILING`.

### New Pydantic Schemas (schemas.py additions)

```python
# Source: pattern from existing schemas.py

class FlinkJobEntry(BaseModel):
    job_id: str
    name: str
    state: str          # RUNNING | FAILED | RESTARTING | ...
    start_time: int     # Unix ms
    duration_ms: int
    tasks_running: int

class FlinkJobsResponse(BaseModel):
    jobs: list[FlinkJobEntry]
    total_running: int
    total_failed: int

class FeastViewFreshness(BaseModel):
    view_name: str
    last_updated: str | None = None   # ISO-8601 UTC
    staleness_seconds: int | None = None
    status: str  # "fresh" | "stale" | "unknown"

class FeastFreshnessResponse(BaseModel):
    views: list[FeastViewFreshness]
    registry_available: bool

class KafkaPartitionLag(BaseModel):
    partition: int
    current_offset: int
    end_offset: int
    lag: int

class KafkaLagResponse(BaseModel):
    topic: str
    consumer_group: str
    partitions: list[KafkaPartitionLag]
    total_lag: int
    sampled_at: str   # ISO-8601 UTC

class AnalyticsSummaryResponse(BaseModel):
    argocd_sync_status: str | None = None  # "Synced" | "OutOfSync" | None
    flink_running_jobs: int
    flink_failed_jobs: int
    feast_online_latency_ms: float | None = None
    ca_last_refresh: str | None = None     # ISO-8601 UTC of last continuous aggregate refresh
```

### TypeScript Interfaces (additions to types.ts)

```typescript
// Source: pattern from existing src/api/types.ts

export interface FlinkJobEntry {
  job_id: string;
  name: string;
  state: "RUNNING" | "FAILED" | "FAILING" | "RESTARTING" | "CANCELED" | "FINISHED" | string;
  start_time: number;
  duration_ms: number;
  tasks_running: number;
}

export interface FlinkJobsResponse {
  jobs: FlinkJobEntry[];
  total_running: number;
  total_failed: number;
}

export interface FeastViewFreshness {
  view_name: string;
  last_updated: string | null;
  staleness_seconds: number | null;
  status: "fresh" | "stale" | "unknown";
}

export interface FeastFreshnessResponse {
  views: FeastViewFreshness[];
  registry_available: boolean;
}

export interface KafkaPartitionLag {
  partition: number;
  current_offset: number;
  end_offset: number;
  lag: number;
}

export interface KafkaLagResponse {
  topic: string;
  consumer_group: string;
  partitions: KafkaPartitionLag[];
  total_lag: number;
  sampled_at: string;
}

export interface AnalyticsSummaryResponse {
  argocd_sync_status: string | null;
  flink_running_jobs: number;
  flink_failed_jobs: number;
  feast_online_latency_ms: number | null;
  ca_last_refresh: string | null;
}
```

### Staleness Color Logic (FeatureFreshnessPanel)

```typescript
// Thresholds from UI-RT-03: green <15min, amber <1h, red >1h
function getStalenessColor(stalenessSeconds: number | null): "success" | "warning" | "error" | "default" {
  if (stalenessSeconds === null) return "default";
  if (stalenessSeconds < 15 * 60) return "success";
  if (stalenessSeconds < 60 * 60) return "warning";
  return "error";
}
```

### OLAPCandleChart with Recharts (reusing existing pattern)

```typescript
// Source: existing src/components/dashboard/CandlestickChart.tsx + src/api/queries.ts

// Query: reuse existing useQuery pattern with refetchInterval
export function useAnalyticsCandles(ticker: string, interval: "1h" | "1d") {
  return useQuery({
    queryKey: ["analytics", "candles", ticker, interval],
    queryFn: async () => {
      const { data } = await apiClient.get<CandlesResponse>(
        "/market/candles",
        { params: { ticker, interval, limit: 100 } }
      );
      return data;
    },
    refetchInterval: 30_000,
  });
}
```

Note: `CandlesResponse` is already defined in `src/api/types.ts` — it is not in the existing type file but CandleBar is in `schemas.py`. Need to add `CandlesResponse` and `CandleBar` TS types to `types.ts`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Recharts Bar workaround for candlestick | lightweight-charts native candlestick | v5.x (2024-2025) | True OHLC rendering with price scale and cross-hair; but imperative API via useRef |
| Static API client (axios only) | React Query v5 with refetchInterval | Phase 25+ | All polling uses `refetchInterval` — no manual setInterval |
| Hardcoded mock data fallbacks | API-first with empty-state fallback | Phase 32 | API errors show empty/error states, mock data only for dev storybook |

**Deprecated/outdated:**
- `polling with setInterval + useState`: Replaced by React Query `refetchInterval`. Never use raw `setInterval` for API polling in this codebase.

---

## Open Questions

1. **Flink REST Service Name**
   - What we know: Phase 67 uses application mode with three separate FlinkDeployments
   - What's unclear: Whether the Flink Operator creates a single cluster-level REST service or per-job REST services
   - Recommendation: Check `kubectl get svc -n flink` output. If per-job, configure three separate REST URLs; if cluster-level exists, use that. Default `FLINK_REST_URL` to `http://ohlcv-normalizer-rest.flink.svc.cluster.local:8081` and add config for the other two.

2. **Feast SQL Registry Table Name**
   - What we know: Feast 0.61.0 uses SQL registry; Phase 66 ran `feast apply`
   - What's unclear: Exact PostgreSQL table name and column schema for FeatureView metadata
   - Recommendation: Query `information_schema.columns WHERE table_name LIKE '%feast%'` at test time, or check Phase 66 SUMMARY.md for what tables were actually created. If `feast_metadata` doesn't exist, fall back to returning `registry_available=false`.

3. **Kafka Consumer Group Name for Feast Writer**
   - What we know: Flink Job 3 (`feast_writer.py`) consumes `processed-features` topic
   - What's unclear: The group.id set in the Flink SQL DDL inside `feast_writer.py`
   - Recommendation: Read `services/flink-jobs/feast_writer/feast_writer.py` and grep for `group.id` to find the exact consumer group name. Make it a config env var with that value as default.

4. **Argo CD Token for SystemHealthSummary**
   - What we know: Argo CD API needs a JWT bearer token; Phase 65 deployed Argo CD
   - What's unclear: Whether a read-only service account token is available in K8s secret
   - Recommendation: Make `ARGOCD_TOKEN` optional — if not set, SystemHealthSummary shows `argocd_sync_status=null` without error. The panel should degrade gracefully.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (FastAPI backend) / Playwright (frontend E2E) |
| Config file | `services/api/pytest.ini` (existing) / `playwright.config.ts` (existing) |
| Quick run command (backend) | `cd services/api && python -m pytest tests/test_analytics_router.py -x` |
| Full suite command (backend) | `cd services/api && python -m pytest tests/ -x` |
| E2E run command (frontend) | `cd services/frontend && npx playwright test e2e/analytics.spec.ts` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-RT-01 | `/analytics` route renders without crash | E2E (Playwright) | `npx playwright test e2e/analytics.spec.ts -g "heading renders"` | ❌ Wave 0 |
| UI-RT-02 | `GET /analytics/flink/jobs` returns valid FlinkJobsResponse | unit | `pytest tests/test_analytics_router.py::test_flink_jobs_endpoint -x` | ❌ Wave 0 |
| UI-RT-03 | `GET /analytics/feast/freshness` returns FeastFreshnessResponse | unit | `pytest tests/test_analytics_router.py::test_feast_freshness_endpoint -x` | ❌ Wave 0 |
| UI-RT-04 | OLAPCandleChart renders with interval toggle at `1h` | E2E (Playwright) | `npx playwright test e2e/analytics.spec.ts -g "OLAPCandleChart"` | ❌ Wave 0 |
| UI-RT-05 | `GET /analytics/kafka/lag` returns KafkaLagResponse | unit | `pytest tests/test_analytics_router.py::test_kafka_lag_endpoint -x` | ❌ Wave 0 |
| UI-RT-06 | SystemHealthSummary card row visible on page load | E2E (Playwright) | `npx playwright test e2e/analytics.spec.ts -g "SystemHealthSummary"` | ❌ Wave 0 |
| UI-RT-07 | All panels render at 375px viewport without overflow | E2E (Playwright) | `npx playwright test e2e/analytics.spec.ts -g "responsive"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_analytics_router.py -x`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x`
- **Phase gate:** Full backend test suite + Playwright analytics spec green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `services/api/tests/test_analytics_router.py` — covers UI-RT-02, UI-RT-03, UI-RT-05
- [ ] `services/frontend/e2e/analytics.spec.ts` — covers UI-RT-01, UI-RT-04, UI-RT-06, UI-RT-07

*(No new test framework install needed — pytest and Playwright already configured)*

---

## Sources

### Primary (HIGH confidence)
- Existing project source files read directly (App.tsx, Sidebar.tsx, api/queries.ts, api/types.ts, main.py, market.py, health_service.py, kserve_client.py, schemas.py, cache.py, config.py, CandlestickChart.tsx, Drift.tsx, flinkdeployment-ohlcv-normalizer.yaml) — all findings grounded in the actual codebase
- `.planning/phases/67-apache-flink-real-time-stream-processing/67-RESEARCH.md` — Flink REST API shape, service names, job states
- `.planning/phases/66-feast-production-feature-store/66-RESEARCH.md` — Feast SQL registry, FeatureView names, table patterns
- `.planning/phases/64-timescaledb-olap-continuous-aggregates-compression/64-RESEARCH.md` — supported candle intervals (1h, 1d only)
- `.planning/ROADMAP.md` Phase 69 success criteria — UI-RT-01 through UI-RT-07 specifications

### Secondary (MEDIUM confidence)
- Flink REST API endpoint shape (`/v1/jobs/overview`) — documented in Apache Flink REST API docs; confirmed consistent with what `e2e/infra/flink-web-ui.spec.ts` already queries
- npm registry: `lightweight-charts@5.1.0` published 2025-12-16 (verified via `npm view`)
- Feast SQL registry `feast_metadata` table — inferred from Feast open-source source patterns for SQL registry backend (Phase 66 research confirms SQL registry type)

### Tertiary (LOW confidence)
- Exact Feast SQL registry table column names — not directly verified against running DB; may need to be confirmed at execution time
- Exact Kafka consumer group name used by `feast_writer.py` — not verified; must be confirmed by reading the actual file before implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new frameworks; all patterns are direct copies of existing code
- Architecture: HIGH — three new FastAPI endpoints following established patterns; five new React components following established patterns
- Pitfalls: HIGH — Flink REST service naming and Feast table schema are the two real risks; both have safe fallback strategies documented
- Candle interval scope: HIGH — confirmed only 1h and 1d supported by existing DB aggregates

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable stack — all core libraries already deployed)
