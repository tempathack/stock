# Roadmap — Stock Prediction Platform

**Granularity:** Fine | **Mode:** YOLO | **Parallelization:** Enabled
**Milestone v1.0:** Phases 1–30 (Complete) | **Milestone v1.1:** Phases 31–50 (Production-Ready) | **Milestone v2.0:** Phases 51–63 (MinIO + KServe + E2E Tests) | **Milestone v3.0:** Phases 64–68 (Real-Time Analytics & GitOps)

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
| 8 | 1/1 | Complete   | 2026-03-25 | 1 |
| 9 | Kafka Consumers — Batch Writer | Consume topics, upsert to PostgreSQL | CONS-01–07 | 2 |
| 10 | Technical Indicators | All momentum/trend/volatility/volume indicators | FEAT-01–14 | 4 |
| 11 | Lag Features & Transformers | Lag features, rolling stats, scaler pipelines | FEAT-15–21 | 2 |
| 12 | Linear & Regularized Models | Train linear family, TimeSeriesSplit CV | MODEL-01–06, MODEL-19–21 | 3 |
| 13 | Tree-Based Models | Train tree/ensemble family | MODEL-07–12, MODEL-16–18 | 2 |
| 14 | Distance & Neural Models | Train KNN, SVR, MLP | MODEL-13–15 | 2 |
| 15 | Evaluation Framework | All metrics, model ranking, winner selection | EVAL-01–10 | 3 |
| 16 | SHAP Explainability | SHAP values for top 5 models, store summary | EVAL-11–12 | 1 |
| 17 | 2/2 | Complete   | 2026-03-25 | 2 |
| 18 | 2/2 | Complete   | 2026-03-25 | 2 |
| 19 | 2/2 | Complete   | 2026-03-25 | 2 |
| 20 | 2/2 | Complete   | 2026-03-25 | 2 |
| 21 | 2/2 | Complete    | 2026-03-25 | 2 |
| 22 | 1/1 | Complete   | 2026-03-25 | 1 |
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
| 37 | 2/2 | Complete   | 2026-03-25 | 2 |
| 38 | 3/3 | Complete   | 2026-03-25 | 3 |
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
| 58 | Docker-Compose Runtime Fixes | Kafka broker default + ML pipeline entrypoint fix | FIX-KAFKA, FIX-ML | 1 | ✅ |
| 59 | Minikube E2E Validation | Full stack deploy + ingest-train-KServe serve flow | KSERV-15 | 4 | ✅ |
| 60 | Fix model_name in predict response | Fetch serving metadata from MinIO on API startup | PRED-MNAME-01–05 | 2 | ✅ |
| 61 | Playwright E2E — Frontend Coverage | All 5 pages: Dashboard, Forecasts, Models, Drift, Backtest | TEST-PW-01–05 | 5 | ✅ |
| 62 | Playwright E2E — Infra Coverage | Grafana, Prometheus, MinIO, Kubeflow, K8s Dashboard | TEST-INFRA-01–05 | 5 | ✅ |
| 63 | Fix E2E Test Assertions | Real API data guards in all spec beforeAll blocks | TEST-E2E-01 | 1 | ✅ |
| 64 | 2/2 | Complete    | 2026-03-29 | 2 |
| 65 | 2/2 | Complete    | 2026-03-29 | 2 |
| 66 | 3/3 | Complete    | 2026-03-30 | 3 |
| 67 | 3/3 | Complete   | 2026-03-30 | 3 |
| 68 | 2/2 | Complete    | 2026-03-30 | 2 |
| 69 | 2/2 | Complete    | 2026-03-30 | 2 |
| 70 | 2/2 | Complete    | 2026-03-31 | 2 |
| 71 | 4/4 | Complete    | 2026-03-31 | 4 |
| 72 | 2/2 | Complete    | 2026-03-31 | 2 |
| 73 | 7/7 | Complete    | 2026-03-31 | 7 |
| 74–81 | Various hotfixes & Grafana fixes | Complete | 2026-04-02 | — |
| 82 | 2/2 | Complete    | 2026-04-02 |
| 83 | 1/1 | Complete    | 2026-04-02 | 1 plan |
| 84–87 | Various ML/infra phases | Complete | 2026-04-03 | — |
| 88 | 3/3 | Complete   | 2026-04-03 | 3 plans |
| 89 | 2/2 | Complete   | 2026-04-03 | 2 plans |
| 90 | 4/5 | Complete    | 2026-04-03 | 5 plans |

