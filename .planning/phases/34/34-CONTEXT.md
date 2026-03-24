# Phase 34 — K8s ML CronJobs & Model Serving

## What This Phase Delivers

Scheduled K8s CronJobs for weekly model training and daily drift detection, persistent model storage via PVC, and a fully wired deploy-all.sh covering phases 17–25.

1. **cronjob-training.yaml** — Weekly CronJob (Sunday 03:00 UTC) that runs `python -m ml.pipelines.training_pipeline` using the `stock-ml-pipeline:latest` image from Phase 33
2. **cronjob-drift.yaml** — Daily CronJob (weekdays 22:00 UTC) that runs `python -m ml.drift.trigger --auto-retrain` using the same image
3. **model-pvc.yaml** — 5Gi PersistentVolumeClaim in the `ml` namespace for model artifacts, shared by CronJobs and model-serving
4. **model-serving.yaml update** — Replace `emptyDir` with the PVC so artifacts persist across pod restarts
5. **trigger.py CLI enhancement** — Add `--auto-retrain` CLI entry point for CronJob execution (drift check + conditional retrain)
6. **deploy-all.sh updates** — Uncomment phases 17–25, add ML CronJob deployment phases, add Docker build for ml-pipeline image

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| DEPLOY-03 | K8s CronJob for weekly model retraining (Sunday 03:00 UTC) | `k8s/ml/cronjob-training.yaml` |
| DEPLOY-04 | K8s CronJob for daily drift detection (weekdays 22:00 UTC) | `k8s/ml/cronjob-drift.yaml` |
| DEPLOY-05 | PersistentVolumeClaim for model artifacts (5Gi, ReadWriteOnce) | `k8s/ml/model-pvc.yaml` |
| DEPLOY-06 | model-serving Deployment uses PVC (not emptyDir) | `k8s/ml/model-serving.yaml` (modified) |
| DEPLOY-07 | deploy-all.sh phases 17–25 uncommented and active | `scripts/deploy-all.sh` (modified) |
| DEPLOY-08 | ml/drift/trigger.py CLI entry point for K8s CronJob execution | `ml/drift/trigger.py` (modified) |

## Architecture

### Current State (Phase 33)

```
┌─────────────────────────────────────────────────┐
│ K8s ML Namespace                                 │
│                                                  │
│  configmap.yaml  → ml-pipeline-config            │
│    DATABASE_URL, MODEL_REGISTRY_DIR,             │
│    SERVING_DIR, DRIFT_LOG_DIR                    │
│                                                  │
│  model-serving.yaml  → uses emptyDir volume      │
│    (artifacts lost on pod restart!)              │
│                                                  │
│  No CronJobs                                     │
│  No PVC for model persistence                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ deploy-all.sh                                    │
│  Phases 17-25 ALL COMMENTED OUT                  │
│  No ML image build step                          │
│  No ML CronJob deployment                        │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ ml/drift/trigger.py                              │
│  evaluate_and_trigger() function only            │
│  No CLI __main__ entry point                     │
│  Not runnable from K8s CronJob                   │
└─────────────────────────────────────────────────┘
```

### Target State (Phase 34)

```
┌─────────────────────────────────────────────────┐
│ K8s ML Namespace                                 │
│                                                  │
│  configmap.yaml  → ml-pipeline-config            │
│  model-pvc.yaml  → model-artifacts-pvc (5Gi)    │
│                                                  │
│  model-serving.yaml  → PVC-backed volume         │
│    model-artifacts-pvc mounted at /models        │
│    Artifacts survive pod restarts                │
│                                                  │
│  cronjob-training.yaml  → weekly-training        │
│    Schedule: "0 3 * * 0" (Sunday 03:00 UTC)     │
│    Image: stock-ml-pipeline:latest               │
│    Cmd: python -m ml.pipelines.training_pipeline │
│    PVC mounted at /data                          │
│    envFrom: ml-pipeline-config                   │
│                                                  │
│  cronjob-drift.yaml  → daily-drift              │
│    Schedule: "0 22 * * 1-5" (weekdays 22:00)    │
│    Image: stock-ml-pipeline:latest               │
│    Cmd: python -m ml.drift.trigger --auto-retrain│
│    PVC mounted at /data                          │
│    envFrom: ml-pipeline-config                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ deploy-all.sh                                    │
│  Phase 33: Build stock-ml-pipeline Docker image  │
│  Phase 34a: Apply model-pvc.yaml                 │
│  Phase 34b: Apply configmap.yaml                 │
│  Phase 34c: Apply cronjob-training.yaml          │
│  Phase 34d: Apply cronjob-drift.yaml             │
│  Phase 34e: Apply model-serving.yaml             │
│  Phase 25: Apply frontend deployment + service   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ ml/drift/trigger.py                              │
│  evaluate_and_trigger() — unchanged              │
│  __main__ CLI added:                             │
│    --auto-retrain    drift → auto retrain        │
│    --registry-dir    model registry path         │
│    --serving-dir     serving directory path       │
│    --drift-log-dir   drift log directory          │
│    --tickers         comma-separated tickers     │
│    --skip-shap       skip SHAP computation       │
└─────────────────────────────────────────────────┘
```

### Volume Architecture

```
model-artifacts-pvc (5Gi, ReadWriteOnce, standard)
│
├─ /data/model_registry/    ← training pipeline writes here
│   ├── winner/
│   ├── runs/
│   └── shap/
│
├─ /data/models/active/     ← deployer copies winner here
│   └── pipeline.pkl
│
└─ /data/drift_logs/        ← drift trigger writes here
    └── drift_events.jsonl

Access pattern:
  CronJob training  → mounts PVC at /data → writes to MODEL_REGISTRY_DIR + SERVING_DIR
  CronJob drift     → mounts PVC at /data → writes to DRIFT_LOG_DIR, reads SERVING_DIR
  model-serving     → mounts PVC at /models (= /data/models/active) → reads pipeline.pkl
```

### Key Design Decisions

1. **Single PVC shared across CronJobs and model-serving** — ReadWriteOnce is sufficient since Minikube uses a single-node cluster. The training CronJob and model-serving will not run in parallel (concurrencyPolicy: Forbid).
2. **CronJobs use `envFrom: configMapRef`** — Inherits DATABASE_URL, MODEL_REGISTRY_DIR, SERVING_DIR, DRIFT_LOG_DIR from ml-pipeline-config ConfigMap (Phase 33).
3. **model-serving mounts a sub-path** — `/data/models/active` is the SERVING_DIR; model-serving mounts it at `/models` using `subPath: models/active`.
4. **trigger.py CLI uses environment variables as defaults** — CLI args override env vars, matching the CronJob pattern where ConfigMap provides defaults.
5. **CronJob resource limits** — Training gets more CPU/memory (2Gi, 2 CPU) than drift (1Gi, 1 CPU) since training runs full model fitting.
