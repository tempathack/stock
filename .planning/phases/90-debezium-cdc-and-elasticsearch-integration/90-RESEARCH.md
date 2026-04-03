# Phase 90: Debezium CDC and Elasticsearch Integration - Research

**Researched:** 2026-04-03
**Domain:** Debezium CDC / Strimzi KafkaConnect / Elasticsearch / FastAPI search / React search UI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Kafka Connect Deployment
- Use **Strimzi KafkaConnect CR** (operator-managed, K8s-native) — leverages existing Strimzi operator
- Deploy in **processing namespace** (alongside Flink jobs in `k8s/processing/`)
- Use **debezium/connect** as the base image — build a custom KafkaConnect image `FROM debezium/connect` for Strimzi
- Declare connectors as **KafkaConnector CRs** (Debezium PostgreSQL connector + ES Sink connector)
- CDC topic naming convention: `debezium.public.{table}` — standard Debezium format
  - `debezium.public.predictions`
  - `debezium.public.drift_logs`
  - `debezium.public.model_registry`

#### Elasticsearch Deployment
- **Plain K8s StatefulSet** (no ECK operator) — matches existing Redis/PostgreSQL deployment pattern
- **Elasticsearch 8.x**, `discovery.type=single-node`, `xpack.security.enabled=false` for dev
- Lives in **storage namespace** alongside PostgreSQL, Redis, MinIO (`k8s/storage/`)
- **10Gi PVC** for data persistence
- **Include Kibana** — K8s Deployment + Service in storage namespace, for debugging/ops visibility

#### Search API Surface
- **Separate endpoints per entity** in a new `/search` router (`app/routers/search.py`):
  - `GET /search/predictions` — filter by ticker, date range, model_id, confidence threshold + free-text hybrid
  - `GET /search/models` — filter by metric thresholds (R², RMSE, MAE, status)
  - `GET /search/drift-events` — filter by drift_type, severity, ticker, date range
  - `GET /search/stocks` — full-text on company_name, sector, industry
- All endpoints support **pagination**: `page` + `page_size` query params (default 50, max 500)
- `/search/predictions` supports **full-text + filter hybrid** (free-text on notes/metadata + structured field filters)
- Register `/search` router in `main.py` alongside existing routers

#### Frontend: New /search Page
- Add a new **`/search` page** (`services/frontend/src/pages/Search.tsx`)
- **Unified search box** at top with **tabbed results** below: Predictions / Models / Drift Events / Stocks
- Each tab shows a paginated results table with entity-specific columns
- Add `/search` to the sidebar navigation
- No changes to existing Analytics, Models, or Drift pages this phase

### Claude's Discretion
- Elasticsearch index mappings (field types, analyzers) — standard mappings are fine
- Debezium connector config details (slot name, snapshot mode, heartbeat interval)
- ES Sink connector transform config (flatten nested Debezium envelope)
- FastAPI elasticsearch-py client initialization and connection pooling
- Specific column definitions per tab on the /search page
- Kibana NodePort port number

### Deferred Ideas (OUT OF SCOPE)
- Analytics, Models, Drift page ES enhancements (metric threshold filters, ES health panel, drift search bar)
- ES alerting (Watcher / Kibana alerting) for drift event patterns
- Full-text search on OHLCV data or company news
- Multi-node Elasticsearch cluster
</user_constraints>

---

## Summary

Phase 90 wires PostgreSQL WAL changes into Elasticsearch via Debezium CDC on Strimzi KafkaConnect, then exposes a FastAPI `/search` router and a React `/search` page. There are five distinct infrastructure concerns: (1) enabling PostgreSQL logical replication, (2) building and deploying a custom KafkaConnect image containing the Debezium PostgreSQL connector and Confluent ES Sink connector as Strimzi plugins, (3) deploying Elasticsearch 8 and Kibana as plain K8s StatefulSet/Deployment in the storage namespace, (4) adding the FastAPI search service layer backed by `AsyncElasticsearch`, and (5) building the React Search page with tabbed results.

