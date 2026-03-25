---
phase: 60-fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup
plan: 02
subsystem: infra
tags: [kubernetes, configmap, minio, boto3, model-metadata, stock-api]

# Dependency graph
requires:
  - phase: 60-01
    provides: model_metadata_cache.py — MinIO/DB startup fetch wired into API lifespan

provides:
  - ConfigMap ingestion-config now carries MINIO_ENDPOINT, MINIO_BUCKET_MODELS, MINIO_SERVING_PREFIX
  - fastapi-deployment envFrom references minio-secrets Secret for credentials
  - minio-secrets Secret exists in ingestion namespace (copied from storage)
  - stock-api image rebuilt with Plan 01 model_metadata_cache changes
  - /predict/AAPL returns real model_name from MinIO serving_config.json at startup

affects: [predict-router, model-metadata-cache, ingestion-configmap, fastapi-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "minio-secrets copied cross-namespace (storage -> ingestion) for credential access"
    - "ConfigMap carries MinIO endpoint/bucket/prefix; Secret carries credentials via secretRef"

key-files:
  created: []
  modified:
    - stock-prediction-platform/k8s/ingestion/configmap.yaml
    - stock-prediction-platform/k8s/ingestion/fastapi-deployment.yaml

key-decisions:
  - "minio-secrets copied from storage to ingestion namespace rather than referencing cross-namespace (K8s does not support cross-namespace secretRef)"
  - "ConfigMap provides non-sensitive MinIO config (endpoint, bucket, prefix); Secret provides credentials only"
  - "Stock-api image rebuilt inside minikube Docker context to include Plan 01 model_metadata_cache.py module"

patterns-established:
  - "Cross-namespace Secret copy: kubectl get secret -n source -o yaml | sed namespace | kubectl apply - pattern"

requirements-completed:
  - PRED-MNAME-01
  - PRED-MNAME-04

# Metrics
duration: 35min
completed: 2026-03-25
---

# Phase 60 Plan 02: Fix Model Name Unknown — K8s ConfigMap + Secret Wiring Summary

**MinIO env vars injected into stock-api pod via ConfigMap + secretRef, enabling model_metadata_cache to load `model_name=stacking_ensemble` from MinIO at API startup**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-03-25T08:32:00Z
- **Completed:** 2026-03-25T09:15:00Z
- **Tasks:** 2/2 (all complete including human-verify checkpoint)
- **Files modified:** 2

## Accomplishments

- Added `MINIO_ENDPOINT`, `MINIO_BUCKET_MODELS`, `MINIO_SERVING_PREFIX` to `ingestion-config` ConfigMap
- Added `secretRef: name: minio-secrets` to `fastapi-deployment.yaml` envFrom block
- Copied `minio-secrets` Secret from `storage` namespace to `ingestion` namespace
- Rebuilt `stock-api:latest` Docker image inside minikube to include Plan 01 `model_metadata_cache.py`
- Confirmed startup log: `active model metadata loaded: model_name=stacking_ensemble scaler=meta_ridge version=1`
- Human E2E verified: all 5 tickers (AAPL, MSFT, GOOGL, TSLA, NVDA) return `model_name="stacking_ensemble_meta_ridge"` (not "unknown")

## Task Commits

Each task was committed atomically:

1. **Task 1: Add MINIO vars to ConfigMap and secretRef to Deployment** - `97c40a8` (feat)
2. **Task 2: Human E2E verify — /predict/AAPL returns real model_name** - approved; all 5 tickers confirmed returning `stacking_ensemble_meta_ridge`

**Plan metadata:** `088659f` (docs: complete plan — MinIO env wiring + stock-api rebuild; await human E2E verify)

## Files Created/Modified

- `stock-prediction-platform/k8s/ingestion/configmap.yaml` - Added MINIO_ENDPOINT, MINIO_BUCKET_MODELS, MINIO_SERVING_PREFIX keys
- `stock-prediction-platform/k8s/ingestion/fastapi-deployment.yaml` - Added secretRef for minio-secrets in envFrom

## Decisions Made

- Copied minio-secrets from `storage` to `ingestion` namespace because K8s secretRef does not support cross-namespace references
- ConfigMap carries non-sensitive config (endpoint URL, bucket name, prefix); credentials come only via Secret
- Docker image rebuild was required because Plan 01 changes (model_metadata_cache.py) were not in the running image

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rebuilt stock-api Docker image to include Plan 01 code**
- **Found during:** Task 1 (verification — pod logs showed no metadata cache activity)
- **Issue:** The running stock-api pod was using a pre-Plan-01 image; `app.services.model_metadata_cache` module was absent from the container
- **Fix:** Ran `docker build -t stock-api:latest` with minikube Docker context using project root as build context; performed `kubectl rollout restart`
- **Files modified:** None (image rebuild only)
- **Verification:** `kubectl logs ... | grep "model metadata"` showed `active model metadata loaded: model_name=stacking_ensemble scaler=meta_ridge version=1`
- **Committed in:** 97c40a8 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Image rebuild was the essential step without which no config changes would have taken effect. No scope creep.

## Issues Encountered

- Minikube apiserver stopped twice during execution (TLS handshake timeouts) — restarted with `minikube start` each time, no data loss
- Docker build ran for ~6 minutes due to pip install layer not being cached in minikube context

## User Setup Required

None - all changes are cluster-side infrastructure.

## Next Phase Readiness

- Phase 60 fully complete: `/predict/{ticker}` returns `model_name="stacking_ensemble_meta_ridge"` sourced from MinIO `serving_config.json` at startup
- Both `PRED-MNAME-01` and `PRED-MNAME-04` requirements satisfied
- No blockers for subsequent phases

## Self-Check: PASSED

- FOUND: `.planning/phases/60-.../60-02-SUMMARY.md`
- FOUND: commit `97c40a8` (Task 1 — ConfigMap + secretRef)
- FOUND: commit `088659f` (plan metadata commit)

---
*Phase: 60-fix-model-name-unknown-in-predict-response-fetch-metadata-from-minio-or-db-on-api-startup*
*Completed: 2026-03-25*
