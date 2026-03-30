# Phase 70: Display Flink-Computed Streaming Features in the Dashboard — Research

**Researched:** 2026-03-30
**Domain:** React + MUI + React Query, FastAPI new streaming-features endpoint, Feast Redis online store reads, dashboard UI extension
**Confidence:** HIGH (all findings grounded in the deployed codebase from Phases 67–69)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TBD-01 | New FastAPI endpoint returning live Flink-computed features (EMA-20, RSI-14, MACD signal) for a given ticker from the Feast Redis online store | Feast FeatureStore.get_online_features() pattern; `technical_indicators_fv` with `ema_20`, `rsi_14`, `macd_signal` already pushed to Redis by Phase 67 feast_writer job |
| TBD-02 | Dashboard stock detail drawer (or dedicated component) shows Flink streaming features alongside the existing batch-computed TA panel | Dashboard.tsx Drawer already contains `DashboardTAPanel` accordion; a new `StreamingFeaturesPanel` section can be added inside the same Drawer |
| TBD-03 | Frontend React component displays EMA-20, RSI-14, and MACD signal current values with visual context (value, freshness, source badge "LIVE – Flink") | Phase 69 `FeatureFreshnessPanel.tsx` uses `MUI LinearProgress` + staleness indicator; same pattern applies here with MUI `Chip` for "LIVE" badge |
| TBD-04 | Component polls the new endpoint on a short interval (5–10s) to reflect live updates from the streaming pipeline | React Query `refetchInterval: 5000` pattern used on `useFlinkJobs` hook in queries.ts — exact same pattern |
| TBD-05 | Graceful degradation: when Feast Redis is unavailable or Flink job is not yet running, a meaningful empty state is shown rather than an error crash | ErrorBoundary per panel pattern established in Phase 69 Analytics.tsx; same `PlaceholderCard` pattern applies |
</phase_requirements>

---

## Summary

Phase 70 is a targeted extension of the existing Dashboard page to surface the three real-time streaming indicator values (EMA-20, RSI-14, MACD signal) computed by the Phase 67 Flink indicator_stream job and pushed to the Feast Redis online store by the feast_writer job. No new infrastructure is needed. The Flink jobs are already deployed, the Feast PushSource already populates Redis, and the dashboard already has a stock-detail Drawer with a `DashboardTAPanel` accordion.

The work has two layers: (1) a new FastAPI endpoint `GET /market/streaming-features/{ticker}` that calls `FeatureStore.get_online_features()` to retrieve the latest EMA-20, RSI-14, and MACD signal from Redis for a single ticker, and (2) a new `StreamingFeaturesPanel.tsx` React component rendered inside the Dashboard stock detail Drawer, below the existing `DashboardTAPanel` accordion. The panel shows the three live indicator values with their Flink-computed timestamp and a visual "LIVE — Flink" source badge.

The critical integration point is the Feast Redis online store read path. The `technical_indicators_fv` FeatureView already has `online=True` and its `stream_source` wired to `technical_indicators_push` (Phase 66/67). The API endpoint follows the exact same `FeatureStore(repo_path=...).get_online_features()` Python pattern used in `prediction_service.py`. The dashboard UI follows the Phase 69 `StreamHealthPanel.tsx` component pattern verbatim — MUI `Paper`, `Typography`, `Chip`, `Stack`, with React Query polling.

**Primary recommendation:** Implement the FastAPI endpoint first (wires `feast_service.py` extension + new router entry in `market.py`), then build `StreamingFeaturesPanel.tsx` using the established Phase 69 analytics component skeleton, and wire it into `Dashboard.tsx` stock detail Drawer as a new accordion section.

---

## Standard Stack

