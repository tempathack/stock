---
phase: 65-argo-cd-gitops-deployment-pipeline
plan: 02
subsystem: infra
tags: [argocd, gitops, kubernetes, lua, health-checks, strimzi, kserve, smoke-test, bash]

# Dependency graph
requires:
  - phase: 65-01
    provides: Argo CD v3.3.6 installed, root-app + 7 child Application CRs Synced in argocd namespace

provides:
  - argocd-cm ConfigMap patched with Lua health check for kafka.strimzi.io_Kafka (Healthy/Degraded/Progressing)
  - argocd-cm ConfigMap patched with Lua health check for serving.kserve.io_InferenceService (Healthy/Degraded/Progressing)
  - validate-argocd.sh smoke test covering all 5 GITOPS requirements (32 checks, confirmed 0 FAIL on healthy cluster)
  - argocd-cm-health.yaml tracked in k8s/argocd/ so root app manages it via GitOps

affects:
  - phase-66-feast
  - phase-67-flink
  - phase-68-e2e-integration

# Tech tracking
tech-stack:
  added: [Lua 5.3 embedded health checks in Argo CD argocd-cm]
  patterns:
    - "argocd-cm-health.yaml uses server-side apply (--server-side --force-conflicts) to merge into existing ConfigMap"
    - "ConfigMap key format: resource.customizations.health.<api-group>_<Kind> (underscore not slash between group and Kind)"
    - "sync-wave 0 on argocd-cm-health.yaml ensures health checks applied before workload resources"
    - "Lua scripts return hs table with status (Healthy/Degraded/Progressing) and message fields"
    - "Use applications.argoproj.io fully-qualified resource name to avoid ambiguity with app.k8s.io (Kubeflow)"

key-files:
  created:
    - stock-prediction-platform/k8s/argocd/argocd-cm-health.yaml
    - stock-prediction-platform/scripts/validate-argocd.sh
  modified: []

key-decisions:
  - "kubectl apply uses --server-side --force-conflicts to merge health check keys into existing argocd-cm without overwriting other managed fields"
  - "validate-argocd.sh uses applications.argoproj.io (not application) to avoid kubectl ambiguity with Kubeflow app.k8s.io CRD — both CRDs named Application in same cluster"
  - "argocd-cm-health.yaml placed in k8s/argocd/ so root app syncs it going forward — one-time apply needed immediately since Argo CD needs health checks before it can report correct status"

patterns-established:
  - "Custom CRD health check: Lua script in argocd-cm data with resource.customizations.health.<group>_<Kind> key"
  - "Smoke test pattern: bash script with check() helper function, PASS/FAIL echo, port-forward lifecycle, trap cleanup EXIT"

requirements-completed: [GITOPS-04, GITOPS-05]

# Metrics
duration: 2min
completed: 2026-03-29
---

# Phase 65 Plan 02: Argo CD Custom Health Checks and Validation Script Summary

**Lua health checks for Strimzi Kafka and KServe InferenceService added to argocd-cm; validate-argocd.sh confirms all 5 GITOPS requirements with 32 PASS, 0 FAIL**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-29T21:45:25Z
- **Completed:** 2026-03-29T21:47:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `argocd-cm-health.yaml` with Lua health scripts for `kafka.strimzi.io_Kafka` and `serving.kserve.io_InferenceService`; applied live via server-side apply — both keys confirmed in the running argocd-cm ConfigMap
- Created `validate-argocd.sh` with 32 checks covering all 5 GITOPS requirements; script passes syntax check and exits 0 with FAIL: 0 on the live cluster
- Auto-fixed kubectl API group ambiguity — two Application CRDs coexist (argoproj.io and app.k8s.io/Kubeflow); script uses `applications.argoproj.io` to ensure correct resource is queried

## Task Commits

Each task was committed atomically:

1. **Task 1: Create argocd-cm-health.yaml with Strimzi and KServe Lua health checks** - `5d5786e` (feat)
2. **Task 2: Write validate-argocd.sh smoke test covering all 5 GITOPS requirements** - `ae18080` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `stock-prediction-platform/k8s/argocd/argocd-cm-health.yaml` - ConfigMap (name: argocd-cm) with sync-wave 0; Lua scripts for Strimzi Kafka and KServe InferenceService CRD health evaluation
- `stock-prediction-platform/scripts/validate-argocd.sh` - Standalone smoke test; 32 checks across GITOPS-01 to GITOPS-05; manages port-forward lifecycle with trap cleanup; exits 0 on success

## Decisions Made

- **Server-side apply for argocd-cm merge**: `kubectl apply --server-side --force-conflicts` merges the health check keys into the existing argocd-cm without clearing other Argo CD-managed fields like `application.instanceLabelKey` — preserves existing ConfigMap state
- **Immediate live apply before GitOps cycle**: The health checks must be active before Argo CD can accurately report health; applied immediately with kubectl rather than waiting for root-app sync cycle
- **applications.argoproj.io API group in validate script**: Cluster has two Application CRDs — `argoproj.io/v1alpha1` (Argo CD) and `app.k8s.io/v1beta1` (Kubeflow). Unqualified `kubectl get application` resolves to the Kubeflow CRD causing NotFound errors for Argo CD apps. Using fully-qualified `applications.argoproj.io` avoids the ambiguity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed kubectl API group ambiguity for Application resource**
- **Found during:** Task 2 (validate-argocd.sh execution)
- **Issue:** `kubectl get application root-app -n argocd` returned `NotFound` because kubectl resolved "application" to the Kubeflow `applications.app.k8s.io` CRD (alphabetically first), not the Argo CD `applications.argoproj.io` CRD. Script produced 25 FAIL checks on the first run.
- **Fix:** Replaced all `kubectl get application <name>` and `kubectl get applications` commands in the script with `kubectl get applications.argoproj.io <name>` to force correct API group resolution.
- **Files modified:** `stock-prediction-platform/scripts/validate-argocd.sh`
- **Verification:** Re-run produced 32 PASS, 0 FAIL
- **Committed in:** `ae18080` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix essential for correctness — script would always report false failures without it. No scope creep.

## Issues Encountered

None beyond the auto-fixed kubectl API group ambiguity documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GITOPS-04 and GITOPS-05 requirements fulfilled; all 5 Phase 65 GITOPS requirements are now complete (GITOPS-01/02/03 from Plan 01)
- Kafka and InferenceService CRs now report meaningful health status (Healthy/Degraded/Progressing) instead of Unknown in Argo CD UI
- `validate-argocd.sh` can be used as a quick smoke test after any cluster change to verify Argo CD pipeline health
- Phase 66 (Feast) and Phase 67 (Flink) can proceed — their manifests will be managed by Argo CD once added to k8s/feast/ and k8s/flink/ and pushed to master

---
*Phase: 65-argo-cd-gitops-deployment-pipeline*
*Completed: 2026-03-29*

## Self-Check: PASSED

- FOUND: stock-prediction-platform/k8s/argocd/argocd-cm-health.yaml
- FOUND: stock-prediction-platform/scripts/validate-argocd.sh
- FOUND: .planning/phases/65-argo-cd-gitops-deployment-pipeline/65-02-SUMMARY.md
- FOUND commit: 5d5786e (Task 1 - argocd-cm-health.yaml)
- FOUND commit: ae18080 (Task 2 - validate-argocd.sh)
