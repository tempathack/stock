# Phase 30 — Integration Testing & Seed Data

## What This Phase Delivers

End-to-end validation of all cross-service data flows and a seed data script for development:

1. **seed-data.sh** — Populates all 6 PostgreSQL tables (stocks, ohlcv_daily, ohlcv_intraday, model_registry, predictions, drift_logs) with realistic S&P 500 test data
2. **Ingest → Kafka → PostgreSQL integration test** — Validates the full ingestion pipeline from API call through Kafka produce/consume to database upsert
3. **ML pipeline → model registry → serving integration test** — Validates the training pipeline produces a deployed model and /predict returns values
4. **API → Frontend integration test** — Validates all FastAPI endpoints return correctly shaped data consumable by the React frontend
5. **Drift → retrain → redeploy integration test** — Validates the full drift detection → retraining → redeployment → prediction regeneration cycle

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| TEST-01 | E2E flow: ingest → Kafka → PostgreSQL | `tests/integration/test_ingest_to_db.py` |
| TEST-02 | E2E flow: PostgreSQL → Kubeflow → model registry → serving | `tests/integration/test_pipeline_to_serving.py` |
| TEST-03 | E2E flow: FastAPI prediction endpoints → frontend | `tests/integration/test_api_to_frontend.py` |
| TEST-04 | Drift → retraining → redeployment cycle | `tests/integration/test_drift_cycle.py` |
| TEST-05 | seed-data.sh script for test data population | `scripts/seed-data.sh` |

## Data Foundation

### Database Schema (6 Tables)

```
stocks            — S&P 500 reference (ticker PK, company_name, sector, industry, market_cap)
ohlcv_daily       — Daily bars (ticker FK, date PK, OHLCV + adj_close + vwap) → TimescaleDB hypertable
ohlcv_intraday    — Intraday bars (ticker FK, timestamp PK, OHLCV) → TimescaleDB hypertable
model_registry    — ML model catalog (model_id PK, model_name, version, metrics_json, is_active)
predictions       — 7-day forecasts (ticker FK, model_id FK, prediction_date, predicted_date, predicted_price)
drift_logs        — Drift events (drift_type, severity, details_json, detected_at)
```

### Seed Data Strategy

- **20 S&P 500 stocks** — AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK-B, JPM, JNJ, V, PG, UNH, HD, MA, BAC, XOM, PFE, ABBV, CVX (matches `TICKER_SYMBOLS` in API config)
- **90 days of daily OHLCV** — Synthetic but realistic price series with proper OHLC relationships
- **5 days of intraday OHLCV** — 5-min bars during market hours (9:30–16:00 ET), ~78 bars/day
- **3 model registry entries** — CatBoost_standard (winner/active), Ridge_quantile, RandomForest_minmax
- **7-day predictions per stock** — For the active model, 20 tickers × 7 days = 140 prediction rows
- **5 drift log entries** — Mix of data_drift, prediction_drift, concept_drift with varying severity

### API Endpoints Under Test

| Endpoint | Method | Data Source |
|----------|--------|-------------|
| `/health` | GET | Static |
| `/ingest/intraday` | POST | Yahoo Finance → Kafka |
| `/ingest/historical` | POST | Yahoo Finance → Kafka |
| `/predict/{ticker}` | GET | File-based (model_registry/) |
| `/predict/bulk` | GET | File-based (model_registry/) |
| `/models/comparison` | GET | File-based (model_registry/) |
| `/models/drift` | GET | File-based (drift_logs/) |
| `/market/overview` | GET | PostgreSQL (stocks + ohlcv_daily) |
| `/market/indicators/{ticker}` | GET | PostgreSQL (ohlcv_daily) → compute_all_indicators() |

### Integration Test Architecture

Tests use **in-process testing** with mocked external dependencies (Yahoo Finance, Kafka broker) but real data flow between internal components. This validates the component wiring without requiring live K8s infrastructure.

- **Ingest flow (TEST-01):** Mock Yahoo Finance responses → real `OHLCVProducer.produce_records()` with mocked Kafka → real `MessageProcessor` → mock `BatchWriter` → verify SQL upsert calls
- **ML pipeline flow (TEST-02):** Synthetic DataFrame → real `run_training_pipeline()` (skip_shap=True) → verify model_registry dir populated → verify serving dir has pipeline.pkl → verify `generate_predictions()` returns values
- **API flow (TEST-03):** Pre-seed file fixtures → FastAPI TestClient → verify all endpoints return valid response shapes matching frontend TypeScript interfaces
- **Drift flow (TEST-04):** Synthetic features + errors → real `evaluate_and_trigger()` → verify retraining triggered → verify new model deployed → verify predictions regenerated

## Existing Test Coverage

### ML Tests (ml/tests/) — 30 files
- Unit tests for all 14 indicator families, lag features, transformations
- Unit tests for all model configs, training, evaluation, ranking
- Unit tests for SHAP explainability, model selection, deployment
- Unit tests for drift detection (detector, monitor, trigger)
- Integration tests for pipeline (training_pipeline, drift_pipeline, drift_retrain)
- Serialization tests for Parquet data transfer

### API Tests (services/api/tests/) — 11 files
- Unit tests for all 9 endpoints (health, ingest ×2, predict ×2, models ×2, market ×2)
- Service layer tests (prediction_service, market_service)
- Utility tests (yahoo_finance, kafka_producer, cronjob_triggers)

### What's Missing (Phase 30 Adds)
- **Cross-service integration tests** — Tests that span multiple service boundaries
- **Seed data script** — Reproducible test data for development and manual testing
- **End-to-end flow validation** — Full pipeline from ingestion through prediction delivery

## Key File Paths

```
scripts/seed-data.sh                              — Seed data script (currently stub)
db/init.sql                                       — Full schema definition
services/api/app/main.py                          — FastAPI app with all routers
services/api/app/config.py                        — Settings (TICKER_SYMBOLS, DB_URL, etc.)
services/api/app/routers/                         — All 5 routers (health, ingest, predict, market, models)
services/api/app/services/                        — Service layer (prediction_service, market_service, etc.)
services/kafka-consumer/consumer/                 — Kafka consumer (main, processor, db_writer)
ml/pipelines/training_pipeline.py                 — 11-step training pipeline
ml/pipelines/drift_pipeline.py                    — Drift-triggered retraining
ml/drift/trigger.py                               — evaluate_and_trigger() bridge
ml/drift/detector.py                              — 3 drift detector classes
ml/drift/monitor.py                               — DriftMonitor orchestrator
ml/pipelines/components/predictor.py              — generate_predictions() + save_predictions()
ml/pipelines/components/deployer.py               — deploy_winner_model()
ml/models/registry.py                             — ModelRegistry with activate/deactivate
k8s/storage/configmap.yaml                        — DB credentials (stockuser/devpassword123/stockdb)
```
