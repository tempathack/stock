# Phase 2: Minikube & K8s Namespaces - Research

**Researched:** 2026-03-18
**Domain:** Local Kubernetes cluster bootstrap (Minikube + shell scripting)
**Confidence:** HIGH

## Summary

Phase 2 delivers two executable shell scripts and confirms that namespace manifests (already written in Phase 1) are applied correctly. The technical surface is narrow -- Minikube CLI, kubectl, and bash scripting -- all of which are stable, well-documented tools. The main engineering challenge is idempotency (safe re-runs) and future-proofing `deploy-all.sh` with stub sections for phases 3-30.

The local environment has minikube v1.35.0, kubectl v1.30.14, and Docker 29.1.5 installed. A minikube cluster is already running on this machine, which confirms the docker driver works. The `--addons` flag on `minikube start` accepts a comma-separated list to enable addons at startup time. Node readiness can be verified with `kubectl wait --for=condition=Ready node --all --timeout=Ns`.

**Primary recommendation:** Write two focused shell scripts with prerequisite checks, idempotent start logic, verbose echo output, and `set -euo pipefail`. Use `kubectl wait` for readiness instead of manual polling loops. Keep `deploy-all.sh` simple with clearly labelled phase-stub sections.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Driver: `docker` -- most portable, no VM overhead, requires Docker Engine running
- CPU: 6 CPUs
- Memory: 12GB RAM
- Addons to enable at startup: `ingress`, `metrics-server`, `dashboard`
- After start: poll `kubectl get nodes` until status is `Ready`, then confirm all enabled addons are running; fail if not ready within timeout
- deploy-all.sh: Write the complete ordered script now with all future sections present but commented out -- uncomment per-phase as manifests land
- Explicit dependency order: Namespaces -> Storage (PVC/DB) -> Kafka -> Ingestion -> Processing -> ML -> Frontend
- Each section clearly labelled with the phase that activates it
- Both scripts use `set -euo pipefail` -- fail fast on any command failure
- `setup-minikube.sh` is idempotent: check `minikube status` first; if cluster is already `Running`, skip start and proceed directly to namespace apply
- Verbosity: step-by-step `echo` statements for each major action -- no silent running
- `setup-minikube.sh`: validate `minikube`, `kubectl`, and `docker` are on `$PATH` before doing anything; print clear error and exit if any are missing
- `deploy-all.sh`: validate `kubectl` is available and `minikube status` shows running before applying any manifests
- deploy-all.sh section stubs should include the phase number in comments

### Claude's Discretion
- Exact readiness poll timeout value and retry interval
- Specific echo formatting / colour codes (if any)
- Whether to use a shared `check_prereqs` function or inline checks

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Minikube cluster initialized with 5 namespaces: ingestion, processing, storage, ml, frontend | Verified minikube start flags, kubectl apply for namespaces.yaml, kubectl wait for readiness |
| INFRA-02 | K8s namespace YAML manifests for all 5 namespaces | Already exists at `k8s/namespaces.yaml` -- no work needed, just apply |
| INFRA-04 | setup-minikube.sh shell script with all cluster bootstrap steps | Full script pattern documented below with idempotency, prereqs, addons, readiness |
| INFRA-05 | deploy-all.sh orchestration script | Full script pattern documented below with stub sections for phases 3-30 |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| minikube | v1.35.0 (installed) | Local K8s cluster | De facto local K8s tool, project requirement |
| kubectl | v1.30.14 (installed) | K8s CLI | Standard K8s client, pairs with minikube |
| docker | 29.1.5 (installed) | Container runtime / minikube driver | Locked decision: docker driver |
| bash | system | Shell scripting | Both scripts are .sh, uses `set -euo pipefail` |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `minikube addons enable` | Enable K8s addons post-start | Fallback if `--addons` flag at start doesn't enable all |
| `kubectl wait` | Readiness polling | Node and pod readiness verification |
| `kubectl get` | Status checks | Addon pod verification in kube-system namespace |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual polling loop | `kubectl wait --for=condition=Ready` | kubectl wait is cleaner, built-in timeout; use it |
| `minikube addons enable` post-start | `--addons` flag on start | Flag is cleaner but may silently skip on re-runs; use both for idempotency |

