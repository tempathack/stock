---
phase: 64-timescaledb-olap-continuous-aggregates-compression
plan: 02
subsystem: api
tags: [timescaledb, fastapi, redis, grafana, postgresql, pydantic, continuous-aggregates]

# Dependency graph
requires:
  - phase: 64-01
    provides: ohlcv_daily_1h_agg and ohlcv_daily_agg continuous aggregate views in TimescaleDB
  - phase: 47
    provides: Redis caching layer (cache_get, cache_set, build_key, TTL constants)
  - phase: 24
    provides: market router pattern, market_service.py async DB query pattern

provides:
  - "GET /market/candles?ticker=AAPL&interval=1h endpoint backed by ohlcv_daily_1h_agg"
  - "GET /market/candles?ticker=AAPL&interval=1d endpoint backed by ohlcv_daily_agg"
  - "HTTP 400 with interval detail for unsupported intervals (e.g. 5m)"
  - "Redis cache (30s TTL) on candles responses via MARKET_CANDLES_TTL"
  - "CandleBar and CandlesResponse Pydantic schemas"
  - "get_candles() async service function with _CANDLE_VIEW_MAP dict"
  - "Grafana ConfigMap updated with PostgreSQL/TimescaleDB datasource"

affects: [phase-68-e2e, phase-69-analytics-ui, grafana-dashboards]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "View-mapped query: _CANDLE_VIEW_MAP dict maps user-facing interval string to safe view name — view name from dict, not from user input"
    - "Candle endpoint follows same cache-check → DB-query → cache-set pattern as market_overview and market_indicators"
    - "SUPPORTED_CANDLE_INTERVALS set in router guards interval before it reaches service layer (defence-in-depth)"

key-files:
  created:
    - stock-prediction-platform/services/api/tests/test_candles_router.py
  modified:
    - stock-prediction-platform/services/api/app/cache.py
    - stock-prediction-platform/services/api/app/models/schemas.py
    - stock-prediction-platform/services/api/app/services/market_service.py
    - stock-prediction-platform/services/api/app/routers/market.py
    - stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml

key-decisions:
  - "View name from _CANDLE_VIEW_MAP dict (not user input) — text(f-string) safe because view is whitelist-validated"
  - "Router guards interval with SUPPORTED_CANDLE_INTERVALS before calling get_candles — None return from service is dead code in production but kept for defence-in-depth"
  - "Grafana TimescaleDB password uses ${TIMESCALEDB_PASSWORD} env var substitution — K8s Secret provisioning deferred to Phase 65 GitOps"
  - "MARKET_CANDLES_TTL = 30 consistent with MARKET_OVERVIEW_TTL and MARKET_INDICATORS_TTL"

patterns-established:
  - "Candle endpoint: interval validation in router -> cache check -> get_candles() -> cache set -> return CandlesResponse"

requirements-completed: [TSDB-06]

# Metrics
duration: 12min
completed: 2026-03-29
---

# Phase 64 Plan 02: Candles Endpoint & Grafana TimescaleDB Datasource Summary

**GET /market/candles endpoint backed by two TimescaleDB continuous aggregates, Redis 30s caching, 400 guard for unsupported intervals, and Grafana PostgreSQL datasource configured for OLAP queries**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-29T21:05:00Z
- **Completed:** 2026-03-29T21:17:00Z
- **Tasks:** 2 (TDD: 1 RED commit + 1 GREEN commit)
- **Files modified:** 6

## Accomplishments

- GET /market/candles returns 200 with CandlesResponse for 1h (ohlcv_daily_1h_agg) and 1d (ohlcv_daily_agg) intervals
- Returns 400 with interval detail for any unsupported interval (e.g. 5m, 15m)
- Redis cache (30s TTL) on candle responses using build_key("market", "candles", ticker, interval)
- Cache hit bypasses get_candles() entirely (test_candles_cache_hit verified)
- Grafana ConfigMap extended with PostgreSQL/TimescaleDB datasource (timescaledb=true, type=postgres)
- Full test suite: 157/157 green

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 — Write test scaffold for candles endpoint** - `ba56286` (test) — RED state
2. **Task 2: Implement candles schema, service, router endpoint, and Grafana datasource** - `e921d2d` (feat) — GREEN state

## Files Created/Modified

- `stock-prediction-platform/services/api/tests/test_candles_router.py` - 6 TDD tests for /market/candles (created)
- `stock-prediction-platform/services/api/app/cache.py` - Added MARKET_CANDLES_TTL = 30
- `stock-prediction-platform/services/api/app/models/schemas.py` - Added CandleBar and CandlesResponse schemas
- `stock-prediction-platform/services/api/app/services/market_service.py` - Added _CANDLE_VIEW_MAP dict and get_candles() async function
- `stock-prediction-platform/services/api/app/routers/market.py` - Added GET /candles endpoint with interval guard and caching
- `stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml` - Added TimescaleDB PostgreSQL datasource entry

## Decisions Made

- View name from _CANDLE_VIEW_MAP dict rather than user input: text(f-string) is safe because the view name is whitelist-validated before interpolation, not derived from request parameters
- Router-level interval guard (SUPPORTED_CANDLE_INTERVALS set) fires before cache lookup or DB call, meaning get_candles() is only called with valid intervals in production
- Grafana password uses ${TIMESCALEDB_PASSWORD} env var substitution — actual K8s Secret provisioning is out of scope (Phase 65 GitOps)
- MARKET_CANDLES_TTL = 30 matches the existing pattern for MARKET_OVERVIEW_TTL and MARKET_INDICATORS_TTL

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 69 (/analytics UI) can now call GET /market/candles to render the OLAPCandleChart panel
- Phase 68 E2E tests can exercise the /market/candles endpoint against live TimescaleDB
- Grafana datasource is provisioned declaratively — once the K8s Secret for TIMESCALEDB_PASSWORD is created (Phase 65 or manual), OLAP panels can query continuous aggregates directly

---
*Phase: 64-timescaledb-olap-continuous-aggregates-compression*
*Completed: 2026-03-29*
