---
phase: 65-argo-cd-gitops-deployment-pipeline
plan: 01
subsystem: infra
tags: [argocd, gitops, kubernetes, app-of-apps, k8s, deployment-pipeline]

# Dependency graph
requires:
  - phase: 64-timescaledb-olap
    provides: All k8s manifests present under stock-prediction-platform/k8s/ — argocd Applications point to these paths
  - phase: 2-minikube-k8s-namespaces
    provides: Minikube cluster and namespaces exist for Argo CD installation
provides:
  - Argo CD v3.3.6 installed in argocd namespace with all 5 deployments ready
  - root-app Application CR using app-of-apps pattern watching k8s/argocd/
  - 7 child Application CRs covering ingestion, processing, storage, kafka, ml, frontend, monitoring
  - All Applications configured with automated sync, prune=true, selfHeal=true
  - GitOps reconciliation — future manifest changes deploy via git push not kubectl apply
affects:
  - phase-66-feast
  - phase-67-flink
  - phase-68-e2e-integration
  - phase-69-frontend-analytics

# Tech tracking
tech-stack:
  added: [argocd v3.3.6, argoproj.io/v1alpha1 Application CRD]
  patterns: [app-of-apps pattern, sync-wave ordering (wave 1 = infra, wave 2 = workloads), directory.recurse=false for operator-managed subdirs, ignoreDifferences for Secret /data]

key-files:
  created:
    - stock-prediction-platform/k8s/argocd/root-app.yaml
    - stock-prediction-platform/k8s/argocd/app-ingestion.yaml
    - stock-prediction-platform/k8s/argocd/app-processing.yaml
    - stock-prediction-platform/k8s/argocd/app-storage.yaml
    - stock-prediction-platform/k8s/argocd/app-kafka.yaml
    - stock-prediction-platform/k8s/argocd/app-ml.yaml
    - stock-prediction-platform/k8s/argocd/app-frontend.yaml
    - stock-prediction-platform/k8s/argocd/app-monitoring.yaml
  modified:
    - stock-prediction-platform/scripts/deploy-all.sh

key-decisions:
  - "argocd CLI installed to ~/.local/bin/ instead of /usr/local/bin/ (sudo not available in non-interactive shell)"
  - "Files pushed to origin/master before root-app sync — Argo CD reads from remote git, not local filesystem"
  - "app-kafka destination namespace is storage (not kafka) — Strimzi CRs deploy into storage namespace"
  - "app-ml uses directory.recurse=false to exclude kserve/ and kubeflow/ subdirs from Argo CD reconciliation (operator-managed)"
  - "ignoreDifferences on Secret /data added to storage, ingestion, processing, ml apps to prevent drift loops on externally-managed secrets"

patterns-established:
  - "App-of-apps: root-app watches k8s/argocd/ and creates child Application CRs automatically"
  - "Sync waves: wave 1 = storage/kafka (infra), wave 2 = ingestion/processing/ml/frontend/monitoring (workloads)"
  - "All child apps: automated sync + prune + selfHeal + retry (limit: 5, exponential backoff up to 3m)"

requirements-completed: [GITOPS-01, GITOPS-02, GITOPS-03]

# Metrics
duration: 8min
completed: 2026-03-29
---

# Phase 65 Plan 01: Argo CD GitOps Bootstrap Summary

**Argo CD v3.3.6 installed in argocd namespace with app-of-apps pattern — root-app watches k8s/argocd/ and manages 7 child Application CRs covering all platform namespaces, all Synced with automated prune+selfHeal**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-29T21:34:08Z
- **Completed:** 2026-03-29T21:42:51Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Created k8s/argocd/ directory with root-app.yaml + 7 child Application CRs using app-of-apps pattern
- Installed Argo CD v3.3.6 (client + server both v3.3.6) with all components ready (argocd-server, argocd-repo-server, argocd-application-controller, argocd-dex-server, argocd-notifications-controller)
- Applied root-app, triggered sync — all 8 Application CRs exist in argocd namespace and show Synced status
- Updated deploy-all.sh with Phase 65 bootstrap section (conditional install, login, repo register, app sync) and Argo CD UI port-forward on 8079

## Task Commits

Each task was committed atomically:

