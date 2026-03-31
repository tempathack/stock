# Phase 71: High-Frequency Alternative Data Pipeline — Research

**Researched:** 2026-03-31
**Domain:** Reddit PRAW producer, Kafka topics, PyFlink HOP window (VADER sentiment), Feast FeatureView, FastAPI WebSocket, React WebSocket hook + MUI SentimentPanel
**Confidence:** HIGH (all findings grounded in deployed codebase from Phases 45/66/67/70)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data Sources**
- Source: Reddit via PRAW — subreddits: r/wallstreetbets, r/stocks, r/investing
- Ticker extraction: Regex matching on post title + body — pattern `\$([A-Z]{1,5})` plus direct uppercase match against S&P 500 ticker list; maintain a blocklist for common false positives (IT, A, AT, BE, GO, OR, etc.)
- Coverage: All S&P 500 tickers — posts mentioning any S&P 500 ticker are captured
- Polling interval: Every 1 minute per subreddit (stays within Reddit API rate limits of 60 req/min for authenticated clients)
- Kafka producer: Standalone Python service producing to `reddit-raw` topic; runs as a K8s Deployment (not CronJob — persistent polling loop)

**Kafka Topics**
- `reddit-raw` — raw Reddit post JSON: `{post_id, title, body, subreddit, created_utc, tickers: []}`
- `sentiment-aggregated` — Flink windowed output: `{ticker, window_start, window_end, avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit}`
- Follow existing topic naming convention (matches intraday-data, processed-features pattern)

**Sentiment Model & Flink Analysis**
- NLP model: VADER (vaderSentiment library) — lexicon-based, social-media-tuned, in-process (no GPU, no sidecar), returns compound score −1 to +1
- Flink job: `sentiment_stream` — consumes `reddit-raw`, applies VADER per post, aggregates with HOP window (1-min hop, 5-min window) per ticker
- Output per window: `avg_sentiment`, `mention_count`, `positive_ratio`, `negative_ratio`, `top_subreddit` (most frequent subreddit in window)
- Persistence: Feast Redis online store — new FeatureView `reddit_sentiment_fv` with fields: `avg_sentiment`, `mention_count`, `positive_ratio`, `negative_ratio`, `last_updated`; entity: `ticker`

**FastAPI WebSocket Endpoint**
- Endpoint: `GET /ws/sentiment/{ticker}` — WebSocket connection; server pushes new sentiment JSON on each completed Flink window
- Reads from Feast Redis online store on each push cycle (same pattern as `feast_online_service.py` from Phase 70)
- Push interval: every 60 seconds (aligns with 1-min HOP output rate)
- Connection lifecycle: client connects per ticker on drawer open, disconnects on drawer close

**Frontend Display**
- Location: New `SentimentPanel` accordion inside Dashboard stock detail drawer — below the existing `StreamingFeaturesPanel` from Phase 70. Same MUI Paper/Accordion pattern.
- Visual elements: `avg_sentiment` as MUI `LinearProgress` bar colored red (−1) → yellow (0) → green (+1); `mention_count` as MUI `Typography` label; `positive_ratio` / `negative_ratio` as secondary text; freshness timestamp (last_updated) with staleness indicator; MUI `Chip` label "LIVE — Reddit" in green
- WebSocket client: Custom React hook `useSentimentSocket(ticker)` — opens WS connection, updates state on message, closes on unmount; no React Query polling (WS push instead)

**Degraded State**
- While connecting or no data received yet: MUI `Skeleton` placeholder rows
- If WebSocket disconnects or API returns null: `PlaceholderCard` with message "Sentiment data unavailable — pipeline may be starting"
- Same ErrorBoundary pattern as Phase 69/70 panels — no crash, graceful fallback

### Claude's Discretion
- Exact K8s Deployment manifest structure for the Reddit PRAW producer
- VADER score thresholds for positive/negative/neutral classification (suggest: positive > 0.05, negative < −0.05)
- WebSocket reconnect logic (exponential backoff, max retries)
- Exact MUI color mapping for the sentiment LinearProgress gradient
- Flink job parallelism settings and checkpoint interval

### Deferred Ideas (OUT OF SCOPE)
- NewsAPI integration (institutional news sentiment)
- Historical sentiment TimescaleDB table for trend charts
- FinBERT inference (finance-tuned BERT) — requires GPU/sidecar
- Sentiment signals used as ML model features in training pipeline
- /sentiment dedicated page with market-wide heatmap
</user_constraints>

---

## Summary

Phase 71 builds a complete high-frequency alternative data pipeline layered on top of the existing Phase 67 Flink infrastructure. The pipeline has five layers: (1) a Reddit PRAW producer as a K8s Deployment polling three subreddits every 60 seconds and publishing to a new `reddit-raw` Kafka topic, (2) a new `sentiment_stream` Flink job that consumes `reddit-raw`, scores each post with VADER, and aggregates per-ticker sentiment in a 1-min-hop / 5-min-window HOP window to the `sentiment-aggregated` Kafka topic, (3) a new Feast `reddit_sentiment_fv` FeatureView with a `PushSource` and a new `sentiment_writer` Flink job (replicating `feast_writer.py`) that pushes from `sentiment-aggregated` to Feast Redis, (4) a new FastAPI WebSocket endpoint `/ws/sentiment/{ticker}` that reads Feast Redis every 60 seconds and pushes to connected clients, and (5) a `SentimentPanel.tsx` React component inside the Dashboard stock-detail Drawer using a `useSentimentSocket(ticker)` hook.

All six major subsystems have direct predecessors in the codebase to replicate: the PRAW producer is a new standalone Python service similar to `kafka_producer.py`; `sentiment_stream` replicates the `indicator_stream.py` HOP window job structure; the `sentiment_writer` is a direct copy of `feast_writer.py` targeting a new PushSource; the new FeatureView follows the `technical_indicators_fv` pattern in `feature_repo.py`; the WebSocket endpoint replicates `/ws/prices` from `ws.py` but with a per-ticker subscription model and a timed push loop instead of a broadcaster; and `SentimentPanel.tsx` follows the `StreamingFeaturesPanel.tsx` component skeleton from Phase 70.

The primary complexity difference from Phase 70 is the WebSocket push model (not HTTP polling) for the frontend, the VADER in-process scoring inside the Flink job, and the two new Kafka topics that require Strimzi KafkaTopic CRs. The `useSentimentSocket` hook reuses the existing `useWebSocket.ts` infrastructure.

**Primary recommendation:** Build in dependency order: Kafka topics → PRAW producer → sentiment_stream Flink job → sentiment_writer Flink job → Feast FeatureView → FastAPI WebSocket endpoint → SentimentPanel.tsx + hook. Each layer can be tested independently before the next is wired.

---

## Standard Stack

