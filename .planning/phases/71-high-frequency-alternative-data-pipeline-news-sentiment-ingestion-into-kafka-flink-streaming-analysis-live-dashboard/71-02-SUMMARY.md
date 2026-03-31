---
phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard
plan: "02"
subsystem: infra
tags: [flink, pyflink, vader, sentiment, kafka, feast, redis, feature-store]

# Dependency graph
requires:
  - phase: 71-01
    provides: reddit-raw Kafka topic + PRAW producer writing JSON posts with ticker arrays
  - phase: 67
    provides: Flink Operator + FlinkDeployment CRD + feast_writer pattern
provides:
  - sentiment_stream Flink job with VADER UDFs + HOP(1min, 5min) window aggregation writing to sentiment-aggregated
  - sentiment_writer Flink job consuming sentiment-aggregated and pushing to Feast Redis via reddit_sentiment_push
  - reddit_sentiment_fv FeatureView with 5 fields (avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit)
  - Two FlinkDeployment K8s CRs ready for minikube deployment
affects: [71-03, phase-71-dashboard, feature-serving, prediction-pipeline]

# Tech tracking
tech-stack:
  added: [vaderSentiment==3.3.2, PyFlink Table API with ScalarFunction UDF]
  patterns:
    - VADER module-level singleton for thread-safe sentiment scoring in Flink UDFs
    - HOP window TVF syntax (Flink 1.19) for sliding-window stream aggregation
    - UNNEST tickers ARRAY to explode one-to-many post-ticker rows before aggregation
    - window_start aliased as event_timestamp in sink DDL to match Feast push column contract
    - sentiment_writer mirrors feast_writer pattern with only topic/group_id/push_source/columns changed

key-files:
  created:
    - stock-prediction-platform/services/flink-jobs/sentiment_stream/sentiment_stream.py
    - stock-prediction-platform/services/flink-jobs/sentiment_stream/Dockerfile
    - stock-prediction-platform/services/flink-jobs/sentiment_stream/requirements.txt
    - stock-prediction-platform/services/flink-jobs/sentiment_writer/sentiment_writer.py
    - stock-prediction-platform/services/flink-jobs/sentiment_writer/Dockerfile
    - stock-prediction-platform/services/flink-jobs/sentiment_writer/requirements.txt
    - stock-prediction-platform/k8s/flink/flinkdeployment-sentiment-stream.yaml
    - stock-prediction-platform/k8s/flink/flinkdeployment-sentiment-writer.yaml
  modified:
    - stock-prediction-platform/ml/feature_store/feature_repo.py

key-decisions:
  - "VADER compound score threshold: >0.05 positive, <-0.05 negative (standard VADER thresholds)"
  - "HOP(1 min slide, 5 min size) chosen so per-ticker sentiment rows emit every minute with 5-minute context"
  - "window_start aliased as event_timestamp in sink DDL so sentiment_writer passes it directly to Feast without rename"
  - "FIRST_VALUE(subreddit) as top_subreddit — simplest deterministic approach for window aggregation"
  - "String type added to existing feast.types import line — no duplicate import"
  - "sentiment_stream Dockerfile uses standard python3 (not 3.10) since no Feast dependency; sentiment_writer mirrors feast_writer with python3.10"
  - "FEAST_STORE_PATH env var omitted from flinkdeployment-sentiment-stream.yaml (no Feast in that job)"

patterns-established:
  - "Flink VADER pattern: module-level SentimentIntensityAnalyzer singleton + ScalarFunction wrapping polarity_scores()"
  - "Feast FeatureView extension: append to feature_repo.py, use existing indicators_source as placeholder batch_source for push-only views"

requirements-completed: [ALT-04, ALT-05, ALT-06]

# Metrics
duration: 4min
completed: 2026-03-31
---

# Phase 71 Plan 02: Flink Sentiment Processing Layer Summary

**PyFlink VADER sentiment pipeline: reddit-raw Kafka -> HOP windowed aggregation -> sentiment-aggregated -> Feast Redis with reddit_sentiment_fv FeatureView (avg_sentiment, mention_count, positive/negative ratios)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T08:51:11Z
- **Completed:** 2026-03-31T08:54:29Z
- **Tasks:** 2
- **Files modified:** 9 (8 created, 1 modified)

