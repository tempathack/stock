# Phase 5: Kafka via Strimzi - Research

**Researched:** 2026-03-19
**Domain:** Kubernetes Kafka deployment via Strimzi operator (KRaft mode)
**Confidence:** HIGH

## Summary

Strimzi 0.40.0 provides stable KRaft (ZooKeeper-less) support with the `UseKRaft` feature gate enabled by default at beta stage. The operator supports Kafka 3.7.0, which is the exact version specified in the user's locked decisions. KRaft mode requires two annotations on the Kafka CR (`strimzi.io/kraft: enabled` and `strimzi.io/node-pools: enabled`) and a `KafkaNodePool` resource with combined `broker` + `controller` roles for a single-node deployment.

The operator YAML is a single file downloaded from the GitHub releases page. To deploy into the `storage` namespace (rather than the default `kafka` or `myproject`), all RoleBinding namespace references and the `STRIMZI_NAMESPACE` environment variable must be modified before committing. The `KafkaTopic` CRs from the Phase 1 scaffold are nearly correct -- only the Kafka CR needs restructuring from ZooKeeper-based to KRaft-based with a `KafkaNodePool`.

**Primary recommendation:** Download `strimzi-cluster-operator-0.40.0.yaml`, sed-modify namespace references to `storage`, commit it to `k8s/kafka/strimzi-operator.yaml`. Create a `kafka-cluster.yaml` containing both a KafkaNodePool CR (combined roles, persistent storage) and a Kafka CR with KRaft annotations. Separate `kafka-topics.yaml` carries forward the existing topic configs verbatim.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Install method: download official Strimzi release YAML and commit to repo as `k8s/kafka/strimzi-operator.yaml` -- no curl at runtime, fully reproducible offline
- Pinned version: Strimzi 0.40.0 specifically for determinism
- Operator applied in `setup-minikube.sh` immediately after namespace creation, followed by `kubectl wait` for operator pod Ready
- Operator namespace: `storage` (matches existing namespace layout)
- KRaft (ZooKeeper-less) -- no ZooKeeper pod or PVC
- KRaft node pool lives in `kafka-cluster.yaml` (same file as Kafka CR) -- not a separate file
- Kafka version: 3.7.x (bumped from 3.6.0 in scaffold; required for stable KRaft with Strimzi 0.40)
- Three manifest files: `k8s/kafka/strimzi-operator.yaml`, `k8s/kafka/kafka-cluster.yaml`, `k8s/kafka/kafka-topics.yaml`
- Delete `k8s/storage/kafka-strimzi.yaml` -- superseded by new layout
- `setup-minikube.sh`: apply strimzi-operator.yaml + wait for operator Ready
- `deploy-all.sh` Phase 5 section: apply kafka-cluster.yaml + kafka-topics.yaml (uncomment existing stubs)
- Both topics: 3 partitions, 1 replica, intraday-data 7-day retention, historical-data 30-day retention
- Human checkpoint as final verification gate (matching Phase 4 pattern)

### Claude's Discretion
- Exact resource requests/limits for Kafka broker pod (scaffold has 1Gi/2Gi RAM, 500m/1 CPU -- adjust if Minikube constrained)
- Entity Operator configuration (topicOperator and userOperator settings)
- Exact `kubectl wait` timeout values in setup-minikube.sh
- Whether to add `--feature-gates=+UseKRaft` or use Strimzi 0.40 annotations for KRaft enablement

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| KAFKA-01 | Strimzi operator deployed in storage namespace | Operator YAML download + namespace sed modification + setup-minikube.sh integration |
| KAFKA-02 | Kafka broker with persistent storage | KafkaNodePool CR with persistent-claim storage type, 10Gi PVC |
| KAFKA-03 | intraday-data topic created | KafkaTopic CR with 3 partitions, 1 replica, 7-day retention |
| KAFKA-04 | historical-data topic created | KafkaTopic CR with 3 partitions, 1 replica, 30-day retention |
| KAFKA-05 | K8s manifests for Kafka/Strimzi | Three-file layout under k8s/kafka/ with operator, cluster, and topics manifests |
</phase_requirements>

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Strimzi Operator | 0.40.0 | Kafka lifecycle management on K8s | Official K8s operator for Kafka; KRaft beta-enabled by default |
| Apache Kafka | 3.7.0 | Message broker | Supported by Strimzi 0.40.0; stable KRaft metadata support |
| KRaft mode | N/A | ZooKeeper-less cluster metadata | Eliminates ZooKeeper dependency; beta in Strimzi 0.40 |

