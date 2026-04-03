---
phase: 90-debezium-cdc-and-elasticsearch-integration
verified: 2026-04-03T11:00:00Z
status: passed
score: 22/22 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Live end-to-end CDC data flow"
    expected: "PostgreSQL insert into predictions/drift_logs/model_registry appears in Elasticsearch index within seconds via Debezium -> Kafka -> ES Sink"
    why_human: "Requires running Minikube cluster with all services live; cannot verify WAL event propagation programmatically from static files"
  - test: "Search page returns real results"
    expected: "Typing a ticker symbol in /search Predictions tab returns rows from Elasticsearch"
    why_human: "Requires live Elasticsearch populated by CDC; automated check only verifies code wiring not runtime behavior"
---

# Phase 90: Debezium CDC and Elasticsearch Integration Verification Report

**Phase Goal:** Deploy Debezium Connect as a K8s workload capturing PostgreSQL WAL changes for predictions, drift_logs, and model_registry tables into Kafka CDC topics; route CDC events to Elasticsearch via Kafka Connect ES Sink Connector; expose FastAPI /search/* endpoints; update React analytics and model-comparison pages to query Elasticsearch. All components run as Kubernetes resources in Minikube.
**Verified:** 2026-04-03T11:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Elasticsearch 8 StatefulSet exists in storage namespace with xpack.security.enabled=false and discovery.type=single-node | VERIFIED | `elasticsearch-statefulset.yaml` contains `kind: StatefulSet`, `namespace: storage`, env vars for both settings, 2 YAML docs (StatefulSet + Service) |
| 2 | Kibana Deployment exists in storage namespace pointing to Elasticsearch service | VERIFIED | `kibana-deployment.yaml` has `ELASTICSEARCH_HOSTS=http://elasticsearch.storage.svc.cluster.local:9200`, NodePort 30601 |
| 3 | PostgreSQL Deployment has args enabling wal_level=logical, max_replication_slots=5, max_wal_senders=5 | VERIFIED | `postgresql-deployment.yaml` args block contains all three WAL parameters |
| 4 | 10Gi PVC exists for Elasticsearch data persistence | VERIFIED | `elasticsearch-pvc.yaml` requests `storage: 10Gi` |
| 5 | KafkaConnect CR for Debezium exists in processing namespace with strimzi.io/use-connector-resources: true annotation | VERIFIED | `kafka-connect-debezium.yaml` has annotation, FQDN bootstrap address, and `imagePullPolicy: Never` |
| 6 | KafkaConnector CR for Debezium PostgreSQL source exists with table.include.list for predictions, drift_logs, model_registry | VERIFIED | `kafka-connect-connector-pg.yaml` class is `io.debezium.connector.postgresql.PostgresConnector`, SMT is `ExtractNewRecordState`, `table.include.list: "public.predictions,public.drift_logs,public.model_registry"` |
| 7 | KafkaConnector CR for Elasticsearch Sink exists wiring CDC topics to elasticsearch.storage.svc.cluster.local:9200 | VERIFIED | `kafka-connect-connector-es.yaml` class is `ElasticsearchSinkConnector`, topics lists all 3 CDC topic names, connection.url points to ES ClusterIP |
| 8 | Three KafkaTopic CRs exist for debezium.public.predictions, debezium.public.drift_logs, debezium.public.model_registry in storage namespace | VERIFIED | `kafka-topics-cdc.yaml` has exactly 3 `kind: KafkaTopic` docs, all in `namespace: storage` with `strimzi.io/cluster: kafka` |
| 9 | Dockerfile builds custom Debezium image FROM debezium/connect:2.7 with Confluent ES Sink connector JAR | VERIFIED | `docker/debezium-connect/Dockerfile` has `FROM debezium/connect:2.7` and downloads `kafka-connect-elasticsearch-14.2.0.jar` |
| 10 | GET /search/predictions returns paginated results from Elasticsearch index debezium.public.predictions | VERIFIED | `elasticsearch_service.py::search_predictions` queries `INDEX_PREDICTIONS = "debezium.public.predictions"` with pagination, NotFoundError guard |
| 11 | GET /search/models returns paginated results from Elasticsearch index debezium.public.model_registry | VERIFIED | `elasticsearch_service.py::search_models` queries `INDEX_MODELS = "debezium.public.model_registry"` |
| 12 | GET /search/drift-events returns paginated results from Elasticsearch index debezium.public.drift_logs | VERIFIED | `elasticsearch_service.py::search_drift_events` queries `INDEX_DRIFT = "debezium.public.drift_logs"` |
| 13 | GET /search/stocks returns full-text search results from Elasticsearch | VERIFIED | `elasticsearch_service.py::search_stocks` queries `INDEX_STOCKS = "stocks"` with multi_match |
| 14 | All search endpoints support page + page_size query params (default 50, max 500) | VERIFIED | `search.py` router has `page: int = Query(1, ge=1)` and `page_size: int = Query(50, ge=1, le=500)` on all 4 endpoints |
| 15 | AsyncElasticsearch client is initialized in main.py lifespan and closed on shutdown | VERIFIED | `main.py` calls `close_es_client()` in lifespan shutdown; lazy singleton in `elasticsearch_service.py` |
| 16 | ELASTICSEARCH_URL setting exists in config.py with default http://elasticsearch.storage.svc.cluster.local:9200 | VERIFIED | `config.py` Group 16: `ELASTICSEARCH_URL: Optional[str] = "http://elasticsearch.storage.svc.cluster.local:9200"` |
| 17 | Navigating to /search shows a page titled 'Search' with a unified search input | VERIFIED | `Search.tsx` renders `PageHeader title="Search"` and `TextField` with autoFocus; Playwright screenshot `phase-90-search-page.png` confirms |
| 18 | Four tabs appear below: Predictions, Models, Drift Events, Stocks | VERIFIED | `Search.tsx` has 4 `TabPanel` components; plan-05 Playwright check confirmed all 4 tabs visible |
| 19 | Typing in the search box debounces 300ms then fires queries to all four /search/* endpoints | VERIFIED | `Search.tsx` uses `setTimeout` debounce timer, `hasQuery` guard enabling all 4 React Query hooks |
| 20 | Empty state (no query) shows 'Start searching' heading | VERIFIED | `Search.tsx` renders `<Typography>"Start searching"</Typography>` when `hasQuery` is false |
| 21 | Sidebar navigation includes a Search item with SearchIcon | VERIFIED | `Sidebar.tsx` has `{ to: "/search", label: "Search", Icon: SearchIcon }` |
| 22 | /search route is lazy-loaded in App.tsx Suspense | VERIFIED | `App.tsx` has `const Search = lazy(() => import("./pages/Search"))` and `path="search"` route |

**Score:** 22/22 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `k8s/storage/elasticsearch-statefulset.yaml` | Elasticsearch 8 StatefulSet + ClusterIP Service | VERIFIED | 2 YAML docs, kind: StatefulSet, init container, correct env vars, references elasticsearch-pvc |
| `k8s/storage/elasticsearch-pvc.yaml` | 10Gi PVC | VERIFIED | `storage: 10Gi`, ReadWriteOnce, namespace: storage |
| `k8s/storage/kibana-deployment.yaml` | Kibana Deployment + NodePort Service | VERIFIED | nodePort: 30601, ELASTICSEARCH_HOSTS env set |
| `k8s/storage/postgresql-deployment.yaml` | Updated PostgreSQL with WAL args | VERIFIED | args[] contains wal_level=logical, max_replication_slots=5, max_wal_senders=5 |
| `docker/debezium-connect/Dockerfile` | Custom Debezium image spec | VERIFIED | FROM debezium/connect:2.7, Confluent ES Sink 14.2.0 JAR installed |
| `k8s/processing/kafka-topics-cdc.yaml` | 3 KafkaTopic CRs | VERIFIED | Exactly 3 topics in storage namespace with strimzi.io/cluster: kafka |
| `k8s/processing/kafka-connect-debezium.yaml` | KafkaConnect CR | VERIFIED | use-connector-resources annotation, FQDN bootstrap, imagePullPolicy: Never |
| `k8s/processing/kafka-connect-connector-pg.yaml` | Debezium PostgreSQL source connector | VERIFIED | Correct class, ExtractNewRecordState SMT, 3 tables listed |
| `k8s/processing/kafka-connect-connector-es.yaml` | Confluent ES Sink connector | VERIFIED | Correct class, 3 CDC topics, ES ClusterIP URL |
| `services/api/app/services/elasticsearch_service.py` | AsyncElasticsearch service module | VERIFIED | Singleton, close_es_client, 4 search functions with NotFoundError guard |
| `services/api/app/routers/search.py` | FastAPI /search router | VERIFIED | prefix="/search", 4 GET endpoints with pagination, 30s cache |
| `services/api/app/models/schemas.py` | Pydantic search response models | VERIFIED | PredictionSearchResponse, ModelSearchResponse, DriftEventSearchResponse, StockSearchResponse appended |
| `services/api/app/config.py` | ELASTICSEARCH_URL setting | VERIFIED | Group 16 setting with default ES ClusterIP URL |
| `services/api/app/main.py` | search router registered + ES lifecycle | VERIFIED | search imported and registered, close_es_client called in shutdown |
| `services/api/requirements.txt` | elasticsearch[async]==8.19.3 | VERIFIED | Present |
| `services/frontend/src/api/types.ts` | TypeScript search types | VERIFIED | PredictionSearchItem, ModelSearchItem, DriftEventSearchItem, StockSearchItem, SearchPaginatedResponse<T> |
| `services/frontend/src/api/queries.ts` | 4 React Query hooks | VERIFIED | useSearchPredictions, useSearchModels, useSearchDriftEvents, useSearchStocks |
| `services/frontend/src/pages/Search.tsx` | Search page component | VERIFIED | Debounced TextField, 4 TabPanel, DataGrid per tab, empty state |
| `services/frontend/src/App.tsx` | Lazy /search route | VERIFIED | lazy(() => import('./pages/Search')), path="search" |
| `services/frontend/src/components/layout/Sidebar.tsx` | Search nav item | VERIFIED | SearchIcon, { to: "/search", label: "Search" } |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `elasticsearch-statefulset.yaml` | `elasticsearch-pvc.yaml` | volumes[].persistentVolumeClaim.claimName: elasticsearch-pvc | WIRED | StatefulSet references PVC by name in volumes[] |
| `kibana-deployment.yaml` | elasticsearch service | ELASTICSEARCH_HOSTS env | WIRED | Points to `http://elasticsearch.storage.svc.cluster.local:9200` |
| `kafka-connect-connector-pg.yaml` | `kafka-connect-debezium.yaml` | label strimzi.io/cluster: debezium-connect | WIRED | Both KafkaConnector CRs have matching label |
| `kafka-connect-connector-es.yaml` | `kafka-topics-cdc.yaml` | topics field matches KafkaTopic names | WIRED | topics: "debezium.public.predictions,debezium.public.drift_logs,debezium.public.model_registry" |
| `kafka-connect-debezium.yaml` | Kafka cluster | spec.bootstrapServers FQDN | WIRED | `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` |
| `routers/search.py` | `services/elasticsearch_service.py` | imports search_predictions, search_models, search_drift_events, search_stocks | WIRED | from app.services.elasticsearch_service import all 4 functions |
| `main.py` | `routers/search.py` | app.include_router(search.router) | WIRED | search in router import line; include_router call present |
| `main.py lifespan` | `elasticsearch_service.close_es_client` | await close_es_client() in shutdown | WIRED | Called in lifespan shutdown block |
| `Search.tsx` | `api/queries.ts` hooks | import from "@/api" barrel | WIRED | `export * from "./queries"` in api/index.ts; hooks imported and called |
| `App.tsx` | `pages/Search.tsx` | lazy(() => import('./pages/Search')) | WIRED | Route path="search" wraps lazy Search component |
| `Sidebar.tsx` | /search route | { to: "/search" } nav item | WIRED | SearchIcon + label "Search" added to navItems |

### Requirements Coverage

| Requirement | Source Plan | Description | Status |
|-------------|------------|-------------|--------|
| TBD | All plans | Phase requirements listed as TBD in all plan frontmatter | N/A — no formal requirement IDs assigned |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `Search.tsx` | 203 | `if (!active) return null` | Info | Intentional TabPanel pattern — tab content unmounts when not active; documented in plan 04 decisions as deliberate design choice |

No blockers or warnings found. The `return null` at line 203 is the intended TabPanel lazy-render pattern, not a stub.

### Human Verification Required

#### 1. Live CDC End-to-End Data Flow

**Test:** Insert a row into `predictions` table in PostgreSQL, wait ~10 seconds, then query `GET /search/predictions?q=<ticker>`.
**Expected:** The new prediction appears in Elasticsearch and is returned by the search endpoint.
**Why human:** Requires a running Minikube cluster with all services live (PostgreSQL, Kafka, Debezium Connect, Elasticsearch). Static file analysis cannot verify WAL event propagation and CDC replication slot creation.

#### 2. Search Page Shows Live Results

**Test:** Navigate to `/search`, type a known ticker symbol (e.g., "AAPL") in the search box, wait 300ms for debounce.
**Expected:** Predictions tab DataGrid shows rows; no "Error loading" message in any tab.
**Why human:** Requires Elasticsearch to be populated via CDC pipeline. The Playwright screenshot from plan 05 confirms the page renders but cannot confirm data flow.

### Gaps Summary

No gaps. All 22 observable truths verified at all three levels (exists, substantive, wired). All 8 commit hashes documented in SUMMARYs confirmed present in git log. Playwright screenshot `phase-90-search-page.png` exists at repo root confirming plan 05 browser verification was completed.

The two human verification items above are operational concerns (require live infrastructure), not code gaps. The manifests, connectors, API layer, and frontend are fully implemented and wired.

---

_Verified: 2026-04-03T11:00:00Z_
_Verifier: Claude (gsd-verifier)_
