---
phase: 87
slug: point-in-time-correct-feature-serving-feast-kserve-transformer-backtest-lookahead-leakage
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-03
---

# Phase 87 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/api && pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd stock-prediction-platform/services/api && pytest tests/ -q --timeout=60` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `pytest tests/ -q --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Created By | Status |
|---------|------|------|-------------|-----------|-------------------|-----------------|--------|
| 87-01-T1 | 01 | 1 | PIT-02, PIT-03 | structural | `grep -q "class FeastTransformer" services/feast-transformer/feast_transformer.py && echo PASS` | Plan 01 Task 1 | ⬜ pending |
| 87-01-T2 | 01 | 1 | PIT-02, PIT-03 | unit | `cd services/api && pytest tests/test_feast_transformer.py -x -q` | Plan 01 Task 2 | ⬜ pending |
| 87-02-T1 | 02 | 1 | PIT-01 | structural | `grep -q "def assert_no_future_leakage" ml/feature_store/pit_validator.py && echo PASS` | Plan 02 Task 1 | ⬜ pending |
| 87-02-T2 | 02 | 1 | PIT-01, PIT-04 | unit | `cd services/api && pytest tests/test_pit_correctness.py -x -q` | Plan 02 Task 2 | ⬜ pending |
| 87-03-T1 | 03 | 2 | PIT-05 | structural | `grep -q "feast-snapshot-date" k8s/ml/cronjob-feast-materialize.yaml && grep -q "feast-transformer" k8s/ml/kserve/kserve-inference-service.yaml && echo PASS` | Plan 03 Task 1 | ⬜ pending |
| 87-03-T2 | 03 | 2 | PIT-02, PIT-03, PIT-04 | unit | `cd services/api && pytest tests/test_pit_correctness.py tests/test_feast_transformer.py -q` | Plan 03 Task 2 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 is satisfied by the plans themselves — test files are created as part of Plan 01 Task 2 (test_feast_transformer.py) and Plan 02 Task 2 (test_pit_correctness.py). No separate Wave 0 scaffold step is needed.

Test files created by this phase:
- `services/api/tests/test_feast_transformer.py` — KServe Transformer unit tests (Plan 01 Task 2)
- `services/api/tests/test_pit_correctness.py` — PIT correctness validator tests (Plan 02 Task 2)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| KServe Transformer routes requests through preprocess() in RawDeployment mode | PIT-02 | Requires live KServe cluster | Deploy Transformer, send inference request, verify Feast is called via pod logs |
| Backtest returns no future OHLCV rows for historical dates | PIT-01 | Requires production data | Run backtest for a past date, verify no feature rows with timestamp > prediction date |
| ONLINE_FEATURES column order matches trained sklearn pipeline | PIT-02 | Requires MinIO access to read features.json | Read s3://model-artifacts/serving/active/features.json, confirm order matches ONLINE_FEATURES list in feast_transformer.py |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covered: test files created by plan tasks (not pre-existing)
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