### Core (new additions to existing project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| praw | 7.8.1 (current) | Reddit API Python wrapper — subreddit streaming/polling | Official Reddit API SDK; handles OAuth, rate limiting, pagination |
| vaderSentiment | 3.3.2 (current) | In-process sentiment scoring — returns compound score −1 to +1 | Social-media-tuned lexicon; handles ALL CAPS, emoji, slang; no GPU; no sidecar needed |
| confluent-kafka | 2.4.0 (already in API requirements.txt) | Kafka producer for PRAW service | Already pinned in codebase; used by `kafka_producer.py` |
| apache-flink | 1.19.x (already in Flink Dockerfiles) | sentiment_stream and sentiment_writer Flink jobs | Existing Flink 1.19 infrastructure; same operator and CRs |
| feast[redis] | 0.61.0 (already pinned) | `reddit_sentiment_fv` online store push + read | Already installed; `technical_indicators_fv` pattern is identical |
| FastAPI | 0.111.0 (already installed) | `/ws/sentiment/{ticker}` WebSocket endpoint | Already running; replicate `ws.py` |
| websockets | >=12.0 (already in requirements.txt) | WebSocket transport layer for FastAPI | Already pinned |
| MUI v7 | 7.3.9 (already installed) | SentimentPanel, LinearProgress, Chip, Skeleton | All existing — no new installs |

### Reddit PRAW Producer — new standalone service

```
services/
└── reddit-producer/
    ├── Dockerfile
    ├── requirements.txt      # praw, confluent-kafka, vaderSentiment (NOT needed here — Flink scores)
    ├── reddit_producer.py    # polling loop, ticker extraction, Kafka publish
    └── sp500_tickers.py      # S&P 500 ticker list + blocklist
```

**Installation for reddit-producer:**
```bash
pip install praw==7.8.1 confluent-kafka==2.4.0
```

**Installation for sentiment_stream Flink job (added to Dockerfile):**
```bash
pip install vaderSentiment==3.3.2 apache-flink==1.19.* pandas
```

**Installation for sentiment_writer Flink job (same as feast_writer):**
```bash
# Same as feast_writer Dockerfile — adds feast[redis]==0.61.0
pip install feast[redis]==0.61.0 apache-flink==1.19.* pandas
```

**Version verification (confirmed from PyPI on 2026-03-31):**
- praw: 7.8.1 (latest)
- vaderSentiment: 3.3.2 (latest, unchanged since 2020 — stable)

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| VADER in-process | FinBERT sidecar | FinBERT is finance-tuned and more accurate on institutional text, but requires GPU; VADER is explicitly designed for social media slang — deferred to future phase |
| PRAW polling every 60s | Reddit streaming (praw `stream.submissions()`) | `stream.submissions()` is WebSocket-based and lower-latency, but is harder to rate-limit and manage in K8s — polling is more reliable and predictable |
| Per-ticker WS endpoint `/ws/sentiment/{ticker}` | Single broadcast WS `/ws/sentiment` | Per-ticker is lower bandwidth per client (only receives data for the selected stock); single broadcast would push all tickers to every drawer — wasteful |
| Feast Redis for sentiment store | Direct Redis hash writes | Feast provides schema contract, TTL management, and compatibility with `get_online_features()` API — same reason as Phase 70 |

---

## Architecture Patterns

### Recommended Project Structure

New files this phase adds:

```
stock-prediction-platform/
├── services/
│   ├── reddit-producer/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── reddit_producer.py      NEW: polling loop, ticker extraction, Kafka publish
│   │   └── sp500_tickers.py        NEW: S&P 500 ticker list + blocklist
│   └── flink-jobs/
│       ├── sentiment_stream/
│       │   ├── Dockerfile           NEW: flink:1.19 + vaderSentiment + apache-flink
│       │   ├── requirements.txt
│       │   └── sentiment_stream.py  NEW: HOP window job, VADER scoring, ticker grouping
│       └── sentiment_writer/
│           ├── Dockerfile           NEW: copy of feast_writer Dockerfile + sentiment target
│           ├── requirements.txt
│           └── sentiment_writer.py  NEW: consumes sentiment-aggregated, pushes to Feast Redis
│
├── k8s/
│   ├── kafka/
│   │   └── kafka-topic-reddit.yaml        NEW: reddit-raw + sentiment-aggregated KafkaTopic CRs
│   ├── flink/
│   │   ├── flinkdeployment-sentiment-stream.yaml   NEW: FlinkDeployment CR for sentiment_stream
│   │   └── flinkdeployment-sentiment-writer.yaml   NEW: FlinkDeployment CR for sentiment_writer
│   └── ingestion/
│       ├── reddit-producer-deployment.yaml  NEW: K8s Deployment for reddit_producer service
│       └── reddit-producer-configmap.yaml   NEW: ConfigMap with KAFKA_BOOTSTRAP_SERVERS, SUBREDDITS
│
├── ml/
│   └── feature_store/
│       └── feature_repo.py         MODIFY: add reddit_sentiment_push PushSource + reddit_sentiment_fv
│
└── services/
    ├── api/
    │   ├── app/
    │   │   ├── routers/
    │   │   │   └── ws.py             MODIFY: add /ws/sentiment/{ticker} WebSocket endpoint
    │   │   ├── services/
    │   │   │   └── feast_online_service.py  MODIFY: add get_sentiment_features(ticker)
    │   │   └── models/
    │   │       └── schemas.py        MODIFY: add SentimentFeaturesResponse Pydantic schema
    │   └── tests/
    │       └── test_sentiment_ws.py  NEW: unit tests for sentiment WS endpoint + service
    │
    └── frontend/src/
        ├── hooks/
        │   └── useSentimentSocket.ts  NEW: WS hook for /ws/sentiment/{ticker}
        └── components/dashboard/
            ├── SentimentPanel.tsx     NEW: displays avg_sentiment LinearProgress + mention count
            └── index.ts               MODIFY: re-export SentimentPanel
```

`Dashboard.tsx` receives one new import and one new Accordion section below `StreamingFeaturesPanel`.

---

### Pattern 1: Reddit PRAW Producer Service

**What:** Standalone Python script that runs as a persistent K8s Deployment. Polls three subreddits every 60 seconds using PRAW, extracts ticker symbols, and publishes to `reddit-raw` Kafka topic.

**When to use:** Anytime new Reddit data needs to be ingested. No CronJob — must be a persistent Deployment.

**Key PRAW API pattern:**
```python
# Source: PRAW 7.8.1 official docs — https://praw.readthedocs.io/en/stable/
import praw
import re
import time
import json
from confluent_kafka import Producer

SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
TICKER_RE = re.compile(r'\$([A-Z]{1,5})\b')
BLOCKLIST = {"IT", "A", "AT", "BE", "GO", "OR", "ARE", "SO", "ALL", "CAN", "CEO", "IMO",
             "DD", "EOD", "AI", "US", "UK", "EU", "FOR", "ME"}

reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent="stock-sentiment-bot/1.0",
    read_only=True,  # IMPORTANT: read-only avoids write permission scope
)

producer = Producer({"bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"]})

def extract_tickers(text: str, sp500_set: set[str]) -> list[str]:
    """Extract S&P 500 ticker mentions from text."""
    found = set()
    # Pattern 1: $AAPL style
    for m in TICKER_RE.finditer(text or ""):
        t = m.group(1)
        if t in sp500_set and t not in BLOCKLIST:
            found.add(t)
    # Pattern 2: bare uppercase words that match S&P 500 and aren't in blocklist
    for word in re.findall(r'\b([A-Z]{1,5})\b', text or ""):
        if word in sp500_set and word not in BLOCKLIST:
            found.add(word)
    return list(found)

def poll_subreddit(subreddit_name: str, sp500_set: set[str], limit: int = 25) -> None:
    sub = reddit.subreddit(subreddit_name)
    for post in sub.new(limit=limit):
        text = f"{post.title} {post.selftext}"
        tickers = extract_tickers(text, sp500_set)
        if not tickers:
            continue
        record = {
            "post_id": post.id,
            "title": post.title,
            "body": post.selftext[:2000],   # truncate to avoid large payloads
            "subreddit": subreddit_name,
            "created_utc": int(post.created_utc),
            "tickers": tickers,
        }
        producer.produce(
            topic="reddit-raw",
            key=post.id,
            value=json.dumps(record).encode(),
        )
    producer.flush()

# Main loop:
while True:
    for sr in SUBREDDITS:
        poll_subreddit(sr, SP500_SET)
    time.sleep(60)
```

