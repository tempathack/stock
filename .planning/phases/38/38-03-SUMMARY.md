---
phase: 38-grafana-dashboards-alerting
plan: 03
subsystem: infra
tags: [prometheus, alerting, alert-rules, promql, kubernetes, configmap, monitoring]

requires:
  - phase: 38-grafana-dashboards-alerting plan 01
    provides: prometheus-configmap.yaml with placeholder alert_rules.yml
  - phase: 37-prometheus-metrics-instrumentation
    provides: model_inference_errors_total, http_requests_total, consumer_lag metric definitions

provides:
  - Prometheus alert rule group "stock-prediction-alerts" with 3 production-ready rules
  - HighDriftSeverity alert — fires when model_inference_errors_total rate > 0.1/s for 5m (severity: critical)
  - HighAPIErrorRate alert — fires when HTTP 5xx rate > 5% for 5m (severity: warning)
  - HighConsumerLag alert — fires when consumer_lag > 1000 messages for 10m (severity: warning)
  - alerting section in prometheus.yml pointing to alertmanager.monitoring.svc.cluster.local:9093

affects: [phase-62-infra-e2e-tests]

tech-stack:
  added: []
  patterns:
    - Prometheus alert rules embedded in ConfigMap alongside scrape config
    - Alert annotations with Go template label interpolation for dynamic context
    - Alertmanager reference configured but not yet deployed (future integration point)

key-files:
  modified:
    - stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml

key-decisions:
  - "HighDriftSeverity threshold 0.1/s rate over 5m — model inference errors above this indicate systematic issue"
  - "HighAPIErrorRate threshold 5% matches MON-08 requirement — warning not critical allows investigation before escalation"
  - "HighConsumerLag threshold 1000 messages over 10m matches MON-08 requirement — sustained lag indicates consumer stall"
  - "All alerts labeled team: platform for routing when Alertmanager is added"
  - "Alertmanager configured as future integration target — not deployed in this phase"
  - "HighAPIErrorRate uses > not >= for threshold — > 0.05 means strictly more than 5%"

requirements-completed: [MON-08]

duration: 15min
completed: 2026-03-23
---

# Phase 38 Plan 03: Prometheus Alert Rules Summary

**Three production-ready Prometheus alerting rules for model drift severity, API error rate > 5%, and Kafka consumer lag > 1000 messages — fulfills MON-08**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-23T11:05:00Z
- **Completed:** 2026-03-23T11:20:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Populated alert_rules.yml in prometheus-configmap with 3 alert rules in group "stock-prediction-alerts"
- HighDriftSeverity: critical alert when model inference error rate exceeds 0.1/s for 5 minutes, includes ticker and error_type labels in annotation
- HighAPIErrorRate: warning alert when HTTP 5xx rate exceeds 5% for 5 minutes, includes current percentage in description
- HighConsumerLag: warning alert when consumer lag exceeds 1000 messages for 10 minutes, includes topic/partition labels
- Added alerting section to prometheus.yml referencing alertmanager (for future Alertmanager deployment)

## Task Commits

All tasks committed as part of the large batch commit:

1. **Task 1: Populate alert_rules.yml** — 3 alert rules with labels, annotations, thresholds
2. **Task 2: Verify alert rules configuration** — YAML syntax valid, 2-key ConfigMap structure confirmed, metric references verified

**Plan metadata:** `fdbe69c` (Phase 31-57 batch commit)

## Files Created/Modified
- `k8s/monitoring/prometheus-configmap.yaml` — alert_rules.yml populated with 3 rules; prometheus.yml gains alerting.alertmanagers section

## Decisions Made
- All three thresholds (0.1/s drift, 5% error rate, 1000 lag) match MON-08 requirements exactly
- All alerts carry `team: platform` label for Alertmanager routing when deployed
- Alertmanager static target configured at alertmanager.monitoring.svc.cluster.local:9093 — Alertmanager not deployed in this phase

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Prometheus evaluates all 3 alert rules every 15s (evaluation_interval from global config)
- Alert state visible at Prometheus /api/v1/rules and /alerts endpoints
- Phase 62 E2E tests verify alert rule names (HighDriftSeverity, HighAPIErrorRate, HighConsumerLag) via Grafana API

## Self-Check: PASSED
- `k8s/monitoring/prometheus-configmap.yaml` — exists with 3 alert rules
- `k8s/monitoring/grafana-dashboard-api-health.yaml` — exists with api-health.json
- `k8s/monitoring/grafana-dashboard-ml-perf.yaml` — exists with ml-performance.json
- `k8s/monitoring/grafana-dashboard-kafka.yaml` — exists with kafka-infra.json
- All files committed in `fdbe69c`

---
*Phase: 38-grafana-dashboards-alerting*
*Completed: 2026-03-23*