The biggest operational pitfall in this stack is the cross-namespace bootstrap address: KafkaConnect runs in `processing` but Kafka lives in `storage`. The bootstrap server must be the fully-qualified service DNS name `kafka-kafka-bootstrap.storage.svc.cluster.local:9092`. The second significant pitfall is PostgreSQL WAL configuration: `wal_level=logical` is NOT set in the current `storage-config` ConfigMap and must be injected via a new `postgresql.conf`-style command-arg or ConfigMap key before Debezium can connect.

**Primary recommendation:** Build the Strimzi KafkaConnect image using Strimzi's native `spec.build` (maven artifact type for both connector JARs), deploy KafkaConnect in `processing` namespace with bootstrap pointing to `kafka-kafka-bootstrap.storage.svc.cluster.local:9092`, use `io.debezium.transforms.ExtractNewRecordState` SMT to flatten the CDC envelope before the ES Sink connector writes documents, and use `AsyncElasticsearch` (elasticsearch-py 8.x) with lifespan-managed connection in FastAPI.

---

## Standard Stack

### Core
| Library / Component | Version | Purpose | Why Standard |
|---------------------|---------|---------|--------------|
| debezium/connect | 2.7.x (latest) | Base image for KafkaConnect with PostgreSQL connector bundled | Official Debezium image, pgoutput plugin built-in |
| kafka-connect-elasticsearch (Confluent) | 14.x | ES Sink connector artifact | Official Confluent maintained, ES 8.x compatible |
| elasticsearch (Python) | 8.19.3 | FastAPI client | Matches ES 8.x server, `AsyncElasticsearch` built-in |
| Elasticsearch | 8.13+ | Search / index store | Stable 8.x GA, `xpack.security.enabled=false` for dev |
| Kibana | 8.x (match ES) | Index browser / ops | Must match ES major version exactly |
| Strimzi KafkaConnect CR | existing operator | Operator-managed Connect cluster | Already installed, no new operator needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| elasticsearch[async] extra | 8.19.3 | Async transport for asyncio | Required for FastAPI; install as `elasticsearch[async]` to pull aiohttp |
| aiohttp | latest compatible | Async HTTP transport | Pulled transitively by elasticsearch[async] |
| @tanstack/react-query | ^5.62.0 (existing) | Data fetching for search page | Already in project — reuse pattern |
| @mui/x-data-grid | ^8.28.1 (existing) | Paginated results tables | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Strimzi build spec | Pre-built custom image pushed to registry manually | Strimzi build is K8s-native and reproducible; manual image management is error-prone in Minikube |
| Confluent ES Sink | Debezium's own ES sink | Confluent's connector is more actively maintained for ES 8.x; Debezium's direct ES sink is less common |
| AsyncElasticsearch | synchronous Elasticsearch | Synchronous blocks FastAPI event loop; async is the correct choice |

**Installation (API):**
```bash
pip install "elasticsearch[async]==8.19.3"
```

**Version verification (confirmed against PyPI 2026-04-03):**
- `elasticsearch`: latest stable 9.3.0 (targets ES 9.x). Use `elasticsearch==8.19.3` to match ES 8.x server. The 8.x client series is maintained for ES 8.x servers.

---

## Architecture Patterns

### Recommended File Structure
```
k8s/
├── storage/
│   ├── elasticsearch-statefulset.yaml   # ES 8 StatefulSet + Service
│   ├── elasticsearch-pvc.yaml           # 10Gi PVC
│   ├── elasticsearch-configmap.yaml     # ES env vars
│   ├── kibana-deployment.yaml           # Kibana Deployment + NodePort Service
│   └── kibana-configmap.yaml            # ELASTICSEARCH_HOSTS env var
└── processing/
    ├── kafka-connect-build.yaml         # KafkaConnect CR with spec.build plugins
    ├── kafka-connect-connector-pg.yaml  # KafkaConnector CR: Debezium PostgreSQL
    ├── kafka-connect-connector-es.yaml  # KafkaConnector CR: ES Sink
    └── kafka-topics-cdc.yaml            # KafkaTopic CRs for 3 CDC topics

services/api/
├── app/
│   ├── routers/
│   │   └── search.py                    # APIRouter(prefix="/search")
│   ├── services/
│   │   └── elasticsearch_service.py     # AsyncElasticsearch + search logic
│   ├── models/
│   │   └── schemas.py                   # SearchResponse Pydantic models (append)
│   └── config.py                        # Add ELASTICSEARCH_URL, KIBANA_URL

services/frontend/src/
├── pages/
│   └── Search.tsx                       # New search page
├── api/
│   └── search.ts                        # React Query hooks for search endpoints
└── App.tsx                              # Add /search route
```

