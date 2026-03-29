# Phase 65: Argo CD — GitOps Deployment Pipeline - Research

**Researched:** 2026-03-29
**Domain:** Argo CD GitOps, Kubernetes declarative deployment, app-of-apps pattern, custom CRD health checks
**Confidence:** HIGH

---

## Summary

Argo CD v3.3.6 (latest stable as of 2026-03-27) is a mature GitOps tool that continuously reconciles a Kubernetes cluster to a git repository state. The core workflow is: commit manifests to git → Argo CD detects the diff → applies changes automatically. For this project the "app-of-apps" pattern is the correct approach: one root `Application` CR points to a directory in git that contains child `Application` CRs (one per K8s namespace). All child apps get `syncPolicy.automated` with `prune: true` and `selfHeal: true`.

The project already has an existing K8s manifest tree under `stock-prediction-platform/k8s/` with subdirectories for every namespace. This structure maps directly to the app-of-apps pattern — each subdirectory becomes its own child Argo CD Application. The git remote is `https://github.com/tempathack/stock.git`, which Argo CD can register as a public or authenticated HTTPS repository with no special networking changes needed.

Two custom Lua health checks must be written: one for `kafka.strimzi.io/Kafka` (status.conditions Ready=True) and one for `serving.kserve.io/InferenceService` (same Ready condition pattern). Both follow the standard Lua script pattern already used by Argo CD's built-in resource customizations. The `deploy-all.sh` script is updated to a two-mode operation: initial bootstrap via raw `kubectl apply -n argocd` then subsequent deploys via `argocd app sync --all`.

**Primary recommendation:** Install Argo CD v3.3.6 via `kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.3.6/manifests/install.yaml`, create one root `Application` pointing to `k8s/argocd/` in git, and define seven child `Application` CRs (one per existing namespace). All management after bootstrap goes through Argo CD, not `kubectl apply`.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GITOPS-01 | Argo CD installed in `argocd` namespace; `argocd` CLI accessible via port-forward at localhost:8080 | Standard kubectl apply + port-forward pattern; v3.3.6 install.yaml URL documented |
| GITOPS-02 | Root `Application` (app-of-apps) in `argocd` namespace pointing to `k8s/` directory | App-of-apps YAML pattern documented with repoURL + path fields |
| GITOPS-03 | Child `Application` CRs for: ingestion, processing, storage, ml, frontend, monitoring, argocd namespaces | Each maps to existing k8s/ subdirectory; child Application YAML pattern documented |
| GITOPS-04 | Sync policy: automated with `prune: true` and `selfHeal: true` on all apps | syncPolicy.automated YAML schema documented with exact field names |
| GITOPS-05 | Custom health checks for Strimzi `Kafka` CR and KServe `InferenceService` CR | Lua script pattern for Ready condition documented; argocd-cm ConfigMap key format documented |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Argo CD | v3.3.6 | GitOps CD controller + API server | Current stable; CNCF graduated; 4 releases/year cadence |
| `argocd` CLI | v3.3.6 (matches server) | Bootstrap commands, `argocd app sync`, login | Ships with Argo CD; must match server version |
| Lua 5.3 (embedded) | built-in | Custom health checks for CRDs | Argo CD embeds gopher-lua; no separate install |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ApplicationSet controller | built-in (v3.x) | Generate many Applications from a template + generator | Optional — alternative to hand-written child Application CRs when app count is large |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw `Application` CRs (app-of-apps) | `ApplicationSet` with List generator | ApplicationSet is more DRY for 10+ apps; for 7 child apps with different directory structures, explicit Application CRs are clearer and easier to debug |
| `kubectl apply -f install.yaml` | Helm chart (`argo/argo-cd`) | Helm gives easier upgrades but adds Helm dependency; raw YAML is simpler for Minikube dev context |

