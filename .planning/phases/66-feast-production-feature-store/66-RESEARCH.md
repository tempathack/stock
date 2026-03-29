# Phase 66: Feast — Production Feature Store - Research

**Researched:** 2026-03-29
**Domain:** Feast 0.61.0 — PostgreSQL offline store, Redis online store, K8s feature server
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FEAST-01 | `ml/feature_store/feature_store.yaml` configures Feast with PostgreSQL offline store + Redis online store | feature_store.yaml structure with SQL registry, postgres offline_store, redis online_store documented in §Standard Stack |
| FEAST-02 | Three FeatureViews registered: `ohlcv_stats_fv`, `technical_indicators_fv`, `lag_features_fv` | FeatureView definition patterns with PostgreSQLSource, Entity, Field types in §Architecture Patterns |
| FEAST-03 | `feast apply` completes without error | feast apply mechanics and what it creates in PostgreSQL documented in §Architecture Patterns |
| FEAST-04 | `store.get_historical_features(entity_df)` returns point-in-time correct training data | Point-in-time join mechanics, entity_df format with `event_timestamp` column in §Architecture Patterns |
| FEAST-05 | `store.get_online_features({"ticker": ["AAPL"]})` returns features from Redis in <5ms | Online retrieval patterns, Redis key structure, sub-millisecond characteristics in §Architecture Patterns |
| FEAST-06 | ML training pipeline uses `feast.get_historical_features()` instead of raw DB queries | Integration changes to `feature_engineer.py` and `training_pipeline.py` documented in §Code Examples |
| FEAST-07 | Prediction API uses `feast.get_online_features()` for real-time feature retrieval | API integration pattern via `predict.py` service layer documented in §Code Examples |
| FEAST-08 | K8s CronJob materializes features daily at 18:30 ET; Feast feature server Deployment in `ml` namespace | Materialization CronJob and feature server Deployment manifests documented in §Architecture Patterns |
</phase_requirements>

---

## Summary

Feast 0.61.0 (released March 10, 2026) is the current stable release and is fully compatible with Python 3.11 used in the ML Dockerfile. The project already has Redis deployed in the `storage` namespace at `redis.storage.svc.cluster.local:6379` and PostgreSQL at `postgresql.storage.svc.cluster.local:5432` — both are the exact infrastructure Feast expects. No new infrastructure is needed for Phase 66; Feast is purely a software layer layered on top of existing services.

The core architectural change is replacing `ml/features/store.py` (an EAV-table-based custom feature cache) with Feast's standard offline + online store API. The existing `feature_store` PostgreSQL table (EAV format) is replaced by three structured tables that serve as Feast's DataSources: one per FeatureView (`ohlcv_stats_fv`, `technical_indicators_fv`, `lag_features_fv`). These tables store features in wide columnar format indexed by `(ticker, timestamp)`, which Feast queries with its point-in-time join engine. Redis stores current feature values for sub-millisecond online serving.

The migration pattern is additive: `feature_engineer.py` gets a new `use_feast=True` code path that calls `store.get_historical_features()`; the old `use_feature_store=True` (EAV path) is preserved as fallback. The prediction path acquires a new service function that calls `store.get_online_features()` before falling back to live computation. This preserves full backward compatibility.

**Primary recommendation:** Install `feast[postgres,redis]==0.61.0`, create `ml/feature_store/` as the Feast repo directory, wire three wide-format DataSource tables as PostgreSQLSources, define one Entity (`ticker`) and three FeatureViews, run `feast apply`, then update the two call sites (training pipeline and prediction router).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| feast | 0.61.0 | Feature store SDK — offline + online retrieval | Current stable, Python 3.11 compatible, PyPI March 2026 |
| feast[postgres] extra | included | PostgreSQL offline store driver (psycopg2 + SQLAlchemy) | Required for `PostgreSQLSource` and `postgres` offline_store type |
| feast[redis] extra | included | Redis online store driver (redis-py) | Required for `redis` online_store type |
| psycopg2-binary | already in ml/requirements.txt | PostgreSQL driver | Already present; feast[postgres] will use it |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| feastdev/feature-server Docker image | 0.61.0 tag | Pre-built K8s feature server | Used for Feast feature server Deployment in ml namespace |
| pyarrow | >=21.0.0 (feast dep) | Feast uses Arrow for offline data transfer | Pulled in transitively; already in ml requirements at 23.0.1 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `feast[postgres]` offline store | DuckDB offline store | DuckDB is file-based; PostgreSQL already exists, no added infra |
| SQL registry (PostgreSQL path) | File-based registry (registry.db) | File registry is fine for local dev but not K8s — SQL registry survives pod restarts |
| `feast serve` Python feature server | Java feature server | Python server matches project's Python ML stack; Java server has better throughput but unnecessary here |

**Installation:**
```bash
pip install 'feast[postgres,redis]==0.61.0'
```

Add to `ml/requirements.txt`:
```
feast[postgres,redis]==0.61.0
```

