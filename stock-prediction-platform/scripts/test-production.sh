#!/usr/bin/env bash
# Usage: ./scripts/test-production.sh [--skip-infra] [--skip-app] [--report]
# Runs all production E2E tests against the live Minikube cluster.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/services/frontend"

# ── Argument parsing ──────────────────────────────────────────────────────────
SKIP_INFRA=false
SKIP_APP=false
OPEN_REPORT=false

for arg in "$@"; do
  case "$arg" in
    --skip-infra) SKIP_INFRA=true ;;
    --skip-app)   SKIP_APP=true   ;;
    --report)     OPEN_REPORT=true ;;
  esac
done

# ── Colors ────────────────────────────────────────────────────────────────────
RESET='\033[0m'
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'

info()    { echo -e "${CYAN}${BOLD}[INFO]${RESET}  $*"; }
ok()      { echo -e "${GREEN}${BOLD}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}${BOLD}[WARN]${RESET}  $*"; }
err()     { echo -e "${RED}${BOLD}[ERROR]${RESET} $*" >&2; }

# ── Port assignments (production test ports — separate from deploy-all.sh) ───
PORT_FRONTEND=3000
PORT_API=8000
PORT_GRAFANA=3001
PORT_PROMETHEUS=9090
PORT_MINIO_CONSOLE=9001
PORT_MINIO_API=9000
PORT_KUBEFLOW=8888
PORT_K8S_DASHBOARD=8443

PF_PIDS=()

cleanup() {
  info "Cleaning up port-forwards..."
  for pid in "${PF_PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  # Also clean up PID files written in this session
  for f in /tmp/pf-prod-*.pid; do
    [ -f "$f" ] && pid=$(cat "$f") && kill "$pid" 2>/dev/null || true
    rm -f "$f"
  done
}
trap cleanup EXIT

# =============================================================================
# Step 1 — Preflight checks
# =============================================================================
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║   Stock Prediction Platform — Production E2E Test Runner    ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
info "Step 1: Preflight checks"

# Minikube running
if ! minikube status 2>/dev/null | grep -q 'host: Running'; then
  err "Minikube is not running. Start it with: minikube start"
  exit 1
fi
ok "Minikube is running"

# kubectl context
if ! kubectl cluster-info --context minikube &>/dev/null; then
  err "kubectl context is not set to minikube. Run: kubectl config use-context minikube"
  exit 1
fi
ok "kubectl context: minikube"

# Required tools
for tool in jq node npx; do
  if ! command -v "$tool" &>/dev/null; then
    err "Required tool not found: $tool"
    exit 1
  fi
done
ok "Required tools present (jq, node, npx)"

# Cluster summary
info "Cluster summary:"
echo -e "  ${DIM}Nodes:$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')${RESET}"
echo -e "  ${DIM}Namespaces: $(kubectl get namespaces --no-headers 2>/dev/null | awk '{print $1}' | tr '\n' ' ')${RESET}"
echo ""

# =============================================================================
# Step 2 — Port-forward management
# =============================================================================
info "Step 2: Setting up port-forwards (test-specific ports)"

# Kill any stale port-forwards on our target ports
for port in $PORT_FRONTEND $PORT_API $PORT_GRAFANA $PORT_PROMETHEUS \
            $PORT_MINIO_CONSOLE $PORT_MINIO_API $PORT_KUBEFLOW $PORT_K8S_DASHBOARD; do
  pkill -f "kubectl port-forward.*:${port}$" 2>/dev/null || true
done
sleep 1

start_pf() {
  local name="$1"; shift
  local cmd=("$@")
  "${cmd[@]}" >/tmp/pf-prod-${name}.log 2>&1 &
  local pid=$!
  echo "$pid" >/tmp/pf-prod-${name}.pid
  PF_PIDS+=("$pid")
  echo -e "  ${DIM}Started $name port-forward (PID $pid)${RESET}"
}

start_pf frontend    kubectl port-forward -n frontend   svc/frontend              ${PORT_FRONTEND}:80
start_pf stock-api   kubectl port-forward -n ingestion  svc/stock-api             ${PORT_API}:8000
start_pf grafana     kubectl port-forward -n monitoring svc/grafana               ${PORT_GRAFANA}:3000
start_pf prometheus  kubectl port-forward -n monitoring svc/prometheus            ${PORT_PROMETHEUS}:9090
start_pf minio-cons  kubectl port-forward -n storage    svc/minio                 ${PORT_MINIO_CONSOLE}:9001
start_pf minio-api   kubectl port-forward -n storage    svc/minio                 ${PORT_MINIO_API}:9000

# Optional services — don't fail if not installed
if kubectl get svc ml-pipeline-ui -n kubeflow &>/dev/null 2>&1; then
  start_pf kubeflow kubectl port-forward -n kubeflow svc/ml-pipeline-ui ${PORT_KUBEFLOW}:80
  ok "Kubeflow Pipelines UI port-forward started"
else
  warn "KFP not installed — kubeflow tests will be skipped"
fi

if kubectl get svc kubernetes-dashboard -n kubernetes-dashboard &>/dev/null 2>&1; then
  start_pf k8s-dashboard kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard ${PORT_K8S_DASHBOARD}:443
  ok "K8s Dashboard port-forward started"
else
  warn "K8s Dashboard not installed — k8s-dashboard tests will be skipped"
fi

echo ""

# =============================================================================
# Step 3 — Wait for services to become reachable
# =============================================================================
info "Step 3: Waiting for services to be reachable (up to 60s each)"