1. **Task 1: Create k8s/argocd/ with root Application and 7 child Application CRs** - `1307156` (feat)
2. **Task 2: Install Argo CD v3.3.6, register git repo, bootstrap root app** - `6bd42cc` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `stock-prediction-platform/k8s/argocd/root-app.yaml` - Bootstrap Application CR watching k8s/argocd/ path, creates all child apps
- `stock-prediction-platform/k8s/argocd/app-ingestion.yaml` - Child Application for ingestion namespace, sync-wave 2
- `stock-prediction-platform/k8s/argocd/app-processing.yaml` - Child Application for processing namespace, sync-wave 2
- `stock-prediction-platform/k8s/argocd/app-storage.yaml` - Child Application for storage namespace, sync-wave 1
- `stock-prediction-platform/k8s/argocd/app-kafka.yaml` - Child Application for k8s/kafka/ deploying into storage namespace, sync-wave 1
- `stock-prediction-platform/k8s/argocd/app-ml.yaml` - Child Application for ml namespace with directory.recurse=false, sync-wave 2
- `stock-prediction-platform/k8s/argocd/app-frontend.yaml` - Child Application for frontend namespace, sync-wave 2
- `stock-prediction-platform/k8s/argocd/app-monitoring.yaml` - Child Application for monitoring namespace, sync-wave 2
- `stock-prediction-platform/scripts/deploy-all.sh` - Phase 65 bootstrap section + argocd-server port-forward + Argo CD UI link

## Decisions Made

- **argocd CLI installed to ~/.local/bin/**: sudo not available in non-interactive bash; used user-local bin path instead of /usr/local/bin/
- **Files pushed to origin/master before root-app sync**: Argo CD reads manifests from remote git (targetRevision: HEAD on master), not local filesystem — required pushing to make k8s/argocd/ path visible to Argo CD
- **app-kafka destination namespace is storage**: Strimzi operator and Kafka CRs must live in storage namespace; kafka/ manifests path but destination diverges
- **app-ml uses directory.recurse=false**: kserve/ and kubeflow/ subdirs contain operator-install manifests with non-standard apply patterns (--server-side, URL-based sources) that must not be applied by Argo CD
- **ignoreDifferences on Secret /data**: Prevents Argo CD from reporting drift on externally-managed secrets (minio-secrets, stock-platform-secrets injected by deploy-all.sh)

## Deviations from Plan

None - plan executed exactly as written. One operational note: argocd CLI installation used ~/.local/bin/ instead of /usr/local/bin/ (sudo unavailable in non-interactive shell), which required adding ~/.local/bin/ to PATH during bootstrap. The deploy-all.sh bootstrap section still uses `sudo install` as specified (correct for interactive shell execution).

## Issues Encountered

- **argocd CLI sudo install**: sudo requires interactive terminal; worked around by installing to ~/.local/bin/ for the live bootstrap session. The deploy-all.sh block correctly uses `sudo install` for future runs (interactive terminal available).
- **root-app sync initially failed with "app path does not exist"**: Argo CD reads from remote git; the k8s/argocd/ files needed to be pushed to origin/master before the sync would work. Pushed local commit and re-ran sync successfully.

## User Setup Required

None - no external service configuration required beyond what deploy-all.sh handles.

To register the GitHub repo with a PAT (if repo becomes private):
```bash
argocd repo add https://github.com/tempathack/stock.git --username tempathack --password <PAT>
```

## Next Phase Readiness

- Argo CD operational — future manifest changes deploy via `git push origin master` (no kubectl apply needed)
- Argo CD UI available at https://localhost:8079 after running deploy-all.sh (admin password in /tmp/argocd-pwd.txt)
- Phase 66 (Feast) and Phase 67 (Flink) can proceed — their k8s/ manifests will be auto-synced by Argo CD once added to k8s/feast/ and k8s/flink/ directories and pushed to master

---
*Phase: 65-argo-cd-gitops-deployment-pipeline*
*Completed: 2026-03-29*

## Self-Check: PASSED

- FOUND: stock-prediction-platform/k8s/argocd/root-app.yaml
- FOUND: stock-prediction-platform/k8s/argocd/app-ingestion.yaml
- FOUND: stock-prediction-platform/k8s/argocd/app-kafka.yaml
- FOUND: stock-prediction-platform/k8s/argocd/app-ml.yaml
- FOUND: .planning/phases/65-argo-cd-gitops-deployment-pipeline/65-01-SUMMARY.md
- FOUND commit: 1307156 (Task 1 — argocd Application CRs)
- FOUND commit: 6bd42cc (Task 2 — Argo CD install + deploy-all.sh)
