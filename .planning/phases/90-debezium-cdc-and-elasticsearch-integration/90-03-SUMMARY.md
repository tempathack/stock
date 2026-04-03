---
phase: 90-debezium-cdc-and-elasticsearch-integration
plan: "03"
subsystem: api
tags: [elasticsearch, search, fastapi, async, cdc]
dependency_graph:
  requires: [90-01, 90-02]
  provides: [search-api-endpoints]
  affects: [api-service, frontend-search]
tech_stack:
  added: [elasticsearch[async]==8.19.3]
  patterns: [AsyncElasticsearch singleton, router+service+cache pattern, NotFoundError guard]
key_files:
  created:
    - stock-prediction-platform/services/api/app/services/elasticsearch_service.py
    - stock-prediction-platform/services/api/app/routers/search.py
  modified:
    - stock-prediction-platform/services/api/app/config.py
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/main.py
    - stock-prediction-platform/services/api/requirements.txt
decisions:
  - "Used str() conversion for all cache key parts in build_key() calls since build_key() accepts *parts: str — prevents TypeError when passing int/float/None query params"
  - "SEARCH_TTL=30s matches CDC write frequency; search results change frequently vs analytics TTLs of 10-30s"
  - "Lazy singleton pattern for AsyncElasticsearch client matches Redis pattern — created on first call, closed in lifespan shutdown"
metrics:
  duration: "2 minutes"
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 6
---

# Phase 90 Plan 03: FastAPI Search Layer (Elasticsearch) Summary

**One-liner:** AsyncElasticsearch-backed /search router with 4 endpoints (predictions, models, drift-events, stocks), 30s Redis cache, singleton lifecycle, and NotFoundError guard for missing indices.

## What Was Built

Added a complete FastAPI search layer on top of Elasticsearch, following the existing analytics.py router+service+cache pattern.

### Task 1: Config + Schemas + Elasticsearch Service + Requirements

- **config.py**: Added `ELASTICSEARCH_URL: Optional[str] = "http://elasticsearch.storage.svc.cluster.local:9200"` as Group 16 setting
- **schemas.py**: Appended 8 new Pydantic classes — 4 `SearchItem` types (PredictionSearchItem, ModelSearchItem, DriftEventSearchItem, StockSearchItem) and 4 `SearchResponse` types with pagination fields (items, total, page, page_size)
- **elasticsearch_service.py**: Created with AsyncElasticsearch singleton (`get_es_client`/`close_es_client`), `_build_pagination` helper, and 4 async search functions using bool/must query builders with NotFoundError catch for missing indices
- **requirements.txt**: Added `elasticsearch[async]==8.19.3`

### Task 2: Search Router + main.py Wiring

- **routers/search.py**: Created with `APIRouter(prefix="/search", tags=["search"])`, SEARCH_TTL=30, and 4 GET endpoints each with cache_get/cache_set wrapping
- **main.py**: Added `search` to router imports, `app.include_router(search.router)` after analytics router, and `close_es_client()` call in lifespan shutdown before `close_redis()`

## Endpoints Exposed

| Endpoint | Description | Key Filters |
|---|---|---|
| `GET /search/predictions` | Search predictions index | q, ticker, model_id, confidence_min, date_from, date_to, page, page_size |
| `GET /search/models` | Search model_registry index | q, status, r2_min, rmse_max, mae_max, page, page_size |
| `GET /search/drift-events` | Search drift_logs index | q, drift_type, severity, ticker, date_from, date_to, page, page_size |
| `GET /search/stocks` | Full-text search on stocks | q, sector, exchange, page, page_size |

## Decisions Made

1. **Cache key type safety**: `build_key(*parts: str)` requires string parts — all query params cast to `str()` before passing (e.g., `str(model_id)`, `str(None)` → `"None"`). This is consistent behavior and avoids TypeError at runtime.
2. **SEARCH_TTL = 30s**: CDC writes propagate to Elasticsearch within seconds; 30s TTL balances freshness vs Redis load.
3. **Lazy ES client**: Singleton created on first `get_es_client()` call, not in lifespan startup. This avoids startup failure if Elasticsearch is not yet reachable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Cache key type safety**
- **Found during:** Task 2
- **Issue:** `build_key()` signature is `(*parts: str)` but plan passed raw int/float/None values like `model_id`, `confidence_min` — would raise TypeError at runtime
- **Fix:** Wrapped all non-string params in `str()` in the router cache key construction calls
- **Files modified:** `stock-prediction-platform/services/api/app/routers/search.py`
- **Commit:** fd581b5

## Self-Check: PASSED

Files verified:
- FOUND: stock-prediction-platform/services/api/app/services/elasticsearch_service.py
- FOUND: stock-prediction-platform/services/api/app/routers/search.py
- FOUND: ELASTICSEARCH_URL in config.py
- FOUND: PredictionSearchResponse in schemas.py (8 search classes total)
- FOUND: search.router in main.py
- FOUND: close_es_client in main.py
- FOUND: elasticsearch[async]==8.19.3 in requirements.txt

Commits verified:
- d0f6de7: feat(90-03): add ES config, schemas, elasticsearch_service, and requirements
- fd581b5: feat(90-03): add search router and wire into main.py lifespan