### Core (all already in the project — zero new installs required)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| feast[redis] | 0.61.0 | Read EMA-20/RSI-14/MACD signal from Feast Redis online store | Already installed in API requirements.txt and feast_writer Dockerfile |
| redis (via Feast) | bundled | Feast Redis online store adapter for `get_online_features()` | Redis already deployed in storage namespace (Phase 47) |
| FastAPI | 0.111.0 | New streaming-features endpoint in market.py router | Already running — just add one `@router.get` entry |
| SQLAlchemy async | 2.0.30 | Not needed for this endpoint (Feast reads Redis directly) | N/A — Feast online store path bypasses DB |
| React + Vite | 18.3.1 + 6.0.5 | Frontend component | Already bootstrapped |
| MUI v7 | 7.3.9 | `Paper`, `Chip`, `Stack`, `Typography`, `Skeleton`, `Divider` | All existing dashboard panels use MUI — consistent with Bloomberg dark theme |
| React Query v5 | 5.62.0 | `useQuery({ refetchInterval: 5000 })` poll hook | Pattern already used for `useFlinkJobs` (5s) and all market data hooks |
| axios / apiClient | 1.7.9 | HTTP calls from React to FastAPI | Already used throughout via `apiClient` from `@/api/client` |

### Feast Online Read Path (critical)

The Feast online store read follows this exact pattern (verified from `prediction_service.py` and `feast_service.py`):

```python
from feast import FeatureStore

store = FeatureStore(repo_path=settings.FEAST_STORE_PATH)
feature_vector = store.get_online_features(
    features=["technical_indicators_fv:ema_20", "technical_indicators_fv:rsi_14", "technical_indicators_fv:macd_signal"],
    entity_rows=[{"ticker": ticker.upper()}],
).to_dict()
```

The `technical_indicators_fv` FeatureView has `online=True` and `stream_source=technical_indicators_push` — confirmed in `ml/feature_store/feature_repo.py`. The feast_writer job pushes `ema_20`, `rsi_14`, `macd_signal` fields for each ticker (schema confirmed from `feast_writer.py` lines 47–49).

**Version verification:** feast 0.61.0 already pinned in `services/api/requirements.txt` — no change needed.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Feast `get_online_features()` from API | Direct Redis query via `redis.asyncio` | Direct Redis requires knowing Feast's internal key format (non-standard, Feast-managed) — fragile, bypasses Feast schema contract |
| New `/market/streaming-features/{ticker}` endpoint | Reuse `GET /market/indicators/{ticker}` with a new field | Batch indicators endpoint reads PostgreSQL; Flink features come from Redis online store — different latency and staleness profile; keep separate for clarity |
| Polling `refetchInterval: 5000` | WebSocket for real-time push | WebSocket infrastructure is already used for live prices (Phase 45) but adding a new WS topic for streaming features is heavier than polling; 5-second polling matches the 5-minute HOP window output rate of the Flink job — there is no sub-5-minute freshness gain from WS |

---

## Architecture Patterns

### Recommended Project Structure

New files this phase adds:

```
stock-prediction-platform/
├── services/api/
│   ├── app/
│   │   ├── routers/
│   │   │   └── market.py               MODIFY: add GET /market/streaming-features/{ticker}
│   │   ├── services/
│   │   │   └── feast_online_service.py NEW: get_streaming_features(ticker) via Feast online store
│   │   └── models/
│   │       └── schemas.py              MODIFY: add StreamingFeaturesResponse Pydantic schema
│   └── tests/
│       └── test_streaming_features.py  NEW: unit tests for feast_online_service + router
│
└── services/frontend/src/
    ├── api/
    │   ├── types.ts                    MODIFY: add StreamingFeaturesResponse TS interface
    │   └── queries.ts                  MODIFY: add useStreamingFeatures(ticker) hook
    └── components/dashboard/
        ├── StreamingFeaturesPanel.tsx  NEW: displays EMA-20/RSI-14/MACD signal with LIVE badge
        └── index.ts                    MODIFY: re-export StreamingFeaturesPanel
```

`Dashboard.tsx` receives one new import and one new accordion section inside the existing `selectedTicker` Drawer.

### Pattern 1: Feast Online Store Read in FastAPI Service

