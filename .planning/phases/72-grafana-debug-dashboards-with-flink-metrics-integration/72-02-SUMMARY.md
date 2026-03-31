---
phase: 72-grafana-debug-dashboards-with-flink-metrics-integration
plan: 02
subsystem: infra
tags: [grafana, flink, prometheus, kubernetes, monitoring, dashboards]

# Dependency graph
requires:
  - phase: 72-01
    provides: Prometheus flink-jobs scrape job and Grafana datasource UID pinned to lowercase "prometheus"

provides:
  - 10-panel Flink debug dashboard covering job uptime, restarts, checkpoints, throughput, watermarks, JVM heap
  - Consistent lowercase "prometheus" datasource UID confirmed across all four dashboard ConfigMaps
  - All four dashboard ConfigMaps applied to cluster with Grafana restarted

affects:
  - grafana-debug-dashboards-with-flink-metrics-integration (human verification checkpoint)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Grafana dashboard ConfigMap: embedded JSON with explicit datasource objects on every panel and target using { type: prometheus, uid: prometheus }"
    - "Flink dashboard layout: row panels (id 100-104) grouping stat and timeseries panels by concern"

key-files:
  created: []
  modified:
    - k8s/monitoring/grafana-dashboard-flink.yaml
    - k8s/monitoring/grafana-dashboard-api-health.yaml (verified correct, re-applied)
    - k8s/monitoring/grafana-dashboard-ml-perf.yaml (verified correct, re-applied)
    - k8s/monitoring/grafana-dashboard-kafka.yaml (verified correct, re-applied)

key-decisions:
  - "Used kubectl delete + create instead of kubectl apply/replace because apply was patching annotation metadata and not updating ConfigMap content in cluster"
  - "api-health, ml-perf, and kafka dashboards required no content changes — all already had lowercase prometheus uid from prior work"
  - "Flink dashboard completely replaced (not patched) — 2-panel stub had capital-P uid and wrong panel structure"

patterns-established:
  - "Every Grafana panel datasource object: { type: prometheus, uid: prometheus } (lowercase uid matches pinned datasource from plan 72-01)"

requirements-completed: [MON-05, MON-06, MON-07]

# Metrics
duration: 4min
completed: 2026-03-31
---

# Phase 72 Plan 02: Grafana Dashboard Expansion Summary

**10-panel Flink debug dashboard with job uptime, checkpoint health, record throughput, watermark lag, and JVM heap — replacing 2-panel stub; all four dashboards confirmed with correct lowercase prometheus datasource UID**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T11:37:49Z
- **Completed:** 2026-03-31T11:41:33Z
- **Tasks:** 2 (checkpoint task pending human verification)
- **Files modified:** 1 (grafana-dashboard-flink.yaml replaced; 3 others verified correct)

## Accomplishments

- Replaced 2-panel Flink dashboard stub with 10-panel comprehensive dashboard across 5 row sections: Job Overview, Throughput, Checkpointing, Watermarks, JVM Resources
- Fixed capital-P `"uid": "Prometheus"` in Flink dashboard — all panels now use lowercase `{ "type": "prometheus", "uid": "prometheus" }`
- Audited api-health, ml-perf, and kafka dashboards — all three already had correct lowercase uid (no changes required)
- Applied all four ConfigMaps to cluster; Grafana rolled out successfully

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace Flink dashboard stub with 10-panel dashboard** - `c6fd9de` (feat)
2. **Task 2: Audit and confirm datasource UIDs in other three dashboards** - `eabbe8e` (chore)

## Files Created/Modified

- `/home/tempa/Desktop/priv-project/stock-prediction-platform/k8s/monitoring/grafana-dashboard-flink.yaml` - Complete replacement: 10 data panels (3 stat + 7 timeseries) organized in 5 row sections, all using lowercase prometheus datasource UID, covering flink_jobmanager_* and flink_taskmanager_* metrics

## Decisions Made

- Used `kubectl delete` + `kubectl create` for Flink ConfigMap because `kubectl apply` and `kubectl replace` both returned success but left old content in the cluster (annotation patching issue with ConfigMaps not managed by apply from the start)
- api-health, ml-perf, and kafka dashboards were already correct — all had lowercase `"uid": "prometheus"` throughout. Applied to cluster anyway to pick up last-applied-configuration annotation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] kubectl apply/replace did not update ConfigMap content in cluster**
- **Found during:** Task 1 verification
- **Issue:** `kubectl apply` and `kubectl replace` on grafana-dashboard-flink ConfigMap returned success but cluster still served old 2-panel content with version:1
- **Fix:** Used `kubectl delete configmap grafana-dashboard-flink -n monitoring` followed by `kubectl create -f` to force fresh creation
- **Files modified:** None (cluster state fix only)
- **Verification:** `kubectl get configmap grafana-dashboard-flink -o jsonpath='{.data.flink-stream\.json}'` showed version:2, 15 total panels, lastCheckpointDuration present
- **Committed in:** c6fd9de (part of Task 1 commit — file was already correct, cluster apply was the fix)

---

**Total deviations:** 1 auto-fixed (Rule 1 - cluster apply bug)
**Impact on plan:** Required an extra apply step but no scope change. ConfigMap is now correct in cluster.

## Issues Encountered

- `kubectl apply` on pre-existing ConfigMaps (not originally created via apply) patched annotation metadata but did not update `.data` content. `kubectl replace` had the same behavior. Used delete+create to resolve.

## User Setup Required

**Human verification required.** See checkpoint below — all four dashboards are loaded in Grafana and ready for visual inspection.

## Next Phase Readiness

- Grafana is running with the updated 10-panel Flink dashboard loaded
- All four dashboards applied to cluster with correct datasource UIDs
- Human checkpoint: verify dashboards load without "Datasource not found" errors
- Port-forward command: `kubectl port-forward -n monitoring svc/grafana 3000:3000`
- Dashboard URL: http://localhost:3000 (anonymous access, no login required)

## Self-Check: PASSED

- FOUND: stock-prediction-platform/k8s/monitoring/grafana-dashboard-flink.yaml
- FOUND: .planning/phases/72-grafana-debug-dashboards-with-flink-metrics-integration/72-02-SUMMARY.md
- FOUND commit c6fd9de (Task 1)
- FOUND commit eabbe8e (Task 2)

---
*Phase: 72-grafana-debug-dashboards-with-flink-metrics-integration*
*Completed: 2026-03-31*