**PRAW Authentication:** PRAW requires `client_id` and `client_secret` from https://www.reddit.com/prefs/apps. A "script" app type is sufficient for read-only access. These go in a new K8s Secret `reddit-secrets` in the ingestion namespace.

**Rate limiting:** Reddit allows 100 requests per minute for authenticated OAuth2 clients. Polling 3 subreddits with `limit=25` uses 3 requests per cycle. 1 cycle per minute = 3 req/min — well within limits.

---

### Pattern 2: sentiment_stream Flink Job (HOP Window + VADER)

**What:** PyFlink Table API job that consumes `reddit-raw`, applies VADER scoring per post, and aggregates per-ticker sentiment over a 1-min hop / 5-min window.

**Architecture note:** VADER scoring happens INSIDE a ScalarFunction UDF (one record at a time), NOT inside a UDAF. The UDAF only accumulates numeric scores. This is a clean architecture that separates scoring from aggregation.

**Key implementation pattern (replicate indicator_stream.py structure):**
```python
# Source: replicates indicator_stream.py HOP window structure + adds VADER ScalarFunction
from pyflink.table import EnvironmentSettings, TableEnvironment, DataTypes
from pyflink.table.udf import ScalarFunction, AggregateFunction, udf, udaf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()  # module-level singleton — thread-safe, no locking

class VaderScoreUdf(ScalarFunction):
    """Score a concatenated title+body text with VADER. Returns compound score −1..+1."""
    def eval(self, text: str) -> float:
        if not text:
            return 0.0
        scores = _analyzer.polarity_scores(str(text))
        return float(scores["compound"])  # −1.0 to +1.0

class AvgSentimentUdaf(AggregateFunction):
    """Accumulates (sum, count) of sentiment scores over HOP window."""
    def create_accumulator(self): return [0.0, 0]
    def accumulate(self, acc, score):
        if score is not None:
            acc[0] += float(score); acc[1] += 1
    def get_value(self, acc): return acc[0] / acc[1] if acc[1] > 0 else 0.0
    def get_accumulator_type(self): return DataTypes.ARRAY(DataTypes.DOUBLE())
    def get_result_type(self): return DataTypes.DOUBLE()

class MentionCountUdaf(AggregateFunction):
    """Counts records in window."""
    def create_accumulator(self): return [0]
    def accumulate(self, acc, val): acc[0] += 1 if val is not None else 0
    def get_value(self, acc): return acc[0]
    def get_accumulator_type(self): return DataTypes.ARRAY(DataTypes.INT())
    def get_result_type(self): return DataTypes.INT()

class PositiveRatioUdaf(AggregateFunction):
    """Ratio of posts with compound > 0.05."""
    def create_accumulator(self): return [0, 0]  # [positive_count, total]
    def accumulate(self, acc, score):
        if score is not None:
            acc[1] += 1
            if float(score) > 0.05: acc[0] += 1
    def get_value(self, acc): return acc[0] / acc[1] if acc[1] > 0 else 0.0
    def get_accumulator_type(self): return DataTypes.ARRAY(DataTypes.DOUBLE())
    def get_result_type(self): return DataTypes.DOUBLE()
```

**HOP window SQL (replicate indicator_stream.py pattern):**
```sql
-- Source: replicates indicator_stream.py HOP window TVF syntax
INSERT INTO sentiment_aggregated_sink
SELECT
    ticker,
    window_start AS window_start,
    window_end   AS window_end,
    avg_sentiment_udaf(compound_score) AS avg_sentiment,
    mention_count_udaf(compound_score) AS mention_count,
    positive_ratio_udaf(compound_score) AS positive_ratio,
    negative_ratio_udaf(compound_score) AS negative_ratio,
    FIRST_VALUE(subreddit)             AS top_subreddit
FROM TABLE(
    HOP(TABLE reddit_scored_source, DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE, INTERVAL '5' MINUTE)
)
GROUP BY ticker, window_start, window_end
```

**Key Flink table design:** The `reddit-raw` Kafka topic needs a preprocessing step. The job defines:
1. `reddit_raw_source` — Kafka source reading `reddit-raw` topic JSON: `{post_id, title, body, subreddit, created_utc, tickers: ARRAY<STRING>}`
2. An UNNEST step to expand the `tickers` array into one row per (post, ticker) pair
3. A VADER UDF applied to compute `compound_score` per row
4. A HOP window aggregation per ticker

**UNNEST pattern in Flink Table API SQL:**
```sql
-- UNNEST the tickers array so each ticker becomes a separate row
CREATE VIEW reddit_unnested AS
SELECT
    post_id,
    CAST(created_utc AS TIMESTAMP_LTZ(3)) AS event_time,
    subreddit,
    ticker,
    vader_score(CONCAT(title, ' ', body)) AS compound_score
FROM reddit_raw_source
CROSS JOIN UNNEST(tickers) AS t(ticker)
WHERE ARRAY_LENGTH(tickers) > 0
```

**IMPORTANT:** PyFlink 1.19 supports `UNNEST` for array columns via the Table API SQL. This pattern is confirmed to work in Flink 1.18+ with `CROSS JOIN UNNEST(array_col) AS alias(col_name)` syntax.

**Source schema for `reddit-raw`:**
```sql
CREATE TABLE reddit_raw_source (
    post_id      STRING,
    title        STRING,
    body         STRING,
    subreddit    STRING,
    created_utc  BIGINT,
    tickers      ARRAY<STRING>,
    event_time   AS TO_TIMESTAMP_LTZ(created_utc, 3),
    WATERMARK FOR event_time AS event_time - INTERVAL '30' SECONDS
) WITH (
    'connector'                    = 'kafka',
    'topic'                        = 'reddit-raw',
    'properties.bootstrap.servers' = '...',
    'properties.group.id'          = 'flink-sentiment-stream',
    'scan.startup.mode'            = 'group-offsets',
    'format'                       = 'json',
    'json.ignore-parse-errors'     = 'true'
)
```

**Sink schema for `sentiment-aggregated`:**
```sql
CREATE TABLE sentiment_aggregated_sink (
    ticker          STRING,
    window_start    TIMESTAMP(3),
    window_end      TIMESTAMP(3),
    avg_sentiment   DOUBLE,
    mention_count   INT,
    positive_ratio  DOUBLE,
    negative_ratio  DOUBLE,
    top_subreddit   STRING,
    PRIMARY KEY (ticker, window_start) NOT ENFORCED
) WITH (
    'connector'                    = 'upsert-kafka',
    'topic'                        = 'sentiment-aggregated',
    'properties.bootstrap.servers' = '...',
    'key.format'                   = 'json',
    'value.format'                 = 'json'
)
```

---

### Pattern 3: Strimzi KafkaTopic CRs

**Two new topics following the exact `kafka-topic-processed-features.yaml` pattern:**