### Supporting
| Component | Purpose | When to Use |
|-----------|---------|-------------|
| Entity Operator | Manages KafkaTopic and KafkaUser CRs | Always -- required for topic CR reconciliation |
| KafkaNodePool CR | Defines node roles and storage for KRaft | Required for all KRaft deployments in Strimzi 0.40+ |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Strimzi operator YAML | Helm chart | User locked decision: committed YAML for offline reproducibility |
| KRaft mode | ZooKeeper mode | User locked decision: KRaft eliminates ZooKeeper pod/PVC overhead |

**Installation (one-time download, then commit):**
```bash
# Download the operator YAML (done once, committed to repo)
curl -L https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.40.0/strimzi-cluster-operator-0.40.0.yaml \
  -o k8s/kafka/strimzi-operator.yaml

# Modify namespace references from default 'myproject' to 'storage'
sed -i 's/namespace: .*/namespace: storage/' k8s/kafka/strimzi-operator.yaml
```

**Version verification:** Strimzi 0.40.0 released on GitHub (confirmed via releases page). Supports Kafka 3.6.0, 3.6.1, and 3.7.0.

## Architecture Patterns

### Manifest Structure
```
k8s/kafka/
  strimzi-operator.yaml    # Strimzi CRDs + RBAC + Deployment (committed, namespace-modified)
  kafka-cluster.yaml       # KafkaNodePool CR + Kafka CR (KRaft, single broker)
  kafka-topics.yaml        # KafkaTopic CRs for intraday-data and historical-data
```

### Pattern 1: KRaft Kafka CR with Node Pools
**What:** Kafka CR with KRaft annotations + KafkaNodePool in same file
**When to use:** All KRaft deployments with Strimzi 0.40+

