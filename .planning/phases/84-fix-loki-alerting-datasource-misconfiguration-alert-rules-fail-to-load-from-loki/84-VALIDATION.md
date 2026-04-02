---
phase: 84
slug: fix-loki-alerting-datasource-misconfiguration-alert-rules-fail-to-load-from-loki
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 84 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.3 |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/test_loki_alerting.py -x -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/test_loki_alerting.py -x -q`
- **After every plan wave:** Run `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 84-01-01 | 01 | 0 | LOKI-ALERT-01..05 | unit | `pytest tests/test_loki_alerting.py -x -q` | ❌ W0 | ⬜ pending |
| 84-01-02 | 01 | 1 | LOKI-ALERT-01 | unit | `pytest tests/test_loki_alerting.py::test_loki_datasource_has_uid -x` | ✅ after W0 | ⬜ pending |
| 84-01-03 | 01 | 1 | LOKI-ALERT-02 | unit | `pytest tests/test_loki_alerting.py::test_alerting_configmap_has_rules -x` | ✅ after W0 | ⬜ pending |
| 84-01-04 | 01 | 1 | LOKI-ALERT-03 | unit | `pytest tests/test_loki_alerting.py::test_alert_rules_use_stable_loki_uid -x` | ✅ after W0 | ⬜ pending |
| 84-01-05 | 01 | 1 | LOKI-ALERT-04 | unit | `pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -x` | ✅ after W0 | ⬜ pending |
| 84-01-06 | 01 | 1 | LOKI-ALERT-05 | unit | `pytest tests/test_loki_alerting.py::test_grafana_deployment_mounts_alerting_configmap -x` | ✅ after W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/tests/test_loki_alerting.py` — stubs for LOKI-ALERT-01 through 05 (YAML structure tests, no cluster needed)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grafana unified alerting UI shows provisioned Loki rule | LOKI-ALERT-05 | Requires live cluster with Grafana pod restart | 1. `kubectl rollout restart deployment/grafana -n monitoring` 2. Open Grafana → Alerting → Alert rules → confirm "High Error Log Rate (Loki)" appears in active/pending/firing state |
| Promtail targets page shows active targets | LOKI-ALERT-04 | Requires live cluster | `kubectl port-forward ds/promtail 9080:9080 -n monitoring` then check `localhost:9080/targets` — should show >0 active targets |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
