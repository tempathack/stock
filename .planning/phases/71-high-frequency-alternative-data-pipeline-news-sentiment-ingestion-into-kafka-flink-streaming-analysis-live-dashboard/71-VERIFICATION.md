---
phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard
verified: 2026-03-31T09:45:00Z
status: human_needed
score: 14/14 must-haves verified
human_verification:
  - test: "Start the frontend dev server (npm run dev from services/frontend), navigate to Dashboard, click a stock, expand the 'Reddit Sentiment' Accordion in the Drawer"
    expected: "Accordion renders without crash. Shows either Skeleton rows or 'Sentiment data unavailable — pipeline may be starting' message. No React error overlays. No TypeScript/React errors in DevTools console."
    why_human: "Visual rendering, Drawer interaction, and React error overlay detection cannot be verified programmatically without a running browser"
  - test: "With the full pipeline running (Kafka, Flink jobs, Feast Redis), wait for sentiment data and observe SentimentPanel in the Dashboard Drawer"
    expected: "LinearProgress gauge renders in red/amber/green depending on avg_sentiment value. Mention count, positive/negative ratio, and top subreddit are populated. Chip shows 'LIVE — Reddit'. Updated timestamp appears."
    why_human: "End-to-end pipeline sentiment data flow and live gauge rendering requires a running cluster environment"
---

# Phase 71 Verification Report: High-Frequency Alternative Data Pipeline

**Phase Goal:** Build a high-frequency alternative data pipeline — Reddit PRAW producer ingesting posts to Kafka, Flink jobs scoring with VADER and aggregating sentiment, FastAPI WebSocket endpoint serving real-time sentiment, and a SentimentPanel React component in the Dashboard Drawer.
**Verified:** 2026-03-31T09:45:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Two Strimzi KafkaTopic CRs exist for reddit-raw (1-day retention) and sentiment-aggregated (7-day retention) | VERIFIED | `kafka-topic-reddit.yaml` contains exactly 2 `kind: KafkaTopic` CRs; `retention.ms: 86400000` and `retention.ms: 604800000` confirmed |
| 2 | reddit_producer.py polls 3 subreddits, extracts tickers via SP500_SET + BLOCKLIST, publishes to reddit-raw topic | VERIFIED | `def extract_tickers`, `def poll_subreddit`, `REDDIT_TOPIC = "reddit-raw"`, `topic=REDDIT_TOPIC` produce call all present |
| 3 | K8s Deployment for reddit-producer wired with ConfigMap and Secret via envFrom | VERIFIED | Deployment YAML contains `configMapRef: name: reddit-producer-config` and `secretRef: name: reddit-secrets` |
| 4 | sentiment_stream Flink job reads reddit-raw, applies VADER UDF, aggregates with HOP(1min, 5min), outputs to sentiment-aggregated | VERIFIED | `class VaderScoreUdf`, `class AvgSentimentUdaf`, `topic = 'reddit-raw'` source, `topic = 'sentiment-aggregated'` sink, `HOP(TABLE reddit_unnested, DESCRIPTOR(event_time), INTERVAL '1' MINUTE, INTERVAL '5' MINUTE)` all present |
| 5 | sentiment_writer Flink job reads sentiment-aggregated and pushes to Feast Redis via reddit_sentiment_push | VERIFIED | `.set_topics("sentiment-aggregated")`, `.set_group_id("flink-sentiment-writer")`, `push_source_name="reddit_sentiment_push"` all present |
| 6 | feature_repo.py has reddit_sentiment_push PushSource and reddit_sentiment_fv FeatureView with all 5 fields | VERIFIED | `reddit_sentiment_push = PushSource(...)`, `reddit_sentiment_fv = FeatureView(...)` with `avg_sentiment`, `mention_count`, `positive_ratio`, `negative_ratio`, `top_subreddit` fields and `stream_source=reddit_sentiment_push`; single `from feast.types import` confirmed |
| 7 | Two FlinkDeployment CRs exist for sentiment-stream and sentiment-writer with correct images and checkpoint paths | VERIFIED | `name: sentiment-stream`, `image: stock-flink-sentiment-stream:latest`; `name: sentiment-writer`, `image: stock-flink-sentiment-writer:latest`, `FEAST_STORE_PATH` env var present in writer CR |
| 8 | GET /ws/sentiment/{ticker} WebSocket endpoint registered, pushes Feast sentiment every 60s, handles disconnect | VERIFIED | `@router.websocket("/ws/sentiment/{ticker}")` registered; `await asyncio.sleep(60)` in push loop; `run_in_threadpool(_get_sentiment_sync, ticker_upper)` call wired to Feast service; `ws_prices` endpoint preserved (no regression) |
| 9 | feast_online_service.get_sentiment_features(ticker) reads reddit_sentiment_fv from Feast Redis, returns available=False on exception | VERIFIED | `def get_sentiment_features(ticker: str) -> dict:` reads `reddit_sentiment_fv:avg_sentiment` and 4 other fields; exception handler returns `available: False` with all-None values |
| 10 | SentimentFeaturesResponse Pydantic schema with 7 fields defined in schemas.py | VERIFIED | `class SentimentFeaturesResponse(BaseModel):` with ticker, avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit, available, sampled_at |
| 11 | Unit tests exist for ws_sentiment endpoint and get_sentiment_features service | VERIFIED | `test_sentiment_ws.py` contains `class TestGetSentimentFeatures` (3 test cases) and `class TestWsSentimentEndpoint` (2 smoke tests); local `client` fixture defined; autouse monkeypatch fixture prevents 60s hang |
| 12 | useSentimentSocket hook opens /ws/sentiment/{ticker}, reconnects with exponential backoff (max 5 retries), closes on unmount | VERIFIED | `new WebSocket(url)` with URL pattern `${wsBase}/ws/sentiment/${encodeURIComponent(ticker)}`; `MAX_RETRIES = 5`; `Math.pow(2, retryCountRef.current)` backoff; `ws.close(1000)` cleanup |
| 13 | SentimentPanel shows Skeleton while connecting, unavailable state, LinearProgress gauge with red/amber/green thresholds; LIVE Reddit Chip present | VERIFIED | Skeleton rendered during connecting state; "Sentiment data unavailable" fallback; `LinearProgress` with `#e05454` / `#f59e0b` / `#22c983` thresholds; `label="LIVE — Reddit"` Chip present |
| 14 | Dashboard.tsx stock detail Drawer has Reddit Sentiment Accordion containing SentimentPanel; SentimentPanel exported from index.ts | VERIFIED | `import { ..., SentimentPanel }` in Dashboard.tsx; `<SentimentPanel ticker={selectedTicker} />` inside `Reddit Sentiment` Accordion; `export { default as SentimentPanel }` in index.ts |

