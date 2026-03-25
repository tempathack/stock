# Requirements

## v1 Requirements

### Infrastructure — Kubernetes / Docker

- [x] **INFRA-01**: Minikube cluster initialized with 5 namespaces: ingestion, processing, storage, ml, frontend
- [x] **INFRA-02**: K8s namespace YAML manifests for all 5 namespaces
- [x] **INFRA-03**: Base folder structure created (stock-prediction-platform/ tree)
- [x] **INFRA-04**: setup-minikube.sh shell script with all cluster bootstrap steps
- [x] **INFRA-05**: deploy-all.sh orchestration script
- [x] **INFRA-06**: docker-compose.yml for local dev convenience
- [ ] **INFRA-07**: All services have Dockerfiles with multi-stage builds where applicable
- [ ] **INFRA-08**: All configuration via environment variables — zero hardcoded secrets
- [x] **INFRA-09**: Structured JSON logging configured for all services

### FastAPI Backend — Base

- [x] **API-01**: FastAPI app skeleton with config.py, main.py, router structure
- [x] **API-02**: GET /health endpoint returning service status
- [x] **API-03**: Dockerfile for FastAPI service (multi-stage)
- [x] **API-04**: K8s Deployment + Service YAML for FastAPI in ingestion namespace
- [x] **API-05**: POST /ingest/intraday endpoint (triggers Yahoo Finance intraday fetch)
- [x] **API-06**: POST /ingest/historical endpoint (triggers Yahoo Finance historical fetch)
- [ ] **API-07**: GET /predict/{ticker} endpoint (returns 7-day forecast)
- [ ] **API-08**: GET /predict/bulk endpoint (forecasts for all S&P 500)
- [ ] **API-09**: GET /models/comparison endpoint (model metrics comparison)
- [ ] **API-10**: GET /models/drift endpoint (drift detection status)
- [ ] **API-11**: GET /market/overview endpoint (treemap + sector data)
- [ ] **API-12**: GET /market/indicators/{ticker} endpoint (technical indicators)

### PostgreSQL / Storage

- [x] **DB-01**: PostgreSQL deployed in storage namespace with PVC
- [x] **DB-02**: TimescaleDB extension enabled
- [x] **DB-03**: init.sql with all table schemas: stocks, ohlcv_daily, ohlcv_intraday, predictions, model_registry, drift_logs
- [x] **DB-04**: Composite primary keys on (ticker, date) and (ticker, timestamp)
- [x] **DB-05**: Indexes on (ticker, date) and (ticker, timestamp)
- [x] **DB-06**: Partitioning on date columns for ohlcv_daily and ohlcv_intraday
- [x] **DB-07**: K8s ConfigMap for PostgreSQL credentials

### Kafka / Streaming

- [x] **KAFKA-01**: Strimzi operator deployed in storage namespace
- [x] **KAFKA-02**: Kafka broker with persistent storage
- [x] **KAFKA-03**: intraday-data topic created
- [x] **KAFKA-04**: historical-data topic created
- [x] **KAFKA-05**: K8s manifests for Kafka/Strimzi

### Data Ingestion

- [x] **INGEST-01**: yahoo_finance.py service — fetches OHLCV for S&P 500 tickers via yfinance
- [x] **INGEST-02**: S&P 500 ticker list (dev: 20-stock subset, prod: full universe)
- [x] **INGEST-03**: kafka_producer.py — validates, normalizes, and publishes to Kafka topics
- [x] **INGEST-04**: K8s CronJob for intraday ingestion (daily, market hours)
- [x] **INGEST-05**: K8s CronJob for historical ingestion (weekly)
- [x] **INGEST-06**: Data validation and normalization logic (schema enforcement, nulls, types)

### Kafka Consumers

- [ ] **CONS-01**: Python Kafka consumer service for intraday-data topic
- [ ] **CONS-02**: Python Kafka consumer service for historical-data topic
- [ ] **CONS-03**: Micro-batch processing (configurable batch size and interval)
- [ ] **CONS-04**: Idempotent upsert writes (ON CONFLICT DO UPDATE) for ohlcv tables
- [ ] **CONS-05**: Retry logic with exponential backoff
- [ ] **CONS-06**: Dead-letter queue handling for failed records
- [ ] **CONS-07**: Dockerfile + K8s Deployment for consumer service

### Feature Engineering

