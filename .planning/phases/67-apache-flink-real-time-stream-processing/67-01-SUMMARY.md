---
phase: 67-apache-flink-real-time-stream-processing
plan: "01"
subsystem: infra
tags: [flink, kafka, pyflink, jdbc, timescaledb, kubernetes, rbac, strimzi, rocksdb, prometheus]

# Dependency graph
requires:
  - phase: 64-timescaledb-olap
    provides: ohlcv_intraday hypertable for JDBC upsert sink
  - phase: 66-feast-production-feature-store
    provides: stock-platform-secrets Secret pattern copied across namespaces
  - phase: 5-kafka-via-strimzi
    provides: Strimzi operator + KafkaTopic CR pattern in storage namespace

provides:
  - flink namespace in k8s/namespaces.yaml
  - k8s/flink/rbac.yaml: ServiceAccount flink + ClusterRoleBinding to ClusterRole edit
  - k8s/kafka/kafka-topic-processed-features.yaml: processed-features Strimzi KafkaTopic (3 partitions, 24h retention)
  - k8s/processing/configmap.yaml: INTRADAY_TOPIC cleared — Flink owns intraday path
  - services/flink-jobs/ohlcv_normalizer/normalizer_logic.py: pure Python filter/validation/rounding helpers
  - services/flink-jobs/ohlcv_normalizer/ohlcv_normalizer.py: PyFlink Table API job (Kafka source + JDBC upsert sink)
  - services/flink-jobs/ohlcv_normalizer/Dockerfile: flink:1.19 image with PyFlink, Kafka, JDBC, PostgreSQL JARs
  - k8s/flink/flink-config-configmap.yaml: cross-namespace DNS addresses for Kafka + PostgreSQL
  - k8s/flink/flinkdeployment-ohlcv-normalizer.yaml: FlinkDeployment CR with RocksDB + MinIO checkpointing

affects:
  - 67-02 (subsequent Flink jobs inherit same flink namespace + RBAC + ConfigMap pattern)
  - 68-e2e-integration (Flink Web UI + job status checks)
  - deploy-all.sh (must copy stock-platform-secrets + minio-secrets to flink namespace)

# Tech tracking
tech-stack:
  added:
    - Apache Flink 1.19 (PyFlink Table API)
    - flink-sql-connector-kafka-3.2.0-1.19
    - flink-connector-jdbc-3.2.0-1.19
    - postgresql-42.7.3 JDBC driver
    - Flink Kubernetes Operator (FlinkDeployment CRD)
    - RocksDB state backend
  patterns:
    - PyFlink job split: normalizer_logic.py (pure Python, unit testable) + ohlcv_normalizer.py (Flink Table API)
    - JDBC upsert mode via PRIMARY KEY (ticker, timestamp) NOT ENFORCED declaration
    - Kafka cross-namespace DNS: kafka-kafka-bootstrap.storage.svc.cluster.local:9092
    - PostgreSQL cross-namespace DNS: postgresql.storage.svc.cluster.local:5432
    - MinIO S3 checkpoint path with path-style access for non-AWS endpoint
    - envFrom: [configMapRef + secretRef] pattern identical to ml/processing namespaces
    - imagePullPolicy: Never for all minikube local images

key-files:
  created:
    - stock-prediction-platform/k8s/flink/rbac.yaml
    - stock-prediction-platform/k8s/flink/flink-config-configmap.yaml
    - stock-prediction-platform/k8s/flink/flinkdeployment-ohlcv-normalizer.yaml
    - stock-prediction-platform/k8s/kafka/kafka-topic-processed-features.yaml
    - stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/normalizer_logic.py
    - stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/ohlcv_normalizer.py
    - stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/Dockerfile
    - stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/requirements.txt
    - stock-prediction-platform/tests/flink/__init__.py
    - stock-prediction-platform/tests/flink/test_ohlcv_normalizer.py
  modified:
    - stock-prediction-platform/k8s/namespaces.yaml (flink namespace appended)
    - stock-prediction-platform/k8s/processing/configmap.yaml (INTRADAY_TOPIC set to "")

