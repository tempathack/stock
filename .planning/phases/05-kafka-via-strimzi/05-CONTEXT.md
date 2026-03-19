# Phase 5: Kafka via Strimzi - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy the Strimzi operator into the `storage` namespace, bring up a single-node Kafka broker in KRaft mode (ZooKeeper-less), and create both `intraday-data` and `historical-data` topics with persistent PVCs. Verify the full stack: operator Ready, broker Ready, both topics producible/consumable via kafka-console tools. Consumer services and ingestion wiring are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Strimzi Operator Delivery
- Install method: download the official Strimzi release YAML and **commit it** to the repo as `k8s/kafka/strimzi-operator.yaml` — no curl at runtime, fully reproducible offline
- Pinned version: **Strimzi 0.40.x** (0.40.0 specifically for determinism)
- Operator is applied in `setup-minikube.sh` immediately after namespace creation, followed by `kubectl wait` for the operator pod to be Ready before continuing — ensures Kafka CRDs are registered before the cluster manifest is applied
- Operator namespace: `storage` (matches existing namespace layout)

### Kafka Mode
- **KRaft (ZooKeeper-less)** — no ZooKeeper pod or PVC
- The Phase 1 scaffold's `zookeeper:` block is discarded; replaced with KRaft node pool definition
- KRaft node pool lives **in `kafka-cluster.yaml`** (same file as the Kafka CR) — not a separate file
- Kafka version: **3.7.x** (bumped from 3.6.0 in the scaffold; required for stable KRaft with Strimzi 0.40)

### Manifest Structure
- **Create `k8s/kafka/`** with three files matching deploy-all.sh stubs exactly:
  - `k8s/kafka/strimzi-operator.yaml` — Strimzi operator CRDs + RBAC + Deployment (committed YAML)
  - `k8s/kafka/kafka-cluster.yaml` — Kafka CR + KafkaNodePool CR (KRaft, single broker, persistent 10Gi PVC)
  - `k8s/kafka/kafka-topics.yaml` — KafkaTopic CRs for `intraday-data` and `historical-data`
- **Delete** `k8s/storage/kafka-strimzi.yaml` — superseded by the new layout
- Responsibility split (matching Phase 4 pattern):
  - `setup-minikube.sh`: apply `strimzi-operator.yaml` + wait for operator Ready
  - `deploy-all.sh` Phase 5 section: apply `kafka-cluster.yaml` + `kafka-topics.yaml` (uncomment existing stubs, fix paths from `k8s/kafka/` — they already match)

### Topic Configuration
- Both topics: 3 partitions, 1 replica (single-broker cluster)
- `intraday-data`: 7-day retention (`retention.ms: 604800000`)
- `historical-data`: 30-day retention (`retention.ms: 2592000000`)
- These values carry over from the Phase 1 scaffold — no change needed

### Verification Approach
- **Human checkpoint** plan (matching Phase 4 pattern)
- Verification checklist covers the full stack:
  1. Strimzi operator pod is `Running/Ready` in `storage` namespace
  2. Kafka broker pod is `Running/Ready` (single KRaft node, no ZooKeeper pod present)
  3. Both KafkaTopic CRs exist and show `Ready` condition
  4. `intraday-data` topic: produce a test message via `kafka-console-producer`, consume it via `kafka-console-consumer` — message received
  5. `historical-data` topic: same produce/consume verification
  6. Entity Operator pod is `Running` (manages topic/user CRs)

### Claude's Discretion
- Exact resource requests/limits for the Kafka broker pod (reference: scaffold has 1Gi/2Gi RAM, 500m/1 CPU — Claude adjusts if Minikube memory is constrained)
- Entity Operator configuration (topicOperator and userOperator settings)
- Exact `kubectl wait` timeout values in setup-minikube.sh
- Whether to add `--feature-gates=+UseKRaft` or use Strimzi 0.40 annotations for KRaft enablement

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing manifests (read before modifying)
- `stock-prediction-platform/k8s/storage/kafka-strimzi.yaml` — Phase 1 scaffold to DELETE; read to understand what's being replaced
- `stock-prediction-platform/scripts/deploy-all.sh` — Phase 5 stubs already reference `k8s/kafka/` paths; uncomment and verify paths match

### Existing scripts (extend, do not replace)
- `stock-prediction-platform/scripts/setup-minikube.sh` — add Strimzi operator install + wait after namespace section; follow Phase 4's idempotent pattern exactly
- `stock-prediction-platform/scripts/deploy-all.sh` — uncomment Phase 5 section; stubs already use correct `k8s/kafka/` paths

### Requirements
- `.planning/REQUIREMENTS.md` §KAFKA-01 through KAFKA-05 — full acceptance criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/setup-minikube.sh` Phase 4 additions — idempotent `--dry-run=client -o yaml | kubectl apply -f -` pattern and `kubectl wait` usage; replicate exactly for Strimzi operator install
- `k8s/storage/kafka-strimzi.yaml` — topic partition/retention config values are correct; carry forward to new `kafka-topics.yaml`

### Established Patterns
- **Operator in setup-minikube.sh, workloads in deploy-all.sh** — Phase 4 established that `setup-minikube.sh` preps infrastructure prerequisites (Secrets, ConfigMaps, now operator) and `deploy-all.sh` applies workloads
- **`set -euo pipefail` + explicit echo** — all script additions follow this pattern
- **`kubectl wait` for readiness** — used in Phase 2 for node readiness; same pattern for operator pod
- **Human checkpoint as final verification gate** — Phase 4 pattern, replicate for Kafka

### Integration Points
- `deploy-all.sh` Phase 5 stubs already exist with correct `k8s/kafka/` paths — just uncomment
- Kafka broker will be reachable at `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` (Strimzi naming convention) — this service address is used by ingestion services in Phase 6+
- `KAFKA_BOOTSTRAP_SERVERS` env var in `services/api/app/config.py` should be set to this address for future phases

</code_context>

<specifics>
## Specific Ideas

- No ZooKeeper — KRaft is the explicit choice; any plan step that mentions ZooKeeper is wrong
- Strimzi 0.40.0 + Kafka 3.7.x is the pinned version combo — researcher should confirm the exact compatible Kafka 3.7.x patch version supported by Strimzi 0.40.0
- The operator YAML must be committed to the repo, not downloaded at runtime

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-kafka-via-strimzi*
*Context gathered: 2026-03-19*
