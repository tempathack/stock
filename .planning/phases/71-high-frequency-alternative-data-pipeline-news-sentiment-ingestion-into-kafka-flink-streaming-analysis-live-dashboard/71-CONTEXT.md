# Phase 71: High-Frequency Alternative Data Pipeline — Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a high-frequency alternative data pipeline that ingests Reddit sentiment posts (r/wallstreetbets, r/stocks, r/investing) into Kafka, processes them with a new Flink job using VADER sentiment scoring, aggregates per-ticker sentiment in rolling time windows, persists results to the Feast Redis online store, and streams live sentiment data to the dashboard frontend via WebSocket — displayed as a new SentimentPanel inside the existing Dashboard stock detail drawer.

New capabilities: Reddit PRAW producer, `reddit-raw` and `sentiment-aggregated` Kafka topics, `sentiment_stream` Flink job (VADER scoring + HOP windowing), new Feast FeatureView for sentiment, new FastAPI WebSocket endpoint `/ws/sentiment/{ticker}`, `SentimentPanel.tsx` React component inside Dashboard drawer.

</domain>

<decisions>
## Implementation Decisions

### Data Sources
- **Source:** Reddit via PRAW — subreddits: r/wallstreetbets, r/stocks, r/investing
- **Ticker extraction:** Regex matching on post title + body — pattern `\$([A-Z]{1,5})` plus direct uppercase match against S&P 500 ticker list; maintain a blocklist for common false positives (IT, A, AT, BE, GO, OR, etc.)
- **Coverage:** All S&P 500 tickers — posts mentioning any S&P 500 ticker are captured
- **Polling interval:** Every 1 minute per subreddit (stays within Reddit API rate limits of 60 req/min for authenticated clients)
- **Kafka producer:** Standalone Python service producing to `reddit-raw` topic; runs as a K8s Deployment (not CronJob — persistent polling loop)

### Kafka Topics
- `reddit-raw` — raw Reddit post JSON: `{post_id, title, body, subreddit, created_utc, tickers: []}`
- `sentiment-aggregated` — Flink windowed output: `{ticker, window_start, window_end, avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit}`
- Follow existing topic naming convention (matches intraday-data, processed-features pattern)

### Sentiment Model & Flink Analysis
- **NLP model:** VADER (vaderSentiment library) — lexicon-based, social-media-tuned, in-process (no GPU, no sidecar), returns compound score −1 to +1
- **Flink job:** `sentiment_stream` — consumes `reddit-raw`, applies VADER per post, aggregates with HOP window (1-min hop, 5-min window) per ticker
- **Output per window:** `avg_sentiment`, `mention_count`, `positive_ratio`, `negative_ratio`, `top_subreddit` (most frequent subreddit in window)
- **Persistence:** Feast Redis online store — new FeatureView `reddit_sentiment_fv` with fields: `avg_sentiment`, `mention_count`, `positive_ratio`, `negative_ratio`, `last_updated`; entity: `ticker`

### FastAPI WebSocket Endpoint
- **Endpoint:** `GET /ws/sentiment/{ticker}` — WebSocket connection; server pushes new sentiment JSON on each completed Flink window
- Reads from Feast Redis online store on each push cycle (same pattern as `feast_online_service.py` from Phase 70)
- Push interval: every 60 seconds (aligns with 1-min HOP output rate)
- Connection lifecycle: client connects per ticker on drawer open, disconnects on drawer close

### Frontend Display
- **Location:** New `SentimentPanel` accordion inside Dashboard stock detail drawer — below the existing `StreamingFeaturesPanel` from Phase 70. Same MUI Paper/Accordion pattern.
- **Visual elements:**
  - `avg_sentiment` displayed as MUI `LinearProgress` bar colored red (−1) → yellow (0) → green (+1)
  - `mention_count` displayed as MUI `Typography` label
  - `positive_ratio` / `negative_ratio` as secondary text
  - Freshness timestamp (last_updated) with staleness indicator — same pattern as Phase 70 `FeatureFreshnessPanel`
  - MUI `Chip` label: "LIVE — Reddit" in green (matching "LIVE — Flink" from Phase 70)
- **WebSocket client:** Custom React hook `useSentimentSocket(ticker)` — opens WS connection, updates state on message, closes on unmount; no React Query polling (WS push instead)

### Degraded State
- While connecting or no data received yet: MUI `Skeleton` placeholder rows
- If WebSocket disconnects or API returns null: `PlaceholderCard` with message "Sentiment data unavailable — pipeline may be starting"
- Same ErrorBoundary pattern as Phase 69/70 panels — no crash, graceful fallback