```yaml
# Source: kafka-topics.yaml and kafka-topic-processed-features.yaml in codebase
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: reddit-raw
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 86400000   # 1 day — raw posts don't need long retention
    segment.bytes: 1073741824
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: sentiment-aggregated
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000   # 7 days — aggregated sentiment useful for replay
    segment.bytes: 1073741824
```

---

### Pattern 4: Feast FeatureView Addition — `reddit_sentiment_fv`

**What:** Add a new `PushSource` and `FeatureView` to `ml/feature_store/feature_repo.py`. Mirrors the `technical_indicators_push` / `technical_indicators_fv` pattern exactly.

```python
# Source: feature_repo.py existing pattern — add after technical_indicators_fv
from feast.types import Float64, Int64, String

# New PushSource for streaming sentiment aggregates
reddit_sentiment_push = PushSource(
    name="reddit_sentiment_push",
    batch_source=indicators_source,  # Reuse any existing batch source as placeholder — push-only in practice
)

# New FeatureView for Reddit sentiment
reddit_sentiment_fv = FeatureView(
    name="reddit_sentiment_fv",
    entities=[ticker],
    ttl=timedelta(minutes=10),  # Short TTL — sentiment data is ephemeral; stale if pipeline stops
    schema=[
        Field(name="avg_sentiment",   dtype=Float64),
        Field(name="mention_count",   dtype=Int64),
        Field(name="positive_ratio",  dtype=Float64),
        Field(name="negative_ratio",  dtype=Float64),
        Field(name="top_subreddit",   dtype=String),
        Field(name="window_start",    dtype=String),  # ISO8601 string
        Field(name="window_end",      dtype=String),
    ],
    online=True,
    source=indicators_source,  # Placeholder batch source (required by Feast API)
    stream_source=reddit_sentiment_push,
)
```

**Important note on `batch_source` placeholder:** Feast requires every FeatureView to have a `source` (batch source). For this phase, reuse any existing `PostgreSQLSource` as a placeholder. The FeatureView will only ever be populated via `store.push()` from the sentiment_writer job — the batch source is never queried. This is the same pattern used by Phase 67's `feast_writer.py` which pushes to `technical_indicators_fv`.

**After adding to `feature_repo.py`, run `feast apply`** to register the new FeatureView in the registry. The deploy-all.sh Phase 71 block should include this step.

---

### Pattern 5: sentiment_writer Flink Job

**What:** Direct copy of `feast_writer.py` with changed topic name (`sentiment-aggregated` instead of `processed-features`) and changed `push_source_name` (`reddit_sentiment_push` instead of `technical_indicators_push`).

```python
# Source: feast_writer.py — replicate exactly, change 3 things:
# 1. set_topics("sentiment-aggregated")  (was "processed-features")
# 2. set_group_id("flink-sentiment-writer")  (was "flink-feast-writer")
# 3. push_source_name="reddit_sentiment_push"  (was "technical_indicators_push")
# 4. df columns: ["ticker", "event_timestamp", "avg_sentiment", "mention_count",
#                 "positive_ratio", "negative_ratio", "top_subreddit",
#                 "window_start", "window_end"]

store.push(
    push_source_name="reddit_sentiment_push",
    df=df[["ticker", "event_timestamp", "avg_sentiment", "mention_count",
           "positive_ratio", "negative_ratio", "top_subreddit"]],
    to=PushMode.ONLINE,
)
```

**Dockerfile for sentiment_writer:** Exact copy of `feast_writer/Dockerfile` — same Python 3.10 upgrade path, same `feast[redis]==0.61.0` install. Only change: `COPY sentiment_writer.py /opt/flink/usrlib/sentiment_writer.py`.

---

### Pattern 6: FastAPI WebSocket Endpoint `/ws/sentiment/{ticker}`

**What:** A per-ticker WebSocket endpoint that wakes every 60 seconds, reads Feast Redis for the latest sentiment features for the requested ticker, and pushes JSON to the connected client.

**Key design difference from `/ws/prices`:** The prices endpoint uses a global `PriceBroadcaster` fan-out pattern (all subscribers get the same message). The sentiment endpoint uses a **per-connection loop** — each connection runs its own 60-second push cycle reading Feast for its specific ticker. This is simpler and more correct for per-ticker subscriptions.

**Pattern (add to `ws.py`):**
```python
# Source: ws.py existing /ws/prices pattern + feast_online_service.py pattern from Phase 70
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool
import asyncio
import logging

logger = logging.getLogger(__name__)

@router.websocket("/ws/sentiment/{ticker}")
async def ws_sentiment(websocket: WebSocket, ticker: str) -> None:
    """Push live sentiment data for a single ticker every 60 seconds."""
    await websocket.accept()
    ticker_upper = ticker.upper()
    logger.info("sentiment ws connected: ticker=%s client=%s", ticker_upper, websocket.client)

    async def _recv_loop() -> None:
        """Drain incoming client messages (ping/close detection)."""
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    recv_task = asyncio.create_task(_recv_loop())
    try:
        while True:
            # Read from Feast Redis (sync call wrapped in threadpool)
            features = await run_in_threadpool(get_sentiment_features_sync, ticker_upper)
            await websocket.send_json(features)
            await asyncio.sleep(60)  # aligns with 1-min HOP output rate
    except WebSocketDisconnect:
        pass
    finally:
        recv_task.cancel()
        logger.info("sentiment ws disconnected: ticker=%s", ticker_upper)
```

**`get_sentiment_features_sync(ticker)`** is a sync function (not async) that calls `FeatureStore.get_online_features()` — same as Phase 70 `feast_online_service.py` pattern. It reads the `reddit_sentiment_fv` feature view:

```python
# Source: feast_online_service.py Phase 70 pattern
def get_sentiment_features_sync(ticker: str) -> dict:
    """Synchronous Feast online read — called via run_in_threadpool from WS handler."""
    try:
        store = FeatureStore(repo_path=settings.FEAST_STORE_PATH)
        result = store.get_online_features(
            features=[
                "reddit_sentiment_fv:avg_sentiment",
                "reddit_sentiment_fv:mention_count",
                "reddit_sentiment_fv:positive_ratio",
                "reddit_sentiment_fv:negative_ratio",
                "reddit_sentiment_fv:top_subreddit",
            ],
            entity_rows=[{"ticker": ticker}],
        ).to_dict()
        return {
            "ticker": ticker,
            "avg_sentiment": (result.get("avg_sentiment") or [None])[0],
            "mention_count": (result.get("mention_count") or [None])[0],
            "positive_ratio": (result.get("positive_ratio") or [None])[0],
            "negative_ratio": (result.get("negative_ratio") or [None])[0],
            "top_subreddit": (result.get("top_subreddit") or [None])[0],
            "available": True,
            "sampled_at": datetime.utcnow().isoformat(),
        }
    except Exception:
        return {"ticker": ticker, "available": False, "sampled_at": None}
```

**Rate limit exemption:** The existing `RateLimitMiddleware` in `main.py` already exempts `/ws` paths (`exempt_paths=["/health", "/metrics", "/ws"]`). No change needed.

---

### Pattern 7: React `useSentimentSocket` Hook

**What:** A custom React hook that manages the WebSocket lifecycle for `/ws/sentiment/{ticker}`. Replaces the React Query polling approach used in Phase 70 — this is WebSocket push as locked in CONTEXT.md.

