# Phase 24: FastAPI Market Endpoints - Research

**Researched:** 2026-03-20
**Domain:** FastAPI REST endpoints, PostgreSQL queries, technical indicators
**Confidence:** HIGH

## Summary

Phase 24 is **already fully implemented**. Both endpoints (GET /market/overview and GET /market/indicators/{ticker}) exist with router, service layer, Pydantic schemas, and tests. The router is registered in main.py. All 13 tests pass (7 router + 6 service) when PYTHONPATH includes the platform root for `ml` module access.

There is one operational gap: the service-level tests for `get_ticker_indicators` fail when run from the API service directory without PYTHONPATH set to include `stock-prediction-platform/` root (needed for `from ml.features.indicators import compute_all_indicators`). This is not a code bug but a test environment configuration issue that the planner should address.

**Primary recommendation:** Verify existing implementation satisfies API-11 and API-12, fix the PYTHONPATH issue in pytest configuration, and mark the phase complete.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-11 | GET /market/overview endpoint (treemap + sector data) | Fully implemented in `market.py` router + `market_service.py`. Returns ticker, company_name, sector, market_cap, last_close, daily_change_pct for all active stocks via PostgreSQL LATERAL JOIN. |
| API-12 | GET /market/indicators/{ticker} endpoint (technical indicators) | Fully implemented. Loads OHLCV from DB, runs `compute_all_indicators()` from Phase 10, returns 26 indicator columns as time series + latest snapshot. 404 on missing ticker. |
</phase_requirements>

## Implementation Audit

### API-11: GET /market/overview

**Status:** COMPLETE

| Aspect | Finding | Meets Requirement? |
|--------|---------|-------------------|
| Endpoint path | `/market/overview` | YES |
| Response fields | ticker, company_name, sector, market_cap, last_close, daily_change_pct | YES - all treemap fields present |
| Data source | PostgreSQL `stocks` JOIN LATERAL `ohlcv_daily` | YES |
| Daily change calc | `((close - open) / open) * 100` | YES |
| Ordering | By market_cap DESC NULLS LAST | YES - largest first for treemap |
| Filter | `WHERE s.is_active = true` | YES - only active S&P 500 stocks |
| Error handling | Returns empty list on DB failure | YES - graceful degradation |
| Schema | MarketOverviewResponse with count | YES |
| Tests | 3 router tests (data, empty, schema) + 2 service tests | YES |

**SQL query verification against init.sql:**
- `stocks.ticker` - EXISTS (VARCHAR(10) PK)
- `stocks.company_name` - EXISTS (VARCHAR(255))
- `stocks.sector` - EXISTS (VARCHAR(100))
- `stocks.market_cap` - EXISTS (BIGINT)
- `stocks.is_active` - EXISTS (BOOLEAN)
- `ohlcv_daily.close` - EXISTS (NUMERIC(12,4))
- `ohlcv_daily.open` - EXISTS (NUMERIC(12,4))
- `ohlcv_daily.date` - EXISTS (DATE)

All columns referenced in the query exist in the database schema.

### API-12: GET /market/indicators/{ticker}

**Status:** COMPLETE

| Aspect | Finding | Meets Requirement? |
|--------|---------|-------------------|
| Endpoint path | `/market/indicators/{ticker}` | YES |
| Indicator source | `ml.features.indicators.compute_all_indicators()` (Phase 10) | YES - all 27 columns |
| Response structure | ticker, latest (single row), series (full history), count | YES |
| Indicators returned | RSI, MACD (3), Stochastic (2), SMA (3), EMA (2), ADX, Bollinger (3), ATR, Volatility, OBV, VWAP, Volume SMA, AD Line, Returns (4) | YES - 26 indicator fields |
| 404 handling | Returns 404 with detail when no OHLCV data for ticker | YES |
| NaN handling | Replaces NaN/inf with None for JSON serialization | YES |
| Lookback | Default 250 trading days (~1 year) | YES - reasonable default |
| Tests | 4 router tests + 4 service tests (including uppercase columns) | YES |

### Known Issue: PYTHONPATH for Tests

The `market_service.py` imports `from ml.features.indicators import compute_all_indicators` at line 75. The `ml` package lives at `stock-prediction-platform/ml/`, but pytest runs from `stock-prediction-platform/services/api/`. Without PYTHONPATH including the platform root, 3 service tests fail with `ModuleNotFoundError: No module named 'ml'`.

**Fix options (planner should choose one):**
1. Add `pythonpath` to `pytest.ini`: `pythonpath = ../..` (pytest >= 7.0 feature)
2. Add `sys.path` manipulation in `conftest.py`
3. Document PYTHONPATH requirement in test run instructions

**Verified:** All 13 tests pass with `PYTHONPATH=/path/to/stock-prediction-platform python -m pytest`

## Standard Stack

### Already In Use (from previous phases)
| Library | Purpose | Status |
|---------|---------|--------|
| FastAPI | REST framework | Already configured |
| Pydantic v2 | Schema validation | Already configured |
| psycopg2 | PostgreSQL driver | Already in use (lazy import) |
| pandas + numpy | Data manipulation | Already in use |
| ml.features.indicators | Technical indicator computation | Phase 10, already working |

No new dependencies needed for this phase.

## Architecture Patterns

