---
phase: 65
slug: argo-cd-gitops-deployment-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 65 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | kubectl / argocd CLI / bash scripts |
| **Config file** | none — infra validation via CLI commands |
| **Quick run command** | `kubectl get applications -n argocd` |
| **Full suite command** | `argocd app list && argocd app sync --all --dry-run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `kubectl get applications -n argocd`
- **After every plan wave:** Run `argocd app list && argocd app sync --all --dry-run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 65-01-01 | 01 | 1 | GITOPS-01 | infra | `kubectl get namespace argocd` | ✅ | ⬜ pending |
| 65-01-02 | 01 | 1 | GITOPS-01 | infra | `kubectl get pods -n argocd` | ✅ | ⬜ pending |
| 65-01-03 | 01 | 1 | GITOPS-02 | infra | `kubectl get application root-app -n argocd` | ✅ W0 | ⬜ pending |
| 65-01-04 | 01 | 1 | GITOPS-02 | infra | `kubectl get applications -n argocd \| grep -c Application` | ✅ W0 | ⬜ pending |
| 65-02-01 | 02 | 2 | GITOPS-03 | infra | `kubectl get application -n argocd -o json \| grep -c 'selfHeal'` | ✅ W0 | ⬜ pending |
| 65-02-02 | 02 | 2 | GITOPS-04 | infra | `kubectl get cm argocd-cm -n argocd -o yaml \| grep -c 'strimzi'` | ✅ W0 | ⬜ pending |
| 65-02-03 | 02 | 2 | GITOPS-05 | manual | `cat deploy-all.sh \| grep argocd` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements (kubectl and argocd CLI available post-install).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Argo CD UI accessible at localhost:8080 via port-forward | GITOPS-01 | Requires live cluster port-forward | `kubectl port-forward svc/argocd-server -n argocd 8080:443` then browse |
| Git push triggers automatic sync | GITOPS-03 | Requires live cluster + git remote | Push a manifest change and watch `argocd app get <app>` status transition |
| Custom health checks show Healthy for Kafka/InferenceService | GITOPS-04 | Requires live CRD instances | `argocd app get ingestion` shows Kafka resource as Healthy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
