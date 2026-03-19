---
phase: 09
slug: kafka-consumers
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | stock-prediction-platform/services/kafka-consumer/pytest.ini |
| **Quick run command** | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -q --tb=short` |
| **Full suite command** | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -v --tb=short` |
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
| 09-01-01 | 01 | 1 | CONS-03 | unit | `pytest tests/test_processor.py::test_add_message -q` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | CONS-03 | unit | `pytest tests/test_processor.py::test_should_flush_batch_size -q` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | CONS-03 | unit | `pytest tests/test_processor.py::test_should_flush_timeout -q` | ❌ W0 | ⬜ pending |
| 09-01-04 | 01 | 1 | CONS-04 | unit | `pytest tests/test_db_writer.py::test_upsert_intraday -q` | ❌ W0 | ⬜ pending |
| 09-01-05 | 01 | 1 | CONS-04 | unit | `pytest tests/test_db_writer.py::test_upsert_daily -q` | ❌ W0 | ⬜ pending |
| 09-01-06 | 01 | 1 | CONS-04 | unit | `pytest tests/test_db_writer.py::test_idempotent_upsert -q` | ❌ W0 | ⬜ pending |
| 09-01-07 | 01 | 1 | CONS-05 | unit | `pytest tests/test_db_writer.py::test_retry_on_operational_error -q` | ❌ W0 | ⬜ pending |
| 09-01-08 | 01 | 1 | CONS-06 | unit | `pytest tests/test_db_writer.py::test_dead_letter_logging -q` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | CONS-01 | unit | `pytest tests/test_main.py::test_consumer_subscribes_to_topics -q` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | CONS-02 | unit | `pytest tests/test_main.py::test_consumer_processes_both_topics -q` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 2 | CONS-07 | manual | Dockerfile builds and K8s deployment applies | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `services/kafka-consumer/tests/__init__.py` — package init
- [ ] `services/kafka-consumer/tests/conftest.py` — shared fixtures (mock Kafka Consumer/messages, mock DB pool)
- [ ] `services/kafka-consumer/tests/test_processor.py` — stubs for CONS-03
- [ ] `services/kafka-consumer/tests/test_db_writer.py` — stubs for CONS-04, CONS-05, CONS-06
- [ ] `services/kafka-consumer/tests/test_main.py` — stubs for CONS-01, CONS-02
- [ ] `services/kafka-consumer/pytest.ini` — pytest configuration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Consumer reads from live Kafka topics | CONS-01/02 | Requires Kafka + PostgreSQL in Minikube | Deploy consumer, produce test messages via FastAPI /ingest, verify rows in ohlcv_daily and ohlcv_intraday |
| Duplicate messages produce no duplicate rows | CONS-04 | Requires live DB to verify ON CONFLICT | Produce same message twice, `SELECT COUNT(*)` for that ticker/date must equal 1 |
| Consumer survives broker restart | CONS-01/02 | Requires cluster manipulation | `kubectl delete pod kafka-kafka-0`, verify consumer reconnects and resumes processing |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
