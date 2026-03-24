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

# --- Phase 3: Build stock-api Docker image ---
echo "[Phase 3] Building stock-api Docker image..."
eval $(minikube docker-env)
docker build -t stock-api:latest "$PROJECT_ROOT/services/api/"
echo "[Phase 3] stock-api:latest built"

# --- Phase 3: FastAPI Base Service ---
echo "[Phase 3] Deploying FastAPI service..."
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/fastapi-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/fastapi-service.yaml"

# --- Phase 36: K8s Secrets ---
echo "[Phase 36] Applying K8s Secrets..."
if [ -f "$PROJECT_ROOT/k8s/storage/secrets.yaml" ]; then
    kubectl apply -f "$PROJECT_ROOT/k8s/storage/secrets.yaml"
    # Copy secret to namespaces that need database access
    kubectl get secret stock-platform-secrets -n storage -o yaml \
        | sed 's/namespace: storage/namespace: ingestion/' \
        | kubectl apply -f -
    kubectl get secret stock-platform-secrets -n storage -o yaml \
        | sed 's/namespace: storage/namespace: processing/' \
        | kubectl apply -f -
    kubectl get secret stock-platform-secrets -n storage -o yaml \
        | sed 's/namespace: storage/namespace: ml/' \
        | kubectl apply -f -
    echo "[Phase 36] Secrets applied to storage, ingestion, processing, ml namespaces"
else
    echo "WARNING: k8s/storage/secrets.yaml not found. Copy from secrets.yaml.example and fill in values."
    exit 1
fi

# --- Phase 4: Storage (PostgreSQL + TimescaleDB) ---
echo "[Phase 4] Deploying PostgreSQL + TimescaleDB..."
kubectl apply -f "$PROJECT_ROOT/k8s/storage/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-deployment.yaml"

# --- Phase 36: Database RBAC Roles ---
echo "[Phase 36] Applying database RBAC roles..."
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgresql -n storage --timeout=120s

PG_POD=$(kubectl get pod -l app=postgresql -n storage -o jsonpath='{.items[0].metadata.name}')
kubectl cp "$PROJECT_ROOT/db/migrations/002_rbac_roles.sql" "storage/$PG_POD:/tmp/002_rbac_roles.sql"
kubectl exec -n storage "$PG_POD" -- psql -U stockuser -d stockdb -f /tmp/002_rbac_roles.sql

# Update role passwords from secrets (if password keys exist)
READONLY_PWD=$(kubectl get secret stock-platform-secrets -n storage -o jsonpath='{.data.POSTGRES_READONLY_PASSWORD}' 2>/dev/null | base64 -d 2>/dev/null || true)
WRITER_PWD=$(kubectl get secret stock-platform-secrets -n storage -o jsonpath='{.data.POSTGRES_WRITER_PASSWORD}' 2>/dev/null | base64 -d 2>/dev/null || true)

if [ -n "$READONLY_PWD" ]; then
    kubectl exec -n storage "$PG_POD" -- \
        psql -U stockuser -d stockdb -c "ALTER ROLE stock_readonly PASSWORD '$READONLY_PWD';"
fi
if [ -n "$WRITER_PWD" ]; then
    kubectl exec -n storage "$PG_POD" -- \
        psql -U stockuser -d stockdb -c "ALTER ROLE stock_writer PASSWORD '$WRITER_PWD';"
fi

echo "[Phase 36] RBAC roles applied"

# --- Phase 41: Database Backup Strategy ---
echo "[Phase 41] Deploying database backup CronJob..."
kubectl apply -f "$PROJECT_ROOT/k8s/storage/backup-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/cronjob-backup.yaml"
echo "[Phase 41] ✓ Database backup CronJob deployed (daily at 04:00 UTC)"

# --- Phase 51: MinIO Object Storage ---
echo "[Phase 51] Deploying MinIO object storage..."
if [ -f "$PROJECT_ROOT/k8s/storage/minio-secrets.yaml" ]; then
    kubectl apply -f "$PROJECT_ROOT/k8s/storage/minio-secrets.yaml"
else
    echo "WARNING: k8s/storage/minio-secrets.yaml not found. Copy from minio-secrets.yaml.example and fill in values."
    exit 1
fi
kubectl apply -f "$PROJECT_ROOT/k8s/storage/minio-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/minio-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/minio-deployment.yaml"