- [ ] **FEAT-01**: RSI (14-period) computation
- [ ] **FEAT-02**: MACD (12/26/9) computation
- [ ] **FEAT-03**: Stochastic Oscillator computation
- [ ] **FEAT-04**: SMA (20, 50, 200) computation
- [ ] **FEAT-05**: EMA (12, 26) computation
- [ ] **FEAT-06**: ADX computation
- [ ] **FEAT-07**: Bollinger Bands (20-period, 2σ) computation
- [ ] **FEAT-08**: ATR computation
- [ ] **FEAT-09**: Rolling Volatility (21-day) computation
- [ ] **FEAT-10**: OBV computation
- [ ] **FEAT-11**: VWAP computation
- [ ] **FEAT-12**: Volume SMA computation
- [ ] **FEAT-13**: Accumulation/Distribution computation
- [ ] **FEAT-14**: Returns: 1d, 5d, 21d and log returns
- [ ] **FEAT-15**: Lag features: close price at t-1, t-2, t-3, t-5, t-7, t-14, t-21
- [ ] **FEAT-16**: Rolling window stats (mean, std, min, max) over 5, 10, 21-day windows
- [ ] **FEAT-17**: StandardScaler pipeline variant
- [ ] **FEAT-18**: QuantileTransformer pipeline variant
- [ ] **FEAT-19**: MinMaxScaler pipeline variant
- [ ] **FEAT-20**: t+7 target label generation with strict no-leakage enforcement
- [ ] **FEAT-21**: Drop rows where target is unavailable

### Model Training

- [ ] **MODEL-01**: LinearRegression training
- [ ] **MODEL-02**: Ridge training with hyperparameter tuning
- [ ] **MODEL-03**: Lasso training with hyperparameter tuning
- [ ] **MODEL-04**: ElasticNet training with hyperparameter tuning
- [ ] **MODEL-05**: BayesianRidge training
- [ ] **MODEL-06**: HuberRegressor training
- [ ] **MODEL-07**: RandomForestRegressor training with hyperparameter tuning
- [ ] **MODEL-08**: GradientBoostingRegressor training with hyperparameter tuning
- [ ] **MODEL-09**: HistGradientBoostingRegressor training
- [ ] **MODEL-10**: ExtraTreesRegressor training
- [ ] **MODEL-11**: DecisionTreeRegressor training
- [ ] **MODEL-12**: AdaBoostRegressor training
- [ ] **MODEL-13**: KNeighborsRegressor training
- [ ] **MODEL-14**: SVR (RBF kernel) training
- [ ] **MODEL-15**: MLPRegressor training
- [ ] **MODEL-16**: XGBoost training (optional booster)
- [ ] **MODEL-17**: LightGBM training (optional booster)
- [ ] **MODEL-18**: CatBoost training (optional booster)
- [ ] **MODEL-19**: TimeSeriesSplit CV with ≥5 folds, no shuffling
- [ ] **MODEL-20**: RandomizedSearchCV or Optuna tuning with TimeSeriesSplit as CV strategy
- [ ] **MODEL-21**: Hyperparameter search spaces defined per model family

### Evaluation & Model Selection

- [ ] **EVAL-01**: R² computed per model (in-sample and OOS)
- [ ] **EVAL-02**: MAE computed per model (in-sample and OOS)
- [ ] **EVAL-03**: RMSE computed per model (in-sample and OOS)
- [ ] **EVAL-04**: MAPE computed per model (in-sample and OOS)
- [ ] **EVAL-05**: Directional Accuracy computed per model
- [ ] **EVAL-06**: Fold stability (metric variance across CV folds) computed
- [ ] **EVAL-07**: Models ranked by OOS RMSE (primary) and directional accuracy (secondary)
- [ ] **EVAL-08**: High-variance models penalized in ranking
- [ ] **EVAL-09**: ONE winner model selected
- [ ] **EVAL-10**: Model artifact, scaler pipeline, feature list, and all metrics persisted to model_registry
- [ ] **EVAL-11**: SHAP values computed for top 5 models (TreeExplainer / KernelExplainer fallback)
- [ ] **EVAL-12**: SHAP feature importance and summary data stored for frontend

### Kubeflow Pipeline

