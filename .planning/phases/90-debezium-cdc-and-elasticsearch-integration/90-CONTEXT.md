# Phase 90: Debezium CDC and Elasticsearch Integration - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy Debezium Connect + Elasticsearch as Kubernetes workloads in Minikube. Capture PostgreSQL WAL changes for `predictions`, `drift_logs`, and `model_registry` tables → Kafka CDC topics → Elasticsearch via Kafka Connect ES Sink Connector. Expose FastAPI `/search/*` endpoints (separate per entity). Add a new React `/search` page with unified search box and tabbed results. All infrastructure follows existing K8s manifest patterns (StatefulSet/Deployment + Service + ConfigMap + PVC).

Frontend scope is limited to the new `/search` page only — existing Analytics, Models, and Drift pages are NOT modified this phase.

</domain>

<decisions>
## Implementation Decisions

### Kafka Connect Deployment
- Use **Strimzi KafkaConnect CR** (operator-managed, K8s-native) — leverages existing Strimzi operator
- Deploy in **processing namespace** (alongside Flink jobs in `k8s/processing/`)
- Use **debezium/connect** as the base image — build a custom KafkaConnect image `FROM debezium/connect` for Strimzi
- Declare connectors as **KafkaConnector CRs** (Debezium PostgreSQL connector + ES Sink connector)
- CDC topic naming convention: `debezium.public.{table}` — standard Debezium format
  - `debezium.public.predictions`
  - `debezium.public.drift_logs`
  - `debezium.public.model_registry`

### Elasticsearch Deployment
- **Plain K8s StatefulSet** (no ECK operator) — matches existing Redis/PostgreSQL deployment pattern
- **Elasticsearch 8.x**, `discovery.type=single-node`, `xpack.security.enabled=false` for dev
- Lives in **storage namespace** alongside PostgreSQL, Redis, MinIO (`k8s/storage/`)
- **10Gi PVC** for data persistence
- **Include Kibana** — K8s Deployment + Service in storage namespace, for debugging/ops visibility

### Search API Surface
- **Separate endpoints per entity** in a new `/search` router (`app/routers/search.py`):
  - `GET /search/predictions` — filter by ticker, date range, model_id, confidence threshold + free-text hybrid
  - `GET /search/models` — filter by metric thresholds (R², RMSE, MAE, status)
  - `GET /search/drift-events` — filter by drift_type, severity, ticker, date range
  - `GET /search/stocks` — full-text on company_name, sector, industry
- All endpoints support **pagination**: `page` + `page_size` query params (default 50, max 500)
- `/search/predictions` supports **full-text + filter hybrid** (free-text on notes/metadata + structured field filters)
- Register `/search` router in `main.py` alongside existing routers

### Frontend: New /search Page
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing K8s deployment patterns
- `stock-prediction-platform/k8s/storage/redis-deployment.yaml` — StatefulSet/Deployment + Service + ConfigMap pattern to follow for ES
- `stock-prediction-platform/k8s/storage/postgresql-deployment.yaml` — PVC + Deployment pattern
- `stock-prediction-platform/k8s/storage/postgresql-pvc.yaml` — PVC spec pattern

### Existing Kafka/Strimzi patterns
- `stock-prediction-platform/k8s/kafka/kafka-cluster.yaml` — Strimzi Kafka CR, basis for KafkaConnect CR
- `stock-prediction-platform/k8s/kafka/kafka-topics.yaml` — KafkaTopic CR format for new CDC topics

### FastAPI router patterns
- `stock-prediction-platform/services/api/app/main.py` — Router registration (import + include_router)
- `stock-prediction-platform/services/api/app/routers/analytics.py` — Router pattern: APIRouter + cache-get/set + service call
- `stock-prediction-platform/services/api/app/cache.py` — Cache utilities (build_key, cache_get, cache_set)

### Frontend page patterns
- `stock-prediction-platform/services/frontend/src/pages/Models.tsx` — Page structure: Container + PageHeader + MUI components
- `stock-prediction-platform/services/frontend/src/pages/Analytics.tsx` — Existing analytics page (do not modify)

### Project constraints
- `stock-prediction-platform/services/api/app/config.py` — Settings class pattern for new ES/Kibana env vars
- `stock-prediction-platform/docker-compose.yml` — docker-compose service pattern for local dev

No external spec documents — all requirements captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/routers/analytics.py`: APIRouter + Redis cache + service pattern is the exact template for `/search` router
- `app/cache.py`: `build_key`, `cache_get`, `cache_set` utilities ready to use for search result caching
- `app/models/schemas.py`: Pydantic response model pattern to follow for SearchResponse types
- `k8s/storage/redis-deployment.yaml`: Direct template for Elasticsearch StatefulSet and Kibana Deployment

### Established Patterns
- K8s manifests: Deployment/StatefulSet + Service + ConfigMap + Secret + PVC per service, namespace-scoped
- FastAPI routers: `APIRouter(prefix="...", tags=[...])`, registered in `main.py` with `app.include_router()`
- Config: `app/config.py` `Settings` class with env var fields — add `ELASTICSEARCH_URL`, `KIBANA_URL`
- Frontend pages: `Container maxWidth="xl"` + `PageHeader` + MUI components + React Query hooks

### Integration Points
- New router file: `services/api/app/routers/search.py` → registered in `main.py`
- New service file: `services/api/app/services/elasticsearch_service.py` → called by search router
- New frontend page: `services/frontend/src/pages/Search.tsx` → added to router and sidebar nav
- New K8s manifests: `k8s/storage/elasticsearch-*.yaml`, `k8s/storage/kibana-*.yaml`
- New K8s manifests: `k8s/processing/kafka-connect-*.yaml` (KafkaConnect CR + KafkaConnector CRs)
- PostgreSQL WAL: must enable `wal_level=logical` in PostgreSQL ConfigMap

</code_context>

<specifics>
## Specific Ideas

- CDC source: capture only `predictions`, `drift_logs`, `model_registry` — do NOT index raw OHLCV data (too large, wrong use case)
- Strimzi KafkaConnect image: custom Dockerfile `FROM debezium/connect:latest` pushed to local Minikube registry
- ES Sink connector: use Confluent Elasticsearch Sink connector or Debezium's own — flatten CDC envelope with SMT (Single Message Transform) `ExtractField` to get clean documents in ES
- PostgreSQL WAL: `wal_level=logical` must be set — check current postgresql.conf ConfigMap before assuming it's set
- Kibana: expose via NodePort in storage namespace; useful for verifying indices during development

</specifics>

<deferred>
## Deferred Ideas

- Analytics, Models, Drift page ES enhancements (metric threshold filters, ES health panel, drift search bar) — follow-on phase after /search page is proven
- ES alerting (Watcher / Kibana alerting) for drift event patterns — separate phase
- Full-text search on OHLCV data or company news — out of scope (data volume too high for Minikube)
- Multi-node Elasticsearch cluster — cloud deployment phase only

</deferred>

---

*Phase: 90-debezium-cdc-and-elasticsearch-integration*
*Context gathered: 2026-04-03*