```yaml
# Source: Strimzi docs 0.40.0 + blog posts
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: combined
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  replicas: 1
  roles:
    - controller
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        deleteClaim: false
  resources:
    requests:
      memory: 1Gi
      cpu: "500m"
    limits:
      memory: 2Gi
      cpu: "1"
---
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: kafka
  namespace: storage
  annotations:
    strimzi.io/node-pools: enabled
    strimzi.io/kraft: enabled
spec:
  kafka:
    version: 3.7.0
    metadataVersion: 3.7-IV4
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
      log.retention.hours: 168
      log.segment.bytes: 1073741824
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

**Key details:**
- `strimzi.io/node-pools: enabled` and `strimzi.io/kraft: enabled` annotations are REQUIRED on the Kafka CR
- `KafkaNodePool` must have `strimzi.io/cluster: kafka` label matching the Kafka CR name
- `roles: [controller, broker]` creates combined nodes (single-node cluster needs both roles)
- `metadataVersion: 3.7-IV4` is the latest metadata version for Kafka 3.7.0
- NO `spec.zookeeper` section -- KRaft mode does not use it
- NO `inter.broker.protocol.version` -- not used in KRaft mode
- Storage is defined in KafkaNodePool, NOT in Kafka CR's `spec.kafka.storage` (node pools own storage)
- JBOD storage type with a single persistent-claim volume is the standard pattern

### Pattern 2: Operator Namespace Modification
**What:** sed-modify the downloaded operator YAML to target `storage` namespace
**When to use:** When deploying operator in a non-default namespace

The downloaded `strimzi-cluster-operator-0.40.0.yaml` defaults to namespace `myproject`. To change:
1. Replace all `namespace: myproject` with `namespace: storage`
2. The `STRIMZI_NAMESPACE` env var in the Deployment controls which namespace the operator watches
3. For single-namespace deployment (operator watches same namespace it runs in), set `STRIMZI_NAMESPACE` to `storage`

```bash
# Replace all namespace references
sed -i 's/namespace: .*/namespace: storage/' strimzi-cluster-operator-0.40.0.yaml
```

**Warning:** The sed command above is aggressive -- it replaces ALL `namespace:` lines. The downloaded YAML has `namespace: myproject` in RoleBindings and the Deployment. This is correct for single-namespace deployment where operator and Kafka are in the same namespace. However, ClusterRoleBinding subjects also have namespace references that must match the operator's namespace.

### Pattern 3: Idempotent Script Integration
**What:** Follow Phase 4's pattern for setup-minikube.sh and deploy-all.sh
**When to use:** All script modifications

```bash
# In setup-minikube.sh (after namespace creation, before deploy-all.sh)
echo "=== Installing Strimzi Kafka Operator ==="
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/strimzi-operator.yaml" -n storage
echo "Waiting for Strimzi operator to be ready..."
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator -n storage --timeout=300s
echo "Strimzi operator ready"
```

### Anti-Patterns to Avoid
- **Including `spec.zookeeper` in KRaft mode:** The operator will warn about unused fields. Remove it entirely.
- **Putting storage config in Kafka CR instead of KafkaNodePool:** In node pool mode, storage is defined per-pool, not in the Kafka CR.
- **Setting `inter.broker.protocol.version` in KRaft mode:** This field is ZooKeeper-only. Use `metadataVersion` instead.
- **Downloading operator YAML at runtime:** User locked decision requires committed YAML for offline reproducibility.
- **Using `replicas` in Kafka CR spec:** With node pools enabled, replica count is defined in KafkaNodePool, not Kafka CR.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kafka on K8s | Raw StatefulSet + ConfigMap | Strimzi operator | Handles rolling updates, storage, TLS, topic management |
| Topic management | kubectl exec + kafka-topics.sh | KafkaTopic CR + Entity Operator | Declarative, reconciled, drift-corrected |
| KRaft metadata | Manual controller.quorum.voters config | Strimzi KafkaNodePool | Operator generates correct quorum voter config |
| CRD installation | Manual CRD YAML | Strimzi operator YAML (bundles CRDs) | Single file includes all CRDs + RBAC + Deployment |

**Key insight:** Strimzi's operator YAML is a single monolithic file containing CRDs, ClusterRoles, RoleBindings, ServiceAccount, ConfigMap, and Deployment. Do not split it or hand-manage individual CRDs.

## Common Pitfalls

### Pitfall 1: Operator Not Ready Before Kafka CR Applied
**What goes wrong:** Applying `kafka-cluster.yaml` before the Strimzi CRDs are registered causes kubectl to fail with "no matches for kind Kafka"
**Why it happens:** CRDs take time to register after operator deployment
**How to avoid:** `kubectl wait` for the operator pod to be Ready before applying Kafka/KafkaNodePool/KafkaTopic CRs. The operator pod becoming Ready implies CRDs are registered.
**Warning signs:** `error: unable to recognize "kafka-cluster.yaml": no matches for kind "Kafka"`

### Pitfall 2: Kafka Broker Takes Several Minutes to Start
**What goes wrong:** Scripts timeout waiting for broker pod
**Why it happens:** KRaft initialization, storage provisioning, and metadata bootstrapping take 2-5 minutes on Minikube
**How to avoid:** Use generous timeout (300s-600s) for `kubectl wait` on the Kafka broker pod. The Strimzi operator manages the broker StatefulSet; wait for the pod, not the StatefulSet directly.
**Warning signs:** Pod stuck in `Pending` (storage) or `Init` (metadata bootstrap) for extended periods

### Pitfall 3: Wrong Namespace in Operator YAML
**What goes wrong:** Operator deploys to wrong namespace, cannot watch Kafka CRs in `storage`
**Why it happens:** Downloaded YAML defaults to `myproject` namespace. Incomplete sed replacement misses some references.
**How to avoid:** After sed, verify ALL namespace references point to `storage`. Check: Deployment namespace, ServiceAccount namespace, RoleBinding subjects, STRIMZI_NAMESPACE env var.
**Warning signs:** Operator pod running in `myproject` or `default` instead of `storage`

### Pitfall 4: KafkaTopic Applied Before Broker Ready
**What goes wrong:** Topics show `NotReady` condition, Entity Operator cannot connect to broker
**Why it happens:** Entity Operator needs a running Kafka broker to manage topics
**How to avoid:** In deploy-all.sh, apply `kafka-cluster.yaml` first, wait for broker Ready, then apply `kafka-topics.yaml`. Or accept eventual consistency -- Entity Operator will retry.
**Warning signs:** KafkaTopic CR status shows connection errors

### Pitfall 5: Resource Exhaustion on Minikube
**What goes wrong:** Pods stuck in Pending due to insufficient CPU/memory
**Why it happens:** Strimzi operator + Kafka broker + Entity Operator + existing services (PostgreSQL, FastAPI) compete for Minikube's 12GB RAM and 6 CPUs
**How to avoid:** Keep broker resources reasonable (1Gi request / 2Gi limit). The operator itself needs ~256Mi. Entity Operator needs ~256Mi. Total Kafka-related overhead: ~1.5-2Gi.
**Warning signs:** `kubectl describe pod` shows `Insufficient memory` or `Insufficient cpu`

### Pitfall 6: JBOD Storage in KafkaNodePool
**What goes wrong:** Confusion about JBOD vs persistent-claim storage types
**Why it happens:** KafkaNodePool uses JBOD storage type even for a single volume. The `type: jbod` with `volumes` array containing a single `persistent-claim` entry is the correct pattern.
**How to avoid:** Always use `type: jbod` with `volumes` array in KafkaNodePool, even for single-disk setups.
**Warning signs:** Validation errors about storage type

## Code Examples

### kafka-cluster.yaml (Complete)
```yaml
# Source: Strimzi 0.40.0 docs + KRaft blog posts
# KafkaNodePool defines node roles, replicas, and storage for KRaft
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: combined
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  replicas: 1
  roles:
    - controller
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        deleteClaim: false
  resources:
    requests:
      memory: 1Gi
      cpu: "500m"
    limits:
      memory: 2Gi
      cpu: "1"