wait_for_service() {
  local name="$1"
  local url="$2"
  local max_attempts="${3:-20}"
  local attempt=0
  echo -n "  Waiting for $name ($url) ..."
  while [ $attempt -lt $max_attempts ]; do
    if curl -sk --max-time 3 "$url" -o /dev/null -w "%{http_code}" 2>/dev/null | grep -qE '^[23]'; then
      echo -e " ${GREEN}ready${RESET}"
      return 0
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 3
  done
  echo -e " ${YELLOW}unreachable (tests will skip)${RESET}"
  return 1
}

wait_for_service "Frontend"         "http://localhost:${PORT_FRONTEND}"       20
wait_for_service "API"              "http://localhost:${PORT_API}/health"      20
wait_for_service "Grafana"          "http://localhost:${PORT_GRAFANA}/api/health" 20
wait_for_service "Prometheus"       "http://localhost:${PORT_PROMETHEUS}/-/ready" 20
wait_for_service "MinIO console"    "http://localhost:${PORT_MINIO_CONSOLE}/login" 20 || true
wait_for_service "MinIO API health" "http://localhost:${PORT_MINIO_API}/minio/health/live" 10 || true
wait_for_service "Kubeflow"         "http://localhost:${PORT_KUBEFLOW}"        10 || true
echo ""

# =============================================================================
# Step 4 — Environment exports
# =============================================================================
info "Step 4: Exporting environment variables"

export BASE_API_URL="http://localhost:${PORT_API}"
export GRAFANA_URL="http://localhost:${PORT_GRAFANA}"
export PROMETHEUS_URL="http://localhost:${PORT_PROMETHEUS}"
export MINIO_URL="http://localhost:${PORT_MINIO_CONSOLE}"
export KUBEFLOW_URL="http://localhost:${PORT_KUBEFLOW}"
export K8S_DASHBOARD_URL="http://localhost:${PORT_K8S_DASHBOARD}"

echo -e "  ${DIM}BASE_API_URL=${BASE_API_URL}${RESET}"
echo -e "  ${DIM}GRAFANA_URL=${GRAFANA_URL}${RESET}"
echo -e "  ${DIM}PROMETHEUS_URL=${PROMETHEUS_URL}${RESET}"
echo -e "  ${DIM}MINIO_URL=${MINIO_URL}${RESET}"
echo -e "  ${DIM}KUBEFLOW_URL=${KUBEFLOW_URL}${RESET}"
echo -e "  ${DIM}K8S_DASHBOARD_URL=${K8S_DASHBOARD_URL}${RESET}"
echo ""

# K8s Dashboard token instructions
if [ -z "${KUBERNETES_DASHBOARD_TOKEN:-}" ]; then
  warn "KUBERNETES_DASHBOARD_TOKEN is not set."
  echo -e "  ${DIM}To generate a token, run:${RESET}"
  echo -e "  ${DIM}  kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard --dry-run=client -o yaml | kubectl apply -f -${RESET}"
  echo -e "  ${DIM}  kubectl create clusterrolebinding dashboard-admin --clusterrole=cluster-admin --serviceaccount=kubernetes-dashboard:dashboard-admin --dry-run=client -o yaml | kubectl apply -f - ${RESET}"
  echo -e "  ${DIM}  export KUBERNETES_DASHBOARD_TOKEN=\$(kubectl create token dashboard-admin -n kubernetes-dashboard)${RESET}"
  echo -e "  ${DIM}K8s Dashboard tests will be skipped.${RESET}"
  echo ""
fi

# =============================================================================
# Step 5 — Run tests
# =============================================================================
info "Step 5: Running tests"

APP_EXIT=0
INFRA_EXIT=0

cd "$FRONTEND_DIR"

if [ "$SKIP_APP" = "false" ]; then
  echo ""
  info "Running production app tests (playwright.production.config.ts)..."
  npx playwright test --config=playwright.production.config.ts || APP_EXIT=$?
  if [ $APP_EXIT -eq 0 ]; then
    ok "App tests passed"
  else
    warn "App tests had failures (exit code $APP_EXIT)"
  fi
fi

if [ "$SKIP_INFRA" = "false" ]; then
  echo ""
  info "Running infra tests (playwright.infra.config.ts)..."
  npx playwright test --config=playwright.infra.config.ts || INFRA_EXIT=$?
  if [ $INFRA_EXIT -eq 0 ]; then
    ok "Infra tests passed"
  else
    warn "Infra tests had failures (exit code $INFRA_EXIT)"
  fi
fi

# =============================================================================
# Step 6 — Summary
# =============================================================================
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║                        Test Summary                         ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if [ "$SKIP_APP" = "false" ]; then
  if [ $APP_EXIT -eq 0 ]; then
    ok "App tests:   PASSED"
  else
    warn "App tests:   FAILED/SKIPPED (exit $APP_EXIT)"
  fi
fi

if [ "$SKIP_INFRA" = "false" ]; then
  if [ $INFRA_EXIT -eq 0 ]; then
    ok "Infra tests: PASSED"
  else
    warn "Infra tests: FAILED/SKIPPED (exit $INFRA_EXIT)"
  fi
fi

REPORT_DIR="$FRONTEND_DIR/playwright-report"
if [ -d "$REPORT_DIR" ]; then
  echo ""
  echo -e "  ${DIM}HTML report: $REPORT_DIR/index.html${RESET}"
  if [ "$OPEN_REPORT" = "true" ]; then
    info "Opening HTML report..."
    npx playwright show-report 2>/dev/null || open "$REPORT_DIR/index.html" 2>/dev/null || xdg-open "$REPORT_DIR/index.html" 2>/dev/null || true
  fi
fi

echo ""

# Exit with non-zero if any test suite failed
OVERALL_EXIT=$(( APP_EXIT + INFRA_EXIT ))
[ $OVERALL_EXIT -gt 0 ] && exit 1 || exit 0
