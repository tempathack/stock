---
phase: 68
slug: e2e-integration-v3-0-stack-validation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 68 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash (validate-v3.sh) + Playwright (infra specs) |
| **Config file** | `stock-prediction-platform/services/frontend/playwright.config.ts` |
| **Quick run command** | `bash scripts/validate-v3.sh` |
| **Full suite command** | `bash scripts/validate-v3.sh && npx playwright test e2e/infra/ --project=chromium` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash scripts/validate-v3.sh` (or spec linting for Playwright tasks)
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 68-01-01 | 01 | 1 | V3INT-01 | integration | `bash scripts/validate-v3.sh 2>&1 \| grep OLAP` | ❌ W0 | ⬜ pending |
| 68-01-02 | 01 | 1 | V3INT-02 | integration | `bash scripts/validate-v3.sh 2>&1 \| grep "Argo CD"` | ❌ W0 | ⬜ pending |
| 68-01-03 | 01 | 1 | V3INT-01 | integration | `bash scripts/validate-v3.sh 2>&1 \| grep "schema"` | ❌ W0 | ⬜ pending |
| 68-02-01 | 02 | 2 | V3INT-03 | integration | `bash scripts/validate-v3.sh 2>&1 \| grep "Feast offline"` | ❌ W0 | ⬜ pending |
| 68-02-02 | 02 | 2 | V3INT-04 | integration | `bash scripts/validate-v3.sh 2>&1 \| grep "Feast online"` | ❌ W0 | ⬜ pending |
| 68-02-03 | 02 | 2 | V3INT-05 | integration | `bash scripts/validate-v3.sh 2>&1 \| grep "Flink"` | ❌ W0 | ⬜ pending |
| 68-02-04 | 02 | 2 | V3INT-01 | e2e | `npx playwright test e2e/infra/argocd.spec.ts` | ❌ W0 | ⬜ pending |
| 68-02-05 | 02 | 2 | V3INT-05 | e2e | `npx playwright test e2e/infra/flink-web-ui.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/validate-v3.sh` — main validation script (created in Wave 1)
- [ ] `stock-prediction-platform/services/frontend/e2e/infra/argocd.spec.ts` — Playwright spec (created in Wave 2)
- [ ] `stock-prediction-platform/services/frontend/e2e/infra/flink-web-ui.spec.ts` — Playwright spec (created in Wave 2)

*Wave 0: Script and spec files are the deliverables — they are created, not pre-existing.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OLAP ratio ≥10x printed to stdout | V3INT-01 | Requires live cluster with data | Run `bash scripts/validate-v3.sh` and verify `OLAP ratio: NNx` line shows ≥10 |
| Argo CD sync within 3 min after push | V3INT-02 | Requires live git push + cluster | Run script, observe polling output for `operationState.phase=Succeeded` |
| Flink upsert within 10s | V3INT-05 | Requires live Kafka + Flink cluster | Run script, observe `Row found within Ns` output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