- [x] **KF-01**: Kubeflow Pipelines installed in ml namespace
- [x] **KF-02**: data_loading component (container) — loads from PostgreSQL
- [x] **KF-03**: feature_engineering component (container)
- [x] **KF-04**: label_generation component (container)
- [x] **KF-05**: train_models component (container) — parallel model training
- [x] **KF-06**: cross_validation component (container)
- [ ] **KF-07**: evaluation component (container)
- [ ] **KF-08**: model_comparison component (container)
- [x] **KF-09**: explainability component (container) — SHAP
- [x] **KF-10**: winner_selection component (container)
- [x] **KF-11**: model_persistence component (container) — saves to registry
- [x] **KF-12**: deployment component (container) — deploys winner as serving endpoint
- [x] **KF-13**: Full pipeline definition (training_pipeline.py)
- [x] **KF-14**: Pipeline is reproducible and versioned
- [x] **KF-15**: Pipeline can be triggered manually or by drift detection

### Drift Detection

- [x] **DRIFT-01**: Data drift detector using KS-test and PSI on feature distributions
- [x] **DRIFT-02**: Prediction drift detector (rolling prediction error threshold)
- [x] **DRIFT-03**: Concept drift detector (recent vs. historical model performance)
- [x] **DRIFT-04**: Daily drift check job (triggered after ingestion)
- [x] **DRIFT-05**: Drift events logged to drift_logs table with type, severity, details
- [x] **DRIFT-06**: Auto-trigger Kubeflow retraining pipeline on drift detection
- [x] **DRIFT-07**: Post-retrain: new winner selected, deployed, predictions regenerated

### React Frontend — Shared

- [ ] **FE-01**: React app bootstrapped (Vite or Next.js) with Tailwind CSS
- [ ] **FE-02**: Dark theme (Bloomberg Terminal aesthetic)
- [ ] **FE-03**: Sidebar or top navigation linking all 4 pages
- [ ] **FE-04**: Responsive layout
- [ ] **FE-05**: API client layer (Zustand or React Query) connected to FastAPI
- [ ] **FE-06**: Dockerfile + K8s Deployment/Service for frontend in frontend namespace

### Frontend — /models Page

- [ ] **FMOD-01**: Sortable, filterable table of all trained models
- [ ] **FMOD-02**: In-sample vs. OOS metrics side-by-side columns
- [ ] **FMOD-03**: Winner model highlighted with reasoning
- [ ] **FMOD-04**: SHAP feature importance bar charts
- [ ] **FMOD-05**: SHAP beeswarm plots
- [ ] **FMOD-06**: Fold-by-fold performance charts per model

### Frontend — /forecasts Page

- [ ] **FFOR-01**: Forecast table for all S&P 500 stocks (current price, predicted price, expected return %, confidence, trend indicator)
- [ ] **FFOR-02**: Filter by sector, expected return range, confidence level
- [ ] **FFOR-03**: Multi-stock comparison view (select multiple side by side)
- [ ] **FFOR-04**: Per-stock detail view with historical + forecast time series chart
- [ ] **FFOR-05**: Technical indicators overlay (RSI, MACD, Bollinger Bands) on stock detail chart
- [ ] **FFOR-06**: SHAP explanation panel per stock

### Frontend — /dashboard Page

- [ ] **FDASH-01**: S&P 500 treemap by market cap, color-coded by daily performance (green/red gradient)
- [ ] **FDASH-02**: Treemap cells clickable → opens stock detail
- [ ] **FDASH-03**: Dynamic dropdown to select individual stocks
- [ ] **FDASH-04**: Intraday candlestick/line chart (minute-level)
- [ ] **FDASH-05**: Historical OHLCV chart with adjustable timeframe
- [ ] **FDASH-06**: TA panel: RSI, MACD, Bollinger Bands, Moving Averages
- [ ] **FDASH-07**: Volume bars and VWAP overlay
- [ ] **FDASH-08**: Key metric cards: Price, Change %, Volume, Market Cap, P/E, 52w High/Low

### Frontend — /drift Page

- [ ] **FDRFT-01**: Active model info card (name, version, trained date)
- [ ] **FDRFT-02**: Rolling performance chart (RMSE, MAE, Directional Accuracy over time)
- [ ] **FDRFT-03**: Drift alert timeline (type, severity, timestamp)
- [ ] **FDRFT-04**: Retraining status panel (last date, in-progress indicator, old vs new metrics)
- [ ] **FDRFT-05**: Feature distribution charts (training vs. recent data)

