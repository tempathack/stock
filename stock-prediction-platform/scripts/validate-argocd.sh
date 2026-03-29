#!/usr/bin/env bash
# validate-argocd.sh — Phase 65 smoke test for Argo CD GitOps requirements
# Tests: GITOPS-01 through GITOPS-05
# Runtime: ~30 seconds on healthy cluster
# Usage: ./scripts/validate-argocd.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PASS=0
FAIL=0
ARGOCD_PF_PID=""

# ── Cleanup port-forward on exit ──────────────────────────────────────────────
cleanup() {
  if [ -n "$ARGOCD_PF_PID" ]; then
    kill "$ARGOCD_PF_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

check() {
  local id="$1"
  local desc="$2"
  local cmd="$3"
  if eval "$cmd" &>/dev/null; then
    echo "  PASS [$id] $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL [$id] $desc"
    echo "       Command: $cmd"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "=== Argo CD GitOps Validation — Phase 65 ==="
echo ""

# ── GITOPS-01: Argo CD installed in argocd namespace ─────────────────────────
echo "--- GITOPS-01: Argo CD Installation ---"
check "GITOPS-01-a" "argocd namespace exists" \
  "kubectl get namespace argocd -o jsonpath='{.status.phase}' | grep -q Active"
check "GITOPS-01-b" "argocd-server deployment available" \
  "kubectl get deployment argocd-server -n argocd -o jsonpath='{.status.availableReplicas}' | grep -qE '^[1-9]'"
check "GITOPS-01-c" "argocd-repo-server deployment available" \
  "kubectl get deployment argocd-repo-server -n argocd -o jsonpath='{.status.availableReplicas}' | grep -qE '^[1-9]'"
check "GITOPS-01-d" "argocd CLI installed" \
  "command -v argocd"

# ── Start port-forward for CLI commands ──────────────────────────────────────
echo ""
echo "--- Setting up port-forward to argocd-server (localhost:8080) ---"
kubectl port-forward svc/argocd-server -n argocd 8080:443 >/tmp/pf-argocd-validate.log 2>&1 &
ARGOCD_PF_PID=$!
sleep 4

# Login (required for argocd app commands)
ARGOCD_PWD=$(argocd admin initial-password -n argocd 2>/dev/null | head -1 || \
  kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")

if [ -n "$ARGOCD_PWD" ]; then
  argocd login localhost:8080 \
    --username admin \
    --password "$ARGOCD_PWD" \
    --insecure \
    --grpc-web \
    2>/dev/null || echo "  WARNING: argocd login failed — CLI checks will use kubectl only"
fi

# ── GITOPS-02: Root Application exists and is Synced ─────────────────────────
echo ""
echo "--- GITOPS-02: Root Application (app-of-apps) ---"
check "GITOPS-02-a" "root-app Application CR exists" \
  "kubectl get applications.argoproj.io root-app -n argocd"
check "GITOPS-02-b" "root-app source path points to k8s/argocd" \
  "kubectl get applications.argoproj.io root-app -n argocd -o jsonpath='{.spec.source.path}' | grep -q 'stock-prediction-platform/k8s/argocd'"
check "GITOPS-02-c" "root-app repoURL is correct" \
  "kubectl get applications.argoproj.io root-app -n argocd -o jsonpath='{.spec.source.repoURL}' | grep -q 'github.com/tempathack/stock'"

# ── GITOPS-03: 7 child Application CRs exist ─────────────────────────────────
echo ""
echo "--- GITOPS-03: Child Application CRs (7 required) ---"
EXPECTED_APPS="ingestion processing storage kafka ml frontend monitoring"
for app in $EXPECTED_APPS; do
  check "GITOPS-03-${app}" "Application '${app}' exists in argocd namespace" \
    "kubectl get applications.argoproj.io ${app} -n argocd"
done
check "GITOPS-03-count" "Total applications count >= 8 (root + 7 children)" \
  "[ \$(kubectl get applications.argoproj.io -n argocd --no-headers 2>/dev/null | wc -l) -ge 8 ]"

# ── GITOPS-04: Automated sync with prune+selfHeal ────────────────────────────
echo ""
echo "--- GITOPS-04: Sync Policies ---"
for app in $EXPECTED_APPS; do
  check "GITOPS-04-prune-${app}" "App '${app}' has prune: true" \
    "kubectl get applications.argoproj.io ${app} -n argocd -o jsonpath='{.spec.syncPolicy.automated.prune}' | grep -q true"
  check "GITOPS-04-selfheal-${app}" "App '${app}' has selfHeal: true" \
    "kubectl get applications.argoproj.io ${app} -n argocd -o jsonpath='{.spec.syncPolicy.automated.selfHeal}' | grep -q true"
done

# ── GITOPS-05: Custom health checks in argocd-cm ─────────────────────────────
echo ""
echo "--- GITOPS-05: Custom Health Checks ---"
check "GITOPS-05-strimzi" "argocd-cm has Strimzi Kafka health check" \
  "kubectl get cm argocd-cm -n argocd -o yaml | grep -q 'resource.customizations.health.kafka.strimzi.io_Kafka'"
check "GITOPS-05-kserve" "argocd-cm has KServe InferenceService health check" \
  "kubectl get cm argocd-cm -n argocd -o yaml | grep -q 'resource.customizations.health.serving.kserve.io_InferenceService'"
check "GITOPS-05-file" "argocd-cm-health.yaml tracked in git (k8s/argocd/)" \
  "test -f '$PROJECT_ROOT/k8s/argocd/argocd-cm-health.yaml'"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Results ==="
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo "All Phase 65 checks PASSED — Argo CD GitOps pipeline is operational."
  exit 0
else
  echo "FAIL: $FAIL check(s) failed. Review output above."
  exit 1
fi
