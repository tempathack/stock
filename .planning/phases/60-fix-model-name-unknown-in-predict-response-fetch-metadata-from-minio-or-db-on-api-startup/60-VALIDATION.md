---
phase: 60
slug: fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-25
---

# Phase 60 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | stock-prediction-platform/services/api/pytest.ini (or none) |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/test_model_metadata_cache.py -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

Note: All test files live flat in `tests/` (no `unit/` or `integration/` subdirectories). Plan 01 creates `tests/test_model_metadata_cache.py` and adds `test_predict_model_name_not_unknown` to `tests/test_prediction_service.py`.

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/test_model_metadata_cache.py -q`
- **After every plan wave:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 60-01-1a | 01 | 1 | cache unit tests RED | unit | `pytest tests/test_model_metadata_cache.py -q` (expect FAIL) | created in task | ⬜ pending |
| 60-01-1b | 01 | 1 | cache module + config.py | unit | `pytest tests/test_model_metadata_cache.py -q` | ✅ after 1a | ⬜ pending |
| 60-01-2 | 01 | 1 | lifespan + inference wiring + PRED-MNAME-03 | unit | `pytest tests/ -q` | ✅ existing | ⬜ pending |
| 60-02-1 | 02 | 2 | K8s configmap vars | file grep | `grep MINIO_ENDPOINT k8s/ingestion/configmap.yaml` | ✅ | ⬜ pending |
| 60-02-2 | 02 | 2 | K8s secretRef | file grep | `grep minio-secrets k8s/ingestion/fastapi-deployment.yaml` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 is satisfied by Plan 01 Task 1a which creates the test file before implementation. No separate Wave 0 setup step needed — the TDD RED task produces the test scaffold.

- [x] `stock-prediction-platform/services/api/tests/test_model_metadata_cache.py` — created in Task 1a (RED phase)
- [x] `stock-prediction-platform/services/api/tests/test_prediction_service.py` — exists; `test_predict_model_name_not_unknown` added in Task 2

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| K8s ConfigMap has MINIO vars | Phase 60 K8s fix | Requires cluster apply | `kubectl get configmap ingestion-config -n ingestion -o yaml \| grep MINIO` |
| API Pod has minio-secrets mounted | Phase 60 K8s fix | Requires cluster apply | `kubectl get deployment stock-api -n ingestion -o yaml \| grep secretRef` |
| `/predict/AAPL` returns non-unknown model_name | Phase 60 E2E | Requires live cluster | `curl /predict/AAPL \| jq .model_name` must not be "unknown" |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covered by TDD RED task (Task 1a) — no MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
