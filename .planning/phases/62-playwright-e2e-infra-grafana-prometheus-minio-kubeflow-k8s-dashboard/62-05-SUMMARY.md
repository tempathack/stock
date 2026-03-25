---
phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard
plan: "05"
subsystem: testing
tags: [playwright, e2e, kubeflow, kubernetes-dashboard, k8s, infra]

# Dependency graph
requires:
  - phase: 62-01
    provides: auth.ts helpers with KUBEFLOW_URL, K8S_DASHBOARD_URL, K8S_DASHBOARD_TOKEN, loginK8sDashboard

provides:
  - kubeflow.spec.ts — 3 hash-router navigation tests for pipeline list, runs, experiments pages
  - k8s-dashboard.spec.ts — 2 tests: bearer token login + cluster workloads overview
  - Complete Phase 62 infra test suite (19 total tests across 5 spec files)

affects: [phase-62, infra-testing, kubeflow, kubernetes-dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hash-router navigation: goto(URL/#/route) then wait for DOM element (not waitForURL)"
    - "Two-stage beforeAll skip: env var check first, then HTTP probe"
    - "Self-documenting skip messages with exact kubectl commands for operator recovery"

key-files:
  created:
    - stock-prediction-platform/services/frontend/e2e/infra/kubeflow.spec.ts
    - stock-prediction-platform/services/frontend/e2e/infra/k8s-dashboard.spec.ts
  modified: []

key-decisions:
  - "Hash-router navigation uses DOM waits not waitForURL — KFP uses /#/ routing; waitForURL does not fire on hash changes"
  - "Two-stage skip for K8s Dashboard: missing token skips first (before HTTP probe), service probe skips second — ordering matters for UX"
  - "Skip messages embed exact kubectl commands (port-forward, create token) so operators can self-serve"
  - "K8S_DASHBOARD_TOKEN non-null assertion (!!) is safe: beforeAll skips all tests if token is undefined"

patterns-established:
  - "Service probe pattern: request.newContext() → GET URL with 5s timeout → skip on 5xx or catch"
  - "Graceful infra tests: all infra specs skip cleanly when services not deployed, suite exits 0"

requirements-completed:
  - TEST-INFRA-04
  - TEST-INFRA-05

# Metrics
duration: 1min
completed: "2026-03-25"
---

# Phase 62 Plan 05: Kubeflow and Kubernetes Dashboard E2E Tests Summary

**Playwright infra suite completed: kubeflow.spec.ts (3 hash-router tests) + k8s-dashboard.spec.ts (2 token-auth tests), bringing Phase 62 to 19 total tests across 5 spec files**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-25T14:05:56Z
- **Completed:** 2026-03-25T14:07:15Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- kubeflow.spec.ts with service probe in beforeAll, graceful skip if KFP not deployed, 3 tests navigating to /#/pipelines, /#/runs, /#/experiments using DOM waits
- k8s-dashboard.spec.ts with two-stage skip (missing token then unreachable service), bearer token login via loginK8sDashboard, 2 cluster overview tests
- Full Phase 62 suite complete: 19 tests (grafana 6 + prometheus 4 + minio 4 + kubeflow 3 + k8s-dashboard 2) confirmed via `--list`

## Task Commits

Each task was committed atomically:

1. **Task 1: Write kubeflow.spec.ts** - `cbf0af8` (feat)
2. **Task 2: Write k8s-dashboard.spec.ts** - `eb2791c` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `stock-prediction-platform/services/frontend/e2e/infra/kubeflow.spec.ts` — Kubeflow Pipelines UI navigation tests; hash-router aware; skips if KFP not deployed
- `stock-prediction-platform/services/frontend/e2e/infra/k8s-dashboard.spec.ts` — K8s Dashboard token auth + cluster overview; two-stage skip logic

## Decisions Made

- Hash-router navigation pattern: `page.goto(URL/#/route)` followed by DOM element wait — `waitForURL` does not fire for hash changes
- Two-stage beforeAll for K8s Dashboard: token check before HTTP probe — if token is missing the HTTP probe is unnecessary and potentially confusing
- Skip messages embed exact kubectl commands (port-forward, create token, proxy) for operator self-service
- `K8S_DASHBOARD_TOKEN!` non-null assertion is correct — TypeScript requires it but runtime safety is guaranteed by the beforeAll skip

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The plan verification grep `grep "waitForURL" e2e/infra/kubeflow.spec.ts && echo "FAIL" || echo "OK"` produced a false FAIL because a comment line contains the phrase "Do NOT use waitForURL". The actual code contains no waitForURL calls — verified with line-specific grep. This is a plan script bug (comment text matching), not a spec issue.

## User Setup Required

To run these tests against live infra, operators need:
- Kubeflow: `kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow`
- K8s Dashboard: `kubectl proxy --port=8001` + `KUBERNETES_DASHBOARD_TOKEN=$(kubectl -n kubernetes-dashboard create token kubernetes-dashboard)`

Tests skip gracefully with exact commands in the skip messages if services are not available.

## Next Phase Readiness

- Phase 62 infra test suite is complete (all 5 spec files present)
- `npm run test:infra` wired and covers all 5 projects
- Suite exits 0 with allowed skips when infra services not deployed

---
*Phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard*
*Completed: 2026-03-25*
