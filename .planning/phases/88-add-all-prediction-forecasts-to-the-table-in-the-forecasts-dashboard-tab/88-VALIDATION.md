---
phase: 88
slug: add-all-prediction-forecasts-to-the-table-in-the-forecasts-dashboard-tab
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 88 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) |
| **Config file** | frontend/vitest.config.ts |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose 2>&1 | tail -20` |
| **Full suite command** | `cd frontend && npx vitest run 2>&1 | tail -30` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose 2>&1 | tail -20`
- **After every plan wave:** Run `cd frontend && npx vitest run 2>&1 | tail -30`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 88-01-01 | 01 | 1 | multi-horizon fetch | unit | `cd frontend && npx vitest run --reporter=verbose 2>&1 \| tail -20` | ✅ | ⬜ pending |
| 88-01-02 | 01 | 1 | column grouping render | unit | `cd frontend && npx vitest run --reporter=verbose 2>&1 \| tail -20` | ✅ | ⬜ pending |
| 88-01-03 | 01 | 2 | table display | manual | Playwright browser check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/__tests__/forecasts-table-multi-horizon.test.tsx` — stubs for multi-horizon column rendering

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Multi-horizon columns render in browser | UI correctness | Visual layout can't be verified by unit tests alone | Open /dashboard → Forecasts tab → confirm 1d/7d/14d/30d columns appear per ticker row |
| All 159 tickers show prediction data | Data completeness | Requires live API + KServe | Open /dashboard → Forecasts tab → scroll through table, verify predictions populated |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
