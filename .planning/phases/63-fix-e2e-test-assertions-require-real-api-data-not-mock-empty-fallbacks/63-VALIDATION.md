---
phase: 63
slug: fix-e2e-test-assertions-require-real-api-data-not-mock-empty-fallbacks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 63 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright (already installed) |
| **Config file** | `stock-prediction-platform/services/frontend/playwright.config.ts` |
| **Quick run command** | `cd stock-prediction-platform/services/frontend && npx playwright test e2e/dashboard.spec.ts --project chromium` |
| **Full suite command** | `cd stock-prediction-platform/services/frontend && npx playwright test e2e/ --project chromium` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npx playwright test e2e/{spec-file} --project chromium`
- **After every plan wave:** Run full suite `npx playwright test e2e/ --project chromium`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 63-01-01 | 01 | 1 | TBD | e2e | `npx playwright test e2e/dashboard.spec.ts --project chromium` | ✅ | ⬜ pending |
| 63-01-02 | 01 | 1 | TBD | e2e | `npx playwright test e2e/models.spec.ts --project chromium` | ✅ | ⬜ pending |
| 63-01-03 | 01 | 1 | TBD | e2e | `npx playwright test e2e/drift.spec.ts --project chromium` | ✅ | ⬜ pending |
| 63-01-04 | 01 | 1 | TBD | e2e | `npx playwright test e2e/forecasts.spec.ts --project chromium` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed — this phase modifies existing E2E spec files only.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tests skip when backend is down | Phase goal | Requires running backend to be killed during test | Start tests, kill API, verify tests skip not fail |
| Tests skip when DB has no seed data | Phase goal | Requires empty DB environment | Run against fresh DB, verify tests skip |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