---
# Kafka CR with KRaft annotations (no ZooKeeper section)
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: kafka
  namespace: storage
  annotations:
    strimzi.io/node-pools: enabled
    strimzi.io/kraft: enabled
spec:
  kafka:
    version: 3.7.0
    metadataVersion: 3.7-IV4
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
      log.retention.hours: 168
      log.segment.bytes: 1073741824
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

### kafka-topics.yaml (Complete)
```yaml
# Source: Carried forward from Phase 1 scaffold with correct structure
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: intraday-data
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000    # 7 days
    segment.bytes: 1073741824
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: historical-data
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 2592000000   # 30 days
    segment.bytes: 1073741824
```

### setup-minikube.sh Addition Pattern
```bash
# After namespace creation, before final verification
echo "=== Installing Strimzi Kafka Operator ==="
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/strimzi-operator.yaml" -n storage
echo "Waiting for Strimzi operator to be ready..."
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator \
  -n storage --timeout=300s
echo "Strimzi operator ready"
```

### deploy-all.sh Phase 5 Section (Uncommented)
```bash
# --- Phase 5: Kafka (Strimzi) ---
echo "[Phase 5] Deploying Kafka cluster and topics..."
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-cluster.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/kafka/kafka-topics.yaml"
```

### Verification Commands
```bash
# Check operator pod
kubectl get pods -n storage -l name=strimzi-cluster-operator

# Check Kafka broker pod (Strimzi naming: <cluster>-<nodepool>-<id>)
kubectl get pods -n storage -l strimzi.io/cluster=kafka

# Check Kafka CR status
kubectl get kafka kafka -n storage -o jsonpath='{.status.conditions}'

# Check topics
kubectl get kafkatopics -n storage

# Produce/consume test (intraday-data)
kubectl run kafka-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 \
  --rm=true --restart=Never -n storage -- \
  bin/kafka-console-producer.sh --broker-list kafka-kafka-bootstrap:9092 --topic intraday-data

kubectl run kafka-consumer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 \
  --rm=true --restart=Never -n storage -- \
  bin/kafka-console-consumer.sh --bootstrap-server kafka-kafka-bootstrap:9092 \
  --topic intraday-data --from-beginning --max-messages 1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ZooKeeper-based Kafka | KRaft (ZooKeeper-less) | Kafka 3.3+ (production-ready 3.7+) | No ZooKeeper pod/PVC, simpler operations |
| Kafka CR `spec.kafka.storage` | KafkaNodePool `spec.storage` | Strimzi 0.36+ (node pools GA) | Storage defined per-pool, not globally |
| `UseKRaft` feature gate manual enable | Enabled by default (beta) | Strimzi 0.40.0 | No need to modify operator feature gates |
| `inter.broker.protocol.version` | `metadataVersion` | KRaft mode | Different metadata management approach |

**Deprecated/outdated:**
- `spec.zookeeper` section in Kafka CR: Not used in KRaft mode, will generate warnings
- `inter.broker.protocol.version` config: ZooKeeper-only, use `metadataVersion` for KRaft
- Strimzi `UseKRaft` feature gate flag: Already enabled by default in 0.40.0, no need to set

## Open Questions

1. **Exact metadataVersion value for Kafka 3.7.0**
   - What we know: Kafka 3.7.0 has metadata versions 3.7-IV0 through 3.7-IV4. IV4 is the latest.
   - What's unclear: Whether Strimzi 0.40.0 defaults `metadataVersion` to the latest when not specified
   - Recommendation: Explicitly set `metadataVersion: 3.7-IV4` for determinism. If validation fails, try omitting it (Strimzi docs say it defaults to the version matching `spec.kafka.version`).

2. **Operator YAML sed scope**
   - What we know: `sed -i 's/namespace: .*/namespace: storage/'` will replace ALL namespace references
   - What's unclear: Whether the YAML contains namespace references that should NOT be `storage` (e.g., kube-system ClusterRoleBindings)
   - Recommendation: After sed, manually review the file. ClusterRoleBindings typically reference the operator's ServiceAccount namespace, which should be `storage`. This should be safe for single-namespace deployment.

3. **Strimzi Kafka container image tag**
   - What we know: The verification commands use `quay.io/strimzi/kafka:0.40.0-kafka-3.7.0`
   - What's unclear: Whether this exact tag exists on quay.io
   - Recommendation: Verify tag existence before committing verification instructions. If not available, use `quay.io/strimzi/kafka:latest-kafka-3.7.0`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual verification (human checkpoint) |
| Config file | N/A -- infrastructure phase |
| Quick run command | `kubectl get pods -n storage -l strimzi.io/cluster=kafka` |
| Full suite command | See verification checklist below |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KAFKA-01 | Strimzi operator pod Running in storage namespace | smoke | `kubectl get pods -n storage -l name=strimzi-cluster-operator -o jsonpath='{.items[0].status.phase}'` | N/A (kubectl) |
| KAFKA-02 | Kafka broker pod Running with persistent PVC | smoke | `kubectl get pods -n storage -l strimzi.io/cluster=kafka,strimzi.io/kind=Kafka -o jsonpath='{.items[0].status.phase}'` | N/A (kubectl) |
| KAFKA-03 | intraday-data topic exists and is producible/consumable | manual | kafka-console-producer/consumer via kubectl run | N/A (manual) |
| KAFKA-04 | historical-data topic exists and is producible/consumable | manual | kafka-console-producer/consumer via kubectl run | N/A (manual) |
| KAFKA-05 | K8s manifests exist in k8s/kafka/ | smoke | `ls k8s/kafka/strimzi-operator.yaml k8s/kafka/kafka-cluster.yaml k8s/kafka/kafka-topics.yaml` | Wave 0 creates these |

### Sampling Rate
- **Per task commit:** `kubectl get pods -n storage` (quick check)
- **Per wave merge:** Full verification checklist (operator + broker + topics + produce/consume)
- **Phase gate:** Human checkpoint -- all 6 verification items green before marking complete

### Wave 0 Gaps
- [ ] `k8s/kafka/strimzi-operator.yaml` -- downloaded and namespace-modified operator YAML
- [ ] `k8s/kafka/kafka-cluster.yaml` -- KafkaNodePool + Kafka CR for KRaft
- [ ] `k8s/kafka/kafka-topics.yaml` -- KafkaTopic CRs
- [ ] Delete `k8s/storage/kafka-strimzi.yaml` -- superseded

## Sources

### Primary (HIGH confidence)
- [Strimzi 0.40.0 GitHub Release](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/0.40.0) - Kafka 3.7.0 support, UseKRaft beta by default, breaking changes
- [Strimzi 0.40.0 Deploying Docs](https://strimzi.io/docs/operators/0.40.0/deploying) - Operator installation, namespace configuration
- [Strimzi 0.40.0 Configuring Docs](https://strimzi.io/docs/operators/0.40.0/configuring) - metadataVersion field, KafkaNodePool schema

### Secondary (MEDIUM confidence)
- [Strimzi KRaft Blog Post](https://strimzi.io/blog/2023/09/11/kafka-node-pools-supporting-kraft/) - KafkaNodePool combined roles pattern, KRaft requirements
- [Strimzi KRaft Migration Blog](https://strimzi.io/blog/2024/03/22/strimzi-kraft-migration/) - KRaft annotation values (enabled/disabled/migration)
- [Apache Kafka MetadataVersion source](https://github.com/apache/kafka/blob/trunk/server-common/src/main/java/org/apache/kafka/server/common/MetadataVersion.java) - 3.7-IV0 through 3.7-IV4 values

### Tertiary (LOW confidence)
- [Medium: KRaft deployment with Strimzi](https://remyasavithry.medium.com/kafka-kubernetes-deployment-brokers-with-kraft-zookeeperless-deployment-3-59c9b617b557) - Community example (could not verify YAML, 403 on fetch)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Strimzi 0.40.0 release confirmed, Kafka 3.7.0 support verified via GitHub release
- Architecture: HIGH - KRaft annotations and KafkaNodePool pattern verified across multiple official sources
- Pitfalls: MEDIUM - based on operational experience patterns; namespace sed replacement needs validation during implementation
- Code examples: MEDIUM - synthesized from multiple official sources; metadataVersion value (3.7-IV4) needs runtime validation

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable -- Strimzi 0.40.0 is a fixed release)
