---
phase: 81
slug: fix-grafana-no-data-on-green-panels-api-health-error-rate-and-inference-errors-show-no-data-on-green-background-appearing-healthy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 81 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual visual verification (no automated Grafana panel rendering tests in project) |
| **Config file** | n/a |
| **Quick run command** | `kubectl port-forward svc/grafana 3000:3000 -n monitoring` then open browser |
| **Full suite command** | Same — visual check of all four panels in "No data" state |
| **Estimated runtime** | ~5 minutes |

---

## Sampling Rate

- **After every task commit:** `kubectl apply -f k8s/monitoring/grafana-dashboard-api-health.yaml && kubectl rollout restart deployment/grafana -n monitoring`
- **After every plan wave:** Visual port-forward check of all affected panels
- **Before `/gsd:verify-work`:** All four stat panels show blue "No data" background with no metrics present
- **Max feedback latency:** ~300 seconds (Grafana reload + port-forward)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 81-01-01 | 01 | 1 | 81-01 | manual-only | Visual check — Error Rate % panel shows blue/neutral on no data | N/A | ⬜ pending |
| 81-01-02 | 01 | 1 | 81-02 | manual-only | Visual check — p50/p95/p99 stat panels show blue/neutral on no data | N/A | ⬜ pending |
| 81-01-03 | 01 | 1 | 81-03 | manual-only | Visual check — threshold colors (green/yellow/red) work with live data | N/A | ⬜ pending |
| 81-01-04 | 01 | 1 | 81-04 | smoke | `kubectl logs -n monitoring deploy/grafana \| grep -i "error\|provision"` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Smoke test step in plan: `kubectl logs -n monitoring deploy/grafana | grep -i "provision"` after apply — confirms no provisioning errors

*Existing infrastructure covers all automated phase requirements. Wave 0 only needs the smoke test command documented in the plan.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Error Rate % shows blue background when no metric data | 81-01 | Grafana panel rendering requires live instance | Port-forward → open API Health dashboard → confirm Error Rate % panel is blue/neutral, not green, when no data |
| p50/p95/p99 Latency stats show blue when no metric data | 81-02 | Grafana panel rendering requires live instance | Same dashboard — confirm all three latency stat panels are blue/neutral on no data |
| Threshold colors work with live data | 81-03 | Requires live metrics flowing | With metrics present, confirm green/yellow/red thresholds still apply correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 300s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
