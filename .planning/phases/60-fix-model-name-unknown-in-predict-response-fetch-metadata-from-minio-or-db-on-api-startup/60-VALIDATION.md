---
phase: 60
slug: fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 60 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | stock-prediction-platform/services/api/pytest.ini (or none — Wave 0 installs) |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/unit/test_model_metadata_cache.py -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/unit/test_model_metadata_cache.py -q`
- **After every plan wave:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 60-01-01 | 01 | 0 | model_name fix | unit stub | `pytest tests/unit/test_model_metadata_cache.py -q` | ❌ W0 | ⬜ pending |
| 60-01-02 | 01 | 1 | boto3 dep | unit | `python -c "import boto3"` | ✅ | ⬜ pending |
| 60-01-03 | 01 | 1 | metadata cache module | unit | `pytest tests/unit/test_model_metadata_cache.py -q` | ❌ W0 | ⬜ pending |
| 60-01-04 | 01 | 1 | lifespan loader | integration | `pytest tests/integration/test_startup_metadata.py -q` | ❌ W0 | ⬜ pending |
| 60-01-05 | 01 | 2 | inference uses cache | unit | `pytest tests/unit/test_prediction_service.py -q` | ✅ | ⬜ pending |
| 60-02-01 | 02 | 2 | K8s configmap vars | manual | inspect configmap.yaml | ✅ | ⬜ pending |
| 60-02-02 | 02 | 2 | K8s secretRef | manual | inspect fastapi-deployment.yaml | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/tests/unit/test_model_metadata_cache.py` — stubs for MinIO load + DB fallback + None fallback
- [ ] `stock-prediction-platform/services/api/tests/integration/test_startup_metadata.py` — stub for lifespan metadata load
- [ ] `stock-prediction-platform/services/api/tests/unit/test_prediction_service.py` — stubs for model_name populated in response

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| K8s ConfigMap has MINIO vars | Phase 60 K8s fix | Requires cluster apply | `kubectl get configmap api-config -n ingestion -o yaml \| grep MINIO` |
| API Pod has minio-secrets mounted | Phase 60 K8s fix | Requires cluster apply | `kubectl get deployment fastapi-deployment -n ingestion -o yaml \| grep secretRef` |
| `/predict/AAPL` returns non-unknown model_name | Phase 60 E2E | Requires live cluster | `curl /predict/AAPL \| jq .model_name` must not be "unknown" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