### Pattern 1: Strimzi KafkaConnect with spec.build (maven artifacts)

**What:** Strimzi operator builds the KafkaConnect Docker image at apply time, pulling connector JARs from Maven Central and pushing to a registry. No manual Dockerfile required.

**When to use:** When no pre-built image is available; Strimzi operator is already running; development environment uses a local registry.

**Key detail for Minikube:** Strimzi's `spec.build.output.type: docker` requires a registry. Use Minikube's built-in registry addon (`minikube addons enable registry`) or `eval $(minikube docker-env)` and push manually, then use `spec.image` instead of `spec.build` to skip the build phase.

**Recommended approach for Minikube (no build-time registry):** Build the image outside Strimzi using a Dockerfile, load it into Minikube with `minikube image load`, then reference it via `spec.image` in the KafkaConnect CR with `imagePullPolicy: Never`.

```yaml
# k8s/processing/kafka-connect-build.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnect
metadata:
  name: debezium-connect
  namespace: processing
  annotations:
    strimzi.io/use-connector-resources: "true"
spec:
  version: 3.7.0
  replicas: 1
  bootstrapServers: kafka-kafka-bootstrap.storage.svc.cluster.local:9092
  image: debezium-connect-custom:latest    # pre-built image, loaded via minikube image load
  config:
    group.id: debezium-connect-cluster
    offset.storage.topic: debezium-connect-offsets
    config.storage.topic: debezium-connect-configs
    status.storage.topic: debezium-connect-status
    config.storage.replication.factor: 1
    offset.storage.replication.factor: 1
    status.storage.replication.factor: 1
  resources:
    requests:
      memory: 512Mi
      cpu: "500m"
    limits:
      memory: 1Gi
      cpu: "1"
  template:
    pod:
      imagePullPolicy: Never
```

**Custom Dockerfile (for local minikube image load):**
```dockerfile
FROM debezium/connect:2.7
# ES Sink connector — download confluent kafka-connect-elasticsearch jar
USER root
RUN curl -L https://packages.confluent.io/maven/io/confluent/kafka-connect-elasticsearch/14.2.0/kafka-connect-elasticsearch-14.2.0.jar \
    -o /kafka/connect/elasticsearch/kafka-connect-elasticsearch-14.2.0.jar
USER kafka
```

### Pattern 2: KafkaConnector CR for Debezium PostgreSQL Source

```yaml
# k8s/processing/kafka-connect-connector-pg.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: debezium-postgres-source
  namespace: processing
  labels:
    strimzi.io/cluster: debezium-connect
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    database.hostname: postgresql.storage.svc.cluster.local
    database.port: "5432"
    database.user: stockuser
    database.password: "${file:/opt/kafka/external-configuration/connector-secrets/POSTGRES_PASSWORD}"
    database.dbname: stockdb
    database.server.name: debezium
    topic.prefix: debezium
    plugin.name: pgoutput
    publication.name: dbz_publication
    slot.name: debezium_slot
    snapshot.mode: initial
    table.include.list: "public.predictions,public.drift_logs,public.model_registry"
    heartbeat.interval.ms: "10000"
    transforms: unwrap
    transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState
    transforms.unwrap.drop.tombstones: "false"
    transforms.unwrap.delete.handling.mode: rewrite
    transforms.unwrap.add.fields: "op,ts_ms"
```

**Key config notes:**
- `topic.prefix: debezium` + table name → topics `debezium.public.predictions` etc.
- `plugin.name: pgoutput` — native PostgreSQL 10+ plugin, no extra extensions needed
- `transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState` — the correct current SMT class name (NOT `UnwrapFromEnvelope`, which is deprecated)
- `transforms.unwrap.delete.handling.mode: rewrite` — preserves delete events with `__deleted` field instead of dropping them
- Connector secret injection via Strimzi's `externalConfiguration` volume mount

### Pattern 3: KafkaConnector CR for Elasticsearch Sink

