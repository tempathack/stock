#!/bin/bash
# run-production-e2e.sh — Run all production Playwright E2E tests against the live cluster
# Usage: ./scripts/run-production-e2e.sh [--report]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PLATFORM_DIR/services/frontend"

OPEN_REPORT=false
for arg in "$@"; do
  case $arg in
    --report) OPEN_REPORT=true ;;
  esac
done

# ---------------------------------------------------------------------------
# Step 1 — Preflight checks
# ---------------------------------------------------------------------------
echo "=== Preflight checks ==="

if ! minikube status | grep -q "host: Running"; then
  echo "ERROR: Minikube is not running. Start it with: minikube start"
  exit 1
fi

if ! command -v kubectl &>/dev/null; then
  echo "ERROR: kubectl not found in PATH"
  exit 1
fi

if ! kubectl config current-context | grep -q "minikube"; then
  echo "WARNING: kubectl context is not minikube (current: $(kubectl config current-context))"
fi

if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found — some checks may not work"
fi

if ! command -v node &>/dev/null || ! command -v npx &>/dev/null; then
  echo "ERROR: node/npx not found in PATH"
  exit 1
fi

echo "Cluster info:"
kubectl get nodes --no-headers 2>/dev/null | awk '{print "  Node:", $1, "Status:", $2}' || true
echo "  Namespaces: $(kubectl get ns --no-headers 2>/dev/null | awk '{print $1}' | tr '\n' ' ')"
echo ""

# ---------------------------------------------------------------------------
# Step 2 — Port-forward management
# ---------------------------------------------------------------------------
echo "=== Starting port-forwards ==="

# Kill stale port-forwards
for port in 3000 8000 3001 9090 9000 9001 8888 8443; do
  pkill -f "kubectl port-forward.*:${port}" 2>/dev/null || true
done
pkill -f "kubectl proxy" 2>/dev/null || true
sleep 1

# Start port-forwards
kubectl port-forward svc/frontend-service 3000:80   -n frontend   >/tmp/pf-frontend.log   2>&1 & echo $! >/tmp/pf-frontend.pid
echo "  frontend        :3000"

kubectl port-forward svc/stock-api 8000:8000 -n ingestion >/tmp/pf-stock-api.log 2>&1 & echo $! >/tmp/pf-stock-api.pid
echo "  API             :8000"

kubectl port-forward svc/grafana 3001:3000 -n monitoring >/tmp/pf-grafana.log 2>&1 & echo $! >/tmp/pf-grafana.pid
echo "  Grafana         :3001"

kubectl port-forward svc/prometheus 9090:9090 -n monitoring >/tmp/pf-prometheus.log 2>&1 & echo $! >/tmp/pf-prometheus.pid
echo "  Prometheus      :9090"

kubectl port-forward svc/minio 9001:9001 -n storage >/tmp/pf-minio-console.log 2>&1 & echo $! >/tmp/pf-minio-console.pid
echo "  MinIO console   :9001"

kubectl port-forward svc/minio 9000:9000 -n storage >/tmp/pf-minio-api.log 2>&1 & echo $! >/tmp/pf-minio-api.pid
echo "  MinIO API       :9000"

kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow >/tmp/pf-kubeflow.log 2>&1 & echo $! >/tmp/pf-kubeflow.pid 2>/dev/null \
  || echo "  KFP not installed — skipping"
echo "  Kubeflow        :8888"

kubectl port-forward svc/kubernetes-dashboard 8443:443 -n kubernetes-dashboard >/tmp/pf-k8s-dashboard.log 2>&1 & echo $! >/tmp/pf-k8s-dashboard.pid 2>/dev/null \
  || echo "  K8s Dashboard not installed — skipping"
echo "  K8s Dashboard   :8443"

sleep 2

# ---------------------------------------------------------------------------
# Wait for services to become reachable
# ---------------------------------------------------------------------------
wait_for_service() {
  local name="$1"
  local url="$2"
  local max_wait=60
  local elapsed=0
  printf "  Waiting for %-20s" "$name..."
  while ! curl -sk --max-time 3 "$url" -o /dev/null 2>/dev/null; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ $elapsed -ge $max_wait ]; then
      echo " TIMEOUT (skipping)"
      return 1
    fi
    printf "."
  done
  echo " OK"
  return 0
}

echo ""
echo "=== Waiting for services ==="
wait_for_service "frontend"      "http://localhost:3000" || true
wait_for_service "API"           "http://localhost:8000/health" || true
wait_for_service "Grafana"       "http://localhost:3001/api/health" || true
wait_for_service "Prometheus"    "http://localhost:9090/-/ready" || true
wait_for_service "MinIO console" "http://localhost:9001" || true
wait_for_service "MinIO API"     "http://localhost:9000/minio/health/live" || true
wait_for_service "Kubeflow"      "http://localhost:8888" || true
wait_for_service "K8s Dashboard" "https://localhost:8443" || true

# ---------------------------------------------------------------------------
# Step 3 — Environment exports
# ---------------------------------------------------------------------------
echo ""
echo "=== Exporting environment ==="
export GRAFANA_URL="http://localhost:3001"
export PROMETHEUS_URL="http://localhost:9090"
export MINIO_URL="http://localhost:9001"
export KUBEFLOW_URL="http://localhost:8888"
export K8S_DASHBOARD_URL="https://localhost:8443"
export BASE_API_URL="http://localhost:8000"

echo "  GRAFANA_URL=$GRAFANA_URL"
echo "  PROMETHEUS_URL=$PROMETHEUS_URL"
echo "  MINIO_URL=$MINIO_URL"
echo "  KUBEFLOW_URL=$KUBEFLOW_URL"
echo "  K8S_DASHBOARD_URL=$K8S_DASHBOARD_URL"
echo "  BASE_API_URL=$BASE_API_URL"

if [ -z "${KUBERNETES_DASHBOARD_TOKEN:-}" ]; then
  echo ""
  echo "  NOTE: KUBERNETES_DASHBOARD_TOKEN is not set."
  echo "  To generate a token for the K8s Dashboard tests, run:"
  echo "    kubectl -n kubernetes-dashboard create token kubernetes-dashboard"
  echo "  Then export it:"
  echo "    export KUBERNETES_DASHBOARD_TOKEN=<token>"
fi

# ---------------------------------------------------------------------------
# Step 4 — Run tests
# ---------------------------------------------------------------------------
echo ""
echo "=== Running production Playwright tests ==="

cd "$FRONTEND_DIR"

EXIT_CODE=0

npx playwright test --config=playwright.production.config.ts || EXIT_CODE=$?

# ---------------------------------------------------------------------------
# Step 5 — Cleanup + report
# ---------------------------------------------------------------------------
echo ""
echo "=== Cleaning up port-forwards ==="
for pid_file in /tmp/pf-*.pid; do
  if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    kill "$pid" 2>/dev/null || true
    rm -f "$pid_file"
  fi
done

if [ "$OPEN_REPORT" = "true" ]; then
  npx playwright show-report || true
fi

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "All tests passed (or skipped gracefully)."
else
  echo "Some tests failed. See playwright-report/index.html for details."
  echo "Run: cd services/frontend && npx playwright show-report"
fi

exit $EXIT_CODE
