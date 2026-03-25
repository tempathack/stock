---
phase: 60-fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup
verified: 2026-03-25T12:00:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 60: Fix model_name unknown in predict response — Verification Report

**Phase Goal:** Fix model_name returning "unknown" in predict response by loading model metadata from MinIO (serving_config.json at s3://model-artifacts/serving/active/) or DB fallback (model_registry WHERE is_active=true) on API startup, then returning the real model_name in /predict/{ticker} responses.
**Verified:** 2026-03-25T12:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | GET /predict/AAPL returns model_name that is not "unknown" when startup metadata load succeeds | VERIFIED (E2E) | kubectl logs: "active model metadata loaded: model_name=stacking_ensemble scaler=meta_ridge version=1"; all 5 tickers confirmed returning model_name="stacking_ensemble_meta_ridge" |
| 2  | get_active_model_metadata() returns a dict with model_name key from the startup cache | VERIFIED | model_metadata_cache.py line 22-29: returns _active_metadata or _SAFE_DEFAULT.copy() with model_name key; confirmed by 6/6 unit tests pass |
| 3  | load_active_model_metadata() fetches serving_config.json from MinIO s3://model-artifacts/serving/active/ | VERIFIED | _sync_fetch_from_minio() at line 60-96: s3.get_object(Bucket=bucket, Key="serving/active/serving_config.json"); test_minio_fetch_uses_s3_path asserts Bucket="model-artifacts", Key="serving/active/serving_config.json" |
| 4  | load_active_model_metadata() falls back to model_registry DB query when MinIO fails | VERIFIED | load_active_model_metadata() line 41-42: if result is None: result = await _fetch_from_db(); test_db_fallback_queries_active_model confirms this path |
| 5  | API starts successfully even when both MinIO and DB are unavailable (logs WARNING, continues) | VERIFIED | Exception handler at line 56-57 catches all errors and logs warning; test_startup_failure_does_not_raise passes (both sources raise Exception, no raise propagated) |
| 6  | API Pod receives MINIO_ENDPOINT, MINIO_BUCKET_MODELS, MINIO_SERVING_PREFIX via ConfigMap | VERIFIED | configmap.yaml lines 24-26 contain all three keys |
| 7  | API Pod receives MINIO_ROOT_USER and MINIO_ROOT_PASSWORD via minio-secrets secretRef | VERIFIED | fastapi-deployment.yaml line 33: secretRef name: minio-secrets |
| 8  | Human confirms /predict/AAPL returns a non-unknown model_name on live cluster | VERIFIED (E2E) | All 5 tickers (AAPL, MSFT, GOOGL, TSLA, NVDA) return model_name="stacking_ensemble_meta_ridge" per 60-02-SUMMARY.md human checkpoint |

**Score:** 8/8 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `stock-prediction-platform/services/api/app/services/model_metadata_cache.py` | Startup loader + in-memory cache; exports load_active_model_metadata, get_active_model_metadata | VERIFIED | 131 lines; exports both functions; _sync_fetch_from_minio and _fetch_from_db implemented; _active_metadata module-level cache present |
| `stock-prediction-platform/services/api/app/config.py` | MINIO_SERVING_PREFIX field in Settings pydantic model | VERIFIED | Line 69: MINIO_SERVING_PREFIX: str = "serving/active" under Group 13 — MinIO / Model Metadata |
| `stock-prediction-platform/services/api/tests/test_model_metadata_cache.py` | Unit tests covering all 5 PRED-MNAME requirements | VERIFIED | 6 tests present; all 6 pass (confirmed by test run: 6 passed in 0.07s) |
| `stock-prediction-platform/services/api/app/main.py` | Import + lifespan call for load_active_model_metadata | VERIFIED | Line 19: import; line 56: await call in lifespan before price_feed_loop yield |
| `stock-prediction-platform/services/api/app/services/prediction_service.py` | Both inference functions use get_active_model_metadata() | VERIFIED | _kserve_inference line 279, _legacy_inference line 443: both import and call get_active_model_metadata(); old metadata_path.exists() filesystem read removed from both model_name resolution blocks |
| `stock-prediction-platform/services/api/requirements.txt` | boto3==1.37.5 | VERIFIED | Line 28: boto3==1.37.5 |
| `stock-prediction-platform/services/api/tests/test_prediction_service.py` | test_predict_model_name_not_unknown test | VERIFIED | Line 139: test present; asserts model_name != "unknown" and == "Ridge_standard" |
| `stock-prediction-platform/k8s/ingestion/configmap.yaml` | MINIO_ENDPOINT, MINIO_BUCKET_MODELS, MINIO_SERVING_PREFIX | VERIFIED | Lines 24-26 contain all three keys with correct values |
| `stock-prediction-platform/k8s/ingestion/fastapi-deployment.yaml` | minio-secrets secretRef in envFrom | VERIFIED | Line 33: secretRef name: minio-secrets |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| app/main.py (lifespan) | app.services.model_metadata_cache.load_active_model_metadata | await load_active_model_metadata() call in lifespan before yield | WIRED | Confirmed: import at line 19, call at line 56 inside lifespan, before yield at line 70 |
| app/services/prediction_service.py (_kserve_inference) | app.services.model_metadata_cache.get_active_model_metadata | cached = get_active_model_metadata() replaces local filesystem read | WIRED | Line 279-291: import and call present; model_display set from cached result; old metadata_path block removed |
| app/services/prediction_service.py (_legacy_inference) | app.services.model_metadata_cache.get_active_model_metadata | cached = get_active_model_metadata() replaces local filesystem read | WIRED | Line 443-455: import and call present; model_name set from cached result |
| k8s/ingestion/fastapi-deployment.yaml (envFrom) | minio-secrets Secret in ingestion namespace | secretRef: name: minio-secrets | WIRED | Line 33 confirmed; 60-02-SUMMARY notes secret copied from storage to ingestion namespace |
| k8s/ingestion/configmap.yaml | model_metadata_cache._sync_fetch_from_minio | MINIO_ENDPOINT env var read via os.environ.get("MINIO_ENDPOINT") | WIRED | ConfigMap carries MINIO_ENDPOINT="http://minio.storage.svc.cluster.local:9000"; _sync_fetch_from_minio reads it at line 67 |

---

## Requirements Coverage

| Requirement ID | Source Plan | Description | Status | Evidence |
|---------------|-------------|-------------|--------|----------|
| PRED-MNAME-01 | 60-01, 60-02 | MinIO serving_config.json fetch at API startup | SATISFIED | _sync_fetch_from_minio fetches s3://model-artifacts/serving/active/serving_config.json; ConfigMap provides MINIO_ENDPOINT to pod |
| PRED-MNAME-02 | 60-01 | DB fallback to model_registry WHERE is_active=true | SATISFIED | _fetch_from_db queries model_registry with is_active=true LIMIT 1; DB fallback unit test passes |
| PRED-MNAME-03 | 60-01 | /predict response returns non-unknown model_name | SATISFIED | Both inference functions use get_active_model_metadata(); test_predict_model_name_not_unknown passes; E2E confirmed for 5 tickers |
| PRED-MNAME-04 | 60-01, 60-02 | API starts gracefully when MinIO/DB unavailable | SATISFIED | Exception handler logs WARNING and continues; test_startup_failure_does_not_raise confirms no raise; K8s pod confirmed running |
| PRED-MNAME-05 | 60-01 | Module-level cache populated once at lifespan, read per-request | SATISFIED | _active_metadata module-level variable; loaded via load_active_model_metadata() in lifespan; read via get_active_model_metadata() per-request |

**Note on REQUIREMENTS.md traceability:** PRED-MNAME-01 through PRED-MNAME-05 are phase-local requirement IDs defined in plan frontmatter. They do not appear in `.planning/REQUIREMENTS.md` (which uses a different ID namespace) and are not listed in the ROADMAP.md traceability table (which ends at phase 57 / KSERV-13-15). This is expected — they are fix-specific IDs introduced in this phase, not project-level v1/v1.1 requirements.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_prediction_service.py` (test_predict_model_name_not_unknown) | 139-158 | Test calls get_active_model_metadata() directly rather than exercising the inference function end-to-end | Info | The test verifies the cache getter logic in isolation, not the prediction_service wiring. PRED-MNAME-03 is substantively covered by E2E evidence (5 tickers confirmed), so this is a test design note, not a blocker. |
| `tests/test_predict.py` | 66 | test_response_schema_fields: pre-existing failure — response includes `assigned_model_id` field not expected by test | Warning | Pre-existing regression from phases 31-57 (A/B testing added assigned_model_id to response). Not introduced by phase 60. 141 of 142 tests pass; 1 pre-existing failure unrelated to this phase. |

---

## Human Verification (Completed)

The following human verification was performed and documented in 60-02-SUMMARY.md:

**Test:** Call /predict/{ticker} on live cluster after API restart with new ConfigMap + secretRef.
**Result:** All 5 tickers (AAPL, MSFT, GOOGL, TSLA, NVDA) returned model_name="stacking_ensemble_meta_ridge".
**Startup log confirmed:** "active model metadata loaded: model_name=stacking_ensemble scaler=meta_ridge version=1"
**Status:** PASSED — human checkpoint approved.

---

## Test Results Summary

- `tests/test_model_metadata_cache.py`: 6/6 passed (0.07s)
- `tests/test_prediction_service.py` (relevant tests): 17/17 passed including test_predict_model_name_not_unknown
- Full suite: 141/142 passed; 1 failure (test_response_schema_fields in test_predict.py) is pre-existing from phases 31-57, not caused by phase 60 changes

---

## Gaps Summary

No gaps. All must-haves from both plans are verified:

- model_metadata_cache.py: substantive, wired into lifespan and both inference functions
- config.py: MINIO_SERVING_PREFIX field added
- requirements.txt: boto3==1.37.5 added
- K8s ConfigMap: 3 MINIO env vars present
- K8s Deployment: minio-secrets secretRef present
- 6 unit tests pass; 1 PRED-MNAME-03 integration test passes
- E2E live cluster: 5/5 tickers return real model_name (not "unknown")
- Graceful degradation on MinIO+DB failure: confirmed by unit test and design

---

_Verified: 2026-03-25T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
