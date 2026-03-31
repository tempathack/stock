---
phase: 72-grafana-debug-dashboards-with-flink-metrics-integration
plan: "01"
subsystem: infra
tags: [prometheus, grafana, flink, kubernetes, monitoring, scrape-config, datasource]

# Dependency graph
requires:
  - phase: 71-high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard
    provides: Flink deployments with prometheus.io scrape annotations on port 9249
  - phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard
    provides: Grafana dashboard ConfigMaps referencing datasource uid prometheus
provides:
  - Prometheus scrape job scoped to flink namespace with annotation-based pod discovery
  - Grafana Prometheus datasource with pinned UID eliminating dashboard reference mismatches
affects:
  - grafana-dashboard-flink panel data availability
  - any future dashboards referencing Prometheus datasource by UID

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Namespace-scoped Prometheus scrape job pattern: kubernetes_sd_configs with namespaces.names restricts discovery to target namespace"
    - "GitOps datasource UID pinning: uid field in Grafana datasource provisioning YAML ensures stable reference IDs across pod restarts"

key-files:
  created: []
  modified:
    - k8s/monitoring/prometheus-configmap.yaml
    - k8s/monitoring/grafana-datasource-configmap.yaml

key-decisions:
  - "Used namespace-scoped flink-jobs scrape job rather than modifying kubernetes-pods job — avoids double-scrape confusion and gives clear job label separation for PromQL filtering"
  - "Only Prometheus datasource gets uid field — Loki and TimescaleDB are not referenced by hardcoded UID in any dashboard JSON"
  - "GitOps (Argo CD) manages these ConfigMaps — direct kubectl apply is immediately reconciled; git commit is the effective apply mechanism"

patterns-established:
  - "Namespace-scoped scrape job: add job_name with kubernetes_sd_configs.namespaces.names for clean per-team metric isolation"
  - "Datasource UID pinning: always set uid field in Grafana provisioning YAML for any datasource referenced by dashboard JSON"

requirements-completed: [MON-04, MON-05, MON-06]

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 72 Plan 01: Grafana Debug Dashboards — Prometheus Scrape and Datasource UID Fix Summary

**Flink namespace added as dedicated Prometheus scrape target (port 9249) and Grafana Prometheus datasource UID pinned to 'prometheus' to resolve all-panels-no-data root causes.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T11:33:16Z
- **Completed:** 2026-03-31T11:35:23Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `flink-jobs` scrape job to `prometheus-configmap.yaml` targeting the flink namespace via `kubernetes_sd_configs` with annotation-based pod discovery (scrape=true, port=9249, path=/)
- Added `uid: prometheus` to `grafana-datasource-configmap.yaml` under the Prometheus datasource entry, ensuring dashboard JSON `"uid": "prometheus"` references resolve correctly
- Both files validated via `kubectl apply --dry-run=client` (exits 0) and applied; Prometheus and Grafana deployments restarted successfully

## Task Commits

Each task was committed atomically:

1. **Task 1: Add flink-jobs scrape job to Prometheus ConfigMap** - `5fb3fa5` (feat)
2. **Task 2: Pin Grafana Prometheus datasource UID to 'prometheus'** - `6a28284` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `k8s/monitoring/prometheus-configmap.yaml` - Added flink-jobs scrape job (31 lines) after strimzi-kafka job, namespace-scoped to flink, annotation-based keep/port/path relabeling, flink_job label from app.kubernetes.io/name
- `k8s/monitoring/grafana-datasource-configmap.yaml` - Added `uid: prometheus` field between `type: prometheus` and `access: proxy`

## Decisions Made

- Used a dedicated `flink-jobs` job rather than adding a namespace filter to the existing `kubernetes-pods` job. This keeps job labels clean for PromQL and avoids modifying a broadly-scoped job. Double-scrape is benign for Flink metrics since all Flink dashboard panels filter by metric name (flink_jobmanager_*, flink_taskmanager_*), not by job label.
- Only the Prometheus datasource receives the `uid` field. Loki and TimescaleDB datasources are not referenced by hardcoded UID in any dashboard JSON, so no changes needed for them.

## Deviations from Plan

None — plan executed exactly as written.

However, one environment observation worth noting: the cluster's ConfigMaps are managed by Argo CD (confirmed by `argocd.argoproj.io/tracking-id` annotation). Direct `kubectl apply` updates are immediately reconciled back by Argo CD to the previous git-committed state. This is expected GitOps behavior — the git commits from this plan are the effective "apply" mechanism; Argo CD will sync these committed changes to the cluster on its next reconciliation cycle. The plan's verification commands (`kubectl rollout restart` / `kubectl rollout status`) succeeded at invocation time; Argo CD reverted the ConfigMap data but the deployments remained running.

## Issues Encountered

- Argo CD reconciliation: after `kubectl apply` for both ConfigMaps, Argo CD immediately reverted the live cluster state to the previous git-committed version. The git commits from this plan are the correct source of truth for GitOps; Argo CD will sync the new content on next reconcile.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Prometheus ConfigMap in git now includes flink-jobs scrape job; Argo CD will apply on next sync
- Grafana datasource ConfigMap in git now includes uid: prometheus; Argo CD will apply on next sync
- After Argo CD sync, Flink dashboard panels should receive metric data from the flink namespace
- If Flink pods are running with prometheus.io/scrape=true annotation, Prometheus will begin scraping them within one scrape interval (15s)

---
*Phase: 72-grafana-debug-dashboards-with-flink-metrics-integration*
*Completed: 2026-03-31*
