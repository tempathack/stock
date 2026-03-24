# Phase 38 — Grafana Dashboards & Alerting

## What This Phase Delivers

Deploy a complete monitoring stack (Prometheus + Grafana) in a new `monitoring` namespace, with provisioned dashboards and alert rules that provide operational visibility into the stock prediction platform.

1. **Monitoring namespace + Prometheus server** — New K8s namespace with Prometheus Deployment, ServiceAccount, ClusterRole/Binding for scraping, ConfigMap for scrape config targeting the annotation-based service discovery from Phase 37
2. **Grafana deployment with provisioning** — Grafana Deployment with ConfigMap-based provisioning for datasources (Prometheus) and dashboard JSON files, accessible via NodePort/port-forward
3. **API Health dashboard** — Request rate, latency p50/p95/p99, error rate panels using `http_request_duration_seconds` and `http_requests_total` from prometheus-fastapi-instrumentator
4. **ML Performance dashboard** — Model RMSE over time, retraining frequency, drift events timeline using `prediction_requests_total`, `prediction_latency_seconds`, `model_inference_errors_total`
5. **Kafka & Infrastructure dashboard** — Consumer lag, messages consumed, batch write duration using `messages_consumed_total`, `batch_write_duration_seconds`, `consumer_lag`
6. **Alert rules** — PrometheusRule/alerting config for: drift severity high, API error rate > 5%, Kafka consumer lag > 1000

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| MON-04 | Prometheus server deployed in monitoring namespace | Prometheus Deployment + Service + RBAC + ConfigMap in `k8s/monitoring/` |
| MON-05 | Grafana deployed with provisioned datasources and dashboards | Grafana Deployment + provisioning ConfigMaps for datasource + dashboard JSON |
| MON-06 | API Health dashboard (request rate, latency p50/p95/p99, error rate) | `api-health.json` dashboard provisioned into Grafana |
| MON-07 | ML Performance dashboard (model RMSE over time, retraining frequency, drift events) | `ml-performance.json` dashboard provisioned into Grafana |
| MON-08 | Alert rules: drift severity high, API error rate > 5%, Kafka consumer lag > 1000 | Prometheus alerting rules ConfigMap + Grafana alert notification channel |

## Architecture

### Current State (Phase 37)

```
┌──────────────────────────────────────────────────────────────────┐
│ Observability — METRICS EXPOSED, NO COLLECTION                   │
│                                                                  │
│  FastAPI (ingestion namespace, port 8000)                        │
│    ├── /metrics ← prometheus-fastapi-instrumentator              │
│    ├── http_request_duration_seconds (histogram)                 │
│    ├── http_requests_total (counter)                             │
│    ├── prediction_requests_total (counter: ticker, model, status)│
│    ├── prediction_latency_seconds (histogram: ticker, model)     │
│    └── model_inference_errors_total (counter: ticker, error_type)│
│                                                                  │
│  Kafka Consumer (processing namespace, port 9090)                │
│    ├── /metrics ← prometheus_client HTTP server                  │
│    ├── messages_consumed_total (counter: topic)                  │
│    ├── batch_write_duration_seconds (histogram: table)           │
│    └── consumer_lag (gauge: topic, partition)                    │
│                                                                  │
│  K8s Annotations on both Deployments:                            │
│    prometheus.io/scrape: "true"                                  │
│    prometheus.io/port: "8000" | "9090"                           │
│    prometheus.io/path: "/metrics"                                │
│                                                                  │
│  ❌ No Prometheus server to scrape these endpoints               │
│  ❌ No Grafana for visualization                                 │
│  ❌ No alerting rules                                            │
│  ❌ No monitoring namespace                                      │
└──────────────────────────────────────────────────────────────────┘
```

### Target State (Phase 38)

