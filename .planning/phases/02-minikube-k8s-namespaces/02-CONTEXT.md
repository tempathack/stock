# Phase 2: Minikube & K8s Namespaces - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Bootstrap a local Minikube Kubernetes cluster with the docker driver, apply all 5 namespace manifests, and deliver two executable shell scripts: `setup-minikube.sh` (cluster initialisation and readiness verification) and `deploy-all.sh` (ordered manifest orchestration with full future-phase section stubs). No services, workloads, or Helm charts are deployed in this phase.

</domain>

<decisions>
## Implementation Decisions

### Minikube Driver & Resources
- Driver: `docker` — most portable, no VM overhead, requires Docker Engine running
- CPU: 6 CPUs
- Memory: 12GB RAM
- Addons to enable at startup: `ingress`, `metrics-server`, `dashboard`
- After start: poll `kubectl get nodes` until status is `Ready`, then confirm all enabled addons are running; fail if not ready within timeout

### deploy-all.sh Scope & Ordering
- Write the complete ordered script now with all future sections present but commented out — uncomment per-phase as manifests land
- Explicit dependency order: Namespaces → Storage (PVC/DB) → Kafka → Ingestion → Processing → ML → Frontend
- Each section clearly labelled with the phase that activates it

### Script Error Handling & Idempotency
- Both scripts use `set -euo pipefail` — fail fast on any command failure
- `setup-minikube.sh` is idempotent: check `minikube status` first; if cluster is already `Running`, skip start and proceed directly to namespace apply
- Verbosity: step-by-step `echo` statements for each major action (e.g. "Starting Minikube...", "Enabling addons...", "Applying namespaces...", "Cluster ready ✓") — no silent running

### Prerequisite Checks
- `setup-minikube.sh`: validate `minikube`, `kubectl`, and `docker` are on `$PATH` before doing anything; print clear error and exit if any are missing
- `deploy-all.sh`: validate `kubectl` is available and `minikube status` shows running before applying any manifests

### Claude's Discretion
- Exact readiness poll timeout value and retry interval
- Specific echo formatting / colour codes (if any)
- Whether to use a shared `check_prereqs` function or inline checks

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Infrastructure scripts
- `stock-prediction-platform/scripts/setup-minikube.sh` — stub to implement (cluster bootstrap)
- `stock-prediction-platform/scripts/deploy-all.sh` — stub to implement (manifest orchestration)

### Kubernetes manifests
- `stock-prediction-platform/k8s/namespaces.yaml` — 5 namespace definitions already written (apply this in setup and deploy scripts)

### Requirements
- `.planning/REQUIREMENTS.md` §INFRA-01, INFRA-02, INFRA-04, INFRA-05 — exact acceptance criteria for this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `stock-prediction-platform/k8s/namespaces.yaml` — already defines all 5 namespaces with `app.kubernetes.io/part-of: stock-prediction-platform` labels; ready to apply directly, no edits needed

### Established Patterns
- Phase 1 used `set -euo pipefail` is implied by project-wide "production-ready, no shortcuts" constraint from PROJECT.md
- Structured JSON logging is a project-wide requirement (structlog utility already implemented in Phase 1) — not applicable to shell scripts directly, but echo verbosity follows the same philosophy of visible progress

### Integration Points
- `setup-minikube.sh` is the entry point for all subsequent phases — every later phase assumes the cluster is Running and namespaces exist
- `deploy-all.sh` will be extended by phases 3-30 as each adds its own k8s manifests; the stub sections act as the extension contract

</code_context>

<specifics>
## Specific Ideas

- No specific references — open to standard Minikube CLI approach (`minikube start --driver=docker --cpus=6 --memory=12288 --addons=...`)
- deploy-all.sh section stubs should include the phase number in comments so it's obvious which phase activates each block

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-minikube-k8s-namespaces*
*Context gathered: 2026-03-18*
