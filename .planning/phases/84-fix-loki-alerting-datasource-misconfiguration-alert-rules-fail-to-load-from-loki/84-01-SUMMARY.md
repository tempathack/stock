---
phase: 84-fix-loki-alerting-datasource-misconfiguration-alert-rules-fail-to-load-from-loki
plan: 01
subsystem: testing
tags: [pytest, loki, grafana, promtail, alerting, k8s, yaml]

# Dependency graph
requires: []
provides:
  - "Pytest RED baseline for 5 Loki alerting requirements (LOKI-ALERT-01 through 05)"
  - "test_loki_alerting.py scaffold verifying datasource UID, alerting ConfigMap, alert rule UIDs, Promtail separator, deployment mount"
affects:
  - 84-02 (GREEN phase — K8s YAML fixes must pass these tests)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED scaffold: K8S_MONITORING path resolution via 4x pathlib parent from tests/"
    - "Inner YAML parsing: yaml.safe_load of ConfigMap data values to inspect Grafana provisioning config"

key-files:
  created:
    - stock-prediction-platform/services/api/tests/test_loki_alerting.py
  modified: []

key-decisions:
  - "K8S_MONITORING resolved as pathlib.Path(__file__).parent.parent.parent.parent / 'k8s' / 'monitoring' — consistent with test_dashboard_json.py pattern"
  - "Tests assert against file existence (alerting configmap) rather than skipping — ensures clear RED failure message"

patterns-established:
  - "Pattern: ConfigMap inner YAML loaded via yaml.safe_load(cm['data'][key]) for nested YAML in K8s ConfigMaps"
  - "Pattern: RED tests fail with descriptive AssertionError messages showing exactly what YAML change is needed"

requirements-completed:
  - LOKI-ALERT-01
  - LOKI-ALERT-02
  - LOKI-ALERT-03
  - LOKI-ALERT-04
  - LOKI-ALERT-05

# Metrics
duration: 5min
completed: 2026-04-03
---

# Phase 84 Plan 01: Loki Alerting Test Scaffold Summary

**Five pytest tests establishing the RED baseline for Loki alerting fixes: datasource UID pinning, alerting ConfigMap existence, stable datasourceUid in alert rules, Promtail underscore separator, and Grafana deployment mount.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-03T11:31:30Z
- **Completed:** 2026-04-03T11:36:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `test_loki_alerting.py` with 5 test functions covering all LOKI-ALERT requirements
- Confirmed all 5 tests fail RED against current unmodified YAML files
- Path resolution follows the established `test_dashboard_json.py` pattern (4x parent from tests/)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing test scaffold for all 5 Loki alerting requirements** - `89fcf50` (test)

## Files Created/Modified

- `stock-prediction-platform/services/api/tests/test_loki_alerting.py` - 5 failing pytest tests for Loki alerting requirements

## Decisions Made

- Used `pathlib.Path(__file__).parent.parent.parent.parent` for K8S_MONITORING — consistent with existing `test_dashboard_json.py` pattern
- Tests fail with descriptive assertion messages that tell the developer exactly what YAML field to add/change in Plan 02

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RED baseline established; Plan 02 can now apply the K8s YAML fixes to turn tests GREEN
- Tests cover: `grafana-datasource-configmap.yaml` (uid field), `grafana-alerting-configmap.yaml` (new file), `promtail-configmap.yaml` (separator), `grafana-deployment.yaml` (volumeMount)

---
*Phase: 84-fix-loki-alerting-datasource-misconfiguration-alert-rules-fail-to-load-from-loki*
*Completed: 2026-04-03*
