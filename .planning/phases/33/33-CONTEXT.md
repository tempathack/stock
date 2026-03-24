# Phase 33 — ML Pipeline Container & Config

## What This Phase Delivers

Dockerize the ML pipeline as a standalone container and provide K8s ConfigMap for the ML namespace. This is the foundation for Phase 34 (CronJobs, PVC, deploy-all.sh wiring).

1. **ml/Dockerfile** — Multi-stage Python 3.11 image containing the entire `ml/` package with all ML dependencies (scikit-learn, xgboost, lightgbm, catboost, shap, psycopg2). No EXPOSE — this is a batch job container, not a service.
2. **ml/requirements.txt** — Pinned dependency list for ML pipeline (separate from services/api/requirements.txt)
3. **k8s/ml/configmap.yaml** — ConfigMap in the `ml` namespace providing DATABASE_URL, MODEL_REGISTRY_DIR, SERVING_DIR, DRIFT_LOG_DIR to all ML workloads

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| DEPLOY-01 | ML pipeline Dockerfile (Python 3.11, multi-stage, all ML dependencies) | `ml/Dockerfile` + `ml/requirements.txt` |
| DEPLOY-02 | K8s ConfigMap for ML namespace (DATABASE_URL, MODEL_REGISTRY_DIR, SERVING_DIR, DRIFT_LOG_DIR) | `k8s/ml/configmap.yaml` |

## Architecture

### Current State (Phase 32)

```
┌─────────────────────────────────────────────────┐
│ ML Pipeline (local only)                         │
│                                                  │
│  python -m ml.pipelines.training_pipeline        │
│  python -m ml.pipelines.drift_pipeline           │
│                                                  │
│  Dependencies: installed in local venv           │
│  Config: CLI args or hardcoded defaults          │
│  No Dockerfile, no container image               │
└─────────────────────────────────────────────────┘
                                                    
┌─────────────────────────────────────────────────┐
│ K8s ML Namespace                                 │
│                                                  │
│  model-serving.yaml  → uses stock-api:latest     │
│  kubeflow/           → KFP standalone YAML       │
│  NO ConfigMap for ML jobs                        │
└─────────────────────────────────────────────────┘
```

### Target State (Phase 33)

```
┌─────────────────────────────────────────────────┐
│ ML Pipeline Container                            │
│                                                  │
│  ml/Dockerfile  → stock-ml-pipeline:latest       │
│  ml/requirements.txt  → pinned ML deps           │
│                                                  │
│  Entry points:                                   │
│    python -m ml.pipelines.training_pipeline      │
│    python -m ml.pipelines.drift_pipeline         │
│                                                  │
│  Multi-stage: builder (pip install) → runtime    │
│  Non-root user (appuser:1000)                    │
│  No EXPOSE (batch job, not a server)             │
└─────────────────────────────────────────────────┘
                                                    
┌─────────────────────────────────────────────────┐
│ K8s ML Namespace                                 │
│                                                  │
│  configmap.yaml  → ml-pipeline-config            │
│    DATABASE_URL=postgresql://stockuser:...        │
│      @postgresql.storage.svc.cluster.local:5432  │
│    MODEL_REGISTRY_DIR=/data/model_registry       │
│    SERVING_DIR=/data/models/active               │
│    DRIFT_LOG_DIR=/data/drift_logs                │
│                                                  │
│  model-serving.yaml  → unchanged (Phase 34 PVC)  │
│  kubeflow/           → unchanged                 │
└─────────────────────────────────────────────────┘
```

### Dependency Map

```
ml/requirements.txt
├── scikit-learn==1.4.2
├── xgboost==2.0.3
├── lightgbm==4.3.0
├── catboost==1.2.5
├── shap==0.45.1
├── pandas==2.2.2
├── numpy==1.26.4
├── psycopg2-binary==2.9.9    # DB access for data_loader
├── yfinance==0.2.38          # Fallback data fetch
├── joblib==1.4.2             # Model serialization
├── structlog==24.2.0         # Logging
└── tenacity==8.3.0           # Retry logic
```

### Build Context

The Dockerfile is placed inside `ml/` but uses the **project root** as build context so it can `COPY ml/ ./ml/` as a package. The docker build command should be:

```bash
docker build -t stock-ml-pipeline:latest -f ml/Dockerfile .
```

This matches how Phase 34's CronJobs and deploy-all.sh will build the image.

## Key Files

| File | Role |
|------|------|
| `ml/Dockerfile` | Multi-stage Python 3.11 container for ML pipeline |
| `ml/requirements.txt` | Pinned ML dependencies |
| `k8s/ml/configmap.yaml` | ML namespace ConfigMap (DB URL, paths) |
| `ml/pipelines/training_pipeline.py` | Main entry point (`python -m ...`) |
| `ml/pipelines/drift_pipeline.py` | Drift retrain entry point |
| `k8s/ml/model-serving.yaml` | Existing serving deployment (unchanged) |

## Relationship to Phase 34

Phase 33 creates the container image and config. Phase 34 will:
- Create K8s CronJobs that USE this image + ConfigMap
- Replace emptyDir with PVC in model-serving.yaml
- Wire deploy-all.sh to build the image and apply ML manifests