**Installation:**
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.3.6/manifests/install.yaml
# Install CLI (Linux)
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/download/v3.3.6/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
```

---

## Architecture Patterns

### Recommended Project Structure for Argo CD

```
stock-prediction-platform/k8s/
├── argocd/                     # NEW — child Application CRs managed by root app
│   ├── app-ingestion.yaml      # Child Application → k8s/ingestion/
│   ├── app-processing.yaml     # Child Application → k8s/processing/
│   ├── app-storage.yaml        # Child Application → k8s/storage/
│   ├── app-ml.yaml             # Child Application → k8s/ml/
│   ├── app-frontend.yaml       # Child Application → k8s/frontend/
│   ├── app-monitoring.yaml     # Child Application → k8s/monitoring/
│   └── argocd-cm-health.yaml   # ConfigMap with custom health check Lua scripts
├── ingestion/                  # EXISTING — unchanged manifest files
├── processing/                 # EXISTING
├── storage/                    # EXISTING
├── ml/                         # EXISTING
├── frontend/                   # EXISTING
├── monitoring/                 # EXISTING
└── namespaces.yaml             # EXISTING
```

The root `Application` lives in the `argocd` namespace but is created via `kubectl apply` during initial bootstrap. After that, it self-manages by watching `k8s/argocd/` in git.

### Pattern 1: Root Application (App-of-Apps)

**What:** A single Application CR bootstrapped manually that watches the `k8s/argocd/` directory. When Argo CD syncs this app, it creates all child Application CRs.
**When to use:** Single cluster, multiple logically-separated namespaces.

```yaml
# Source: https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/tempathack/stock.git
    targetRevision: HEAD
    path: stock-prediction-platform/k8s/argocd
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### Pattern 2: Child Application CR

**What:** One Application per namespace, all placed in `k8s/argocd/` directory (managed by root app).
**When to use:** Each child points to an existing `k8s/<namespace>/` manifest directory.

```yaml
# Source: https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ingestion
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/tempathack/stock.git
    targetRevision: HEAD
    path: stock-prediction-platform/k8s/ingestion
  destination:
    server: https://kubernetes.default.svc
    namespace: ingestion
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

Repeat this pattern for: processing, storage, ml, frontend, monitoring.

### Pattern 3: Bootstrap Sequence in `deploy-all.sh`

**What:** Two-mode deploy script. First run: full bootstrap. Subsequent runs: `argocd app sync --all`.

```bash
# Bootstrap (run once)
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.3.6/manifests/install.yaml
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=120s

# Get initial admin password
ARGOCD_PWD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)

# Login (requires port-forward running in background)
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
sleep 3
argocd login localhost:8080 --username admin --password "$ARGOCD_PWD" --insecure

# Apply root app (bootstraps child apps)
kubectl apply -n argocd -f "$PROJECT_ROOT/k8s/argocd/root-app.yaml"

# Sync all
argocd app sync root-app
argocd app sync --all
```

### Pattern 4: Custom Health Check Lua Scripts (argocd-cm)

**What:** Extend `argocd-cm` ConfigMap to add Lua health checks for Strimzi `Kafka` and KServe `InferenceService` CRDs.
**When to use:** When Argo CD would otherwise show CRs as "Unknown" health status.

```yaml
# Source: https://oneuptime.com/blog/post/2026-02-26-argocd-health-checks-crds/view
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-cm
    app.kubernetes.io/part-of: argocd
data:
  resource.customizations.health.kafka.strimzi.io_Kafka: |
    hs = {}
    if obj.status == nil or obj.status.conditions == nil then
      hs.status = "Progressing"
      hs.message = "Kafka cluster initializing"
      return hs
    end
    for i, condition in ipairs(obj.status.conditions) do
      if condition.type == "Ready" then
        if condition.status == "True" then
          hs.status = "Healthy"
          hs.message = "Kafka cluster is ready"
        else
          hs.status = "Degraded"
          hs.message = condition.message or "Kafka cluster is not ready"
        end
        return hs
      end
      if condition.type == "NotReady" and condition.status == "True" then
        hs.status = "Progressing"
        hs.message = condition.message or "Kafka cluster not yet ready"
        return hs
      end
    end
    hs.status = "Progressing"
    hs.message = "Waiting for Ready condition"
    return hs

  resource.customizations.health.serving.kserve.io_InferenceService: |
    hs = {}
    if obj.status == nil or obj.status.conditions == nil then
      hs.status = "Progressing"
      hs.message = "InferenceService initializing"
      return hs
    end
    for i, condition in ipairs(obj.status.conditions) do
      if condition.type == "Ready" then
        if condition.status == "True" then
          hs.status = "Healthy"
          hs.message = "InferenceService is ready"
        elseif condition.status == "False" then
          hs.status = "Degraded"
          hs.message = condition.message or "InferenceService is not ready"
        else
          hs.status = "Progressing"
          hs.message = "InferenceService status unknown"
        end
        return hs
      end
    end
    hs.status = "Progressing"
    hs.message = "Waiting for Ready condition"
    return hs