**What:** A new `feast_online_service.py` that wraps `FeatureStore.get_online_features()` with the same graceful-degradation pattern as `flink_service.py` — returns a result with `available=False` instead of raising on connection failure.

**When to use:** Any time the API needs to retrieve Flink-computed features from Redis.

**Example:**
```python
# Source: feast_service.py + prediction_service.py patterns in codebase
from feast import FeatureStore
from app.config import settings
from app.models.schemas import StreamingFeaturesResponse

async def get_streaming_features(ticker: str) -> StreamingFeaturesResponse:
    try:
        store = FeatureStore(repo_path=settings.FEAST_STORE_PATH)
        result = store.get_online_features(
            features=[
                "technical_indicators_fv:ema_20",
                "technical_indicators_fv:rsi_14",
                "technical_indicators_fv:macd_signal",
            ],
            entity_rows=[{"ticker": ticker.upper()}],
        ).to_dict()
        return StreamingFeaturesResponse(
            ticker=ticker.upper(),
            ema_20=result.get("ema_20", [None])[0],
            rsi_14=result.get("rsi_14", [None])[0],
            macd_signal=result.get("macd_signal", [None])[0],
            available=True,
            source="flink-indicator-stream",
        )
    except Exception:
        return StreamingFeaturesResponse(
            ticker=ticker.upper(),
            ema_20=None, rsi_14=None, macd_signal=None,
            available=False,
            source="flink-indicator-stream",
        )
```

**Important:** `FeatureStore()` initialization is NOT async-native in Feast 0.61.0. Use `asyncio.get_event_loop().run_in_executor(None, ...)` or a sync helper wrapped in FastAPI's `run_in_threadpool` if blocking becomes an issue. The `flink_service.py` already uses httpx's async API; for Feast calls, the sync wrapper pattern is simpler and safe given the low-frequency poll rate.

### Pattern 2: FastAPI Router Extension (market.py)

Add a new route that follows the exact caching pattern of `GET /market/indicators/{ticker}`:

```python
# Source: market.py in codebase — existing indicators route pattern
STREAMING_FEATURES_TTL = 5  # 5s — matches frontend poll interval

@router.get("/streaming-features/{ticker}", response_model=StreamingFeaturesResponse)
async def streaming_features(ticker: str) -> StreamingFeaturesResponse:
    key = build_key("market", "streaming-features", ticker.upper())
    cached = await cache_get(key)
    if cached is not None:
        return StreamingFeaturesResponse(**cached)
    result = await get_streaming_features(ticker.upper())
    await cache_set(key, result.model_dump(), STREAMING_FEATURES_TTL)
    return result
```

The TTL of 5 seconds matches the frontend poll interval, so each poll always gets a fresh Feast read on the first request. Redis caching here protects against multiple users polling the same ticker simultaneously — consistent with the existing pattern.

### Pattern 3: React Component — StreamingFeaturesPanel

**What:** A self-contained MUI component that displays three indicator values (EMA-20, RSI-14, MACD signal) with per-indicator meaning annotations and a "LIVE — Flink" chip, rendered inside the Dashboard Drawer.

**When to use:** Inside Dashboard.tsx Drawer for the selected ticker, as a new Accordion section below `DashboardTAPanel`.

**Example skeleton:**
```tsx
// Source: Phase 69 StreamHealthPanel.tsx + Phase 69 FeatureFreshnessPanel.tsx patterns
import { Chip, Divider, Paper, Skeleton, Stack, Typography } from "@mui/material";
import { useStreamingFeatures } from "@/api";

interface StreamingFeaturesPanelProps { ticker: string; }

export default function StreamingFeaturesPanel({ ticker }: StreamingFeaturesPanelProps) {
  const { data, isLoading, isError } = useStreamingFeatures(ticker);

  if (isLoading) return <Skeleton variant="rectangular" height={120} />;
  if (isError || !data?.available) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Streaming features unavailable — Flink job may not be running
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="subtitle2" fontWeight={700}>Streaming Indicators</Typography>
        <Chip label="LIVE — Flink" size="small" color="success" />
      </Stack>
      <Divider sx={{ mb: 1.5 }} />
      <Stack spacing={1}>
        <FeatureRow label="EMA-20" value={data.ema_20} unit="" />
        <FeatureRow label="RSI-14" value={data.rsi_14} unit="" rsiContext />
        <FeatureRow label="MACD Signal" value={data.macd_signal} unit="" />
      </Stack>
    </Paper>
  );
}
```