Plans:
- [ ] 70-01-PLAN.md — FastAPI streaming-features endpoint + feast_online_service + tests
- [ ] 70-02-PLAN.md — StreamingFeaturesPanel React component + Dashboard.tsx Drawer wiring
- [ ] 72-01-PLAN.md — Prometheus flink-jobs scrape job + Grafana datasource UID pin
- [ ] 72-02-PLAN.md — Flink dashboard 10-panel expansion + human verification
- [ ] 82-01-PLAN.md — Grafana ML perf panel 2 threshold line + HighPredictionLatencyP95 alert rule
- [ ] 82-02-PLAN.md — test_dashboard_json.py: 5 tests verifying threshold line + histogram sources
- [ ] 83-01-PLAN.md — Fix INTRADAY_TOPIC, prometheus.yml port 8001→9090, create kafka-consumer Service
- [ ] 90-01-PLAN.md — Elasticsearch 8 + Kibana K8s manifests + PostgreSQL WAL config
- [ ] 90-02-PLAN.md — Debezium KafkaConnect image Dockerfile + CR + KafkaConnector CRs + CDC topics
- [ ] 90-03-PLAN.md — FastAPI elasticsearch_service + /search router + config + schemas
- [ ] 90-04-PLAN.md — React /search page + API hooks + App.tsx route + Sidebar nav
- [ ] 90-05-PLAN.md — Playwright browser verification checkpoint

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

**Plans:** 1/1 plans complete

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

**Plans:** 2/2 plans complete

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

**Plans:** 2/2 plans complete

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

**Plans:** 2/2 plans complete

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

**Plans:** 2/2 plans complete

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

**Plans:** 1/1 plans complete

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

**Plans:** 2/2 plans complete

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

**Plans:** 3/3 plans complete

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
**Plans:** 2/2 plans complete

Plans:
- [ ] 60-01-PLAN.md — model_metadata_cache.py (MinIO+DB startup load), boto3 dep, lifespan wire, inference functions updated
- [ ] 60-02-PLAN.md — K8s ConfigMap MINIO vars + minio-secrets secretRef + human E2E verify

### Phase 61: Playwright E2E tests — full frontend feature coverage

**Goal:** Install Playwright in the frontend, write real E2E tests for all 5 pages (Dashboard, Forecasts, Models, Drift, Backtest) using `page.route()` API interceptors with fixture data matching exact API response schemas — zero tolerance for frontend mock-fallback paths passing tests.
**Requirements**: TEST-PW-01, TEST-PW-02, TEST-PW-03, TEST-PW-04, TEST-PW-05
**Depends on:** Phase 60
**Plans:** 5/5 plans complete

Plans:
- [ ] 61-01-PLAN.md — Playwright install, playwright.config.ts, package.json scripts, shared API fixture factories (types match types.ts schemas exactly)
- [ ] 61-02-PLAN.md — Navigation + Dashboard page tests (sidebar links, treemap click→select, metric cards, TA panel toggle, close detail)
- [ ] 61-03-PLAN.md — Forecasts page tests (horizon toggle, filter controls, table rows, search, comparison panel, detail section open/close, export buttons)
- [ ] 61-04-PLAN.md — Models page tests (winner card, table click→detail panel, SHAP bar + beeswarm charts, fold performance chart, export buttons) + Drift page tests (ActiveModelCard, RetrainStatusPanel, RollingPerformanceChart, DriftTimeline, FeatureDistributionChart)
- [ ] 61-05-PLAN.md — Backtest page tests (ticker select, date inputs, horizon select, Run Backtest → chart + metrics summary, export buttons) + CI npm script wiring

### Phase 62: Playwright E2E tests — infra UI coverage (Grafana, Prometheus, MinIO, Kubeflow, K8s Dashboard)

**Goal:** Write Playwright E2E tests for every non-React UI exposed by deploy-all.sh: Grafana login + 3 dashboards + 2 datasources, Prometheus query execution + targets + alerts, MinIO Console login + bucket existence + object navigation, Kubeflow Pipelines UI navigation, and Kubernetes Dashboard cluster overview. Tests hit the live deployed stack — no route interceptors, no mocks.
**Requirements**: TEST-INFRA-01, TEST-INFRA-02, TEST-INFRA-03, TEST-INFRA-04, TEST-INFRA-05
**Depends on:** Phase 61
**Plans:** 5/5 plans complete

Plans:
- [ ] 62-01-PLAN.md — Infra Playwright config (playwright.infra.config.ts, multi-project setup for ports 3000/9090/9001/8888/8001, env var credentials, shared auth helpers)
- [ ] 62-02-PLAN.md — Grafana tests: login, datasource health (Prometheus + Loki), all 3 dashboards load with panels rendered (HTTP Overview, Prediction Volume, Consumer Metrics)
- [ ] 62-03-PLAN.md — Prometheus tests: homepage, query editor executes `up` and returns results, Targets page shows expected job labels, Alerts page accessible
- [ ] 62-04-PLAN.md — MinIO Console tests: login, model-artifacts bucket exists, drift-logs bucket exists, bucket navigation, object upload/list assertions
- [ ] 62-05-PLAN.md — Kubeflow Pipelines tests (homepage + pipelines/experiments list) + Kubernetes Dashboard tests (cluster overview, namespace list, pod list) + npm script wiring