```yaml
# k8s/processing/kafka-connect-connector-es.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: es-sink-connector
  namespace: processing
  labels:
    strimzi.io/cluster: debezium-connect
spec:
  class: io.confluent.connect.elasticsearch.ElasticsearchSinkConnector
  tasksMax: 1
  config:
    topics: "debezium.public.predictions,debezium.public.drift_logs,debezium.public.model_registry"
    connection.url: http://elasticsearch.storage.svc.cluster.local:9200
    type.name: _doc
    key.ignore: "false"
    schema.ignore: "true"
    behavior.on.null.values: delete
    batch.size: "100"
    linger.ms: "1000"
    index.name.format: "${topic}"
```

### Pattern 4: Elasticsearch StatefulSet

Follow `redis-deployment.yaml` and `postgresql-deployment.yaml` patterns exactly:
- `StatefulSet` (not Deployment) for stable identity
- `xpack.security.enabled=false` and `discovery.type=single-node` via env vars
- Init container: `busybox chown -R 1000:1000 /usr/share/elasticsearch/data` to fix permissions
- Ports: 9200 (HTTP REST), 9300 (inter-node — unused in single-node but required)
- PVC: 10Gi, `ReadWriteOnce`

```yaml
# Env vars pattern for ES StatefulSet container
env:
  - name: discovery.type
    value: single-node
  - name: xpack.security.enabled
    value: "false"
  - name: ES_JAVA_OPTS
    value: "-Xms512m -Xmx512m"   # critical for Minikube memory constraints
  - name: cluster.name
    value: stock-platform-es
```

**Critical Minikube note:** ES 8.x requires `vm.max_map_count=262144`. Must set via `minikube ssh "sudo sysctl -w vm.max_map_count=262144"` or an init DaemonSet. Without this, the ES pod crashes with bootstrap check failure.

### Pattern 5: AsyncElasticsearch in FastAPI

```python
# services/api/app/services/elasticsearch_service.py
from elasticsearch import AsyncElasticsearch

_es_client: AsyncElasticsearch | None = None

def get_es_client() -> AsyncElasticsearch:
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL],
            connections_per_node=5,
        )
    return _es_client

async def close_es_client() -> None:
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None
```

Initialize in `main.py` lifespan alongside Redis — call `close_es_client()` in shutdown.

### Pattern 6: FastAPI search router (mirrors analytics.py)

```python
# services/api/app/routers/search.py
from fastapi import APIRouter, Query
from app.cache import build_key, cache_get, cache_set
from app.services.elasticsearch_service import search_predictions, search_models, search_drift_events, search_stocks
from app.models.schemas import (
    PredictionSearchResponse, ModelSearchResponse,
    DriftEventSearchResponse, StockSearchResponse
)

router = APIRouter(prefix="/search", tags=["search"])
SEARCH_TTL = 30   # 30s cache — search results change with CDC writes

@router.get("/predictions", response_model=PredictionSearchResponse)
async def search_predictions_endpoint(
    q: str | None = Query(None),
    ticker: str | None = None,
    model_id: int | None = None,
    confidence_min: float | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> PredictionSearchResponse:
    key = build_key("search", "predictions", q, ticker, model_id, confidence_min, date_from, date_to, page, page_size)
    cached = await cache_get(key)
    if cached is not None:
        return PredictionSearchResponse(**cached)
    result = await search_predictions(q=q, ticker=ticker, ...)
    await cache_set(key, result.model_dump(), SEARCH_TTL)
    return result
```

### Pattern 7: React Search Page Structure

Mirrors `Models.tsx` exactly:
- `Container maxWidth="xl"` + `PageHeader`
- MUI `Tabs` + `TabPanel` — one tab per entity (Predictions / Models / Drift Events / Stocks)
- Each tab: `DataGrid` from `@mui/x-data-grid` with pagination
- React Query `useQuery` hook per tab, keys include active tab + search params
- Sidebar: add `SearchIcon` entry to `navItems` array in `Sidebar.tsx`
- App.tsx: add lazy-loaded `<Route path="search" element={<Search />} />`

### Anti-Patterns to Avoid