**Reuse `useWebSocket.ts` directly or create a thin wrapper:**

```typescript
// Source: useWebSocket.ts existing hook — thin wrapper for sentiment data
// File: src/hooks/useSentimentSocket.ts

import { useState, useEffect, useRef } from "react";
import type { WebSocketStatus } from "@/api/types";

export interface SentimentData {
  ticker: string;
  avg_sentiment: number | null;
  mention_count: number | null;
  positive_ratio: number | null;
  negative_ratio: number | null;
  top_subreddit: string | null;
  available: boolean;
  sampled_at: string | null;
}

export interface UseSentimentSocketReturn {
  data: SentimentData | null;
  status: WebSocketStatus;
}

export function useSentimentSocket(ticker: string | null): UseSentimentSocketReturn {
  const [data, setData] = useState<SentimentData | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 5;

  useEffect(() => {
    if (!ticker) {
      setStatus("disconnected");
      setData(null);
      return;
    }

    const wsBase = (import.meta.env.VITE_API_URL || "http://localhost:8000")
      .replace(/^http/, "ws");
    const url = `${wsBase}/ws/sentiment/${encodeURIComponent(ticker)}`;

    function connect() {
      setStatus("connecting");
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => { setStatus("connected"); retryCountRef.current = 0; };
      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as SentimentData;
          setData(parsed);
        } catch { /* ignore malformed */ }
      };
      ws.onerror = () => setStatus("error");
      ws.onclose = (e) => {
        setStatus("disconnected");
        wsRef.current = null;
        if (e.code !== 1000 && retryCountRef.current < MAX_RETRIES) {
          const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 30_000);
          retryCountRef.current += 1;
          setTimeout(connect, delay);  // exponential backoff
        }
      };
    }

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
    };
  }, [ticker]);

  return { data, status };
}
```

---

### Pattern 8: SentimentPanel.tsx React Component

**What:** MUI Accordion panel inside Dashboard Drawer — below `StreamingFeaturesPanel`. Displays `avg_sentiment` as a color-coded LinearProgress, `mention_count`, `positive_ratio`, `negative_ratio`, `top_subreddit`, and a freshness indicator.

```tsx
// Source: Phase 70 StreamingFeaturesPanel.tsx + Phase 69 FeatureFreshnessPanel.tsx patterns
import { Chip, Divider, LinearProgress, Paper, Skeleton, Stack, Typography } from "@mui/material";
import { useSentimentSocket } from "@/hooks/useSentimentSocket";

// Sentiment score to 0-100 scale for LinearProgress (−1 → 0, +1 → 100)
const scoreToPercent = (s: number | null): number =>
  s == null ? 50 : Math.round(((s + 1) / 2) * 100);

// Color: red < 40, yellow 40-60, green > 60
const progressColor = (pct: number): string => {
  if (pct < 40) return "#e05454";   // red — bearish
  if (pct < 60) return "#f59e0b";   // amber — neutral
  return "#22c983";                  // green — bullish
};

export default function SentimentPanel({ ticker }: { ticker: string }) {
  const { data, status } = useSentimentSocket(ticker);

  if (status === "connecting" || (status === "connected" && !data)) {
    return <Skeleton variant="rectangular" height={140} sx={{ borderRadius: 1 }} />;
  }

  if (!data?.available) {
    return (
      <Paper sx={{ p: 2, bgcolor: "rgba(10,14,25,0.6)" }}>
        <Typography variant="caption" color="text.secondary">
          Sentiment data unavailable — pipeline may be starting
        </Typography>
      </Paper>
    );
  }

  const pct = scoreToPercent(data.avg_sentiment);
  const color = progressColor(pct);

  return (
    <Paper sx={{ p: 2, bgcolor: "rgba(10,14,25,0.6)" }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="subtitle2" fontWeight={700} sx={{ fontFamily: '"Syne", sans-serif', fontSize: "0.68rem" }}>
          Reddit Sentiment
        </Typography>
        <Chip label="LIVE — Reddit" size="small" sx={{ bgcolor: "#22c983", color: "#000", fontSize: "0.6rem", height: 18 }} />
      </Stack>
      <Divider sx={{ mb: 1.5, borderColor: "rgba(232,164,39,0.1)" }} />
      {/* Sentiment gauge */}
      <Stack spacing={0.5} sx={{ mb: 1.5 }}>
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem" }}>
            Sentiment
          </Typography>
          <Typography variant="caption" sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem", color }}>
            {data.avg_sentiment != null ? data.avg_sentiment.toFixed(3) : "—"}
          </Typography>
        </Stack>
        <LinearProgress
          variant="determinate"
          value={pct}
          sx={{ height: 6, borderRadius: 3, bgcolor: "rgba(255,255,255,0.08)",
                "& .MuiLinearProgress-bar": { bgcolor: color, borderRadius: 3 } }}
        />
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.58rem" }}>Bearish −1</Typography>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.58rem" }}>Bullish +1</Typography>
        </Stack>
      </Stack>
      {/* Mention stats */}
      <Stack direction="row" spacing={2}>
        <Typography variant="caption" sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem" }}>
          Mentions: <strong>{data.mention_count ?? "—"}</strong>
        </Typography>
        <Typography variant="caption" sx={{ color: "#22c983", fontSize: "0.65rem" }}>
          +{((data.positive_ratio ?? 0) * 100).toFixed(0)}%
        </Typography>
        <Typography variant="caption" sx={{ color: "#e05454", fontSize: "0.65rem" }}>
          −{((data.negative_ratio ?? 0) * 100).toFixed(0)}%
        </Typography>
      </Stack>
      {data.top_subreddit && (
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.6rem" }}>
          Top: r/{data.top_subreddit}
        </Typography>
      )}
      {data.sampled_at && (
        <Typography variant="caption" color="text.disabled" sx={{ display: "block", fontSize: "0.58rem", mt: 0.5 }}>
          Updated: {new Date(data.sampled_at).toLocaleTimeString()}
        </Typography>
      )}
    </Paper>
  );
}
```

**Dashboard.tsx integration point:** Add below existing `DashboardTAPanel` accordion (which is already last in the Drawer):

```tsx
// In Dashboard.tsx — add after the existing Technical Indicators Accordion
{selectedTicker && (
  <Accordion sx={{ bgcolor: "#0d1220", mt: 1 }}>
    <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: "rgba(107,122,159,0.6)", fontSize: "1rem" }} />}
                      sx={{ minHeight: 40, "& .MuiAccordionSummary-content": { my: 0 } }}>
      <Typography sx={{ fontFamily: '"Syne", sans-serif', fontWeight: 700, fontSize: "0.68rem",
                        letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(107,122,159,0.8)" }}>
        Reddit Sentiment
      </Typography>
    </AccordionSummary>
    <AccordionDetails sx={{ pt: 0 }}>
      <SentimentPanel ticker={selectedTicker} />
    </AccordionDetails>
  </Accordion>
)}
```

---

### Pattern 9: FlinkDeployment CRs for sentiment_stream and sentiment_writer

**What:** Two new FlinkDeployment CRs following the exact `flinkdeployment-indicator-stream.yaml` and `flinkdeployment-feast-writer.yaml` patterns.

