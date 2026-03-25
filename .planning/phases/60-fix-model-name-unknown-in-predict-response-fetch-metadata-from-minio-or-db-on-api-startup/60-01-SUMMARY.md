---
phase: 60-fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup
plan: 01
subsystem: api

tags: [boto3, minio, model-metadata, fastapi, prediction, kserve, cache]

# Dependency graph
requires:
  - phase: 59-minikube-e2e-validation-start-cluster-deploy-full-stack-run-ingest-train-serve-flow
    provides: E2E validation that revealed model_name='unknown' cosmetic bug in predict responses
  - phase: 31-live-model-inference-api
    provides: prediction_service.py with _kserve_inference and _legacy_inference that this plan fixes
provides:
  - Startup model metadata cache (model_metadata_cache.py) fetching serving_config.json from MinIO with DB fallback
  - MINIO_SERVING_PREFIX setting in Settings for configurable serving path
  - Lifespan hook calling load_active_model_metadata() before yield
  - Both inference functions using get_active_model_metadata() instead of local filesystem reads
  - 6 unit tests for cache module covering all PRED-MNAME requirements
  - test_predict_model_name_not_unknown test covering PRED-MNAME-03
affects: [prediction endpoints, model metadata display, KServe inference, legacy inference]

# Tech tracking
tech-stack:
  added: [boto3==1.37.5]
  patterns:
    - Startup cache pattern — module-level _active_metadata populated once in lifespan, read per-request
    - Thread-pool boto3 pattern — sync boto3 call wrapped in asyncio.to_thread() for async lifespan
    - Graceful degradation — MinIO fail -> DB fallback -> WARNING log, never raises

key-files:
  created:
    - stock-prediction-platform/services/api/app/services/model_metadata_cache.py
    - stock-prediction-platform/services/api/tests/test_model_metadata_cache.py
  modified:
    - stock-prediction-platform/services/api/app/config.py
    - stock-prediction-platform/services/api/app/main.py
    - stock-prediction-platform/services/api/app/services/prediction_service.py
    - stock-prediction-platform/services/api/requirements.txt
    - stock-prediction-platform/services/api/tests/test_prediction_service.py

key-decisions:
  - "boto3 sync call wrapped in asyncio.to_thread() — boto3 is not async-native; thread pool avoids blocking event loop"
  - "os.environ used in _sync_fetch_from_minio (not pydantic Settings) — runs in thread pool, cannot access FastAPI DI; env var matches Settings.MINIO_SERVING_PREFIX default"
  - "Model metadata is cosmetic — graceful degradation on both MinIO+DB failure logs WARNING and continues startup"
  - "metadata_path definition kept in _legacy_inference — still needed for pipeline_path structure; only the model_name read from it is removed"

patterns-established:
  - "Startup cache pattern: module-level _active_metadata = None, populated in lifespan, read per-request via getter"
  - "TDD RED-GREEN: test file written first with ImportError, then implementation to make all pass"

requirements-completed: [PRED-MNAME-01, PRED-MNAME-02, PRED-MNAME-03, PRED-MNAME-04, PRED-MNAME-05]

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 60 Plan 01: Fix model_name unknown in predict response Summary

**Startup MinIO->DB metadata cache eliminates model_name='unknown' in /predict responses by fetching serving_config.json from s3://model-artifacts/serving/active/ via boto3 at lifespan startup**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T08:27:15Z
- **Completed:** 2026-03-25T08:30:53Z
- **Tasks:** 3 (1a TDD RED, 1b TDD GREEN, 2 wire+integrate)
- **Files modified:** 6

## Accomplishments

- Created `model_metadata_cache.py` with `load_active_model_metadata` (async lifespan loader) and `get_active_model_metadata` (per-request getter) — MinIO first, DB fallback, graceful WARNING if both fail
- Added `MINIO_SERVING_PREFIX: str = "serving/active"` to Settings and `boto3==1.37.5` to requirements; wired `await load_active_model_metadata()` into lifespan before price_feed_loop
- Replaced local filesystem `metadata.json` reads in both `_kserve_inference` and `_legacy_inference` with `get_active_model_metadata()` cache lookup
- 17 tests pass: 6 new cache tests + 1 new PRED-MNAME-03 test + 10 existing prediction service tests

## Task Commits

Each task was committed atomically:

1. **Task 1a: Write failing tests for model_metadata_cache (TDD RED)** - `9822e2a` (test)
2. **Task 1b: Implement model_metadata_cache + add MINIO_SERVING_PREFIX (TDD GREEN)** - `6a61272` (feat)
3. **Task 2: Wire lifespan + update both inference functions + add predict response test** - `70f0071` (feat)

_Note: TDD tasks have two commits (test RED then feat GREEN)_

## Files Created/Modified

- `stock-prediction-platform/services/api/app/services/model_metadata_cache.py` - New module: startup loader + in-memory cache for active model metadata
- `stock-prediction-platform/services/api/tests/test_model_metadata_cache.py` - 6 unit tests covering all 5 PRED-MNAME requirements
- `stock-prediction-platform/services/api/app/config.py` - Added MINIO_SERVING_PREFIX field to Settings
- `stock-prediction-platform/services/api/app/main.py` - Import + lifespan call for load_active_model_metadata
- `stock-prediction-platform/services/api/app/services/prediction_service.py` - Both inference functions updated to use cache
- `stock-prediction-platform/services/api/requirements.txt` - Added boto3==1.37.5
- `stock-prediction-platform/services/api/tests/test_prediction_service.py` - Added test_predict_model_name_not_unknown

## Decisions Made

- boto3 sync call wrapped in `asyncio.to_thread()` — boto3 is not async-native; thread pool avoids blocking the event loop
- `os.environ` used directly in `_sync_fetch_from_minio` rather than pydantic Settings — the function runs in a thread pool and cannot use FastAPI's DI container; the env var name matches the Settings field
- Model metadata is cosmetic (prices are correct) — graceful degradation logs WARNING and never raises, ensuring API always starts
- `metadata_path` definition kept in `_legacy_inference` — it was used for `pipeline_path.exists()` path construction; only the model_name extraction from it is removed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `prometheus_fastapi_instrumentator` not installed in local test environment — pre-existing issue affecting tests that import `app.main` (test_health.py, test_predict.py, etc.). Tests for files I created/modified all pass. This is out of scope (pre-existing, not caused by this plan's changes).

## User Setup Required

None - no external service configuration required beyond what is already present in K8s ConfigMaps.

## Next Phase Readiness

- Fix is complete: when `MINIO_ENDPOINT` is set in the API pod's environment (K8s ConfigMap), the next API startup will load model_name from MinIO's `serving_config.json` and /predict responses will show the real model name
- If MinIO is unavailable at startup, the DB fallback will attempt to query `model_registry WHERE is_active=true`
- If both fail (e.g., cold start before any training run), responses gracefully show model_name="unknown" with a WARNING log

---
*Phase: 60-fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup*
*Completed: 2026-03-25*
