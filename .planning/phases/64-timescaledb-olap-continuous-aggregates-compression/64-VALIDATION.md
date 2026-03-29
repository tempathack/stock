---
phase: 64
slug: timescaledb-olap-continuous-aggregates-compression
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 64 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/test_candles_router.py -x` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/test_candles_router.py -x`
- **After every plan wave:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 64-02-01 | 02 | 0 | TSDB-01, TSDB-02, TSDB-06 | unit | `pytest tests/test_candles_router.py -x` | ❌ W0 | ⬜ pending |
| 64-01-01 | 01 | 1 | TSDB-01 | unit (mock DB) | `pytest tests/test_candles_router.py::test_candles_1h -x` | ❌ W0 | ⬜ pending |
| 64-01-02 | 01 | 1 | TSDB-02 | unit (mock DB) | `pytest tests/test_candles_router.py::test_candles_daily -x` | ❌ W0 | ⬜ pending |
| 64-01-03 | 01 | 1 | TSDB-03 | manual | `SELECT * FROM timescaledb_information.compression_settings` | N/A | ⬜ pending |
| 64-01-04 | 01 | 1 | TSDB-04 | manual | Verify `show_chunks()` returns compressed chunks after 3 days | N/A | ⬜ pending |
| 64-01-05 | 01 | 1 | TSDB-05 | manual | `SELECT * FROM timescaledb_information.jobs WHERE proc_name='policy_retention'` | N/A | ⬜ pending |
| 64-02-02 | 02 | 2 | TSDB-06 | unit | `pytest tests/test_candles_router.py::test_candles_endpoint_200 -x` | ❌ W0 | ⬜ pending |
| 64-02-03 | 02 | 2 | TSDB-06 | unit | `pytest tests/test_candles_router.py::test_candles_bad_interval -x` | ❌ W0 | ⬜ pending |
| 64-02-04 | 02 | 2 | TSDB-06 | unit | `pytest tests/test_candles_router.py::test_candles_cache_hit -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/tests/test_candles_router.py` — stubs for TSDB-01, TSDB-02, TSDB-06 (unit tests with mocked DB/Redis)

*Existing test infrastructure (pytest.ini, conftest.py, async fixtures) covers all phase requirements — only new test file needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Compression policy registered for `ohlcv_daily` | TSDB-03 | Requires running TimescaleDB background jobs against live DB | `SELECT * FROM timescaledb_information.compression_settings WHERE hypertable_name='ohlcv_daily'` |
| Compression policy registered for `ohlcv_intraday` | TSDB-04 | Requires live DB with chunks older than 3 days | `SELECT * FROM timescaledb_information.jobs WHERE proc_name='policy_compression'` + `SELECT show_chunks('ohlcv_intraday', older_than => INTERVAL '3 days')` |
| Retention policies registered for both tables | TSDB-05 | Requires live DB; retention job doesn't run until chunks are old enough | `SELECT * FROM timescaledb_information.jobs WHERE proc_name='policy_retention'` — expect 2 rows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
