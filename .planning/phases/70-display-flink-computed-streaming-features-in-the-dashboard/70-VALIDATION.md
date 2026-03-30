---
phase: 70
slug: display-flink-computed-streaming-features-in-the-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 70 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + vitest (frontend) |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` / `stock-prediction-platform/frontend/vite.config.ts` |
| **Quick run command** | `cd stock-prediction-platform/services/api && pytest tests/test_feast_online.py -x -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && pytest tests/ -q && cd ../frontend && npm test -- --run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_feast_online.py -x -q`
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 70-01-01 | 01 | 1 | feast-online | unit | `pytest tests/test_feast_online.py -x -q` | ❌ W0 | ⬜ pending |
| 70-01-02 | 01 | 1 | feast-route | integration | `pytest tests/test_feast_online.py -x -q` | ❌ W0 | ⬜ pending |
| 70-02-01 | 02 | 2 | frontend-panel | component | `npm test -- --run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/tests/test_feast_online.py` — stubs for Feast online feature endpoint
- [ ] `stock-prediction-platform/frontend/src/components/__tests__/StreamingFeaturesPanel.test.tsx` — stubs for panel component

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Panel displays live RSI/EMA/MACD values in browser | UI-FLINK-01 | Requires live Flink + Feast stack running | Open dashboard, select symbol, expand StreamingFeaturesPanel, verify 3 metric cards show non-zero values updating every 15s |
| Graceful empty state when Feast offline | UI-FLINK-02 | Requires simulated Feast failure | Stop Redis, reload panel, verify "Feature store unavailable" message shown |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
