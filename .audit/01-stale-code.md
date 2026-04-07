# Audit Section 1: Stale Code & Infrastructure Baseline

Status: IN PROGRESS

---

## K8s Pod Baseline

_Recorded: 2026-04-07_

| Namespace | Pod | Status |
|-----------|-----|--------|
| argocd | argocd-application-controller-0 | Running |
| argocd | argocd-applicationset-controller-f66c56b59-dzb9h | Running |
| argocd | argocd-dex-server-6d8548d96d-p57mq | Error |
| argocd | argocd-notifications-controller-65dbccbd4b-72xrd | Running |
| argocd | argocd-redis-6859df457f-clm9v | Running |
| argocd | argocd-repo-server-5f7f9c4dcb-xn28s | Completed |
| argocd | argocd-server-7cd9848b87-qmdvm | Running |
| cert-manager | cert-manager-767f578ff-c62zs | Running |
| cert-manager | cert-manager-cainjector-c7fdb4dbf-bwjnw | Running |
| cert-manager | cert-manager-webhook-768bf9d966-n64kk | Running |
| flink | feast-writer-654455db6d-df6wm | Running |
| flink | feast-writer-taskmanager-11-1 | Running |
| flink | flink-kubernetes-operator-7848cffc97-z9ffc | Running |
| flink | indicator-stream-58dcc69587-wrhtj | Running |
| flink | indicator-stream-taskmanager-10-1 | Running |
| flink | ohlcv-normalizer-6bc9464c66-zmjlz | Running |
| flink | ohlcv-normalizer-taskmanager-20-1 | Running |
| flink | sentiment-stream-7f7f565b7d-wfq8w | Running |
| flink | sentiment-stream-taskmanager-2-1 | Running |
| flink | sentiment-writer-744c697854-gswpk | Running |
| flink | sentiment-writer-taskmanager-3-1 | Running |
| frontend | frontend-7bdcb79c89-966q9 | Running |
| ingestion | intraday-ingestion-29587775-jnwfk | Completed |
| ingestion | intraday-ingestion-29587780-kxjnh | Completed |
| ingestion | intraday-ingestion-29587790-kz7tc | Completed |
| ingestion | reddit-producer-75dcc9fdb6-7jj6m | Running |
| ingestion | stock-api-8779d87f4-bgnmb | Running |
| ingress-nginx | ingress-nginx-controller-56d7c84fd4-n7x2r | Running |
| kserve | kserve-controller-manager-78bbf54fdb-lp52q | Running |
| kserve | kserve-localmodel-controller-manager-f5b5cd9cc-fhj5n | Running |
| kube-system | coredns-6b6cdb8cfd-rjps7 | Running |
| kube-system | etcd-minikube | Running |
| kube-system | kube-apiserver-minikube | Running |
| kube-system | kube-controller-manager-minikube | Running |
| kube-system | kube-proxy-hbv8x | Running |
| kube-system | kube-scheduler-minikube | Running |
| kube-system | metrics-server-7fbb699795-4g828 | Running |
| kube-system | storage-provisioner | Running |
| kubeflow | cache-deployer-deployment-6cd49db798-kjjrf | Running |
| kubeflow | cache-server-6669dd6674-msxjk | Running |
| kubeflow | metadata-envoy-deployment-677d8c6fb9-fhzr6 | Running |
| kubeflow | metadata-grpc-deployment-76d6fb49f8-kr7tl | Running |
| kubeflow | metadata-writer-685b9776db-77df6 | Running |
| kubeflow | minio-84b5cc74b5-b9mt2 | Running |
| kubeflow | ml-pipeline-64469779df-f5cjq | Running |
| kubeflow | ml-pipeline-persistenceagent-644484d7cd-qtzc6 | Running |
| kubeflow | ml-pipeline-scheduledworkflow-58b5f859c-zhbg6 | Running |
| kubeflow | ml-pipeline-ui-67df75b4cc-gzjcl | Running |
| kubeflow | ml-pipeline-viewer-crd-54d6b54bcb-6kjbc | Running |
| kubeflow | ml-pipeline-visualizationserver-6b6b7c7d6b-g9jhf | Running |
| kubeflow | mysql-767f4d9f9b-57flx | Running |
| kubeflow | smoke-daily-daily-closewvtrl-78-... | Init:ImagePullBackOff |
| kubeflow | smoke-intraday-intraday-r8st9d-... | Init:ErrImagePull |
| kubeflow | workflow-controller-6bc9b6d744-c2bxh | Running |
| kubernetes-dashboard | dashboard-metrics-scraper-5d59dccf9b-26pnw | Running |
| kubernetes-dashboard | kubernetes-dashboard-7779f9b69b-k4lq7 | Running |
| ml | aapl-retrain-v2-7df5v | Completed |
| ml | feast-feature-server-7f947d7777-xxgwm | Running |
| ml | manual-train-linear-rms9s | Completed |
| ml | stock-model-serving-canary-predictor-5f59f87547-6rh6v | Running |
| ml | stock-model-serving-predictor-cfbc44bd9-fv9rq | Running |
| monitoring | alertmanager-7d775494cb-lzf6c | Running |
| monitoring | grafana-c78fd8498-8lgm7 | Running |
| monitoring | loki-78d86995c4-tcdr2 | Running |
| monitoring | prometheus-769b456d4b-5pm92 | Running |
| monitoring | promtail-v949h | Running |
| processing | kafka-consumer-78875d9b96-t8m62 | Running |
| processing | kafka-consumer-78875d9b96-tbr7z | Running |
| storage | elasticsearch-0 | Running |
| storage | kafka-combined-0 | Running |
| storage | kafka-entity-operator-54c575b5b6-8bljs | Running |
| storage | kibana-5df4b8474c-8k9n5 | Running |
| storage | minio-76748b8597-d5nv5 | Running |
| storage | postgresql-5d7959b55-mx5qz | Running |
| storage | postgresql-backup-29587920-k9pmv | Completed |
| storage | redis-5d9fb5ffff-bqd5s | Running |
| storage | strimzi-cluster-operator-5444567598-db6xb | Running |

