---
phase: 92
slug: feast-powered-prediction-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 92 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `ml/tests/pytest.ini` and `services/api/pytest.ini` |
| **Quick run command (ML)** | `cd stock-prediction-platform && python -m pytest ml/tests/test_feast_store.py ml/tests/test_data_loader.py -x -q` |
| **Quick run command (API)** | `cd stock-prediction-platform && python -m pytest services/api/tests/test_prediction_service.py -x -q` |
| **Full suite command (ML)** | `cd stock-prediction-platform/ml && python -m pytest tests/ -q` |
| **Full suite command (API)** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds (quick), ~2 minutes (full) |

---

## Sampling Rate

- **After every task commit:** Run quick run command for the affected component (ML or API)
- **After every plan wave:** Run full suite for both `ml/` and `services/api/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 92-01-01 | 01 | 0 | Wave 0 stubs | unit | `pytest ml/tests/test_data_loader.py::TestFeastDataLoader -x` | ❌ W0 | ⬜ pending |
| 92-01-02 | 01 | 0 | Wave 0 stubs | unit | `pytest services/api/tests/test_prediction_service.py::TestFeastInference -x` | ❌ W0 | ⬜ pending |
| 92-01-03 | 01 | 1 | Training features | unit | `pytest ml/tests/test_feast_store.py -x -q` | ✅ extend | ⬜ pending |
| 92-01-04 | 01 | 1 | Feast data loader | unit | `pytest ml/tests/test_data_loader.py::TestFeastDataLoader -x` | ❌ W0 | ⬜ pending |
| 92-02-01 | 02 | 2 | Online inference | unit | `pytest services/api/tests/test_prediction_service.py::TestFeastInference -x` | ❌ W0 | ⬜ pending |
| 92-02-02 | 02 | 2 | Fallback logic | unit | `pytest services/api/tests/test_prediction_service.py::TestFeastInference -x` | ❌ W0 | ⬜ pending |
| 92-02-03 | 02 | 2 | Prometheus counter | unit | `pytest services/api/tests/test_prediction_service.py::TestFeastInference -x` | ❌ W0 | ⬜ pending |
| 92-02-04 | 02 | 2 | feature_freshness_seconds | unit | `pytest services/api/tests/test_predict.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `ml/tests/test_data_loader.py::TestFeastDataLoader` — unit tests for `load_feast_data()` with mocked `FeatureStore`
- [ ] `services/api/tests/test_prediction_service.py::TestFeastInference` — unit tests for rewritten `get_online_features_for_ticker()`, `_feast_inference()`, fallback logic (stale/unavailable), and `feast_stale_features_total` counter emissions
- [ ] New test case in `ml/tests/test_feast_store.py` — assert `_TRAINING_FEATURES` includes all 4 sentiment columns (`positive_ratio`, `negative_ratio`, `avg_sentiment`, `mention_count`) and column names match Feast `to_dict()` key format (bare names, no `view_name:` prefix)

*Wave 0 must be written and passing (even as stubs) before Wave 1 execution begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Kubeflow training pipeline runs end-to-end with Feast offline store | Training retraining | Requires live Kubeflow + Feast cluster | Trigger pipeline run, verify step 1 uses `get_historical_features()` in logs |
| Feast online store returns features for a live ticker | Inference path | Requires Redis + Feast cluster running | Call `/api/v1/predict/{ticker}` with `FEAST_INFERENCE_ENABLED=true`, check `feature_freshness_seconds` in response |
| Fallback triggers for a ticker with stale Feast data | Fallback strategy | Requires controlled Feast staleness | Let Feast TTL expire, call predict endpoint, verify response still returns prediction |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
