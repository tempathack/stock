# Roadmap — Stock Prediction Platform

**Granularity:** Fine | **Mode:** YOLO | **Parallelization:** Enabled  
**Milestone v1.0:** Phases 1–30 (Complete) | **Milestone v1.1:** Phases 31–50 (Production-Ready) | **Milestone v2.0:** Phases 51–57 (MinIO + KServe Migration)

---

## Phase Overview

| # | Phase | Goal | Requirements | Plans |
|---|-------|------|--------------|-------|
| 1 | Repo & Folder Scaffold | Project skeleton, docker-compose, logging | INFRA-03, INFRA-06, INFRA-09 | 3 |
| 2 | Minikube & K8s Namespaces | Cluster bootstrap, 5 namespaces | INFRA-01, INFRA-02, INFRA-04, INFRA-05 | 2 |
| 3 | FastAPI Base Service | /health endpoint, Dockerfile, K8s deployment | API-01–04 | 2 |
| 4 | PostgreSQL + TimescaleDB | DB deployed, schema initialized, indexes | DB-01–07 | 3 |
| 5 | Kafka via Strimzi | Strimzi operator, broker, both topics | KAFKA-01–05 | 2 |
| 6 | Yahoo Finance Ingestion Service | OHLCV fetch, validation, Kafka prodlluce | INGEST-01–03, INGEST-06 | 2 |
| 7 | FastAPI Ingestion Endpoints | /ingest/intraday and /ingest/historical wired | API-05, API-06 | 1 |
| 8 | K8s CronJobs for Ingestion | Scheduled intraday + historical CronJobs | INGEST-04, INGEST-05 | 1 |
| 9 | Kafka Consumers — Batch Writer | Consume topics, upsert to PostgreSQL | CONS-01–07 | 2 |
| 10 | Technical Indicators | All momentum/trend/volatility/volume indicators | FEAT-01–14 | 4 |
| 11 | Lag Features & Transformers | Lag features, rolling stats, scaler pipelines | FEAT-15–21 | 2 |
| 12 | Linear & Regularized Models | Train linear family, TimeSeriesSplit CV | MODEL-01–06, MODEL-19–21 | 3 |
| 13 | Tree-Based Models | Train tree/ensemble family | MODEL-07–12, MODEL-16–18 | 2 |
| 14 | Distance & Neural Models | Train KNN, SVR, MLP | MODEL-13–15 | 2 |
| 15 | Evaluation Framework | All metrics, model ranking, winner selection | EVAL-01–10 | 3 |
| 16 | SHAP Explainability | SHAP values for top 5 models, store summary | EVAL-11–12 | 1 |
| 17 | Kubeflow Pipeline — Data & Features | data_loading, feature_engineering, label_generation | KF-01–04 | 2 |
| 18 | Kubeflow Pipeline — Training & Eval | train_models, cross_validation, evaluation, comparison | KF-05–08 | 2 |
| 19 | Kubeflow Pipeline — Selection & Deploy | explainability, winner_selection, persistence, deployment | KF-09–12 | 2 |
| 20 | Kubeflow Pipeline — Definition & Trigger | Full pipeline definition, versioning, triggers | KF-13–15 | 2 |
| 21 | Drift Detection System | All 3 drift types, daily check, drift_logs | DRIFT-01–05 | 2 |
| 22 | Drift Auto-Retrain Trigger | Trigger Kubeflow on drift, redeploy, regen predictions | DRIFT-06–07 | 1 |
| 23 | FastAPI Prediction & Model Endpoints | /predict/{ticker}, /predict/bulk, /models/* | API-07–10 | 1 |
| 24 | FastAPI Market Endpoints | /market/overview, /market/indicators/{ticker} | API-11–12 | 1 |
| 25 | React App Bootstrap & Navigation | App skeleton, dark theme, nav, API client, K8s deploy | FE-01–06 | 1 |
| 26 | Frontend — /models Page | Model comparison, SHAP charts, fold charts, winner | FMOD-01–06 | 1 |
| 27 | Frontend — /forecasts Page | Forecast table, filters, comparison, stock detail, TA | FFOR-01–06 | 1 |
| 28 | Frontend — /dashboard Page | Treemap, intraday + historical charts, TA, metrics | FDASH-01–08 | 1 |
| 29 | Frontend — /drift Page | Active model card, rolling perf, drift timeline, retrain | FDRFT-01–05 | 1 |
| 30 | Integration Testing & Seed Data | End-to-end flow validation, seed script | TEST-01–05 | 5 |
| 31 | Live Model Inference API | Wire /predict + /models to DB and live inference | LIVE-01–05 | 3 |
| 32 | Frontend Live Data Integration | API-first loading states, remove mock-as-primary | LIVE-06–09 | 2 |
| 33 | ML Pipeline Container & Config | Dockerized ML pipeline with K8s ConfigMap | DEPLOY-01–02 | 2 |
| 34 | K8s ML CronJobs & Model Serving | Training/drift CronJobs, PVC, deploy-all.sh | DEPLOY-03–08 | 3 |
| 35 | Alembic Migration System | Schema versioning with initial migration | DBHARD-01–03 | 2 |
| 36 | Secrets Management & DB RBAC | K8s Secrets, remove hardcoded creds, DB roles | DBHARD-06–07 | 2 |
| 37 | Prometheus Metrics Instrumentation | /metrics on FastAPI + Kafka consumer | MON-01–03 | 2 |
| 38 | Grafana Dashboards & Alerting | Monitoring namespace, dashboards, alert rules | MON-04–08 | 3 |
| 39 | Structured Logging & Aggregation | structlog JSON + Loki centralized logs | MON-09–10 | 2 |
| 40 | SQLAlchemy Connection Pooling | Async engine, session factory, migrate services | DBHARD-04–05 | 2 |
| 41 | Database Backup Strategy | Daily pg_dump CronJob with retention | DBHARD-08 | 1 |
| 42 | Ensemble Stacking | StackingRegressor with Ridge meta-learner | ADVML-01–02 | 2 |
| 43 | Multi-Horizon Predictions | 1d/7d/30d horizons across pipeline, API, frontend | ADVML-03–06 | 3 |
| 44 | Feature Store | Precomputed features table with daily CronJob | ADVML-07–08 | 2 |
| 45 | WebSocket Live Prices | Real-time price updates backend→frontend | FENH-01–03 | 2 |
| 46 | Backtesting UI | /backtest endpoint + Backtest.tsx page | FENH-04–05 | 2 |
| 47 | Redis Caching Layer | Redis deploy + API response caching with TTL | PROD-01–03 | 2 |
| 48 | Rate Limiting & Deep Health Checks | slowapi middleware + comprehensive /health | PROD-04–05 | 2 |
| 49 | A/B Model Testing | Traffic splitting, assignment logging, results | PROD-06–08 | 2 |
| 50 | Export & Mobile Responsive | CSV/PDF export + Tailwind responsive layout | FENH-06–07 | 2 |
| 51 | MinIO Object Storage Deployment | MinIO in K8s, buckets, credentials | OBJST-01–04 | 2 |
| 52 | Model Registry S3 Backend | Refactor ModelRegistry to S3-compatible storage | OBJST-05–08 | 2 |
| 53 | Training & Drift Pipeline MinIO Integration | Pipelines read/write artifacts via MinIO | OBJST-09–12 | 2 |
| 54 | KServe Installation & Configuration | KServe CRDs, controller, ServingRuntime | KSERV-01–04 | 2 |
| 55 | KServe InferenceService Deployment | Replace uvicorn serving with KServe InferenceService | KSERV-05–08 | 2 | ✅ |
| 56 | API & Frontend KServe Adaptation | Prediction service calls KServe V2 inference protocol | KSERV-09–12 | 2 | ✅ |
| 57 | Migration Cleanup & E2E Validation | Remove PVC serving, validate full flow, update docs | KSERV-13–15 | 2 | ✅ |

---

## Phase Details

### Phase 1: Repo & Folder Scaffold

**Goal:** Create the production project skeleton — folder structure, docker-compose, logging config, and git initialization.

**Requirements:** INFRA-03, INFRA-06, INFRA-09

**Success Criteria:**
1. Full folder tree from Project_scope.md §15 exists with all placeholder files
2. docker-compose.yml present with service stubs for all microservices
3. Structured JSON logging utility (utils/logging.py) implemented and importable

---

### Phase 2: Minikube & K8s Namespaces

**Goal:** Local Kubernetes cluster bootstrapped with all 5 namespaces and orchestration scripts.

**Requirements:** INFRA-01, INFRA-02, INFRA-04, INFRA-05

**Success Criteria:**
1. setup-minikube.sh runs end-to-end and cluster is Ready
2. All 5 namespaces (ingestion, processing, storage, ml, frontend) active in cluster
3. deploy-all.sh present and applies all manifests in correct order


**Plans:** 2/2 plans executed

Plans:
- [x] 02-01-PLAN.md — Implement setup-minikube.sh and deploy-all.sh scripts
- [x] 02-02-PLAN.md — Execute scripts and verify live cluster state
---

### Phase 3: FastAPI Base Service

**Goal:** Production-ready FastAPI service with /health, Dockerfile, and K8s deployment.

**Requirements:** API-01, API-02, API-03, API-04

**Success Criteria:**
1. GET /health returns 200 with service name, version, status
2. Dockerfile builds successfully (multi-stage)
3. K8s Deployment + Service YAML applies to ingestion namespace
4. Pod is Running and /health is reachable via port-forward

**Plans:** 2/2 plans executed

Plans:
- [x] 03-01-PLAN.md — FastAPI app skeleton (config.py + health.py + main.py + tests)
- [x] 03-02-PLAN.md — Dockerfile, K8s manifests, deploy-all.sh integration

---

### Phase 4: PostgreSQL + TimescaleDB

**Goal:** PostgreSQL deployed in K8s with TimescaleDB, full schema, indexes, and partitioning.

**Requirements:** DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, DB-07

**Success Criteria:**
1. PostgreSQL pod Running with PVC bound in storage namespace
2. TimescaleDB extension enabled (`\dx` shows timescaledb)
3. All 6 tables created: stocks, ohlcv_daily, ohlcv_intraday, predictions, model_registry, drift_logs
4. Composite PKs, indexes, and date partitioning verified via `\d` inspection

**Plans:** 3/3 plans complete

Plans:
- [ ] 04-01-PLAN.md — Write db/init.sql with full schema (6 tables, hypertables, indexes, trigger)
- [ ] 04-02-PLAN.md — Update setup-minikube.sh (Secret + ConfigMap) and deploy-all.sh (uncomment Phase 4)
- [ ] 04-03-PLAN.md — Deploy to live Minikube cluster and verify all DB requirements

---

### Phase 5: Kafka via Strimzi

**Goal:** Strimzi operator deployed, Kafka broker running, both topics created with persistent storage.

**Requirements:** KAFKA-01, KAFKA-02, KAFKA-03, KAFKA-04, KAFKA-05

**Success Criteria:**
1. Strimzi operator pod Running in storage namespace
2. Kafka broker pod Running with persistent PVC
3. intraday-data topic exists and is producible/consumable
4. historical-data topic exists and is producible/consumable (verified with kafka-console tools)


**Plans:** 2/2 plans complete

Plans:
- [x] 05-01-PLAN.md — Write Kafka/Strimzi K8s manifests and update deployment scripts
- [x] 05-02-PLAN.md — Deploy to live cluster and verify full Kafka stack
---

### Phase 6: Yahoo Finance Ingestion Service

**Goal:** Python service fetches OHLCV from Yahoo Finance for S&P 500 tickers and produces validated records to Kafka.

**Requirements:** INGEST-01, INGEST-02, INGEST-03, INGEST-06

**Success Criteria:**
1. S&P 500 ticker list loaded (20-stock dev subset configurable via env var)
2. yfinance fetch returns OHLCV data for intraday and historical modes
3. Data validation rejects malformed/null records with structured error logs
4. Valid records published to correct Kafka topics (confirmed with consumer)


**Plans:** 2/2 plans complete

Plans:
- [ ] 06-01-PLAN.md — Test stubs, config extension, and YahooFinanceService implementation
- [ ] 06-02-PLAN.md — Kafka producer (OHLCVProducer) implementation with tests
---

### Phase 7: FastAPI Ingestion Endpoints

**Goal:** Wire /ingest/intraday and /ingest/historical endpoints to the ingestion service.

**Requirements:** API-05, API-06

**Success Criteria:**
1. POST /ingest/intraday triggers intraday fetch and returns job status
2. POST /ingest/historical triggers historical fetch and returns job status
3. Errors (Yahoo Finance unavailable, Kafka down) return structured error responses

---

### Phase 8: K8s CronJobs for Ingestion

**Goal:** Automated scheduled ingestion via K8s CronJobs for both intraday (daily) and historical (weekly) modes.

**Requirements:** INGEST-04, INGEST-05

**Success Criteria:**
1. cronjob-intraday.yaml deploys and fires on schedule during market hours
2. cronjob-historical.yaml deploys and fires weekly
3. CronJob logs show successful FastAPI calls

---

### Phase 9: Kafka Consumers — Batch Writer

**Goal:** Python consumer service reads both Kafka topics in micro-batches and upserts records into PostgreSQL idempotently.

**Requirements:** CONS-01, CONS-02, CONS-03, CONS-04, CONS-05, CONS-06, CONS-07

**Success Criteria:**
1. Consumer processes intraday-data topic and upserts to ohlcv_intraday (ON CONFLICT DO UPDATE)
2. Consumer processes historical-data topic and upserts to ohlcv_daily
3. Duplicate records produce no duplicate rows in PostgreSQL
4. Retry logic fires on transient DB errors; dead-letter records logged separately

---

### Phase 10: Technical Indicators

**Goal:** Compute all 14 technical indicator families (momentum, trend, volatility, volume, price action) as modular, testable functions.

**Requirements:** FEAT-01–FEAT-14

**Success Criteria:**
1. All momentum indicators (RSI, MACD, Stochastic) return correct values against reference data
2. All trend indicators (SMA/EMA/ADX) return correct values
3. All volatility indicators (Bollinger, ATR, Rolling Vol) computed correctly
4. All volume indicators (OBV, VWAP, Vol SMA, A/D) and return/log-return features computed correctly

**Plans:** 0/4 plans executed

Plans:
- [ ] 10-01-PLAN.md — Momentum indicators (RSI, MACD, Stochastic) + test infrastructure
- [ ] 10-02-PLAN.md — Trend indicators (SMA, EMA, ADX) + _true_range helper
- [ ] 10-03-PLAN.md — Volatility indicators (Bollinger, ATR, Rolling Vol)
- [ ] 10-04-PLAN.md — Volume indicators (OBV, VWAP, Vol SMA, A/D) + returns + compute_all_indicators

---

### Phase 11: Lag Features & Transformer Pipelines

**Goal:** Lag features, rolling window statistics, and three transformer pipeline variants built with no data leakage.

**Requirements:** FEAT-15–FEAT-21

**Success Criteria:**
1. Lag features (t-1, t-2, t-3, t-5, t-7, t-14, t-21) computed correctly with no look-ahead
2. Rolling stats (mean, std, min, max) over 5/10/21-day windows correct
3. Three sklearn Pipeline variants (StandardScaler, QuantileTransformer, MinMaxScaler) fit/transform without leakage
4. t+7 target generated correctly; rows with no future target dropped

---

### Phase 12: Linear & Regularized Models

**Goal:** Train all 6 linear-family regressors with TimeSeriesSplit CV and hyperparameter tuning.

**Requirements:** MODEL-01–MODEL-06, MODEL-19, MODEL-20, MODEL-21

**Success Criteria:**
1. All 6 models (LinearRegression, Ridge, Lasso, ElasticNet, BayesianRidge, HuberRegressor) trained
2. TimeSeriesSplit with ≥5 folds applied — no data shuffling
3. RandomizedSearchCV or Optuna tunes Ridge, Lasso, ElasticNet with defined search spaces
4. Per-model metrics (R², MAE, RMSE, MAPE, Directional Accuracy, fold variance) computed and stored

**Plans:** 3/3 plans complete

Plans:
- [x] 12-01-PLAN.md — Evaluation metrics (6 functions) + TimeSeriesSplit cross-validation
- [x] 12-02-PLAN.md — ModelConfig, TrainingResult dataclasses, LINEAR_MODELS search spaces
- [x] 12-03-PLAN.md — Model trainer: train_single_model, train_linear_models (18 runs), JSON persistence

---

### Phase 13: Tree-Based & Boosting Models

**Goal:** Train all 8 tree/ensemble regressors plus optional XGBoost/LightGBM/CatBoost boosters.

**Requirements:** MODEL-07–MODEL-12, MODEL-16, MODEL-17, MODEL-18

**Success Criteria:**
1. RF, GBM, HistGBM, ExtraTrees, DT, AdaBoost all trained with TimeSeriesSplit
2. RF and GBM hyperparameter-tuned via RandomizedSearchCV/Optuna
3. Optional boosters (XGBoost, LightGBM, CatBoost) trained if dependencies available
4. All metrics computed per model and stored in consistent format

**Plans:** 2/2 plans complete

Plans:
- [x] 13-01-PLAN.md — TREE_MODELS + BOOSTER_MODELS configs, search spaces, conditional imports
- [x] 13-02-PLAN.md — train_tree_models, train_all_models batch functions + tests

---

### Phase 14: Distance, SVM & Neural Models

**Goal:** Train KNeighborsRegressor, SVR (RBF), and MLPRegressor with TimeSeriesSplit.

**Requirements:** MODEL-13–MODEL-15

**Success Criteria:**
1. KNN, SVR, MLP trained with TimeSeriesSplit CV
2. SVR and MLP hyperparameter-tuned
3. All metrics computed per model and stored
4. Training completes within reasonable wall time (MLP early stopping configured)

**Plans:** 0/2 plans executed

Plans:
- [ ] 14-01-PLAN.md — DISTANCE_NEURAL_MODELS configs, search spaces, registration + config tests
- [ ] 14-02-PLAN.md — train_distance_neural_models batch fn, train_all_models update + trainer tests

---

### Phase 15: Evaluation Framework & Model Selection

**Goal:** Compute all 6 metrics per model, rank by OOS RMSE, penalize high-variance models, and select one winner.

**Requirements:** EVAL-01–EVAL-10

**Success Criteria:**
1. All 6 metrics (R², MAE, RMSE, MAPE, Directional Accuracy, fold stability) computed in-sample and OOS for every model
2. Models ranked by OOS RMSE primary, directional accuracy secondary, with variance penalty applied
3. ONE winner model identified and written to model_registry with is_active=true
4. Winner's artifact, scaler pipeline, feature list, and full metrics persisted to disk + DB

**Plans:** 0/3 plans executed

Plans:
- [ ] 15-01-PLAN.md — ranking.py: composite scoring, variance penalty, winner selection + tests
- [ ] 15-02-PLAN.md — registry.py: ModelRegistry (save/load/list artifacts + metadata) + tests
- [ ] 15-03-PLAN.md — Pipeline components (evaluator.py, model_selector.py) + tests

---

### Phase 16: SHAP Explainability

**Goal:** Compute SHAP values for the top 5 ranked models and store summary data for frontend consumption.

**Requirements:** EVAL-11, EVAL-12

**Success Criteria:**
1. TreeExplainer used for tree-based models; LinearExplainer for linear family; KernelExplainer as fallback for distance/neural
2. Feature importance rankings computed and stored for top 5 models
3. SHAP summary (beeswarm data) stored as JSON in model registry folder (shap_importance.json + shap_values.json)
4. Explainability output consumable by /models/comparison API endpoint

**Plans:** 1/1 plans executed

Plans:
- [x] 16-01-PLAN.md — SHAP analysis module, explainer pipeline component + tests

---

### Phase 17: Kubeflow Pipeline — Data & Feature Components

**Goal:** Install Kubeflow Pipelines in ml namespace and build containerized data_loading, feature_engineering, and label_generation components.

**Requirements:** KF-01, KF-02, KF-03, KF-04

**Success Criteria:**
1. Kubeflow Pipelines UI accessible via port-forward in ml namespace
2. data_loading component container builds and loads data from PostgreSQL
3. feature_engineering component applies all indicators and lag features correctly
4. label_generation component produces t+7 targets with no leakage

**Plans:** 2/2 plans executed

Plans:
- [x] 17-01-PLAN.md — Data loading component + KFP scaffold + tests
- [x] 17-02-PLAN.md — Feature engineering & label generation components + tests

---

### Phase 18: Kubeflow Pipeline — Training & Evaluation Components

**Goal:** Build containerized train_models (parallel), cross_validation, evaluation, and model_comparison pipeline components.

**Requirements:** KF-05, KF-06, KF-07, KF-08

**Success Criteria:**
1. train_models component trains all regressors in parallel where supported
2. cross_validation component applies TimeSeriesSplit ≥5 folds
3. evaluation component outputs all 6 metrics per model
4. model_comparison component ranks models and outputs winner candidate

**Plans:** 2/2 plans executed

Plans:
- [x] 18-01-PLAN.md — Data preparation (prepare_training_data) + training orchestration (train_all_models_pipeline) + tests
- [x] 18-02-PLAN.md — Cross-validation report component (generate_cv_report) + exports + tests

---

### Phase 19: Kubeflow Pipeline — Selection, Persistence & Deployment Components

**Goal:** Build explainability, winner_selection, model_persistence, and deployment Kubeflow components.

**Requirements:** KF-09, KF-10, KF-11, KF-12

**Success Criteria:**
1. explainability component computes SHAP for top 5 models as container step
2. winner_selection component writes final winner to model_registry (is_active=true)
3. model_persistence component saves artifact + scaler + feature list to artifact path
4. deployment component deploys winner model as live serving endpoint in ml namespace

**Plans:** 2/2 plans executed

Plans:
- [x] 19-01-PLAN.md — Registry activation methods (activate, deactivate, get_active) + deployment component (deployer.py) + tests
- [x] 19-02-PLAN.md — End-to-end pipeline integration tests (KF-09 → KF-12 chained flow)

---

### Phase 20: Kubeflow Pipeline — Full Definition & Trigger

**Goal:** Assemble all components into a single versioned, reproducible Kubeflow pipeline; wire manual and drift triggers.

**Requirements:** KF-13, KF-14, KF-15

**Success Criteria:**
1. training_pipeline.py defines the full 11-step pipeline as a Kubeflow DSL
2. Pipeline is versioned (pipeline version recorded in model_registry)
3. Pipeline can be triggered manually via Kubeflow UI or API call
4. drift_pipeline.py trigger invokes the training pipeline programmatically

**Plans:** 0/2 plans executed

Plans:
- [ ] 20-01-PLAN.md — Parquet serialisation + training pipeline orchestrator + versioning + tests
- [ ] 20-02-PLAN.md — Drift trigger + KFP pipeline definition + tests

---

### Phase 21: Drift Detection System

**Goal:** Implement all 3 drift detectors (data, prediction, concept), daily check job, and drift_logs persistence.

**Requirements:** DRIFT-01–DRIFT-05

**Success Criteria:**
1. Data drift detector computes KS-test and PSI between training feature distributions and recent 7-day data
2. Prediction drift detector flags when rolling prediction error exceeds configured threshold
3. Concept drift detector compares recent model performance vs. historical baseline
4. Daily drift check job runs after ingestion; all drift events logged to drift_logs with type, severity, details

---

### Phase 22: Drift Auto-Retrain Trigger

**Goal:** Wire drift detection output to automatic Kubeflow pipeline trigger, post-retrain redeployment, and prediction regeneration.

**Requirements:** DRIFT-06, DRIFT-07

**Success Criteria:**
1. Any detected drift event triggers full Kubeflow training pipeline programmatically
2. New winner model is selected and deployed, replacing the previous active model
3. Predictions for all S&P 500 stocks regenerated using new model and stored in predictions table

---

### Phase 23: FastAPI Prediction & Model Endpoints

**Goal:** Implement /predict/{ticker}, /predict/bulk, /models/comparison, and /models/drift endpoints backed by file-based model registry and drift logs.

**Requirements:** API-07, API-08, API-09, API-10

**Success Criteria:**
1. GET /predict/{ticker} returns 7-day forecast with confidence metrics from active model
2. GET /predict/bulk returns forecasts for all configured S&P 500 tickers
3. GET /models/comparison returns ranked model table with all 6 metrics
4. GET /models/drift returns current drift status, last check time, and any active alerts

**Plans:** 0/1 plans complete

Plans:
- [ ] 23-01-PLAN.md — Prediction & Model Endpoints (schemas, service, routers, tests) — pre-implemented, verify

---

### Phase 24: FastAPI Market Endpoints

**Goal:** Implement /market/overview (treemap data) and /market/indicators/{ticker} endpoints.

**Requirements:** API-11, API-12

**Success Criteria:**
1. GET /market/overview returns all S&P 500 stocks with market cap, sector, daily change for treemap rendering
2. GET /market/indicators/{ticker} returns all computed technical indicators for a stock

---

### Phase 25: React App Bootstrap & Navigation

**Goal:** React application scaffolded with dark Bloomberg theme, routing for 4 pages, API client, and K8s deployment.

**Requirements:** FE-01–FE-06

**Success Criteria:**
1. App runs locally and in K8s (frontend namespace) with dark theme applied
2. Navigation links to all 4 pages (/models, /forecasts, /dashboard, /drift)
3. API client layer (React Query or Zustand) configured and hitting FastAPI health endpoint
4. Dockerfile builds and K8s Deployment/Service applies in frontend namespace

**Plans:** 0/3 plans executed

Plans:
- [ ] 25-01-PLAN.md — Vite + React + Tailwind scaffold, dark theme, API client (FE-01, FE-02, FE-05)
- [ ] 25-02-PLAN.md — Routing, layout, sidebar navigation, page skeletons (FE-03, FE-04)
- [ ] 25-03-PLAN.md — Dockerfile, docker-compose update, build & dev server verification (FE-06)

---

### Phase 26: Frontend — /models Page

**Goal:** Full model comparison page with sortable/filterable table, in-sample vs OOS metrics, SHAP visualizations, and winner highlight.

**Requirements:** FMOD-01–FMOD-06

**Success Criteria:**
1. Table shows all trained models with R², MAE, RMSE, MAPE, Directional Accuracy columns, sortable by any column
2. In-sample and OOS metrics displayed side-by-side per model
3. Winner model row highlighted with reasoning tooltip
4. SHAP feature importance bar chart rendered for selected model
5. SHAP beeswarm plot and fold-by-fold performance chart rendered

**Plans:** 0/3 plans executed

Plans:
- [ ] 26-01-PLAN.md — Install Recharts, Add Types, Build Model Comparison Table (FMOD-01, FMOD-02, FMOD-03)
- [ ] 26-02-PLAN.md — SHAP Charts (Bar + Beeswarm) and Fold Performance Chart (FMOD-04, FMOD-05, FMOD-06)
- [ ] 26-03-PLAN.md — Model Detail Expansion, Polish, and Build Verification

---

### Phase 27: Frontend — /forecasts Page

**Goal:** Full forecasts page with S&P 500 table, multi-filter, stock comparison, per-stock detail with TA chart overlay and SHAP panel.

**Requirements:** FFOR-01–FFOR-06

**Success Criteria:**
1. Table shows all S&P 500 stocks with current price, predicted price, expected return %, confidence, trend badge
2. Filters for sector, return range, and confidence work correctly
3. Multi-stock comparison view renders selected stocks side-by-side
4. Per-stock detail shows historical + 7-day forecast chart
5. TA indicators (RSI, MACD, Bollinger Bands) overlay on detail chart and SHAP panel rendered

**Plans:** 0/3 plans executed

Plans:
- [ ] 27-01-PLAN.md — Forecast types, mock data, ForecastTable & ForecastFilters (FFOR-01, FFOR-02)
- [ ] 27-02-PLAN.md — StockComparisonPanel, StockDetailChart, IndicatorOverlayCharts (FFOR-03, FFOR-04, FFOR-05)
- [ ] 27-03-PLAN.md — StockShapPanel, responsive polish, edge cases, build verification (FFOR-06)

---

### Phase 28: Frontend — /dashboard Page ✅ COMPLETE (2026-03-22, 3/3 plans executed)

**Goal:** Full market dashboard with interactive treemap, intraday candlestick, historical chart, TA panel, and metric cards.

**Requirements:** FDASH-01–FDASH-08

**Success Criteria:**
1. S&P 500 treemap renders with market cap sizing and daily performance color gradient (green/red)
2. Clicking a treemap cell opens stock detail view
3. Intraday minute-level candlestick chart renders for selected stock
4. Historical OHLCV chart renders with adjustable timeframe selector
5. TA panel (RSI, MACD, Bollinger Bands, MAs, Volume, VWAP) renders correctly with key metric cards

Plans:
- [x] 28-01-PLAN.md — Treemap types, mock data, MarketTreemap, MetricCards, dashboard wiring (FDASH-01, FDASH-02, FDASH-06, FDASH-08)
- [x] 28-02-PLAN.md — CandlestickChart, HistoricalChart, TimeframeSelector (FDASH-03, FDASH-04)
- [x] 28-03-PLAN.md — DashboardTAPanel, responsive polish, build verification (FDASH-05, FDASH-07, FDASH-08)

---

### Phase 29: Frontend — /drift Page

**Goal:** Full drift monitoring page with active model card, rolling performance charts, drift alert timeline, retrain status, and feature distributions.

**Requirements:** FDRFT-01–FDRFT-05

**Success Criteria:**
1. Active model card shows name, version, and trained date
2. Rolling performance chart (RMSE, MAE, Directional Accuracy over time) renders
3. Drift alert timeline shows all historical drift events with type, severity, timestamp
4. Retraining status panel shows last retrain date, in-progress indicator, old vs new model metrics
5. Feature distribution charts show training vs. recent data per feature

---

### Phase 30: Integration Testing & Seed Data

**Goal:** Validate the full end-to-end pipeline, all cross-service flows, drift cycle, and provide seed data tooling.

**Requirements:** TEST-01–TEST-05

**Success Criteria:**
1. Ingest → Kafka → PostgreSQL flow validated: data appears in correct tables after CronJob fires
2. PostgreSQL → Kubeflow → model registry → serving flow validated: model deployed and /predict returns values
3. FastAPI prediction + market endpoints return correct data visible in React frontend
4. Drift detection → retrain → redeploy cycle runs end-to-end without manual intervention
5. seed-data.sh populates all tables with realistic test data for development

**Plans:** 5/5 plans complete

Plans:
- [x] 30-01-PLAN.md — seed-data.sh: populate all 6 PostgreSQL tables with realistic S&P 500 test data
- [x] 30-02-PLAN.md — Integration test: ingest → Kafka → PostgreSQL flow (TEST-01)
- [x] 30-03-PLAN.md — Integration test: ML pipeline → model registry → serving → predictions (TEST-02)
- [x] 30-04-PLAN.md — Integration test: FastAPI endpoints → frontend contract validation (TEST-03)
- [x] 30-05-PLAN.md — Integration test: drift detection → retraining → redeployment cycle (TEST-04)

---

## v1.1 Phases — Production-Ready

> **Milestone:** v1.1 — Phases 31–50  
> **Strategy:** 4 waves — Foundation (31–36), Observability (37–41), Features (42–46), Hardening (47–50)  
> **ML Orchestration:** Plain K8s CronJobs (matching ingestion pattern); KFP containerization deferred to v2  
> **Dependencies:** Wave 1–2 can run in parallel; Wave 3 depends on Wave 1; Wave 4 depends on Waves 2+3  

---

### Wave 1 — Foundation (31–36)

---

### Phase 31: Live Model Inference API

**Goal:** Wire /predict and /models endpoints to PostgreSQL and live model inference, with graceful fallback to cached file responses.

**Requirements:** LIVE-01, LIVE-02, LIVE-03, LIVE-04, LIVE-05

**Success Criteria:**
1. GET /predict/AAPL returns live prediction from loaded pipeline.pkl (not cached JSON)
2. GET /predict/bulk returns predictions for all configured tickers via live inference
3. GET /models/comparison queries model_registry table when DATABASE_URL is set
4. GET /models/drift queries drift_logs table when DATABASE_URL is set
5. All endpoints fall back to file-based responses when DB or model is unavailable

**Plans:** 3/3 plans executed

Plans:
- [x] 31-01-PLAN.md — Implement database.py helper + DB query functions + live inference in prediction_service.py
- [x] 31-02-PLAN.md — Update predict.py + models.py routers for DB-first with file fallback logic
- [x] 31-03-PLAN.md — Add /models/drift/rolling-performance and /models/retrain-status endpoints + schemas

---

### Phase 32: Frontend Live Data Integration

**Goal:** Replace mock-as-primary pattern with API-first loading states across all frontend pages.

**Requirements:** LIVE-06, LIVE-07, LIVE-08, LIVE-09

**Success Criteria:**
1. All pages show LoadingSpinner while API data is fetching (no flash of mock data)
2. Mock data only appears when API returns error (error fallback, not primary)
3. Drift page uses new useRollingPerformance and useRetrainStatus hooks
4. All existing React Query hooks remain functional with live API backend

**Plans:** 2/2 plans executed

Plans:
- [x] 32-01-PLAN.md — Refactor Dashboard/Forecasts/Models pages to API-first loading (mock only on error)
- [x] 32-02-PLAN.md — Add useRollingPerformance + useRetrainStatus hooks; refactor Drift.tsx to live API

---

### Phase 33: ML Pipeline Container & Config

**Goal:** Dockerized ML pipeline container and K8s ConfigMap for the ML namespace.

**Requirements:** DEPLOY-01, DEPLOY-02

**Success Criteria:**
1. ml/Dockerfile builds successfully with all ML dependencies (scikit-learn, xgboost, lightgbm, catboost, shap)
2. Docker image runs `python -m ml.pipelines.training_pipeline` without import errors
3. K8s ConfigMap provides DATABASE_URL, MODEL_REGISTRY_DIR, SERVING_DIR, DRIFT_LOG_DIR
4. ConfigMap references PostgreSQL service at postgresql.storage.svc.cluster.local:5432

**Plans:** 2/2 plans executed

Plans:
- [x] 33-01-PLAN.md — Create ml/Dockerfile (Python 3.11, multi-stage, all ML deps, no EXPOSE)
- [x] 33-02-PLAN.md — Create k8s/ml/configmap.yaml with DATABASE_URL, registry/serving paths

---

### Phase 34: K8s ML CronJobs & Model Serving

**Goal:** Scheduled weekly training and daily drift CronJobs, persistent model storage, and finalized deploy-all.sh.

**Requirements:** DEPLOY-03, DEPLOY-04, DEPLOY-05, DEPLOY-06, DEPLOY-07, DEPLOY-08

**Success Criteria:**
1. `kubectl get cronjobs -n ml` shows weekly-training (Sunday 03:00) and daily-drift (weekdays 22:00) CronJobs
2. Model artifacts persist across pod restarts via PVC (not emptyDir)
3. deploy-all.sh phases 17–25 are active (ML pipeline, drift, prediction API, frontend)
4. Drift trigger CLI (`python -m ml.drift.trigger --auto-retrain`) works in container
5. Manually triggered training job completes and writes pipeline.pkl to model PVC

**Plans:** 0/3 plans

Plans:
- [ ] 34-01-PLAN.md — Create cronjob-training.yaml, cronjob-drift.yaml, model-pvc.yaml
- [ ] 34-02-PLAN.md — Fix model-serving.yaml (emptyDir→PVC), wire drift trigger CLI in trigger.py
- [ ] 34-03-PLAN.md — Uncomment deploy-all.sh phases 17–25, add ML CronJob deployment phases

---

### Phase 35: Alembic Migration System

**Goal:** Database schema versioning with Alembic, initial migration matching init.sql.

**Requirements:** DBHARD-01, DBHARD-02, DBHARD-03

**Success Criteria:**
1. `alembic upgrade head` on empty DB creates all 6 tables with correct schema
2. `alembic downgrade base` cleanly removes all tables
3. `alembic revision --autogenerate` detects schema changes against live DB
4. API Dockerfile runs `alembic upgrade head` as startup init step

**Plans:** 2/2 plans executed

Plans:
- [x] 35-01-PLAN.md — Add psycopg2-binary, create ORM models (orm.py), alembic.ini, env.py, initial migration (DBHARD-01, DBHARD-02)
- [x] 35-02-PLAN.md — Create entrypoint.sh, update Dockerfile for alembic upgrade head on startup (DBHARD-03)

---

### Phase 36: Secrets Management & DB RBAC

**Goal:** Replace hardcoded credentials with K8s Secrets and implement database role-based access.

**Requirements:** DBHARD-06, DBHARD-07

**Success Criteria:**
1. `kubectl get secrets -n storage` shows stock-platform-secrets (no plaintext passwords in configmaps)
2. All deployments reference Secret for DATABASE_URL (not ConfigMap)
3. stock_readonly role used by API service, stock_writer used by consumer + ML pipeline
4. Raw secrets YAML is gitignored; README documents Sealed Secrets workflow

**Plans:** 2/2 plans

Plans:
- [x] 36-01-PLAN.md — Create K8s Secret, remove hardcoded creds from configmaps/source, update deployments to reference secret
- [x] 36-02-PLAN.md — Add DB RBAC roles (stock_readonly, stock_writer), per-service DATABASE_URL configs

---

### Wave 2 — Observability (37–41)

---

### Phase 37: Prometheus Metrics Instrumentation

**Goal:** Prometheus metrics endpoints on FastAPI and Kafka consumer services.

**Requirements:** MON-01, MON-02, MON-03

**Success Criteria:**
1. `curl http://stock-api:8000/metrics` returns Prometheus text format with request histograms
2. Custom prediction metrics (prediction_requests_total, prediction_latency_seconds) visible in /metrics
3. Kafka consumer exposes /metrics on port 9090 with messages_consumed_total, batch_write_duration
4. Kafka consumer K8s deployment has prometheus.io/scrape annotations

**Plans:** 2/2 plans executed

Plans:
- [x] 37-01-PLAN.md — Wire prometheus-fastapi-instrumentator + custom prediction metric counters/histograms
- [x] 37-02-PLAN.md — Add prometheus_client to Kafka consumer with HTTP metrics server on port 9090

---

### Phase 38: Grafana Dashboards & Alerting

**Goal:** Monitoring namespace with Prometheus server, Grafana, provisioned dashboards, and alert rules.

**Requirements:** MON-04, MON-05, MON-06, MON-07, MON-08

**Success Criteria:**
1. Prometheus server running in monitoring namespace, scraping all ServiceMonitors
2. Grafana accessible via port-forward with 3 provisioned dashboards
3. API Health dashboard shows request rate, latency percentiles, error rate
4. ML Performance dashboard shows model RMSE trend and drift events timeline
5. At least one alert rule fires (testable via synthetic drift event)

**Plans:** 3/3 plans

Plans:
- [x] 38-01-PLAN.md — Create k8s/monitoring/ manifests (namespace, Prometheus deployment, Grafana deployment)
- [x] 38-02-PLAN.md — Create Grafana dashboard JSON provisioning (API health, ML performance, drift timeline)
- [x] 38-03-PLAN.md — Configure alert rules (drift severity, error rate, consumer lag) and notification channels

---

### Phase 39: Structured Logging & Aggregation

**Goal:** JSON structured logging with centralized log aggregation via Loki.

**Requirements:** MON-09, MON-10

**Success Criteria:**
1. `kubectl logs -n ingestion <api-pod> | jq` parses valid JSON (structured output)
2. Kafka consumer logs are also structured JSON
3. Loki + Promtail DaemonSet collecting logs from all namespaces
4. Grafana Loki datasource allows log querying by namespace, pod, level

**Plans:** 2/2 plans written

**Scope Exclusions:** Log-based alerting rules, distributed tracing (OpenTelemetry), long-term log retention policies

Plans:
- [ ] 39-01-PLAN.md — Configure structlog JSON output in FastAPI + Kafka consumer (uvicorn routing, request middleware, schema alignment)
- [ ] 39-02-PLAN.md — Deploy Loki + Promtail DaemonSet, add Grafana Loki datasource

---

### Phase 40: SQLAlchemy Connection Pooling

**Goal:** Replace raw psycopg2 with SQLAlchemy async engine and connection pooling.

**Requirements:** DBHARD-04, DBHARD-05

**Success Criteria:**
1. services/api/app/db.py provides async engine with pool_size=10, max_overflow=20
2. market_service.py uses SQLAlchemy async sessions instead of raw psycopg2
3. prediction_service.py DB queries use sessions from db.py
4. Connection pool metrics visible (active/idle connections via health endpoint)

**Plans:** 2/2 plans executed

Plans:
- [x] 40-01-PLAN.md — Create db.py with SQLAlchemy async engine, session factory, pool metrics in /health
- [x] 40-02-PLAN.md — Migrate market_service.py + prediction_service.py to async sessions, update routers

---

### Phase 41: Database Backup Strategy

**Goal:** Automated daily pg_dump backups with retention policy.

**Requirements:** DBHARD-08

**Success Criteria:**
1. K8s CronJob runs daily at 04:00 UTC in storage namespace
2. pg_dump produces custom-format backup file in /backups/ volume
3. Retention script keeps 7 daily + 4 weekly backups
4. Manual restore from backup verified: `pg_restore -d stockdb backup.dump`

**Plans:** 1/1 plans

Plans:
- [x] 41-01-PLAN.md — Create k8s/storage/cronjob-backup.yaml with pg_dump, PVC, and retention script

---

### Wave 3 — Features (42–46)

---

### Phase 42: Ensemble Stacking

**Goal:** StackingRegressor ensemble with Ridge meta-learner from top-N base models.

**Requirements:** ADVML-01, ADVML-02

**Success Criteria:**
1. ml/models/ensemble.py provides StackingEnsemble class wrapping sklearn StackingRegressor
2. Ensemble uses Ridge meta-learner trained on OOS predictions from top-N base models
3. Ensemble integrated into training_pipeline.py as optional step after model ranking
4. Ensemble model appears in registry with comparative RMSE metrics

**Plans:** 2/2 plans executed

Plans:
- [x] 42-01-PLAN.md — Create ml/models/ensemble.py with StackingEnsemble class + unit tests
- [x] 42-02-PLAN.md — Integrate ensemble into training_pipeline.py after ranking step

---

### Phase 43: Multi-Horizon Predictions

**Goal:** Support 1-day, 7-day, and 30-day prediction horizons across the full pipeline.

**Requirements:** ADVML-03, ADVML-04, ADVML-05, ADVML-06

**Success Criteria:**
1. label_generator.py generates target_1d, target_7d, target_30d columns
2. Training pipeline trains separate model suite per horizon
3. GET /predict/AAPL?horizon=1 vs ?horizon=30 return different predictions
4. Forecasts.tsx has 1D/7D/30D toggle that switches displayed horizon

**Plans:** 3/3 plans executed

Plans:
- [x] 43-01-PLAN.md — Multi-horizon label generation + per-horizon training pipeline loop + deployer + predictor
- [x] 43-02-PLAN.md — API ?horizon query param on /predict endpoints + /predict/horizons discovery + schemas
- [x] 43-03-PLAN.md — Frontend HorizonToggle component + useAvailableHorizons hook + Forecasts.tsx integration

---

### Phase 44: Feature Store

**Goal:** Precomputed features table with daily CronJob, consumed by training pipeline.

**Requirements:** ADVML-07, ADVML-08

**Success Criteria:**
1. feature_store PostgreSQL table stores (ticker, date, feature_name, feature_value)
2. Daily CronJob computes all features and writes to feature_store
3. Training pipeline reads from feature_store instead of computing features on-the-fly
4. /market/indicators endpoint optionally serves from feature_store (faster response)

**Plans:** 0/2 plans

Plans:
- [ ] 44-01-PLAN.md — feature_store table DDL + ORM model + ml/features/store.py (compute/write/read) + tests
- [ ] 44-02-PLAN.md — K8s CronJob (daily 18:00 UTC) + CLI entry point + training pipeline feature store integration

---

### Phase 45: WebSocket Live Prices

**Goal:** Real-time price updates streamed from backend to frontend via WebSocket.

**Requirements:** FENH-01, FENH-02, FENH-03

**Success Criteria:**
1. WebSocket endpoint at /ws/prices pushes JSON price updates every 5s during market hours
2. useWebSocket.ts hook manages connection lifecycle with auto-reconnect
3. Dashboard CandlestickChart updates in real-time without page refresh
4. WebSocket gracefully disconnects outside market hours

**Plans:** 2/2 plans

Plans:
- [x] 45-01-PLAN.md — WebSocket /ws/prices endpoint with PriceBroadcaster and market-hours-aware feed loop
- [x] 45-02-PLAN.md — useWebSocket.ts hook with auto-reconnect, live CandlestickChart updates, connection status dot

---

### Phase 46: Backtesting UI

**Goal:** Backtest API endpoint and frontend page with actual vs predicted comparison.

**Requirements:** FENH-04, FENH-05

**Success Criteria:**
1. GET /backtest/AAPL?start=2025-01-01&end=2025-12-31 returns actual vs predicted series
2. Backtest.tsx renders dual-line chart (actual price + predicted price) with error band
3. Summary metrics (RMSE, MAE, directional accuracy) displayed below chart
4. Page accessible from navigation sidebar

**Plans:** 2/2 plans executed

Plans:
- [x] 46-01-PLAN.md — Backend: /backtest/{ticker} endpoint + backtest_service (SQL join, numpy metrics)
- [x] 46-02-PLAN.md — Frontend: Backtest.tsx page + BacktestChart + BacktestMetricsSummary + sidebar nav

---

### Wave 4 — Hardening (47–50)

---

### Phase 47: Redis Caching Layer

**Goal:** Redis deployment with API response caching and invalidation.

**Requirements:** PROD-01, PROD-02, PROD-03

**Success Criteria:**
1. Redis running in storage namespace (single replica, 256Mi)
2. Second request to /market/overview returns in <5ms (cache hit)
3. Cache TTLs: market_overview 30s, bulk_predictions 60s, model_comparison 300s
4. Cache automatically invalidated on model retrain event

**Plans:** 2/2 plans

Plans:
- [x] 47-01-PLAN.md — Deploy Redis (k8s/storage/redis-deployment.yaml), create services/api/app/cache.py
- [x] 47-02-PLAN.md — Wire caching into routers with configurable TTL and retrain invalidation

---

### Phase 48: Rate Limiting & Deep Health Checks

**Goal:** API rate limiting and comprehensive health checking.

**Requirements:** PROD-04, PROD-05

**Success Criteria:**
1. 101st request in 1 minute returns 429 with Retry-After header
2. /predict/* limited to 30/min per IP; /ingest/* limited to 10/min
3. GET /health returns {status: "degraded"} when DB is unreachable
4. Health check validates: DB connectivity, Kafka reachability, model freshness (<7d), prediction staleness (<24h)

**Plans:** 2/2 plans

Plans:
- [x] 48-01-PLAN.md — slowapi rate limiting: rate_limit.py module, per-endpoint decorators (100/min global, 30/min /predict, 10/min /ingest), /health exempt, ConfigMap env vars
- [x] 48-02-PLAN.md — Deep health checks: health_service.py (check_db, check_kafka, check_model_freshness, check_prediction_staleness), /health degraded detection, /health/deep endpoint, unit tests

---

### Phase 49: A/B Model Testing

**Goal:** Concurrent model evaluation with traffic splitting and accuracy comparison.

**Requirements:** PROD-06, PROD-07, PROD-08

**Success Criteria:**
1. model_registry supports multiple active models with traffic_weight field
2. Prediction requests are routed to models proportional to traffic_weight
3. ab_test_assignments table logs model_id, ticker, predicted_price per request
4. GET /models/ab-results returns accuracy comparison between A and B models

**Plans:** 2/2 plans

Plans:
- [x] 49-01-PLAN.md — Schema migration (traffic_weight + ab_test_assignments), ab_service.py, A/B prediction routing
- [x] 49-02-PLAN.md — GET /models/ab-results endpoint, comparison enrichment, canary K8s manifest

---

### Phase 50: Export & Mobile Responsive

**Goal:** Data export functionality and mobile-responsive layout.

**Requirements:** FENH-06, FENH-07

**Success Criteria:**
1. CSV export button on Forecasts, Models, and Backtest pages downloads correct data
2. PDF export generates downloadable report with charts
3. Dashboard treemap converts to stacked list on mobile (<640px)
4. All tables convert to card layout on mobile; no horizontal scroll at 375px

**Plans:** 2/2 plans

Plans:
- [x] 50-01-PLAN.md — Add CSV/PDF export buttons to Forecasts, Models, Backtest pages (client-side Blob)
- [x] 50-02-PLAN.md — Audit and fix responsive layout with Tailwind sm/md/lg breakpoints

---

### Phase 51: MinIO Object Storage Deployment

**Goal:** Deploy MinIO to the K8s storage namespace as the S3-compatible object store for all ML artifacts.

**Requirements:** OBJST-01, OBJST-02, OBJST-03, OBJST-04

**Success Criteria:**
1. MinIO pod Running in storage namespace with PVC-backed persistent volume (10Gi)
2. `model-artifacts` and `drift-logs` buckets created via init Job
3. K8s Secret holds MinIO root credentials (access key + secret key)
4. ConfigMap exposes MINIO_ENDPOINT, MINIO_BUCKET_MODELS, MINIO_BUCKET_DRIFT env vars
5. mc (MinIO Client) or AWS CLI can list/put/get objects from within the cluster

**Plans:** 2/2 plans executed

Plans:
- [x] 51-01-PLAN.md — MinIO K8s manifests (Deployment, Service, PVC, Secret, ConfigMap) in k8s/storage/
- [x] 51-02-PLAN.md — Bucket initialization Job + connectivity verification from ml namespace

---

### Phase 52: Model Registry S3 Backend

**Goal:** Refactor ModelRegistry from filesystem-based persistence to S3-compatible MinIO storage.

**Requirements:** OBJST-05, OBJST-06, OBJST-07, OBJST-08

**Success Criteria:**
1. boto3 (or minio SDK) added to ml/requirements.txt
2. ModelRegistry.save_model() uploads pipeline.pkl, metadata.json, features.json to s3://model-artifacts/{model_name}/{version}/
3. ModelRegistry.load_model() downloads and deserializes from MinIO
4. get_winner(), activate_model(), get_active_model() operate against MinIO-stored metadata
5. All existing ml/tests/ for registry pass against MinIO backend (via moto or MinIO testcontainer)
6. Filesystem fallback mode retained via STORAGE_BACKEND=local|s3 env var for local dev

**Plans:** 2/2 plans executed

Plans:
- [x] 52-01-PLAN.md — Add S3StorageBackend class implementing save/load/list/delete with boto3, update registry.py
- [x] 52-02-PLAN.md — Update tests with moto S3 mock, add STORAGE_BACKEND env var toggle

---

### Phase 53: Training & Drift Pipeline MinIO Integration

**Goal:** Update training and drift pipelines to persist all artifacts to MinIO instead of local PVC.

**Requirements:** OBJST-09, OBJST-10, OBJST-11, OBJST-12

**Success Criteria:**
1. training_pipeline.py persists winner model artifacts to MinIO via updated ModelRegistry
2. deployer.py uploads winner to s3://model-artifacts/serving/active/ instead of filesystem copy
3. drift_pipeline.py reads baseline model and writes drift logs to s3://drift-logs/
4. K8s CronJob manifests no longer mount model-artifacts-pvc; use MinIO env vars instead
5. drift_pipeline retrain cycle stores new winner in MinIO and updates serving path

**Plans:** 2/2 plans executed

Plans:
- [x] 53-01-PLAN.md — S3Storage client, ModelRegistry S3 backend, deployer S3 deploy, training pipeline S3 run results
- [x] 53-02-PLAN.md — DriftLogger S3 persistence, drift pipeline S3 retraining log, K8s CronJob PVC→MinIO migration

---

### Phase 54: KServe Installation & Configuration

**Goal:** Install KServe in the ml namespace and configure it to pull models from MinIO.

**Requirements:** KSERV-01, KSERV-02, KSERV-03, KSERV-04

**Success Criteria:**
1. KServe controller pod Running in ml namespace (or kserve namespace)
2. KServe CRDs installed: InferenceService, ServingRuntime, ClusterServingRuntime
3. KServe configured with S3 credentials Secret for MinIO access (serviceAccountConfig or storage-initializer secret)
4. ClusterServingRuntime for sklearn (mlserver or custom) deployed and ready
5. `kubectl get inferenceservices` returns empty but operational

**Plans:** 2/2 plans executed

Plans:
- [x] 54-01-PLAN.md — Install cert-manager + KServe (RawDeployment mode), S3 credentials Secret + ServiceAccount, deploy-all.sh integration
- [x] 54-02-PLAN.md — Deploy custom ClusterServingRuntime for sklearn (MLServer), verify full Phase 54 checklist

---

### Phase 55: KServe InferenceService Deployment ✅ COMPLETE

**Goal:** Replace the custom uvicorn model-serving Deployment with a KServe InferenceService CR.

**Requirements:** KSERV-05, KSERV-06, KSERV-07, KSERV-08

**Success Criteria:**
1. InferenceService CR deployed pointing to s3://model-artifacts/serving/active/
2. KServe predictor pod Running, storage-initializer downloads model from MinIO
3. V2 inference protocol endpoint responds to POST /v2/models/{model}/infer
4. Readiness and liveness probes pass; autoscaling scales to zero after idle timeout
5. Old model-serving.yaml Deployment scaled to 0 (kept for rollback) but all traffic goes to KServe

**Plans:** 2/2 plans executed

Plans:
- [x] 55-01-PLAN.md — Primary InferenceService CR (stock-model-serving) with MinIO storageUri, deploy-all.sh integration
- [x] 55-02-PLAN.md — Canary InferenceService CR, autoscaling config, legacy model-serving scale to 0

---

### Phase 56: API & Frontend KServe Adaptation

**Goal:** Update the prediction API to call KServe's V2 inference endpoint instead of loading models from disk.

**Requirements:** KSERV-09, KSERV-10, KSERV-11, KSERV-12

**Success Criteria:**
1. prediction_service.py calls KServe InferenceService via HTTP (V2 protocol) instead of loading pipeline.pkl
2. KSERVE_INFERENCE_URL env var configurable in API ConfigMap
3. GET /predict/{ticker} and /predict/bulk return same response schema as before (backward-compatible)
4. Fallback to cached predictions when KServe endpoint is unreachable
5. A/B model testing (Phase 49) uses KServe canary traffic splitting instead of application-level routing

**Plans:** 2/2 plans

Plans:
- [x] 56-01-PLAN.md — KServe V2 inference client & prediction service refactor (KSERV-09/10/11)
- [x] 56-02-PLAN.md — A/B testing via KServe canary & backward-compatible responses (KSERV-12/11)

---

### Phase 57: Migration Cleanup & E2E Validation

**Goal:** Remove legacy PVC-based serving artifacts, validate the full MinIO + KServe pipeline end-to-end.

**Requirements:** KSERV-13, KSERV-14, KSERV-15

**Success Criteria:**
1. Old model-serving.yaml Deployment deleted from k8s/ml/
2. model-artifacts-pvc reclaimed or repurposed (no longer used for model serving)
3. deploy-all.sh updated with MinIO, KServe, and InferenceService deployment steps
4. E2E validated: ingest → train → MinIO upload → KServe InferenceService → API /predict → frontend
5. Drift detection → retrain → MinIO update → KServe rollout → new predictions validated
6. README.md updated with MinIO + KServe architecture diagram and setup instructions

**Plans:** 2/2 plans

Plans:
- [x] 57-01-PLAN.md — Remove legacy manifests, update deploy-all.sh, reclaim PVC
- [x] 57-02-PLAN.md — Full E2E smoke test (train → serve → predict → drift → retrain), update README

### Phase 58: Fix docker-compose runtime: kafka-consumer configurable broker + ml-pipeline entrypoint fix

**Goal:** Fix two docker-compose runtime crashes: kafka-consumer hardcoded K8s broker default and ml-pipeline ValueError when TICKERS not provided via CLI.
**Requirements**: FIX-KAFKA, FIX-ML
**Depends on:** Phase 57
**Plans:** 1/1 plans complete

Plans:
- [ ] 58-01-PLAN.md — Fix ConsumerSettings broker default, inject env vars in docker-compose, fix __main__ TICKERS env fallback

### Phase 59: Minikube E2E validation: start cluster, deploy full stack, run ingest-train-serve flow

**Goal:** Start Minikube cluster, deploy full stack, run ingest-train-KServe serve E2E flow, close all Phase 57 human_verification gaps.
**Requirements**: KSERV-15
**Depends on:** Phase 58
**Plans:** 3/4 plans complete

Plans:
- [ ] 59-01-PLAN.md — Pre-flight: create secrets from examples, patch deploy-all.sh (stock-api build + Redis + conditional KServe wait)
- [ ] 59-02-PLAN.md — Cluster bootstrap: setup-minikube.sh + deploy-all.sh SKIP_KSERVE_WAIT=true, human verification
- [ ] 59-03-PLAN.md — Data + training: seed DB, trigger training, verify MinIO artifact, KServe Ready, /predict/AAPL E2E
- [ ] 59-04-PLAN.md — Drift + frontend: trigger drift CronJob, verify drift_logs, frontend /forecasts and /drift human verification

### Phase 60: Fix model_name unknown in predict response: fetch metadata from MinIO or DB on API startup

**Goal:** Eliminate "unknown" model_name in /predict responses by loading serving_config.json from MinIO (or DB fallback) at API startup via a module-level cache
**Requirements**: PRED-MNAME-01, PRED-MNAME-02, PRED-MNAME-03, PRED-MNAME-04, PRED-MNAME-05
**Depends on:** Phase 59
**Plans:** 2 plans

Plans:
- [ ] 60-01-PLAN.md — model_metadata_cache.py (MinIO+DB startup load), boto3 dep, lifespan wire, inference functions updated
- [ ] 60-02-PLAN.md — K8s ConfigMap MINIO vars + minio-secrets secretRef + human E2E verify

---

## Requirement Traceability

| REQ-ID | Phase |
|--------|-------|
| INFRA-01–02 | 2 |
| INFRA-03, INFRA-06, INFRA-09 | 1 |
| INFRA-04–05 | 2 |
| INFRA-07–08 | Enforced throughout all phases |
| API-01–04 | 3 |
| API-05–06 | 7 |
| API-07–10 | 23 |
| API-11–12 | 24 |
| DB-01–07 | 4 |
| KAFKA-01–05 | 5 |
| INGEST-01–03, INGEST-06 | 6 |
| INGEST-04–05 | 8 |
| CONS-01–07 | 9 |
| FEAT-01–14 | 10 |
| FEAT-15–21 | 11 |
| MODEL-01–06, MODEL-19–21 | 12 |
| MODEL-07–12, MODEL-16–18 | 13 |
| MODEL-13–15 | 14 |
| EVAL-01–10 | 15 |
| EVAL-11–12 | 16 |
| KF-01–04 | 17 |
| KF-05–08 | 18 |
| KF-09–12 | 19 |
| KF-13–15 | 20 |
| DRIFT-01–05 | 21 |
| DRIFT-06–07 | 22 |
| FE-01–06 | 25 |
| FMOD-01–06 | 26 |
| FFOR-01–06 | 27 |
| FDASH-01–08 | 28 |
| FDRFT-01–05 | 29 |
| TEST-01–05 | 30 |
| LIVE-01–05 | 31 |
| LIVE-06–09 | 32 |
| DEPLOY-01–02 | 33 |
| DEPLOY-03–08 | 34 |
| DBHARD-01–03 | 35 |
| DBHARD-06–07 | 36 |
| MON-01–03 | 37 |
| MON-04–08 | 38 |
| MON-09–10 | 39 |
| DBHARD-04–05 | 40 |
| DBHARD-08 | 41 |
| ADVML-01–02 | 42 |
| ADVML-03–06 | 43 |
| ADVML-07–08 | 44 |
| FENH-01–03 | 45 |
| FENH-04–05 | 46 |
| PROD-01–03 | 47 |
| PROD-04–05 | 48 |
| PROD-06–08 | 49 |
| FENH-06–07 | 50 |
| OBJST-01–04 | 51 |
| OBJST-05–08 | 52 |
| OBJST-09–12 | 53 |
| KSERV-01–04 | 54 |
| KSERV-05–08 | 55 |
| KSERV-09–12 | 56 |
| KSERV-13–15 | 57 |
phase 