**Key settings to replicate:**
- `image: stock-flink-sentiment-stream:latest` / `stock-flink-sentiment-writer:latest`
- `imagePullPolicy: Never` (minikube local)
- `flinkVersion: v1_19`
- `state.checkpoints.dir: s3://model-artifacts/flink-checkpoints/sentiment-stream` (new path)
- `KAFKA_BOOTSTRAP_SERVERS` from `flink-config` ConfigMap (already has correct value)
- `FEAST_STORE_PATH: "/opt/feast"` (same as feast_writer)
- `parallelism: 1` (sufficient for Minikube dev; increase for prod)
- `execution.checkpointing.interval: "30s"` (same as existing jobs)
- `restart-strategy.type: exponential-delay` (same resilience pattern)

**MinIO checkpoint prefix:** The `minio-init-job.yaml` will need a new `flink-checkpoints/sentiment-stream/.keep` placeholder added, following the existing `flink-checkpoints/feast-writer` pattern.

---

### Pattern 10: Reddit Producer K8s Deployment

**What:** A K8s Deployment in the `ingestion` namespace (not a CronJob — must poll continuously).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reddit-producer
  namespace: ingestion
  labels:
    app: reddit-producer
    app.kubernetes.io/part-of: stock-prediction-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: reddit-producer
  template:
    spec:
      containers:
        - name: reddit-producer
          image: stock-reddit-producer:latest
          imagePullPolicy: Never
          envFrom:
            - configMapRef:
                name: reddit-producer-config
          env:
            - name: REDDIT_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: reddit-secrets
                  key: REDDIT_CLIENT_ID
            - name: REDDIT_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: reddit-secrets
                  key: REDDIT_CLIENT_SECRET
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
```

**ConfigMap** (`reddit-producer-config`): `KAFKA_BOOTSTRAP_SERVERS`, `SUBREDDITS=wallstreetbets,stocks,investing`, `POLL_INTERVAL_SECONDS=60`, `POST_LIMIT=25`.

**Secret** (`reddit-secrets`): `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` — created manually (not committed to Git).

### Anti-Patterns to Avoid

- **Do not run VADER inside a UDAF accumulate() call:** VADER scoring should happen in a ScalarFunction UDF applied per-row BEFORE the UDAF window aggregation. Running it inside `accumulate()` creates hidden state and makes testing harder.
- **Do not use a CronJob for the Reddit producer:** A CronJob restarts on a fixed schedule. The Reddit API polling loop must be a persistent Deployment with a `time.sleep(60)` loop — ensuring no posts are missed between CronJob invocations.
- **Do not reuse the global `PriceBroadcaster` for sentiment:** The sentiment WS endpoint uses a per-connection push loop (not fan-out). Using the broadcaster would push all tickers to all clients.
- **Do not block the Flink event loop with module-level VADER initialization:** VADER's `SentimentIntensityAnalyzer()` should be initialized at module level as a singleton, not inside the UDF's `eval()` method on every call.
- **Do not forget to run `feast apply` after adding `reddit_sentiment_fv`:** The new FeatureView must be registered in the Feast registry before the sentiment_writer job can call `store.push()` — if `feast apply` hasn't run, the push will fail with `FeatureViewNotFoundException`.
- **Do not use `event_timestamp` from `created_utc` without timezone awareness:** Reddit's `created_utc` is a Unix timestamp in UTC. Flink's watermarking requires `TIMESTAMP_LTZ` — use `TO_TIMESTAMP_LTZ(created_utc, 3)` in the source DDL. The `INTERVAL '30' SECONDS` watermark delay is correct for 1-minute polling.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reddit API access | Custom HTTP requests to Reddit API | PRAW 7.8.1 | PRAW handles OAuth2 token refresh, rate limiting, pagination, user-agent headers — all required by Reddit's API ToS |
| Sentiment scoring for social media | Custom lexicon or naive positive/negative word count | vaderSentiment 3.3.2 | VADER is specifically designed for social media: handles ALL CAPS, emoji, slang, negations, punctuation emphasis. Hand-rolled word lists are < 70% accurate on Reddit posts |
| Flink UDF for text scoring | Attempting to use HuggingFace transformers in PyFlink | VADER ScalarFunction UDF | GPU models cannot run inside PyFlink UDFs without sidecars; VADER runs in-process in <0.5ms per post |
| Feast Redis key format | Direct Redis HGET with custom key format | `FeatureStore.get_online_features()` | Feast's internal Redis key format is versioned — Phase 70 pitfall confirmed in research |
| WebSocket reconnect logic | Custom exponential backoff with jitter | Pattern from `useWebSocket.ts` | Existing hook already implements reconnect with linear backoff; `useSentimentSocket` extends the same pattern |

**Key insight:** VADER was the correct choice. It requires no model download, no GPU, no inference server — just `pip install vaderSentiment`. It runs in <1ms per call, making it viable inside a PyFlink ScalarFunction UDF at high throughput.

---

## Common Pitfalls

### Pitfall 1: VADER Import Fails Inside Flink Worker JVM

**What goes wrong:** `from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer` raises `ModuleNotFoundError` when the PyFlink job submits the UDF to worker nodes.

**Why it happens:** PyFlink UDF functions run in a Python subprocess spawned by the JVM. If `PYFLINK_PYTHON` is not set to the correct Python binary that has vaderSentiment installed, the import fails.

**How to avoid:** Set `ENV PYFLINK_PYTHON=/usr/bin/python3.10` in the Dockerfile (matching `feast_writer/Dockerfile` pattern). Verify `pip3.10 install vaderSentiment` in the Dockerfile — not the system pip. Test with: `python3.10 -c "from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer; print('ok')"`.

**Warning signs:** Flink TaskManager logs show `ModuleNotFoundError: No module named 'vaderSentiment'`.

---

### Pitfall 2: Flink UNNEST on ARRAY<STRING> Fails With JSON Deserialization

**What goes wrong:** The `reddit-raw` topic contains `"tickers": ["AAPL", "MSFT"]` as a JSON array. Flink's JSON format deserializer may fail to map this to `ARRAY<STRING>` if the format config is missing.

**Why it happens:** PyFlink's Kafka JSON source requires `'json.ignore-parse-errors' = 'true'` to handle missing or malformed array fields gracefully. Posts with no tickers should be filtered out, not crash the job.

**How to avoid:** Use `'json.ignore-parse-errors' = 'true'` in the source DDL (same as `indicator_stream.py`). Add a `WHERE ARRAY_LENGTH(tickers) > 0` guard in the UNNEST view. Test with a mock message containing `"tickers": []` and `"tickers": null`.

**Warning signs:** Flink job logs show `org.apache.flink.formats.json.JsonRowDeserializationSchema` parse errors at high rate.

---

### Pitfall 3: Reddit PRAW Rate Limiting — 429 Too Many Requests

**What goes wrong:** After running for a while, the Reddit producer starts receiving HTTP 429 responses and stops producing to Kafka.

**Why it happens:** PRAW's `subreddit.new(limit=25)` makes one API call per subreddit. With 3 subreddits × 1 poll per minute = 3 req/min, this is well within the 60 req/min authenticated limit. However, PRAW's authenticated session expires after 1 hour (OAuth2 token TTL). If token refresh fails, subsequent requests fail with 401/429.

**How to avoid:** Use `praw.Reddit(read_only=True)` which uses the simpler script-type app authentication with client credentials (no user session). PRAW automatically refreshes credentials. Add retry logic: `tenacity.retry(stop=stop_after_attempt(3), wait=wait_exponential())` around the `subreddit.new()` call.

**Warning signs:** Producer logs show `prawcore.exceptions.ResponseException: received 429 HTTP response`.

---

### Pitfall 4: Feast FeatureView TTL Too Long — Stale Sentiment Shows as Fresh

**What goes wrong:** The `reddit_sentiment_fv` TTL is set to 365 days (matching `technical_indicators_fv`). A ticker with no recent Reddit activity will show stale sentiment data (from days ago) as if it were current.

**Why it happens:** Feast's online store only evicts records when TTL expires. Long TTL means old values persist indefinitely in Redis.

**How to avoid:** Set `ttl=timedelta(minutes=10)` for `reddit_sentiment_fv`. This means: if the Flink job hasn't pushed a new window in the last 10 minutes, Feast returns `None` for all fields — and the WebSocket sends `available=False`. The `SentimentPanel` then shows the "pipeline may be starting" message, which is correct.

**Warning signs:** SentimentPanel shows non-null sentiment values for a ticker that hasn't been mentioned on Reddit in days.

---

### Pitfall 5: WebSocket Connection Per Ticker Leaks When Drawer Closes

**What goes wrong:** The `useSentimentSocket` hook doesn't clean up the WebSocket when the Dashboard drawer closes, leaving zombie connections open.

**Why it happens:** React `useEffect` cleanup must close the WebSocket. If the ticker prop changes (drawer switches from AAPL to MSFT) without `null` in between, a new connection is opened before the old one closes.

**How to avoid:** The `useSentimentSocket` `useEffect` must list `ticker` as a dependency AND close the existing connection at the start of the cleanup function. The implementation above uses `ws.close(1000)` in the effect cleanup — verify this is called on both unmount AND ticker change.

**Warning signs:** Browser DevTools Network tab shows multiple open WebSocket connections to `/ws/sentiment/AAPL` and `/ws/sentiment/MSFT` simultaneously.

---

### Pitfall 6: MinIO Checkpoint Prefix Missing for New Flink Jobs

**What goes wrong:** `sentiment-stream` and `sentiment-writer` FlinkDeployment CRs fail to start because MinIO doesn't have the `flink-checkpoints/sentiment-stream/` and `flink-checkpoints/sentiment-writer/` prefixes.

**Why it happens:** MinIO has no directory concept — write operations to a prefix that doesn't exist create the prefix implicitly. But Flink's RocksDB checkpoint writer does a prefix-listing check first and fails if no objects exist under the prefix.

**How to avoid:** Add placeholder object creation to `minio-init-job.yaml` — same pattern as existing `flink-checkpoints/.keep`:
```bash
echo "" | mc pipe local/model-artifacts/flink-checkpoints/sentiment-stream/.keep
echo "" | mc pipe local/model-artifacts/flink-checkpoints/sentiment-writer/.keep
```

---

### Pitfall 7: `feast apply` Must Be Run After Adding `reddit_sentiment_fv`

**What goes wrong:** `sentiment_writer` job starts and calls `store.push("reddit_sentiment_push", ...)` but Feast raises `FeatureViewNotFoundException: reddit_sentiment_fv`.

**Why it happens:** `feast apply` registers FeatureView definitions in the Feast SQL registry (the `feast_metadata` PostgreSQL table). If `feature_repo.py` is updated but `feast apply` isn't re-run, the registry is stale.

**How to avoid:** Include a `feast apply` step in the deploy-all.sh Phase 71 block, pointing to `ml/feature_store/`:
```bash
kubectl exec -n ml deploy/ml-serving -- feast -c /opt/feast apply
```
Or run it via a one-shot K8s Job after updating the feature_repo ConfigMap.

---

## Code Examples

### Pydantic Schema addition (schemas.py)

```python
# Source: schemas.py existing patterns + Phase 70 StreamingFeaturesResponse
class SentimentFeaturesResponse(BaseModel):
    ticker: str
    avg_sentiment: float | None = None
    mention_count: int | None = None
    positive_ratio: float | None = None
    negative_ratio: float | None = None
    top_subreddit: str | None = None
    available: bool = False
    sampled_at: str | None = None   # ISO8601
