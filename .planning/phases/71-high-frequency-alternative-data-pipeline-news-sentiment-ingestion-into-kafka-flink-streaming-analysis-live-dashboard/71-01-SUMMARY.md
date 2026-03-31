---
phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard
plan: 01
subsystem: infra
tags: [kafka, strimzi, praw, reddit, confluent-kafka, python, docker, kubernetes]

# Dependency graph
requires:
  - phase: 5-kafka-via-strimzi
    provides: Strimzi KafkaTopic CR pattern and kafka-kafka-bootstrap service endpoint
  - phase: 8-k8s-cronjobs-for-ingestion
    provides: ingestion namespace, ConfigMap pattern (envFrom), Deployment pattern with imagePullPolicy Never

provides:
  - reddit-raw KafkaTopic CR (3 partitions, 1-day retention) in storage namespace
  - sentiment-aggregated KafkaTopic CR (3 partitions, 7-day retention) in storage namespace
  - reddit-producer Python service with PRAW polling loop + SP500 ticker extraction
  - sp500_tickers.py with SP500_SET (476 tickers) and BLOCKLIST (34 false-positive suppressions)
  - K8s Deployment + ConfigMap for reddit-producer in ingestion namespace

affects:
  - phase 71-02 (Flink sentiment analysis job consuming from reddit-raw)
  - phase 71-03 (sentiment-aggregated topic consumer for WebSocket endpoint)
  - phase 71-04 (SentimentPanel frontend reading from sentiment WebSocket)

# Tech tracking
tech-stack:
  added:
    - praw==7.8.1 (Reddit PRAW Python API wrapper)
    - confluent-kafka==2.4.0 (Kafka producer client)
  patterns:
    - Strimzi KafkaTopic CR pattern with namespace: storage and strimzi.io/cluster: kafka label
    - envFrom configmap + secret pattern for K8s Deployments in ingestion namespace
    - SP500 ticker extraction: dollar-sign pattern ($AAPL) + bare uppercase pattern with blocklist filtering

key-files:
  created:
    - stock-prediction-platform/k8s/kafka/kafka-topic-reddit.yaml
    - stock-prediction-platform/services/reddit-producer/requirements.txt
    - stock-prediction-platform/services/reddit-producer/Dockerfile
    - stock-prediction-platform/services/reddit-producer/sp500_tickers.py
    - stock-prediction-platform/services/reddit-producer/reddit_producer.py
    - stock-prediction-platform/k8s/ingestion/reddit-producer-configmap.yaml
    - stock-prediction-platform/k8s/ingestion/reddit-producer-deployment.yaml
  modified: []

key-decisions:
  - "BLOCKLIST applied after SP500_SET intersection to suppress 34 common English words/abbreviations (IT, AI, DD, etc.) that are valid S&P 500 tickers but cause false positives in Reddit text"
  - "Two-pattern ticker extraction: explicit $TICKER prefix captures high-confidence mentions; bare uppercase word scan captures e.g. 'NVDA is mooning' style posts"
  - "reddit-secrets K8s Secret must be created manually by operator before deployment — credentials not stored in git"
  - "1-day retention for reddit-raw (processed immediately by Flink), 7-day retention for sentiment-aggregated (replay/debug value)"

patterns-established:
  - "Pattern: S&P 500 ticker extraction with SP500_SET + BLOCKLIST two-stage filter"
  - "Pattern: Per-subreddit error handling in polling loop so one failure doesn't abort others"

requirements-completed: [ALT-01, ALT-02, ALT-03]

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 71 Plan 01: Kafka Topics + Reddit PRAW Producer Summary

**Strimzi KafkaTopic CRs for reddit-raw and sentiment-aggregated plus a PRAW-based Python producer polling 3 subreddits with SP500 ticker extraction and confluent-kafka publish to reddit-raw**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-31T08:46:29Z
- **Completed:** 2026-03-31T08:49:21Z
- **Tasks:** 2
- **Files modified:** 7 (all created new)

