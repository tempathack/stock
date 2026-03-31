---
phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard
plan: "01"
subsystem: testing
tags: [playwright, e2e, grafana, prometheus, minio, kubeflow, k8s-dashboard, typescript]

# Dependency graph
requires: []
provides:
  - playwright.infra.config.ts: standalone Playwright config for 5 infra service projects (grafana, prometheus, minio, kubeflow, k8s-dashboard)
  - e2e/infra/helpers/auth.ts: shared credentials and login helpers for all infra specs
  - package.json test:infra script: npm entry point for running the infra test suite
affects:
  - 62-02 (grafana spec)
  - 62-03 (prometheus spec)
  - 62-04 (minio spec)
  - 62-05 (kubeflow spec)
  - 62-06 (k8s-dashboard spec, if applicable)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Separate Playwright config per test domain (app vs infra) — no shared baseURL, no webServer block"
    - "Env-var overrides with localhost dev defaults for all infra service URLs and credentials"
    - "loginGrafana/loginMinIO/loginK8sDashboard helpers with resilient locators (ID fallbacks, radio detection)"

key-files:
  created:
    - stock-prediction-platform/services/frontend/playwright.infra.config.ts
    - stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts
  modified:
    - stock-prediction-platform/services/frontend/package.json

key-decisions:
  - "No webServer block in playwright.infra.config.ts — infra services are already running via kubectl port-forward"
  - "No baseURL — each spec sets its own origin via named URL exports (GRAFANA_URL, PROMETHEUS_URL, etc.)"
  - "fullyParallel: false, workers: 1 — infra tests run serially to avoid port-forward connection conflicts"
  - "MINIO_USER default is minioadmin, MINIO_PASSWORD is minioadmin123 matching actual MinIO deployment defaults"
  - "K8S_DASHBOARD_TOKEN has no hardcoded default — must be supplied via KUBERNETES_DASHBOARD_TOKEN env var"
  - "loginMinIO uses ID-based locators (input#accessKey, input#secretKey) with aria-label fallback for resilience"
  - "loginK8sDashboard detects radio button presence with 3s timeout before falling back to direct token input"

patterns-established:
  - "Pattern 1: Infra test separation — playwright.infra.config.ts vs playwright.config.ts keeps app and infra tests independent"
  - "Pattern 2: Credential exports with env-var override — process.env.VAR ?? 'default' for all URLs and credentials"
  - "Pattern 3: Resilient login helpers — primary locator OR fallback locator via .or() for cross-version UI compat"

requirements-completed: [TEST-INFRA-01, TEST-INFRA-02, TEST-INFRA-03, TEST-INFRA-04, TEST-INFRA-05]

# Metrics
duration: 1min
completed: "2026-03-25"
---

# Phase 62 Plan 01: Playwright Infra Test Infrastructure Summary

**Playwright infra test scaffold with standalone config (5 named projects), shared auth helpers for Grafana/MinIO/K8s Dashboard, and npm test:infra entry point**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-25T14:02:37Z
- **Completed:** 2026-03-25T14:03:49Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created `playwright.infra.config.ts` with 5 named projects (grafana, prometheus, minio, kubeflow, k8s-dashboard), no webServer block, no baseURL, workers: 1, fullyParallel: false
- Created `e2e/infra/helpers/auth.ts` exporting all 10 credential constants and 3 login helper functions with resilient locators
- Added `test:infra`, `test:infra:grafana`, and `test:infra:headed` scripts to package.json preserving all existing scripts

## Task Commits

Each task was committed atomically:

1. **Task 1: Create playwright.infra.config.ts and e2e/infra/helpers/auth.ts** - `938adcd` (feat)
2. **Task 2: Add test:infra npm script to package.json** - `ad26e4f` (feat)

## Files Created/Modified
- `stock-prediction-platform/services/frontend/playwright.infra.config.ts` - Standalone Playwright config for 5 infra service projects; testDir ./e2e/infra; no webServer
- `stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts` - Shared credentials (GRAFANA_URL/USER/PASSWORD, PROMETHEUS_URL, MINIO_URL/USER/PASSWORD, KUBEFLOW_URL, K8S_DASHBOARD_URL/TOKEN) and loginGrafana/loginMinIO/loginK8sDashboard helpers
- `stock-prediction-platform/services/frontend/package.json` - Added test:infra, test:infra:grafana, test:infra:headed scripts

## Decisions Made
- No webServer block in playwright.infra.config.ts — infra services run via kubectl port-forward, not started by Playwright
- No baseURL — each spec navigates to its own service URL using named constants from auth.ts
- Workers: 1, fullyParallel: false to prevent port-forward connection conflicts during serial infra test execution
- K8S_DASHBOARD_TOKEN references process.env.KUBERNETES_DASHBOARD_TOKEN (no hardcoded default) — token must be supplied externally
- loginMinIO uses input#accessKey / input#secretKey ID locators with aria-label fallback for cross-MinIO-version resilience

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required for this plan. Credential env vars (GRAFANA_URL, MINIO_USER, etc.) have dev defaults; KUBERNETES_DASHBOARD_TOKEN must be set when running k8s-dashboard specs against a live cluster.

## Next Phase Readiness
- Wave 1 foundation complete: playwright.infra.config.ts and helpers/auth.ts are ready for all 5 spec files
- Plans 02-05 can import from `./helpers/auth` and use the named Playwright projects from this config
- All 5 named projects (grafana, prometheus, minio, kubeflow, k8s-dashboard) are wired up and awaiting spec files

---
*Phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard*
*Completed: 2026-03-25*

## Self-Check: PASSED

- FOUND: stock-prediction-platform/services/frontend/playwright.infra.config.ts
- FOUND: stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts
- FOUND: .planning/phases/62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard/62-01-SUMMARY.md
- FOUND: commit 938adcd (Task 1)
- FOUND: commit ad26e4f (Task 2)
- FOUND: commit a5c0701 (docs metadata)
