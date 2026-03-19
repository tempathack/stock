# Roadmap — Stock Prediction Platform

**Granularity:** Fine | **Mode:** YOLO | **Parallelization:** Enabled

---

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | 3/3 | Complete   | 2026-03-18 | 3 | 1/2 | In Progress|  | Complete   | 2026-03-18 | 3 |
| 3 | FastAPI Base Service | /health endpoint, Dockerfile, K8s deployment | API-01, API-02, API-03, API-04 | 4 | 3/3 | Complete   | 2026-03-19 | DB deployed, schema initialized, indexes | DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, DB-07 | 4 |
| 5 | 2/2 | Complete   | 2026-03-19 | 3 |
| 6 | Yahoo Finance Ingestion Service | Fetch S&P 500 OHLCV, produce to Kafka | INGEST-01, INGEST-02, INGEST-03, INGEST-06 | 4 |
| 7 | FastAPI Ingestion Endpoints | /ingest/intraday and /ingest/historical wired | API-05, API-06 | 3 |
| 8 | K8s CronJobs for Ingestion | Scheduled intraday + historical CronJobs | INGEST-04, INGEST-05 | 3 |
| 9 | Kafka Consumers — Batch Writer | Consume topics, upsert to PostgreSQL | CONS-01, CONS-02, CONS-03, CONS-04, CONS-05, CONS-06, CONS-07 | 4 |
| 10 | Technical Indicators | All momentum/trend/volatility/volume indicators | FEAT-01–FEAT-14 | 4 |
| 11 | Lag Features & Transformers | Lag features, rolling stats, scaler pipelines | FEAT-15–FEAT-21 | 3 |
| 12 | Linear & Regularized Models | Train linear family, TimeSeriesSplit CV | MODEL-01–MODEL-06, MODEL-19, MODEL-20, MODEL-21 | 4 |
| 13 | Tree-Based Models | Train tree/ensemble family | MODEL-07–MODEL-12, MODEL-16, MODEL-17, MODEL-18 | 3 |
| 14 | Distance & Neural Models | Train KNN, SVR, MLP | MODEL-13–MODEL-15 | 3 |
| 15 | Evaluation Framework | All metrics, model ranking, winner selection | EVAL-01–EVAL-10 | 4 |
| 16 | SHAP Explainability | SHAP values for top 5 models, store summary | EVAL-11, EVAL-12 | 3 |
| 17 | Kubeflow Pipeline — Data & Features | KF install, data_loading, feature_engineering, label_generation components | KF-01, KF-02, KF-03, KF-04 | 3 |
| 18 | Kubeflow Pipeline — Training & Eval | train_models, cross_validation, evaluation, model_comparison components | KF-05, KF-06, KF-07, KF-08 | 3 |
| 19 | Kubeflow Pipeline — Selection & Deploy | explainability, winner_selection, model_persistence, deployment components | KF-09, KF-10, KF-11, KF-12 | 4 |
| 20 | Kubeflow Pipeline — Definition & Trigger | Full pipeline definition, versioning, manual + drift triggers | KF-13, KF-14, KF-15 | 3 |
| 21 | Drift Detection System | All 3 drift types, daily check, drift_logs | DRIFT-01–DRIFT-05 | 4 |
| 22 | Drift Auto-Retrain Trigger | Trigger Kubeflow on drift, redeploy, regenerate predictions | DRIFT-06, DRIFT-07 | 3 |
| 23 | FastAPI Prediction & Model Endpoints | /predict/{ticker}, /predict/bulk, /models/comparison, /models/drift | API-07, API-08, API-09, API-10 | 4 |
| 24 | FastAPI Market Endpoints | /market/overview, /market/indicators/{ticker} | API-11, API-12 | 3 |
| 25 | React App Bootstrap & Navigation | App skeleton, dark theme, nav, API client, K8s deployment | FE-01–FE-06 | 4 |
| 26 | Frontend — /models Page | Model comparison table, SHAP charts, fold charts, winner highlight | FMOD-01–FMOD-06 | 5 |
| 27 | Frontend — /forecasts Page | Forecast table, filters, comparison, stock detail, TA overlay, SHAP | FFOR-01–FFOR-06 | 5 |
| 28 | Frontend — /dashboard Page | Treemap, intraday + historical charts, TA panel, metric cards | FDASH-01–FDASH-08 | 5 |
| 29 | Frontend — /drift Page | Active model card, rolling perf chart, drift timeline, retrain panel, feature dists | FDRFT-01–FDRFT-05 | 4 |
| 30 | Integration Testing & Seed Data | End-to-end flow validation, seed script | TEST-01–TEST-05 | 5 |

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


**Plans:** 2 plans

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

---

### Phase 13: Tree-Based & Boosting Models

**Goal:** Train all 8 tree/ensemble regressors plus optional XGBoost/LightGBM/CatBoost boosters.

**Requirements:** MODEL-07–MODEL-12, MODEL-16, MODEL-17, MODEL-18