### Notable Issues (Pod Baseline)
- `argocd-dex-server`: Error (OAuth/SSO provider — non-critical for core function)
- `kubeflow smoke-daily / smoke-intraday`: Init:ImagePullBackOff / Init:ErrImagePull — pipeline smoke test pods stuck (image pull issue)

---

## Service Connectivity Baseline

_Recorded: 2026-04-07_

| Service | Endpoint | Status |
|---------|----------|--------|
| Stock API | http://localhost:8010/health | **UP** — `{"service":"stock-api","version":"1.0.0","status":"ok"}` |
| Prometheus | http://localhost:9090/-/ready | **UP** — `Prometheus Server is Ready.` |
| Grafana | http://localhost:3000/api/health | **UP** — `{"database":"ok","version":"10.4.0"}` |

### Port-Forward Commands Used
```bash
kubectl port-forward pod/stock-api-8779d87f4-bgnmb -n ingestion 8010:8000
kubectl port-forward svc/grafana -n monitoring 3000:3000
kubectl port-forward svc/prometheus -n monitoring 9090:9090
```

Note: API port-forward required pod-level forward (not svc-level) due to pod restart after minikube start.

---

## MinIO Artifact Inventory

### US-032: MinIO console audit (2026-04-07)

**Access:** `minioadmin / minioadmin123` (via MINIO_ROOT_USER/MINIO_ROOT_PASSWORD from `minio-secrets` secret in `storage` namespace)

**Buckets (2 total, no unexpected/orphaned buckets):**

| Bucket | Objects | Size | Access | Contents |
|---|---|---|---|---|
| model-artifacts | 294 | 24.1 MiB | PRIVATE | flink-checkpoints/, model_registry/, serving/ |
| drift-logs | 1 | 132.0 KiB | PRIVATE | drift_logs/ folder |

**model-artifacts structure:**
- `flink-checkpoints/` — Flink state backend checkpoints
- `model_registry/` — Trained model pickle/joblib files
- `serving/` — Model artifacts for KServe serving

**drift-logs structure:**
- `drift_logs/` — 1 file, 132 KiB — JSONL drift detection log

**Status:** Both expected buckets present with correct content. 294 model artifacts = healthy training pipeline output. 1 drift log file = drift detection running.

**Note:** MinIO not port-forwarded on 9001 by default (`scripts/deploy-all.sh` may not include MinIO forward). Used `kubectl port-forward -n storage svc/minio 9002:9001` to access. Credentials differ from story assumption (minio/minio123 wrong; actual: minioadmin/minioadmin123).


---

## Python Unused Imports — Routers

### US-034: Router unused imports scan (2026-04-07)

**Syntax check:** All routers compile cleanly (`python3 -m py_compile` exit 0)

**Unused imports (flake8 F401):**
| File | Import | Severity |
|---|---|---|
| `health.py:7` | `from typing import Any` | LOW — remove |
| `ingest.py:5` | `import threading` | LOW — remove |
| `ingest.py:8` | `from fastapi import HTTPException` | LOW — remove |
| `ingest.py:10` | `from app.config import settings` | LOW — remove |
| `ws.py:7` | `from datetime.datetime import datetime` | LOW — remove |

**Route ordering check (predict.py):** CORRECT — `/bulk` registered at line 67, `/{ticker}` at line 166. No path-capture bug.

**Macro fields (market.py):** All macro endpoints use relevant fields via `get_macro_latest()` and `get_macro_history()` — no dead field references found.

**Summary:** 5 unused imports across 3 files — all LOW severity cosmetic issues. No logic errors or dead code in routing logic.


---

## Dead Python Service Functions

### US-035: Service files dead code scan (2026-04-07)

**Unused imports (flake8 F401):**
| File | Import | Notes |
|---|---|---|
| `flink_service.py:115` | `datetime` (inside function) | LOW — local import not used |
| `kafka_lag_service.py:7` | `confluent_kafka.KafkaException` | LOW — imported but not raised |