key-decisions:
  - "PyFlink job split into normalizer_logic.py (pure Python) + ohlcv_normalizer.py (Flink Table API) so unit tests exercise filter logic without pyflink runtime installed"
  - "JDBC upsert mode triggered by PRIMARY KEY (ticker, timestamp) NOT ENFORCED on sink table DDL — maps to INSERT ON CONFLICT DO UPDATE in PostgreSQL"
  - "COALESCE(vwap, close) in SQL INSERT handles vwap null fallback inline — no Python UDF needed"
  - "s3.access.key / s3.secret.key omitted from flinkConfiguration — flink-s3-fs-presto plugin resolves from AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars injected via minio-secrets secretRef"
  - "stock-platform-secrets and minio-secrets must be copied to flink namespace in deploy-all.sh before FlinkDeployment apply — documented as inline YAML comments"
  - "kafka-topic-processed-features.yaml kept separate from kafka-topics.yaml for Phase 67 traceability"
  - "normalizer_logic.py copied alongside ohlcv_normalizer.py into /opt/flink/usrlib/ in Dockerfile so import works at runtime"

patterns-established:
  - "Flink job pattern: pure Python logic module + PyFlink Table API orchestrator"
  - "TDD for PyFlink: extract pure helpers to separate module, test without Flink runtime"

requirements-completed: [FLINK-01, FLINK-02, FLINK-05]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 67 Plan 01: Apache Flink OHLCV Normalizer Infrastructure Summary

**PyFlink Table API job reading intraday-data Kafka topic and upserting to ohlcv_intraday TimescaleDB hypertable via JDBC PRIMARY KEY NOT ENFORCED upsert pattern, with RocksDB + MinIO checkpointing and full flink namespace/RBAC infrastructure**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T08:25:27Z
- **Completed:** 2026-03-30T08:28:32Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Flink namespace + RBAC (ServiceAccount flink, ClusterRoleBinding to ClusterRole edit) ready for Flink Kubernetes Operator
- processed-features KafkaTopic CR (3 partitions, 24h retention) and kafka-consumer ConfigMap updated to remove intraday-data subscription
- OHLCV Normalizer PyFlink job with Kafka DDL source, JDBC upsert sink (PRIMARY KEY NOT ENFORCED), filter/validation WHERE clause, and vwap COALESCE fallback
- Dockerfile with flink:1.19 base, PyFlink, and kafka/jdbc/postgres JARs in /opt/flink/lib/
- FlinkDeployment CR with RocksDB state backend, MinIO S3 checkpointing, Prometheus annotations, and stateful upgradeMode
- 7 unit tests passing without pyflink runtime via normalizer_logic.py pure Python module split

## Task Commits

Each task was committed atomically:

1. **Task 1: Namespace, RBAC, Kafka topic, ConfigMap update** - `2ed28f6` (feat)
2. **Task 2 RED: Failing unit tests for normalizer logic** - `fbd3f52` (test)
3. **Task 2 GREEN: PyFlink job, Dockerfile, requirements, normalizer_logic** - `e0e37af` (feat)
4. **Task 3: FlinkDeployment CR + flink-config ConfigMap** - `a23d67f` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD task 2 produced two commits: test (RED) then feat (GREEN)_

## Files Created/Modified

- `stock-prediction-platform/k8s/namespaces.yaml` - flink namespace appended
- `stock-prediction-platform/k8s/flink/rbac.yaml` - ServiceAccount flink + ClusterRoleBinding to edit ClusterRole
- `stock-prediction-platform/k8s/flink/flink-config-configmap.yaml` - Kafka + Postgres + Feast cross-namespace DNS config
- `stock-prediction-platform/k8s/flink/flinkdeployment-ohlcv-normalizer.yaml` - FlinkDeployment CR with RocksDB, MinIO S3 checkpoints, Prometheus
- `stock-prediction-platform/k8s/kafka/kafka-topic-processed-features.yaml` - Strimzi KafkaTopic 3-partition 24h-retention
- `stock-prediction-platform/k8s/processing/configmap.yaml` - INTRADAY_TOPIC set to "" (Flink owns intraday path)
- `stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/normalizer_logic.py` - Pure Python filter/validate/round helpers
- `stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/ohlcv_normalizer.py` - PyFlink Table API job
- `stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/Dockerfile` - flink:1.19 image with connector JARs
- `stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/requirements.txt` - apache-flink==1.19.*
- `stock-prediction-platform/tests/flink/__init__.py` - Package marker
- `stock-prediction-platform/tests/flink/test_ohlcv_normalizer.py` - 7 unit tests for normalizer logic

