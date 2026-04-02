---
phase: 82-fix-ml-prediction-latency-alerting-add-threshold-line-for-8-10s-p95-verify-p50-p95-p99-are-real-histogram-metrics-not-synthetic
plan: 01
subsystem: infra
tags: [grafana, prometheus, alerting, histogram, slo, timeseries, configmap]

# Dependency graph
requires:
  - phase: monitoring
    provides: grafana-dashboard-ml-perf.yaml and prometheus-configmap.yaml baseline
provides:
  - 8-second SLO dashed reference line in Grafana ML perf panel 2 (Prediction Latency by Model p95)
  - HighPredictionLatencyP95 Prometheus alert rule firing when p95 > 8s for 5 minutes
affects:
  - future monitoring phases
  - SLO dashboards
  - on-call alerting

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Grafana thresholdsStyle mode=line for SLO reference lines in timeseries panels
    - Prometheus histogram_quantile alert rule pattern using _bucket series with by (le)

key-files:
  created: []
  modified:
    - stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml
    - stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml

key-decisions:
  - "Used thresholdsStyle.mode=line (inside custom) + thresholds at defaults level — Grafana schemaVersion 39 pattern for dashed SLO reference lines without extra PromQL query"
  - "Alert uses prediction_latency_seconds_bucket (histogram bucket series) with sum by (le) — correct Prometheus pattern for histogram_quantile aggregation"
  - "Threshold step 1 is transparent/null (required Grafana base step), step 2 is red/8 (SLO boundary)"

patterns-established:
  - "Grafana SLO line: add thresholdsStyle:{mode:line} to custom, add thresholds:{mode:absolute,steps:[{transparent,null},{red,value}]} to defaults"
  - "Prometheus histogram alert: histogram_quantile(0.95, sum(rate(metric_bucket[5m])) by (le)) > threshold"

requirements-completed: [MON-06, MON-08]

# Metrics
duration: 3min
completed: 2026-04-02
---

# Phase 82 Plan 01: ML Prediction Latency Alerting Summary

**Dashed red 8-second SLO reference line added to Grafana ML perf panel 2, plus HighPredictionLatencyP95 alert rule using real histogram_quantile over prediction_latency_seconds_bucket**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-02T22:26:45Z
- **Completed:** 2026-04-02T22:27:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Panel 2 ("Prediction Latency by Model (p95)") in the ML Performance Grafana dashboard now shows a dashed red horizontal line at y=8 seconds using Grafana's native threshold line feature (no extra PromQL query needed)
- HighPredictionLatencyP95 Prometheus alert fires when histogram_quantile(0.95, prediction_latency_seconds_bucket) exceeds 8s for 5 consecutive minutes
- Both ConfigMap YAML files validated with python3 yaml.safe_load and kubectl apply --dry-run=client

## Task Commits

Each task was committed atomically:

1. **Task 1: Add 8s threshold line to Grafana ML perf panel 2** - `aba7e56` (feat)
2. **Task 2: Add HighPredictionLatencyP95 alert rule to Prometheus configmap** - `fc8a114` (feat)

## Files Created/Modified
- `stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml` - Panel 2 fieldConfig.defaults.custom gets thresholdsStyle:{mode:line}, fieldConfig.defaults gets thresholds with transparent base step and red step at value=8
- `stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml` - Fourth alert rule HighPredictionLatencyP95 appended to stock-prediction-alerts group

## Decisions Made
- thresholdsStyle.mode="line" goes inside the `custom` block (not at defaults level) per Grafana schemaVersion 39 timeseries panel schema
- The thresholds object goes at defaults level alongside color, custom, and unit
- Alert expression uses `sum(...) by (le)` without a model label to give aggregate p95 across all models — simplest actionable signal

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. Changes take effect when ConfigMaps are applied to the cluster.

## Next Phase Readiness
- Both ConfigMaps ready to apply with `kubectl apply -f`
- Grafana will show the 8s SLO line immediately after dashboard reload
- Prometheus will start evaluating HighPredictionLatencyP95 after configmap reload

---
*Phase: 82-fix-ml-prediction-latency-alerting-add-threshold-line-for-8-10s-p95-verify-p50-p95-p99-are-real-histogram-metrics-not-synthetic*
*Completed: 2026-04-02*
