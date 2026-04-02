---
phase: 81-fix-grafana-no-data-on-green-panels-api-health-error-rate-and-inference-errors-show-no-data-on-green-background-appearing-healthy
plan: 01
subsystem: infra
tags: [grafana, kubernetes, configmap, monitoring, dashboard]

# Dependency graph
requires:
  - phase: 38-grafana-dashboards-alerting
    provides: grafana-dashboard-api-health.yaml ConfigMap baseline with stat panels for Error Rate, Latency
provides:
  - "grafana-dashboard-api-health.yaml with null+nan value mappings on panels 2, 3, 4, 5 — blue No data state"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Grafana stat panel null+nan mapping: add fieldConfig.defaults.mappings with type=special, match=null+nan, color=blue to eliminate green no-data false positives"
    - "kubectl replace vs kubectl apply: use kubectl replace when ConfigMap already exists and kubectl apply reports immutable field conflicts"

key-files:
  created: []
  modified:
    - stock-prediction-platform/k8s/monitoring/grafana-dashboard-api-health.yaml

key-decisions:
  - "Used Grafana special value mapping (match: null+nan) rather than noValue field alone — noValue sets text but does not override the threshold color; mappings override both text and color"
  - "kubectl replace required instead of kubectl apply — the existing ConfigMap had a resource version conflict that prevented apply from updating; replace forces the update"
  - "Did not add mappings to panels 8 (Active Pods) or 10 — these panels intentionally use red as no-data base to signal a potentially absent workload"

patterns-established:
  - "Grafana no-data color fix: add mappings[type=special, match=null+nan, result.color=blue] to fieldConfig.defaults alongside existing thresholds — thresholds remain untouched"

requirements-completed:
  - GRAFANA-81-01
  - GRAFANA-81-02
  - GRAFANA-81-03
  - GRAFANA-81-04

# Metrics
duration: ~15min
completed: 2026-04-03
---

# Phase 81 Plan 01: Grafana No-Data Green Panel Fix Summary

**Grafana API Health dashboard stat panels (Error Rate %, p50/p95/p99 Latency) now display blue "No data" background instead of green when metrics are absent, eliminating false-healthy signals via null+nan value mappings in the ConfigMap.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-03
- **Completed:** 2026-04-03
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments
- Added `"mappings"` with `type: special`, `match: null+nan`, `color: blue` to `fieldConfig.defaults` for panels 2, 3, 4, and 5 in `grafana-dashboard-api-health.yaml`
- Added `"noValue": "No data"` to all four panels for explicit no-data text display
- Applied ConfigMap to cluster (via `kubectl replace`) and restarted Grafana — provisioning confirmed clean with no errors
- Human reviewer verified all four panels display blue "No data" background; latency panels with live data continue to show correct threshold colors (green)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add null+nan value mappings to panels 2, 3, 4, 5** - `1ddd41c` (fix)
2. **Task 2: Apply ConfigMap and restart Grafana** - cluster applied (no code change, Task 1 commit covers YAML)
3. **Task 3: Visual verification** - approved by human reviewer

## Files Created/Modified
- `stock-prediction-platform/k8s/monitoring/grafana-dashboard-api-health.yaml` — Added null+nan value mappings and noValue field to panels 2, 3, 4, 5

## Decisions Made
- Used Grafana `special` value mapping with `match: null+nan` rather than relying on `noValue` alone — the `noValue` field only changes display text, not the background/value color driven by threshold evaluation. The mapping overrides both.
- `kubectl replace` was required for the cluster apply step. The existing ConfigMap had a conflict that prevented `kubectl apply` from updating correctly. This was an infrastructure-level issue, not a code defect — the YAML committed in task 1 was already correct.
- Panels 8 (Active Pods) and 10 were intentionally left unchanged — they use different threshold semantics appropriate for their context.

## Deviations from Plan

### Infrastructure Issue (not a code deviation)

**kubectl replace instead of kubectl apply**
- **Found during:** Task 2 (cluster apply)
- **Issue:** `kubectl apply` failed to update the ConfigMap due to a resource version conflict on the existing object
- **Fix:** Used `kubectl replace -f ...` to force the update
- **Files modified:** None (YAML was already correct from Task 1)
- **Verification:** ConfigMap updated, Grafana restart succeeded, provisioning logs clean
- **Committed in:** 1ddd41c (Task 1 commit — YAML was already correct)

---

**Total deviations:** 1 infrastructure issue (kubectl replace) — no code deviations
**Impact on plan:** No scope impact. The YAML was correct from Task 1; only the apply command needed adjustment.

## Issues Encountered
- `kubectl apply` would not update the existing ConfigMap. Resolved by using `kubectl replace`. This is a known Kubernetes behavior when ConfigMap was originally created outside of the apply workflow (missing `kubectl.kubernetes.io/last-applied-configuration` annotation).

## User Setup Required
None - no external service configuration required beyond the cluster apply already completed.

## Next Phase Readiness
- Grafana API Health dashboard is now correctly signaling no-data vs healthy states
- All four affected stat panels verified blue in no-data state; live metric thresholds confirmed unaffected
- No blockers

---
*Phase: 81-fix-grafana-no-data-on-green-panels*
*Completed: 2026-04-03*