- **Using synchronous `Elasticsearch` client in FastAPI** — blocks the event loop; always use `AsyncElasticsearch`
- **Deploying KafkaConnect in `storage` namespace** — must be in `processing` per decision; bootstrap uses FQDN to cross namespaces
- **Using old `UnwrapFromEnvelope` SMT class** — deprecated; use `io.debezium.transforms.ExtractNewRecordState`
- **Forgetting `strimzi.io/use-connector-resources: "true"` annotation** — without this, KafkaConnector CRs are ignored by the operator
- **Using `wal_level=replica` (default)** — Debezium requires `wal_level=logical`; the current PostgreSQL ConfigMap does NOT set this
- **Not setting `vm.max_map_count`** — ES 8.x crashes silently (CrashLoopBackOff) on Minikube without this kernel parameter
- **Mismatching Kibana and ES versions** — Kibana must match the ES major version; both must be `8.x`
- **Using `type: docker` in KafkaConnect build on Minikube without a push-accessible registry** — Strimzi's build mechanism requires pushing the image somewhere; use `spec.image` + `minikube image load` instead

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Debezium CDC envelope flattening | Custom Kafka Streams job to transform events | `io.debezium.transforms.ExtractNewRecordState` SMT | Complex edge cases: tombstones, DELETE handling, schema evolution |
| PostgreSQL CDC event capture | psycopg2 LISTEN/NOTIFY polling | Debezium PostgreSQL connector | WAL-based streaming handles schema changes, transactions, ordering |
| Elasticsearch index management | Custom index creation scripts | Let ES Sink connector create indices on first write | Connector handles mapping creation; override with explicit index templates only when needed |
| Async ES connection pooling | Custom aiohttp session management | `AsyncElasticsearch(connections_per_node=N)` | Built-in connection pool with retry, sniffing, and proper cleanup |
| Search pagination | Manual offset/limit SQL | ES `from` + `size` with `search_after` for deep pagination | `search_after` avoids deep-pagination performance cliff |

**Key insight:** Debezium + Kafka Connect SMTs handle the entire CDC-to-sink pipeline declaratively via connector config. Custom streaming code for this problem always misses edge cases (DDL changes, replication slot cleanup, at-least-once delivery).

---

## Common Pitfalls

### Pitfall 1: PostgreSQL wal_level Not Set to Logical
**What goes wrong:** Debezium connector fails to start with `ERROR: logical replication not enabled`. The connector pod appears healthy but the KafkaConnector CR shows `FAILED` status.
**Why it happens:** PostgreSQL defaults to `wal_level=replica`. Debezium requires `wal_level=logical` for the `pgoutput` plugin. The current `storage-config` ConfigMap only sets `POSTGRES_DB`, `POSTGRES_USER`, `PGDATA` — no WAL configuration.
**How to avoid:** Add command-line arguments to the PostgreSQL Deployment container: `args: ["-c", "wal_level=logical", "-c", "max_replication_slots=5", "-c", "max_wal_senders=5"]`. Changes require a PostgreSQL pod restart. Existing data is preserved via PVC.
**Warning signs:** `KafkaConnector` CR status shows connector state `FAILED`; Debezium pod logs contain `ERROR: logical replication not enabled`.

### Pitfall 2: vm.max_map_count Too Low for Elasticsearch
**What goes wrong:** ES pod enters `CrashLoopBackOff`. Logs show `max virtual memory areas vm.max_map_count [65530] is too low`.
**Why it happens:** Elasticsearch 8.x requires `vm.max_map_count >= 262144` at the OS/kernel level. Minikube's default VM does not set this.
**How to avoid:** Run `minikube ssh "sudo sysctl -w vm.max_map_count=262144"` before applying ES manifests. Add to `setup-minikube.sh`. Alternatively, use an init container with `privileged: true` that calls `sysctl`.
**Warning signs:** ES StatefulSet pod never reaches `Running`; `kubectl logs` on the ES pod shows the max_map_count error.