## Architecture Patterns

### Recommended Project Structure
```
stock-prediction-platform/
  scripts/
    setup-minikube.sh      # Cluster bootstrap (this phase)
    deploy-all.sh           # Manifest orchestration (this phase)
  k8s/
    namespaces.yaml         # Already exists from Phase 1
```

### Pattern 1: Idempotent Cluster Bootstrap
**What:** Check minikube status before starting; skip start if already running.
**When to use:** Every invocation of setup-minikube.sh.
**Example:**
```bash
# Source: minikube CLI verified locally
MINIKUBE_STATUS=$(minikube status --format='{{.Host}}' 2>/dev/null || true)
if [ "$MINIKUBE_STATUS" = "Running" ]; then
  echo "Minikube is already running -- skipping start"
else
  echo "Starting Minikube..."
  minikube start \
    --driver=docker \
    --cpus=6 \
    --memory=12288 \
    --addons=ingress,metrics-server,dashboard
fi
```

### Pattern 2: Node Readiness with kubectl wait
**What:** Use `kubectl wait` instead of a manual poll loop for node readiness.
**When to use:** After minikube start or when verifying existing cluster.
**Example:**
```bash
# Source: kubectl wait verified locally
echo "Waiting for node to be Ready..."
kubectl wait --for=condition=Ready node --all --timeout=120s
echo "Node is Ready"
```

