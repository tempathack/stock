---
phase: 61
slug: playwright-e2e-tests-full-frontend-coverage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 61 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | @playwright/test 1.58.2 |
| **Config file** | `stock-prediction-platform/services/frontend/playwright.config.ts` — Wave 0 creates this |
| **Quick run command** | `cd stock-prediction-platform/services/frontend && npx playwright test --project=chromium e2e/dashboard.spec.ts` |
| **Full suite command** | `cd stock-prediction-platform/services/frontend && npx playwright test` |
| **Estimated runtime** | ~60 seconds (5 spec files, Chromium only) |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/frontend && npx playwright test --project=chromium <spec_file> --reporter=line`
- **After every plan wave:** Run `cd stock-prediction-platform/services/frontend && npx playwright test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 61-01-01 | 01 | 1 | TEST-PW-01 | smoke | `cd services/frontend && npx playwright test --list` | ❌ W0 | ⬜ pending |
| 61-01-02 | 01 | 1 | TEST-PW-01 | smoke | `cd services/frontend && npx playwright test --list` | ❌ W0 | ⬜ pending |
| 61-02-01 | 02 | 2 | TEST-PW-02 | e2e | `cd services/frontend && npx playwright test e2e/dashboard.spec.ts` | ❌ W0 | ⬜ pending |
| 61-02-02 | 02 | 2 | TEST-PW-02 | e2e | `cd services/frontend && npx playwright test e2e/dashboard.spec.ts` | ❌ W0 | ⬜ pending |
| 61-03-01 | 03 | 2 | TEST-PW-03 | e2e | `cd services/frontend && npx playwright test e2e/forecasts.spec.ts` | ❌ W0 | ⬜ pending |
| 61-04-01 | 04 | 2 | TEST-PW-04 | e2e | `cd services/frontend && npx playwright test e2e/models.spec.ts e2e/drift.spec.ts` | ❌ W0 | ⬜ pending |
| 61-05-01 | 05 | 2 | TEST-PW-05 | e2e | `cd services/frontend && npx playwright test e2e/backtest.spec.ts` | ❌ W0 | ⬜ pending |
| 61-05-02 | 05 | 2 | TEST-PW-05 | smoke | `cd services/frontend && npx playwright test` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `services/frontend/playwright.config.ts` — Playwright configuration with baseURL, webServer, chromium project
- [ ] `services/frontend/e2e/fixtures/api.ts` — typed fixture factories for all API responses
- [ ] `services/frontend/e2e/dashboard.spec.ts` — stub covering TEST-PW-02
- [ ] `services/frontend/e2e/forecasts.spec.ts` — stub covering TEST-PW-03
- [ ] `services/frontend/e2e/models.spec.ts` — stub covering TEST-PW-04 (Models)
- [ ] `services/frontend/e2e/drift.spec.ts` — stub covering TEST-PW-04 (Drift)
- [ ] `services/frontend/e2e/backtest.spec.ts` — stub covering TEST-PW-05
- [ ] Framework install: `npm install --save-dev @playwright/test@1.58.2 && npx playwright install chromium`
- [ ] npm scripts: `test:e2e`, `test:e2e:ui`, `test:e2e:headed`, `test:e2e:report` in package.json

*Plan 61-01 is Wave 0 — all spec files + config created here before page tests execute in Wave 2.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WebSocket live price updates in Dashboard ticker detail | TEST-PW-02 | Playwright `page.route()` doesn't intercept WebSocket frames — WS mock requires separate setup or test stub | Open Dashboard, click ticker from treemap, verify price updates appear; or add `page.routeWebSocket()` if Playwright 1.48+ WS support is used |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