```

### TypeScript Interface (types.ts addition)

```typescript
// Source: Phase 70 StreamingFeaturesResponse pattern
export interface SentimentData {
  ticker: string;
  avg_sentiment: number | null;
  mention_count: number | null;
  positive_ratio: number | null;
  negative_ratio: number | null;
  top_subreddit: string | null;
  available: boolean;
  sampled_at: string | null;
}
```

### VADER scoring test (unit test pattern)

```python
# Source: test_feast_writer.py sys.modules mock pattern
import sys
from unittest.mock import MagicMock, patch

# Test VADER scoring logic directly — no Flink runtime needed
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def test_vader_scores_wsb_post():
    analyzer = SentimentIntensityAnalyzer()
    # Typical WSB post — VADER should score positively
    text = "AAPL to the MOON!! 🚀🚀 This stock is absolutely AMAZING!!"
    scores = analyzer.polarity_scores(text)
    assert scores["compound"] > 0.5  # strongly positive

def test_vader_scores_bearish_post():
    text = "This company is garbage. Going to zero. SELL SELL SELL."
    scores = analyzer.polarity_scores(text)
    assert scores["compound"] < -0.3  # negative
```

### PRAW ticker extraction test

```python
import re

TICKER_RE = re.compile(r'\$([A-Z]{1,5})\b')
BLOCKLIST = {"IT", "A", "AT", "BE", "GO", "OR"}

def extract_tickers(text: str, sp500_set: set) -> list:
    found = set()
    for m in TICKER_RE.finditer(text or ""):
        t = m.group(1)
        if t in sp500_set and t not in BLOCKLIST:
            found.add(t)
    return sorted(found)

def test_extract_dollar_sign_ticker():
    sp500 = {"AAPL", "MSFT", "TSLA"}
    result = extract_tickers("$AAPL is going to $TSLA levels!", sp500)
    assert "AAPL" in result
    assert "TSLA" in result

def test_blocklist_filters_common_words():
    sp500 = {"A", "IT", "AAPL"}
    result = extract_tickers("$A $IT company AT the top", sp500)
    assert "A" not in result
    assert "IT" not in result
    assert "AAPL" not in result  # "AAPL" not in text
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No alternative data in pipeline | Reddit PRAW → Kafka → Flink → Feast → Dashboard | Phase 71 | Live retail sentiment per S&P 500 ticker; dashboard surfaces crowd-sourced signals |
| Polling HTTP endpoint for live features (Phase 70) | WebSocket push for sentiment (Phase 71) | Phase 71 | Sentiment arrives exactly when Flink window closes; no wasted polling between windows |
| Single shared broadcaster for WS (Phase 45) | Per-ticker WS push loop for sentiment | Phase 71 | More efficient: clients only receive data for their selected ticker |
| Feast TTL=365 days for technical indicators | Short TTL=10 min for sentiment FeatureView | Phase 71 | Sentiment without recent pipeline activity returns null instead of stale days-old data |

**Deprecated / not applicable:**
- Using `praw.Reddit(username=..., password=...)` personal account: Reddit deprecated personal account access in 2023 for bots. Use script-type app with `read_only=True`.

---

## Open Questions