## Decisions Made

- PyFlink job split into `normalizer_logic.py` (pure Python, unit testable) and `ohlcv_normalizer.py` (Flink Table API) — enables unit tests without pyflink runtime
- JDBC upsert mode triggered by `PRIMARY KEY (ticker, \`timestamp\`) NOT ENFORCED` on sink table DDL — maps to INSERT ON CONFLICT DO UPDATE in PostgreSQL/TimescaleDB
- `COALESCE(vwap, close)` in SQL INSERT handles vwap null fallback inline — no Python UDF needed
- `s3.access.key`/`s3.secret.key` omitted from `flinkConfiguration` — flink-s3-fs-presto plugin resolves from `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars via minio-secrets secretRef
- `stock-platform-secrets` and `minio-secrets` must be copied to `flink` namespace before FlinkDeployment apply — documented as inline YAML comments with exact kubectl commands
- `kafka-topic-processed-features.yaml` kept as separate file from `kafka-topics.yaml` for Phase 67 traceability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- FlinkDeployment dry-run reports "no matches for kind FlinkDeployment" as expected — CRD not yet installed (Flink Kubernetes Operator Helm install happens at deploy time). Plan's verify clause explicitly handles this with `|| echo "dry-run OK (CRD may not be installed yet)"`.

## User Setup Required

Before applying the FlinkDeployment CR, deploy-all.sh must copy secrets to the flink namespace:

```bash
# Copy stock-platform-secrets to flink namespace
kubectl get secret stock-platform-secrets -n storage -o yaml \
  | sed 's/namespace: storage/namespace: flink/' \
  | kubectl apply -f -

# Copy minio-secrets to flink namespace
kubectl get secret minio-secrets -n storage -o yaml \
  | sed 's/namespace: storage/namespace: flink/' \
  | kubectl apply -f -
```

These are documented as inline comments in `flinkdeployment-ohlcv-normalizer.yaml`.

## Next Phase Readiness

- Flink namespace, RBAC, and flink-config ConfigMap are reusable by subsequent Flink jobs (indicator stream, Feast writer)
- FlinkDeployment pattern established for Phase 67 plans 02 and 03
- deploy-all.sh needs Flink Kubernetes Operator Helm install command and Secret copy steps added in a future plan

---
*Phase: 67-apache-flink-real-time-stream-processing*
*Completed: 2026-03-30*

## Self-Check: PASSED

All 13 expected files found on disk. All 4 task commits found in git log.

| Item | Status |
|------|--------|
| k8s/namespaces.yaml (flink appended) | FOUND |
| k8s/flink/rbac.yaml | FOUND |
| k8s/flink/flink-config-configmap.yaml | FOUND |
| k8s/flink/flinkdeployment-ohlcv-normalizer.yaml | FOUND |
| k8s/kafka/kafka-topic-processed-features.yaml | FOUND |
| k8s/processing/configmap.yaml (INTRADAY_TOPIC cleared) | FOUND |
| services/flink-jobs/ohlcv_normalizer/normalizer_logic.py | FOUND |
| services/flink-jobs/ohlcv_normalizer/ohlcv_normalizer.py | FOUND |
| services/flink-jobs/ohlcv_normalizer/Dockerfile | FOUND |
| services/flink-jobs/ohlcv_normalizer/requirements.txt | FOUND |
| tests/flink/__init__.py | FOUND |
| tests/flink/test_ohlcv_normalizer.py | FOUND |
| 67-01-SUMMARY.md | FOUND |
| Commit 2ed28f6 (Task 1) | FOUND |
| Commit fbd3f52 (Task 2 RED) | FOUND |
| Commit e0e37af (Task 2 GREEN) | FOUND |
| Commit a23d67f (Task 3) | FOUND |