### Pattern: Service Layer Separation (already followed)
- **Router** (`market.py`): HTTP concerns only - request parsing, response construction, HTTP errors
- **Service** (`market_service.py`): Business logic - DB queries, indicator computation
- **Schemas** (`schemas.py`): Pydantic models for request/response validation

### Pattern: Lazy Import for Optional Dependencies
```python
# Used in market_service.py for psycopg2 and ml.features.indicators
from ml.features.indicators import compute_all_indicators  # imported inside function
```
This avoids import errors when the module is not on PYTHONPATH during unit testing of other components.

### Pattern: Graceful Degradation
Both service functions return empty/None when DB is unavailable rather than raising exceptions. The router converts None to HTTP 404.

## Don't Hand-Roll

| Problem | Already Solved By | Notes |
|---------|-------------------|-------|
| Technical indicators | `ml.features.indicators.compute_all_indicators()` | Phase 10 - 14 indicator families, 27 columns |
| JSON NaN handling | `subset.replace([np.inf, -np.inf], np.nan).where(subset.notna(), None)` | Already implemented correctly |
| SQL injection | Parameterized queries (`%s` placeholders) | Already implemented correctly |

## Common Pitfalls

### Pitfall 1: PYTHONPATH for Cross-Service Imports
**What goes wrong:** Tests fail with ModuleNotFoundError for `ml` package
**Why it happens:** `ml/` package is at platform root, API tests run from `services/api/`
**How to avoid:** Configure pytest.ini with `pythonpath` or set PYTHONPATH in CI/test scripts
**Status:** Known issue - needs fix in plan

### Pitfall 2: NaN/Infinity in JSON Responses
**What goes wrong:** JSON serialization fails on NaN/Infinity values from pandas
**How to avoid:** Replace with None before serialization
**Status:** Already handled correctly in `market_service.py` line 103

### Pitfall 3: LATERAL JOIN Performance
**What goes wrong:** N+1 query pattern when fetching latest OHLCV per stock
**How to avoid:** Use LATERAL JOIN (already done) - PostgreSQL optimizes this well
**Status:** Already implemented correctly

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest with FastAPI TestClient |
| Config file | `stock-prediction-platform/services/api/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/api && PYTHONPATH="../../:$PYTHONPATH" python -m pytest tests/test_market_router.py tests/test_market_service.py -v` |
| Full suite command | `cd stock-prediction-platform/services/api && PYTHONPATH="../../:$PYTHONPATH" python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-11 | /market/overview returns stocks with treemap data | unit (mock) | `pytest tests/test_market_router.py::TestMarketOverview -x` | YES |
| API-11 | Service returns empty on no DB | unit | `pytest tests/test_market_service.py::TestGetMarketOverview -x` | YES |
| API-12 | /market/indicators/{ticker} returns indicator data | unit (mock) | `pytest tests/test_market_router.py::TestMarketIndicators -x` | YES |
| API-12 | Service computes indicators from DataFrame | unit | `pytest tests/test_market_service.py::TestGetTickerIndicators -x` | YES (needs PYTHONPATH) |

### Sampling Rate
- **Per task commit:** `PYTHONPATH="../../:$PYTHONPATH" python -m pytest tests/test_market_router.py tests/test_market_service.py -x`
- **Per wave merge:** `PYTHONPATH="../../:$PYTHONPATH" python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Fix PYTHONPATH in pytest.ini so `ml` module is importable without manual env var — add `pythonpath = ../..` to pytest.ini

## Open Questions

1. **Daily change calculation uses open-to-close, not close-to-close**
   - What we know: The SQL computes `((close - open) / open) * 100` for daily_change_pct
   - What's unclear: The frontend treemap (Phase 28, FDASH-01) says "daily performance" -- this could mean open-to-close or previous-close-to-close
   - Recommendation: Open-to-close is standard for intraday change display in treemaps (matches TradingView/Finviz convention). Accept as-is.

2. **No pagination on /market/overview**
   - What we know: Returns all ~500 S&P 500 stocks in one response
   - What's unclear: Whether this will be a performance issue
   - Recommendation: For 500 stocks with 6 fields each, payload is ~50KB. Acceptable for treemap rendering which needs all data at once.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `stock-prediction-platform/services/api/app/routers/market.py` - full implementation reviewed
- Existing codebase: `stock-prediction-platform/services/api/app/services/market_service.py` - full implementation reviewed
- Existing codebase: `stock-prediction-platform/services/api/app/models/schemas.py` - all schemas verified
- Existing codebase: `stock-prediction-platform/services/api/tests/test_market_router.py` - 7 tests reviewed
- Existing codebase: `stock-prediction-platform/services/api/tests/test_market_service.py` - 6 tests reviewed
- Existing codebase: `stock-prediction-platform/db/init.sql` - SQL column references verified

### Verification
- All 13 tests confirmed passing with PYTHONPATH set (3 fail without it)
- SQL query column names cross-referenced against init.sql schema
- Router registration in main.py confirmed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all existing
- Architecture: HIGH - follows exact same pattern as Phase 23
- Pitfalls: HIGH - only issue is known PYTHONPATH config, already verified fix
- Implementation completeness: HIGH - code reviewed line by line, tests verified

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable - implementation already exists)
