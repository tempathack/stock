#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# deploy-all.sh — Ordered manifest orchestration for Stock Prediction Platform
# =============================================================================

# --- Path resolution ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Prerequisite checks ---
if ! command -v kubectl &>/dev/null; then
  echo "ERROR: 'kubectl' is required but not found on PATH" >&2
  exit 1
fi

MINIKUBE_STATUS=$(minikube status --format='{{.Host}}' 2>/dev/null || true)
if [ "$MINIKUBE_STATUS" != "Running" ]; then
  echo "ERROR: Minikube is not running. Run setup-minikube.sh first." >&2
  exit 1
fi

echo "=== Stock Prediction Platform - Deploy All ==="

# --- Phase 2: Namespaces ---
echo "[Phase 2] Applying namespaces..."
kubectl apply -f "$PROJECT_ROOT/k8s/namespaces.yaml"

# --- Phase 3: FastAPI Base Service ---
echo "[Phase 3] Deploying FastAPI service..."
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/fastapi-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/fastapi-service.yaml"

# --- Phase 4: Storage (PostgreSQL + TimescaleDB) ---
echo "[Phase 4] Deploying PostgreSQL + TimescaleDB..."
kubectl apply -f "$PROJECT_ROOT/k8s/storage/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-deployment.yaml"

# --- Phase 5: Kafka (Strimzi Operator) ---
# echo "[Phase 5] Deploying Strimzi and Kafka..."
# kubectl apply -f "$PROJECT_ROOT/k8s/kafka/strimzi-operator.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-cluster.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-topics.yaml"

# --- Phase 6-7: Ingestion Service ---
# echo "[Phase 6-7] Deploying ingestion service..."
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/ingestion-deployment.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/ingestion-service.yaml"

# --- Phase 8: Ingestion CronJobs ---
# echo "[Phase 8] Deploying ingestion CronJobs..."
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/cronjob-intraday.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/cronjob-historical.yaml"

# --- Phase 9: Kafka Consumers ---
# echo "[Phase 9] Deploying Kafka consumer service..."
# kubectl apply -f "$PROJECT_ROOT/k8s/processing/consumer-deployment.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/processing/consumer-service.yaml"

# --- Phase 17-20: Kubeflow Pipelines (ML) ---
# echo "[Phase 17-20] Deploying Kubeflow Pipelines..."
# kubectl apply -f "$PROJECT_ROOT/k8s/ml/kubeflow-pipelines.yaml"

# --- Phase 21-22: Drift Detection ---
# echo "[Phase 21-22] Deploying drift detection..."
# kubectl apply -f "$PROJECT_ROOT/k8s/ml/drift-detection.yaml"

# --- Phase 23-24: FastAPI Prediction & Market Endpoints ---
# echo "[Phase 23-24] Deploying prediction API..."
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/prediction-deployment.yaml"

# --- Phase 25: React Frontend ---
# echo "[Phase 25] Deploying frontend..."
# kubectl apply -f "$PROJECT_ROOT/k8s/frontend/frontend-deployment.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/frontend/frontend-service.yaml"

echo "=== Deployment complete ==="