### Integration & Testing

- [ ] **TEST-01**: End-to-end flow validation: ingest → Kafka → PostgreSQL
- [ ] **TEST-02**: End-to-end flow validation: PostgreSQL → Kubeflow → model registry → serving
- [ ] **TEST-03**: End-to-end flow validation: FastAPI prediction endpoints → frontend
- [ ] **TEST-04**: Drift detection → retraining → redeployment cycle validated
- [ ] **TEST-05**: seed-data.sh script for test data population

---

## v1.1 Requirements

### Live Inference Integration

- [ ] **LIVE-01**: GET /predict/{ticker} returns live model inference (not cached JSON)
- [ ] **LIVE-02**: GET /predict/bulk runs live inference for all configured tickers
- [ ] **LIVE-03**: GET /models/comparison queries model_registry table when DATABASE_URL set
- [ ] **LIVE-04**: GET /models/drift queries drift_logs table when DATABASE_URL set
- [ ] **LIVE-05**: Graceful fallback to cached file responses when DB or model unavailable
- [ ] **LIVE-06**: Frontend shows loading spinner during API fetch (no flash of mock data)
- [ ] **LIVE-07**: Frontend uses API as primary data source; mock data only on error
- [ ] **LIVE-08**: New API endpoints: /models/drift/rolling-performance and /models/retrain-status
- [ ] **LIVE-09**: Drift page powered by live API data (rolling perf, retrain status, feature dists)

### ML K8s Deployment

- [ ] **DEPLOY-01**: ML pipeline Dockerfile (Python 3.11, multi-stage, all ML dependencies)
- [ ] **DEPLOY-02**: K8s ConfigMap for ML namespace (DATABASE_URL, MODEL_REGISTRY_DIR, SERVING_DIR, DRIFT_LOG_DIR)
- [ ] **DEPLOY-03**: K8s CronJob for weekly model retraining (Sunday 03:00 UTC)
- [ ] **DEPLOY-04**: K8s CronJob for daily drift detection (weekdays 22:00 UTC)
- [ ] **DEPLOY-05**: PersistentVolumeClaim for model artifacts (5Gi, ReadWriteOnce)
- [ ] **DEPLOY-06**: model-serving Deployment uses PVC (not emptyDir)
- [ ] **DEPLOY-07**: deploy-all.sh phases 17–25 uncommented and active
- [ ] **DEPLOY-08**: ml/drift/trigger.py CLI entry point for K8s CronJob execution

### Monitoring & Observability

- [x] **MON-01**: FastAPI /metrics endpoint via prometheus-fastapi-instrumentator
- [x] **MON-02**: Custom Prometheus metrics: prediction_requests_total, prediction_latency_seconds, model_inference_errors_total
- [x] **MON-03**: Kafka consumer /metrics on port 9090 (messages_consumed_total, batch_write_duration, consumer_lag)
- [x] **MON-04**: Prometheus server deployed in monitoring namespace
- [x] **MON-05**: Grafana deployed with provisioned datasources and dashboards
- [x] **MON-06**: API Health dashboard (request rate, latency p50/p95/p99, error rate)
- [x] **MON-07**: ML Performance dashboard (model RMSE over time, retraining frequency, drift events)
- [x] **MON-08**: Alert rules: drift severity high → Slack, API error rate > 5%, Kafka consumer lag > 1000
- [ ] **MON-09**: structlog JSON output configured for FastAPI and Kafka consumer
- [ ] **MON-10**: Centralized log aggregation via Loki + Promtail with Grafana datasource

### Database Hardening

- [ ] **DBHARD-01**: Alembic configured with alembic.ini, env.py, and versions/ directory
- [ ] **DBHARD-02**: Initial Alembic migration matching db/init.sql schema (all 6 tables)
- [ ] **DBHARD-03**: API Dockerfile runs alembic upgrade head on startup
- [ ] **DBHARD-04**: SQLAlchemy async engine with connection pooling (pool_size=10, max_overflow=20)
- [ ] **DBHARD-05**: market_service.py migrated from raw psycopg2 to SQLAlchemy async sessions
- [ ] **DBHARD-06**: K8s Secrets replace hardcoded credentials in configmaps
- [ ] **DBHARD-07**: Database RBAC roles: stock_readonly (API reads), stock_writer (consumer + ML)
- [ ] **DBHARD-08**: Daily pg_dump backup CronJob with 7-day retention