```

**Key**: ConfigMap keys use the format `resource.customizations.health.<api-group>_<Kind>` (underscore between group and Kind, no `/`).

**KServe API group**: `serving.kserve.io` (verify by running `kubectl api-resources | grep kserve` on cluster).

**Strimzi API group**: `kafka.strimzi.io` (confirmed from Argo CD upstream Lua files at `resource_customizations/kafka.strimzi.io/KafkaConnect/health.lua`).

### Anti-Patterns to Avoid

- **Pointing child Application to a directory containing other Application CRs:** The root app should exclusively point to the `k8s/argocd/` directory (which contains child Application CRs only). Child apps point to workload manifests.
- **Using `kubectl apply` for ongoing deploys:** After bootstrap, all changes must go through git. Direct `kubectl apply` will be reverted by selfHeal within 5 seconds.
- **Storing secrets in the root git repo:** All K8s Secrets should use `secrets.yaml.example` pattern or External Secrets Operator. The existing `secrets.yaml` pattern (committing actual secrets) is a risk if this is a private repo — document this.
- **Adding `argocd` namespace Applications to argocd self-management without care:** Managing argocd's own `argocd-cm` via Argo CD is valid but requires the app to be set up before the health check CM is synced. Use a sync wave (`argocd.argoproj.io/sync-wave: "0"`) to ensure argocd-cm is applied early.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Health polling for CRD readiness | Custom bash polling loops | Argo CD built-in + Lua health checks | Argo CD handles requeue, backoff, and UI display natively |
| Diff detection between git and cluster | Manual `kubectl diff` | Argo CD sync status | Argo CD tracks full resource tree with 3-way merge diff |
| Rollback on deploy failure | Manual `git revert` + `kubectl apply` | Argo CD automated sync + retry with backoff | `retry.limit` + backoff handles transient failures; git is the rollback mechanism |
| Multi-namespace deploy ordering | Complex bash orchestration in deploy-all.sh | Sync waves (`argocd.argoproj.io/sync-wave` annotations) | Declarative ordering with built-in sequencing |

**Key insight:** The entire `kubectl apply` loop in `deploy-all.sh` (phases 2–50+) is replaced by one `kubectl apply -n argocd -f root-app.yaml` after Argo CD is installed. Argo CD then manages all subsequent reconciliation.

---

## Common Pitfalls

### Pitfall 1: Port-Forward Not Running When argocd CLI Commands Execute
**What goes wrong:** `argocd login` or `argocd app sync` fail with "connection refused".
**Why it happens:** Argo CD server is not exposed via LoadBalancer or NodePort in Minikube; must use port-forward.
**How to avoid:** In `deploy-all.sh`, start port-forward in background (`kubectl port-forward svc/argocd-server -n argocd 8080:443 &`), sleep 2-3 seconds for it to establish, then run argocd CLI commands. Kill the background port-forward at script end.
**Warning signs:** `dial tcp 127.0.0.1:8080: connect: connection refused`

### Pitfall 2: Child Application Paths Are Relative to Repo Root
**What goes wrong:** Argo CD cannot find manifests; Application shows "ComparisonError".
**Why it happens:** The `spec.source.path` is relative to the repository root, not to any subdirectory. This project has manifests at `stock-prediction-platform/k8s/ingestion/` — the full sub-path from repo root must be used.
**How to avoid:** Use `path: stock-prediction-platform/k8s/ingestion` (not `k8s/ingestion`).
**Warning signs:** `rpc error: code = Unknown desc = repository ... not found` or empty sync result.

### Pitfall 3: Secrets in Git Are Visible to Argo CD Server
**What goes wrong:** Argo CD shows and logs Secret values when syncing resources.
**Why it happens:** Argo CD reads all manifests including Secrets from git. The existing `secrets.yaml` files (which should NOT be committed) would be synced to cluster and visible in Argo CD UI.
**How to avoid:** Ensure `secrets.yaml` is in `.gitignore`. Use `secrets.yaml.example` pattern. For Phase 65 scope, rely on the pre-existing manually-applied secrets; the Argo CD apps can have `ignoreDifferences` for Secret resources to avoid pruning manually-managed secrets.
**Warning signs:** `argocd app diff` shows Secret values; Argo CD UI displays secret data.

### Pitfall 4: Strimzi and KServe CRDs Unknown Health Without Custom Checks
**What goes wrong:** Argo CD shows `kafka.strimzi.io/Kafka` and `serving.kserve.io/InferenceService` resources as "Unknown" health status, preventing the Application from reaching "Healthy" state.
**Why it happens:** Argo CD has no built-in health checks for these CRDs. It knows about common K8s resources (Deployment, StatefulSet) but not operator CRDs.
**How to avoid:** Apply the `argocd-cm` ConfigMap with Lua health check scripts BEFORE or at the same time as Argo CD installation. Use a sync wave annotation on the argocd-cm resource.
**Warning signs:** Argo CD UI shows Application as `Progressing` indefinitely even though pods are running.

### Pitfall 5: `prune: true` Deletes Resources Not Yet in Git
**What goes wrong:** Resources applied manually (e.g., CRDs installed by Strimzi operator, KServe CRDs) get pruned by Argo CD.
**Why it happens:** Resources in the cluster that have no corresponding manifest in the git path are pruned.
**How to avoid:** For the `storage` app (which contains Strimzi CRs), ensure all necessary YAML files are tracked in git. Operator-installed CRDs are typically in different namespaces (e.g., `kube-system`) and are not in the Application's destination namespace so are not pruned. If needed, use `syncOptions: ["Prune=false"]` on specific problematic apps.
**Warning signs:** Resources disappear after Argo CD sync; `argocd app diff` shows resources only in cluster.

### Pitfall 6: App-of-Apps Self-Reference Circular Dependency
**What goes wrong:** Including the Argo CD namespace's own Application CRs inside the same Argo CD namespace app causes confusion.
**Why it happens:** The root app manages `k8s/argocd/` which contains child Application CRs. If a child Application also points to `k8s/argocd/` you get recursion.
**How to avoid:** The `k8s/argocd/` directory must ONLY contain child `Application` CRs and the `argocd-cm` ConfigMap. Child apps must point to workload directories (`k8s/ingestion/`, etc.), not back to `k8s/argocd/`.

---

## Code Examples

### Full Child Application YAML (Storage Namespace)
```yaml
# Source: https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: storage
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
  annotations:
    argocd.argoproj.io/sync-wave: "1"   # storage before ingestion