### Pattern 4: React Query Polling Hook

```tsx
// Source: queries.ts useFlinkJobs pattern (refetchInterval: 5000)
export function useStreamingFeatures(ticker: string) {
  return useQuery({
    queryKey: ["market", "streaming-features", ticker.toUpperCase()],
    queryFn: async () => {
      const { data } = await apiClient.get<StreamingFeaturesResponse>(
        `/market/streaming-features/${encodeURIComponent(ticker.toUpperCase())}`,
      );
      return data;
    },
    enabled: !!ticker,
    refetchInterval: 5_000,   // 5s — Flink HOP window fires every 5 minutes, but polling fast ensures we catch new values quickly
    staleTime: 4_000,
  });
}
```

### Dashboard.tsx Integration Point

The Drawer already has the `DashboardTAPanel` in an Accordion. Add `StreamingFeaturesPanel` as a second Accordion section just above it (streaming features are more prominent — live data before historical batch data):

```tsx
// In Dashboard.tsx Drawer section (after MetricCards, before charts):
<Accordion>
  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
    <Typography variant="body2">
      Streaming Features
      <Chip size="small" label="Flink" color="success" sx={{ ml: 1, fontSize: "0.6rem", height: 16 }} />
    </Typography>
  </AccordionSummary>
  <AccordionDetails>
    <StreamingFeaturesPanel ticker={selectedTicker} />
  </AccordionDetails>
</Accordion>
```

### Anti-Patterns to Avoid

- **Do not call `FeatureStore()` in a FastAPI async endpoint without executor wrapping:** Feast's online read path uses synchronous Redis client calls. Calling blocking I/O in an async def handler without `run_in_executor` will block the event loop. Use `starlette.concurrency.run_in_threadpool` or an executor.
- **Do not cache streaming features for longer than the poll interval:** A 60s TTL would defeat the "live" nature of the data. Keep TTL at 5s maximum.
- **Do not render `StreamingFeaturesPanel` unless `selectedTicker` is set:** The `enabled: !!ticker` guard in the query hook already prevents requests, but the component should also return `null` early if `ticker` is empty to avoid mounting React Query hooks with empty strings.
- **Do not import feast at module level in the FastAPI app:** Feast's package-level imports can be slow (registry discovery). Import inside the service function or use lazy module import to avoid slowing API startup.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Online feature lookup from Redis | Custom Redis hash key parsing | `FeatureStore.get_online_features()` | Feast's internal Redis key format is versioned and non-obvious — only the Feast SDK is guaranteed to decode it correctly |
| Live indicator value for the "freshest" timestamp | Manual Kafka consumer in FastAPI | Feast Redis online store | Feast guarantees only the latest value per entity key is stored in the online store — no timestamp management needed |
| Streaming-aware chart with scrolling updates | Custom WebSocket push + chart redraws | `refetchInterval` polling in React Query | The Flink HOP window only produces output every 5 minutes; sub-5-minute polling provides no new data and adds complexity without benefit |

---

## Common Pitfalls

### Pitfall 1: Feast Not Yet Applied / Redis Empty on First Run

**What goes wrong:** `get_online_features()` returns `None` values for all features because the `feast apply` command has not been run or the feast_writer Flink job has not emitted any records yet.

**Why it happens:** The Feast Redis online store is populated exclusively by `store.push()` calls from the feast_writer job. If the job is not RUNNING or no intraday data has been ingested since the last cluster start, all feature values will be `None`.