## Accomplishments
- sentiment_stream Flink job: VaderScoreUdf ScalarFunction + 4 UDAFs (AvgSentiment, MentionCount, PositiveRatio, NegativeRatio) + UNNEST tickers array + HOP(1min, 5min) window aggregation outputting to sentiment-aggregated topic
- sentiment_writer Flink job: consumes sentiment-aggregated, pushes 7-column df (ticker, event_timestamp + 5 sentiment fields) to reddit_sentiment_push Feast PushSource
- feature_repo.py extended with reddit_sentiment_push PushSource and reddit_sentiment_fv FeatureView (5 fields, ttl=10min, online=True, stream_source wired)
- Two FlinkDeployment CRs created following feast-writer pattern with unique names/images/checkpoint paths

## Task Commits

Each task was committed atomically:

1. **Task 1: sentiment_stream Flink job** - `fde7322` (feat)
2. **Task 2: sentiment_writer job + feature_repo + FlinkDeployment CRs** - `607e6fa` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `stock-prediction-platform/services/flink-jobs/sentiment_stream/sentiment_stream.py` - PyFlink Table API job: VADER UDFs, UNNEST, HOP window, reddit-raw -> sentiment-aggregated
- `stock-prediction-platform/services/flink-jobs/sentiment_stream/Dockerfile` - flink:1.19 + python3 + vaderSentiment==3.3.2
- `stock-prediction-platform/services/flink-jobs/sentiment_stream/requirements.txt` - apache-flink, vaderSentiment, pandas
- `stock-prediction-platform/services/flink-jobs/sentiment_writer/sentiment_writer.py` - DataStream job consuming sentiment-aggregated, pushing to Feast redis
- `stock-prediction-platform/services/flink-jobs/sentiment_writer/Dockerfile` - flink:1.19 + python3.10 + feast[redis]==0.61.0
- `stock-prediction-platform/services/flink-jobs/sentiment_writer/requirements.txt` - apache-flink, feast[redis], pandas
- `stock-prediction-platform/ml/feature_store/feature_repo.py` - Extended: reddit_sentiment_push PushSource + reddit_sentiment_fv FeatureView, String added to types import
- `stock-prediction-platform/k8s/flink/flinkdeployment-sentiment-stream.yaml` - FlinkDeployment CR for sentiment-stream job
- `stock-prediction-platform/k8s/flink/flinkdeployment-sentiment-writer.yaml` - FlinkDeployment CR for sentiment-writer job with FEAST_STORE_PATH

## Decisions Made
- window_start aliased as event_timestamp directly in the sink DDL so sentiment_writer reads the column by name without any DataFrame rename step — preserves the end-to-end timestamp contract with Feast
- FIRST_VALUE(subreddit) used for top_subreddit to avoid a second aggregation pass over the window; acceptable for the metrics use case
- sentiment_stream uses standard python3 (not python3.10) since no Feast dependency — simpler image, faster build
- sentiment_writer mirrors feast_writer exactly for maintainability — only 4 values changed (topic, group_id, push_source_name, df columns)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. The jobs deploy via existing FlinkDeployment CRDs applied to the flink namespace.

## Next Phase Readiness
- sentiment_stream + sentiment_writer Flink jobs ready for `docker build` + minikube image push
- FlinkDeployment CRs ready to apply after `feast apply` registers reddit_sentiment_fv
- Phase 71-03 can build the WebSocket sentiment endpoint consuming from Feast Redis

## Self-Check: PASSED
- sentiment_stream/sentiment_stream.py exists with VaderScoreUdf, 4 UDAFs, UNNEST, HOP window
- sentiment_writer/sentiment_writer.py exists with reddit_sentiment_push and sentiment-aggregated
- feature_repo.py contains reddit_sentiment_fv + reddit_sentiment_push + single feast.types import
- flinkdeployment-sentiment-stream.yaml and flinkdeployment-sentiment-writer.yaml exist with correct names/images/paths
- Task commits: fde7322 (sentiment_stream), 607e6fa (sentiment_writer + feature_repo + CRs)

---
*Phase: 71-high-frequency-alternative-data-pipeline*
*Completed: 2026-03-31*