spec:
  project: default
  source:
    repoURL: https://github.com/tempathack/stock.git
    targetRevision: HEAD
    path: stock-prediction-platform/k8s/storage
  destination:
    server: https://kubernetes.default.svc
    namespace: storage
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true   # prevents annotation size limits on large resources
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Verify argocd-cm Health Check Key Format
```bash
# Verify the API group of Strimzi Kafka CR
kubectl api-resources | grep -i kafka
# Expected: kafka.strimzi.io / Kind=Kafka

# Verify the API group of KServe InferenceService CR
kubectl api-resources | grep -i inferenceservice
# Expected: serving.kserve.io / Kind=InferenceService

# Test Lua health check offline (requires argocd CLI)
argocd admin settings resource-overrides health kafka.strimzi.io/Kafka \
  --argocd-cm-path ./k8s/argocd/argocd-cm-health.yaml \
  --yaml ./k8s/storage/kafka.yaml
```

### ignoreDifferences for Manually-Managed Secrets
```yaml
# Add to each Application that has a manually-managed Secret
spec:
  ignoreDifferences:
    - group: ""
      kind: Secret
      jsonPointers:
        - /data
```

### `argocd app sync --all` in deploy-all.sh
```bash
# Pattern for deploy-all.sh "subsequent runs" mode
ARGOCD_SERVER="localhost:8080"
kubectl port-forward svc/argocd-server -n argocd 8080:443 &>/dev/null &
PF_PID=$!
sleep 3

ARGOCD_PWD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")

argocd login "$ARGOCD_SERVER" --username admin \
  --password "$ARGOCD_PWD" --insecure --grpc-web

argocd app sync root-app --timeout 300
argocd app wait root-app --health --timeout 120
argocd app sync --all --timeout 300

kill $PF_PID 2>/dev/null || true
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `kubectl apply -f` loops in shell scripts | Argo CD declarative Application CRs | 2018-onwards (mature since 2021) | Full audit trail, drift detection, UI |
| Health polling via bash `kubectl wait` | Argo CD health checks (built-in + Lua) | Argo CD 1.x | Unified health model across all resource types |
| ApplicationSet was separate controller | ApplicationSet merged into Argo CD core | Argo CD 2.5 (2022) | No separate install needed |
| `argocd-initial-admin-secret` manual decode | `argocd admin initial-password` command | Argo CD 2.7 | Cleaner CLI UX |

**Deprecated/outdated:**
- **Argo CD 2.x**: Active but EOL approaching; v3.x (current) is the maintained line.
- **`argocd-util` commands**: Replaced by `argocd admin` subcommands in v2.x+.

---

## Open Questions

1. **Should `secrets.yaml` files be excluded from Argo CD sync scope?**
   - What we know: The project has `secrets.yaml` and `secrets.yaml.example` pattern. If actual `secrets.yaml` is committed to git (it likely is not, as it's in `.gitignore`), Argo CD will sync it.
   - What's unclear: Is `secrets.yaml` in the gitignore? If excluded from git, Argo CD will attempt to prune the Secret from the cluster (because `prune: true`).
   - Recommendation: Add `ignoreDifferences` blocks for Secrets in affected Application CRs, OR use `syncOptions: ["Prune=false"]` for Secrets, OR manage Secrets outside the Argo CD application scope via a separate bootstrap step.

2. **KServe API group name**
   - What we know: KServe uses `serving.kserve.io` for `InferenceService` resources.
   - What's unclear: Some older KServe versions used `serving.kubeflow.org`. Verify with `kubectl api-resources | grep inferenceservice` on the running cluster.
   - Recommendation: Add a runtime check in the deploy script to detect the correct API group.

3. **Git repo access from within Minikube**
   - What we know: `https://github.com/tempathack/stock.git` is a private GitHub repo. Argo CD needs credentials to clone it.
   - What's unclear: Are credentials (PAT or deploy key) available for the Minikube-hosted Argo CD to access GitHub?
   - Recommendation: Register the repo via `argocd repo add https://github.com/tempathack/stock.git --username tempathack --password <PAT>` or create a `Secret` of type `Opaque` in `argocd` namespace with `type: git` field. This is a one-time bootstrap step.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None (infrastructure validation — shell-based smoke tests) |
