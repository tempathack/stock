---
phase: 82
slug: fix-ml-prediction-latency-alerting-add-threshold-line-for-8-10s-p95-verify-p50-p95-p99-are-real-histogram-metrics-not-synthetic
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 82 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | manual (YAML/JSON config validation + kubectl apply dry-run) |
| **Config file** | none — validation is grep/diff based |
| **Quick run command** | `grep -c "constantLine\|threshold" stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml` |
| **Full suite command** | `kubectl apply --dry-run=client -f stock-prediction-platform/k8s/monitoring/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 82-01-01 | 01 | 1 | threshold-line | grep | `grep "thresholds\|constantLine" stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml` | ✅ | ⬜ pending |
| 82-01-02 | 01 | 1 | alert-rule | grep | `grep "HighPredictionLatencyP95" stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml` | ✅ | ⬜ pending |
| 82-02-01 | 02 | 1 | histogram-verify | grep | `grep "histogram_quantile" stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. No test stubs needed — changes are YAML config files verified by grep and dry-run apply.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Threshold line appears at 8s on Grafana panel | threshold-line | Requires running Grafana UI | Port-forward Grafana, open ML Performance dashboard, verify dashed red line at y=8 |
| Alert fires when p95 > 8s | alert-rule | Requires Prometheus to evaluate | Check Prometheus alerts UI for HighPredictionLatencyP95 rule present and PENDING/FIRING state when injected |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
