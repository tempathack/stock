---
phase: 2
slug: minikube-k8s-namespaces
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash assertions (shell scripts only — no Python/JS test runner needed) |
| **Config file** | none |
| **Quick run command** | `minikube status && kubectl get namespaces` |
| **Full suite command** | `kubectl get namespaces && kubectl get nodes && minikube addons list \| grep -E "ingress\|metrics-server\|dashboard"` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `minikube status && kubectl get namespaces`
- **After every plan wave:** Run full suite command above
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | INFRA-04 | shell | `bash -n stock-prediction-platform/scripts/setup-minikube.sh` | ✅ | ⬜ pending |
| 2-01-02 | 01 | 1 | INFRA-04 | shell | `grep -q "set -euo pipefail" stock-prediction-platform/scripts/setup-minikube.sh` | ✅ | ⬜ pending |
| 2-02-01 | 02 | 1 | INFRA-05 | shell | `bash -n stock-prediction-platform/scripts/deploy-all.sh` | ✅ | ⬜ pending |
| 2-02-02 | 02 | 1 | INFRA-05 | shell | `grep -q "set -euo pipefail" stock-prediction-platform/scripts/deploy-all.sh` | ✅ | ⬜ pending |
| 2-03-01 | 03 | 2 | INFRA-01 | live | `kubectl get namespaces \| grep -E "ingestion\|processing\|storage\|ml\|frontend"` | N/A | ⬜ pending |
| 2-03-02 | 03 | 2 | INFRA-02 | live | `kubectl get nodes \| grep -i ready` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. This phase only creates shell scripts and applies existing YAML manifests — no test framework installation needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| setup-minikube.sh idempotency (run twice) | INFRA-04 | Requires live cluster state to test skip-if-running path | Run `./scripts/setup-minikube.sh` twice; second run should print "Cluster already running, skipping start" and exit 0 |
| All 3 addons active in cluster | INFRA-01 | Requires live cluster | `minikube addons list \| grep -E "ingress\|metrics-server\|dashboard"` — all should show `enabled` |
| deploy-all.sh applies namespaces idempotently | INFRA-05 | Requires live cluster | Run `./scripts/deploy-all.sh` twice; no errors on second apply (`kubectl apply` is idempotent) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