```
┌──────────────────────────────────────────────────────────────────┐
│ monitoring namespace                                             │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────┐    │
│  │ Prometheus Server     │   │ Grafana                       │    │
│  │ (port 9090)          │   │ (port 3000)                   │    │
│  │                      │   │                               │    │
│  │ Scrape Config:       │   │ Provisioned:                  │    │
│  │  ├── kubernetes-pods │   │  ├── Datasource: Prometheus   │    │
│  │  │   (annotation     │   │  ├── Dashboard: API Health    │    │
│  │  │    discovery)     │   │  ├── Dashboard: ML Perf       │    │
│  │  └── alerting rules  │   │  └── Dashboard: Kafka/Infra   │    │
│  │                      │   │                               │    │
│  │ Alert Rules:         │   │ Alert Channels:               │    │
│  │  ├── HighDriftSev    │   │  └── (webhook placeholder)   │    │
│  │  ├── HighAPIErrorRate│   │                               │    │
│  │  └── HighConsumerLag │   │                               │    │
│  └──────────┬───────────┘   └──────────────┬────────────────┘    │
│             │ scrapes                       │ queries             │
│             ▼                               ▼                    │
│  ┌──────────────────────────────────────────────────────┐        │
│  │ cross-namespace scrape targets                        │        │
│  │  ├── stock-api (ingestion:8000/metrics)              │        │
│  │  ├── kafka-consumer (processing:9090/metrics)        │        │
│  │  └── model-serving (ml:8000/metrics) [if exposed]    │        │
│  └──────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

## Key Files to Create

```
k8s/monitoring/
  ├── namespace.yaml                     # monitoring namespace
  ├── prometheus-rbac.yaml               # ServiceAccount + ClusterRole + ClusterRoleBinding
  ├── prometheus-configmap.yaml          # prometheus.yml scrape config + alerting rules
  ├── prometheus-deployment.yaml         # Prometheus server Deployment
  ├── prometheus-service.yaml            # Prometheus ClusterIP Service
  ├── grafana-datasource-configmap.yaml  # Grafana datasource provisioning
  ├── grafana-dashboards-configmap.yaml  # Dashboard provider config
  ├── grafana-dashboard-api-health.yaml  # API Health dashboard JSON as ConfigMap
  ├── grafana-dashboard-ml-perf.yaml     # ML Performance dashboard JSON as ConfigMap
  ├── grafana-dashboard-kafka.yaml       # Kafka/Infrastructure dashboard JSON as ConfigMap
  ├── grafana-deployment.yaml            # Grafana Deployment
  └── grafana-service.yaml               # Grafana NodePort Service
```

## Key Files to Modify

```
k8s/namespaces.yaml                      # Add monitoring namespace
scripts/deploy-all.sh                    # Add Phase 38 deployment section
docker-compose.yml                       # Add Prometheus + Grafana services for local dev
```

## Existing Metrics Reference

### FastAPI (ingestion namespace)

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `http_request_duration_seconds` | Histogram | method, handler, status | prometheus-fastapi-instrumentator (auto) |
| `http_requests_total` | Counter | method, handler, status | prometheus-fastapi-instrumentator (auto) |
| `prediction_requests_total` | Counter | ticker, model, status | services/api/app/metrics.py |
| `prediction_latency_seconds` | Histogram | ticker, model | services/api/app/metrics.py |
| `model_inference_errors_total` | Counter | ticker, error_type | services/api/app/metrics.py |

### Kafka Consumer (processing namespace)

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `messages_consumed_total` | Counter | topic | services/kafka-consumer/consumer/metrics.py |
| `batch_write_duration_seconds` | Histogram | table | services/kafka-consumer/consumer/metrics.py |
| `consumer_lag` | Gauge | topic, partition | services/kafka-consumer/consumer/metrics.py |

## Prometheus Scrape Approach

Use `kubernetes-sd-configs` with `role: pod` and annotation-based relabeling:
- Only scrape pods with `prometheus.io/scrape: "true"`
- Use `prometheus.io/port` and `prometheus.io/path` for endpoint discovery
- This automatically picks up the FastAPI and Kafka consumer pods from Phase 37

## Dashboard Design Notes

### API Health Dashboard (MON-06)
- **Row 1:** Request Rate (rate of http_requests_total), Error Rate (rate where status=~"5..")
- **Row 2:** Latency p50/p95/p99 (histogram_quantile on http_request_duration_seconds)
- **Row 3:** Prediction-specific: prediction request rate, prediction latency, inference errors

### ML Performance Dashboard (MON-07)
- **Row 1:** Prediction request volume by model, prediction latency by model
- **Row 2:** Model inference errors over time, error rate by error type
- **Row 3:** Drift events timeline (from drift_logs if exposed, or from model_inference_errors as proxy)

### Kafka & Infrastructure Dashboard
- **Row 1:** Messages consumed rate, consumer lag per partition
- **Row 2:** Batch write duration percentiles, batch write rate
- **Row 3:** Pod status overview (up metric)

## Alert Rules (MON-08)

| Alert | Condition | Severity | For |
|-------|-----------|----------|-----|
| HighDriftSeverity | `model_inference_errors_total` rate > threshold | critical | 5m |
| HighAPIErrorRate | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05` | warning | 5m |
| HighConsumerLag | `consumer_lag > 1000` | warning | 10m |

## Dependencies

- **Phase 37 (complete):** Prometheus metrics endpoints on FastAPI + Kafka consumer with K8s annotations
- **Phase 36 (complete):** K8s Secrets management
- **No external dependencies:** Prometheus and Grafana are self-contained deployments
