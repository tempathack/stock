---
phase: 05-kafka-via-strimzi
plan: 01
subsystem: infra
tags: [kafka, strimzi, kraft, kubernetes, messaging]

# Dependency graph
requires:
  - phase: 02-minikube-k8s-namespaces
    provides: storage namespace and kubectl/minikube setup scripts
  - phase: 04-postgresql-timescaledb
    provides: setup-minikube.sh and deploy-all.sh patterns
provides:
  - Strimzi 0.40.0 operator YAML committed to repo (namespace: storage)
  - KRaft-mode Kafka cluster manifest (KafkaNodePool + Kafka CR, no ZooKeeper)
  - KafkaTopic CRs for intraday-data (7-day retention) and historical-data (30-day retention)
  - setup-minikube.sh Strimzi operator install with readiness wait
  - deploy-all.sh Phase 5 section deploying cluster and topics
affects: [06-yahoo-finance-ingestion, 08-k8s-cronjobs, 09-kafka-consumers]

# Tech tracking
tech-stack:
  added: [strimzi-0.40.0, kafka-3.7.0, kraft]
  patterns: [operator-in-setup-workloads-in-deploy, kraft-kafkanodepool-combined-roles]

key-files:
  created:
    - stock-prediction-platform/k8s/kafka/strimzi-operator.yaml
    - stock-prediction-platform/k8s/kafka/kafka-cluster.yaml
    - stock-prediction-platform/k8s/kafka/kafka-topics.yaml
  modified:
    - stock-prediction-platform/scripts/setup-minikube.sh
    - stock-prediction-platform/scripts/deploy-all.sh

key-decisions:
  - "Strimzi operator YAML downloaded and committed for offline reproducibility (not fetched at runtime)"
  - "Used targeted sed (namespace: myproject -> storage) to avoid replacing unrelated namespace refs"
  - "Operator install in setup-minikube.sh with 300s wait; workloads in deploy-all.sh (established pattern)"

patterns-established:
  - "KRaft deployment: KafkaNodePool with combined controller+broker roles, Kafka CR with strimzi.io/kraft annotation"
  - "Operator lifecycle: operator in setup-minikube.sh, CRs in deploy-all.sh"

requirements-completed: [KAFKA-01, KAFKA-02, KAFKA-03, KAFKA-04, KAFKA-05]

# Metrics
duration: 2min
completed: 2026-03-19
---

# Phase 5 Plan 01: Kafka Manifests Summary

**Strimzi 0.40.0 operator and KRaft-mode Kafka cluster manifests with intraday-data and historical-data topics, integrated into deployment scripts**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-19T08:41:26Z
- **Completed:** 2026-03-19T08:42:58Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created three-file Kafka manifest layout (operator, cluster, topics) under k8s/kafka/
- KRaft-mode Kafka cluster with KafkaNodePool (no ZooKeeper) using Strimzi 0.40.0
- Integrated Strimzi operator install into setup-minikube.sh with readiness wait
- Uncommented deploy-all.sh Phase 5 section for cluster and topic deployment
- Deleted superseded Phase 1 scaffold (k8s/storage/kafka-strimzi.yaml)

## Task Commits

Each task was committed atomically:

1. **Task 1: Download Strimzi operator YAML and create Kafka manifests** - `3348f50` (feat)
2. **Task 2: Update setup-minikube.sh and deploy-all.sh for Phase 5** - `ac36975` (feat)

## Files Created/Modified
- `stock-prediction-platform/k8s/kafka/strimzi-operator.yaml` - Strimzi 0.40.0 CRDs + RBAC + Deployment targeting storage namespace
- `stock-prediction-platform/k8s/kafka/kafka-cluster.yaml` - KafkaNodePool CR + Kafka CR for KRaft single-broker deployment
- `stock-prediction-platform/k8s/kafka/kafka-topics.yaml` - KafkaTopic CRs for intraday-data and historical-data
- `stock-prediction-platform/k8s/storage/kafka-strimzi.yaml` - Deleted (superseded Phase 1 scaffold)
- `stock-prediction-platform/scripts/setup-minikube.sh` - Added Phase 5 Strimzi operator install + wait
- `stock-prediction-platform/scripts/deploy-all.sh` - Uncommented Phase 5 section (cluster + topics)

## Decisions Made
- Strimzi operator YAML downloaded and committed for offline reproducibility (not fetched at runtime)
- Used targeted sed (namespace: myproject -> storage) to avoid replacing unrelated namespace references
- Operator install in setup-minikube.sh with 300s wait; workloads in deploy-all.sh (established pattern from Phase 4)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Kafka manifests ready for deployment on Minikube cluster
- Bootstrap service address: kafka-kafka-bootstrap:9092 (for downstream consumers/producers)
- Topics intraday-data and historical-data will be created when deploy-all.sh runs after operator is ready

## Self-Check: PASSED

All created files verified present. All commit hashes verified in git log.

---
*Phase: 05-kafka-via-strimzi*
*Completed: 2026-03-19*