echo "[Phase 51] Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n storage --timeout=120s

echo "[Phase 51] Initializing MinIO buckets..."
kubectl delete job minio-init-buckets -n storage --ignore-not-found
kubectl apply -f "$PROJECT_ROOT/k8s/storage/minio-init-job.yaml"
kubectl wait --for=condition=complete job/minio-init-buckets -n storage --timeout=60s

# Copy MinIO secrets and config to ml namespace
kubectl get secret minio-secrets -n storage -o yaml \
    | sed 's/namespace: storage/namespace: ml/' \
    | kubectl apply -f -
kubectl get configmap minio-config -n storage -o yaml \
    | sed 's/namespace: storage/namespace: ml/' \
    | kubectl apply -f -

echo "[Phase 51] ✓ MinIO deployed with model-artifacts and drift-logs buckets"

# --- Phase 47: Redis Caching Layer ---
echo "[Phase 47] Deploying Redis..."
kubectl apply -f "$PROJECT_ROOT/k8s/storage/redis-deployment.yaml"
echo "[Phase 47] Redis deployed"

# --- Phase 54: KServe Installation & Configuration ---
echo "[Phase 54] Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml
echo "[Phase 54] Waiting for cert-manager..."
kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=180s
kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=180s
kubectl wait --for=condition=Available deployment/cert-manager-cainjector -n cert-manager --timeout=180s

echo "[Phase 54] Installing KServe (RawDeployment mode)..."
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve.yaml
kubectl wait --for=condition=Available deployment/kserve-controller-manager -n kserve --timeout=180s

echo "[Phase 54] Installing KServe cluster resources (ServingRuntimes)..."
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve-cluster-resources.yaml

echo "[Phase 54] Configuring KServe for RawDeployment mode..."
kubectl patch configmap/inferenceservice-config -n kserve --type=merge \
    -p '{"data":{"deploy":"{\"defaultDeploymentMode\":\"RawDeployment\"}"}}'

echo "[Phase 54] Applying KServe S3 credentials..."
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kserve/kserve-s3-secret.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kserve/kserve-s3-sa.yaml"

echo "[Phase 54] Deploying custom sklearn ServingRuntime..."
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kserve/sklearn-serving-runtime.yaml"

echo "[Phase 54] Verifying KServe CRDs..."
kubectl get crd inferenceservices.serving.kserve.io
kubectl get crd clusterservingruntimes.serving.kserve.io

echo "[Phase 54] ✓ KServe installed and configured"

# --- Phase 55: KServe InferenceService Deployment ---
echo "[Phase 55] Deploying KServe InferenceService (primary)..."
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kserve/kserve-inference-service.yaml"

echo "[Phase 55] Deploying KServe InferenceService (canary)..."
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kserve/kserve-inference-service-canary.yaml"

echo "[Phase 55] Waiting for primary InferenceService to be ready..."
if [ "${SKIP_KSERVE_WAIT:-false}" = "true" ]; then
  echo "[Phase 55] SKIP_KSERVE_WAIT=true — skipping InferenceService wait (no model artifact yet)"
  echo "[Phase 55] Run: kubectl wait --for=condition=Ready inferenceservice/stock-model-serving -n ml --timeout=600s"
  echo "[Phase 55] after placing a model artifact in s3://model-artifacts/serving/active/"
else
  kubectl wait --for=condition=Ready inferenceservice/stock-model-serving -n ml --timeout=300s
fi

echo "[Phase 55] Verifying KServe predictor pod..."
kubectl get inferenceservice -n ml
kubectl get pods -n ml -l serving.kserve.io/inferenceservice=stock-model-serving

echo "[Phase 55] ✓ KServe InferenceService deployed"

# --- Phase 57: Migration Cleanup ---
echo "[Phase 57] Verifying KServe replaces legacy serving..."
if kubectl get deployment model-serving -n ml &>/dev/null; then
    echo "[Phase 57] Removing legacy model-serving Deployment..."
    kubectl delete deployment model-serving -n ml --ignore-not-found
    kubectl delete service model-serving -n ml --ignore-not-found
fi
if kubectl get deployment model-serving-canary -n ml &>/dev/null; then
    echo "[Phase 57] Removing legacy model-serving-canary Deployment..."
    kubectl delete deployment model-serving-canary -n ml --ignore-not-found
