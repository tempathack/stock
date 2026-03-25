---
phase: 38-grafana-dashboards-alerting
plan: 02
subsystem: infra
tags: [grafana, dashboard, prometheus, promql, configmap, kubernetes, monitoring]

requires:
  - phase: 38-grafana-dashboards-alerting plan 01
    provides: Grafana deployment with file-based provisioning at /var/lib/grafana/dashboards
  - phase: 37-prometheus-metrics-instrumentation
    provides: prediction_requests_total, prediction_latency_seconds, model_inference_errors_total, messages_consumed_total, batch_write_duration_seconds, consumer_lag metrics

provides:
  - API Health dashboard (uid: api-health) — HTTP request rate, error rate, latency p50/p95/p99, prediction metrics
  - ML Performance dashboard (uid: ml-performance) — predictions by model, inference errors, success/error ratio, model comparison
  - Kafka & Infrastructure dashboard (uid: kafka-infra) — consumer lag, message throughput, batch write duration, pod status
  - Grafana Deployment updated with volume mounts for all three dashboard ConfigMaps

affects: [39-structured-logging, phase-62-infra-e2e-tests]

tech-stack:
  added: []
  patterns:
    - Grafana dashboard JSON wrapped in Kubernetes ConfigMap for automatic provisioning
    - PromQL queries using kubernetes_namespace label from annotation-based scraping
    - Template variable `namespace` with label_values query for multi-namespace filtering
    - Threshold coloring for error rate and latency panels

key-files:
  created:
    - stock-prediction-platform/k8s/monitoring/grafana-dashboard-api-health.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-dashboard-kafka.yaml
  modified:
    - stock-prediction-platform/k8s/monitoring/grafana-deployment.yaml

key-decisions:
  - "Dashboard UIDs (api-health, ml-performance, kafka-infra) are stable strings for linking and referencing"
  - "datasource UID set to 'prometheus' matching the provisioned datasource uid from Plan 01"
  - "namespace template variable uses label_values query to dynamically discover namespaces from Prometheus"
  - "Error Rate panel uses stat type with threshold coloring (green<1%, yellow<5%, red>=5%)"
  - "Consumer Lag panel uses timeseries with threshold lines at 100 (yellow) and 1000 (red)"
  - "Grafana deployment updated in Plan 02 to include dashboard ConfigMap volume mounts"

requirements-completed: [MON-06, MON-07]

duration: 30min
completed: 2026-03-23
---

# Phase 38 Plan 02: Grafana Dashboard JSONs Summary

**Three Grafana dashboard ConfigMaps auto-provisioned via file-based provider: API Health (HTTP + prediction metrics), ML Performance (model comparison + errors), and Kafka & Infrastructure (consumer lag + throughput)**

## Performance

- **Duration:** 30 min
- **Started:** 2026-03-23T10:35:00Z
- **Completed:** 2026-03-23T11:05:00Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments
- API Health dashboard with 9 panels covering HTTP request rate, error rate %, latency p50/p95/p99, prediction request rate by status, prediction p95 latency, and inference errors by type
- ML Performance dashboard with 6 panels covering predictions by model, latency by model, inference errors by type and ticker, success/error pie chart, and model comparison table
- Kafka & Infrastructure dashboard with 6 panels covering messages consumed rate, consumer lag, batch write duration, batch write rate, pod status, and scrape targets
- Grafana Deployment patched to mount all three dashboard ConfigMaps at /var/lib/grafana/dashboards/

## Task Commits

All tasks committed as part of the large batch commit:

1. **Task 1: grafana-dashboard-api-health.yaml** — ConfigMap with api-health.json
2. **Task 2: grafana-dashboard-ml-perf.yaml** — ConfigMap with ml-performance.json
3. **Task 3: grafana-dashboard-kafka.yaml** — ConfigMap with kafka-infra.json
4. **Task 4: grafana-deployment.yaml** — added 3 volume/volumeMount entries for dashboard JSONs

**Plan metadata:** `fdbe69c` (Phase 31-57 batch commit)

## Files Created/Modified
- `k8s/monitoring/grafana-dashboard-api-health.yaml` — ConfigMap wrapping API Health dashboard JSON (UID: api-health, 9 panels)
- `k8s/monitoring/grafana-dashboard-ml-perf.yaml` — ConfigMap wrapping ML Performance dashboard JSON (UID: ml-performance, 6 panels)
- `k8s/monitoring/grafana-dashboard-kafka.yaml` — ConfigMap wrapping Kafka & Infrastructure dashboard JSON (UID: kafka-infra, 6 panels)
- `k8s/monitoring/grafana-deployment.yaml` — added volume mounts for api-health.json, ml-performance.json, kafka-infra.json

## Decisions Made
- All panels reference datasource uid "prometheus" matching the provisioned Grafana datasource
- Template variable `namespace` uses `label_values(http_requests_total, kubernetes_namespace)` for dynamic namespace discovery
- Consumer Lag panel uses timeseries type (not gauge) to show lag over time for trend visibility
- Schema version 39 for Grafana 10.4.0 compatibility

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- All three dashboards auto-load when Grafana starts — no manual import required
- Plan 03 populates alert_rules.yml in the prometheus-configmap
- Phase 39 (Loki) will add a new datasource and log-based panels

---
*Phase: 38-grafana-dashboards-alerting*
*Completed: 2026-03-23*
