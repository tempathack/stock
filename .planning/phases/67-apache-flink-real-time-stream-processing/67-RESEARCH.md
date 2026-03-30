# Phase 67: Apache Flink — Real-Time Stream Processing - Research

**Researched:** 2026-03-30
**Domain:** Apache Flink, Flink Kubernetes Operator, PyFlink, Kafka streaming, TimescaleDB upsert, Feast online push
**Confidence:** HIGH (core operator/connector patterns), MEDIUM (RSI/MACD via Flink SQL windowing), HIGH (MinIO checkpoint config)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FLINK-01 | Flink Kubernetes Operator installed in `flink` namespace; FlinkDeployment CRD available | Helm install pattern, cert-manager pre-req, operator v1.11.0 confirmed |
| FLINK-02 | Job 1 — OHLCV Normalizer: reads `intraday-data` → validates/normalizes → upserts to `ohlcv_intraday` hypertable | JDBC connector upsert-mode with primary-key DDL, flink-connector-jdbc 3.2.0-1.19 JAR |
| FLINK-03 | Job 2 — Indicator Stream: reads `intraday-data` → 5-min windowed RSI/MACD signal/EMA-20 → publishes to `processed-features` | PyFlink SQL sliding/hopping windows, Kafka Table API source+sink DDL |
| FLINK-04 | Job 3 — Feast Online Writer: consumes `processed-features` → pushes to Redis online store via `feast.push()` | Feast PushSource + `store.push()` API confirmed, Spark analogue maps to Flink foreachBatch |
| FLINK-05 | New `processed-features` Kafka topic (3 partitions, 24h retention) via Strimzi KafkaTopic CR | Existing topic YAML pattern in `k8s/kafka/kafka-topics.yaml` |
| FLINK-06 | Flink jobs packaged as Docker images, deployed as FlinkDeployment CRs in `flink` namespace | Dockerfile: FROM flink:1.19 + PyFlink + connector JARs, FlinkDeployment YAML with application mode |
| FLINK-07 | Flink metrics to Prometheus via PrometheusReporter; Grafana panel shows job uptime + record throughput | `metrics.reporter.prom.factory.class` + pod annotations; existing Prometheus kubernetes_sd picks up annotations |
| FLINK-08 | All 3 jobs survive Kafka broker restart (checkpointing enabled, RocksDB state backend) | RocksDB + incremental checkpoints to MinIO via `flink-s3-fs-presto`, `s3.endpoint` + `s3.path.style.access` |
</phase_requirements>

---

## Summary

Phase 67 deploys Apache Flink via the Flink Kubernetes Operator (v1.11.0) to replace the existing Python batch Kafka consumer for the intraday path. Three PyFlink jobs run in application mode as `FlinkDeployment` custom resources in a new `flink` namespace. Job 1 (OHLCV Normalizer) reads from the existing `intraday-data` Kafka topic and upserts to the `ohlcv_intraday` TimescaleDB hypertable using the JDBC connector's primary-key upsert mode. Job 2 (Indicator Stream) computes sliding-window RSI, MACD signal line, and EMA-20 using Flink SQL TUMBLE/HOP window functions and publishes results to a new `processed-features` Kafka topic. Job 3 (Feast Writer) consumes `processed-features` and pushes features to the Feast Redis online store using `store.push()`. All three jobs use RocksDB state backend with incremental checkpoints stored in the existing MinIO S3 bucket.

The project already has all required infrastructure: Kafka via Strimzi (namespace `storage`), TimescaleDB with `ohlcv_intraday` hypertable (primary key `(ticker, timestamp)`), MinIO in `storage` namespace (endpoint `http://minio.storage.svc.cluster.local:9000`), Redis for Feast online store, and Prometheus with kubernetes pod SD that auto-discovers pods with `prometheus.io/scrape: "true"` annotations. The new `flink` namespace must be added to `namespaces.yaml`.