**Service file usage:**
| Service | Used By | Active |
|---|---|---|
| `elasticsearch_service.py` | `search.py` router + `main.py` (close) | YES — ES pod Running |
| `feast_service.py` | `analytics.py` router (freshness) | YES |
| `feast_online_service.py` | `market.py` router (streaming features) | YES — separate from feast_service |
| `flink_service.py` | `analytics.py` router (jobs + summary) | YES |
| `kserve_client.py` | `prediction_service.py` + `main.py` | YES — lazy import for KServe inference |
| `model_metadata_cache.py` | `main.py` + `prediction_service.py` | YES |
| `ab_service.py` | `models.py` router (A/B results) | YES |
| `backtest_service.py` | via `predict.py` or `backtest.py` | YES |
| `health_service.py` | `health.py` router | YES |
| `kafka_producer.py` | `ingest.py` router | YES |
| `market_service.py` | `market.py` router | YES |
| `price_feed.py` | `ws.py` router | YES |
| `yahoo_finance.py` | `market_service.py` + `ingest.py` | YES |
| `kafka_lag_service.py` | `analytics.py` router | YES |
| `prediction_service.py` | multiple routers | YES |

**Note:** `feast_service.py` and `feast_online_service.py` serve different purposes — not duplicates. feast_service queries feast_metadata table; feast_online_service queries Redis online store.

**Summary:** No dead service files. Only 2 low-severity unused imports.


---

## Dead Python Modules

### US-036: Jobs, middleware, utils dead code audit (2026-04-07)

**Jobs (trigger_intraday.py, trigger_historical.py):**
- Both are **NOT imported** by main.py or any router — intentional design
- Invoked directly by K8s CronJobs via `python -m app.jobs.trigger_intraday`
- Status: ACTIVE via K8s CronJob manifest (not dead code)

**middleware.py (RequestContextMiddleware):**
- Registered in `main.py:102` via `app.add_middleware(RequestContextMiddleware)` ✓
- Status: ACTIVE

**rate_limit.py (RateLimitMiddleware):**
- Imported and registered in `main.py:103` via `app.add_middleware(RateLimitMiddleware, ...)` ✓
- Status: ACTIVE

**utils/logging.py (get_logger, configure_uvicorn_logging):**
- Used by `main.py`, `middleware.py`, `kafka_producer.py`, `yahoo_finance.py`, `health_service.py`, `ingest.py`, `rate_limit.py`, `trigger_intraday.py`, `trigger_historical.py` ✓
- Status: ACTIVE — widely used

**utils/indicators.py:**
- File contains only 3 lines (module docstring + `from __future__ import annotations`)
- **EMPTY MODULE** — no function definitions
- Real indicator logic lives in `ml/features/indicators.py` (imported via lazy imports in services)
- Status: DEAD EMPTY FILE — can be deleted

**Summary:**
- 0 dead jobs/middleware/rate_limit/logging modules — all active
- `utils/indicators.py` is empty stub (3 lines) — safe to delete


---

## Dead ML Pipeline Code

### US-037: ML pipeline dead code scan (2026-04-07)

**File inventory:** 75 Python files (39 pipeline/model files + 36 test files)

**SHAP guard:** ✓ Properly handled via `try/except ImportError` in `explainer.py` — not a flag but equivalent protection.

**Pipeline component coverage:** All components in `ml/pipelines/components/` referenced from `training_pipeline.py` or `drift_pipeline.py`.

**Storage backends:** Both `storage_backends.py` and `s3_storage.py` are active:
- `storage_backends.py`: abstract `StorageBackend` + `create_storage_backend()` factory — used by `registry.py`
- `s3_storage.py`: concrete MinIO/S3 implementation — lazy-imported in 4 pipeline files

**sktime integration:** `sktime_wrappers.py` defined, functions called from `model_trainer.py` (`train_sktime_models`, `train_sktime_regression_models`) — ACTIVE via Phase 96

**pit_validator.py:** Referenced from `feature_store/__init__.py` — ACTIVE

**Commented-out stages:** None found in `ml/pipelines/` scan.

**No dead ML code found** — all pipeline stages, feature files, and model modules are referenced.

**Minor note:** `shap_analysis.py` imports `shap` at module level (line 8) without guard — should be inside try/except. But this is only imported by `explainer.py` which has the guard, so practically safe.


---

## TypeScript Unused Imports — Pages

### US-038: Frontend pages TS unused imports scan (2026-04-07)

**TypeScript config:** `noUnusedLocals: true`, `noUnusedParameters: true` — TS compiler enforces no unused variables.

**`npx tsc --noEmit` result:** Exit 0, 0 errors, 0 warnings

**All page files clean:**
| Page | Unused Imports | Status |
|---|---|---|
| Analytics.tsx | 0 | ✓ Clean |
| Backtest.tsx | 0 | ✓ Clean |
| Dashboard.tsx | 0 | ✓ Clean |
| Drift.tsx | 0 | ✓ Clean |
| Forecasts.tsx | 0 | ✓ Clean |
| Models.tsx | 0 | ✓ Clean |
| Search.tsx | 0 | ✓ Clean |

**Summary:** Zero unused imports in any page file. TypeScript strict mode (`noUnusedLocals: true`) would have caught any real unused imports at compile time.

