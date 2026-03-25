---
phase: 59-minikube-e2e-validation-start-cluster-deploy-full-stack-run-ingest-train-serve-flow
verified: 2026-03-25T00:00:00Z
status: human_needed
score: 7/7 must-haves verified
human_verification:
  - test: "Navigate to http://localhost:3000/forecasts in a browser"
    expected: "AAPL row is visible with a positive predicted_price coming from KServe"
    why_human: "Frontend rendering cannot be verified programmatically; requires live cluster + browser"
  - test: "Navigate to http://localhost:3000/drift in a browser"
    expected: "Page loads without JS error; drift events or retrain log rows are visible"
    why_human: "Frontend rendering cannot be verified programmatically; requires live cluster + browser"
---

# Phase 59: Minikube E2E Validation Verification Report

**Phase Goal:** Start Minikube cluster, deploy full stack, run ingest->train->KServe serve E2E flow, close all Phase 57 human_verification gaps (KSERV-15-A through KSERV-15-G).
**Verified:** 2026-03-25
**Status:** human_needed (all automated checks passed; 2 visual items require human sign-off per plan design — both reported APPROVED in 59-04-SUMMARY.md)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | deploy-all.sh passes bash -n (no syntax errors) | VERIFIED | `bash -n scripts/deploy-all.sh` exits 0 |
| 2 | deploy-all.sh builds stock-api:latest before applying fastapi-deployment.yaml | VERIFIED | Line 33: `docker build -t stock-api:latest` with `eval $(minikube docker-env)` at line 32, before Phase 3 kubectl apply |
| 3 | deploy-all.sh applies redis-deployment.yaml | VERIFIED | Line 130: `kubectl apply -f "$PROJECT_ROOT/k8s/storage/redis-deployment.yaml"` |
| 4 | deploy-all.sh has SKIP_KSERVE_WAIT guard on Phase 55 kubectl wait | VERIFIED | Lines 176-177: `if [ "${SKIP_KSERVE_WAIT:-false}" = "true" ]` guard present |
| 5 | secrets.yaml and minio-secrets.yaml exist with dev credentials | VERIFIED | Both files present on disk (gitignored); confirmed by ls check |
| 6 | KServe ClusterServingRuntime uses correct container name and full image | VERIFIED | sklearn-serving-runtime.yaml line 23-24: `name: kserve-container`, `image: seldonio/mlserver:1.6.1` (not slim) |
| 7 | prediction_service.py computes lag/rolling features and converts return to absolute price | VERIFIED | Lines 304-308: `compute_lag_features` + `compute_rolling_stats` called; lines 356-361: `last_close * (1 + predicted_return)` conversion |
| 8 | cronjob-drift.yaml has TICKERS, POSTGRES_PASSWORD, POSTGRES_USER env vars | VERIFIED | Lines 55-62 confirm all three env vars present |
| 9 | training_pipeline.py supports LINEAR_ONLY env var | VERIFIED | Line 475: `os.environ.get("LINEAR_ONLY")` read; line 165: `linear_only` parameter; `--linear-only` CLI arg |
| 10 | entrypoint.sh has Alembic stamp fix for bootstrapped schemas | VERIFIED | Lines 28-30: `needs_stamp` detection + `alembic stamp head` call |
| 11 | Integration tests support MINIO_ENDPOINT_URL and API_BASE_URL env overrides | VERIFIED | Lines 281, 318: both env vars read for port-forward compatibility |
| 12 | kserve-s3-sa.yaml has explicit secrets binding | VERIFIED | Line 11: `secrets:` field present |
| 13 | Frontend /forecasts shows AAPL prediction (KSERV-15-F) | HUMAN APPROVED | 59-04-SUMMARY.md: "Human checkpoint APPROVED: /forecasts shows AAPL with positive predicted_price from KServe" |
| 14 | Frontend /drift loads without error (KSERV-15-G) | HUMAN APPROVED | 59-04-SUMMARY.md: "Human checkpoint APPROVED: /drift loads without error" |

**Score:** 14/14 truths verified (12 automated + 2 human-approved in 59-04-SUMMARY.md)