**Success Criteria:**
1. RF, GBM, HistGBM, ExtraTrees, DT, AdaBoost all trained with TimeSeriesSplit
2. RF and GBM hyperparameter-tuned via RandomizedSearchCV/Optuna
3. Optional boosters (XGBoost, LightGBM, CatBoost) trained if dependencies available
4. All metrics computed per model and stored in consistent format

---

### Phase 14: Distance, SVM & Neural Models

**Goal:** Train KNeighborsRegressor, SVR (RBF), and MLPRegressor with TimeSeriesSplit.

**Requirements:** MODEL-13–MODEL-15

**Success Criteria:**
1. KNN, SVR, MLP trained with TimeSeriesSplit CV
2. SVR and MLP hyperparameter-tuned
3. All metrics computed per model and stored
4. Training completes within reasonable wall time (MLP early stopping configured)

---

### Phase 15: Evaluation Framework & Model Selection

**Goal:** Compute all 6 metrics per model, rank by OOS RMSE, penalize high-variance models, and select one winner.

**Requirements:** EVAL-01–EVAL-10

**Success Criteria:**
1. All 6 metrics (R², MAE, RMSE, MAPE, Directional Accuracy, fold stability) computed in-sample and OOS for every model
2. Models ranked by OOS RMSE primary, directional accuracy secondary, with variance penalty applied
3. ONE winner model identified and written to model_registry with is_active=true
4. Winner's artifact, scaler pipeline, feature list, and full metrics persisted to disk + DB

---

### Phase 16: SHAP Explainability

**Goal:** Compute SHAP values for the top 5 ranked models and store summary data for frontend consumption.

**Requirements:** EVAL-11, EVAL-12

**Success Criteria:**
1. TreeExplainer used for tree-based models; KernelExplainer as fallback for linear/neural
2. Feature importance rankings computed and stored for top 5 models
3. SHAP summary (beeswarm data) stored in structured format (JSON or DB)
4. Explainability output consumable by /models/comparison API endpoint

---

### Phase 17: Kubeflow Pipeline — Data & Feature Components

**Goal:** Install Kubeflow Pipelines in ml namespace and build containerized data_loading, feature_engineering, and label_generation components.

**Requirements:** KF-01, KF-02, KF-03, KF-04

**Success Criteria:**
1. Kubeflow Pipelines UI accessible via port-forward in ml namespace
2. data_loading component container builds and loads data from PostgreSQL
3. feature_engineering component applies all indicators and lag features correctly
4. label_generation component produces t+7 targets with no leakage

---

### Phase 18: Kubeflow Pipeline — Training & Evaluation Components

**Goal:** Build containerized train_models (parallel), cross_validation, evaluation, and model_comparison pipeline components.

**Requirements:** KF-05, KF-06, KF-07, KF-08

**Success Criteria:**
1. train_models component trains all regressors in parallel where supported
2. cross_validation component applies TimeSeriesSplit ≥5 folds
3. evaluation component outputs all 6 metrics per model
4. model_comparison component ranks models and outputs winner candidate

---

### Phase 19: Kubeflow Pipeline — Selection, Persistence & Deployment Components

**Goal:** Build explainability, winner_selection, model_persistence, and deployment Kubeflow components.

**Requirements:** KF-09, KF-10, KF-11, KF-12

**Success Criteria:**
1. explainability component computes SHAP for top 5 models as container step
2. winner_selection component writes final winner to model_registry (is_active=true)
3. model_persistence component saves artifact + scaler + feature list to artifact path
4. deployment component deploys winner model as live serving endpoint in ml namespace

---

### Phase 20: Kubeflow Pipeline — Full Definition & Trigger

**Goal:** Assemble all components into a single versioned, reproducible Kubeflow pipeline; wire manual and drift triggers.

**Requirements:** KF-13, KF-14, KF-15

**Success Criteria:**
1. training_pipeline.py defines the full 11-step pipeline as a Kubeflow DSL
2. Pipeline is versioned (pipeline version recorded in model_registry)
3. Pipeline can be triggered manually via Kubeflow UI or API call
4. drift_pipeline.py trigger invokes the training pipeline programmatically

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

**Goal:** Implement /predict/{ticker}, /predict/bulk, /models/comparison, and /models/drift endpoints backed by live data.

**Requirements:** API-07, API-08, API-09, API-10

**Success Criteria:**
1. GET /predict/{ticker} returns 7-day forecast with confidence metrics from active model
2. GET /predict/bulk returns forecasts for all configured S&P 500 tickers
3. GET /models/comparison returns ranked model table with all 6 metrics
4. GET /models/drift returns current drift status, last check time, and any active alerts

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

---

### Phase 28: Frontend — /dashboard Page

**Goal:** Full market dashboard with interactive treemap, intraday candlestick, historical chart, TA panel, and metric cards.

**Requirements:** FDASH-01–FDASH-08

**Success Criteria:**
1. S&P 500 treemap renders with market cap sizing and daily performance color gradient (green/red)
2. Clicking a treemap cell opens stock detail view
3. Intraday minute-level candlestick chart renders for selected stock
4. Historical OHLCV chart renders with adjustable timeframe selector
5. TA panel (RSI, MACD, Bollinger Bands, MAs, Volume, VWAP) renders correctly with key metric cards

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