### Phase 63: Fix E2E test assertions — require real API data, not mock/empty fallbacks

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 62
**Plans:** 1/1 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 63 to break down) (completed 2026-03-25)

---

## v3.0 Phases — Real-Time Analytics & GitOps

> **Milestone:** v3.0 — Phases 64–69
> **Strategy:** 3 waves — Analytics Foundation (64), GitOps (65), Data Platform (66–67), Integration + UI (68–69)
> **New Technologies:** TimescaleDB OLAP, Argo CD, Feast, Apache Flink
> **Dependencies:** Wave 1 (64–65) parallel; Wave 2 (66–67) parallel, depends on 64; Wave 3 (68–69) depends on 66+67

---

### Phase 64: TimescaleDB OLAP — Continuous Aggregates & Compression

**Goal:** Unlock TimescaleDB's full analytical power — continuous aggregates materialize hourly and daily OHLCV rollups automatically, compression policies shrink cold data storage by 90%+, and retention policies enforce data lifecycle, enabling sub-second OLAP queries that today take seconds on raw hypertables.

**Requirements:** TSDB-01, TSDB-02, TSDB-03, TSDB-04, TSDB-05, TSDB-06

**Success Criteria:**
1. `ohlcv_daily_1h_agg` continuous aggregate materializes 1-hour OHLCV rollups from `ohlcv_intraday` (OHLCV time_bucket, auto-refresh every 30 min)
2. `ohlcv_daily_agg` continuous aggregate materializes daily summaries from `ohlcv_daily` (auto-refresh every 1 hour)
3. Compression policy on `ohlcv_daily`: chunks older than 7 days compressed (segmentby ticker, orderby date)
4. Compression policy on `ohlcv_intraday`: chunks older than 3 days compressed
5. Retention policy: `ohlcv_intraday` drops data older than 90 days; `ohlcv_daily` keeps 5 years
6. New API endpoint `GET /market/candles?ticker=AAPL&interval=1h` queries continuous aggregate and returns ≤50ms p99

**Plans:**
2/2 plans complete
- [ ] 64-02-PLAN.md — API: `GET /market/candles` endpoint querying continuous aggregates + Grafana OLAP datasource query update

---

### Phase 65: Argo CD — GitOps Deployment Pipeline

**Goal:** Replace the manual `deploy-all.sh` kubectl apply workflow with Argo CD GitOps so the K8s cluster continuously reconciles to the git state — every `git push` automatically syncs to the cluster with health checking and rollback.

**Requirements:** GITOPS-01, GITOPS-02, GITOPS-03, GITOPS-04, GITOPS-05

**Success Criteria:**
1. Argo CD installed in `argocd` namespace; `argocd` CLI accessible via port-forward at localhost:8080
2. Root `Application` (app-of-apps) in `argocd` namespace pointing to `k8s/` directory in git repo
3. Child `Application` CRs exist for: ingestion, processing, storage, ml, frontend, monitoring, argocd namespaces
4. Sync policy: automated with `prune: true` and `selfHeal: true` on all apps
5. Custom health checks for Strimzi `Kafka` CR and KServe `InferenceService` CR (Healthy when READY=True)
6. `deploy-all.sh` updated: initial bootstrap via `kubectl apply -n argocd` then `argocd app sync --all` for subsequent deploys

**Plans:**
2/2 plans complete
- [ ] 65-02-PLAN.md — Sync policies, custom health checks for Strimzi/KServe CRDs, deploy-all.sh integration, smoke validation

---

### Phase 66: Feast — Production Feature Store

**Goal:** Replace the ad-hoc `ml/features/store.py` precomputed cache with Feast — a production-grade feature store providing point-in-time correct historical feature retrieval for training (offline store → PostgreSQL) and sub-millisecond online feature serving for inference (online store → Redis).

**Requirements:** FEAST-01, FEAST-02, FEAST-03, FEAST-04, FEAST-05, FEAST-06, FEAST-07, FEAST-08

**Success Criteria:**
1. `ml/feature_store/feature_store.yaml` configures Feast with PostgreSQL offline store and Redis online store
2. Three `FeatureView`s registered: `ohlcv_stats_fv` (OHLCV + returns), `technical_indicators_fv` (RSI/MACD/BBands/ATR etc.), `lag_features_fv` (t-1 to t-21 lags + rolling stats)
3. `feast apply` materializes feature definitions without error
4. `store.get_historical_features(entity_df)` returns point-in-time correct training data (no future leakage)
5. `store.get_online_features({"ticker": ["AAPL"]})` returns current features from Redis in <5ms
6. ML training pipeline uses `feast.get_historical_features()` instead of raw DB queries + `ml/features/` compute
7. Prediction API uses `feast.get_online_features()` for real-time feature retrieval
8. K8s `CronJob` materializes features daily at 18:30 ET; Feast feature server Deployment in `ml` namespace