1. **Reddit PRAW credentials — how are they provided at deploy time?**
   - What we know: The K8s Deployment requires `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` from a K8s Secret. The secret must be created manually before deployment.
   - What's unclear: Whether there is a test/dev Reddit app registered for this project.
   - Recommendation: Treat as a manual pre-step. Document in deploy-all.sh with a guard: `if kubectl get secret reddit-secrets -n ingestion >/dev/null 2>&1; then ...`. The plan should include a task for creating the Reddit app.

2. **`feast apply` trigger location in deploy-all.sh**
   - What we know: `feast apply` must be run after `feature_repo.py` is updated, pointing to the mounted `/opt/feast` directory. In Minikube, this is either via a K8s Job or `kubectl exec` into the API pod.
   - What's unclear: Whether the API pod has the `feast` CLI available (it has `feast[redis]` installed).
   - Recommendation: Run `feast apply` via `kubectl exec -n ingestion deploy/stock-api -- python -c "from feast import FeatureStore; FeatureStore('/opt/feast').apply()"`. The API pod already has `feast` installed.

3. **Should `sentiment_stream` compute `negative_ratio` separately or derive it as `1 - positive_ratio - neutral_ratio`?**
   - What we know: CONTEXT.md specifies separate `positive_ratio` and `negative_ratio` fields. VADER's compound score < −0.05 = negative, > 0.05 = positive, between = neutral.
   - Recommendation: Compute `negative_ratio` as its own UDAF (mirroring `positive_ratio` but with threshold < −0.05). This gives independent counts in case of rounding/neutrals.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (existing test infrastructure in `services/api/tests/`) |
| Config file | `pytest.ini` or `pyproject.toml` in `stock-prediction-platform/services/api/` |
| Quick run command | `cd /home/tempa/Desktop/priv-project/stock-prediction-platform && pytest services/api/tests/test_sentiment.py -x -q` |
| Full suite command | `cd /home/tempa/Desktop/priv-project/stock-prediction-platform && pytest services/api/tests/ -x -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SENT-01 | Reddit PRAW ticker extraction correctly identifies S&P 500 tickers and filters blocklist | unit | `pytest tests/test_sentiment.py::test_extract_tickers -x` | No — Wave 0 |
| SENT-02 | VADER scoring returns positive/negative/neutral correctly for WSB-style text | unit | `pytest tests/test_sentiment.py::test_vader_scoring -x` | No — Wave 0 |
| SENT-03 | `get_sentiment_features_sync("AAPL")` returns correct fields from mocked Feast | unit | `pytest tests/test_sentiment.py::test_get_sentiment_features -x` | No — Wave 0 |
| SENT-04 | `get_sentiment_features_sync("AAPL")` returns `available=False` when Feast raises | unit | `pytest tests/test_sentiment.py::test_get_sentiment_features_unavailable -x` | No — Wave 0 |
| SENT-05 | `/ws/sentiment/AAPL` WebSocket connects, receives JSON with correct schema | integration/smoke | Manual verification or Playwright | No — Wave 0 |
| SENT-06 | `SentimentPanel` renders LinearProgress and mention count when data available | component | Playwright `tests/dashboard.spec.ts::SentimentPanel` extension | Extend existing |
| SENT-07 | `SentimentPanel` shows fallback message when `available=false` | component | Playwright | Extend existing |

### Sampling Rate

- **Per task commit:** `cd /home/tempa/Desktop/priv-project/stock-prediction-platform && pytest services/api/tests/test_sentiment.py -x -q`
- **Per wave merge:** `cd /home/tempa/Desktop/priv-project/stock-prediction-platform && pytest services/api/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `stock-prediction-platform/services/api/tests/test_sentiment.py` — covers SENT-01 through SENT-04 (producer ticker extraction, VADER scoring, Feast service)
- [ ] `stock-prediction-platform/services/reddit-producer/sp500_tickers.py` — needed for ticker extraction test
- [ ] `stock-prediction-platform/services/flink-jobs/sentiment_stream/sentiment_stream.py` — Flink job (created during implementation)
- [ ] `stock-prediction-platform/services/flink-jobs/sentiment_writer/sentiment_writer.py` — Flink writer (created during implementation)
- [ ] `stock-prediction-platform/services/frontend/src/hooks/useSentimentSocket.ts` — WS hook (created during implementation)
- [ ] `stock-prediction-platform/services/frontend/src/components/dashboard/SentimentPanel.tsx` — component (created during implementation)

---

## Sources

### Primary (HIGH confidence)
- `stock-prediction-platform/services/flink-jobs/indicator_stream/indicator_stream.py` — HOP window structure to replicate for `sentiment_stream.py`
- `stock-prediction-platform/services/flink-jobs/feast_writer/feast_writer.py` — Feast push pattern to replicate for `sentiment_writer.py`
- `stock-prediction-platform/services/flink-jobs/feast_writer/Dockerfile` — Python 3.10 upgrade path for Flink Dockerfile with feast[redis]
- `stock-prediction-platform/ml/feature_store/feature_repo.py` — `technical_indicators_fv` + `PushSource` pattern for `reddit_sentiment_fv`
- `stock-prediction-platform/services/api/app/routers/ws.py` — per-connection WebSocket loop to replicate for `/ws/sentiment/{ticker}`
- `stock-prediction-platform/services/api/app/services/price_feed.py` — `run_in_executor` pattern for sync Feast calls in async handlers
- `stock-prediction-platform/services/api/app/main.py` — `/ws` paths already exempted from rate limiting
- `stock-prediction-platform/services/api/app/config.py` — Settings pattern for new REDDIT_ config vars
- `stock-prediction-platform/k8s/flink/flinkdeployment-indicator-stream.yaml` — FlinkDeployment CR structure to replicate
- `stock-prediction-platform/k8s/kafka/kafka-topic-processed-features.yaml` — Strimzi KafkaTopic CR pattern
- `stock-prediction-platform/services/frontend/src/hooks/useWebSocket.ts` — reconnect + cleanup pattern for `useSentimentSocket.ts`
- `stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx` — Drawer + Accordion integration point
- `.planning/phases/70-display-flink-computed-streaming-features-in-the-dashboard/70-RESEARCH.md` — Feast online read pattern, `run_in_threadpool` pitfall, Phase 70 StreamingFeaturesPanel skeleton

### Secondary (MEDIUM confidence)
- PyPI registry: praw==7.8.1 (verified 2026-03-31), vaderSentiment==3.3.2 (verified 2026-03-31)
- Flink 1.19 `CROSS JOIN UNNEST(array_col) AS alias(col_name)` SQL syntax — confirmed working in PyFlink 1.18+; MEDIUM because not verified via Context7 but consistent with Flink SQL docs for array UNNEST

### Tertiary (LOW confidence)
- Reddit API OAuth2 token refresh via PRAW `read_only=True` — behavior documented in PRAW docs but not independently verified against current Reddit API ToS (2026)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PRAW 7.8.1 and vaderSentiment 3.3.2 verified from PyPI; all other libraries already pinned in codebase
- Architecture: HIGH — all patterns grounded in deployed codebase (Phases 45/66/67/70); only UNNEST syntax is MEDIUM
- Pitfalls: HIGH — Flink Python env pitfall (PYFLINK_PYTHON), Feast TTL, MinIO prefix, and WS cleanup are all confirmed from Phase 67/70 codebase analysis

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (praw and vaderSentiment are stable; Flink 1.19 and feast 0.61.0 are pinned)