### Pitfall 3: KafkaConnect Namespace vs Bootstrap Address
**What goes wrong:** KafkaConnect pod starts but cannot connect to Kafka; `WARN Broker may not be available`.
**Why it happens:** KafkaConnect is in `processing` namespace; Kafka bootstrap service is in `storage` namespace. Using the short name `kafka-kafka-bootstrap:9092` resolves within the `processing` namespace only — which has no Kafka service.
**How to avoid:** Always use the fully-qualified name: `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` in `spec.bootstrapServers`.
**Warning signs:** KafkaConnect pod running but no consumer group appears in Kafka; connector status stuck at `UNASSIGNED`.

### Pitfall 4: Strimzi KafkaConnector CR Ignored
**What goes wrong:** KafkaConnector CRs are applied but connectors never appear in the Connect REST API.
**Why it happens:** The `strimzi.io/use-connector-resources: "true"` annotation must be on the **KafkaConnect** CR (not the KafkaConnector CRs). Without it, the Strimzi operator does not reconcile KafkaConnector resources.
**How to avoid:** Add `annotations: strimzi.io/use-connector-resources: "true"` to `metadata.annotations` of the `KafkaConnect` CR.
**Warning signs:** `kubectl get kafkaconnector -n processing` shows resources but `GET /connectors` on the Connect REST API returns empty list.

### Pitfall 5: CDC Topics Require Explicit KafkaTopic CRs
**What goes wrong:** Debezium auto-creates topics but they use default replication factor (which may mismatch single-broker config), or Strimzi's topic operator detects an unmanaged topic and conflicts.
**Why it happens:** Strimzi's topic operator manages topic lifecycle. Auto-created topics bypass the operator.
**How to avoid:** Pre-create all 3 CDC topics as KafkaTopic CRs in the `storage` namespace before starting the connector, with `replicas: 1` matching the single-broker setup (same pattern as existing `kafka-topics.yaml`). Also pre-create connector internal topics: `debezium-connect-offsets`, `debezium-connect-configs`, `debezium-connect-status`.

### Pitfall 6: Elasticsearch-py 9.x Incompatible With ES 8.x Server
**What goes wrong:** `elasticsearch.exceptions.UnsupportedProductError: The client noticed that the server is not Elasticsearch and we do not support this software`.
**Why it happens:** The latest `elasticsearch` PyPI package is 9.3.x which targets ES 9.x. ES 8.x returns version headers that cause the 9.x client to reject the connection.
**How to avoid:** Pin `elasticsearch==8.19.3` in requirements.txt (latest 8.x release as of 2026-04-03).
**Warning signs:** FastAPI startup logs show connection errors to ES despite ES pod being healthy.

### Pitfall 7: Debezium SMT Class Name Changed
**What goes wrong:** Connector fails with `ClassNotFoundException: io.debezium.transforms.UnwrapFromEnvelope`.
**Why it happens:** The old `UnwrapFromEnvelope` SMT was deprecated and renamed to `ExtractNewRecordState` in Debezium 1.x+. Many blog posts and older docs still reference the old name.
**How to avoid:** Always use `transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState`.

---

## Code Examples

### Elasticsearch Index Mapping for predictions Index

```json
{
  "mappings": {
    "properties": {
      "ticker":           { "type": "keyword" },
      "prediction_date":  { "type": "date" },
      "predicted_date":   { "type": "date" },
      "predicted_price":  { "type": "float" },
      "model_name":       { "type": "keyword" },
      "confidence":       { "type": "float" },
      "horizon_days":     { "type": "integer" },
      "__op":             { "type": "keyword" },
      "__ts_ms":          { "type": "date" }
    }
  }
}
```

### AsyncElasticsearch Hybrid Query (predictions)

```python
# Source: elasticsearch-py 8.x docs (www.elastic.co/guide/en/elasticsearch/client/python-api/8.19/async.html)
async def search_predictions(
    *,
    q: str | None,
    ticker: str | None,
    confidence_min: float | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    page_size: int,
) -> dict:
    client = get_es_client()
    must_clauses = []
    filter_clauses = []

    if q:
        must_clauses.append({"multi_match": {"query": q, "fields": ["*"]}})
    if ticker:
        filter_clauses.append({"term": {"ticker": ticker}})
    if confidence_min is not None:
        filter_clauses.append({"range": {"confidence": {"gte": confidence_min}}})
    if date_from or date_to:
        range_filter = {}
        if date_from:
            range_filter["gte"] = date_from
        if date_to:
            range_filter["lte"] = date_to
        filter_clauses.append({"range": {"prediction_date": range_filter}})

    body = {
        "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
        "from": (page - 1) * page_size,
        "size": page_size,
    }
    response = await client.search(index="debezium.public.predictions", body=body)
    return response
```

