---
phase: 68-e2e-integration-v3-0-stack-validation
plan: "02"
subsystem: e2e-playwright-infra
tags: [playwright, e2e, argocd, flink, infra-tests]
dependency_graph:
  requires: [65-argocd-gitops, 67-apache-flink]
  provides: [argocd-ui-playwright-spec, flink-web-ui-playwright-spec]
  affects: [playwright.infra.config.ts, helpers/auth.ts]
tech_stack:
  added: []
  patterns: [probe-skip-serial-no-baseURL, test.fixme-empty-state, env-var-credential-override]
key_files:
  created:
    - stock-prediction-platform/services/frontend/e2e/infra/argocd.spec.ts
    - stock-prediction-platform/services/frontend/e2e/infra/flink-web-ui.spec.ts
  modified:
    - stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts
    - stock-prediction-platform/services/frontend/playwright.infra.config.ts
decisions:
  - "ARGOCD_PASSWORD defaults to empty string — login tests skip gracefully when env var not set"
  - "Flink jobs test uses test.fixme for empty-jobs state (consistent with minio.spec.ts pattern)"
  - "Flink spec probes /overview REST endpoint (not UI) for beforeAll skip — hash-routing makes UI probes unreliable"
  - "playwright.infra.config.ts now has 7 project entries (5 original + argocd + flink-web-ui)"
metrics:
  duration: "99s"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_changed: 4
---

# Phase 68 Plan 02: Argo CD and Flink Web UI Playwright Infra Specs Summary

**One-liner:** Playwright infra specs for Argo CD UI (healthz probe, login, root-app assertion) and Flink Web UI (REST /overview probe, dashboard load, /jobs/overview REST-based job count) following the Phase 62 probe-skip/serial/no-baseURL pattern.

## Objective

Add two Playwright infra specs (argocd.spec.ts and flink-web-ui.spec.ts), update helpers/auth.ts with new URL/credential exports, and register both specs in playwright.infra.config.ts.

## Tasks Completed

| Task | Name | Commit | Files Changed |
|------|------|--------|---------------|
| 1 | Update helpers/auth.ts with ARGOCD_URL, ARGOCD_PASSWORD, FLINK_UI_URL | ce88254 | helpers/auth.ts |
| 2 | Create argocd.spec.ts and flink-web-ui.spec.ts; update playwright.infra.config.ts | 7ca9438 | argocd.spec.ts (new), flink-web-ui.spec.ts (new), playwright.infra.config.ts |

## What Was Built

### helpers/auth.ts
Added three new exports after K8S_DASHBOARD_TOKEN:
- `ARGOCD_URL` — defaults to `http://localhost:8080` (env-var override: `ARGOCD_URL`)
- `ARGOCD_PASSWORD` — defaults to `""` (must be supplied via `ARGOCD_PASSWORD` env var or `argocd admin initial-password`)
- `FLINK_UI_URL` — defaults to `http://localhost:8081` (env-var override: `FLINK_UI_URL`)

All pre-existing exports (GRAFANA_URL, PROMETHEUS_URL, MINIO_URL, KUBEFLOW_URL, K8S_DASHBOARD_URL, K8S_DASHBOARD_TOKEN, login helpers) remain unchanged.

### argocd.spec.ts
Playwright infra spec for Argo CD UI with:
- `beforeAll` probe against `/healthz` — skips entire file with port-forward instructions if Argo CD unreachable
- `test.describe.configure({ mode: "serial" })` — serial mode for live service
- **Availability suite:** `/healthz` non-5xx assertion + root URL redirects to login page
- **Login suite:** fills admin/ARGOCD_PASSWORD, clicks Sign In, asserts Applications list visible (skipped if ARGOCD_PASSWORD empty)
- **Application list suite:** logs in then navigates to `/applications`, asserts `root-app` visible (skipped if ARGOCD_PASSWORD empty)

### flink-web-ui.spec.ts
Playwright infra spec for Flink Web UI with:
- `beforeAll` probe against `/overview` REST endpoint — skips entire file with port-forward instructions if Flink unreachable
- `test.describe.configure({ mode: "serial" })` — serial mode for live service
- **REST API suite:** `/overview` response has `flink-version` field
- **Web Dashboard suite:** navigates to root, asserts Flink branding visible
- **Jobs Overview suite:** hash-router navigation to `/#/overview` (DOM wait, not waitForURL per Phase 62 pattern); REST-based job count via `/jobs/overview` with `test.fixme` for empty-jobs state
- Graceful handling: `console.warn` when jobs present but don't match Phase 67 job names

### playwright.infra.config.ts
Added two project entries to the `projects` array:
```typescript
{ name: "argocd",       testMatch: "**/argocd.spec.ts" },
{ name: "flink-web-ui", testMatch: "**/flink-web-ui.spec.ts" },
```
Total project entries: **7** (grafana, prometheus, minio, kubeflow, k8s-dashboard, argocd, flink-web-ui).

## Usage

```bash
# Run Argo CD spec only
npx playwright test --config playwright.infra.config.ts --project argocd

# Run Flink Web UI spec only
npx playwright test --config playwright.infra.config.ts --project flink-web-ui

# With credentials/URL overrides
ARGOCD_PASSWORD=$(argocd admin initial-password -n argocd | head -1) \
  npx playwright test --config playwright.infra.config.ts --project argocd

# Run all infra specs
npx playwright test --config playwright.infra.config.ts
```

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

Files created/modified:
- FOUND: stock-prediction-platform/services/frontend/e2e/infra/argocd.spec.ts
- FOUND: stock-prediction-platform/services/frontend/e2e/infra/flink-web-ui.spec.ts
- FOUND: stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts (ARGOCD_URL, ARGOCD_PASSWORD, FLINK_UI_URL exports verified)
- FOUND: stock-prediction-platform/services/frontend/playwright.infra.config.ts (7 testMatch entries verified)

Commits:
- ce88254: feat(68-02): add ARGOCD_URL, ARGOCD_PASSWORD, FLINK_UI_URL exports to helpers/auth.ts
- 7ca9438: feat(68-02): add argocd.spec.ts and flink-web-ui.spec.ts; register in playwright.infra.config.ts