### Advanced ML Capabilities

- [ ] **ADVML-01**: StackingRegressor ensemble with Ridge meta-learner from top-N base models
- [ ] **ADVML-02**: Ensemble integrated into training_pipeline.py as optional step after ranking
- [ ] **ADVML-03**: Multi-horizon target generation (1d, 7d, 30d) in label_generator.py
- [ ] **ADVML-04**: Separate model suite trained per prediction horizon
- [ ] **ADVML-05**: GET /predict/{ticker}?horizon=1|7|30 query parameter support
- [ ] **ADVML-06**: Frontend horizon toggle (1D / 7D / 30D) on Forecasts page
- [ ] **ADVML-07**: feature_store PostgreSQL table with daily CronJob for precomputed features
- [ ] **ADVML-08**: Training pipeline reads from feature store instead of computing on-the-fly

### Frontend Enhancements

- [ ] **FENH-01**: WebSocket endpoint /ws/prices pushing price updates every 5s during market hours
- [ ] **FENH-02**: useWebSocket.ts custom React hook with reconnection logic
- [ ] **FENH-03**: Dashboard CandlestickChart receives live candle updates via WebSocket
- [ ] **FENH-04**: GET /backtest/{ticker}?start=...&end=... endpoint returning actual vs predicted series
- [ ] **FENH-05**: Backtest.tsx page with dual-line chart (actual vs predicted) and metrics summary
- [x] **FENH-06**: CSV and PDF export buttons on Forecasts, Models, and Backtest pages
- [x] **FENH-07**: Mobile responsive layout (sm/md/lg breakpoints, treemap→list, tables→cards)

### Production Hardening

- [x] **PROD-01**: Redis deployed in storage namespace (single replica, 256Mi)
- [x] **PROD-02**: API response caching with configurable TTL (market 30s, predictions 60s, models 300s)
- [x] **PROD-03**: Cache invalidation on model retrain (pub/sub or manual flush)
- [ ] **PROD-04**: API rate limiting via slowapi (100/min global, 30/min /predict, 10/min /ingest)
- [ ] **PROD-05**: Deep health checks: DB connectivity, Kafka reachability, model freshness, prediction staleness
- [x] **PROD-06**: A/B model testing with traffic_weight field in model_registry
- [x] **PROD-07**: ab_test_assignments table logging which model served each prediction
- [x] **PROD-08**: GET /models/ab-results endpoint comparing live accuracy of concurrent models

### Object Storage — MinIO

- [ ] **OBJST-01**: MinIO deployed in storage namespace with persistent volume (10Gi)
- [ ] **OBJST-02**: S3 buckets created: model-artifacts, drift-logs
- [ ] **OBJST-03**: K8s Secret for MinIO root credentials (access key, secret key)
- [ ] **OBJST-04**: K8s ConfigMap with MINIO_ENDPOINT, MINIO_BUCKET_MODELS, MINIO_BUCKET_DRIFT
- [ ] **OBJST-05**: boto3 or minio SDK added to ml/requirements.txt
- [ ] **OBJST-06**: ModelRegistry save/load operations use S3-compatible API
- [ ] **OBJST-07**: Model artifacts stored at s3://model-artifacts/{model_name}/{version}/
- [ ] **OBJST-08**: STORAGE_BACKEND env var toggles between local filesystem and S3
- [ ] **OBJST-09**: Training pipeline persists artifacts to MinIO
- [ ] **OBJST-10**: Deployer uploads winner model to s3://model-artifacts/serving/active/
- [ ] **OBJST-11**: Drift pipeline reads/writes from MinIO (drift logs + baseline models)
- [ ] **OBJST-12**: K8s CronJobs use MinIO env vars instead of PVC mounts

### Model Serving — KServe

