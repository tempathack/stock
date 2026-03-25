---
phase: 62
slug: playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 62 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | @playwright/test 1.58.2 |
| **Config file** | `stock-prediction-platform/frontend/playwright.infra.config.ts` (Wave 0 creates) |
| **Quick run command** | `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts --project=grafana` |
| **Full suite command** | `cd stock-prediction-platform/frontend && npm run test:e2e:infra` |
| **Estimated runtime** | ~60–90 seconds (live services, skip-on-unreachable) |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts --project=grafana`
- **After every plan wave:** Run `cd stock-prediction-platform/frontend && npm run test:e2e:infra`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 62-01-01 | 01 | 1 | TEST-INFRA-01 | config | `test -f stock-prediction-platform/frontend/playwright.infra.config.ts` | ❌ W0 | ⬜ pending |
| 62-01-02 | 01 | 1 | TEST-INFRA-01 | unit | `test -f stock-prediction-platform/frontend/tests/e2e/infra/helpers/auth.ts` | ❌ W0 | ⬜ pending |
| 62-02-01 | 02 | 2 | TEST-INFRA-01 | e2e | `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts tests/e2e/infra/grafana.spec.ts` | ❌ W0 | ⬜ pending |
| 62-03-01 | 03 | 2 | TEST-INFRA-02 | e2e | `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts tests/e2e/infra/prometheus.spec.ts` | ❌ W0 | ⬜ pending |
| 62-04-01 | 04 | 2 | TEST-INFRA-03 | e2e | `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts tests/e2e/infra/minio.spec.ts` | ❌ W0 | ⬜ pending |
| 62-05-01 | 05 | 2 | TEST-INFRA-04 | e2e | `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts tests/e2e/infra/kubeflow.spec.ts` | ❌ W0 | ⬜ pending |
| 62-05-02 | 05 | 2 | TEST-INFRA-05 | e2e | `cd stock-prediction-platform/frontend && npx playwright test --config=playwright.infra.config.ts tests/e2e/infra/k8s-dashboard.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/frontend/playwright.infra.config.ts` — multi-project Playwright config for all 5 infra services
- [ ] `stock-prediction-platform/frontend/tests/e2e/infra/helpers/auth.ts` — shared login helpers for Grafana, MinIO, K8s Dashboard
- [ ] `stock-prediction-platform/frontend/tests/e2e/infra/grafana.spec.ts` — Grafana E2E spec stub (TEST-INFRA-01)
- [ ] `stock-prediction-platform/frontend/tests/e2e/infra/prometheus.spec.ts` — Prometheus E2E spec stub (TEST-INFRA-02)
- [ ] `stock-prediction-platform/frontend/tests/e2e/infra/minio.spec.ts` — MinIO Console E2E spec stub (TEST-INFRA-03)
- [ ] `stock-prediction-platform/frontend/tests/e2e/infra/kubeflow.spec.ts` — Kubeflow E2E spec stub (TEST-INFRA-04)
- [ ] `stock-prediction-platform/frontend/tests/e2e/infra/k8s-dashboard.spec.ts` — K8s Dashboard E2E spec stub (TEST-INFRA-05)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grafana dashboard panels render with data | TEST-INFRA-01 | Requires live data in Prometheus/Loki; panels may be empty in CI | Run `npm run test:e2e:infra -- --project=grafana` against deployed stack with data flowing |
| MinIO object upload/list | TEST-INFRA-03 | Requires pre-seeded objects in buckets | Verify model-artifacts and drift-logs buckets contain at least 1 object each |
| K8s Dashboard token auth | TEST-INFRA-05 | `KUBERNETES_DASHBOARD_TOKEN` must be set manually | Run `kubectl -n kubernetes-dashboard create token kubernetes-dashboard`, export, then run suite |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
