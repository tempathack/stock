---
phase: 76
slug: ux-polish-backtest-empty-state-and-loading-feedback-icon-tooltips-sector-and-company-names-in-forecasts-horizon-selector-dashboard-below-fold-content-analytics-olap-chart-ticker-selector
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 76 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) + pytest (backend) |
| **Config file** | `stock-prediction-platform/services/frontend/vitest.config.ts` / `stock-prediction-platform/services/api/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/frontend && npm test -- --run` |
| **Full suite command** | `cd stock-prediction-platform/services/frontend && npm test -- --run && cd ../api && pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/frontend && npm test -- --run`
- **After every plan wave:** Run full suite (frontend + backend)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 76-01-01 | 01 | 1 | idle-state | unit | `npm test -- --run Backtest` | ✅ | ⬜ pending |
| 76-01-02 | 01 | 1 | tooltips | manual | Visual inspection | N/A | ⬜ pending |
| 76-02-01 | 02 | 1 | company-name | manual | DB query + browser inspect | N/A | ⬜ pending |
| 76-02-02 | 02 | 1 | 14D horizon | unit | `pytest tests/test_predictions.py -k horizon` | ✅ | ⬜ pending |
| 76-03-01 | 03 | 2 | OLAP ticker | unit | `npm test -- --run OLAPCandleChart` | ✅ | ⬜ pending |
| 76-03-02 | 03 | 2 | freshness-null | unit | `npm test -- --run FeatureFreshness` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — no new test files needed for stubs. Tests can be added inline with implementation tasks.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tooltips on icon buttons | Icon tooltip UX | Visual/hover behavior not unit-testable | Hover over each icon-only button; tooltip must appear within 500ms |
| Company name displayed in table | Forecasts sector/company | Requires live DB with seeded data | Load Forecasts page; Company column must show names not blank |
| Backtest idle prompt visible | Idle state UX | Requires fresh page state | Load Backtest page without running; prompt must be visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