### Claude's Discretion
- Exact K8s Deployment manifest structure for the Reddit PRAW producer
- VADER score thresholds for positive/negative/neutral classification (suggest: positive > 0.05, negative < −0.05)
- WebSocket reconnect logic (exponential backoff, max retries)
- Exact MUI color mapping for the sentiment LinearProgress gradient
- Flink job parallelism settings and checkpoint interval

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Flink job patterns (Phase 67)
- `.planning/phases/67-apache-flink-real-time-stream-processing/67-03-SUMMARY.md` — Flink job structure, FlinkDeployment CR, indicator_stream HOP window pattern, feast_writer sink pattern to replicate

### Feast online store (Phase 66 + 67)
- `.planning/phases/66-feast-production-feature-store/66-03-SUMMARY.md` — FeatureView definition pattern, PushSource wiring, Redis online store config
- `.planning/phases/67-apache-flink-real-time-stream-processing/67-03-SUMMARY.md` — feast_writer.py pattern for pushing to online store from Flink output

### Phase 70 streaming features (direct reuse)
- `.planning/phases/70-display-flink-computed-streaming-features-in-the-dashboard/70-RESEARCH.md` — feast_online_service.py pattern, StreamingFeaturesPanel.tsx component skeleton, StreamHealthPanel MUI patterns, React Query polling hook structure

### Dashboard drawer integration (Phase 69)
- `.planning/phases/69-frontend-analytics-page/` — Dashboard.tsx Drawer structure, DashboardTAPanel accordion pattern, MUI Paper/Accordion/Chip/LinearProgress usage under Bloomberg Terminal dark theme

### Kafka topic management (Phase 5)
- `.planning/phases/05-kafka-via-strimzi/` — Strimzi KafkaTopic CR pattern for creating new topics

### Existing API services to extend
- `stock-prediction-platform/services/api/app/routers/market.py` — Router to extend with WebSocket endpoint
- `stock-prediction-platform/services/api/app/services/feast_online_service.py` — Service to extend for sentiment reads (created in Phase 70)
- `stock-prediction-platform/services/frontend/src/pages/Dashboard.tsx` — Dashboard drawer to extend with SentimentPanel

### Frontend patterns
- `stock-prediction-platform/services/frontend/src/` — Existing hooks, components, apiClient, MUI theme config under Bloomberg Terminal dark aesthetic

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `services/flink-jobs/feast_writer/feast_writer.py` — Flink → Feast Redis push pattern; replicate for sentiment aggregates sink
- `services/flink-jobs/indicator_stream/indicator_stream.py` — HOP window Flink job structure; replicate for sentiment_stream job
- `services/api/app/services/feast_online_service.py` — Feast get_online_features() client (Phase 70); extend to add `get_sentiment_features(ticker)`
- `services/frontend/src/` — MUI Paper/Accordion/Chip/Skeleton/LinearProgress already in use; no new UI library installs needed
- Kafka topics created via Strimzi `KafkaTopic` CRs in storage namespace — two new CRs needed

### Established Patterns
- Flink jobs packaged as Docker images deployed via `FlinkDeployment` CR in ml namespace
- Feast FeatureViews defined in `ml/feature_store/feature_repo.py` with `PushSource` for streaming
- FastAPI routers in `services/api/app/routers/` — new WebSocket endpoint added to `market.py`
- Bloomberg Terminal dark theme: MUI dark palette, no bright colors except semantic red/green for signals

### Integration Points
- Reddit PRAW producer → `reddit-raw` Kafka topic → `sentiment_stream` Flink job → `sentiment-aggregated` topic → feast_writer sink → Redis
- FastAPI `/ws/sentiment/{ticker}` → reads Redis via Feast → pushes to WebSocket client
- `Dashboard.tsx` stock detail drawer → `SentimentPanel.tsx` component → `useSentimentSocket(ticker)` hook → WebSocket

</code_context>

<specifics>
## Specific Ideas

- VADER was chosen specifically for social media / Reddit slang — it handles emoji, ALL CAPS, exclamation marks better than standard NLP models
- WebSocket push (not polling) was explicitly chosen to match the "live streaming" intent of the phase
- All S&P 500 coverage was selected — regex ticker extraction will be the key quality gate
- Polling interval of 1 minute for Reddit producer to maximize freshness within API limits

</specifics>

<deferred>
## Deferred Ideas

- NewsAPI integration (institutional news sentiment) — would complement Reddit retail sentiment; add as Phase 72 or future extension
- Historical sentiment TimescaleDB table for trend charts — useful for model features but not in scope for this phase
- FinBERT inference (finance-tuned BERT) — higher accuracy than VADER but requires GPU/sidecar; future ML enhancement phase
- Sentiment signals used as ML model features in training pipeline — powerful but a separate feature engineering phase
- /sentiment dedicated page with market-wide heatmap — larger frontend feature; own phase

</deferred>

---

*Phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard*
*Context gathered: 2026-03-31*