### React Search Page Structure

```typescript
// services/frontend/src/pages/Search.tsx — pattern mirrors Models.tsx
import { useState } from "react";
import { Container, Tabs, Tab, Box, TextField } from "@mui/material";
import { PageHeader } from "@/components/layout";
import { useSearchPredictions, useSearchModels, useSearchDriftEvents, useSearchStocks } from "@/api/search";

export default function Search() {
  const [activeTab, setActiveTab] = useState(0);
  const [query, setQuery] = useState("");
  // ...
  return (
    <Container maxWidth="xl">
      <PageHeader title="Search" subtitle="Search predictions, models, drift events, and stocks" />
      <TextField value={query} onChange={(e) => setQuery(e.target.value)} label="Search..." fullWidth />
      <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
        <Tab label="Predictions" />
        <Tab label="Models" />
        <Tab label="Drift Events" />
        <Tab label="Stocks" />
      </Tabs>
      {/* TabPanel per entity with DataGrid */}
    </Container>
  );
}
```

### Sidebar navItem Addition

```typescript
// services/frontend/src/components/layout/Sidebar.tsx — append to navItems array
import SearchIcon from "@mui/icons-material/Search";
// ...
const navItems = [
  // existing items...
  { to: "/search", label: "Search", Icon: SearchIcon },
];
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `UnwrapFromEnvelope` SMT | `ExtractNewRecordState` SMT | Debezium 1.x | Old class throws ClassNotFoundException |
| `wal2json` plugin | `pgoutput` plugin | PostgreSQL 10+ / Debezium 1.7+ | pgoutput is built-in, no extension install needed |
| Elasticsearch 7.x `type.name` mappings | Typeless mappings in ES 8 | ES 8.0 | `type.name: _doc` is the only valid value; types are removed |
| Manual KafkaConnect Docker builds | Strimzi `spec.build` | Strimzi 0.24+ | Declarative, operator-managed; skip for Minikube (use image load) |
| `elasticsearch<8` Python client | `elasticsearch==8.x` | 2022 | Major API change; 9.x client does not work against 8.x server |

**Deprecated/outdated:**
- `io.debezium.transforms.UnwrapFromEnvelope`: removed; use `io.debezium.transforms.ExtractNewRecordState`
- Multi-type Elasticsearch mappings: removed in ES 8; all docs use `_doc`
- `wal2json` extension: still works but `pgoutput` is preferred (no extension install)

---

## Open Questions

1. **Strimzi operator watch scope**
   - What we know: Strimzi is deployed in `storage` namespace and likely watches `storage` only by default
   - What's unclear: Whether the operator's `watchNamespaces` includes `processing` — if not, KafkaConnect CR in `processing` will not be reconciled
   - Recommendation: Check `kubectl get deployment strimzi-cluster-operator -n storage -o yaml | grep WATCH_NAMESPACE`. If only `storage`, either add `processing` to watch list or deploy KafkaConnect CR in `storage` namespace (and adjust the locked decision — but that's a user-locked choice)

2. **PostgreSQL logical replication slot cleanup**
   - What we know: Debezium creates a replication slot `debezium_slot` that retains WAL indefinitely during outages
   - What's unclear: Whether disk space pressure on the storage PVC will cause issues during development
   - Recommendation: Set `heartbeat.interval.ms=10000` and monitor PVC usage; add `slot.drop.on.stop: false` (default) for dev safety

3. **Minikube image registry strategy**
   - What we know: Strimzi `spec.build` requires a push-accessible registry; `minikube image load` bypasses this
   - What's unclear: Whether the Strimzi operator version installed supports `spec.image` override without a build spec
   - Recommendation: Check Strimzi operator version via `kubectl get deployment strimzi-cluster-operator -n storage -o jsonpath='{.spec.template.spec.containers[0].image}'`. All Strimzi versions since 0.20 support `spec.image`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing, services/api/tests/) |
| Config file | `services/api/pytest.ini` or `pyproject.toml` — check existing |
| Quick run command | `cd stock-prediction-platform/services/api && pytest tests/test_search_router.py -x` |
| Full suite command | `cd stock-prediction-platform/services/api && pytest tests/ -x` |

### Phase Requirements → Test Map
| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|--------------|
| `/search/predictions` returns paginated ES results | unit (mock ES client) | `pytest tests/test_search_router.py::test_search_predictions -x` | Wave 0 |
| `/search/models` filters by metric thresholds | unit (mock ES client) | `pytest tests/test_search_router.py::test_search_models -x` | Wave 0 |
| `/search/drift-events` filters by severity + type | unit (mock ES client) | `pytest tests/test_search_router.py::test_search_drift_events -x` | Wave 0 |
| `/search/stocks` full-text search | unit (mock ES client) | `pytest tests/test_search_router.py::test_search_stocks -x` | Wave 0 |
| `elasticsearch_service` builds correct ES query | unit | `pytest tests/test_elasticsearch_service.py -x` | Wave 0 |
| ES client closes on app shutdown (lifespan) | unit | `pytest tests/test_search_router.py::test_lifespan_closes_es -x` | Wave 0 |
| K8s manifests YAML valid | lint (manual) | `kubectl apply --dry-run=client -f k8s/storage/elasticsearch-statefulset.yaml` | manual |
| CDC topics created with correct config | manual K8s check | `kubectl get kafkatopic -n storage` | manual |
| KafkaConnector shows RUNNING state | manual K8s check | `kubectl get kafkaconnector -n processing` | manual |
| ES index receives CDC documents | manual smoke | Kibana DevTools GET index | manual |
| /search page renders with tabs in browser | Playwright | Playwright MCP browser_navigate + snapshot | Wave 3 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_search_router.py tests/test_elasticsearch_service.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green + Playwright browser verification before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_search_router.py` — search endpoint unit tests with mocked AsyncElasticsearch
- [ ] `tests/test_elasticsearch_service.py` — query builder unit tests
- [ ] `tests/conftest.py` update — add `mock_es_client` fixture using `AsyncMock`

