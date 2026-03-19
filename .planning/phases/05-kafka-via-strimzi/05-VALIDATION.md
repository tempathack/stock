---
phase: 5
slug: kafka-via-strimzi
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification (human checkpoint) — infrastructure phase |
| **Config file** | N/A — no test framework config |
| **Quick run command** | `kubectl get pods -n storage -l strimzi.io/cluster=kafka` |
| **Full suite command** | See Per-Task Verification Map below |
| **Estimated runtime** | ~5–10 minutes (Kafka broker takes 2–5 min to start) |

---

## Sampling Rate

- **After every task commit:** Run `kubectl get pods -n storage` (quick pod status check)
- **After every plan wave:** Run full verification checklist (operator + broker + topics + produce/consume)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~600 seconds (generous for Kafka init)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | KAFKA-05 | smoke | `ls k8s/kafka/strimzi-operator.yaml k8s/kafka/kafka-cluster.yaml k8s/kafka/kafka-topics.yaml` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | KAFKA-01 | smoke | `kubectl get pods -n storage -l name=strimzi-cluster-operator -o jsonpath='{.items[0].status.phase}'` | N/A (kubectl) | ⬜ pending |
| 5-01-03 | 01 | 2 | KAFKA-02 | smoke | `kubectl get pods -n storage -l strimzi.io/cluster=kafka,strimzi.io/kind=Kafka -o jsonpath='{.items[0].status.phase}'` | N/A (kubectl) | ⬜ pending |
| 5-01-04 | 01 | 2 | KAFKA-03 | manual | `kubectl run kafka-consumer --rm=true --restart=Never -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 -n storage -- bin/kafka-console-consumer.sh --bootstrap-server kafka-kafka-bootstrap:9092 --topic intraday-data --from-beginning --max-messages 1` | N/A (manual) | ⬜ pending |
| 5-01-05 | 01 | 2 | KAFKA-04 | manual | `kubectl run kafka-consumer --rm=true --restart=Never -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 -n storage -- bin/kafka-console-consumer.sh --bootstrap-server kafka-kafka-bootstrap:9092 --topic historical-data --from-beginning --max-messages 1` | N/A (manual) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `k8s/kafka/strimzi-operator.yaml` — downloaded Strimzi 0.40.0 operator YAML, namespace-modified to `storage`
- [ ] `k8s/kafka/kafka-cluster.yaml` — KafkaNodePool CR + Kafka CR (KRaft, combined roles, persistent storage)
- [ ] `k8s/kafka/kafka-topics.yaml` — KafkaTopic CRs for intraday-data and historical-data
- [ ] Delete `k8s/storage/kafka-strimzi.yaml` — superseded by new three-file layout

*Wave 0 creates the manifest files; verification commands are kubectl-based (no test framework install needed).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| intraday-data topic producible/consumable | KAFKA-03 | Requires live Kafka broker + kubectl run ephemeral pod | Run producer: `kubectl run kafka-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -n storage -- bin/kafka-console-producer.sh --broker-list kafka-kafka-bootstrap:9092 --topic intraday-data`; then consumer to verify message received |
| historical-data topic producible/consumable | KAFKA-04 | Requires live Kafka broker + kubectl run ephemeral pod | Same pattern as above but `--topic historical-data` |
| Kafka broker persistent PVC bound | KAFKA-02 | Storage provisioner behavior varies | `kubectl get pvc -n storage` — verify PVC is `Bound` with 10Gi capacity |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 600s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