**Score:** 14/14 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `stock-prediction-platform/k8s/kafka/kafka-topic-reddit.yaml` | Two Strimzi KafkaTopic CRs | VERIFIED | 2 CRs; reddit-raw 86400000ms, sentiment-aggregated 604800000ms |
| `stock-prediction-platform/services/reddit-producer/reddit_producer.py` | PRAW polling loop with extract_tickers and poll_subreddit | VERIFIED | Both functions present; produces to `REDDIT_TOPIC = "reddit-raw"` |
| `stock-prediction-platform/services/reddit-producer/sp500_tickers.py` | SP500_SET and BLOCKLIST exports | VERIFIED | Both sets defined and exported |
| `stock-prediction-platform/k8s/ingestion/reddit-producer-deployment.yaml` | K8s Deployment in ingestion namespace | VERIFIED | configMapRef and secretRef present |
| `stock-prediction-platform/k8s/ingestion/reddit-producer-configmap.yaml` | ConfigMap with Kafka bootstrap + poll config | VERIFIED | File exists |
| `stock-prediction-platform/services/flink-jobs/sentiment_stream/sentiment_stream.py` | HOP window job with VaderScoreUdf and 4 UDAFs | VERIFIED | All UDF/UDAF classes present; reddit-raw source and sentiment-aggregated sink wired |
| `stock-prediction-platform/services/flink-jobs/sentiment_writer/sentiment_writer.py` | Feast push job consuming sentiment-aggregated | VERIFIED | `reddit_sentiment_push`, `sentiment-aggregated`, `flink-sentiment-writer` all present |
| `stock-prediction-platform/ml/feature_store/feature_repo.py` | Extended with reddit_sentiment_fv and reddit_sentiment_push | VERIFIED | Both present; single feast.types import (no duplicate) |
| `stock-prediction-platform/k8s/flink/flinkdeployment-sentiment-stream.yaml` | FlinkDeployment CR for sentiment-stream | VERIFIED | Correct image and job path |
| `stock-prediction-platform/k8s/flink/flinkdeployment-sentiment-writer.yaml` | FlinkDeployment CR for sentiment-writer | VERIFIED | Correct image, job path, FEAST_STORE_PATH env var |
| `stock-prediction-platform/services/api/app/routers/ws.py` | /ws/sentiment/{ticker} WebSocket endpoint added | VERIFIED | Route registered; ws_prices preserved (no regression) |
| `stock-prediction-platform/services/api/app/services/feast_online_service.py` | get_sentiment_features reading reddit_sentiment_fv | VERIFIED | Function reads 5 fields; graceful fallback on exception |
| `stock-prediction-platform/services/api/app/models/schemas.py` | SentimentFeaturesResponse schema | VERIFIED | Class present with 7 fields |
| `stock-prediction-platform/services/api/tests/test_sentiment_ws.py` | Unit tests for WS endpoint and service | VERIFIED | 5 tests in 2 test classes; autouse fixture prevents blocking |
| `stock-prediction-platform/services/frontend/src/hooks/useSentimentSocket.ts` | useSentimentSocket hook with exponential backoff | VERIFIED | MAX_RETRIES=5, Math.pow backoff, ws.close(1000) cleanup |
| `stock-prediction-platform/services/frontend/src/components/dashboard/SentimentPanel.tsx` | MUI sentiment panel with gauge and states | VERIFIED | Skeleton, unavailable state, LinearProgress, LIVE chip, color thresholds |
| `stock-prediction-platform/services/frontend/src/components/dashboard/index.ts` | SentimentPanel re-export | VERIFIED | `export { default as SentimentPanel }` present |
| `stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx` | Reddit Sentiment Accordion in Drawer | VERIFIED | Accordion with SentimentPanel wired to selectedTicker |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `reddit_producer.py` | reddit-raw Kafka topic | `topic=REDDIT_TOPIC` where `REDDIT_TOPIC = "reddit-raw"` | WIRED | Line 34 and 76 of reddit_producer.py |
| `reddit-producer-deployment.yaml` | `reddit-producer-configmap.yaml` | `configMapRef: name: reddit-producer-config` | WIRED | configMapRef present in Deployment spec |
| `sentiment_stream.py` | reddit-raw Kafka topic | `'topic' = 'reddit-raw'` in Flink SQL DDL | WIRED | Source table DDL confirmed |
| `sentiment_stream.py` | sentiment-aggregated Kafka topic | `'topic' = 'sentiment-aggregated'` in upsert-kafka DDL | WIRED | Sink table DDL confirmed |
| `sentiment_writer.py` | Feast Redis | `push_source_name="reddit_sentiment_push"` | WIRED | store.push call confirmed |
| `feature_repo.py` | reddit_sentiment_fv | `FeatureView(stream_source=reddit_sentiment_push)` | WIRED | stream_source wiring confirmed |
| `ws.py /ws/sentiment/{ticker}` | `feast_online_service.get_sentiment_features` | `run_in_threadpool(_get_sentiment_sync, ticker_upper)` where `_get_sentiment_sync` imports and calls `get_sentiment_features` | WIRED | Both functions present and connected via threadpool |
| `feast_online_service.get_sentiment_features` | Feast Redis | `store.get_online_features(features=['reddit_sentiment_fv:avg_sentiment', ...])` | WIRED | All 5 fields read from redis store |
| `Dashboard.tsx` | `SentimentPanel.tsx` | `import { SentimentPanel } from '@/components/dashboard'` | WIRED | Import present; `<SentimentPanel ticker={selectedTicker} />` in Drawer |
| `SentimentPanel.tsx` | `useSentimentSocket.ts` | `const { data, status } = useSentimentSocket(ticker)` | WIRED | Hook imported and called at component top |
| `useSentimentSocket.ts` | `/ws/sentiment/{ticker}` endpoint | `` `${wsBase}/ws/sentiment/${encodeURIComponent(ticker)}` `` | WIRED | URL construction confirmed |

