---
phase: 84-fix-loki-alerting-datasource-misconfiguration-alert-rules-fail-to-load-from-loki
plan: 02
subsystem: infra
tags: [grafana, loki, promtail, alerting, kubernetes, monitoring]

requires:
  - phase: 84-01
    provides: Diagnosis of the three Loki alerting root causes (missing uid, missing alerting ConfigMap, broken Promtail path glob)

provides:
  - "Loki datasource with pinned uid: loki in grafana-datasource-configmap.yaml"
  - "grafana-alerting-configmap.yaml with loki-high-error-log-rate alert rule using datasourceUid: loki"
  - "Grafana deployment mounting alerting ConfigMap at /etc/grafana/provisioning/alerting"
  - "Promtail __path__ relabel using _ separator and correct /var/log/pods/*$1_$2_*/$3/*.log glob"
  - "All 5 LOKI-ALERT tests passing GREEN"

affects:
  - monitoring
  - grafana-alerting
  - promtail
  - loki

tech-stack:
  added: []
  patterns:
    - "Grafana datasource UID pinning: always set explicit uid: <name> to survive pod restarts"
    - "Grafana unified alerting provisioning via ConfigMap mounted at /etc/grafana/provisioning/alerting"
    - "Promtail K8s pod log path: separator must be _ matching {ns}_{pod}_{uid}/{container} layout"

key-files:
  created:
    - stock-prediction-platform/k8s/monitoring/grafana-alerting-configmap.yaml
  modified:
    - stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml
    - stock-prediction-platform/k8s/monitoring/promtail-configmap.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-deployment.yaml

key-decisions:
  - "Used uid: loki (matches datasource name) as stable UID to avoid auto-generated hash P8E80F9AEF21F6940"
  - "Alert rule references datasourceUid: loki (stable) not auto-generated hash — rules survive restart"
  - "Promtail __path__ uses separator: _ to match real Kubernetes pod log directory layout"

patterns-established:
  - "Grafana datasource UID pinning: set explicit uid field matching datasource name"
  - "Alert rule datasourceUid must match pinned datasource uid, never an auto-generated hash"

requirements-completed: [LOKI-ALERT-01, LOKI-ALERT-02, LOKI-ALERT-03, LOKI-ALERT-04, LOKI-ALERT-05]

duration: 5min
completed: 2026-04-03
---

# Phase 84 Plan 02: Fix Loki Alerting Datasource Misconfiguration Summary

**Four K8s YAML fixes restoring Grafana unified alerting: pinned Loki datasource UID, new alerting provisioning ConfigMap, corrected Promtail log path glob — all 5 LOKI-ALERT tests GREEN**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-02T23:13:54Z
- **Completed:** 2026-04-02T23:18:45Z
- **Tasks:** 2/3 auto tasks complete (Task 3 is human-verify checkpoint)
- **Files modified:** 4

## Accomplishments

- Added `uid: loki` to Loki datasource in grafana-datasource-configmap.yaml — UID now stable across pod restarts
- Created grafana-alerting-configmap.yaml with loki-high-error-log-rate alert rule referencing `datasourceUid: loki`
- Updated grafana-deployment.yaml to mount alerting ConfigMap at `/etc/grafana/provisioning/alerting`
- Fixed Promtail `__path__` relabel: `separator: /` -> `separator: _`, replacement now `/var/log/pods/*$1_$2_*/$3/*.log`
- All 5 pytest tests in test_loki_alerting.py pass GREEN (214 total passing, 1 pre-existing unrelated failure)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pin Loki datasource UID and fix Promtail path separator** - `e0d1059` (fix)
2. **Task 2: Create grafana-alerting-configmap.yaml and update grafana-deployment.yaml** - `7cbefdd` (feat)
3. **Task 3: Verify Grafana unified alerting after rollout restart** - checkpoint:human-verify (awaiting)

## Files Created/Modified

- `stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml` - Added `uid: loki` to Loki datasource entry
- `stock-prediction-platform/k8s/monitoring/promtail-configmap.yaml` - Fixed `__path__` separator to `_` and glob to `*$1_$2_*/$3/*.log`
- `stock-prediction-platform/k8s/monitoring/grafana-alerting-configmap.yaml` - NEW: ConfigMap with loki-high-error-log-rate alert rule
- `stock-prediction-platform/k8s/monitoring/grafana-deployment.yaml` - Added grafana-alerting volume and volumeMount

## Decisions Made

- Used `uid: loki` (lowercase, matches datasource name) as the stable UID to avoid Grafana's auto-generated hash (`P8E80F9AEF21F6940`) which changes on pod restart
- Alert rule `datasourceUid: loki` matches the pinned datasource UID — cross-linking is explicit and verifiable
- Threshold evaluation step uses `datasourceUid: __expr__` (built-in expression engine) — correctly excluded from UID validation test

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — all edits applied cleanly and tests passed on first run.

## User Setup Required

Task 3 (human-verify checkpoint) requires:
1. `kubectl apply` of all 4 modified/created YAML files
2. `kubectl rollout restart deployment/grafana -n monitoring`
3. `kubectl rollout restart daemonset/promtail -n monitoring`
4. Verify via Grafana API: `curl -s http://admin:admin@localhost:3000/api/v1/provisioning/alert-rules`
   Expected: JSON with `"title": "High Error Log Rate (Loki)"` and `"uid": "loki-high-error-log-rate"`

## Next Phase Readiness

- All YAML fixes committed and test-verified locally
- Cluster apply + Grafana restart required to activate provisioning (Task 3 checkpoint)
- After Task 3 approval: Phase 84 fully complete

---
*Phase: 84-fix-loki-alerting-datasource-misconfiguration-alert-rules-fail-to-load-from-loki*
*Completed: 2026-04-03*
