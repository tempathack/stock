---
phase: 89
slug: live-sentiment-timeseries-chart-dashboard-flink-streamed-reddit-news-sentiment-per-stock-2-min-intervals-10-hour-rolling-window
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 89 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend) |
| **Config file** | pytest.ini / vitest.config.ts |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ && cd frontend && npm run test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ && cd frontend && npm run test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 89-01-01 | 01 | 1 | PROMTAIL-FIX | unit | `pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -v` | ✅ | ⬜ pending |
| 89-02-01 | 02 | 1 | SENTIMENT-DB | unit | `pytest tests/ -k sentiment_timeseries -v` | ❌ W0 | ⬜ pending |
| 89-03-01 | 03 | 2 | FLINK-SINK | unit | `pytest tests/ -k flink_jdbc -v` | ❌ W0 | ⬜ pending |
| 89-04-01 | 04 | 2 | API-ENDPOINT | unit | `pytest tests/ -k sentiment_history -v` | ❌ W0 | ⬜ pending |
| 89-05-01 | 05 | 3 | FRONTEND-CHART | e2e | `cd frontend && npm run test -- SentimentTimeseriesChart` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_sentiment_timeseries.py` — stubs for DB migration + Flink sink + API endpoint
- [ ] `frontend/src/components/__tests__/SentimentTimeseriesChart.test.tsx` — component render stubs

*Existing infrastructure:*
- `tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator` — currently RED, existing test specifies exact fix

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chart renders live data in browser | FRONTEND-CHART | Requires running Flink + TimescaleDB stack | Navigate to Dashboard tab, select ticker, verify 10h rolling chart appears with 2-min candles |
| Promtail discovers pods in Loki | PROMTAIL-FIX | Requires live K8s cluster with Loki stack | Check Grafana Explore → Loki → pod labels present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