**Version verification:** Confirmed against PyPI. Feast 0.61.0 released 2026-03-10. Python >=3.10.0 required — project uses Python 3.11 (confirmed in ml/Dockerfile). feast requires numpy>=2.0.0, pyarrow>=21.0.0 — both already satisfied in ml/requirements.txt (numpy 1.26.4 currently; must be bumped to >=2.0.0 for feast, but pyarrow 23.0.1 is already present).

**Critical:** Current `ml/requirements.txt` pins `numpy==1.26.4`. Feast 0.61.0 requires `numpy>=2.0.0`. The numpy bump is a required change in Plan 66-01.

---

## Architecture Patterns

### Recommended Project Structure

```
ml/
├── feature_store/          # Feast repo root (new directory)
│   ├── feature_store.yaml  # Feast configuration (registry + stores)
│   ├── feature_repo.py     # Entity, DataSource, FeatureView definitions
│   └── __init__.py         # Makes importable from ml package
├── features/
│   ├── store.py            # KEEP — existing EAV store (fallback)
│   └── feast_store.py      # NEW — Feast wrapper (get_historical, get_online)
└── ...
```

The `ml/feature_store/` directory is the Feast "feature repository" — the directory passed to `FeatureStore(repo_path=...)`.

### Pattern 1: feature_store.yaml — Full Production Config

**What:** Configures Feast project with SQL registry (PostgreSQL), postgres offline store, redis online store.

**When to use:** Always — this is the single config file for the entire Feast deployment.

```yaml
# ml/feature_store/feature_store.yaml
project: stock_prediction
provider: local
entity_key_serialization_version: 3

registry:
  registry_type: sql
  path: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
  cache_ttl_seconds: 60
  sqlalchemy_config_kwargs:
    echo: false
    pool_pre_ping: true

offline_store:
  type: postgres
  host: ${POSTGRES_HOST}
  port: ${POSTGRES_PORT}
  database: ${POSTGRES_DB}
  db_schema: public
  user: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}

online_store:
  type: redis
  connection_string: "${REDIS_HOST}:${REDIS_PORT}"
```

**Key notes:**
- `provider: local` is correct for self-managed PostgreSQL + Redis (not cloud-managed). This does NOT mean local dev only.
- `entity_key_serialization_version: 3` is required for current Feast versions (avoids deprecation warning).
- `${ENV_VAR}` syntax is natively supported by Feast for secrets injection — use for all credentials.
- `registry_type: sql` stores Feast metadata (FeatureView definitions, materialization watermarks) in PostgreSQL. It auto-creates tables on first `feast apply`.
- `db_schema: public` uses the existing `public` schema; Feast creates its own offline tables there.

### Pattern 2: Entity and DataSource Definitions

**What:** Defines the ticker entity and three PostgreSQL DataSources (one per FeatureView).

```python
# ml/feature_store/feature_repo.py
# Source: https://docs.feast.dev/reference/data-sources/postgres
from datetime import timedelta
from feast import Entity, FeatureView, Field, FeatureStore
from feast.types import Float64, Int64, String
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)

# ── Entity ──────────────────────────────────────────────────────────────────
ticker = Entity(
    name="ticker",
    join_keys=["ticker"],
    description="Stock ticker symbol (e.g. AAPL, MSFT)",
)

# ── DataSources ─────────────────────────────────────────────────────────────
# Each source maps to a wide-format PostgreSQL table populated by a
# materialization step (replaces the EAV feature_store table).

ohlcv_source = PostgreSQLSource(
    name="ohlcv_stats_source",
    query="SELECT ticker, timestamp, open, high, low, close, volume, daily_return, vwap FROM feast_ohlcv_stats",
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

indicators_source = PostgreSQLSource(
    name="technical_indicators_source",
    query="SELECT ticker, timestamp, rsi_14, macd_line, macd_signal, bb_upper, bb_lower, atr_14, adx_14, ema_20, obv FROM feast_technical_indicators",
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

lag_source = PostgreSQLSource(
    name="lag_features_source",
    query=(
        "SELECT ticker, timestamp, "
        "lag_1, lag_2, lag_3, lag_5, lag_7, lag_10, lag_14, lag_21, "
        "rolling_mean_5, rolling_mean_10, rolling_mean_21, "
        "rolling_std_5, rolling_std_10, rolling_std_21 "
        "FROM feast_lag_features"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

# ── FeatureViews ─────────────────────────────────────────────────────────────
ohlcv_stats_fv = FeatureView(
    name="ohlcv_stats_fv",
    entities=[ticker],
    ttl=timedelta(days=7),
    schema=[
        Field(name="open",         dtype=Float64),
        Field(name="high",         dtype=Float64),
        Field(name="low",          dtype=Float64),
        Field(name="close",        dtype=Float64),
        Field(name="volume",       dtype=Int64),
        Field(name="daily_return", dtype=Float64),
        Field(name="vwap",         dtype=Float64),
    ],
    online=True,
    source=ohlcv_source,
)

technical_indicators_fv = FeatureView(
    name="technical_indicators_fv",
    entities=[ticker],
    ttl=timedelta(days=7),
    schema=[
        Field(name="rsi_14",      dtype=Float64),
        Field(name="macd_line",   dtype=Float64),
        Field(name="macd_signal", dtype=Float64),
        Field(name="bb_upper",    dtype=Float64),
        Field(name="bb_lower",    dtype=Float64),
        Field(name="atr_14",      dtype=Float64),
        Field(name="adx_14",      dtype=Float64),
        Field(name="ema_20",      dtype=Float64),
        Field(name="obv",         dtype=Float64),
    ],
    online=True,
    source=indicators_source,
)

lag_features_fv = FeatureView(
    name="lag_features_fv",
    entities=[ticker],
    ttl=timedelta(days=7),
    schema=[
        Field(name="lag_1",          dtype=Float64),
        Field(name="lag_2",          dtype=Float64),
        Field(name="lag_3",          dtype=Float64),
        Field(name="lag_5",          dtype=Float64),
        Field(name="lag_7",          dtype=Float64),
        Field(name="lag_10",         dtype=Float64),
        Field(name="lag_14",         dtype=Float64),
        Field(name="lag_21",         dtype=Float64),
        Field(name="rolling_mean_5", dtype=Float64),
        Field(name="rolling_mean_10",dtype=Float64),
        Field(name="rolling_mean_21",dtype=Float64),
        Field(name="rolling_std_5",  dtype=Float64),
        Field(name="rolling_std_10", dtype=Float64),
        Field(name="rolling_std_21", dtype=Float64),
    ],
    online=True,
    source=lag_source,
)
```

