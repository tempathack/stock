---
phase: 72
slug: grafana-debug-dashboards-with-flink-metrics-integration
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-31
---

# Phase 72 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | kubectl / curl / bash (infra validation) |
| **Config file** | none — infra checks via CLI |
| **Quick run command** | `kubectl -n monitoring get pods` |
| **Full suite command** | `kubectl -n monitoring get pods && kubectl -n flink get pods && curl -s http://localhost:9090/api/v1/targets` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `kubectl -n monitoring get pods`
- **After every plan wave:** Run full suite command above
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 72-01-01 | 01 | 1 | INFRA-MON | infra | `kubectl -n monitoring get configmap prometheus-config -o yaml \| grep flink` | ✅ | ⬜ pending |
| 72-01-02 | 01 | 1 | INFRA-MON | infra | `kubectl -n monitoring get configmap grafana-datasource -o yaml \| grep uid` | ✅ | ⬜ pending |
| 72-01-03 | 01 | 2 | INFRA-MON | infra | `curl -s http://localhost:9090/api/v1/targets \| grep flink` | ✅ | ⬜ pending |
| 72-02-01 | 02 | 1 | INFRA-MON | infra | `kubectl -n monitoring get configmap grafana-dashboard-flink -o yaml \| grep checkpoint` | ✅ | ⬜ pending |
| 72-02-02 | 02 | 2 | INFRA-MON | manual | Grafana UI shows populated Flink panels | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements (kubectl, curl, prometheus port-forward available).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grafana Flink dashboard panels show real data | MON-05 | Requires Grafana UI inspection | Port-forward Grafana, open dashboard, verify panels show metrics not "No data" |
| All existing dashboards show data (not empty) | MON-05, MON-06, MON-07 | Requires Grafana UI inspection | Open each dashboard in Grafana, check for populated panels |

**Deferred:** MON-FLINK-02 Playwright test (add Flink panel visibility assertions to `e2e/infra/grafana.spec.ts`) — deferred to a future phase. Infra validation via kubectl/grep covers all required sampling for this phase.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-03-31