## Accomplishments

- Two Strimzi KafkaTopic CRs (reddit-raw + sentiment-aggregated) following exact existing pattern
- reddit-producer Python service with `extract_tickers()` filtering 476 S&P 500 tickers through a 34-word blocklist
- K8s Deployment wired with ConfigMap + reddit-secrets Secret via envFrom

## Task Commits

Each task was committed atomically:

1. **Task 1: Strimzi KafkaTopic CRs for reddit-raw and sentiment-aggregated** - `e1f1f99` (feat)
2. **Task 2: Reddit PRAW producer service — Python code, Dockerfile, K8s manifests** - `3062503` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `stock-prediction-platform/k8s/kafka/kafka-topic-reddit.yaml` - Two KafkaTopic CRs: reddit-raw (1-day) and sentiment-aggregated (7-day)
- `stock-prediction-platform/services/reddit-producer/requirements.txt` - praw==7.8.1, confluent-kafka==2.4.0
- `stock-prediction-platform/services/reddit-producer/Dockerfile` - python:3.10-slim, copies sp500_tickers.py + reddit_producer.py
- `stock-prediction-platform/services/reddit-producer/sp500_tickers.py` - SP500_SET (476 tickers) and BLOCKLIST (34 false-positive suppressions)
- `stock-prediction-platform/services/reddit-producer/reddit_producer.py` - PRAW polling loop, extract_tickers(), poll_subreddit(), main while loop
- `stock-prediction-platform/k8s/ingestion/reddit-producer-configmap.yaml` - ConfigMap in ingestion namespace with Kafka bootstrap + poll config
- `stock-prediction-platform/k8s/ingestion/reddit-producer-deployment.yaml` - K8s Deployment with envFrom configmap + secretRef for reddit-secrets

## Decisions Made

- BLOCKLIST applied after SP500_SET membership check so common English words (IT, AI, DD) that happen to be S&P 500 tickers are suppressed in free text
- Two extraction patterns used: explicit `$TICKER` prefix (high confidence) and bare uppercase words (catches conversational mentions like "NVDA is mooning")
- reddit-secrets K8s Secret must be created manually by operator with REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET — no credentials committed to git
- 1-day retention for reddit-raw (immediately processed by Flink downstream), 7-day retention for sentiment-aggregated (replay/debug window)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Automated verification command in plan (`python3 -c "... from reddit_producer import extract_tickers"`) fails on host because `praw` is not installed in the host environment. This is expected — praw is a container runtime dependency. Logic was verified by running sp500_tickers.py directly and inlining the extract_tickers function for testing. All assertions pass.

## User Setup Required

Before deploying the reddit-producer Deployment, the operator must create the reddit-secrets K8s Secret:

```bash
kubectl create secret generic reddit-secrets \
  --namespace=ingestion \
  --from-literal=REDDIT_CLIENT_ID=<your-client-id> \
  --from-literal=REDDIT_CLIENT_SECRET=<your-client-secret>
```

Then apply the manifests:

```bash
kubectl apply -f stock-prediction-platform/k8s/kafka/kafka-topic-reddit.yaml
kubectl apply -f stock-prediction-platform/k8s/ingestion/reddit-producer-configmap.yaml
kubectl apply -f stock-prediction-platform/k8s/ingestion/reddit-producer-deployment.yaml
```

## Next Phase Readiness

- reddit-raw topic ready for Flink sentiment analysis job (Phase 71-02)
- sentiment-aggregated topic ready for WebSocket endpoint consumer (Phase 71-03)
- reddit-producer Deployment can be built with `docker build -t stock-reddit-producer:latest stock-prediction-platform/services/reddit-producer/`

---
*Phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard*
*Completed: 2026-03-31*

## Self-Check: PASSED

All 7 task files confirmed present. Both task commits (e1f1f99, 3062503) confirmed in git log.
