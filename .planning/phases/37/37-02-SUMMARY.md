---
phase: 37-prometheus-metrics-instrumentation
plan: 02
subsystem: api
tags: [prometheus, prometheus-client, kafka, metrics, observability, kubernetes, consumer-lag]

requires:
  - phase: 37-01
    provides: FastAPI metrics pattern and K8s annotation conventions
  - phase: 9-kafka-consumers-batch-writer
    provides: Kafka consumer service with processor.py, db_writer.py, main.py

provides:
  - Kafka consumer Prometheus HTTP server on port 9090
  - messages_consumed_total counter (by topic)
  - batch_write_duration_seconds histogram (by table name)
  - consumer_lag gauge (by topic and partition)
  - K8s deployment updated with metrics port, annotations, and HTTP-based liveness/readiness probes
  - Test suite for consumer metrics without Kafka/PostgreSQL dependencies

affects: [38-grafana-dashboards-alerting, observability, monitoring]

tech-stack:
  added: [prometheus_client==0.21.0]
  patterns:
    - start_http_server() in daemon thread — non-blocking metrics HTTP server at startup
    - consumer_lag gauge updated after each flush via get_watermark_offsets() + committed() wrapped in try/except
    - Metrics HTTP server doubles as K8s liveness and readiness probe endpoint

key-files:
  created:
    - stock-prediction-platform/services/kafka-consumer/consumer/metrics.py
    - stock-prediction-platform/services/kafka-consumer/tests/test_metrics.py
  modified:
    - stock-prediction-platform/services/kafka-consumer/consumer/main.py
    - stock-prediction-platform/services/kafka-consumer/consumer/processor.py
    - stock-prediction-platform/services/kafka-consumer/consumer/db_writer.py
    - stock-prediction-platform/services/kafka-consumer/requirements.txt
    - stock-prediction-platform/services/kafka-consumer/Dockerfile
    - stock-prediction-platform/k8s/processing/kafka-consumer-deployment.yaml

key-decisions:
  - "start_http_server() runs in daemon thread by default — non-blocking, no threading boilerplate needed"
  - "consumer_lag update wrapped in try/except to handle unassigned partitions gracefully"
  - "Histogram buckets for batch_write_duration cover 5ms to 30s (DB batch writes can be slow under load)"
  - "Metrics HTTP server port 9090 doubles as K8s liveness and readiness probe endpoint"
  - "Exec-based probes replaced with httpGet on port 9090 — metrics server signals consumer health"

patterns-established:
  - "consumer/metrics.py pattern: Counter/Histogram/Gauge definitions + start_metrics_server() function"
  - "Lag tracking pattern: update after each flush, not per-message — avoids broker call overhead per message"
  - "Test isolation: REGISTRY.get_sample_value() checks delta not absolute — test-order-independent"

requirements-completed: [MON-03]

duration: 15min
completed: 2026-03-23
---

# Phase 37 Plan 02: Kafka Consumer Prometheus Metrics Summary

**prometheus_client HTTP server on port 9090 added to Kafka consumer exposing messages_consumed_total, batch_write_duration_seconds, and consumer_lag metrics with K8s deployment updated to HTTP-based liveness probes**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-23
- **Completed:** 2026-03-23
- **Tasks:** 8
- **Files modified:** 8

## Accomplishments

- Created `consumer/metrics.py` with Counter, Histogram, Gauge definitions and `start_metrics_server()` function
- Added `prometheus_client==0.21.0` to requirements.txt
- Added `EXPOSE 9090` to Dockerfile
- Instrumented `processor.py` with `messages_consumed_total.labels(topic=msg.topic()).inc()` per message
- Instrumented `db_writer.py` `upsert_intraday_batch()` and `upsert_daily_batch()` with `batch_write_duration_seconds` timing
- Wired `start_metrics_server(9090)` into `main.py` before consume loop; added `_update_consumer_lag()` helper called after each flush
- Updated K8s deployment with prometheus annotations, port 9090, and HTTP-based liveness/readiness probes
- Created test suite using REGISTRY.get_sample_value() without real Kafka or PostgreSQL

## Task Commits

All tasks included in batch commit:

1. **Task 1: Create consumer/metrics.py** - `fdbe69c` (feat)
2. **Task 2: Add prometheus_client to requirements.txt** - `fdbe69c` (chore)
3. **Task 3: Add EXPOSE 9090 to Dockerfile** - `fdbe69c` (chore)
4. **Task 4: Instrument processor.py** - `fdbe69c` (feat)
5. **Task 5: Instrument db_writer.py** - `fdbe69c` (feat)
6. **Task 6: Wire metrics server and lag tracking into main.py** - `fdbe69c` (feat)
7. **Task 7: Update K8s deployment** - `fdbe69c` (feat)
8. **Task 8: Create tests/test_metrics.py** - `fdbe69c` (test)

## Files Created/Modified

- `stock-prediction-platform/services/kafka-consumer/consumer/metrics.py` - Counter/Histogram/Gauge definitions + start_metrics_server()
- `stock-prediction-platform/services/kafka-consumer/consumer/main.py` - Metrics server startup + _update_consumer_lag() helper + lag updates after flush
- `stock-prediction-platform/services/kafka-consumer/consumer/processor.py` - messages_consumed_total increment in add_message()
- `stock-prediction-platform/services/kafka-consumer/consumer/db_writer.py` - batch_write_duration_seconds timing in upsert_intraday_batch() and upsert_daily_batch()
- `stock-prediction-platform/services/kafka-consumer/requirements.txt` - Added prometheus_client==0.21.0
- `stock-prediction-platform/services/kafka-consumer/Dockerfile` - Added EXPOSE 9090
- `stock-prediction-platform/k8s/processing/kafka-consumer-deployment.yaml` - Annotations, port 9090, HTTP probes
- `stock-prediction-platform/services/kafka-consumer/tests/test_metrics.py` - Tests using REGISTRY.get_sample_value()

## Decisions Made

- Lag tracking calls `_update_consumer_lag()` only after each flush (not per-message) to avoid watermark offset broker calls on every message
- Consumer lag wrapped in try/except to handle the period between consumer.subscribe() and partition assignment where assignment() returns empty
- Metrics HTTP server port 9090 repurposed as K8s liveness/readiness probe target — metrics server health = consumer health
- Histogram buckets span 5ms–30s to accommodate both fast (SSD) and slow (network) DB batch writes

## Deviations from Plan

None - plan executed exactly as written. All eight tasks matched the plan specification.

## Issues Encountered

None - implementation was already in place from batch commit `fdbe69c`.

## Next Phase Readiness

- Kafka consumer metrics ready for Prometheus scraping (Phase 38)
- consumer_lag gauge will drive alerting rules in Phase 38 Grafana dashboards
- HTTP-based liveness probes are more reliable than exec-based probes

---
*Phase: 37-prometheus-metrics-instrumentation*
*Completed: 2026-03-23*

## Self-Check: PASSED

- `/home/tempa/Desktop/priv-project/stock-prediction-platform/services/kafka-consumer/consumer/metrics.py` exists
- `/home/tempa/Desktop/priv-project/stock-prediction-platform/services/kafka-consumer/tests/test_metrics.py` exists
- `/home/tempa/Desktop/priv-project/stock-prediction-platform/services/kafka-consumer/consumer/main.py` contains `start_metrics_server`
- Commit `fdbe69c` verified present
