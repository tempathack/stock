# Stock Prediction Platform

Scalable stock prediction platform for the S&P 500 universe. Ingests real-time and historical market data, trains and evaluates regression models via automated ML pipelines, selects the best-performing model, detects drift, triggers retraining, and presents results through a React dashboard.

## Architecture

```
CronJob ─► FastAPI (Ingestion) ─► Kafka ─► Batch Consumers ─► PostgreSQL
                                                               │
                                                 Kubeflow (Training Pipeline)
                                                               │
                                                      MinIO (S3 Storage)
                                                      ┌───────┴───────┐
                                            model-artifacts     drift-logs
                                                      │
                                           KServe InferenceService
                                            (MLServer + sklearn)
                                                      │
                                            FastAPI (Prediction API)
                                                      │
                                               React Frontend
```

## Tech Stack

- **Orchestration:** Kubernetes (Minikube), Kubeflow Pipelines
- **Backend:** FastAPI (Python)
- **Streaming:** Apache Kafka (Strimzi)
- **Storage:** PostgreSQL + TimescaleDB
- **Object Storage:** MinIO (S3-compatible)
- **Model Serving:** KServe (InferenceService), MLServer (Seldon)
- **ML:** scikit-learn, SHAP
- **Frontend:** React, Tailwind CSS
- **Data Source:** Yahoo Finance (yfinance)

## Model Serving Architecture

Models are trained via Kubeflow pipelines and stored as artifacts in MinIO
(S3-compatible object storage). KServe InferenceServices pull model artifacts
from MinIO and serve predictions via the V2/Open Inference Protocol.

| Component | Resource | Namespace |
|-----------|----------|-----------|
| MinIO | Deployment, Service, PVC | storage |
| Model Artifacts | S3 bucket `model-artifacts` | — |
| Drift Logs | S3 bucket `drift-logs` | — |
| KServe Controller | Deployment | kserve |
| Primary Model | InferenceService `stock-model-serving` | ml |
| Canary Model | InferenceService `stock-model-serving-canary` | ml |
| Serving Runtime | ClusterServingRuntime `stock-sklearn-mlserver` | — |
| S3 Credentials | Secret `kserve-s3-secret` | ml |

### Inference Flow

1. Training pipeline uploads trained sklearn pipeline to `s3://model-artifacts/serving/active/`
2. KServe InferenceService detects new model via storage-initializer
3. MLServer loads the sklearn model and exposes V2 inference endpoint
4. FastAPI prediction service calls `POST /v2/models/{name}/infer` via httpx
5. Feature flag `KSERVE_ENABLED` controls routing (true = KServe, false = legacy pickle)

### Drift & Retraining

1. Daily drift CronJob detects data/concept/prediction drift
2. On drift → retraining pipeline triggered automatically
3. New model uploaded to MinIO, KServe performs rolling update
4. Canary traffic splitting available via A/B testing configuration

## Project Structure

See `Project_scope.md` Section 15 for the complete folder tree.

## Getting Started

### Prerequisites
- Docker
- Minikube
- kubectl
- Python 3.11+
- Node.js 18+

### Quick Start
```bash
# 1. Bootstrap Minikube cluster
scripts/setup-minikube.sh

# 2. Configure secrets
cp k8s/storage/secrets.yaml.example k8s/storage/secrets.yaml
cp k8s/storage/minio-secrets.yaml.example k8s/storage/minio-secrets.yaml
# Edit both files with your credentials (base64 encoded)

# 3. Deploy everything (includes MinIO, KServe, all services)
scripts/deploy-all.sh

# 4. Verify KServe InferenceService is Ready
kubectl get inferenceservice -n ml

# 5. Seed initial data
scripts/seed-data.sh
```

## Secrets Management

### K8s Secrets Setup

1. Copy the template: `cp k8s/storage/secrets.yaml.example k8s/storage/secrets.yaml`
2. Generate passwords and encode to base64: `echo -n 'your-secure-password' | base64`
3. Replace placeholder values in `secrets.yaml` with real base64-encoded credentials
4. Run `scripts/deploy-all.sh` — secrets are applied automatically to all namespaces

**Never commit `secrets.yaml`** — it is listed in `.gitignore`.

### Database Roles

| Role | Access Level | Used By |
|------|-------------|---------|
| `stockuser` | Admin (DDL + DML) | Alembic migrations |
| `stock_readonly` | SELECT only | API service, model serving |
| `stock_writer` | SELECT + INSERT + UPDATE + DELETE | Kafka consumer, ML training, drift detection |

### Production: Sealed Secrets

For production clusters, use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets):

```bash
# Install kubeseal CLI
# Seal the secret (encrypted, safe to commit)
kubeseal --format yaml < k8s/storage/secrets.yaml > k8s/storage/sealed-secrets.yaml
kubectl apply -f k8s/storage/sealed-secrets.yaml
```