**Key notes:**
- Import path for PostgreSQLSource is `feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source` — this is the contrib (community) path bundled with `feast[postgres]`.
- `timestamp_field` must point to a column name in the source table. The table needs a `timestamp` column with timezone-aware timestamps.
- `created_timestamp_column` enables deduplication when the same (ticker, timestamp) row is written multiple times (latest `created_at` wins).
- `ttl=timedelta(days=7)` means Feast will look back up to 7 days when performing point-in-time joins. Features older than 7 days relative to the entity_df event_timestamp will NOT be joined. Set to `timedelta(days=365)` for training over a year of data.
- `online=True` marks these FeatureViews as eligible for materialization into Redis.
- Feast uses the existing PostgreSQL database; tables `feast_ohlcv_stats`, `feast_technical_indicators`, `feast_lag_features` are **created by a population step** (separate from `feast apply`). `feast apply` only registers the metadata.

### Pattern 3: feast apply Mechanics

**What:** `feast apply` reads `feature_repo.py`, registers all objects with the registry, and provisions online store tables.

```bash
cd ml/feature_store
feast apply
```

**What feast apply creates in PostgreSQL (SQL registry):**
- Auto-creates tables: `entities`, `feature_views`, `feature_services`, `data_sources`, `saved_datasets`, `validation_references`, `managed_infra` in the `feast_` prefixed schema within the configured registry database.
- Does NOT create the source data tables (`feast_ohlcv_stats`, etc.) — those are data tables, not registry tables.
- Does NOT create anything in Redis (materialization does that).

**What feast apply creates in Redis:**
- Nothing. Redis population happens only on `feast materialize` or `feast materialize-incremental`.

**After feast apply, the SQL registry stores:**
- Serialized protobuf definitions of Entity, FeatureView, DataSource objects.
- Last materialization timestamps per FeatureView (watermarks used by `materialize-incremental`).

### Pattern 4: Point-in-Time Correct Historical Retrieval

**What:** `get_historical_features()` performs a temporal join: for each row in entity_df, it finds feature values with timestamp <= event_timestamp and within TTL window.

**entity_df format (required):**
```python
import pandas as pd
from datetime import datetime, timezone

# entity_df MUST have:
# 1. The entity join key column (matching Entity.join_keys — here "ticker")
# 2. An "event_timestamp" column (timezone-aware datetime)
entity_df = pd.DataFrame({
    "ticker": ["AAPL", "MSFT", "AAPL"],
    "event_timestamp": [
        datetime(2025, 1, 10, tzinfo=timezone.utc),
        datetime(2025, 1, 10, tzinfo=timezone.utc),
        datetime(2025, 1, 20, tzinfo=timezone.utc),
    ],
})
```

**Retrieval call:**
```python
from feast import FeatureStore

store = FeatureStore(repo_path="/app/ml/feature_store")
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "ohlcv_stats_fv:close",
        "ohlcv_stats_fv:daily_return",
        "technical_indicators_fv:rsi_14",
        "technical_indicators_fv:macd_line",
        "lag_features_fv:lag_1",
        "lag_features_fv:rolling_mean_5",
        # ... all needed features
    ],
).to_df()
```

**How point-in-time correctness works:**
For each (ticker, event_timestamp) row in entity_df, Feast executes a SQL query against the PostgreSQL offline store that finds the most recent feature row where `feature.timestamp <= entity_df.event_timestamp` (and within TTL). This prevents training data leakage — a model trained on data for 2025-01-10 will NOT see feature values computed after 2025-01-10.

