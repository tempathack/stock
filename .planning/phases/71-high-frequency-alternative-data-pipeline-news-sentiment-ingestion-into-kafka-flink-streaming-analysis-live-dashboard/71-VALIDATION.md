---
phase: 71
slug: high-frequency-alternative-data-pipeline-news-sentiment-ingestion-into-kafka-flink-streaming-analysis-live-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 71 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend) |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 71-01-01 | 01 | 0 | TBD | unit | `pytest tests/test_reddit_producer.py -x -q` | ❌ W0 | ⬜ pending |
| 71-01-02 | 01 | 1 | TBD | integration | `pytest tests/test_sentiment_flink.py -x -q` | ❌ W0 | ⬜ pending |
| 71-02-01 | 02 | 2 | TBD | integration | `pytest tests/test_ws_sentiment.py -x -q` | ❌ W0 | ⬜ pending |
| 71-02-02 | 02 | 3 | TBD | e2e | manual | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/tests/test_reddit_producer.py` — stubs for reddit producer unit tests
- [ ] `stock-prediction-platform/services/api/tests/test_sentiment_flink.py` — stubs for Flink sentiment streaming tests
- [ ] `stock-prediction-platform/services/api/tests/test_ws_sentiment.py` — stubs for WebSocket sentiment endpoint tests

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reddit live feed streams real posts | TBD | Requires live Reddit API credentials | Start reddit-producer, verify messages arrive in Kafka `reddit-raw` topic via `kubectl exec` |
| Live dashboard updates sentiment in browser | TBD | Browser/WebSocket interaction | Open frontend dashboard, observe real-time sentiment panel updating every 60s |
| Flink job checkpoints to MinIO | TBD | Infra state verification | Check MinIO bucket for checkpoint files after Flink job runs 5+ minutes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
