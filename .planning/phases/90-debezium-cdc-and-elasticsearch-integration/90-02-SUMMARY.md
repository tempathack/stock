---
phase: 90-debezium-cdc-and-elasticsearch-integration
plan: "02"
subsystem: infra
tags: [debezium, kafka-connect, elasticsearch, strimzi, cdc, postgresql, kafka]

# Dependency graph
requires:
  - phase: 5-kafka-via-strimzi
    provides: Kafka cluster (kafka) in storage namespace with bootstrap service FQDN
  - phase: 4-postgresql-timescaledb
    provides: PostgreSQL in storage namespace with predictions, drift_logs, model_registry tables
provides:
  - Debezium custom Docker image spec (FROM debezium/connect:2.7 + Confluent ES Sink 14.2.0 JAR)
  - Strimzi KafkaConnect CR (debezium-connect) in processing namespace
  - Debezium PostgreSQL source KafkaConnector CR with ExtractNewRecordState SMT
  - Confluent Elasticsearch Sink KafkaConnector CR wiring CDC topics to Elasticsearch
  - Three KafkaTopic CRs for debezium.public.predictions, debezium.public.drift_logs, debezium.public.model_registry
affects: [phase-90-elasticsearch, elasticsearch-indexing, cdc-pipeline]

# Tech tracking
tech-stack:
  added: [debezium/connect:2.7, confluent-kafka-connect-elasticsearch-14.2.0, strimzi-kafka-connect-cr, strimzi-kafka-connector-cr]
  patterns: [cdc-via-debezium, kafka-connect-strimzi-operator, extract-new-record-state-smt, cross-namespace-kafka-fqdn]

key-files:
  created:
    - stock-prediction-platform/docker/debezium-connect/Dockerfile
    - stock-prediction-platform/k8s/processing/kafka-topics-cdc.yaml
    - stock-prediction-platform/k8s/processing/kafka-connect-debezium.yaml
    - stock-prediction-platform/k8s/processing/kafka-connect-connector-pg.yaml
    - stock-prediction-platform/k8s/processing/kafka-connect-connector-es.yaml
  modified: []

key-decisions:
  - "KafkaTopic CRs placed in storage namespace (not processing) — Strimzi Topic Operator manages topics where Kafka cluster lives"
  - "strimzi.io/use-connector-resources: true annotation on KafkaConnect CR is required for KafkaConnector CRs to be reconciled"
  - "imagePullPolicy: Never used because custom image is loaded via minikube image load — no registry push needed"
  - "ExtractNewRecordState SMT chosen over deprecated UnwrapFromEnvelope for flattening CDC envelopes"
  - "JSON converters without schemas used for simplicity (no Schema Registry dependency)"
  - "Cross-namespace Kafka bootstrap FQDN: kafka-kafka-bootstrap.storage.svc.cluster.local:9092"

patterns-established:
  - "Cross-namespace Kafka connect: KafkaConnect in processing namespace uses FQDN to reach Kafka in storage namespace"
  - "KafkaConnector label strimzi.io/cluster matches KafkaConnect CR name for operator reconciliation"
  - "CDC topic naming: debezium.public.<table> pattern for Debezium topic prefix + schema.table"

requirements-completed: []

# Metrics
duration: 5min
completed: "2026-04-03"
---

# Phase 90 Plan 02: Debezium CDC Pipeline Manifests Summary

**Custom Debezium Connect image spec plus five Kubernetes manifests wiring PostgreSQL WAL changes through Kafka into Elasticsearch via Strimzi KafkaConnect/KafkaConnector CRs and ExtractNewRecordState SMT**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-03T10:23:25Z
- **Completed:** 2026-04-03T10:28:00Z
- **Tasks:** 2
- **Files modified:** 5 (all created)

## Accomplishments
- Custom Dockerfile specifying Debezium Connect 2.7 base with Confluent Elasticsearch Sink 14.2.0 JAR installed to plugin path
- Three KafkaTopic CRs in storage namespace for CDC topics (debezium.public.predictions, debezium.public.drift_logs, debezium.public.model_registry)
- Strimzi KafkaConnect CR in processing namespace with use-connector-resources annotation enabling KafkaConnector CR reconciliation
- Debezium PostgreSQL source KafkaConnector CR with ExtractNewRecordState SMT flattening CDC envelopes for all three tables
- Confluent Elasticsearch Sink KafkaConnector CR routing all three CDC topics to Elasticsearch ClusterIP service

## Task Commits

Each task was committed atomically:

1. **Task 1: Dockerfile + KafkaTopic CRs for CDC topics** - `45190cc` (feat)
2. **Task 2: KafkaConnect CR + KafkaConnector CRs** - `d84336d` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `stock-prediction-platform/docker/debezium-connect/Dockerfile` - Custom image: FROM debezium/connect:2.7, downloads Confluent ES Sink JAR 14.2.0
- `stock-prediction-platform/k8s/processing/kafka-topics-cdc.yaml` - Three KafkaTopic CRs in storage namespace with strimzi.io/cluster: kafka label
- `stock-prediction-platform/k8s/processing/kafka-connect-debezium.yaml` - KafkaConnect CR: debezium-connect in processing, use-connector-resources annotation, FQDN bootstrap, imagePullPolicy: Never
- `stock-prediction-platform/k8s/processing/kafka-connect-connector-pg.yaml` - PostgreSQL source connector: pgoutput plugin, 3 tables, ExtractNewRecordState SMT
- `stock-prediction-platform/k8s/processing/kafka-connect-connector-es.yaml` - ES Sink connector: 3 CDC topics wired to elasticsearch.storage.svc.cluster.local:9200

## Decisions Made
- KafkaTopic CRs placed in `storage` namespace because Strimzi Topic Operator watches the namespace where the Kafka CR lives
- `strimzi.io/use-connector-resources: "true"` annotation on KafkaConnect CR is the critical toggle enabling KafkaConnector CR reconciliation by the operator
- `imagePullPolicy: Never` in pod template spec because the custom image is loaded into Minikube directly — no container registry needed
- ExtractNewRecordState SMT (not deprecated UnwrapFromEnvelope) selected for flattening CDC before/after envelope
- JSON converters without schema registry for simplicity; ES Sink uses StringConverter for keys
- Cross-namespace FQDN pattern `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` required because KafkaConnect lives in `processing` not `storage`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
Before applying `kafka-connect-debezium.yaml`, the custom image must be built and loaded:
```bash
# Run from stock-prediction-platform/ directory
docker build -t debezium-connect-custom:latest -f docker/debezium-connect/Dockerfile .
minikube image load debezium-connect-custom:latest
```

PostgreSQL replication must be enabled (wal_level = logical) and a replication slot/publication created before the connector starts.

## Next Phase Readiness
- All five manifest files are ready to apply once the custom image is built and loaded
- The CDC pipeline connects to Elasticsearch at `elasticsearch.storage.svc.cluster.local:9200` — Phase 90-03 must ensure Elasticsearch is running at that address
- The three CDC topics will be created automatically by Strimzi Topic Operator when `kafka-topics-cdc.yaml` is applied

---
*Phase: 90-debezium-cdc-and-elasticsearch-integration*
*Completed: 2026-04-03*
