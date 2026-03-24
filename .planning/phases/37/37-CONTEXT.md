# Phase 37 — Prometheus Metrics Instrumentation

## What This Phase Delivers

Add Prometheus metrics endpoints to both the FastAPI API service and the Kafka consumer service, enabling observability for request rates, latency, errors, and consumer throughput.

1. **FastAPI /metrics endpoint** — Wire `prometheus-fastapi-instrumentator` (already in requirements.txt) to expose default HTTP request histograms at `/metrics`
2. **Custom prediction metrics** — `prediction_requests_total` counter, `prediction_latency_seconds` histogram, `model_inference_errors_total` counter on `/predict` endpoints
3. **Kafka consumer /metrics** — Standalone HTTP server on port 9090 exposing `messages_consumed_total`, `batch_write_duration_seconds`, `consumer_lag`
4. **K8s annotations** — `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` on both deployments for future Prometheus discovery

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| MON-01 | FastAPI /metrics endpoint via prometheus-fastapi-instrumentator | Instrumentator wired into `app/main.py`, `/metrics` exposed |
| MON-02 | Custom Prometheus metrics: prediction_requests_total, prediction_latency_seconds, model_inference_errors_total | `app/metrics.py` module with Counter + Histogram, instrumented in predict router |
| MON-03 | Kafka consumer /metrics on port 9090 (messages_consumed_total, batch_write_duration, consumer_lag) | `prometheus_client` HTTP server in consumer, metrics in processor + db_writer |

## Architecture

### Current State (Phase 36)

```
┌──────────────────────────────────────────────────────────────────┐
│ Observability — NO METRICS                                       │
│                                                                  │
│  FastAPI (stock-api:8000)                                        │
│    ├── /health          ← only health check exposed              │
│    ├── /predict/{ticker}                                         │
│    ├── /predict/bulk                                             │
│    └── No /metrics endpoint                                      │
│                                                                  │
│  Kafka Consumer (no HTTP server)                                 │
│    ├── Consume loop only                                         │
│    ├── Exec-based liveness probe (python -c sys.exit(0))         │
│    └── No metrics exposure at all                                │
│                                                                  │
│  K8s Deployments                                                 │
│    ├── No prometheus.io/* annotations                            │
│    └── No ServiceMonitor resources                               │
└──────────────────────────────────────────────────────────────────┘
```

### Target State (Phase 37)

```
┌──────────────────────────────────────────────────────────────────┐
│ Observability — PROMETHEUS METRICS                               │
│                                                                  │
│  FastAPI (stock-api:8000)                                        │
│    ├── /health                                                   │
│    ├── /predict/{ticker}  → increments prediction_requests_total │
│    │                      → observes prediction_latency_seconds  │
│    ├── /predict/bulk      → same counters per-ticker             │
│    └── /metrics           ← prometheus-fastapi-instrumentator    │
│         ├── http_requests_total (method, handler, status)        │
│         ├── http_request_duration_seconds                        │
│         ├── prediction_requests_total (ticker, model, status)    │
│         ├── prediction_latency_seconds (ticker, model)           │
│         └── model_inference_errors_total (ticker, error_type)    │
│                                                                  │
│  Kafka Consumer                                                  │
│    ├── Consume loop (unchanged)                                  │
│    └── :9090/metrics      ← prometheus_client HTTP server        │
│         ├── messages_consumed_total (topic)                      │
│         ├── batch_write_duration_seconds (table)                 │
│         └── consumer_lag (topic, partition)                      │
│                                                                  │
│  K8s Deployments (both services)                                 │
│    ├── prometheus.io/scrape: "true"                              │
│    ├── prometheus.io/port: "<port>"                              │
│    └── prometheus.io/path: "/metrics"                            │
└──────────────────────────────────────────────────────────────────┘
```

## Key Technical Decisions

### FastAPI Metrics (Plan 01)

- **Library**: `prometheus-fastapi-instrumentator==7.0.0` (already in requirements.txt)
- **Integration point**: `Instrumentator().instrument(app).expose(app)` in `main.py` lifespan or after app creation
- **Custom metrics module**: `app/metrics.py` — defines Counter and Histogram using `prometheus_client` (transitive dep from instrumentator)
- **Instrumentation approach**: Decorate/wrap predict endpoints to increment counters with labels (ticker, model_name, status)
- **No middleware needed**: The instrumentator handles default HTTP metrics; custom metrics are registered globally via `prometheus_client` registry

### Kafka Consumer Metrics (Plan 02)

- **Library**: `prometheus_client` (add to requirements.txt)
- **HTTP server**: `prometheus_client.start_http_server(9090)` launched at consumer startup before the consume loop
- **Metrics location**: Define in `consumer/metrics.py`, import and use in `processor.py` (messages_consumed_total) and `db_writer.py` (batch_write_duration)
- **Consumer lag**: Expose via Gauge, updated each poll cycle using `consumer.get_watermark_offsets()` and committed offsets
- **Port exposure**: Dockerfile adds `EXPOSE 9090`, K8s deployment adds container port 9090
- **Liveness probe upgrade**: Switch from exec-based to HTTP on port 9090 (metrics server acts as liveness indicator)

## File Inventory

### Plan 01 — FastAPI Metrics

| File | Action | Purpose |
|------|--------|---------|
| `services/api/app/metrics.py` | NEW | Custom prediction Counter + Histogram definitions |
| `services/api/app/main.py` | MODIFY | Wire instrumentator, import metrics |
| `services/api/app/routers/predict.py` | MODIFY | Instrument /predict endpoints with custom metrics |
| `k8s/ingestion/fastapi-deployment.yaml` | MODIFY | Add prometheus.io annotations |
| `services/api/tests/test_metrics.py` | NEW | Verify /metrics endpoint + custom counters |

### Plan 02 — Kafka Consumer Metrics

| File | Action | Purpose |
|------|--------|---------|
| `services/kafka-consumer/consumer/metrics.py` | NEW | Prometheus Counter/Histogram/Gauge definitions + HTTP server start |
| `services/kafka-consumer/consumer/main.py` | MODIFY | Start metrics HTTP server at consumer startup |
| `services/kafka-consumer/consumer/processor.py` | MODIFY | Increment messages_consumed_total on each message |
| `services/kafka-consumer/consumer/db_writer.py` | MODIFY | Observe batch_write_duration on each flush |
| `services/kafka-consumer/requirements.txt` | MODIFY | Add prometheus_client |
| `services/kafka-consumer/Dockerfile` | MODIFY | EXPOSE 9090 |
| `k8s/processing/kafka-consumer-deployment.yaml` | MODIFY | Add port 9090, prometheus.io annotations, HTTP liveness probe |
| `services/kafka-consumer/tests/test_metrics.py` | NEW | Verify /metrics endpoint + counters |

## Verification Commands

```bash
# FastAPI metrics
curl -s http://localhost:8000/metrics | grep -E "^(http_requests|prediction_requests|prediction_latency|model_inference)"

# Kafka consumer metrics
curl -s http://localhost:9090/metrics | grep -E "^(messages_consumed|batch_write|consumer_lag)"

# K8s annotations
kubectl get deploy stock-api -n ingestion -o jsonpath='{.spec.template.metadata.annotations}'
kubectl get deploy kafka-consumer -n processing -o jsonpath='{.spec.template.metadata.annotations}'
```