fi
echo "[Phase 57] ✓ Legacy serving resources cleaned up"

# --- Phase 5: Kafka (Strimzi) ---
echo "[Phase 5] Deploying Kafka cluster and topics..."
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-cluster.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-topics.yaml"

# --- Phase 6-7: Ingestion Service ---
# echo "[Phase 6-7] Deploying ingestion service..."
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/ingestion-deployment.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/ingestion-service.yaml"

# --- Phase 8: Ingestion CronJobs ---
echo "[Phase 8] Deploying ingestion CronJobs..."
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/cronjob-intraday.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/cronjob-historical.yaml"

# --- Phase 9: Kafka Consumers ---
echo "[Phase 9] Building Kafka consumer Docker image..."
eval $(minikube docker-env)
docker build -t stock-kafka-consumer:latest "$PROJECT_ROOT/services/kafka-consumer/"

echo "[Phase 9] Deploying Kafka consumer service..."
kubectl apply -f "$PROJECT_ROOT/k8s/processing/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/processing/kafka-consumer-deployment.yaml"

echo "[Phase 9] Waiting for kafka-consumer deployment..."
kubectl rollout status deployment/kafka-consumer -n processing --timeout=120s

echo "[Phase 9] ✓ Kafka consumer service deployed"

# --- Phase 33: ML Pipeline Docker Image ---
echo "[Phase 33] Building ML pipeline Docker image..."
eval $(minikube docker-env)
docker build -t stock-ml-pipeline:latest -f "$PROJECT_ROOT/ml/Dockerfile" "$PROJECT_ROOT"

# --- Phase 34: ML CronJobs & Model Serving ---
echo "[Phase 34] Deploying ML namespace resources..."
kubectl apply -f "$PROJECT_ROOT/k8s/ml/model-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ml/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ml/cronjob-training.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/ml/cronjob-drift.yaml"
# Phase 44 — Feature store daily compute
kubectl apply -f "$PROJECT_ROOT/k8s/ml/cronjob-feature-store.yaml"

echo "[Phase 34] ✓ ML pipeline deployed (model serving via KServe)"

# --- Phase 25: React Frontend ---
echo "[Phase 25] Building frontend Docker image..."
eval $(minikube docker-env)
docker build -t stock-frontend:latest "$PROJECT_ROOT/services/frontend/"

echo "[Phase 25] Deploying frontend..."
kubectl apply -f "$PROJECT_ROOT/k8s/frontend/deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/frontend/service.yaml"

echo "[Phase 25] Waiting for frontend deployment..."
kubectl rollout status deployment/frontend -n frontend --timeout=120s

echo "[Phase 25] ✓ Frontend deployed"

# --- Phase 38: Monitoring (Prometheus + Grafana) ---
echo "[Phase 38] Deploying monitoring stack..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/namespace.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/prometheus-rbac.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/prometheus-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/prometheus-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/prometheus-service.yaml"

echo "[Phase 38] Deploying Grafana..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-datasource-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboards-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-api-health.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-ml-perf.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-kafka.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-service.yaml"

echo "[Phase 38] Waiting for Prometheus..."
kubectl rollout status deployment/prometheus -n monitoring --timeout=120s
echo "[Phase 38] Waiting for Grafana..."
kubectl rollout status deployment/grafana -n monitoring --timeout=120s
echo "[Phase 38] ✓ Monitoring stack deployed"

# --- Phase 39: Structured Logging & Aggregation (Loki + Promtail) ---
echo "[Phase 39] Deploying Loki log aggregation..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/loki-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/loki-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/loki-service.yaml"

echo "[Phase 39] Deploying Promtail log collector..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/promtail-rbac.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/promtail-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/promtail-daemonset.yaml"

echo "[Phase 39] Updating Grafana datasources (adding Loki)..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-datasource-configmap.yaml"

echo "[Phase 39] Waiting for Loki..."
kubectl rollout status deployment/loki -n monitoring --timeout=120s
echo "[Phase 39] Waiting for Promtail..."
kubectl rollout status daemonset/promtail -n monitoring --timeout=120s

# Restart Grafana to pick up new Loki datasource
kubectl rollout restart deployment/grafana -n monitoring
kubectl rollout status deployment/grafana -n monitoring --timeout=120s

echo "[Phase 39] ✓ Loki + Promtail log aggregation deployed"

echo "=== Deployment complete ==="
