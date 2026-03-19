#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# setup-minikube.sh — Bootstrap local Minikube Kubernetes cluster
# =============================================================================

# --- Path resolution ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Prerequisite checks ---
check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "ERROR: '$1' is required but not found on PATH" >&2
    exit 1
  fi
}

echo "=== Checking prerequisites ==="
check_command minikube
check_command kubectl
check_command docker
echo "All prerequisites found"

# --- Idempotent cluster start ---
echo "=== Checking Minikube cluster status ==="
MINIKUBE_STATUS=$(minikube status --format='{{.Host}}' 2>/dev/null || true)
if [ "$MINIKUBE_STATUS" = "Running" ]; then
  echo "Minikube cluster is already running -- skipping start"
else
  echo "Starting Minikube cluster..."
  minikube start \
    --driver=docker \
    --cpus=6 \
    --memory=12288 \
    --addons=ingress,metrics-server,dashboard
  echo "Minikube started successfully"
fi

# --- Wait for node readiness ---
echo "=== Waiting for Kubernetes node to be Ready... ==="
kubectl wait --for=condition=Ready node --all --timeout=120s
echo "Node is Ready"

# --- Ensure addons are enabled (idempotent for re-runs) ---
echo "=== Ensuring addons are enabled ==="
for addon in ingress metrics-server dashboard; do
  echo "Ensuring addon enabled: $addon"
  minikube addons enable "$addon"
done
echo "All addons enabled"

# --- Apply namespaces ---
echo "=== Applying namespace manifests... ==="
kubectl apply -f "$PROJECT_ROOT/k8s/namespaces.yaml"
echo "Namespaces applied"

# --- Phase 4: PostgreSQL secrets and init SQL ConfigMap ---
# DEV ONLY: password is devpassword123 — never use this in production
echo "=== Creating PostgreSQL secret (dev-only password) ==="
kubectl create secret generic stock-platform-secrets \
  --from-literal=POSTGRES_PASSWORD=devpassword123 \
  -n storage \
  --dry-run=client -o yaml | kubectl apply -f -

echo "=== Creating PostgreSQL init SQL ConfigMap ==="
kubectl create configmap postgresql-init-sql \
  --from-file=init.sql="$PROJECT_ROOT/db/init.sql" \
  -n storage \
  --dry-run=client -o yaml | kubectl apply -f -

# --- Phase 5: Strimzi Kafka Operator ---
echo "=== Installing Strimzi Kafka Operator ==="
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/strimzi-operator.yaml" -n storage
echo "Waiting for Strimzi operator to be ready..."
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator -n storage --timeout=300s
echo "Strimzi operator ready"

# --- Verification ---
echo "=== Verifying namespaces ==="
kubectl get namespaces
echo ""
echo "Cluster ready"
