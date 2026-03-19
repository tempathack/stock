---
phase: 06
slug: yahoo-finance-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | stock-prediction-platform/services/api/pytest.ini |
| **Quick run command** | `python -m pytest services/api/tests/test_yahoo_finance.py services/api/tests/test_kafka_producer.py -q --tb=short -p no:logfire` |
| **Full suite command** | `python -m pytest services/api/tests/ -q --tb=short -p no:logfire` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | INGEST-02 | unit | `pytest tests/test_yahoo_finance.py::test_default_ticker_list -q -p no:logfire` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | INGEST-01 | unit | `pytest tests/test_yahoo_finance.py::test_fetch_intraday -q -p no:logfire` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | INGEST-01 | unit | `pytest tests/test_yahoo_finance.py::test_fetch_historical -q -p no:logfire` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | INGEST-06 | unit | `pytest tests/test_yahoo_finance.py::test_validation -q -p no:logfire` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | INGEST-03 | unit | `pytest tests/test_kafka_producer.py::test_produce_intraday -q -p no:logfire` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | INGEST-03 | unit | `pytest tests/test_kafka_producer.py::test_produce_historical -q -p no:logfire` | ❌ W0 | ⬜ pending |
| 06-02-03 | 02 | 2 | INGEST-03 | unit | `pytest tests/test_kafka_producer.py::test_message_schema -q -p no:logfire` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `services/api/tests/test_yahoo_finance.py` — stubs for INGEST-01, INGEST-02, INGEST-06
- [ ] `services/api/tests/test_kafka_producer.py` — stubs for INGEST-03
- [ ] `services/api/tests/conftest.py` — shared fixtures (mock yfinance, mock confluent Producer)

*Existing infrastructure covers pytest setup (pytest.ini, -p no:logfire flag from Phase 3 decisions).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live yfinance fetch returns non-empty DataFrame | INGEST-01 | Requires network + market hours | Run `python -c "import yfinance as yf; df = yf.download('AAPL', period='1d', interval='1m'); print(len(df), 'rows')"` — expect > 0 rows during market hours |
| Valid records published to Kafka topic | INGEST-03 | Requires live Kafka cluster | Run ingestion function, then consume from intraday-data with kafka-console-consumer — expect JSON messages with ticker, open, high, low, close, volume, timestamp |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