| Config file | none |
| Quick run command | `kubectl get applications -n argocd` |
| Full suite command | `argocd app list; argocd app wait --all --health --timeout 300` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GITOPS-01 | Argo CD server pod running in argocd namespace | smoke | `kubectl wait deploy/argocd-server -n argocd --for=condition=available --timeout=60s` | ❌ Wave 0 |
| GITOPS-02 | Root Application exists and Synced | smoke | `argocd app get root-app --output json \| jq '.status.sync.status'` | ❌ Wave 0 |
| GITOPS-03 | 7 child Application CRs exist and Healthy | smoke | `argocd app list -o json \| jq 'length'` | ❌ Wave 0 |
| GITOPS-04 | Automated sync with prune+selfHeal active | smoke | `argocd app get ingestion --output json \| jq '.spec.syncPolicy.automated'` | ❌ Wave 0 |
| GITOPS-05 | Custom health checks return Healthy for Kafka+ISVC | smoke/manual | `argocd app get storage --output json \| jq '.status.resources[] \| select(.kind=="Kafka") \| .health.status'` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `kubectl get applications -n argocd`
- **Per wave merge:** `argocd app wait --all --health --timeout 300`
- **Phase gate:** All 7 Applications show `Synced` + `Healthy` before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `scripts/validate-argocd.sh` — smoke test script covering all 5 GITOPS-* requirements
- [ ] `k8s/argocd/` directory — must exist with Application CRs before Argo CD can sync

---

## Sources

### Primary (HIGH confidence)
- GitHub argoproj/argo-cd releases — v3.3.6 confirmed as latest stable (2026-03-27)
- `https://github.com/argoproj/argo-cd/blob/master/resource_customizations/kafka.strimzi.io/KafkaConnect/health.lua` — Strimzi Lua health check pattern
- `https://oneuptime.com/blog/post/2026-02-26-argocd-health-checks-crds/view` — Full Lua health check examples and argocd-cm format

### Secondary (MEDIUM confidence)
- `https://codefresh.io/blog/how-to-structure-your-argo-cd-repositories-using-application-sets/` — App-of-apps directory structure patterns
- `https://oneuptime.com/blog/post/2026-02-09-argocd-sync-policies-pruning/view` — Sync policy YAML examples verified against official docs
- `https://cncf.io/blog/2025/10/07/managing-kubernetes-workloads-using-the-app-of-apps-pattern-in-argocd-2/` — App-of-apps best practices (2025)

### Tertiary (LOW confidence)
- Multiple blog posts on Minikube + Argo CD setup (consistent pattern across sources → MEDIUM effective confidence for install steps)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — version confirmed from GitHub releases page (v3.3.6, 2026-03-27)
- Architecture: HIGH — app-of-apps pattern is official and well-documented; fits existing k8s/ directory structure exactly
- Pitfalls: HIGH — port-forward/path/prune pitfalls observed across multiple independent sources
- Custom health checks: HIGH — Strimzi Lua pattern confirmed from upstream Argo CD source; KServe pattern adapted from same ready-condition idiom (MEDIUM for exact API group name — verify on cluster)

**Research date:** 2026-03-29
**Valid until:** 2026-04-29 (Argo CD releases quarterly; v3.3.x patch series is stable)