**Plans:**
3/3 plans complete
- [ ] 66-02-PLAN.md — Update ML training pipeline to use `get_historical_features()`; replace store.py compute with Feast retrieval
- [ ] 66-03-PLAN.md — Feast feature server K8s Deployment + materialization CronJob; update prediction API to use `get_online_features()`

---

### Phase 67: Apache Flink — Real-Time Stream Processing

**Goal:** Deploy Apache Flink via the Flink Kubernetes Operator to replace the batch Kafka consumer with stateful stream processing — real-time OHLCV normalization and upsert to TimescaleDB, windowed technical indicator computation (rolling RSI/MACD/EMA), and live feature push to Feast's Redis online store.

**Requirements:** FLINK-01, FLINK-02, FLINK-03, FLINK-04, FLINK-05, FLINK-06, FLINK-07, FLINK-08

**Success Criteria:**
1. Flink Kubernetes Operator installed in `flink` namespace; `FlinkDeployment` CRD available
2. **Job 1 — OHLCV Normalizer** (`ohlcv_normalizer`): reads `intraday-data` Kafka topic → validates/normalizes → upserts to `ohlcv_intraday` TimescaleDB hypertable (replaces kafka-consumer batch writer for intraday)
3. **Job 2 — Indicator Stream** (`indicator_stream`): reads `intraday-data` → computes 5-min windowed RSI, MACD signal line, EMA-20 via Flink sliding windows → publishes to `processed-features` Kafka topic
4. **Job 3 — Feast Online Writer** (`feast_writer`): consumes `processed-features` → pushes to Feast Redis online store via `feast.write_to_online_store()`
5. New Kafka topic `processed-features` (3 partitions, 24h retention) provisioned via Strimzi KafkaTopic CR
6. Flink jobs packaged as Docker images, deployed as `FlinkDeployment` CRs in `flink` namespace
7. Flink metrics exported to Prometheus via Flink's PrometheusReporter; Grafana panel shows job uptime + record throughput
8. All 3 jobs survive a simulated Kafka broker restart (checkpointing enabled, RocksDB state backend)

**Plans:**
3/3 plans complete
- [ ] 67-02-PLAN.md — Job 2 Indicator Stream (sliding window RSI/MACD/EMA) + Job 3 Feast Online Writer + FlinkDeployment CRs + Prometheus metrics + Grafana panel
- [ ] 67-03-PLAN.md — Checkpoint config (RocksDB, S3 backend → MinIO), restart strategy, deploy-all.sh integration, smoke validation

---

### Phase 68: E2E Integration — v3.0 Stack Validation

**Goal:** End-to-end validation of the complete v3.0 data platform: TimescaleDB continuous aggregates serving API candle queries, Argo CD auto-syncing after a manifest change, Feast point-in-time correct training and online inference, Flink processing a live Kafka stream from ingest to prediction.

**Requirements:** V3INT-01, V3INT-02, V3INT-03, V3INT-04, V3INT-05

**Success Criteria:**
1. **OLAP benchmark:** `GET /market/candles?ticker=AAPL&interval=1h&days=30` returns in <200ms vs >2s on raw hypertable (≥10x improvement documented)
2. **Argo CD sync test:** Update a ConfigMap value in git, push — Argo CD detects diff and syncs within 3 minutes without manual kubectl apply
3. **Feast offline:** ML training pipeline completes using `get_historical_features()` — no raw DB queries in training path; point-in-time correctness validated via future-leakage assertion test
4. **Feast online:** POST to `/predict/AAPL` triggers `get_online_features()` from Redis; feature freshness timestamp <2 min old
5. **Full Flink pipeline:** Trigger `/ingest/intraday` → Flink Job 1 upserts to TimescaleDB within 10s → Flink Job 2 publishes to `processed-features` → Flink Job 3 updates Feast online store → `/predict/AAPL` returns prediction using fresh features

**Plans:**
2/2 plans complete
- [ ] 68-02-PLAN.md — Feast offline/online integration tests, full Flink pipeline E2E smoke test, Playwright infra spec additions (Argo CD UI + Flink Web UI)

---

### Phase 69: Frontend — /analytics Page

**Goal:** Add a new `/analytics` page to the React dashboard exposing the real-time analytics stack — live Flink job health, Feast feature freshness panel, OLAP-powered multi-interval candle chart, and a stream lag monitor — giving operators full visibility into the v3.0 data platform in the existing Bloomberg Terminal UI.

**Requirements:** UI-RT-01, UI-RT-02, UI-RT-03, UI-RT-04, UI-RT-05, UI-RT-06, UI-RT-07