### Pattern 3: Addon Verification
**What:** After start, ensure addons are enabled (idempotent for re-runs where --addons wasn't passed).
**When to use:** Always, to handle the case where cluster was already running but addons weren't enabled.
**Example:**
```bash
# Ensure addons are enabled (idempotent -- safe if already enabled)
for addon in ingress metrics-server dashboard; do
  echo "Enabling addon: $addon"
  minikube addons enable "$addon"
done
```

### Pattern 4: Addon Pod Readiness Check
**What:** Verify that addon pods are actually running, not just enabled.
**When to use:** After enabling addons, before declaring cluster ready.
**Example:**
```bash
echo "Waiting for metrics-server pod..."
kubectl wait --for=condition=Ready pod -l k8s-app=metrics-server -n kube-system --timeout=120s

echo "Waiting for ingress controller pod..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=controller -n ingress-nginx --timeout=120s
```
**Note:** The ingress addon deploys to the `ingress-nginx` namespace. The dashboard addon deploys to the `kubernetes-dashboard` namespace. These are minikube-specific namespace conventions. The labels may vary by minikube version -- if exact label selectors are uncertain, a fallback approach is to just check the addon is listed as enabled via `minikube addons list`.

### Pattern 5: Prerequisite Checks
**What:** Validate required binaries are on PATH before doing anything.
**When to use:** Top of every script.
**Recommendation (Claude's Discretion):** Use a shared function -- it reduces duplication and is cleaner.
**Example:**
```bash
check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "ERROR: '$1' is required but not found on PATH" >&2
    exit 1
  fi
}

check_command minikube
check_command kubectl
check_command docker
```

### Pattern 6: deploy-all.sh Stub Structure
**What:** Full ordered script with commented-out sections per phase.
**When to use:** The deploy-all.sh script structure.
**Example:**
```bash
#!/usr/bin/env bash
set -euo pipefail

# --- Phase 2: Namespaces ---
echo "Applying namespaces..."
kubectl apply -f k8s/namespaces.yaml

# --- Phase 4: Storage (PostgreSQL + TimescaleDB) ---
# echo "Deploying PostgreSQL..."
# kubectl apply -f k8s/storage/

# --- Phase 5: Kafka (Strimzi) ---
# echo "Deploying Strimzi operator..."
# kubectl apply -f k8s/kafka/

# ... etc for all phases in dependency order
```

### Anti-Patterns to Avoid
- **Hardcoded sleep for readiness:** Never use `sleep 30` instead of `kubectl wait`. Sleeps are fragile and waste time.
- **Missing error handling on re-runs:** Always handle the case where minikube is already running. A bare `minikube start` will reconfigure an existing cluster (changing CPUs/memory), which may not be desired.
- **Applying manifests before node is ready:** Always wait for node Ready status before running `kubectl apply`.
- **Forgetting `set -euo pipefail`:** Without it, failed commands are silently ignored.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Node readiness polling | Custom while-loop with sleep | `kubectl wait --for=condition=Ready node --all --timeout=120s` | Built-in, handles edge cases, respects timeouts |
| Command existence check | Manual `which` or path inspection | `command -v` | POSIX standard, works in all shells |
| Addon status check | Parsing `kubectl get pods` output | `minikube addons list -o json` or `minikube addons enable` (idempotent) | minikube manages its own addon state |

## Common Pitfalls

### Pitfall 1: Memory Specification Units
**What goes wrong:** Minikube `--memory` flag accepts values in MB by default, not GB. Passing `12` means 12MB, not 12GB.
**Why it happens:** Confusion between MB and GB.
**How to avoid:** Use `--memory=12288` (MB) or `--memory=12g` (explicit GB suffix).
**Warning signs:** Cluster starts but pods get OOMKilled immediately.

### Pitfall 2: Addons Not Ready After Enable
**What goes wrong:** `minikube addons enable ingress` returns immediately but the ingress controller pod takes 30-60 seconds to start.
**Why it happens:** Addon enable is asynchronous.
**How to avoid:** After enabling addons, wait for the corresponding pods to reach Ready state before declaring the cluster ready.
**Warning signs:** Subsequent phases fail with "connection refused" or "no endpoints available".

### Pitfall 3: Re-running minikube start Changes Config
**What goes wrong:** Running `minikube start --cpus=6 --memory=12288` on an already-running cluster may attempt to reconfigure it, or may ignore the flags silently.
**Why it happens:** Minikube start on an existing cluster doesn't always apply new resource limits without `minikube delete` first.
**How to avoid:** The idempotency check (`minikube status` first) sidesteps this entirely. If cluster is Running, skip start.
**Warning signs:** Cluster appears to restart unnecessarily.

### Pitfall 4: Ingress Addon Namespace
**What goes wrong:** Looking for ingress pods in `kube-system` but they're actually in `ingress-nginx`.
**Why it happens:** Minikube's ingress addon creates its own namespace.
**How to avoid:** Use `ingress-nginx` namespace for ingress controller pod checks.
**Warning signs:** `kubectl wait` times out looking for pods in wrong namespace.

### Pitfall 5: Script Path Assumptions
**What goes wrong:** Script uses relative paths like `k8s/namespaces.yaml` but is executed from a different working directory.
**Why it happens:** User runs `bash scripts/setup-minikube.sh` from project root, but paths are relative to script location.
**How to avoid:** Use `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and derive paths from there, or document that scripts must be run from project root.
**Warning signs:** "file not found" errors on kubectl apply.

## Code Examples

### setup-minikube.sh Full Pattern
```bash
#!/usr/bin/env bash
set -euo pipefail

# Resolve project root relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Prerequisite checks ---
check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "ERROR: '$1' is required but not found on PATH" >&2
    exit 1
  fi
}
check_command minikube
check_command kubectl
check_command docker

# --- Idempotent cluster start ---
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
  echo "Minikube started"
fi

# --- Wait for node readiness ---
echo "Waiting for Kubernetes node to be Ready..."
kubectl wait --for=condition=Ready node --all --timeout=120s
echo "Node is Ready"

# --- Ensure addons (idempotent) ---
for addon in ingress metrics-server dashboard; do
  echo "Ensuring addon enabled: $addon"
  minikube addons enable "$addon"
done

# --- Apply namespaces ---
echo "Applying namespace manifests..."
kubectl apply -f "$PROJECT_ROOT/k8s/namespaces.yaml"
echo "Namespaces applied"

# --- Verify ---
echo "Verifying namespaces..."
kubectl get namespaces
echo ""
echo "Cluster ready"
```

### deploy-all.sh Full Pattern
```bash
#!/usr/bin/env bash
set -euo pipefail

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

# --- Phase 4: Storage (PostgreSQL + TimescaleDB) ---
# echo "[Phase 4] Deploying PostgreSQL..."
# kubectl apply -f "$PROJECT_ROOT/k8s/storage/"

# --- Phase 5: Kafka (Strimzi Operator) ---
# echo "[Phase 5] Deploying Strimzi operator..."
# kubectl apply -f "$PROJECT_ROOT/k8s/kafka/"

# ... (sections for phases 6-30 in dependency order)

echo "=== Deployment complete ==="
```

### Discretion Recommendations

**Timeout and retry interval:** 120 seconds timeout for `kubectl wait` is generous for a local minikube cluster. Node readiness typically takes 15-30 seconds. Addon pods can take up to 60 seconds. 120s provides comfortable margin.

**Echo formatting:** Plain echo statements with descriptive text. No colour codes -- keeps scripts simple and compatible with CI environments where ANSI codes may not render. Use `===` or `---` section separators for visual clarity.

**Shared function vs inline:** Use a `check_command` function in setup-minikube.sh (which checks 3 commands). In deploy-all.sh, inline the single kubectl check since there's only one binary to validate plus the minikube status check.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `minikube start` then `minikube addons enable X` separately | `minikube start --addons=X,Y,Z` | Available since minikube ~v1.10 | Single command setup, but still need post-start enable for idempotency |
| Manual polling with `kubectl get nodes` | `kubectl wait --for=condition=Ready` | kubectl 1.11+ | Cleaner, built-in timeout handling |
| `which` for command existence | `command -v` | POSIX standard | More reliable, works in strict bash mode |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | bash script execution + kubectl verification |
| Config file | none -- shell scripts are self-contained |
| Quick run command | `bash stock-prediction-platform/scripts/setup-minikube.sh && kubectl get ns` |
| Full suite command | `bash stock-prediction-platform/scripts/setup-minikube.sh && bash stock-prediction-platform/scripts/deploy-all.sh && kubectl get ns` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | Minikube running with 5 namespaces | smoke | `minikube status && kubectl get ns ingestion processing storage ml frontend` | N/A (CLI) |
| INFRA-02 | Namespace YAML manifests exist and are valid | unit | `kubectl apply --dry-run=client -f stock-prediction-platform/k8s/namespaces.yaml` | Already exists |
| INFRA-04 | setup-minikube.sh bootstraps cluster | smoke | `bash stock-prediction-platform/scripts/setup-minikube.sh` | Stub exists |
| INFRA-05 | deploy-all.sh orchestrates deployment | smoke | `bash stock-prediction-platform/scripts/deploy-all.sh` | Stub exists |

### Sampling Rate
- **Per task commit:** Run `bash stock-prediction-platform/scripts/setup-minikube.sh` and verify exit code 0
- **Per wave merge:** Full suite: setup + deploy + verify all 5 namespaces exist
- **Phase gate:** `minikube status` shows Running AND `kubectl get ns` shows all 5 namespaces

### Wave 0 Gaps
None -- no test framework setup needed. Validation is via direct script execution and kubectl commands. The existing stub files will be replaced with implementations.

## Open Questions

1. **Dashboard addon pod readiness label**
   - What we know: Dashboard deploys to `kubernetes-dashboard` namespace
   - What's unclear: Exact label selector may vary by minikube version
   - Recommendation: Verify addon is enabled via `minikube addons list` rather than waiting for specific dashboard pods, since dashboard is not critical to cluster operation

2. **deploy-all.sh granularity of future phase stubs**
   - What we know: Need stubs for phases 3-30 in dependency order
   - What's unclear: Exact manifest paths that will be created in each future phase
   - Recommendation: Use placeholder paths based on the roadmap (e.g., `k8s/storage/`, `k8s/kafka/`) and update as phases land

## Sources

### Primary (HIGH confidence)
- Local system: minikube v1.35.0 CLI help and behavior verified directly
- Local system: kubectl v1.30.14 `wait` command verified directly
- Local system: Docker 29.1.5 confirmed installed
- Existing code: `stock-prediction-platform/k8s/namespaces.yaml` reviewed -- 5 namespaces with correct labels

### Secondary (MEDIUM confidence)
- minikube `--addons` flag behavior at startup -- verified via `minikube start --help`
- `minikube status --format='{{.Host}}'` output -- verified locally returns "Running"
- `kubectl wait --for=condition=Ready node --all` -- verified locally

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools installed and verified locally
- Architecture: HIGH - shell scripts with well-known CLI patterns
- Pitfalls: HIGH - verified memory flag behavior and addon namespaces locally

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain, tools don't change frequently)
