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

# --- Phase 65: Argo CD GitOps Bootstrap ---
echo "[Phase 65] Checking Argo CD installation..."
if ! kubectl get namespace argocd &>/dev/null; then
  echo "[Phase 65] Installing Argo CD v3.3.6..."
  kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
  kubectl apply -n argocd \
    -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.3.6/manifests/install.yaml \
    --server-side --force-conflicts
  kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=180s

  # Install argocd CLI if missing
  if ! command -v argocd &>/dev/null; then
    curl -sSL -o /tmp/argocd-linux-amd64 \
      https://github.com/argoproj/argo-cd/releases/download/v3.3.6/argocd-linux-amd64
    sudo install -m 555 /tmp/argocd-linux-amd64 /usr/local/bin/argocd
  fi
fi

# Start port-forward to argocd-server for CLI commands
kubectl port-forward svc/argocd-server -n argocd 8080:443 >/tmp/pf-argocd.log 2>&1 &
ARGOCD_PF_PID=$!
sleep 4

ARGOCD_PWD=$(argocd admin initial-password -n argocd 2>/dev/null | head -1 || \
  kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")

if [ -n "$ARGOCD_PWD" ]; then
  echo "$ARGOCD_PWD" >/tmp/argocd-pwd.txt
  argocd login localhost:8080 --username admin --password "$ARGOCD_PWD" --insecure --grpc-web

  # Register repo if credentials available
  GITHUB_PAT="${GITHUB_TOKEN:-${ARGOCD_GITHUB_PAT:-}}"
  if [ -n "$GITHUB_PAT" ]; then
    argocd repo add https://github.com/tempathack/stock.git \
      --username tempathack --password "$GITHUB_PAT" 2>/dev/null || true
  fi

  # Apply root app (idempotent)
  kubectl apply -n argocd -f "$PROJECT_ROOT/k8s/argocd/root-app.yaml"
  sleep 5
  argocd app sync root-app --timeout 120 2>/dev/null || true
  argocd app sync --all --timeout 300 2>/dev/null || true
  echo "[Phase 65] Argo CD sync triggered for all applications"
else
  echo "[Phase 65] WARNING: Could not obtain Argo CD admin password — skipping app sync"
fi

kill $ARGOCD_PF_PID 2>/dev/null || true
echo "[Phase 65] Argo CD bootstrap complete"

# --- Phase 2: Namespaces ---
echo "[Phase 2] Applying namespaces..."
kubectl apply -f "$PROJECT_ROOT/k8s/namespaces.yaml"

# --- Phase 3: Build stock-api Docker image ---
echo "[Phase 3] Building stock-api Docker image..."
eval $(minikube docker-env)
docker build -t stock-api:latest -f "$PROJECT_ROOT/services/api/Dockerfile" "$PROJECT_ROOT"
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
    # Use delete+create (idempotent) to avoid resourceVersion conflicts with kubectl apply via pipe
    for ns in ingestion processing ml; do
        kubectl delete secret stock-platform-secrets -n "$ns" --ignore-not-found
        kubectl get secret stock-platform-secrets -n storage -o json \
            | python3 -c "import sys,json; d=json.load(sys.stdin); d['metadata']={k:v for k,v in d['metadata'].items() if k in ('name','labels','annotations')}; d['metadata']['namespace']='$ns'; d['metadata'].pop('annotations',None); print(json.dumps(d))" \
            | kubectl create -f -
    done
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
kubectl wait --for=condition=complete job/minio-init-buckets -n storage --timeout=120s

# Copy MinIO secrets and config to ml namespace
# Use delete+create (idempotent) to avoid resourceVersion conflicts with kubectl apply via pipe
kubectl delete secret minio-secrets -n ml --ignore-not-found
kubectl get secret minio-secrets -n storage -o json \
    | python3 -c "import sys,json; d=json.load(sys.stdin); d['metadata']={k:v for k,v in d['metadata'].items() if k in ('name','labels')}; d['metadata']['namespace']='ml'; print(json.dumps(d))" \
    | kubectl create -f -
kubectl delete configmap minio-config -n ml --ignore-not-found
kubectl get configmap minio-config -n storage -o json \
    | python3 -c "import sys,json; d=json.load(sys.stdin); d['metadata']={k:v for k,v in d['metadata'].items() if k in ('name','labels')}; d['metadata']['namespace']='ml'; print(json.dumps(d))" \
    | kubectl create -f -

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
# Use --server-side to avoid the 256KB last-applied-configuration annotation limit on KServe CRDs
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve.yaml \
    --server-side --force-conflicts
kubectl wait --for=condition=Available deployment/kserve-controller-manager -n kserve --timeout=180s

echo "[Phase 54] Installing KServe cluster resources (ServingRuntimes)..."
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve-cluster-resources.yaml \
    --server-side --force-conflicts

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

# --- Phase 67: Apache Flink — Real-Time Stream Processing ---
echo "[Phase 67] Applying Flink namespace and RBAC..."
# Note: flink namespace is already in namespaces.yaml applied in Phase 2 block above
kubectl apply -f "$PROJECT_ROOT/k8s/flink/rbac.yaml"

echo "[Phase 67] Applying processed-features Kafka topic..."
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-topic-processed-features.yaml"

echo "[Phase 67] Copying secrets to flink namespace..."
kubectl delete secret stock-platform-secrets -n flink --ignore-not-found
kubectl get secret stock-platform-secrets -n storage -o json \
    | python3 -c "import sys,json; d=json.load(sys.stdin); d['metadata']={k:v for k,v in d['metadata'].items() if k in ('name','labels')}; d['metadata']['namespace']='flink'; print(json.dumps(d))" \
    | kubectl create -f -
kubectl delete secret minio-secrets -n flink --ignore-not-found
kubectl get secret minio-secrets -n storage -o json \
    | python3 -c "import sys,json; d=json.load(sys.stdin); d['metadata']={k:v for k,v in d['metadata'].items() if k in ('name','labels')}; d['metadata']['namespace']='flink'; print(json.dumps(d))" \
    | kubectl create -f -

echo "[Phase 67] Applying Flink ConfigMap..."
kubectl apply -f "$PROJECT_ROOT/k8s/flink/flink-config-configmap.yaml"

echo "[Phase 67] Building Flink Docker images (in minikube docker context)..."
eval $(minikube docker-env)
docker build -t stock-flink-ohlcv-normalizer:latest \
    "$PROJECT_ROOT/services/flink-jobs/ohlcv_normalizer/"
docker build -t stock-flink-indicator-stream:latest \
    "$PROJECT_ROOT/services/flink-jobs/indicator_stream/"
docker build -t stock-flink-feast-writer:latest \
    "$PROJECT_ROOT/services/flink-jobs/feast_writer/"
echo "[Phase 67] Flink Docker images built"

echo "[Phase 67] Deploying FlinkDeployment CRs..."
kubectl apply -f "$PROJECT_ROOT/k8s/flink/flinkdeployment-ohlcv-normalizer.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/flink/flinkdeployment-indicator-stream.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/flink/flinkdeployment-feast-writer.yaml"

echo "[Phase 67] Waiting for Flink jobs to reach RUNNING state (up to 180s)..."
FLINK_TIMEOUT=180
FLINK_ELAPSED=0
FLINK_INTERVAL=10
until kubectl get flinkdeployment -n flink \
    -o jsonpath='{range .items[*]}{.status.jobManagerDeploymentStatus}{"\n"}{end}' 2>/dev/null \
    | grep -v READY | wc -l | grep -q "^0$" 2>/dev/null \
    || [ $FLINK_ELAPSED -ge $FLINK_TIMEOUT ]; do
  echo "[Phase 67] Waiting for Flink jobs... ${FLINK_ELAPSED}s elapsed"
  sleep $FLINK_INTERVAL
  FLINK_ELAPSED=$((FLINK_ELAPSED + FLINK_INTERVAL))
done
echo "[Phase 67] Flink job status:"
kubectl get flinkdeployment -n flink
echo "[Phase 67] Apache Flink stream processing deployed"

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

# --- Phase 20: Kubeflow Pipelines ---
echo "[Phase 20] Installing Kubeflow Pipelines (standalone, v2.3.0)..."
export PIPELINE_VERSION=2.3.0
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION" \
    --server-side --force-conflicts
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=$PIPELINE_VERSION" \
    --server-side --force-conflicts

echo "[Phase 20] Waiting for KFP API server to be ready..."
kubectl wait --for=condition=Available deployment/ml-pipeline \
    -n kubeflow --timeout=300s
kubectl wait --for=condition=Available deployment/ml-pipeline-ui \
    -n kubeflow --timeout=300s

echo "[Phase 20] Applying KFP install reference ConfigMap..."
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kubeflow/kfp-standalone.yaml"

# --- Phase 20: Compile KFP pipeline YAML ---
echo "[Phase 20] Compiling KFP pipeline (in-cluster Job)..."
kubectl delete job compile-kfp-pipeline -n ml --ignore-not-found
kubectl apply -f "$PROJECT_ROOT/k8s/ml/kubeflow/compile-pipeline-job.yaml"

echo "[Phase 20] Waiting for compile job to complete (up to 120s)..."
if kubectl wait --for=condition=complete job/compile-kfp-pipeline \
       -n ml --timeout=120s 2>/dev/null; then
  COMPILE_POD=$(kubectl get pod -l job-name=compile-kfp-pipeline -n ml \
      -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
  if [ -n "$COMPILE_POD" ]; then
    echo "[Phase 20] Retrieving compiled pipeline YAML from pod $COMPILE_POD ..."
    kubectl cp "ml/${COMPILE_POD}:/pipelines/training_pipeline.yaml" \
        /tmp/training_pipeline.yaml 2>/dev/null \
        && echo "[Phase 20] Compiled YAML saved to /tmp/training_pipeline.yaml" \
        || echo "[Phase 20] WARNING: kubectl cp failed; retrieve manually."
  fi
  echo "[Phase 20] ✓ KFP pipeline compiled successfully"
  echo "[Phase 20]   To submit a pipeline run:"
  echo "[Phase 20]     kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow &"
  echo "[Phase 20]     $SCRIPT_DIR/submit-pipeline.sh"
else
  echo "[Phase 20] WARNING: compile job did not complete within 120s."
  echo "[Phase 20]   Check logs: kubectl logs -l job-name=compile-kfp-pipeline -n ml"
  echo "[Phase 20]   Once ready, submit with: $SCRIPT_DIR/submit-pipeline.sh"
fi

# NOTE: Uploading the pipeline to the KFP UI and creating a run requires the
# KFP Python SDK client (kfp >= 2.0) on the machine running this script.
# Use scripts/submit-pipeline.sh for that step — it handles both one-shot
# runs and recurring runs via cron.  Example:
#
#   PIPELINE_YAML=/tmp/training_pipeline.yaml \
#   EXPERIMENT_NAME=stock-prediction          \
#   ./scripts/submit-pipeline.sh
#
#   # Recurring daily at 02:00 UTC:
#   RECURRING=true CRON="0 2 * * *" ./scripts/submit-pipeline.sh

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

echo "[Phase 38] Deploying Alertmanager..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/alertmanager-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/alertmanager-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/alertmanager-service.yaml"

echo "[Phase 38] Deploying Grafana..."
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-datasource-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboards-configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-api-health.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-ml-perf.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-kafka.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-dashboard-flink.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-deployment.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/grafana-service.yaml"

echo "[Phase 38] Waiting for Prometheus..."
kubectl rollout status deployment/prometheus -n monitoring --timeout=120s
echo "[Phase 38] Waiting for Alertmanager..."
kubectl rollout status deployment/alertmanager -n monitoring --timeout=120s
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

# --- Kubernetes Dashboard ---
echo "[Dashboard] Deploying Kubernetes Dashboard v2.7.0..."
kubectl apply -f "$PROJECT_ROOT/k8s/dashboard/kubernetes-dashboard.yaml"

echo "[Dashboard] Waiting for Kubernetes Dashboard to be ready..."
kubectl rollout status deployment/kubernetes-dashboard -n kubernetes-dashboard --timeout=120s 2>/dev/null \
    || echo "WARNING: kubernetes-dashboard deployment not ready yet — it may still be pulling the image"

echo "[Dashboard] Creating dashboard-admin service account and cluster-admin binding..."
kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard \
    --dry-run=client -o yaml | kubectl apply -f -
kubectl create clusterrolebinding dashboard-admin \
    --clusterrole=cluster-admin \
    --serviceaccount=kubernetes-dashboard:dashboard-admin \
    --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "=== K8s Dashboard Token ==="
KUBERNETES_DASHBOARD_TOKEN=$(kubectl create token dashboard-admin -n kubernetes-dashboard 2>/dev/null || true)
if [ -n "$KUBERNETES_DASHBOARD_TOKEN" ]; then
    echo "KUBERNETES_DASHBOARD_TOKEN=$KUBERNETES_DASHBOARD_TOKEN"
    echo ""
    echo "Export with:"
    echo "  export KUBERNETES_DASHBOARD_TOKEN='$KUBERNETES_DASHBOARD_TOKEN'"
else
    echo "WARNING: Could not generate dashboard token — ensure kubernetes-dashboard namespace is ready."
    echo "Retry with: kubectl create token dashboard-admin -n kubernetes-dashboard"
fi
echo ""

echo "[Dashboard] ✓ Kubernetes Dashboard deployed"

echo "=== Deployment complete ==="

# =============================================================================
# Port-forwarding — expose all UIs on localhost
# =============================================================================
echo ""
echo "=== Setting up port-forwarding ==="

# Kill any stale port-forwards on our ports to avoid bind conflicts
for port in 8079 8080 8000 3000 9090 9001 3100; do
  pkill -f "kubectl port-forward.*:${port}" 2>/dev/null || true
done
sleep 1

# Wait for pods before forwarding
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=frontend    -n frontend   --timeout=120s 2>/dev/null || echo "WARNING: frontend pod not ready yet"
kubectl wait --for=condition=ready pod -l app=stock-api   -n ingestion  --timeout=120s 2>/dev/null || echo "WARNING: stock-api pod not ready yet"
kubectl wait --for=condition=ready pod -l app=grafana     -n monitoring --timeout=120s 2>/dev/null || echo "WARNING: grafana pod not ready yet"
kubectl wait --for=condition=ready pod -l app=prometheus  -n monitoring --timeout=120s 2>/dev/null || echo "WARNING: prometheus pod not ready yet"
kubectl wait --for=condition=ready pod -l app=minio       -n storage    --timeout=120s 2>/dev/null || echo "WARNING: minio pod not ready yet"
kubectl wait --for=condition=ready pod -l app=loki        -n monitoring --timeout=120s 2>/dev/null || echo "WARNING: loki pod not ready yet"

# Start port-forwards in background, log output to /tmp
kubectl port-forward svc/frontend   8080:80   -n frontend   >/tmp/pf-frontend.log   2>&1 & echo $! >/tmp/pf-frontend.pid
kubectl port-forward svc/stock-api  8000:8000 -n ingestion  >/tmp/pf-stock-api.log  2>&1 & echo $! >/tmp/pf-stock-api.pid
kubectl port-forward svc/grafana    3000:3000 -n monitoring >/tmp/pf-grafana.log    2>&1 & echo $! >/tmp/pf-grafana.pid
kubectl port-forward svc/prometheus 9090:9090 -n monitoring >/tmp/pf-prometheus.log 2>&1 & echo $! >/tmp/pf-prometheus.pid
kubectl port-forward svc/minio      9001:9001 -n storage    >/tmp/pf-minio.log      2>&1 & echo $! >/tmp/pf-minio.pid
kubectl port-forward svc/loki       3100:3100 -n monitoring >/tmp/pf-loki.log       2>&1 & echo $! >/tmp/pf-loki.pid
kubectl port-forward svc/argocd-server 8079:443 -n argocd >/tmp/pf-argocd-ui.log 2>&1 & echo $! >/tmp/pf-argocd-ui.pid

# Kubernetes dashboard runs through kubectl proxy (not a standard svc port-forward)
pkill -f "kubectl proxy" 2>/dev/null || true
kubectl proxy --port=8001 >/tmp/pf-k8s-dashboard.log 2>&1 & echo $! >/tmp/pf-k8s-dashboard.pid

# Kubeflow Pipelines UI
kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow >/tmp/pf-kubeflow.log 2>&1 & echo $! >/tmp/pf-kubeflow.pid

sleep 2

# =============================================================================
# Link summary
# =============================================================================
RESET='\033[0m'
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
BLUE='\033[0;34m'
WHITE='\033[1;37m'
DIM='\033[2m'

echo ""
echo -e "${BOLD}┌─────────────────────────────────────────────────────────────┐${RESET}"
echo -e "${BOLD}│           Stock Prediction Platform  —  Access Links         │${RESET}"
echo -e "${BOLD}└─────────────────────────────────────────────────────────────┘${RESET}"
echo ""
echo -e "  ${GREEN}${BOLD}React Dashboard${RESET}       ${DIM}──>${RESET}  ${GREEN}http://localhost:8080${RESET}"
echo -e "  ${DIM}                           /forecasts  /drift  /models  /dashboard${RESET}"
echo ""
echo -e "  ${CYAN}${BOLD}Stock API (FastAPI)${RESET}   ${DIM}──>${RESET}  ${CYAN}http://localhost:8000/docs${RESET}"
echo -e "  ${DIM}                           Swagger UI — /predict/{ticker}  /health${RESET}"
echo ""
echo -e "  ${YELLOW}${BOLD}Grafana${RESET}               ${DIM}──>${RESET}  ${YELLOW}http://localhost:3000${RESET}  ${DIM}(admin / admin)${RESET}"
echo -e "  ${DIM}                           ML performance, API health, Kafka dashboards${RESET}"
echo ""
echo -e "  ${MAGENTA}${BOLD}Prometheus${RESET}            ${DIM}──>${RESET}  ${MAGENTA}http://localhost:9090${RESET}"
echo -e "  ${DIM}                           Raw metrics explorer & alerting rules${RESET}"
echo ""
echo -e "  ${BLUE}${BOLD}MinIO Console${RESET}         ${DIM}──>${RESET}  ${BLUE}http://localhost:9001${RESET}"
echo -e "  ${DIM}                           S3 browser — model-artifacts / drift-logs buckets${RESET}"
echo ""
echo -e "  ${WHITE}${BOLD}Loki (log query API)${RESET}  ${DIM}──>${RESET}  ${WHITE}http://localhost:3100/metrics${RESET}"
echo -e "  ${DIM}                           Query logs via Grafana Explore (not a standalone UI)${RESET}"
echo ""
echo -e "  \033[0;33m${BOLD}Kubeflow Pipelines${RESET}    ${DIM}──>${RESET}  \033[0;33mhttp://localhost:8888${RESET}"
echo -e "  ${DIM}                           Pipeline runs, experiments, artifacts${RESET}"
echo ""
echo -e "  \033[0;32m${BOLD}Kubernetes Dashboard${RESET}  ${DIM}──>${RESET}  \033[0;32mhttp://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/${RESET}"
echo -e "  ${DIM}                           Cluster overview — pods, deployments, logs${RESET}"
echo ""
echo -e "  \033[1;35m${BOLD}Argo CD UI${RESET}            ${DIM}──>${RESET}  \033[1;35mhttps://localhost:8079${RESET}  ${DIM}(admin / see /tmp/argocd-pwd.txt)${RESET}"
echo -e "  ${DIM}                           GitOps sync status for all 7 platform applications${RESET}"
echo ""
echo -e "  ${DIM}Port-forward PIDs saved to /tmp/pf-*.pid${RESET}"
echo -e "  ${DIM}Stop all forwards:  pkill -f 'kubectl port-forward'${RESET}"
echo ""