**Success Criteria:**
1. `/analytics` route added to React Router; nav sidebar shows "Analytics" link below "Drift"
2. **StreamHealthPanel**: shows each Flink job (OHLCV Normalizer, Indicator Stream, Feast Writer) with status badge (RUNNING/FAILED/RESTARTING) and records-per-second throughput — polls `GET /analytics/flink/jobs` every 10s
3. **FeatureFreshnessPanel**: shows last materialization timestamp per FeatureView (ohlcv_stats, technical_indicators, lag_features) with staleness indicator (green <15min, amber <1h, red >1h) — polls `GET /analytics/feast/freshness` every 30s
4. **OLAPCandleChart**: multi-interval candlestick chart (5m, 1h, 4h, 1d) using TimescaleDB continuous aggregates via `GET /market/candles`; interval toggle buttons; renders with Lightweight Charts
5. **StreamLagMonitor**: Kafka consumer group lag for `processed-features` topic per partition, line chart over last 30 min — polls `GET /analytics/kafka/lag` every 15s
6. **SystemHealthSummary**: top-of-page card row showing Argo CD sync status (Synced/OutOfSync), Flink cluster health, Feast online store latency p99, continuous aggregate last-refresh time
7. All panels have graceful empty states and error boundaries; page fully responsive at 375px

**Plans:** 2/2 plans complete

Plans:
- [ ] 69-01-PLAN.md — FastAPI analytics router: 4 endpoints (/flink/jobs, /feast/freshness, /kafka/lag, /summary), Flink/Feast/Kafka service modules, Pydantic schemas, Redis cache, unit + integration tests
- [ ] 69-02-PLAN.md — React /analytics page: TypeScript interfaces, React Query hooks, 5 panel components (SystemHealthSummary, StreamHealthPanel, FeatureFreshnessPanel, OLAPCandleChart, StreamLagMonitor), route + sidebar nav wiring

### Phase 70: Display Flink-computed streaming features in the dashboard

**Goal:** Surface the real-time features computed by the Apache Flink streaming pipeline (RSI, MACD, Bollinger Bands, EMA, volatility, momentum indicators) directly in the frontend dashboard — giving traders and operators live visibility into computed signal values per symbol alongside existing price data.

**Requirements:** TBD

**Depends on:** Phase 69

**Plans:** 2/2 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 70 to break down) (completed 2026-03-31)

### Phase 71: High-Frequency Alternative Data Pipeline — Reddit Sentiment

**Goal:** Build end-to-end Reddit sentiment pipeline: PRAW producer polls r/wallstreetbets/stocks/investing, Flink VADER job scores posts with HOP windows, Feast Redis persists aggregates, FastAPI WebSocket serves live sentiment, SentimentPanel shows live gauge in Dashboard Drawer.
**Requirements**: ALT-01, ALT-02, ALT-03, ALT-04, ALT-05, ALT-06, ALT-07, ALT-08, ALT-09, ALT-10
**Depends on:** Phase 70
**Plans:** 4/4 plans complete

Plans:
- [ ] 71-01-PLAN.md — Strimzi KafkaTopic CRs (reddit-raw + sentiment-aggregated) + Reddit PRAW producer service + K8s Deployment
- [ ] 71-02-PLAN.md — sentiment_stream Flink job (VADER HOP window) + sentiment_writer Flink job + Feast reddit_sentiment_fv + FlinkDeployment CRs
- [ ] 71-03-PLAN.md — FastAPI /ws/sentiment/{ticker} WebSocket endpoint + feast_online_service extension + unit tests
- [ ] 71-04-PLAN.md — useSentimentSocket hook + SentimentPanel component + Dashboard.tsx Drawer wiring

### Phase 72: Grafana debug dashboards with Flink metrics integration

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 71
**Plans:** 2/2 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 72 to break down) (completed 2026-03-31)

### Phase 73: Full system scope verification and functional audit using parallel subagents

**Goal:** Verify every requirement across all milestones (v1.0–v3.0) is satisfied by auditing actual code files using parallel domain subagents, producing a master AUDIT.md with requirements traceability, gap classification, and cross-phase wiring verification.
**Requirements**: AUDIT-01–04
**Depends on:** Phase 72
**Plans:** 7/7 plans complete

Plans:
- [ ] 73-01-PLAN.md — Coordinator: AUDIT.md skeleton, requirements traceability, phase summary, tech debt, E2E chains
- [ ] 73-02-PLAN.md — Domain 1 audit: FastAPI routers, services, tests (API-01–12, LIVE, FENH, PROD)
- [ ] 73-03-PLAN.md — Domain 2 audit: ML features, models, eval, drift, pipeline, Feast (FEAT, MODEL, EVAL, KF, DRIFT, ADVML)
- [ ] 73-04-PLAN.md — Domain 3 audit: Kafka topics, Flink jobs, reddit producer, sentiment pipeline (KAFKA, CONS, Phase 67, 71)
- [ ] 73-05-PLAN.md — Domain 4 audit: Frontend pages, components, hooks, Playwright E2E (FE, FMOD, FFOR, FDASH, FDRFT, FENH)
- [ ] 73-06-PLAN.md — Domain 5 audit: Prometheus, Grafana dashboards, Loki, alerting (MON-01–10)
- [ ] 73-07-PLAN.md — Domain 6 audit: K8s infra, MinIO, KServe, Argo CD, Feast + gap consolidation (OBJST, KSERV, DEPLOY, DBHARD)

