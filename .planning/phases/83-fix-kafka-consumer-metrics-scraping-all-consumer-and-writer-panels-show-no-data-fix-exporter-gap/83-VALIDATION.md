---
phase: 83
slug: fix-kafka-consumer-metrics-scraping-all-consumer-and-writer-panels-show-no-data-fix-exporter-gap
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 83 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification + pytest (consumer service has tests in `services/kafka-consumer/tests/`) |
| **Config file** | `services/kafka-consumer/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds (unit suite) + manual cluster checks |

---

## Sampling Rate

- **After every task commit:** Apply ConfigMap/manifest change, check pod status with `kubectl get pods -n processing -l app=kafka-consumer`
- **After every plan wave:** `kubectl port-forward` verification of Prometheus targets + Grafana panels
- **Before `/gsd:verify-work`:** Full unit suite must be green AND Grafana "Kafka & Infrastructure" dashboard shows live data
- **Max feedback latency:** ~30 seconds (kubectl apply + pod restart + scrape interval)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 83-01-01 | 01 | 1 | INFRA | smoke | `kubectl get pods -n processing -l app=kafka-consumer` | ✅ | ⬜ pending |
| 83-01-02 | 01 | 1 | INFRA | smoke | `grep "INTRADAY_TOPIC: \"intraday-data\"" k8s/processing/configmap.yaml` | ✅ | ⬜ pending |
| 83-01-03 | 01 | 1 | MON-03 | smoke | `grep "kafka-consumer:9090" monitoring/prometheus.yml` | ✅ | ⬜ pending |
| 83-01-04 | 01 | 1 | MON-03 | manual | `kubectl port-forward -n monitoring deploy/prometheus 9090:9090` then check /targets | manual | ⬜ pending |
| 83-01-05 | 01 | 2 | MON-03 | smoke | `ls k8s/processing/kafka-consumer-service.yaml` | ✅ W0 | ⬜ pending |
| 83-01-06 | 01 | 2 | INFRA | manual | Grafana Kafka dashboard panels show data (not "No data") | manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — existing test infrastructure covers the Python metrics code. The fixes are YAML-only and require live cluster verification, not new test files.

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Prometheus targets page shows kafka-consumer as UP | MON-03 | K8s+Prometheus integration — cannot be unit tested | `kubectl port-forward -n monitoring deploy/prometheus 9090:9090` → visit http://localhost:9090/targets, find kafka-consumer row, status = UP |
| Grafana Kafka & Infrastructure dashboard panels show live data | MON-03 | Visual dashboard check requires running Grafana | `kubectl port-forward -n monitoring deploy/grafana 3000:3000` → open Kafka & Infrastructure dashboard, verify Consumer Metrics and Database Writer panels show data (not "No data") |
| Consumer pod starts without CrashLoopBackOff after INTRADAY_TOPIC fix | INFRA | Requires live K8s cluster | `kubectl get pods -n processing -l app=kafka-consumer` — status = Running; `kubectl logs -n processing -l app=kafka-consumer --tail=20` — no subscribe error |
| `messages_consumed_total`, `consumer_lag`, `batch_write_duration_seconds` metrics present | MON-03 | Requires running consumer pod | `kubectl port-forward -n processing <pod-name> 9090:9090 & curl -s http://localhost:9090/metrics \| grep -c "messages_consumed_total\|consumer_lag\|batch_write"` — output ≥ 3 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