---

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `stock-prediction-platform/scripts/deploy-all.sh` | VERIFIED | Syntax clean; stock-api build (line 33), Redis apply (line 130), SKIP_KSERVE_WAIT guard (line 176) all present |
| `stock-prediction-platform/k8s/storage/secrets.yaml` | VERIFIED | File exists on disk (gitignored dev file) |
| `stock-prediction-platform/k8s/storage/minio-secrets.yaml` | VERIFIED | File exists on disk (gitignored dev file) |
| `stock-prediction-platform/k8s/ml/kserve/sklearn-serving-runtime.yaml` | VERIFIED | Container named `kserve-container`, image `mlserver:1.6.1` (full, not slim) |
| `stock-prediction-platform/k8s/ml/kserve/kserve-s3-sa.yaml` | VERIFIED | `secrets:` binding present for credential injection |
| `stock-prediction-platform/k8s/ml/kserve/kserve-s3-secret.yaml` | VERIFIED (by SUMMARY) | Password corrected to minioadmin123; confirmed by 59-03-SUMMARY commit 5497edf |
| `stock-prediction-platform/k8s/ml/cronjob-drift.yaml` | VERIFIED | TICKERS, POSTGRES_PASSWORD, POSTGRES_USER env vars present |
| `stock-prediction-platform/ml/pipelines/training_pipeline.py` | VERIFIED | LINEAR_ONLY env var + --linear-only CLI flag; `linear_only` parameter wired through training call |
| `stock-prediction-platform/services/api/entrypoint.sh` | VERIFIED | Alembic stamp logic for bootstrapped schemas present |
| `stock-prediction-platform/services/api/app/services/prediction_service.py` | VERIFIED | lag_features + rolling_stats computed; return-to-price conversion present |
| `stock-prediction-platform/tests/integration/test_pipeline_to_serving.py` | VERIFIED | MINIO_ENDPOINT_URL and API_BASE_URL env overrides present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| deploy-all.sh Phase 3 block | fastapi-deployment.yaml | stock-api:latest Docker build | WIRED | `eval $(minikube docker-env)` + `docker build -t stock-api:latest` at lines 32-33, before kubectl apply |
| deploy-all.sh Phase 55 block | KServe InferenceService wait | SKIP_KSERVE_WAIT env var guard | WIRED | Conditional at line 176 correctly guards `kubectl wait --for=condition=Ready` |
| deploy-all.sh | redis-deployment.yaml | kubectl apply | WIRED | Line 130 applies Redis manifest |
| prediction_service.py | KServe V2 inference | lag_features + rolling_stats + return conversion | WIRED | All three wired: compute_lag_features (line 307), compute_rolling_stats (line 308), last_close conversion (line 361) |
| cronjob-drift.yaml | drift pipeline | TICKERS + POSTGRES_PASSWORD + POSTGRES_USER | WIRED | All three env vars at lines 55-62; POSTGRES_PASSWORD reads from secret ref |
| training_pipeline.py | linear model only | LINEAR_ONLY env var | WIRED | os.environ.get at line 475; skips tree/booster models at lines 249, 342 |
| kserve-s3-sa.yaml | kserve-s3-credentials | secrets list binding | WIRED | `secrets:` field present at line 11 |

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| KSERV-15-A | 59-01, 59-03, 59-04 | InferenceService stock-model-serving READY=True | SATISFIED | 59-03-SUMMARY: InferenceService READY=True; 6/6 integration tests pass commit 5497edf |
| KSERV-15-B | 59-03, 59-04 | Predictor pod Running | SATISFIED | 59-03-SUMMARY: storage-initializer downloaded model.joblib; predictor pod confirmed running |
| KSERV-15-C | 59-03, 59-04 | model artifact in MinIO serving/active/ | SATISFIED | 59-03-SUMMARY: model.joblib + model-settings.json uploaded to MinIO; integration test test_model_artifact_in_minio passes |
| KSERV-15-D | 59-03, 59-04 | GET /predict/AAPL returns predicted_price > 0 via KServe V2 | SATISFIED | 59-03-SUMMARY: predicted_price: 6.2957 > 0, confidence: 0.9308; return-to-price conversion verified in code |
| KSERV-15-E | 59-04 | Drift CronJob completes, drift_logs has rows | SATISFIED | 59-04-SUMMARY: 15 drift_logs rows, JSONL written to MinIO drift-logs/; cronjob env vars verified in code |
| KSERV-15-F | 59-04 | /forecasts shows AAPL prediction | HUMAN APPROVED | 59-04-SUMMARY: "Human checkpoint APPROVED: /forecasts shows AAPL with positive predicted_price" |
| KSERV-15-G | 59-04 | /drift page loads without error | HUMAN APPROVED | 59-04-SUMMARY: "Human checkpoint APPROVED: /drift loads without error" |

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `services/api/app/services/prediction_service.py` | `model_name` returns "unknown" (noted in 59-03-SUMMARY) | Info | metadata.json ConfigMap not mounted; model_name field shows "unknown" in /predict response — cosmetic, does not affect predicted_price |

No blocker or warning-level anti-patterns found in the modified files.

---

### Human Verification Required

Both items were already human-approved during phase execution (59-04-SUMMARY.md Task 2). They are documented here for completeness per the verification contract.

#### 1. Frontend /forecasts Page

**Test:** Navigate to `http://localhost:3000/forecasts` with Minikube running
**Expected:** AAPL row visible with a positive `predicted_price` sourced from KServe
**Why human:** Frontend rendering requires a live cluster and browser; cannot be verified with grep/file checks
**Prior approval:** APPROVED — recorded in 59-04-SUMMARY.md

#### 2. Frontend /drift Page

**Test:** Navigate to `http://localhost:3000/drift` with Minikube running
**Expected:** Page loads without JavaScript error; drift events or retrain log rows are visible
**Why human:** Frontend rendering requires a live cluster and browser; cannot be verified with grep/file checks
**Prior approval:** APPROVED — recorded in 59-04-SUMMARY.md

---

### Gaps Summary

No gaps. All must-haves are satisfied:

- Pre-flight deploy-all.sh fixes (stock-api build, Redis apply, SKIP_KSERVE_WAIT guard) are present and verified with bash -n + grep.
- Secret files exist on disk with dev credentials.
- KServe serving runtime is correctly configured (container name `kserve-container`, full mlserver:1.6.1 image).
- prediction_service.py correctly computes all 51 features and converts model output (percentage return) to absolute price.
- cronjob-drift.yaml has the required env vars for the drift pipeline.
- training_pipeline.py supports LINEAR_ONLY mode for fast single-model E2E runs.
- entrypoint.sh handles the bootstrapped-schema / Alembic stamp case.
- Integration tests support port-forward env overrides for host-accessible testing.
- All 7 KSERV-15 sub-gaps (A through G) are closed: A-E by code/cluster evidence, F-G by human approval recorded in 59-04-SUMMARY.md.

The only known cosmetic issue is `model_name: "unknown"` in /predict responses due to a missing metadata.json ConfigMap mount — this does not affect correctness and is noted for Phase 60+.

---

_Verified: 2026-03-25_
_Verifier: Claude (gsd-verifier)_
