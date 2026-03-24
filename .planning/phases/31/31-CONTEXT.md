# Phase 31 — Live Model Inference API

## What This Phase Delivers

Wire /predict and /models endpoints to PostgreSQL and live model inference, replacing file-only reads with DB-first queries and graceful fallback:

1. **DB query functions in prediction_service.py** — `load_model_comparison_from_db()`, `load_drift_events_from_db()`, and `get_live_prediction()` that query model_registry, drift_logs, and predictions tables
2. **DB-first predict router** — `/predict/{ticker}` loads the active model pipeline from SERVING_DIR, fetches latest OHLCV + computes features, runs live inference; falls back to cached predictions file when model or DB unavailable
3. **DB-first models router** — `/models/comparison` and `/models/drift` query PostgreSQL when DATABASE_URL is set; fall back to file-based registry/JSONL when DB unavailable
4. **New drift monitoring endpoints** — `/models/drift/rolling-performance` returns recent prediction error trends; `/models/retrain-status` returns latest retraining event metadata
5. **Database session management** — `database.py` populated with psycopg2 connection helper matching the pattern already used by market_service.py

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| LIVE-01 | GET /predict/{ticker} returns live model inference (not cached JSON) | Updated `routers/predict.py` + `get_live_prediction()` in prediction_service.py |
| LIVE-02 | GET /predict/bulk runs live inference for all configured tickers | Updated `routers/predict.py` bulk endpoint |
| LIVE-03 | GET /models/comparison queries model_registry table when DATABASE_URL set | Updated `routers/models.py` + `load_model_comparison_from_db()` |
| LIVE-04 | GET /models/drift queries drift_logs table when DATABASE_URL set | Updated `routers/models.py` + `load_drift_events_from_db()` |
| LIVE-05 | Graceful fallback to cached file responses when DB or model unavailable | try/except wrappers in all endpoints with file-based fallback |

## Architecture

### Current State (Phase 30)

```
┌──────────┐    File reads     ┌──────────────────────────┐
│ /predict │ ───────────────→  │ model_registry/           │
│ /models  │                   │   predictions/latest.json │
└──────────┘                   │   {model}/v{N}/meta.json  │
                               │ drift_logs/events.jsonl   │
                               └──────────────────────────┘
```

### Target State (Phase 31)

```
┌──────────┐    DB query (primary)     ┌──────────────────┐
│ /predict │ ──────────────────────→   │ PostgreSQL        │
│ /models  │                           │   model_registry  │
│          │    Live inference          │   predictions     │
│          │ ──────────────────────→   │   drift_logs      │
│          │    pipeline.pkl + OHLCV   │   ohlcv_daily     │
│          │                           └──────────────────┘
│          │    File fallback (backup)  ┌──────────────────┐
│          │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─→   │ File system       │
└──────────┘                           │   latest.json     │
                                       │   metadata.json   │
                                       │   events.jsonl    │
                                       └──────────────────┘
```

### Live Inference Flow

```
GET /predict/AAPL
  │
  ├─→ Load active pipeline from SERVING_DIR/pipeline.pkl
  ├─→ Query ohlcv_daily for AAPL (last 250 rows for indicator warmup)
  ├─→ Compute features via compute_all_indicators() + lag features
  ├─→ Run pipeline.predict(features[-1:]) → predicted_price
  ├─→ Return PredictionResponse with model_name, confidence
  │
  └─→ [FALLBACK] If pipeline or DB unavailable:
       └─→ Read from model_registry/predictions/latest.json
```

### DB Query Pattern

Follows the same psycopg2 pattern established in `market_service.py`:
- Check if `DATABASE_URL` is set → if not, use file fallback
- Import psycopg2 inside function (lazy import for optional dependency)
- Use context manager: `with psycopg2.connect(db_url) as conn`
- On any exception → log warning → return file-based fallback result

## Database Tables Used

### model_registry
```sql
model_id     SERIAL PRIMARY KEY
model_name   VARCHAR(100) NOT NULL     -- e.g. "CatBoost_standard"
version      VARCHAR(50) NOT NULL      -- e.g. "1"
metrics_json JSONB NOT NULL            -- {oos_rmse, oos_mae, oos_r2, fold_stability, best_params, is_winner, scaler_variant, ...}
trained_at   TIMESTAMPTZ
is_active    BOOLEAN DEFAULT false     -- Only one model active at a time
```

### drift_logs
```sql
id           BIGSERIAL PRIMARY KEY
drift_type   VARCHAR(50)              -- data_drift | prediction_drift | concept_drift
severity     VARCHAR(20)              -- low | medium | high
details_json JSONB                    -- Feature-level statistics, thresholds
detected_at  TIMESTAMPTZ
```

### predictions
```sql
id               BIGSERIAL PRIMARY KEY
ticker           VARCHAR(10) FK → stocks
prediction_date  DATE
predicted_date   DATE
predicted_price  NUMERIC(12,4)
model_id         INTEGER FK → model_registry
confidence       NUMERIC(5,4)
created_at       TIMESTAMPTZ
```

## Key File Paths

```
services/api/app/
  config.py                          -- DATABASE_URL, SERVING_DIR settings
  main.py                            -- Lifespan (no changes needed)
  models/
    database.py                      -- DB connection helper (currently stub)
    schemas.py                       -- Pydantic models (add RollingPerfEntry, RetrainStatusResponse)
  routers/
    predict.py                       -- /predict/{ticker}, /predict/bulk
    models.py                        -- /models/comparison, /models/drift, + new endpoints
  services/
    prediction_service.py            -- Add DB query functions + live inference
    market_service.py                -- Reference for DB query pattern

ml/
  features/indicators.py             -- compute_all_indicators()
  features/lag_features.py           -- create_lag_features()
  models/registry.py                 -- ModelRegistry.load_model(), get_active_model()

db/init.sql                          -- Schema reference
```

## Existing Test Coverage

### API Tests (services/api/tests/)
- `test_predict.py` — Tests for /predict/{ticker} and /predict/bulk with file-based predictions
- `test_models.py` — Tests for /models/comparison and /models/drift with file-based data
- Tests will need updating to cover DB-first path + fallback behavior