### Phase 74: Frontend rendering bug fixes — models duplicate rows React key collision, treemap AAPL contrast, stock drawer wrong selection

**Goal:** Fix all frontend rendering bugs identified in dashboard audit: duplicate model rows caused by React key collision, AAPL treemap cell text invisible due to contrast issue, and stock drawer opening for wrong stock. (Below-fold dashboard content deferred to Phase 76.)
**Requirements**: FDASH-01, FDASH-02, FMOD-01
**Depends on:** Phase 73
**Plans:** 2/2 plans complete

Plans:
- [ ] 74-01-PLAN.md — Fix models duplicate rows (getRowId key collision) and wrong-stock drawer (stale handleSelect closure)
- [ ] 74-02-PLAN.md — Fix treemap AAPL text invisible (pct text contrast — white + drop-shadow)

### Phase 75: Data quality fixes — OOS model metrics missing, forecast constant bias, drift RMSE null as zero, analytics integrations

**Goal:** Fix data quality issues across the platform: populate missing OOS metrics (RMSE, MAE, R², MAPE, Dir Accuracy) in the models page, investigate and fix forecast constant bias where every stock shows identical 0.93 confidence and ~-6.8% return, fix drift page Previous Model RMSE rendering null as 0.0000, and connect Analytics page integrations (ArgoCD sync, Feast Latency p99, CA Last Refresh).
**Requirements**: TBD
**Depends on:** Phase 73
**Plans:** 4/4 plans complete

Plans:
- [x] 75-01-PLAN.md — Wave 0: Test scaffolding (kubernetes pkg, K8s CRD ArgoCD tests, Feast latency tests)
- [x] 75-02-PLAN.md — Drift RMSE null fix (frontend ?? null + API schema previous_oos_metrics)
- [x] 75-03-PLAN.md — Analytics integrations (ArgoCD K8s CRD, Feast latency cached, CA last refresh)
- [x] 75-04-PLAN.md — OOS metrics diagnostic + fix, forecast constant bias diagnostic + fix

### Phase 76: UX polish — empty states, loading feedback, tooltips, missing data fields, analytics charts

**Goal:** Polish UX across all pages: add proper empty state and loading feedback to Backtest page, add tooltips to icon-only buttons, populate Sector and Company name fields in Forecasts table, add multi-horizon selector (1D/3D/7D/14D), add content below dashboard treemap fold, add ticker selector to Analytics OLAP candle chart, fix feature freshness unknown state.
**Requirements**: TBD
**Depends on:** Phase 73
**Plans:** 4/4 plans complete

Plans:
- [ ] 76-01-PLAN.md — Backtest idle state + icon tooltip audit
- [ ] 76-02-PLAN.md — Feature Freshness null fix + OLAP ticker selector
- [ ] 76-03-PLAN.md — Sector/company_name DB fix + 14D horizon config + horizons.json seed
- [ ] 76-04-PLAN.md — Dashboard below-fold content: TopMoversPanel (top gainers/losers)

### Phase 77: Fix Flink pipeline health and Forecasts blank screen

**Goal:** Forecasts page shows skeleton loading (not blank screen); ohlcv-normalizer FlinkDeployment reaches READY with completed MinIO checkpoints
**Requirements**: TBD
**Depends on:** Phase 76
**Plans:** 2/2 plans complete

Plans:
- [ ] 77-01-PLAN.md — Forecasts blank screen: skeleton loading state + partial-failure error logic
- [ ] 77-02-PLAN.md — Flink ohlcv-normalizer: diagnose crash-loop, fix secrets + bucket + topic

### Phase 78: Fix frontend broken-page error states — Dashboard, Models, Drift show tiny error box in a black void with no empty-state design

**Goal:** Fix Models, Dashboard, and Drift pages so API failures and loading states never produce a black void — every page renders PageHeader first, then structured skeleton/error content below.
**Requirements**: ERR-FALLBACK-ICON, MODELS-LOADING-SKELETON, MODELS-ERROR-STATE, DASHBOARD-ERROR-STATE, DASHBOARD-MOCK-REMOVAL, DASHBOARD-INTRADAY-PLACEHOLDER, DRIFT-ERROR-STATE, DRIFT-LOADING-SKELETON, DRIFT-MOCK-REMOVAL, DRIFT-PANEL-ERRORS
**Depends on:** Phase 77
**Plans:** 4/4 plans complete