---

## Anti-Patterns Found

No anti-patterns found across all key phase 71 files. No TODO/FIXME/PLACEHOLDER comments, no stub return values (return null, return {}, Not implemented), no empty implementations.

---

## Human Verification Required

### 1. Reddit Sentiment Accordion Visual Render

**Test:** Start the frontend dev server (`npm run dev` from `stock-prediction-platform/services/frontend`), navigate to the Dashboard page, click any stock ticker to open the stock detail Drawer, scroll to find and expand the "Reddit Sentiment" Accordion at the bottom.
**Expected:** The Accordion expands without any JavaScript crash or React error overlay. Content shows either MUI Skeleton placeholder rows (during WebSocket connecting state) or the "Sentiment data unavailable — pipeline may be starting" message. No blank/empty section, no console errors related to SentimentPanel.
**Why human:** Visual rendering and React error overlay detection cannot be verified programmatically. The Drawer interaction and component mount behavior must be observed in a browser.

### 2. End-to-End Sentiment Data Flow

**Test:** With the full pipeline running (Kafka, reddit-producer Deployment, Flink sentiment-stream + sentiment-writer jobs, Feast Redis), open Dashboard, click a stock ticker with Reddit mentions (e.g. AAPL, NVDA, TSLA), and expand the Reddit Sentiment Accordion.
**Expected:** After up to 5 minutes (first HOP window), the LinearProgress gauge appears with a color reflecting the avg_sentiment value (red if bearish, amber if neutral, green if bullish). Mention count, positive/negative ratio percentages, top subreddit label, and "Updated:" timestamp all populate. The "LIVE — Reddit" green Chip is visible.
**Why human:** End-to-end data flow through Kafka, Flink, and Feast Redis requires a running cluster environment. Live gauge color, label values, and timestamp freshness cannot be asserted statically.

---

## Gaps Summary

None. All 14 observable truths verified programmatically. All 18 artifacts exist and contain substantive implementations (not stubs). All 11 key links are wired end-to-end.

Two items remain for human verification: the visual render of the SentimentPanel in the Dashboard Drawer, and the end-to-end pipeline data flow. These require a running environment and cannot block automated verification.

---

_Verified: 2026-03-31T09:45:00Z_
_Verifier: Claude (gsd-verifier)_