---

## Sources

### Primary (HIGH confidence)
- debezium.io/documentation/reference/stable/connectors/postgresql.html — Debezium PostgreSQL connector config, pgoutput plugin, SMT class names
- debezium.io/documentation/reference/stable/transformations/event-flattening.html — ExtractNewRecordState SMT
- strimzi.io/docs/operators/latest/configuring.html — KafkaConnect CR spec, bootstrapServers, build spec
- github.com/strimzi/strimzi-kafka-operator/blob/main/examples/connect/kafka-connect-build.yaml — build spec with maven artifacts
- elasticsearch-py.readthedocs.io (current) — AsyncElasticsearch API, connection pool, lifespan pattern
- PyPI (verified 2026-04-03) — elasticsearch 8.19.3 is latest 8.x stable; 9.3.0 is latest overall
- Existing project code (directly read): kafka-cluster.yaml, redis-deployment.yaml, postgresql-deployment.yaml, analytics.py, config.py, main.py, App.tsx, Sidebar.tsx

### Secondary (MEDIUM confidence)
- docs.confluent.io/kafka-connectors/elasticsearch/current/ — ES Sink connector configuration, ES 8.x compatibility
- strimzi.io/blog/2021/03/29/connector-build/ — KafkaConnect build spec patterns
- WebSearch: cross-namespace bootstrap server FQDN format
- WebSearch: vm.max_map_count requirement for ES 8 on Minikube

### Tertiary (LOW confidence)
- WebSearch: Kibana + ES version matching requirements (standard practice, low risk)
- WebSearch: Confluent ES Sink connector JAR download URL (verify actual URL before use)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against PyPI, ES 8.x + Debezium 2.7 are current stable
- Architecture patterns: HIGH — directly derived from existing project code + official docs
- Pitfalls: HIGH for wal_level/vm.max_map_count (well-documented); MEDIUM for Strimzi watch namespace (needs env check)
- K8s manifests: HIGH — follows existing patterns exactly
- Frontend: HIGH — mirrors existing React patterns 1:1

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (30 days — stable domain; Strimzi/Debezium minor versions may update)