The kafka-consumer batch writer for `intraday-data` is replaced by Flink Job 1. The kafka-consumer Deployment in `processing` namespace handles `historical-data` only after this phase, or can be left running for `historical-data` (it subscribes to both `intraday-data` and `historical-data` — the intraday path becomes Flink's responsibility).

**Primary recommendation:** Use PyFlink Table API with Flink SQL DDL for all three jobs. This provides the cleanest window operator support and avoids complex DataStream API boilerplate. Use Flink 1.19 (LTS) as the base image version — it has the most stable connector ecosystem and proven Kubernetes operator support.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flink Kubernetes Operator | 1.11.0 | Manages FlinkDeployment CRs, lifecycle, upgrade | Latest stable (released 2025-03-03); supports Flink 1.18+ and Flink 2.0 preview |
| Apache Flink | 1.19 | Stream processing runtime | 1.19 is the latest 1.x LTS before 2.0; connector ecosystem fully stable; 1.20.x also viable |
| PyFlink | 1.19 | Python API wrapping Flink Table/DataStream API | Must match Flink runtime version exactly |
| flink-sql-connector-kafka | 3.2.0-1.19 | Kafka source and sink for Flink SQL | Official Apache Flink Kafka connector, JAR bundled in Docker image |
| flink-connector-jdbc | 3.2.0-1.19 | JDBC sink for PostgreSQL/TimescaleDB upsert | Official connector; primary-key DDL triggers `INSERT ... ON CONFLICT DO UPDATE` |
| postgresql JDBC driver | 42.7.3 | PostgreSQL wire protocol for JDBC connector | Required by flink-connector-jdbc; TimescaleDB is PostgreSQL-compatible |
| cert-manager | v1.14+ | Pre-requisite for Flink Operator webhook | Required before helm install of operator |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| flink-s3-fs-presto plugin | bundled in flink:1.19 | S3-compatible checkpoint storage (MinIO) | Enabled via `ENABLE_BUILT_IN_PLUGINS` env var; required for RocksDB checkpoints to MinIO |
| feast[redis] | 0.61.0 (already installed) | Push features to Redis online store from Job 3 | Already pinned in project |
| apache-flink==1.19.* | PyPI | Python SDK installed in Docker image | Must match Flink runtime |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyFlink Table API (SQL DDL) | PyFlink DataStream API | DataStream gives more control but requires explicit window operators and serializers — significantly more code; Table API with SQL is idiomatic for ETL/windowing |
| Flink 1.19 | Flink 1.20 | 1.20.3 is the latest 1.x, also stable; either works with operator 1.11.0; 1.19 is the LTS choice |
| JDBC connector upsert | Custom Python psycopg2 UPSERT | JDBC connector is managed by Flink and handles back-pressure; custom Python loses fault-tolerance integration |
| MinIO for checkpoints | emptyDir or PVC | emptyDir lost on pod restart defeats checkpointing purpose; MinIO already deployed and used for model artifacts |

**Installation (in Docker image build):**
```bash
# JARs downloaded to /opt/flink/lib/ in Dockerfile
wget https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar
wget https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-1.19/flink-connector-jdbc-3.2.0-1.19.jar
wget https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar
pip3 install apache-flink==1.19.*
```

**Version verification:**
```bash
# Confirmed via Maven Central:
# flink-sql-connector-kafka: 3.2.0-1.19 (latest for Flink 1.19)
# flink-sql-connector-kafka: 3.4.0-1.20 (if using Flink 1.20)
# flink-connector-jdbc: 3.2.0-1.19 (latest for Flink 1.19)
# flink-connector-kafka operator v1.11.0 released 2025-03-03
```

---

## Architecture Patterns

### Recommended Project Structure

```
stock-prediction-platform/
├── k8s/
│   ├── namespaces.yaml              # add flink namespace here
│   └── flink/                       # NEW — all Flink K8s manifests
│       ├── namespace.yaml           # flink namespace (or add to namespaces.yaml)
│       ├── rbac.yaml                # ServiceAccount + ClusterRoleBinding for flink
│       ├── kafka-topic-processed-features.yaml  # Strimzi KafkaTopic CR
│       ├── flinkdeployment-ohlcv-normalizer.yaml
│       ├── flinkdeployment-indicator-stream.yaml
│       └── flinkdeployment-feast-writer.yaml
└── services/
    └── flink-jobs/                  # NEW — PyFlink job source code + Dockerfiles
        ├── ohlcv_normalizer/
        │   ├── Dockerfile
        │   ├── requirements.txt
        │   └── ohlcv_normalizer.py
        ├── indicator_stream/
        │   ├── Dockerfile
        │   ├── requirements.txt
        │   └── indicator_stream.py
        └── feast_writer/
            ├── Dockerfile
            ├── requirements.txt
            └── feast_writer.py
```

### Pattern 1: PyFlink Table API Application Mode Job

**What:** Each job is a standalone Python script using Flink Table API (SQL DDL). Packaged as a Docker image. Deployed via FlinkDeployment CR in application mode. The job entry point is `org.apache.flink.client.python.PythonDriver`.

**When to use:** For all three Flink jobs in this phase — SQL DDL pattern covers Kafka source, window functions, JDBC sink, and Kafka sink cleanly.

**Example — Dockerfile:**
```dockerfile
# Source: https://jaehyeon.me/blog/2024-05-30-beam-deploy-1/ + operator examples
FROM flink:1.19

# Install Python 3.10 and PyFlink
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install apache-flink==1.19.* feast[redis]==0.61.0

# Download connector JARs to Flink lib directory
RUN wget -P /opt/flink/lib/ \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-1.19/flink-connector-jdbc-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar

# Copy job script
COPY ohlcv_normalizer.py /opt/flink/usrlib/ohlcv_normalizer.py
USER flink
```

**Example — FlinkDeployment CR:**
```yaml
# Source: https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-main/docs/custom-resource/overview/
# + https://www.decodable.co/blog/get-running-with-apache-flink-on-kubernetes-2
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: ohlcv-normalizer
  namespace: flink
spec:
  image: stock-flink-ohlcv-normalizer:latest
  imagePullPolicy: Never          # minikube local image
  flinkVersion: v1_19
  serviceAccount: flink
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "2"
    # Prometheus metrics
    metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
    metrics.reporter.prom.port: "9249"
    # RocksDB checkpointing to MinIO
    state.backend: rocksdb
    state.backend.incremental: "true"
    state.checkpoints.dir: s3://model-artifacts/flink-checkpoints
    s3.endpoint: http://minio.storage.svc.cluster.local:9000
    s3.access.key: "${MINIO_ACCESS_KEY}"
    s3.secret.key: "${MINIO_SECRET_KEY}"
    s3.path.style.access: "true"
    execution.checkpointing.interval: "30s"
    execution.checkpointing.mode: EXACTLY_ONCE
    restart-strategy.type: exponential-delay
    restart-strategy.exponential-delay.initial-backoff: 1s
    restart-strategy.exponential-delay.max-backoff: 60s
  jobManager:
    resource:
      memory: "1024m"
      cpu: 0.5
  taskManager:
    resource:
      memory: "1024m"
      cpu: 0.5
  podTemplate:
    spec:
      containers:
        - name: flink-main-container
          env:
            - name: ENABLE_BUILT_IN_PLUGINS
              value: "flink-s3-fs-presto-1.19.0.jar"
          envFrom:
            - configMapRef:
                name: flink-config
            - secretRef:
                name: minio-secrets
  job:
    entryClass: "org.apache.flink.client.python.PythonDriver"
    args: ["-pyclientexec", "/usr/local/bin/python3", "-py", "/opt/flink/usrlib/ohlcv_normalizer.py"]
    parallelism: 1
    upgradeMode: stateful
    state: running
```

**Note on pod annotations for Prometheus:** Add pod template metadata annotations:
```yaml
podTemplate:
  metadata:
    annotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "9249"
      prometheus.io/path: "/"
```
The existing Prometheus config uses `kubernetes_sd_configs` with role `pod` and respects these annotations — no new scrape job needed.

### Pattern 2: Flink SQL JDBC Upsert Sink (Job 1 — OHLCV Normalizer)

**What:** Table DDL with primary key triggers `INSERT ... ON CONFLICT (ticker, timestamp) DO UPDATE SET ...` in PostgreSQL.

**Example:**
```python
# Source: https://nightlies.apache.org/flink/flink-docs-master/docs/connectors/table/jdbc/
env.execute_sql("""
    CREATE TABLE ohlcv_intraday_sink (
        ticker VARCHAR,
        `timestamp` TIMESTAMP(3),
        open DECIMAL(12, 4),
        high DECIMAL(12, 4),
        low DECIMAL(12, 4),
        close DECIMAL(12, 4),
        adj_close DECIMAL(12, 4),
        volume BIGINT,
        vwap DECIMAL(12, 4),
        PRIMARY KEY (ticker, `timestamp`) NOT ENFORCED
    ) WITH (
        'connector' = 'jdbc',
        'url' = 'jdbc:postgresql://postgresql.storage.svc.cluster.local:5432/stockdb',
        'table-name' = 'ohlcv_intraday',
        'username' = '${POSTGRES_USER}',
        'password' = '${POSTGRES_PASSWORD}',
        'sink.buffer-flush.max-rows' = '100',
        'sink.buffer-flush.interval' = '2s'
    )
""")
```

### Pattern 3: Flink SQL Hopping Window Aggregation (Job 2 — Indicator Stream)

**What:** SQL HOP window function computes rolling aggregates over a sliding window. TUMBLE is fixed/non-overlapping; HOP is sliding (overlapping). For a 5-minute slide over a larger window: `HOP(TABLE t, DESCRIPTOR(ts), INTERVAL '5' MINUTES, INTERVAL '30' MINUTES)`.

**Note on RSI/MACD via SQL:** Pure SQL can compute EMA-20 using `AVG` as an approximation or via a Python UDAF (User-Defined Aggregate Function). True EMA requires iterative state, which is better implemented via a Python UDAF registered in the TableEnvironment. MACD signal line (9-period EMA of MACD line) similarly needs a UDAF. RSI needs up/down move tracking — also a UDAF.

**Example skeleton:**
```python
# Source: pattern from https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/connectors/table/kafka/
env.execute_sql("""
    CREATE TABLE intraday_source (
        ticker VARCHAR,
        `timestamp` TIMESTAMP_LTZ(3),
        close DECIMAL(12,4),
        volume BIGINT,
        WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '10' SECONDS
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'intraday-data',
        'properties.bootstrap.servers' = '${KAFKA_BOOTSTRAP_SERVERS}',
        'properties.group.id' = 'flink-indicator-stream',
        'scan.startup.mode' = 'latest-offset',
        'format' = 'json',
        'json.ignore-parse-errors' = 'true'
    )
""")
# For EMA-20 approximation via AVG over HOP window:
# SELECT ticker, HOP_START(...) as ts, AVG(close) as ema_20 ...
# FROM TABLE(HOP(TABLE intraday_source, DESCRIPTOR(`timestamp`), INTERVAL '5' MINUTES, INTERVAL '20' MINUTES))
# GROUP BY ticker, HOP_START(...), HOP_END(...)
```

**RSI/MACD UDAF approach:** Register Python UDAF extending `AggregateFunction` from `pyflink.table.udf`. Requires `pyflink.table.udf.udaf()` decorator. The UDAF accumulates close prices over the window and computes RSI/EMA on flush.

### Pattern 4: Feast Online Push from Flink (Job 3 — Feast Writer)

**What:** In Flink, use `foreachBatch` pattern via Python DataStream API or a custom Flink Sink that calls `store.push()` for each micro-batch.

**Example:**
```python
# Source: https://docs.feast.dev/reference/data-sources/push
# Feast push pattern (Spark analogue maps to Flink)
from feast import FeatureStore
import pandas as pd

store = FeatureStore(repo_path="/opt/feast")

# In Flink: use a MapFunction or process function that accumulates records
# then calls store.push() on each window or micro-batch
def push_to_feast(records: list[dict]):
    df = pd.DataFrame(records)
    df["event_timestamp"] = pd.to_datetime(df["timestamp"])
    store.push(
        push_source_name="technical_indicators_push",
        df=df,
        to=PushMode.ONLINE,
    )
```

**Feast PushSource requirement:** The Feast `feature_repo.py` must define a `PushSource` alongside the `FeatureView`. The `technical_indicators_fv` must be updated to use a `PushSource` as its source (for streaming) alongside the existing `PostgreSQLSource` (for batch). This is an additive change to Phase 66's feature_repo.py.

### Pattern 5: Flink Operator Helm Install

```bash
# Source: https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-main/docs/try-flink-kubernetes-operator/quick-start/
# Step 1: cert-manager (required for operator webhook)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=120s

# Step 2: Create flink namespace
kubectl create namespace flink

# Step 3: Helm install
helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.11.0/
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
  --namespace flink \
  --set webhook.create=true

# Step 4: Verify
kubectl get pods -n flink
kubectl get crd | grep flink
```

**Alternative if cert-manager is a resource concern on Minikube:**
```bash
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
  --namespace flink \
  --set webhook.create=false
```

### RBAC for Flink in K8s

The operator needs a `ServiceAccount` and `ClusterRoleBinding` for managing pods:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flink
  namespace: flink
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flink-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: edit
subjects:
  - kind: ServiceAccount
    name: flink
    namespace: flink
```

### Anti-Patterns to Avoid

- **Mismatched JAR versions:** Connector JARs MUST match the Flink runtime version (e.g., `3.2.0-1.19` JARs with `flink:1.19` base image). Using `3.3.0-1.20` with `flink:1.19` causes ClassLoader errors.
- **No watermarks on Kafka source:** Without `WATERMARK FOR ts AS ts - INTERVAL 'X' SECONDS`, Flink cannot compute event-time windows. HOP/TUMBLE windows require event-time watermarks.
- **Checkpoint dir on emptyDir:** Checkpoints stored in pod-local storage are lost on restart. Always use the MinIO S3 backend.
- **Placing connector JARs in wrong directory:** JARs must go to `/opt/flink/lib/`, NOT `/opt/flink/usrlib/`. The `usrlib/` directory is for application code; `lib/` is for connector plugins.
- **Using `scan.startup.mode=earliest-offset` in production jobs:** On restart after a failure, the job resumes from the checkpoint offset — using `earliest-offset` causes re-processing all historical data from topic start.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kafka consumer with fault tolerance | Custom Python confluent-kafka consumer with offset mgmt | Flink Kafka connector with checkpointing | Flink provides exactly-once semantics, state-backed offset commits, and automatic re-processing from checkpoints |
| Sliding window aggregation | Custom Python deque/buffer for rolling stats | Flink SQL `HOP()` / `TUMBLE()` window functions | Window management (late events, watermarks, state cleanup) is extremely complex to hand-roll correctly |
| Distributed state storage | Custom Redis state management | Flink RocksDB state backend | RocksDB manages incremental state with automatic compaction and S3 offload |
| PostgreSQL upsert from stream | Custom batch writer | `flink-connector-jdbc` with primary key DDL | Handles back-pressure, retries, connection pooling from within Flink's operator graph |
| Flink Kubernetes pod management | Manual pod YAML for JM/TM | Flink Kubernetes Operator + FlinkDeployment CRD | Operator handles job restart, savepoint management, upgrade orchestration automatically |

**Key insight:** Flink's value is in its managed state and fault-tolerance model. Any attempt to replicate checkpoint/restart behavior outside Flink's framework will be fragile at scale and during Kafka broker restarts.

---

## Common Pitfalls

### Pitfall 1: Minikube Docker Context for Flink Images

**What goes wrong:** `docker build` outside `eval $(minikube docker-env)` builds images in the host Docker daemon. Minikube cannot pull them with `imagePullPolicy: Never`.

**Why it happens:** Minikube runs its own Docker daemon in the VM. The FlinkDeployment CR with `imagePullPolicy: Never` requires the image to exist in Minikube's daemon.

**How to avoid:** Always build Flink Docker images with:
```bash
eval $(minikube docker-env)
docker build -t stock-flink-ohlcv-normalizer:latest ./services/flink-jobs/ohlcv_normalizer/
```

**Warning signs:** Pod stays in `ImagePullBackOff` or `ErrImagePull` despite image being present locally.

### Pitfall 2: PyFlink Python Version Mismatch

**What goes wrong:** `flink:1.19` base image ships Python 3.8. PyFlink 1.19 package requires Python 3.8+. Feast 0.61.0 requires Python 3.9+. Conflict arises in Job 3 (Feast Writer).

**Why it happens:** The base Flink Docker image uses an older Python. Feast's newer versions require Python 3.9+.

**How to avoid:** For Job 3 Dockerfile, install Python 3.10 via apt or use `flink:1.19-scala_2.12-java11` with Python 3.10 layered:
```dockerfile
FROM flink:1.19
RUN apt-get update && apt-get install -y python3.10 python3.10-pip python3.10-dev && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
RUN pip3 install apache-flink==1.19.* feast[redis]==0.61.0
```

**Warning signs:** `ImportError` for feast or `ModuleNotFoundError: No module named 'distutils'` in container logs.

### Pitfall 3: JDBC Upsert Requires Primary Key in DDL

**What goes wrong:** JDBC sink runs in append mode (plain INSERT) instead of upsert mode. Duplicate records in `ohlcv_intraday`.

**Why it happens:** The JDBC connector only activates `INSERT ... ON CONFLICT DO UPDATE` when the Table DDL has `PRIMARY KEY (cols) NOT ENFORCED`. Omitting the primary key causes append mode.

**How to avoid:** Always include `PRIMARY KEY (ticker, \`timestamp\`) NOT ENFORCED` in the JDBC sink table DDL. The `NOT ENFORCED` suffix tells Flink the constraint is not validated by Flink (TimescaleDB enforces it at DB level).

**Warning signs:** Growing row count in `ohlcv_intraday` with duplicate `(ticker, timestamp)` pairs.

### Pitfall 4: Kafka Bootstrap Server Address

**What goes wrong:** Flink jobs in `flink` namespace cannot reach `kafka:9092` (which is a docker-compose service name). The K8s address is `kafka-kafka-bootstrap.storage.svc.cluster.local:9092`.

**Why it happens:** Flink jobs run in `flink` namespace; Kafka runs in `storage` namespace. Cross-namespace DNS is required.

**How to avoid:** Use full K8s DNS: `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` in all Flink SQL DDL and config. Pass via ConfigMap env var `KAFKA_BOOTSTRAP_SERVERS`.

**Warning signs:** `org.apache.kafka.common.errors.TimeoutException: Topic not present in metadata` in Flink TaskManager logs.

### Pitfall 5: MinIO Bucket Must Exist for Checkpointing

**What goes wrong:** Flink checkpoint fails with `BucketNotFoundException` or S3 access denied because the checkpoint bucket/prefix doesn't exist.

**Why it happens:** MinIO does not auto-create bucket paths. The Flink S3 plugin requires the bucket to exist.

**How to avoid:** Create the checkpoint prefix in the existing `minio-init-job.yaml` (or add a new init step) to create `s3://model-artifacts/flink-checkpoints/` before FlinkDeployments are applied.

**Warning signs:** Job starts but checkpointing fails with S3 errors; job does not recover after broker restart.

### Pitfall 6: Feast PushSource Must Be Registered in feature_repo.py

**What goes wrong:** `store.push("technical_indicators_push", df)` fails with `PushSourceNotFoundException`.

**Why it happens:** Feast requires a `PushSource` object defined in `feature_repo.py` and applied via `feast apply` before the streaming writer can push to it. The Phase 66 feature_repo.py uses `PostgreSQLSource` only.

**How to avoid:** Add a `PushSource` for `technical_indicators_fv` in `feature_repo.py` and re-run `feast apply`. The FeatureView must reference the PushSource as its batch source or use `stream_source` parameter.

**Warning signs:** `KeyError` or `RegistryRetrievalException` when calling `store.push()` in Job 3.

### Pitfall 7: cert-manager Resource Pressure on Minikube

**What goes wrong:** cert-manager pods (3 deployments) consume 300-500Mi of memory on a resource-constrained Minikube node, causing OOMKilled on other pods.

**Why it happens:** cert-manager is a heavyweight prerequisite for the Flink operator webhook.

**How to avoid:** Deploy with `--set webhook.create=false` to skip cert-manager dependency if resource pressure is observed. The operator still manages FlinkDeployments; only the admission webhook is skipped.

**Warning signs:** Pods in `OOMKilled` state after cert-manager install; `kubectl top nodes` shows >90% memory.

---

## Code Examples

Verified patterns from official sources:

### Job 1 — OHLCV Normalizer (Table API SQL pattern)

```python
# Source: https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/connectors/table/kafka/
#         https://nightlies.apache.org/flink/flink-docs-master/docs/connectors/table/jdbc/
from pyflink.table import EnvironmentSettings, TableEnvironment
import os

env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

KAFKA_BROKERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
PG_URL = f"jdbc:postgresql://{os.environ['POSTGRES_HOST']}:5432/{os.environ['POSTGRES_DB']}"

# Source
t_env.execute_sql(f"""
    CREATE TABLE intraday_source (
        ticker STRING,
        `timestamp` TIMESTAMP_LTZ(3),
        `open` DECIMAL(12, 4),
        high DECIMAL(12, 4),
        low DECIMAL(12, 4),
        close DECIMAL(12, 4),
        adj_close DECIMAL(12, 4),
        volume BIGINT,
        vwap DECIMAL(12, 4),
        fetch_mode STRING,
        WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '10' SECONDS
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'intraday-data',
        'properties.bootstrap.servers' = '{KAFKA_BROKERS}',
        'properties.group.id' = 'flink-ohlcv-normalizer',
        'scan.startup.mode' = 'group-offsets',
        'format' = 'json',
        'json.ignore-parse-errors' = 'true'
    )
""")

# Sink — primary key triggers upsert mode
t_env.execute_sql(f"""
    CREATE TABLE ohlcv_intraday_sink (
        ticker STRING,
        `timestamp` TIMESTAMP(3),
        `open` DECIMAL(12, 4),
        high DECIMAL(12, 4),
        low DECIMAL(12, 4),
        close DECIMAL(12, 4),
        adj_close DECIMAL(12, 4),
        volume BIGINT,
        vwap DECIMAL(12, 4),
        PRIMARY KEY (ticker, `timestamp`) NOT ENFORCED
    ) WITH (
        'connector' = 'jdbc',
        'url' = '{PG_URL}',
        'table-name' = 'ohlcv_intraday',
        'username' = '{os.environ["POSTGRES_USER"]}',
        'password' = '{os.environ["POSTGRES_PASSWORD"]}',
        'sink.buffer-flush.max-rows' = '100',
        'sink.buffer-flush.interval' = '2s'
    )
""")

# Filter intraday only and write
t_env.execute_sql("""
    INSERT INTO ohlcv_intraday_sink
    SELECT ticker, `timestamp`, `open`, high, low, close, adj_close, volume, vwap
    FROM intraday_source
    WHERE fetch_mode = 'intraday'
        AND ticker IS NOT NULL
        AND close IS NOT NULL
        AND close > 0
""")
```

### Job 2 — Indicator Stream: Windowed EMA-20 (simplified via AVG as placeholder for UDAF)

```python
# Source: Flink SQL HOP window TVF pattern
# HOP(TABLE t, DESCRIPTOR(ts), slide, size) — slide < size = overlapping windows
t_env.execute_sql("""
    CREATE VIEW windowed_indicators AS
    SELECT
        ticker,
        window_start,
        window_end,
        AVG(close) AS ema_20,
        -- RSI and MACD require UDAF — computed via registered Python UDAF
        rsi_udaf(close) AS rsi_14,
        macd_signal_udaf(close) AS macd_signal
    FROM TABLE(
        HOP(TABLE intraday_source, DESCRIPTOR(`timestamp`),
            INTERVAL '5' MINUTE, INTERVAL '20' MINUTE)
    )
    GROUP BY ticker, window_start, window_end
""")
```

### Job 3 — Feast Writer (Python process function pattern)

```python
# Source: https://docs.feast.dev/reference/data-sources/push
# Flink Python DataStream API approach for Feast push
from pyflink.datastream import StreamExecutionEnvironment
from feast import FeatureStore
from feast.infra.online_stores.redis import RedisOnlineStore
import pandas as pd

store = FeatureStore(repo_path="/opt/feast")

def push_batch_to_feast(records):
    if not records:
        return
    df = pd.DataFrame(records)
    df["event_timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    store.push(
        push_source_name="technical_indicators_push",
        df=df[["ticker", "event_timestamp", "ema_20", "rsi_14", "macd_signal"]],
        to=PushMode.ONLINE,
    )
```

### Strimzi KafkaTopic CR for processed-features

```yaml
# Source: existing k8s/kafka/kafka-topics.yaml pattern
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: processed-features
  namespace: storage
  labels:
    strimzi.io/cluster: kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 86400000   # 24 hours
    segment.bytes: 1073741824
```

### Prometheus Configuration (no changes needed)

The existing `prometheus-configmap.yaml` uses `kubernetes_sd_configs` with pod role and respects `prometheus.io/scrape: "true"` annotations. Adding pod annotations to the FlinkDeployment `podTemplate` is sufficient — no new Prometheus scrape job required:

```yaml
podTemplate:
  metadata:
    annotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "9249"
      prometheus.io/path: "/"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual K8s YAML for Flink JM/TM pods | Flink Kubernetes Operator + FlinkDeployment CRD | Operator GA'd ~2022, now v1.11.0 | Automatic lifecycle, savepoints, restarts |
| Flink 1.14 standalone | Flink 1.19 LTS (last 1.x) / Flink 2.0 preview | Flink 2.0 preview 2025-03 | 1.19 is stable LTS; 2.0 breaks some APIs |
| Python UDAF for all aggregations | SQL window functions (TUMBLE, HOP, CUMULATE) | Flink 1.16+ TVF window syntax | HOP/TUMBLE as table-valued functions (TVF) replaces older Slide/Tumble API |
| Kafka source with explicit offset management | Flink Kafka connector with checkpoint-integrated offset | Flink 1.12+ | Exactly-once semantics with checkpointed offsets |
| Heap state backend | RocksDB incremental checkpoints | Flink 1.13+ | Much lower memory footprint; S3 offloading |

**Deprecated/outdated:**
- `Slide` class in `pyflink.table.window`: Replaced by `HOP()` table-valued function in Flink SQL (Flink 1.16+). Still functional but not idiomatic.
- `state.backend: filesystem`: Replaced by `hashmap` (in-memory) or `rocksdb` (external). `filesystem` was removed in newer versions.
- `metrics.reporter.prom.class` (old key): Replaced by `metrics.reporter.prom.factory.class` in Flink 1.18+.

---

## Open Questions

1. **kafka-consumer intraday conflict**
   - What we know: The existing `kafka-consumer` Deployment subscribes to BOTH `intraday-data` and `historical-data` topics. Flink Job 1 also reads `intraday-data`.
   - What's unclear: Whether both can coexist safely (they use different `group.id` values, so they'd both write to `ohlcv_intraday` — potentially duplicating upserts), or whether the kafka-consumer should be updated to skip `intraday-data`.
   - Recommendation: The planner should explicitly update the kafka-consumer's `INTRADAY_TOPIC` config to be empty or remove subscription to `intraday-data` in the ConfigMap (`k8s/processing/configmap.yaml`). Both writing to the same hypertable with different group IDs just doubles upserts — not catastrophic but wasteful. Plan 67-01 should include this cleanup step.

2. **Feast feature_repo.py PushSource addition**
   - What we know: Phase 66 defined `technical_indicators_fv` with a `PostgreSQLSource`. Feast requires a `PushSource` to enable `store.push()`.
   - What's unclear: Whether updating `feature_repo.py` and re-running `feast apply` is safe mid-production (it is — additive schema change).
   - Recommendation: Plan 67-02 should include adding `PushSource` to `feature_repo.py` and updating the Feast CronJob to re-apply.

3. **PyFlink RSI/MACD accuracy via SQL windowing**
   - What we know: SQL `AVG()` over a HOP window approximates EMA but does not implement true exponential weighting. True RSI requires per-record state (up/down move series). True EMA requires exponential decay.
   - What's unclear: Whether a simple AVG approximation is acceptable for Phase 67 (where the purpose is demonstrating the streaming pipeline, not production-grade technical analysis).
   - Recommendation: Phase 67 should implement RSI and MACD as Python UDAFs registered with PyFlink's Table API. This is the correct approach. The UDAF accumulates the windowed close prices and applies the exact same algorithms from `ml/features/indicators.py` (already implemented in Phase 10). Document this as the approach in the plan.

4. **MinIO checkpoint bucket creation**
   - What we know: MinIO `minio-init-job.yaml` exists and creates `model-artifacts` and `drift-logs` buckets.
   - What's unclear: Whether an existing bucket can serve as checkpoint location or a dedicated bucket is needed.
   - Recommendation: Use `model-artifacts` bucket with prefix `flink-checkpoints/` — no new bucket needed. Plan 67-03 should add the prefix creation to the init job or verify it auto-creates.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (project standard) |
| Config file | `pytest.ini` at project root |
| Quick run command | `pytest services/flink-jobs/ -x -q` |
| Full suite command | `pytest services/flink-jobs/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FLINK-01 | Operator installed, FlinkDeployment CRD present | smoke (kubectl) | `kubectl get crd flinkdeployments.flink.apache.org` | ❌ Wave 0 |
| FLINK-02 | OHLCV Normalizer upserts intraday records to TimescaleDB | integration | `pytest tests/flink/test_ohlcv_normalizer.py -x` | ❌ Wave 0 |
| FLINK-03 | Indicator Stream publishes to processed-features topic | integration | `pytest tests/flink/test_indicator_stream.py -x` | ❌ Wave 0 |
| FLINK-04 | Feast Writer pushes features to Redis online store | integration | `pytest tests/flink/test_feast_writer.py -x` | ❌ Wave 0 |
| FLINK-05 | processed-features topic exists with 3 partitions | smoke (kubectl) | `kubectl get kafkatopic processed-features -n storage` | ❌ Wave 0 |
| FLINK-06 | FlinkDeployment CRs are RUNNING state | smoke (kubectl) | `kubectl get flinkdeployment -n flink` | ❌ Wave 0 |
| FLINK-07 | Flink metrics scraped by Prometheus | smoke (curl) | `curl http://localhost:9249/` from Flink pod | ❌ Wave 0 |
| FLINK-08 | Jobs recover after broker restart | manual smoke | See deploy-all.sh smoke validation | Manual-only |

**Note:** FLINK-08 (broker restart recovery) is a manual smoke test. It requires killing and restarting the Kafka broker pod and observing Flink job RUNNING state resumes — this cannot be automated in unit tests.

### Sampling Rate

- **Per task commit:** `kubectl get flinkdeployment -n flink` (state check)
- **Per wave merge:** `pytest services/flink-jobs/ -v`
- **Phase gate:** All 3 FlinkDeployments in RUNNING state + smoke validation script passes before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/flink/__init__.py` — package init
- [ ] `tests/flink/test_ohlcv_normalizer.py` — unit test for normalization/filter logic (covers FLINK-02)
- [ ] `tests/flink/test_indicator_stream.py` — unit test for UDAF RSI/EMA/MACD math (covers FLINK-03)
- [ ] `tests/flink/test_feast_writer.py` — unit test for Feast push mock (covers FLINK-04)
- [ ] Framework install: `pip install apache-flink==1.19.*` — if local test environment does not have PyFlink

---

## Sources

### Primary (HIGH confidence)

- `https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-stable/` — operator v1.14.0 confirmed stable, v1.11.0 release notes
- `https://flink.apache.org/2025/03/03/apache-flink-kubernetes-operator-1.11.0-release-announcement/` — v1.11.0 release notes
- `https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/connectors/table/kafka/` — Kafka connector DDL, version 3.2.0-1.19 / 3.3.0-1.20
- `https://nightlies.apache.org/flink/flink-docs-master/docs/connectors/table/jdbc/` — JDBC upsert mode, primary key trigger behavior
- `https://nightlies.apache.org/flink/flink-docs-master/docs/ops/state/state_backends/` — RocksDB config keys
- `https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-main/docs/operations/metrics-logging/` — Prometheus reporter factory class key
- `https://docs.feast.dev/reference/data-sources/push` — Feast push source API, `store.push()` pattern
- Project codebase: `k8s/kafka/kafka-topics.yaml`, `k8s/processing/configmap.yaml`, `k8s/monitoring/prometheus-configmap.yaml`, `ml/feature_store/feature_repo.py`, `services/kafka-consumer/consumer/processor.py`

### Secondary (MEDIUM confidence)

- `https://jaehyeon.me/blog/2024-05-30-beam-deploy-1/` — PyFlink 1.17 Dockerfile pattern (Flink 1.17 → 1.19 pattern same structure)
- `https://www.decodable.co/blog/get-running-with-apache-flink-on-kubernetes-2` — S3/MinIO checkpoint config keys for FlinkDeployment
- `https://mvnrepository.com/artifact/org.apache.flink/flink-sql-connector-kafka/3.3.0-1.20` — Maven version verification
- `https://mvnrepository.com/artifact/org.apache.flink/flink-connector-jdbc/3.2.0-1.19` — JDBC connector version verification

### Tertiary (LOW confidence)

- RSI/MACD UDAF via PyFlink: Pattern inferred from Flink UDAF documentation + existing Phase 10 indicator implementations. No direct example found combining PyFlink UDAF with RSI/MACD — treat as implementation guidance only, not verified code.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Maven Central versions verified, operator release notes confirm 1.11.0 as latest stable
- Architecture: HIGH — FlinkDeployment YAML structure, JDBC upsert, checkpoint config all from official docs
- Pitfalls: HIGH — most pitfalls derived from examining existing project codebase + official connector docs
- RSI/MACD UDAF approach: MEDIUM — pattern is sound (registered UDAF) but exact PyFlink 1.19 UDAF API syntax needs verification at implementation time

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (Flink ecosystem moves slowly; connector versions stable for 30+ days)