**Source:** [docs.feast.dev/master/getting-started/concepts/point-in-time-joins](https://docs.feast.dev/master/getting-started/concepts/point-in-time-joins)

### Pattern 5: Online Feature Serving

**What:** `get_online_features()` hits Redis directly, returning latest materialized features in <5ms.

```python
from feast import FeatureStore

store = FeatureStore(repo_path="/app/ml/feature_store")
feature_vector = store.get_online_features(
    features=[
        "ohlcv_stats_fv:close",
        "ohlcv_stats_fv:daily_return",
        "technical_indicators_fv:rsi_14",
        "lag_features_fv:lag_1",
    ],
    entity_rows=[{"ticker": "AAPL"}],
).to_dict()
# Returns: {"ticker": ["AAPL"], "ohlcv_stats_fv__close": [182.5], ...}
```

**Latency characteristics:** Redis hash lookups are O(N) in number of fields, typically <1ms on LAN. The Python SDK adds serialization overhead; expect 1-5ms total per call.

**Redis storage format:** Feast uses Redis hashes keyed by `{project_name}:{entity_key}`. Each hash field is `{feature_view_name}:{feature_name}`. The value is a serialized protobuf.

### Pattern 6: Materialization — Populating Redis from PostgreSQL

**CLI (CronJob use):**
```bash
# Materialize all FeatureViews up to current time
feast -c /app/ml/feature_store materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")

# Materialize a specific time range (initial load)
feast -c /app/ml/feature_store materialize 2020-01-01T00:00:00 $(date -u +"%Y-%m-%dT%H:%M:%S")
```

**Python SDK (from application code):**
```python
import datetime
store.materialize_incremental(end_date=datetime.datetime.now(tz=datetime.timezone.utc))
```

**What materialize does:**
1. Reads from PostgreSQL (offline store / DataSource query) all rows since the last materialization watermark.
2. Writes the latest feature values per entity key to Redis.
3. Updates the materialization watermark in the SQL registry.

### Pattern 7: K8s Feature Server Deployment

**Docker image:** `feastdev/feature-server:0.61.0` (tag matches feast version)

**How the feature server works:**
- Runs `feast serve` internally.
- Listens on port **6566** (HTTP/JSON).
- Endpoint: `POST /get-online-features` (JSON body with feature names + entity rows).
- Health check: `GET /health`.
- Reads `feature_store.yaml` from a ConfigMap volume mount or base64-encoded env var.

**K8s Deployment sketch:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feast-feature-server
  namespace: ml
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: feature-server
          image: feastdev/feature-server:0.61.0
          ports:
            - containerPort: 6566
          env:
            - name: POSTGRES_HOST
              value: "postgresql.storage.svc.cluster.local"
            - name: POSTGRES_PORT
              value: "5432"
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: ml-pipeline-config
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: stock-platform-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: stock-platform-secrets
                  key: POSTGRES_PASSWORD
            - name: REDIS_HOST
              value: "redis.storage.svc.cluster.local"
            - name: REDIS_PORT
              value: "6379"
          volumeMounts:
            - name: feast-config
              mountPath: /app/ml/feature_store
          livenessProbe:
            httpGet:
              path: /health
              port: 6566
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 6566
            initialDelaySeconds: 10
            periodSeconds: 5
      volumes:
        - name: feast-config
          configMap:
            name: feast-feature-store-config
```

**Note:** The feature server image needs the `feature_store.yaml` accessible. Either mount it via ConfigMap or build a custom image extending `feastdev/feature-server` that bundles it. A ConfigMap approach is cleaner for GitOps.

### Pattern 8: Materialization CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: feast-materialize
  namespace: ml
spec:
  schedule: "30 23 * * 1-5"   # 18:30 ET = 23:30 UTC on weekdays
  timeZone: "UTC"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: feast-materialize
              image: stock-ml-pipeline:latest
              imagePullPolicy: Never
              command:
                - feast
                - -c
                - /app/ml/feature_store
                - materialize-incremental
                - "$(date -u +%Y-%m-%dT%H:%M:%S)"
              # OR use Python SDK:
              # command: ["python", "-m", "ml.feature_store.materialize"]
              env: ...  # same env vars as feature server
```

**Note on schedule:** 18:30 ET = 23:30 UTC in winter (EST, UTC-5), 22:30 UTC in summer (EDT, UTC-4). Use `timeZone: America/New_York` and `schedule: "30 18 * * 1-5"` to avoid DST ambiguity. Requires K8s 1.27+ for `timeZone` field (Minikube supports this).

### Recommended Project Structure (full)
```
ml/
├── feature_store/
│   ├── __init__.py
│   ├── feature_store.yaml       # Feast repo config
│   └── feature_repo.py          # Entity, DataSources, FeatureViews
├── features/
│   ├── store.py                  # KEEP existing EAV store (don't delete)
│   └── feast_store.py            # NEW: Feast wrapper functions
└── pipelines/
    └── components/
        └── feature_engineer.py   # UPDATE: add use_feast=True path
```

### Anti-Patterns to Avoid

- **Putting credentials in feature_store.yaml directly:** Use `${ENV_VAR}` syntax; never hardcode passwords.
- **Using file-based registry (`registry.db`) in K8s:** The file gets lost on pod restart. Use `registry_type: sql` with PostgreSQL for production.
- **Setting TTL too short for training:** If TTL is 1 day and entity_df has timestamps from 2024, features won't be found. Set TTL to `timedelta(days=365)` or `None` for training FeatureViews.
- **Confusing `feast apply` (registers metadata) with data population:** The source tables (`feast_ohlcv_stats`, etc.) must be populated separately before materialization. `feast apply` does NOT load data.
- **Not providing timezone-aware timestamps in entity_df:** Feast's PostgreSQL offline store requires timezone-aware `event_timestamp` values. Use `datetime(..., tzinfo=timezone.utc)`.
- **Calling `get_historical_features()` for real-time serving:** Use `get_online_features()` for inference (<5ms). `get_historical_features()` does a full SQL query — it is for training, not serving.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Point-in-time joins | Custom SQL with LATERAL JOIN or window functions | `feast.get_historical_features()` | Feast handles all edge cases: DST, late arrivals, duplicate rows, multi-source joins |
| Online key-value store schema | Custom Redis key naming and protobuf serialization | Feast Redis online store | Feast manages versioning, TTL, entity key encoding — subtle bugs in custom implementations |
| Materialization watermarks | Custom last-run timestamp table | Feast SQL registry | Registry tracks per-FeatureView watermarks; `materialize-incremental` uses them automatically |
| Feature server HTTP API | Custom FastAPI endpoint wrapping Redis reads | `feast serve` / `feastdev/feature-server` | Feast server handles authentication hooks, metrics, type coercion |
| Feature definition versioning | Git history + manual schema | Feast registry (SQL) | Registry provides point-in-time consistent feature definitions tied to each materialization |

**Key insight:** The existing `ml/features/store.py` hand-rolls all of the above. The EAV schema (ticker, date, feature_name, feature_value) is a single-table approach that makes point-in-time joins and online serving complex. Feast's wide-format DataSources and built-in join engine are dramatically simpler.

---

## Common Pitfalls

### Pitfall 1: numpy Version Conflict
**What goes wrong:** `feast==0.61.0` requires `numpy>=2.0.0` but `ml/requirements.txt` currently pins `numpy==1.26.4`. The install will fail or create an inconsistent environment.
**Why it happens:** Feast 0.61.0 was released March 2026 and adopts numpy 2.x API.
**How to avoid:** Update `ml/requirements.txt` to `numpy>=2.0.0` in Plan 66-01. Also verify scikit-learn, xgboost, lightgbm, catboost, shap are all numpy 2.x compatible (they are at the versions already pinned in the Decisions log: xgboost 3.2.0, lightgbm 4.6.0, catboost 1.2.10).
**Warning signs:** `pip install feast[postgres,redis]==0.61.0` raising dependency conflict on numpy.

### Pitfall 2: TTL Too Short for Training Data Retrieval
**What goes wrong:** `get_historical_features()` returns empty DataFrames or NaN columns for older training rows even though the data exists in PostgreSQL.
**Why it happens:** Feast's TTL is applied relative to each `event_timestamp` row in entity_df. If TTL is `timedelta(days=7)` and you request features for events 6 months ago, Feast won't look back far enough.
**How to avoid:** Use `ttl=timedelta(days=365)` (or longer) for training FeatureViews. TTL can be None for unlimited lookback but then there's no staleness protection.
**Warning signs:** `get_historical_features().to_df()` returns the entity_df columns but all feature columns are NaN.

### Pitfall 3: Missing event_timestamp in entity_df
**What goes wrong:** `store.get_historical_features(entity_df=...)` raises `ValueError: entity_df must have an "event_timestamp" column`.
**Why it happens:** The entity_df DataFrame requires exactly the column named `event_timestamp` (not `timestamp`, `date`, or `ts`).
**How to avoid:** Always build entity_df with an `event_timestamp` column containing timezone-aware datetimes. When converting training data, use `df.index.rename("event_timestamp")` or `df["event_timestamp"] = pd.to_datetime(df.index, utc=True)`.
**Warning signs:** The error message is explicit; will appear immediately on first call.

### Pitfall 4: feast apply Fails Due to Missing SQL Registry Tables
**What goes wrong:** `feast apply` errors on first run if the PostgreSQL database is not accessible or the user lacks CREATE TABLE privileges.
**Why it happens:** SQL registry auto-creates its tables on first `feast apply` call, which requires DDL permissions.
**How to avoid:** Ensure the `stockuser` Postgres user has CREATE TABLE rights in `stockdb` (or create the Feast registry in a dedicated `feast` schema). The existing `stock_writer` role should have sufficient privileges.
**Warning signs:** `sqlalchemy.exc.ProgrammingError: permission denied for schema public`.

### Pitfall 5: feast apply Finds No Feature Views
**What goes wrong:** `feast apply` runs silently but registers nothing because it can't find `feature_repo.py` objects.
**Why it happens:** Feast scans the `repo_path` directory for Python files and imports them. Objects must be at module top level (not inside functions or conditionals).
**How to avoid:** Define all Entity, DataSource, FeatureView objects at module top level in `feature_repo.py`. `feast apply` uses the directory of `feature_store.yaml` as the repo root.
**Warning signs:** Running `feast feature-views list` after apply shows empty list.

### Pitfall 6: Source Tables Must Exist Before Materialization
**What goes wrong:** `feast materialize-incremental` fails with SQL error because `feast_ohlcv_stats` table does not exist.
**Why it happens:** Feast's `feast apply` registers DataSource metadata but does NOT create the source tables. These tables must be created separately (Alembic migration or Postgres DDL).
**How to avoid:** Plan 66-01 must include Alembic migrations (or raw CREATE TABLE) for `feast_ohlcv_stats`, `feast_technical_indicators`, `feast_lag_features`. A data population script (wrapping existing `compute_features_for_ticker()`) writes into these wide-format tables.
**Warning signs:** `feast materialize` exits with `psycopg2.errors.UndefinedTable`.

### Pitfall 7: Redis Connection String for K8s
**What goes wrong:** Feast can't connect to Redis because `feature_store.yaml` has `localhost:6379` instead of the K8s service DNS.
**Why it happens:** `${REDIS_HOST}:${REDIS_PORT}` requires environment variables to be injected into the container.
**How to avoid:** Set `REDIS_HOST=redis.storage.svc.cluster.local` and `REDIS_PORT=6379` as env vars in both the feature server Deployment and the materialization CronJob. The `${ENV_VAR}` substitution in `feature_store.yaml` requires these vars to be present at runtime.
**Warning signs:** `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`.

---

## Code Examples

### feast_store.py — Feast Wrapper Module (new file)
```python
# ml/features/feast_store.py
# Source: https://docs.feast.dev/getting-started/quickstart
from __future__ import annotations
import os
import datetime
import pandas as pd
from feast import FeatureStore

FEAST_REPO_PATH = os.environ.get(
    "FEAST_REPO_PATH",
    os.path.join(os.path.dirname(__file__), "..", "feature_store"),
)

_TRAINING_FEATURES = [
    "ohlcv_stats_fv:open",
    "ohlcv_stats_fv:high",
    "ohlcv_stats_fv:low",
    "ohlcv_stats_fv:close",
    "ohlcv_stats_fv:volume",
    "ohlcv_stats_fv:daily_return",
    "ohlcv_stats_fv:vwap",
    "technical_indicators_fv:rsi_14",
    "technical_indicators_fv:macd_line",
    "technical_indicators_fv:macd_signal",
    "technical_indicators_fv:bb_upper",
    "technical_indicators_fv:bb_lower",
    "technical_indicators_fv:atr_14",
    "technical_indicators_fv:adx_14",
    "technical_indicators_fv:ema_20",
    "technical_indicators_fv:obv",
    "lag_features_fv:lag_1",
    "lag_features_fv:lag_2",
    "lag_features_fv:lag_3",
    "lag_features_fv:lag_5",
    "lag_features_fv:lag_7",
    "lag_features_fv:lag_10",
    "lag_features_fv:lag_14",
    "lag_features_fv:lag_21",
    "lag_features_fv:rolling_mean_5",
    "lag_features_fv:rolling_mean_10",
    "lag_features_fv:rolling_mean_21",
    "lag_features_fv:rolling_std_5",
    "lag_features_fv:rolling_std_10",
    "lag_features_fv:rolling_std_21",
]

_ONLINE_FEATURES = [
    "ohlcv_stats_fv:close",
    "ohlcv_stats_fv:daily_return",
    "technical_indicators_fv:rsi_14",
    "technical_indicators_fv:macd_line",
    "lag_features_fv:lag_1",
    "lag_features_fv:rolling_mean_5",
]


def get_store() -> FeatureStore:
    return FeatureStore(repo_path=FEAST_REPO_PATH)


def get_historical_features(entity_df: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time correct feature retrieval for training.

    entity_df must have columns: ticker (str), event_timestamp (datetime, UTC).
    """
    store = get_store()
    return store.get_historical_features(
        entity_df=entity_df,
        features=_TRAINING_FEATURES,
    ).to_df()


def get_online_features(ticker: str) -> dict:
    """Sub-millisecond feature retrieval from Redis for inference."""
    store = get_store()
    return store.get_online_features(
        features=_ONLINE_FEATURES,
        entity_rows=[{"ticker": ticker}],
    ).to_dict()
```

### feature_engineer.py — Updated use_feast Path
```python
# In engineer_features(), add new branch BEFORE use_feature_store check:
if use_feast:
    from ml.features.feast_store import get_historical_features
    import datetime
    # Build entity_df from data_dict keys + current timestamp
    rows = []
    for ticker, df in data.items():
        for ts in df.index:
            rows.append({
                "ticker": ticker,
                "event_timestamp": pd.Timestamp(ts, tz="UTC"),
            })
    entity_df = pd.DataFrame(rows)
    try:
        feast_df = get_historical_features(entity_df)
        # feast_df is a flat DataFrame; pivot back to per-ticker dict
        result = {}
        for ticker in data.keys():
            t_df = feast_df[feast_df["ticker"] == ticker].set_index("event_timestamp")
            t_df.index.name = "date"
            result[ticker] = t_df.drop(columns=["ticker"], errors="ignore")
        return result
    except Exception as exc:
        logger.warning("Feast get_historical_features failed (%s) — falling back.", exc)
        # falls through to existing on-the-fly path
```

### materialize.py — Python Materialization Script
```python
# ml/feature_store/materialize.py — used by CronJob as Python alternative to CLI
import datetime
from feast import FeatureStore

if __name__ == "__main__":
    store = FeatureStore(repo_path="/app/ml/feature_store")
    end = datetime.datetime.now(tz=datetime.timezone.utc)
    store.materialize_incremental(end_date=end)
    print(f"Materialization complete up to {end.isoformat()}")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| EAV feature_store table (ticker, date, feature_name, value) | Wide-format columnar tables per FeatureView | Feast 0.1+ | Point-in-time joins become SQL-native; no pivot overhead |
| `feast init` with default local provider | `feature_store.yaml` with `registry_type: sql` | Feast 0.26+ | Registry survives pod restarts; materialization watermarks persist |
| `FeatureStore.write_to_online_store()` API | `store.materialize_incremental()` or `PushSource` pattern | Feast 0.30+ | Push sources preferred for real-time; materialize-incremental for batch daily loads |
| `entity_key_serialization_version: 2` | `entity_key_serialization_version: 3` | Feast 0.26+ | Must use v3 in new repos to avoid deprecation warning |
| `feast serve` on bare metal | `feastdev/feature-server` Docker image on K8s | Feast 0.20+ | Pre-built image includes all deps; no custom Dockerfile needed |

**Deprecated/outdated:**
- `FeatureStore.write_to_online_store()`: Superseded by `PushSource` pattern for streaming writes and `materialize_incremental` for batch.
- File-based registry (`registry: data/registry.db`): Works for local dev, not suitable for K8s (file lost on pod restart).
- `provider: gcp` / `provider: aws`: Use `provider: local` for self-managed infrastructure (PostgreSQL + Redis in Minikube).

---

## Open Questions

1. **Feature population tables: DDL ownership**
   - What we know: `feast apply` does NOT create `feast_ohlcv_stats` etc. tables. These must be created separately.
   - What's unclear: Should these tables live in a separate `feast` schema in PostgreSQL, or in `public`? Should they use TimescaleDB hypertables (since they have time dimension)?
   - Recommendation: Use `public` schema initially (matches `db_schema: public` in feature_store.yaml). TimescaleDB hypertable conversion optional — adds range partitioning but Feast doesn't require it. Keep simple for Phase 66; Phase 67 (Flink) may convert them.

2. **numpy version bump impact on existing tests**
   - What we know: numpy must be bumped from 1.26.4 to >=2.0.0 for feast 0.61.0. Previous Decisions log shows shap 0.45.1 required a numba shim for numpy 2.x compatibility.
   - What's unclear: Whether upgrading numpy breaks existing `ml/tests/` suite.
   - Recommendation: Test the numpy bump in isolation in Plan 66-01. The Decisions log from Phase 13 shows xgboost 3.2.0 and lightgbm 4.6.0 were already upgraded for numpy 2.x compat. The shap numba shim is already in place.

3. **Feature server image: custom vs stock**
   - What we know: `feastdev/feature-server:0.61.0` is pre-built. It needs `feature_store.yaml` at a known path.
   - What's unclear: Does the stock image accept a ConfigMap-mounted YAML at `/app/ml/feature_store`?
   - Recommendation: Mount ConfigMap to the feature_repo path. If the stock image doesn't support this, build a thin custom image `FROM feastdev/feature-server:0.61.0` that copies `feature_store.yaml`. The `feast serve` entrypoint reads from `--chdir` or the current directory.

---

## Validation Architecture

nyquist_validation is enabled (`workflow.nyquist_validation: true` in .planning/config.json).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `stock-prediction-platform/ml/tests/pytest.ini` |
| Quick run command | `cd stock-prediction-platform && python -m pytest ml/tests/test_feast_store.py -x -p no:logfire` |
| Full suite command | `cd stock-prediction-platform && python -m pytest ml/tests/ -p no:logfire` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAST-01 | `feature_store.yaml` loads without error, FeatureStore instantiates | unit | `pytest ml/tests/test_feast_store.py::TestFeatureStoreConfig -x` | Wave 0 |
| FEAST-02 | Three FeatureViews registered after `feast apply` | unit | `pytest ml/tests/test_feast_definitions.py::TestFeatureViewDefinitions -x` | Wave 0 |
| FEAST-03 | `feast apply` exits 0, registry contains 3 FeatureViews | integration (mocked registry) | `pytest ml/tests/test_feast_apply.py::test_feast_apply_registers_views -x` | Wave 0 |
| FEAST-04 | `get_historical_features()` returns DataFrame with no future-data leakage | unit (mocked PG) | `pytest ml/tests/test_feast_store.py::TestHistoricalFeatures -x` | Wave 0 |
| FEAST-05 | `get_online_features()` returns dict with expected keys in <5ms | unit (mocked Redis) | `pytest ml/tests/test_feast_store.py::TestOnlineFeatures -x` | Wave 0 |
| FEAST-06 | `engineer_features(use_feast=True)` calls `get_historical_features` | unit | `pytest ml/tests/test_feature_engineer.py::TestFeastPath -x` | Wave 0 |
| FEAST-07 | Prediction service calls `get_online_features()` for inference | unit | `pytest services/api/tests/test_predict.py::TestFeastOnlineFeatures -x` | Wave 0 |
| FEAST-08 | CronJob manifest has correct schedule; feature server passes /health | manual smoke | `kubectl apply -f k8s/ml/cronjob-feast-materialize.yaml && kubectl get cronjob -n ml` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest ml/tests/test_feast_store.py -p no:logfire -x`
- **Per wave merge:** `pytest ml/tests/ -p no:logfire`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `ml/tests/test_feast_store.py` — covers FEAST-01, FEAST-04, FEAST-05 (unit, all mocked)
- [ ] `ml/tests/test_feast_definitions.py` — covers FEAST-02, FEAST-03 (validates feature_repo.py objects)
- [ ] `ml/tests/test_feature_engineer.py` additions — `TestFeastPath` class for FEAST-06
- [ ] `services/api/tests/test_predict.py` additions — mock feast online store for FEAST-07
- [ ] `ml/feature_store/__init__.py` — Feast repo directory marker
- [ ] Framework install note: `pip install 'feast[postgres,redis]==0.61.0'` — not yet in requirements

---

## Sources

### Primary (HIGH confidence)

- [PyPI feast 0.61.0](https://pypi.org/project/feast/) — version, Python compat, install extras confirmed
- [docs.feast.dev — PostgreSQL Offline Store](https://docs.feast.dev/reference/offline-stores/postgres) — offline_store config fields
- [docs.feast.dev — Redis Online Store](https://docs.feast.dev/reference/online-stores/redis) — connection_string format
- [docs.feast.dev — SQL Registry](https://docs.feast.dev/reference/registries/sql) — registry_type sql, SQLAlchemy path format
- [docs.feast.dev — Point-in-Time Joins](https://docs.feast.dev/master/getting-started/concepts/point-in-time-joins) — TTL mechanics, entity_df format
- [docs.feast.dev — Quickstart](https://docs.feast.dev/getting-started/quickstart) — Entity, FeatureView, Field, feast apply patterns
- [docs.feast.dev — Feast CLI Reference](https://docs.feast.dev/master/reference/feast-cli-commands) — materialize-incremental syntax
- [docs.feast.dev — Python Feature Server](https://docs.feast.dev/reference/feature-servers/python-feature-server) — port 6566, /health endpoint, feast serve

### Secondary (MEDIUM confidence)

- [docs.feast.dev — Running Feast in Production](https://docs.feast.dev/how-to-guides/running-feast-in-production) — ${ENV_VAR} substitution, K8s materialization strategy
- [docs.feast.dev — PostgreSQL DataSource](https://docs.feast.dev/reference/data-sources/postgres) — PostgreSQLSource import path, timestamp_field/created_timestamp_column
- [feast-dev/feast GitHub](https://github.com/feast-dev/feast) — feast types (Float64, Int64, String), feature_server image
- [oneuptime.com K8s Feast blog 2026-02](https://oneuptime.com/blog/post/2026-02-09-feast-feature-store-kubernetes/view) — port 6566, /health endpoint, env vars confirmed

### Tertiary (LOW confidence)

- [feast-dev/feast Helm chart README](https://github.com/feast-dev/feast/blob/master/infra/charts/feast-feature-server/README.md) — Helm chart reference for feature server image tag format
- [redis.io Feast tutorial](https://redis.io/blog/feast-with-redis-tutorial-for-machine-learning/) — Redis online store patterns

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyPI version confirmed (0.61.0, March 2026), Python 3.11 compat verified
- Architecture: HIGH — Official docs for all core APIs (feature_store.yaml, Entity, FeatureView, PostgreSQLSource)
- Pitfalls: HIGH — numpy conflict verified via pip dry-run; TTL mechanics from official docs; others from source code review
- K8s deployment: MEDIUM — Docker image tag convention from Helm chart; /health endpoint from blog post (not official docs)

**Research date:** 2026-03-29
**Valid until:** 2026-04-29 (Feast releases frequently; check for 0.62.x)
