---
phase: 59
slug: minikube-e2e-validation-start-cluster-deploy-full-stack-run-ingest-train-serve-flow
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-24
---

# Phase 59 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (integration tests) |
| **Config file** | `tests/integration/conftest.py` |
| **Quick run command** | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow -x -v` |
| **Full suite command** | `pytest tests/integration/ -v` |
| **Estimated runtime** | ~60s (requires live Minikube + KServe) |

---

## Sampling Rate

- **After every task commit:** `kubectl get inferenceservice -n ml` (cluster health check)
- **Per wave merge:** `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow -v`
- **Phase gate:** Full integration suite green + manual frontend visual check

---

## Requirement → Test Map

| Req ID | Behavior | Test Type | Automated Command | File |
|--------|----------|-----------|-------------------|------|
| KSERV-15-A | KServe InferenceService Ready | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_kserve_inference_service_exists -x` | test_pipeline_to_serving.py:232 |
| KSERV-15-B | KServe predictor pod Running | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_kserve_predictor_pod_running -x` | test_pipeline_to_serving.py:243 |
| KSERV-15-C | model-settings.json in MinIO serving/active/ | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_model_artifact_in_minio -x` | test_pipeline_to_serving.py:255 |
| KSERV-15-D | GET /predict/AAPL returns predicted_price > 0 via KServe | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_predict_endpoint_uses_kserve -x` | test_pipeline_to_serving.py:303 |
| KSERV-15-E | Drift CronJob produces drift_logs entries | integration | `pytest tests/integration/test_drift_cycle.py -x` | test_drift_cycle.py |
| KSERV-15-F | Frontend /forecasts shows AAPL prediction | manual | Navigate `http://localhost:3000/forecasts` | N/A — visual |
| KSERV-15-G | Frontend /drift shows events + retrain logs | manual | Navigate `http://localhost:3000/drift` | N/A — visual |

---

## Wave 0 Gaps

None — all integration tests exist at `tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow`. Tests skip gracefully without a running Minikube+KServe cluster.