- [ ] **KSERV-01**: KServe controller deployed (cert-manager + KServe manifests)
- [ ] **KSERV-02**: KServe CRDs installed (InferenceService, ServingRuntime, ClusterServingRuntime)
- [ ] **KSERV-03**: KServe configured with S3 credentials for MinIO access
- [ ] **KSERV-04**: ClusterServingRuntime for sklearn models deployed
- [ ] **KSERV-05**: InferenceService CR pointing to s3://model-artifacts/serving/active/
- [ ] **KSERV-06**: KServe predictor pod downloads model from MinIO via storage-initializer
- [ ] **KSERV-07**: V2 inference protocol endpoint operational (POST /v2/models/{model}/infer)
- [ ] **KSERV-08**: Autoscaling configured (scale-to-zero on idle)
- [ ] **KSERV-09**: prediction_service.py calls KServe V2 inference endpoint via HTTP
- [ ] **KSERV-10**: KSERVE_INFERENCE_URL configurable via K8s ConfigMap
- [ ] **KSERV-11**: Prediction API response schema backward-compatible with pre-KServe format
- [ ] **KSERV-12**: A/B model testing uses KServe canary traffic splitting (percentTraffic)
- [ ] **KSERV-13**: Legacy model-serving.yaml Deployment removed
- [ ] **KSERV-14**: deploy-all.sh updated with MinIO + KServe deployment steps
- [x] **KSERV-15**: E2E flow validated: train → MinIO → KServe → predict → drift → retrain

---

## v2 Requirements (Deferred)

- OAuth / multi-user authentication & watchlists
- User alerts system (price/prediction/drift notifications)
- Cloud deployment (AWS/GCP/Azure)
- Non-S&P 500 universes (crypto, international equities)
- Sentiment / alternative data (news API + FinBERT)
- Sector-level model training (separate model suites per GICS sector)
- Portfolio optimization (Markowitz mean-variance, risk-parity)
- Deep learning models (LSTM, Transformer)
- KFP containerized pipeline components (replace plain K8s CronJobs)
- Live trading / order execution integration
- Canary deployment with Istio traffic splitting

## Out of Scope

- Live trading / brokerage integration — prediction platform only
- Paid data providers — Yahoo Finance only
- Cloud K8s — Minikube local for v1
- Real-time sub-second streaming — polling REST is sufficient
- User authentication — internal single-user tool
- Non-S&P 500 assets — scoped to S&P 500

## Traceability

| Phase | Requirements Covered |
|-------|---------------------|
| 1 | INFRA-03, INFRA-06, INFRA-09 |
| 2 | INFRA-01, INFRA-02, INFRA-04, INFRA-05 |
| 3 | API-01–04 |
| 4 | DB-01–07 |
| 5 | KAFKA-01–05 |
| 6 | INGEST-01–03, INGEST-06 |
| 7 | API-05–06 |
| 8 | INGEST-04–05 |
| 9 | CONS-01–07 |
| 10 | FEAT-01–14 |
| 11 | FEAT-15–21 |
| 12 | MODEL-01–06, MODEL-19–21 |
| 13 | MODEL-07–12, MODEL-16–18 |
| 14 | MODEL-13–15 |
| 15 | EVAL-01–10 |
| 16 | EVAL-11–12 |
| 17 | KF-01–04 |
| 18 | KF-05–08 |
| 19 | KF-09–12 |
| 20 | KF-13–15 |
| 21 | DRIFT-01–05 |
| 22 | DRIFT-06–07 |
| 23 | API-07–10 |
| 24 | API-11–12 |
| 25 | FE-01–06 |
| 26 | FMOD-01–06 |
| 27 | FFOR-01–06 |
| 28 | FDASH-01–08 |
| 29 | FDRFT-01–05 |
| 30 | TEST-01–05 |
| 31 | LIVE-01–05 |
| 32 | LIVE-06–09 |
| 33 | DEPLOY-01–02 |
| 34 | DEPLOY-03–08 |
| 35 | DBHARD-01–03 |
| 36 | DBHARD-06–07 |
| 37 | MON-01–03 |
| 38 | MON-04–08 |
| 39 | MON-09–10 |
| 40 | DBHARD-04–05 |
| 41 | DBHARD-08 |
| 42 | ADVML-01–02 |
| 43 | ADVML-03–06 |
| 44 | ADVML-07–08 |
| 45 | FENH-01–03 |
| 46 | FENH-04–05 |
| 47 | PROD-01–03 |
| 48 | PROD-04–05 |
| 49 | PROD-06–08 |
| 50 | FENH-06–07 |
| 51 | OBJST-01–04 |
| 52 | OBJST-05–08 |
| 53 | OBJST-09–12 |
| 54 | KSERV-01–04 |
| 55 | KSERV-05–08 |
| 56 | KSERV-09–12 |
| 57 | KSERV-13–15 |
