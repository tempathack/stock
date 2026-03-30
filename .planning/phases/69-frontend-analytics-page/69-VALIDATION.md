---
phase: 69
slug: frontend-analytics-page
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 69 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + Playwright (E2E) |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/test_analytics.py -x -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_analytics.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 69-01-01 | 01 | 1 | UI-RT-01 | unit | `pytest tests/test_analytics_flink.py -x -q` | ❌ W0 | ⬜ pending |
| 69-01-02 | 01 | 1 | UI-RT-02 | unit | `pytest tests/test_analytics_feast.py -x -q` | ❌ W0 | ⬜ pending |
| 69-01-03 | 01 | 1 | UI-RT-04 | unit | `pytest tests/test_analytics_kafka.py -x -q` | ❌ W0 | ⬜ pending |
| 69-01-04 | 01 | 1 | UI-RT-05 | unit | `pytest tests/test_analytics_argocd.py -x -q` | ❌ W0 | ⬜ pending |
| 69-01-05 | 01 | 2 | UI-RT-01–07 | integration | `pytest tests/test_analytics_router.py -x -q` | ❌ W0 | ⬜ pending |
| 69-02-01 | 02 | 1 | UI-RT-01–07 | E2E | `npx playwright test analytics.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/tests/test_analytics_flink.py` — stubs for UI-RT-01
- [ ] `stock-prediction-platform/services/api/tests/test_analytics_feast.py` — stubs for UI-RT-02
- [ ] `stock-prediction-platform/services/api/tests/test_analytics_kafka.py` — stubs for UI-RT-04
- [ ] `stock-prediction-platform/services/api/tests/test_analytics_argocd.py` — stubs for UI-RT-05
- [ ] `stock-prediction-platform/services/api/tests/test_analytics_router.py` — integration stubs
- [ ] `stock-prediction-platform/frontend/tests/analytics.spec.ts` — Playwright E2E stubs for UI-RT-01–07

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Flink job status badge colors | UI-RT-01 | Visual rendering of MUI Chip colors | Open `/analytics`, verify RUNNING=green, FAILED=red, RESTARTING=amber |
| Feature freshness staleness colors | UI-RT-02 | Visual color thresholds (<15min green, <1h amber, >1h red) | Inspect panel with mocked timestamps |
| Lightweight Charts candle rendering | UI-RT-03 | Canvas-based chart visual validation | Open `/analytics`, switch interval buttons, verify candles render |
| Stream lag line chart | UI-RT-04 | Recharts visual rendering | Open `/analytics`, verify line chart shows partition lag data |
| Responsive layout at 375px | UI-RT-07 | Browser viewport testing | Open DevTools → 375px, verify no horizontal scroll, panels stack vertically |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