Plans:
- [ ] 78-01-PLAN.md — Enhance ErrorFallback component: add ErrorOutline icon above message text
- [ ] 78-02-PLAN.md — Fix Models page: skeleton loading state + structured error with PageHeader
- [ ] 78-03-PLAN.md — Fix Dashboard page: remove mock fallbacks, structured error, per-panel indicator error, intraday empty state
- [ ] 78-04-PLAN.md — Fix Drift page: remove mock fallbacks, skeleton loading, structured error, per-panel errors for secondary queries

### Phase 79: Grafana security hardening — change default admin password from admin/admin

**Goal:** Remove hardcoded admin/admin credentials from Grafana — use K8s Secret in K8s and env var substitution in docker-compose.
**Requirements**: INFRA-08
**Depends on:** Phase 78
**Plans:** 1/1 plans complete

Plans:
- [ ] 79-01-PLAN.md — Create grafana-secret K8s Secret, update Deployment to secretKeyRef, update docker-compose to env var, update deploy-all.sh

### Phase 80: Analytics page cleanup — remove Coming in Phase 69 placeholder badges and fix N/A values showing green checkmarks

**Goal:** Remove stale "Coming in Phase 69" Chip badges from Analytics page empty states and fix N/A metric cards that incorrectly display green CheckCircle icons
**Requirements**: UI-CLEANUP-80
**Depends on:** Phase 79
**Plans:** 1/1 plans complete

Plans:
- [ ] 80-01-PLAN.md — Remove phase badge from PlaceholderCard; fix neutral icon for N/A metric cards in SystemHealthSummary

### Phase 81: Fix Grafana No-data-on-green panels — API Health Error Rate and Inference Errors show No data on green background appearing healthy

**Goal:** Add null+nan value mappings to four green-base stat panels in the API Health dashboard so no-data states render as blue/neutral instead of falsely green
**Requirements**: GRAFANA-81-01, GRAFANA-81-02, GRAFANA-81-03, GRAFANA-81-04
**Depends on:** Phase 80
**Plans:** 1/1 plans complete

Plans:
- [ ] 81-01-PLAN.md — Add null+nan mappings to Error Rate % and latency stat panels; apply ConfigMap; visual verify

### Phase 82: Fix ML prediction latency alerting — add threshold line for 8-10s p95, verify p50/p95/p99 are real histogram metrics not synthetic

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 81
**Plans:** 2/2 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 82 to break down) (completed 2026-04-02)

### Phase 83: Fix Kafka consumer metrics scraping — all consumer and writer panels show No data, fix exporter gap

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 82
**Plans:** 1/1 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 83 to break down) (completed 2026-04-02)

### Phase 84: Fix Loki alerting datasource misconfiguration — alert rules fail to load from Loki

**Goal:** Pin Loki datasource UID, provision Grafana unified alert rules via ConfigMap, and fix Promtail path glob so logs flow to Loki — enabling end-to-end Loki-backed alerting
**Requirements**: LOKI-ALERT-01, LOKI-ALERT-02, LOKI-ALERT-03, LOKI-ALERT-04, LOKI-ALERT-05
**Depends on:** Phase 83
**Plans:** 2/2 plans complete

Plans:
- [ ] 84-01-PLAN.md — TDD test scaffold (5 tests for all LOKI-ALERT requirements)
- [ ] 84-02-PLAN.md — Apply datasource UID pin, alerting ConfigMap, Promtail path fix, deployment mount

### Phase 85: Backtest UX polish — change red empty-state message to neutral, label orphaned download and table-view icon buttons

**Goal:** Fix two UX issues on the Backtest page: replace the alarming red error/no-data empty state with a neutral grey presentation, and replace icon-only export controls with labelled CSV/PDF buttons consistent with Models and Forecasts pages.
**Requirements**: TBD
**Depends on:** Phase 84
**Plans:** 1/1 plans complete

Plans:
- [ ] 85-01-PLAN.md — Replace red ErrorFallback + icon-only export buttons with neutral empty state + ExportButtons component

### Phase 86: Frontend sidebar icon differentiation — make nav icons visually distinct per section

**Goal:** Replace four visually similar chart-style nav icons with icons that have distinct silhouettes, so each of the six nav sections is identifiable by icon shape alone.
**Requirements**: NAV-ICON-01
**Depends on:** Phase 85
**Plans:** 1/1 plans complete

Plans:
- [ ] 86-01-PLAN.md — Swap four nav icons in Sidebar.tsx (PsychologyIcon, WaterDropIcon, HistoryIcon, InsightsIcon) + Playwright visual verification

### Phase 87: Point-in-time correct feature serving via Feast and KServe Transformer — eliminate lookahead leakage in backtest

**Goal:** Replace ad-hoc on-the-fly feature computation with a Feast-backed pipeline: Flink/batch computes features → Feast online store → KServe Transformer fetches at inference. Ensures backtest uses only features available at prediction time — no lookahead leakage. Covers KServe Transformer sidecar wired to Feast, point-in-time feature retrieval in backtest service, feast materialize cronjob producing versioned snapshots, and validation that historical backtests cannot access future OHLCV rows.
**Requirements**: TBD
**Depends on:** Phase 86
**Plans:** 3/3 plans complete

