---
phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard
plan: "03"
subsystem: testing
tags: [playwright, prometheus, e2e, promql, codemirror, infra]

# Dependency graph
requires:
  - phase: 62-01
    provides: "PROMETHEUS_URL export from helpers/auth.ts, playwright.infra.config.ts with prometheus project"

provides:
  - "prometheus.spec.ts with 4 E2E tests: PromQL query execution, homepage load, targets page, and alerts page"
  - "beforeAll availability probe pattern that skips suite when Prometheus unreachable"

affects:
  - 62-04
  - 62-05

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Service probe pattern: beforeAll request.newContext().get(/-/healthy) with skip-on-failure"
    - "CodeMirror 6 input: .cm-content.click() + keyboard.type() instead of page.fill()"
    - "Serial mode for live-service infra tests to avoid concurrency issues"
    - "Alert assertion on rule names (not state) to avoid flakiness from live metric variability"

key-files:
  created:
    - stock-prediction-platform/services/frontend/e2e/infra/prometheus.spec.ts
  modified: []

key-decisions:
  - "CodeMirror 6 input handled via .cm-content.click() + keyboard.type() — page.fill() is unreliable on CodeMirror editors"
  - "Alert tests assert rule names (HighDriftSeverity, HighAPIErrorRate, HighConsumerLag) not alert state — state depends on live metrics and would be flaky"
  - "Results selector uses .graph-root, table.table — Prometheus may render graph canvas or table depending on query type"
  - "test.describe.configure({ mode: serial }) applied at file level — live service calls are not parallelism-safe"

patterns-established:
  - "beforeAll probe pattern: request.newContext().get(health-endpoint) with test.skip(true, message) on failure"
  - "Infra spec file structure: probe → serial config → describe blocks by feature area"

requirements-completed:
  - TEST-INFRA-02

# Metrics
duration: 1min
completed: 2026-03-25
---

# Phase 62 Plan 03: Prometheus E2E Tests Summary

**Playwright E2E spec for Prometheus covering PromQL query execution via CodeMirror, kubernetes-pods targets page, and alert rule name assertions — with beforeAll availability probe skipping the suite when Prometheus is unreachable.**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-25T14:05:49Z
- **Completed:** 2026-03-25T14:06:27Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created prometheus.spec.ts with 4 tests across 3 describe blocks (query execution x2, targets x1, alerts x1)
- Implemented beforeAll service probe that skips entire suite with descriptive message when Prometheus is unreachable
- Handled CodeMirror 6 query input correctly using .cm-content.click() + keyboard.type() (not page.fill())
- Alert assertions use rule names from prometheus-configmap.yaml, not live alert state, preventing flakiness

## Task Commits

Each task was committed atomically:

1. **Task 1: Write prometheus.spec.ts — query execution, targets, and alerts** - `e3e022c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `stock-prediction-platform/services/frontend/e2e/infra/prometheus.spec.ts` - 4 Prometheus E2E tests with availability probe, query execution, targets, and alerts coverage

## Decisions Made

- CodeMirror 6 input via .cm-content click + keyboard.type per RESEARCH.md Pitfall 6 — page.fill() does not work reliably on CodeMirror editors
- Alert tests check for rule name visibility only, not firing/pending state — state depends on live cluster metrics and would cause non-deterministic failures
- Results selector covers both `.graph-root` and `table.table` since Prometheus renders either depending on result type

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Prometheus E2E tests skip gracefully when the service is not running.

## Next Phase Readiness

- prometheus.spec.ts complete with 4 tests; `npx playwright test --config playwright.infra.config.ts --project=prometheus` ready to run against live Prometheus
- Wave 2 Prometheus tests done; next plans cover MinIO, Kubeflow, and K8s Dashboard
- TEST-INFRA-02 requirement fulfilled

## Self-Check

- [x] `stock-prediction-platform/services/frontend/e2e/infra/prometheus.spec.ts` exists
- [x] Commit e3e022c exists
- [x] `--list` shows exactly 4 tests

## Self-Check: PASSED

---
*Phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard*
*Completed: 2026-03-25*
