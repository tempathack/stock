---
status: complete
phase: 64-timescaledb-olap-continuous-aggregates-compression
source: 64-01-SUMMARY.md, 64-02-SUMMARY.md
started: 2026-03-29T21:30:00Z
updated: 2026-03-29T21:35:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state. Start from scratch. Server boots without errors, migration (alembic upgrade head) completes, and a basic API call returns live data.
result: pass

### 2. Alembic Migration Applies Cleanly
expected: Running `alembic upgrade head` from the api service directory applies migration 005_timescaledb_olap.py without errors. The migration installs two continuous aggregate views (ohlcv_daily_1h_agg, ohlcv_daily_agg), compression policies on both hypertables, and retention policies (90 days intraday / 5 years daily).
result: pass

### 3. GET /market/candles - 1h Interval
expected: Calling `GET /market/candles?ticker=AAPL&interval=1h` returns HTTP 200 with a JSON body matching `{"ticker": "AAPL", "interval": "1h", "candles": [...]}`. Each candle has open, high, low, close, volume, and timestamp fields. Data is sourced from the ohlcv_daily_1h_agg continuous aggregate.
result: pass

### 4. GET /market/candles - 1d Interval
expected: Calling `GET /market/candles?ticker=AAPL&interval=1d` returns HTTP 200 with a JSON body matching `{"ticker": "AAPL", "interval": "1d", "candles": [...]}`. Data is sourced from the ohlcv_daily_agg continuous aggregate. Daily candles roll up correctly from the ohlcv_daily hypertable.
result: pass

### 5. GET /market/candles - Unsupported Interval Returns 400
expected: Calling `GET /market/candles?ticker=AAPL&interval=5m` (or any interval other than 1h/1d) returns HTTP 400. The response body includes a detail message indicating the interval is not supported and lists the supported intervals (1h, 1d).
result: pass

### 6. Redis Cache on Candles (30s TTL)
expected: Two identical requests to `GET /market/candles?ticker=AAPL&interval=1h` within 30 seconds: the second request is served from Redis cache without hitting the database. Observable via response time difference or logs showing "cache hit". After 30+ seconds, the next request goes to the database again.
result: pass

### 7. Grafana TimescaleDB Datasource in ConfigMap
expected: The file `k8s/monitoring/grafana-datasource-configmap.yaml` contains a PostgreSQL/TimescaleDB datasource entry with `timescaledb: true` and `type: postgres`. The datasource uses `${TIMESCALEDB_PASSWORD}` for the password (env var substitution, not hardcoded).
result: pass

### 8. Full Test Suite Green
expected: Running the full API test suite (`pytest` inside the api service) passes all 157 tests with 0 failures. The 6 new candles router tests (test_candles_router.py) are included in the green run.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