Plans:
- [ ] 87-01-PLAN.md — FeastTransformer service (kserve.Model subclass) + Dockerfile + unit tests for preprocess() and 503-on-no-features
- [ ] 87-02-PLAN.md — pit_validator.py (assert_no_future_leakage, build_entity_df_for_backtest) + test_pit_correctness.py
- [ ] 87-03-PLAN.md — Wire Transformer into kserve-inference-service.yaml, add features_pit_correct to BacktestResponse, update materialize CronJob snapshot label

### Phase 88: Add all prediction forecasts to the table in the forecasts dashboard tab

**Goal:** Expose all four prediction horizons (1d, 7d, 14d, 30d) simultaneously as grouped columns in the Forecasts table, fixing the missing horizons.json ConfigMap entry and replacing the single-horizon toggle view.
**Requirements**: FCST-HORIZONS-01, FCST-HOOK-01, FCST-MERGE-01, FCST-TEST-01, FCST-TABLE-01, FCST-EXPORT-01, FCST-UI-01
**Depends on:** Phase 87
**Plans:** 3/3 plans complete

Plans:
- [ ] 88-01-PLAN.md — Fix model-features-config ConfigMap (add horizons.json), add MultiHorizonForecastRow type and useAllHorizonsPredictions hook
- [ ] 88-02-PLAN.md — Add joinMultiHorizonForecastData util + vitest unit tests (6 cases)
- [ ] 88-03-PLAN.md — Rewrite ForecastTable multi-horizon column groups + rewire Forecasts.tsx + Playwright verification

### Phase 89: Live sentiment timeseries chart in Dashboard tab + fix Promtail Kubernetes SD — Flink-streamed Reddit/news sentiment per stock, 2-min intervals, 10-hour rolling window, replaces static unavailable placeholder; fix Promtail 2.9.6 kubernetes_sd_configs role: pod discovering zero targets so logs reach Loki

**Goal:** Deliver live sentiment timeseries LineChart in Dashboard stock-detail drawer (10h rolling window, 2-min Flink TUMBLE intervals via TimescaleDB hypertable); fix Promtail kubernetes_sd_configs path separator so logs reach Loki.
**Requirements**: TBD
**Depends on:** Phase 88
**Plans:** 2/2 plans complete

Plans:
- [x] 89-01-PLAN.md — Promtail fix + sentiment_timeseries DB migration + API endpoint + Flink JDBC sink
- [x] 89-02-PLAN.md — SentimentTimeseriesChart React component + SentimentPanel wiring + Playwright verify

### Phase 90: Debezium CDC and Elasticsearch integration

**Goal:** Deploy Debezium Connect as a K8s workload capturing PostgreSQL WAL changes for predictions, drift_logs, and model_registry tables into Kafka CDC topics; route CDC events to Elasticsearch via Kafka Connect ES Sink Connector; expose FastAPI /search/* endpoints; update React analytics and model-comparison pages to query Elasticsearch. All components run as Kubernetes resources in Minikube.
**Requirements**: TBD
**Depends on:** Phase 89
**Plans:** 5/5 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 90 to break down) (completed 2026-04-03)

### Phase 92: Feast-powered prediction pipeline — retrain ML model on Feast features (OHLCV indicators + Reddit sentiment + Flink real-time indicators) and wire Feast online store into the API inference path, replacing the current ad-hoc Postgres+local-compute approach

**Goal:** Retrain the ML model on Feast-materialized features (OHLCV technical indicators + Flink real-time indicators + Reddit sentiment) and replace the current ad-hoc Postgres+local-compute inference path with Feast online store feature retrieval, making sentiment and streaming features available at prediction time.
**Requirements**: TBD
**Depends on:** Phase 90
**Plans:** 1/4 plans executed

Plans:
- [ ] 92-01-PLAN.md — Wave 0 test scaffolds (TestFeastDataLoader, TestFeastInference, sentiment coverage)
- [ ] 92-02-PLAN.md — Training pipeline Feast integration (extend _TRAINING_FEATURES, add load_feast_data(), wire use_feast_data)
- [ ] 92-03-PLAN.md — Config, metrics, schema additions (FEAST_INFERENCE_ENABLED, feast_stale_features_total, feature_freshness_seconds)
- [ ] 92-04-PLAN.md — Inference path rewrite (get_online_features_for_ticker, _feast_inference, get_live_prediction branch)

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
| TEST-PW-01–05 | 61 |
| TEST-INFRA-01–05 | 62 |
| TEST-E2E-01 | 63 |
| TSDB-01–06 | 64 |
| GITOPS-01–05 | 65 |
| FEAST-01–08 | 66 |
| FLINK-01–08 | 67 |
| V3INT-01–05 | 68 |
| UI-RT-01–07 | 69 |