**How to avoid:** The `StreamingFeaturesResponse.available` field must be set based on whether any feature values are non-None, not just whether the Feast call succeeded. The UI `PlaceholderCard` empty state must explicitly say "No live Flink data yet — intraday data ingestion must be active."

**Warning signs:** `ema_20`, `rsi_14`, `macd_signal` all return `None` — check Flink job state via `/analytics/flink/jobs` before debugging the API.

### Pitfall 2: Feast FeatureStore Initialization is Synchronous and Slow on Cold Start

**What goes wrong:** The first call to `FeatureStore(repo_path=...)` on a cold FastAPI pod takes 1–3 seconds due to Feast registry loading (SQL registry query). This blocks the async event loop.

**Why it happens:** Feast 0.61.0 uses a synchronous registry client internally even when using the PostgreSQL backend.

**How to avoid:** Wrap the `FeatureStore` call in `starlette.concurrency.run_in_threadpool` (already available in FastAPI's dependency injection system). Alternatively, instantiate the `FeatureStore` once at module import time in `feast_online_service.py` (module-level singleton) to amortize the cold-start cost — the same pattern used for other shared clients in the codebase (`model_metadata_cache.py`).

### Pitfall 3: Feast FEAST_STORE_PATH Points to Wrong Location

**What goes wrong:** `FeatureStore(repo_path=settings.FEAST_STORE_PATH)` raises `FileNotFoundError: feature_store.yaml not found`.

**Why it happens:** The `FEAST_STORE_PATH` env var in the API pod configmap points to the feast store used by the ML pipeline (typically `/app/ml/feature_store/`), but the `feature_store.yaml` there uses a PostgreSQL registry while the feast_writer job uses a Redis online store. Both must point to the same Feast registry.

**How to avoid:** Verify that `settings.FEAST_STORE_PATH` is consistent across the API, feast_writer, and ML pipeline pods. The existing `flink-config-configmap.yaml` and the API configmap should both reference the same path. If the API pod does not have `feature_store.yaml` mounted, add a ConfigMap volume mount as done in `flinkdeployment-feast-writer.yaml`.

### Pitfall 4: RSI-14 Context Missing in UI

**What goes wrong:** A raw RSI-14 value of `72.5` is shown without context — users do not know if that is overbought/oversold.

**Why it happens:** Phase 70 shows streaming feature values for the first time without the charted context that `DashboardTAPanel` provides for the batch-computed indicators.

**How to avoid:** Add inline RSI context labels: show "Overbought" in amber for RSI > 70, "Oversold" in green for RSI < 30, and "Neutral" for values in between. The threshold lines already exist in `DashboardTAPanel.tsx` `RsiChart` — mirror the same thresholds in the `StreamingFeaturesPanel`.

### Pitfall 5: Cache TTL Conflicts Between Streaming Features and Batch Indicators

**What goes wrong:** The existing `GET /market/indicators/{ticker}` endpoint uses `MARKET_INDICATORS_TTL = 60` (60s). If the new streaming-features endpoint shares the same cache key prefix by mistake, batch-computed indicator values could be returned for live streaming requests.

**Why it happens:** The `build_key()` function uses positional arguments — `build_key("market", "streaming-features", ticker)` is distinct from `build_key("market", "indicators", ticker)` only if the middle segment differs.

**How to avoid:** Use exactly `build_key("market", "streaming-features", ticker.upper())` for the new endpoint. Verify in the implementation that the cache key matches this pattern.

---

## Code Examples

### Pydantic Schema (schemas.py addition)

```python
# Source: schemas.py existing patterns
class StreamingFeaturesResponse(BaseModel):
    ticker: str
    ema_20: float | None = None
    rsi_14: float | None = None
    macd_signal: float | None = None
    available: bool = False
    source: str = "flink-indicator-stream"
    sampled_at: str | None = None  # ISO8601 timestamp of when Redis was queried
```

### TypeScript Interface (types.ts addition)

```typescript
// Source: Phase 69 FlinkJobsResponse pattern
export interface StreamingFeaturesResponse {
  ticker: string;
  ema_20: number | null;
  rsi_14: number | null;
  macd_signal: number | null;
  available: boolean;
  source: string;
  sampled_at: string | null;
}
```

### Test Pattern (feast_online_service test)

```python
# Source: test_feast_writer.py sys.modules mock pattern
import sys
from unittest.mock import MagicMock, patch

# Mock feast before import to avoid feast runtime dependency
mock_feast = MagicMock()
mock_feast.FeatureStore.return_value.get_online_features.return_value.to_dict.return_value = {
    "ema_20": [155.32],
    "rsi_14": [62.4],
    "macd_signal": [0.073],
}
sys.modules["feast"] = mock_feast

from app.services.feast_online_service import get_streaming_features

async def test_get_streaming_features_returns_values():
    result = await get_streaming_features("AAPL")
    assert result.ticker == "AAPL"
    assert result.ema_20 == pytest.approx(155.32)
    assert result.available is True
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Batch-only technical indicators from PostgreSQL | Flink streaming indicators pushed to Feast Redis via HOP window UDAFs | Phase 67 (2026-03-30) | EMA-20, RSI-14, MACD signal now available at sub-5-minute latency in Redis, not just end-of-day |
| Dashboard TA panel reads only `GET /market/indicators/{ticker}` (daily batch) | Phase 70 adds `GET /market/streaming-features/{ticker}` reading Feast Redis online store | Phase 70 | Traders see live streaming indicator values alongside historical batch TA |

**Note on Bollinger Bands, Volatility, Momentum:** The Phase 67 indicator_stream HOP window job computes ONLY `ema_20`, `rsi_14`, and `macd_signal`. The ROADMAP phase description mentions "RSI, MACD, Bollinger Bands, EMA, volatility, momentum indicators" — however, the Flink job code (confirmed from `indicator_stream.py` and `feast_writer.py`) only pushes these three features. Bollinger Bands, volatility, and momentum are batch-computed in the ML pipeline but NOT currently computed in the Flink streaming job. Phase 70 must scope to only the three features that Flink actually computes. Adding more streaming indicators (Bollinger Bands, momentum) would require changes to `indicator_stream.py` and `feast_writer.py` — that is out of scope for Phase 70 unless explicitly extended.

---

## Open Questions

1. **Should Phase 70 also add Bollinger Bands / volatility / momentum to the Flink streaming pipeline?**
   - What we know: `indicator_stream.py` only computes EMA-20, RSI-14, MACD signal. Bollinger Bands require a separate rolling window computation.
   - What's unclear: Whether the ROADMAP description of "Bollinger Bands, volatility, momentum" for Phase 70 means "display what Flink already computes" or "add those indicators to the Flink job first."
   - Recommendation: Scope Phase 70 to display what Flink already computes (EMA-20, RSI-14, MACD signal). Add new Flink streaming indicators in a separate Phase 71 if desired. This keeps Phase 70 purely a UI/API phase without expanding the Flink job scope.

2. **Should `feast_online_service.py` reuse the existing `feast_service.py` (freshness queries) or be a separate module?**
   - What we know: `feast_service.py` does SQL queries via SQLAlchemy for Feast freshness metadata. `feast_online_service.py` would call `FeatureStore.get_online_features()` to read live values from Redis.
   - What's unclear: Whether sharing the FeatureStore singleton across both services could cause initialization conflicts.
   - Recommendation: Keep them separate. `feast_service.py` = metadata/freshness (SQL). `feast_online_service.py` = live feature values (Redis). Clean separation of concerns.

3. **Should the "LIVE — Flink" badge link to the StreamHealthPanel on the /analytics page?**
   - What we know: The Analytics page (Phase 69) already shows Flink job health. The Dashboard Drawer is independent.
   - Recommendation: Optionally add a tooltip on the "LIVE — Flink" chip that says "Powered by Apache Flink indicator_stream job" with no navigation — keeps the UX simple.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (detected: `tests/` directory with `test_*.py` files throughout) |
| Config file | `pytest.ini` or `pyproject.toml` in `services/api/` |
| Quick run command | `cd stock-prediction-platform && pytest tests/test_streaming_features.py -x -q` |
| Full suite command | `cd stock-prediction-platform && pytest tests/ -x -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TBD-01 | `get_streaming_features("AAPL")` returns EMA/RSI/MACD from mocked Feast | unit | `pytest tests/test_streaming_features.py::test_get_streaming_features_returns_values -x` | No — Wave 0 |
| TBD-01 | `get_streaming_features("AAPL")` returns `available=False` when Feast raises | unit | `pytest tests/test_streaming_features.py::test_get_streaming_features_unavailable -x` | No — Wave 0 |
| TBD-01 | `GET /market/streaming-features/AAPL` returns 200 with `StreamingFeaturesResponse` schema | unit | `pytest tests/test_streaming_features.py::test_streaming_features_endpoint -x` | No — Wave 0 |
| TBD-02 | `StreamingFeaturesPanel` renders three indicator rows when data is available | unit (React Testing Library or Playwright) | `playwright test tests/dashboard.spec.ts` | Extend existing |
| TBD-05 | `StreamingFeaturesPanel` shows empty state when `available=false` | unit | `playwright test tests/dashboard.spec.ts::streaming-features-empty-state` | Extend existing |

### Sampling Rate

- **Per task commit:** `cd stock-prediction-platform && pytest tests/test_streaming_features.py -x -q`
- **Per wave merge:** `cd stock-prediction-platform && pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `stock-prediction-platform/tests/test_streaming_features.py` — covers TBD-01 (FastAPI endpoint + service unit tests)
- [ ] `stock-prediction-platform/services/frontend/src/components/dashboard/StreamingFeaturesPanel.tsx` — component (created during implementation)
- [ ] `stock-prediction-platform/services/api/app/services/feast_online_service.py` — service (created during implementation)

---

## Sources

### Primary (HIGH confidence)

- `stock-prediction-platform/services/flink-jobs/indicator_stream/indicator_stream.py` — confirmed Flink job schema: `ticker`, `timestamp`, `ema_20`, `rsi_14`, `macd_signal` fields on `processed-features` topic
- `stock-prediction-platform/services/flink-jobs/feast_writer/feast_writer.py` — confirmed Feast push schema: pushes `ema_20`, `rsi_14`, `macd_signal` per ticker to Redis via `technical_indicators_push` PushSource
- `stock-prediction-platform/ml/feature_store/feature_repo.py` — confirmed `technical_indicators_fv` FeatureView has `online=True` and `stream_source=technical_indicators_push`
- `stock-prediction-platform/services/api/app/routers/market.py` — existing pattern for new route and caching
- `stock-prediction-platform/services/api/app/services/flink_service.py` — established graceful-degradation pattern for external service calls
- `stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx` — confirmed Drawer structure with `DashboardTAPanel` accordion — exact integration point
- `stock-prediction-platform/services/frontend/src/api/types.ts` — confirmed existing TypeScript interfaces and extension pattern
- `stock-prediction-platform/services/frontend/src/api/queries.ts` — confirmed React Query polling hook pattern (`refetchInterval: 5000`)
- Phase 67 SUMMARY.md files — confirmed all three Flink jobs complete and deployed

### Secondary (MEDIUM confidence)

- Feast 0.61.0 `get_online_features()` synchronous API behavior — inferred from feast_service.py patterns in the codebase and Phase 66/67 research documentation; blocking behavior is well-known in Feast community

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, confirmed in requirements.txt and package.json
- Architecture: HIGH — grounded in deployed Phase 67/69 code patterns, no speculation
- Pitfalls: HIGH — Feast sync blocking and `available=False` empty state identified directly from the code; FEAST_STORE_PATH issue is a known multi-pod deployment concern

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (Feast 0.61.0 and Flink 1.19 are pinned; stable for 30 days)
