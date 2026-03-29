---
phase: 66
slug: feast-production-feature-store
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 66 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | `stock-prediction-platform/ml/tests/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform && python -m pytest ml/tests/test_feast_store.py -x -p no:logfire` |
| **Full suite command** | `cd stock-prediction-platform && python -m pytest ml/tests/ -p no:logfire` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform && python -m pytest ml/tests/test_feast_store.py -x -p no:logfire`
- **After every plan wave:** Run `cd stock-prediction-platform && python -m pytest ml/tests/ -p no:logfire`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 66-01-01 | 01 | 0 | FEAST-01,02,03,04,05 | unit | `pytest ml/tests/test_feast_store.py ml/tests/test_feast_definitions.py -x` | ❌ W0 | ⬜ pending |
| 66-01-02 | 01 | 1 | FEAST-01 | unit | `pytest ml/tests/test_feast_store.py::TestFeatureStoreConfig -x` | ❌ W0 | ⬜ pending |
| 66-01-03 | 01 | 1 | FEAST-02,03 | unit | `pytest ml/tests/test_feast_definitions.py::TestFeatureViewDefinitions -x` | ❌ W0 | ⬜ pending |
| 66-01-04 | 01 | 1 | FEAST-04 | unit | `pytest ml/tests/test_feast_store.py::TestHistoricalFeatures -x` | ❌ W0 | ⬜ pending |
| 66-01-05 | 01 | 1 | FEAST-05 | unit | `pytest ml/tests/test_feast_store.py::TestOnlineFeatures -x` | ❌ W0 | ⬜ pending |
| 66-02-01 | 02 | 2 | FEAST-06 | unit | `pytest ml/tests/test_feature_engineer.py::TestFeastPath -x` | ❌ W0 | ⬜ pending |
| 66-03-01 | 03 | 3 | FEAST-07 | unit | `pytest services/api/tests/test_predict.py::TestFeastOnlineFeatures -x` | ❌ W0 | ⬜ pending |
| 66-03-02 | 03 | 3 | FEAST-08 | manual | `kubectl get cronjob feast-materialize -n ml` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `ml/tests/test_feast_store.py` — TestFeatureStoreConfig, TestHistoricalFeatures, TestOnlineFeatures (all mocked) — covers FEAST-01, FEAST-04, FEAST-05
- [ ] `ml/tests/test_feast_definitions.py` — TestFeatureViewDefinitions — validates feature_repo.py objects without registry — covers FEAST-02, FEAST-03
- [ ] `ml/tests/test_feature_engineer.py` additions — TestFeastPath class for FEAST-06
- [ ] `services/api/tests/test_predict.py` additions — mock feast online store for FEAST-07
- [ ] `ml/feature_store/__init__.py` — Feast repo directory marker (empty, required by feast apply)
- [ ] `feast[postgres,redis]==0.61.0` added to `ml/requirements.txt`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| K8s CronJob materializes features at 18:30 ET | FEAST-08 | Requires live cluster + data | `kubectl apply -f k8s/ml/cronjob-feast-materialize.yaml && kubectl get cronjob feast-materialize -n ml` — verify schedule is `30 22 * * 1-5` |
| Feast feature server /health responds | FEAST-08 | Requires K8s deployment live | `kubectl port-forward svc/feast-feature-server 6566:6566 -n ml && curl http://localhost:6566/health` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
