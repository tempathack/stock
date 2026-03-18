# Requirements

## v1 Requirements

### Infrastructure — Kubernetes / Docker

- [ ] **INFRA-01**: Minikube cluster initialized with 5 namespaces: ingestion, processing, storage, ml, frontend
- [ ] **INFRA-02**: K8s namespace YAML manifests for all 5 namespaces
- [x] **INFRA-03**: Base folder structure created (stock-prediction-platform/ tree)
- [ ] **INFRA-04**: setup-minikube.sh shell script with all cluster bootstrap steps
- [ ] **INFRA-05**: deploy-all.sh orchestration script
- [ ] **INFRA-06**: docker-compose.yml for local dev convenience
- [ ] **INFRA-07**: All services have Dockerfiles with multi-stage builds where applicable
- [ ] **INFRA-08**: All configuration via environment variables — zero hardcoded secrets
- [ ] **INFRA-09**: Structured JSON logging configured for all services

### FastAPI Backend — Base

- [ ] **API-01**: FastAPI app skeleton with config.py, main.py, router structure
- [ ] **API-02**: GET /health endpoint returning service status
- [ ] **API-03**: Dockerfile for FastAPI service (multi-stage)
- [ ] **API-04**: K8s Deployment + Service YAML for FastAPI in ingestion namespace
- [ ] **API-05**: POST /ingest/intraday endpoint (triggers Yahoo Finance intraday fetch)
- [ ] **API-06**: POST /ingest/historical endpoint (triggers Yahoo Finance historical fetch)
- [ ] **API-07**: GET /predict/{ticker} endpoint (returns 7-day forecast)
- [ ] **API-08**: GET /predict/bulk endpoint (forecasts for all S&P 500)
- [ ] **API-09**: GET /models/comparison endpoint (model metrics comparison)
- [ ] **API-10**: GET /models/drift endpoint (drift detection status)
- [ ] **API-11**: GET /market/overview endpoint (treemap + sector data)
- [ ] **API-12**: GET /market/indicators/{ticker} endpoint (technical indicators)

### PostgreSQL / Storage

- [ ] **DB-01**: PostgreSQL deployed in storage namespace with PVC
- [ ] **DB-02**: TimescaleDB extension enabled
- [ ] **DB-03**: init.sql with all table schemas: stocks, ohlcv_daily, ohlcv_intraday, predictions, model_registry, drift_logs
- [ ] **DB-04**: Composite primary keys on (ticker, date) and (ticker, timestamp)
- [ ] **DB-05**: Indexes on (ticker, date) and (ticker, timestamp)
- [ ] **DB-06**: Partitioning on date columns for ohlcv_daily and ohlcv_intraday
- [ ] **DB-07**: K8s ConfigMap for PostgreSQL credentials

### Kafka / Streaming

- [ ] **KAFKA-01**: Strimzi operator deployed in storage namespace
- [ ] **KAFKA-02**: Kafka broker with persistent storage
- [ ] **KAFKA-03**: intraday-data topic created
- [ ] **KAFKA-04**: historical-data topic created
- [ ] **KAFKA-05**: K8s manifests for Kafka/Strimzi

### Data Ingestion

- [ ] **INGEST-01**: yahoo_finance.py service — fetches OHLCV for S&P 500 tickers via yfinance
- [ ] **INGEST-02**: S&P 500 ticker list (dev: 20-stock subset, prod: full universe)
- [ ] **INGEST-03**: kafka_producer.py — validates, normalizes, and publishes to Kafka topics
- [ ] **INGEST-04**: K8s CronJob for intraday ingestion (daily, market hours)
- [ ] **INGEST-05**: K8s CronJob for historical ingestion (weekly)
- [ ] **INGEST-06**: Data validation and normalization logic (schema enforcement, nulls, types)

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

- [ ] **KF-01**: Kubeflow Pipelines installed in ml namespace
- [ ] **KF-02**: data_loading component (container) — loads from PostgreSQL
- [ ] **KF-03**: feature_engineering component (container)
- [ ] **KF-04**: label_generation component (container)
- [ ] **KF-05**: train_models component (container) — parallel model training
- [ ] **KF-06**: cross_validation component (container)
- [ ] **KF-07**: evaluation component (container)
- [ ] **KF-08**: model_comparison component (container)
- [ ] **KF-09**: explainability component (container) — SHAP
- [ ] **KF-10**: winner_selection component (container)
- [ ] **KF-11**: model_persistence component (container) — saves to registry
- [ ] **KF-12**: deployment component (container) — deploys winner as serving endpoint
- [ ] **KF-13**: Full pipeline definition (training_pipeline.py)
- [ ] **KF-14**: Pipeline is reproducible and versioned
- [ ] **KF-15**: Pipeline can be triggered manually or by drift detection

### Drift Detection

- [ ] **DRIFT-01**: Data drift detector using KS-test and PSI on feature distributions
- [ ] **DRIFT-02**: Prediction drift detector (rolling prediction error threshold)
- [ ] **DRIFT-03**: Concept drift detector (recent vs. historical model performance)
- [ ] **DRIFT-04**: Daily drift check job (triggered after ingestion)
- [ ] **DRIFT-05**: Drift events logged to drift_logs table with type, severity, details
- [ ] **DRIFT-06**: Auto-trigger Kubeflow retraining pipeline on drift detection
- [ ] **DRIFT-07**: Post-retrain: new winner selected, deployed, predictions regenerated

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

## v2 Requirements (Deferred)

- OAuth / multi-user authentication
- Cloud deployment (AWS/GCP/Azure)
- Non-S&P 500 universes (crypto, international equities)
- Real-time WebSocket streaming to frontend
- Live trading / order execution integration
- Deep learning models (LSTM, Transformer)

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
| TBD — see ROADMAP.md | |
