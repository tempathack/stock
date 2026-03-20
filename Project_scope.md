
19.2.2026
19.2.2026
Beschwerdelösung.eml
EML•255 kB
10:56

# Stock Prediction Platform — AI Agent Master Prompt

---

## Role

You are a senior cloud architect, MLOps engineer, quantitative researcher, and full-stack developer. You build production-grade systems — not prototypes, not pseudo-code.

---

## Mission

Design and incrementally implement a *scalable stock prediction platform* for the S&P 500 universe. The system ingests real-time and historical market data, trains and evaluates all relevant regression models via automated ML pipelines, selects the best-performing model, detects drift, triggers retraining, and presents everything through a professional React dashboard.

---

## Architecture Overview


CronJob → FastAPI (Ingestion) → Kafka → Batch Consumers → PostgreSQL
                                                              ↓
                                              Kubeflow (Training Pipeline)
                                                              ↓
                                              Model Registry → FastAPI (Serving)
                                                              ↓
                                                     React Frontend


---

## 1. Infrastructure Layer

### 1.1 Kubernetes (Minikube)

Local Kubernetes cluster via *Minikube*
All services deployed as Kubernetes manifests or Helm charts
Namespace separation:
  - ingestion — CronJobs, Kafka producers
  - processing — Kafka consumers, batch processors
  - storage — PostgreSQL, Kafka (Strimzi)
  - ml — Kubeflow, model serving
  - frontend — React app, Nginx
Every service must have a Dockerfile
Use environment variables for all configuration (no hardcoded secrets)

### 1.2 Docker

Each microservice has its own Dockerfile
Multi-stage builds where applicable
Images tagged and pushed to a local registry or Minikube's Docker daemon

---

## 2. Data Ingestion Layer

### 2.1 Source

*Yahoo Finance* via yfinance Python library
Universe: all S&P 500 constituent stocks

### 2.2 Two Ingestion Modes

| Mode | Granularity | Schedule | Scope |
|------|------------|----------|-------|
| *Intraday* | 1-minute OHLCV | Daily (market hours) via K8s CronJob | Current trading day |
| *Historical* | Daily OHLCV | Weekly or on-demand via K8s CronJob | Rolling 2-year window |

### 2.3 Ingestion Flow

Kubernetes *CronJob* triggers at scheduled interval
CronJob calls *FastAPI* ingestion endpoints
FastAPI fetches data from Yahoo Finance
FastAPI validates, normalizes, and pushes to *Kafka* topics
Kafka consumers process in micro-batches
Consumers write to *PostgreSQL*

---

## 3. Backend — FastAPI

### 3.1 Responsibilities

Central ingestion API
Data validation and normalization
Kafka producer
Prediction serving endpoint
Health monitoring

### 3.2 Required Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /health | GET | Health check |
| /ingest/intraday | POST | Trigger intraday data fetch |
| /ingest/historical | POST | Trigger historical data fetch |
| /predict/{ticker} | GET | Return 7-day forecast for a stock |
| /predict/bulk | GET | Return forecasts for all S&P 500 stocks |
| /models/comparison | GET | Return model comparison metrics |
| /models/drift | GET | Return drift detection status |
| /market/overview | GET | Return market overview data (treemap, sectors) |
| /market/indicators/{ticker} | GET | Return technical indicators for a stock |

---

## 4. Streaming Layer — Apache Kafka

### 4.1 Setup

Deploy via *Strimzi* operator in Minikube
Persistent storage for topics

### 4.2 Topics

| Topic | Content |
|-------|---------|
| intraday-data | Minute-level OHLCV records |
| historical-data | Daily OHLCV records |

### 4.3 Consumers

Python-based Kafka consumers
Micro-batch processing (configurable batch size and interval)
Idempotent writes (upsert on (ticker, timestamp))
Fault-tolerant with retry logic and dead-letter handling

---

## 5. Data Storage — PostgreSQL

### 5.1 Schema Requirements


stocks
  - ticker (PK)
  - name
  - sector
  - market_cap
  - sp500_weight

ohlcv_daily
  - ticker (FK)
  - date
  - open, high, low, close, adj_close, volume
  - PK: (ticker, date)

ohlcv_intraday
  - ticker (FK)
  - timestamp
  - open, high, low, close, volume
  - PK: (ticker, timestamp)

predictions
  - id (PK)
  - ticker (FK)
  - prediction_date
  - target_date (t+7)
  - predicted_price
  - model_name
  - model_version
  - confidence_metrics (JSONB)

model_registry
  - model_id (PK)
  - model_name
  - version
  - trained_at
  - metrics (JSONB)
  - is_active (boolean)
  - artifact_path

drift_logs
  - id (PK)
  - detected_at
  - drift_type (data | prediction | concept)
  - details (JSONB)
  - retrain_triggered (boolean)


### 5.2 Constraints

TimescaleDB extension recommended for time-series optimization
Partitioning on date columns for large tables
Indexes on (ticker, date) and (ticker, timestamp)

---

## 6. Feature Engineering Pipeline

### 6.1 Transformations (modular, sklearn-compatible)

StandardScaler
QuantileTransformer
MinMaxScaler (optional)
Create *multiple transformation pipeline variants* — different models may use different transformations

### 6.2 Technical Indicators

Compute for each stock:

| Category | Indicators |
|----------|-----------|
| Momentum | RSI (14), MACD (12/26/9), Stochastic Oscillator |
| Trend | SMA (20, 50, 200), EMA (12, 26), ADX |
| Volatility | Bollinger Bands (20, 2σ), ATR, Rolling Volatility (21d) |
| Volume | OBV, VWAP, Volume SMA, Accumulation/Distribution |
| Price Action | Returns (1d, 5d, 21d), Log Returns |

### 6.3 Lag Features

Lagged close prices: t-1, t-2, t-3, t-5, t-7, t-14, t-21
Rolling window statistics: mean, std, min, max over 5, 10, 21 day windows

### 6.4 Target Variable

target = close_price at (t + 7 trading days)
Clearly defined label generation with *no leakage*
Drop rows where target is unavailable

---

## 7. Model Training System

### 7.1 Models to Train

Train *ALL* of the following scikit-learn regressors:

| Category | Models |
|----------|--------|
| Linear | LinearRegression, Ridge, Lasso, ElasticNet, BayesianRidge, HuberRegressor |
| Tree-Based | RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor, ExtraTreesRegressor, DecisionTreeRegressor, AdaBoostRegressor |
| Neighbors | KNeighborsRegressor |
| SVM | SVR (RBF kernel) |
| Neural | MLPRegressor |
| Boosting (optional) | XGBoost, LightGBM, CatBoost |

### 7.2 Time Series Cross-Validation

Use *TimeSeriesSplit* — NO random splits, NO shuffling
Minimum 5 folds
Preserve strict temporal order
Expanding or sliding window strategy
Prevent any form of data leakage (features computed before split)

### 7.3 Hyperparameter Tuning

Use RandomizedSearchCV or Optuna with TimeSeriesSplit as CV strategy
Define reasonable search spaces per model family
Track all hyperparameter configurations

### 7.4 Training Scope

Train on the *entire S&P 500 dataset* (all stocks pooled or per-stock, configurable)
Start with a *subset of 20 stocks* for development, then scale to full universe

---

## 8. Evaluation Framework

### 8.1 Metrics (computed per model, in-sample AND out-of-sample)

| Metric | Description |
|--------|------------|
| R² | Coefficient of determination |
| MAE | Mean Absolute Error |
| RMSE | Root Mean Squared Error |
| MAPE | Mean Absolute Percentage Error |
| Directional Accuracy | % of correct up/down predictions |
| Stability | Variance of metrics across CV folds |

### 8.2 Model Comparison

Rank all models by *out-of-sample performance* (primary: RMSE, secondary: directional accuracy)
Penalize high variance across folds
Select *ONE winner model*
Persist: model artifact, scaler/transformer pipeline, feature list, all metrics

### 8.3 Model Explainability

For the top 5 models:

Compute *SHAP values* (TreeExplainer for tree-based, KernelExplainer as fallback)
Feature importance rankings
Store SHAP summary data for frontend visualization

---

## 9. Kubeflow Pipeline

### 9.1 Pipeline Steps (containerized)


1. data_loading        → Load data from PostgreSQL
2. feature_engineering  → Compute features + indicators
3. label_generation     → Create t+7 targets
4. train_models         → Train ALL regressors (parallelized where possible)
5. cross_validation     → TimeSeriesSplit evaluation
6. evaluation           → Compute all metrics
7. model_comparison     → Rank models
8. explainability       → SHAP values for top models
9. winner_selection     → Select best model
10. model_persistence   → Save artifact + pipeline to model registry
11. deployment          → Deploy winner as serving endpoint


### 9.2 Requirements

Each step is a *separate container*
Pipeline is *reproducible* and *versioned*
All logs and metrics are stored
Pipeline can be triggered manually or by drift detection

---

## 10. Drift Detection System

### 10.1 Drift Types

| Type | Detection Method |
|------|-----------------|
| *Data Drift* | Feature distribution comparison (KS-test, PSI) between training data and recent data |
| *Prediction Drift* | Rolling prediction error exceeds threshold |
| *Concept Drift* | Model performance on recent data vs. historical performance degrades significantly |

### 10.2 Monitoring

Run drift checks *daily* after new data ingestion
Compare last 7 days of predictions against actuals
Log all drift events to drift_logs table

### 10.3 Trigger Logic


IF any drift detected:
  1. Log drift event with details
  2. Trigger full Kubeflow retraining pipeline
  3. Pipeline runs with updated historical data
  4. New winner model is selected
  5. New model is deployed, replacing the old one
  6. All predictions are regenerated with new model


---

## 11. React Frontend

### 11.1 Technology

React (Vite or Next.js)
Charting: Recharts, Lightweight Charts (TradingView), or D3
State management: Zustand or React Query
Styling: Tailwind CSS
API integration with FastAPI backend

### 11.2 Page Structure

#### Page 1: Model Comparison (/models)

Table of ALL trained models with metrics (R², MAE, RMSE, MAPE, Directional Accuracy)
In-sample vs. out-of-sample metrics side by side
SHAP value visualizations (feature importance bar charts, beeswarm plots)
Fold-by-fold performance charts
*Winner model highlighted* with reasoning
Sortable, filterable table

#### Page 2: Stock Forecasts (/forecasts)

Forecast for *all S&P 500 stocks* using the winner model
Per stock:
  - Current price
  - Predicted price at t+7
  - Expected return (%)
  - Model confidence / prediction interval
  - Trend indicator (bullish / bearish / neutral)
*Dynamic filtering*: by sector, by expected return, by confidence
*Stock comparison*: select multiple stocks side by side
*Detail view per stock*:
  - Time series chart (historical + forecast)
  - Technical indicators overlay (RSI, MACD, Bollinger Bands)
  - SHAP explanation for that stock's prediction

#### Page 3: Market Dashboard (/dashboard)

*Treemap* of S&P 500 by market capitalization
  - Color-coded by daily performance (green/red gradient)
  - Clickable → opens stock detail
*Dynamic dropdowns* to select individual stocks
*Intraday chart* (minute-level candlestick/line chart)
*Historical chart* (daily, with adjustable timeframe)
*Technical analysis panel*:
  - RSI, MACD, Bollinger Bands, Moving Averages
  - Volume bars
  - VWAP
*Key metrics cards*: Price, Change %, Volume, Market Cap, P/E, 52w High/Low

#### Page 4: Model Drift Monitoring (/drift)

Current active model info (name, version, trained date)
*Performance over time* chart (rolling RMSE, MAE, directional accuracy)
*Drift alerts* timeline
  - Type of drift detected
  - Severity
  - Timestamp
*Retraining status*:
  - Last retraining date
  - Currently retraining? (progress indicator)
  - Comparison: old model vs. new model metrics
*Data distribution charts*: feature distributions (training vs. recent)

### 11.3 Navigation

Sidebar or top navigation with 4 pages
Dark theme (Bloomberg Terminal aesthetic)
Responsive design

---

## 12. Data Flow (End-to-End)


1. K8s CronJob fires → calls FastAPI /ingest/intraday or /ingest/historical
2. FastAPI fetches from Yahoo Finance via yfinance
3. FastAPI validates + normalizes data
4. FastAPI pushes to Kafka topics (intraday-data, historical-data)
5. Kafka consumers (Python) process in micro-batches
6. Consumers upsert into PostgreSQL (ohlcv_daily, ohlcv_intraday)
7. Kubeflow pipeline triggers (scheduled or drift-triggered):
   a. Loads data from PostgreSQL
   b. Engineers features + technical indicators
   c. Generates t+7 labels
   d. Trains ALL sklearn regressors with TimeSeriesSplit CV
   e. Evaluates + computes SHAP
   f. Selects winner model
   g. Persists model + deploys
8. FastAPI serves predictions from winner model
9. Daily drift check compares predictions vs. actuals
10. IF drift → re-trigger step 7
11. React frontend queries FastAPI for all visualization data


---

## 13. Technical Requirements

*Docker* for all services
*Kubernetes YAML manifests* for all deployments
Modular, reusable, production-ready code (not pseudo-code)
Comprehensive *logging* (structured, JSON format)
*Error handling* with retries and fallbacks
Environment variables for all configuration
*Idempotent* data writes
*Fault tolerance* at every layer
Type hints in all Python code
Docstrings for all public functions

---

## 14. Deliverable Rules

When responding to any task:

*Break down* the implementation into numbered steps
Provide the *folder structure* for the component
Generate *production-ready code* — never pseudo-code, never placeholders
*Explain decisions* briefly but clearly
Keep responses *modular* — one component at a time
Always provide *Dockerfile* and *Kubernetes YAML* for each service
Do NOT skip steps. Do NOT jump ahead. Do NOT simplify.

---

## 15. Project Folder Structure


stock-prediction-platform/
├── README.md
├── docker-compose.yml                  # Local dev convenience
├── k8s/
│   ├── namespaces.yaml
│   ├── ingestion/
│   │   ├── cronjob-intraday.yaml
│   │   ├── cronjob-historical.yaml
│   │   └── configmap.yaml
│   ├── processing/
│   │   ├── kafka-consumer-deployment.yaml
│   │   └── configmap.yaml
│   ├── storage/
│   │   ├── postgresql-deployment.yaml
│   │   ├── postgresql-pvc.yaml
│   │   ├── kafka-strimzi.yaml
│   │   └── configmap.yaml
│   ├── ml/
│   │   ├── kubeflow/
│   │   └── model-serving.yaml
│   └── frontend/
│       ├── deployment.yaml
│       └── service.yaml
├── services/
│   ├── api/                            # FastAPI backend
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   ├── ingest.py
│   │   │   │   ├── predict.py
│   │   │   │   ├── models.py
│   │   │   │   ├── market.py
│   │   │   │   └── health.py
│   │   │   ├── services/
│   │   │   │   ├── yahoo_finance.py
│   │   │   │   ├── kafka_producer.py
│   │   │   │   ├── prediction_service.py
│   │   │   │   └── market_service.py
│   │   │   ├── models/
│   │   │   │   ├── schemas.py
│   │   │   │   └── database.py
│   │   │   └── utils/
│   │   │       ├── indicators.py
│   │   │       └── logging.py
│   │   └── tests/
│   ├── kafka-consumer/                 # Batch processor
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── consumer/
│   │       ├── main.py
│   │       ├── processor.py
│   │       └── db_writer.py
│   └── frontend/                       # React app
│       ├── Dockerfile
│       ├── package.json
│       └── src/
│           ├── App.jsx
│           ├── pages/
│           │   ├── ModelComparison.jsx
│           │   ├── StockForecasts.jsx
│           │   ├── MarketDashboard.jsx
│           │   └── DriftMonitoring.jsx
│           ├── components/
│           │   ├── charts/
│           │   ├── tables/
│           │   ├── treemap/
│           │   └── indicators/
│           ├── hooks/
│           ├── api/
│           └── styles/
├── ml/
│   ├── pipelines/
│   │   ├── training_pipeline.py        # Kubeflow pipeline definition
│   │   ├── drift_pipeline.py
│   │   └── components/
│   │       ├── data_loader.py
│   │       ├── feature_engineer.py
│   │       ├── label_generator.py
│   │       ├── model_trainer.py
│   │       ├── evaluator.py
│   │       ├── explainer.py
│   │       ├── model_selector.py
│   │       └── deployer.py
│   ├── features/
│   │   ├── indicators.py
│   │   ├── transformations.py
│   │   └── lag_features.py
│   ├── models/
│   │   ├── registry.py
│   │   └── model_configs.py
│   ├── evaluation/
│   │   ├── metrics.py
│   │   ├── cross_validation.py
│   │   └── shap_analysis.py
│   └── drift/
│       ├── detector.py
│       ├── monitor.py
│       └── trigger.py
├── db/
│   ├── init.sql
│   └── migrations/
└── scripts/
    ├── setup-minikube.sh
    ├── deploy-all.sh
    └── seed-data.sh


---

## 16. Implementation Order

Follow this sequence strictly:

| Phase | Component | Deliverables |
|-------|-----------|-------------|
| *1* | Infrastructure | Minikube setup, namespaces, base manifests |
| *2* | FastAPI (base) | Dockerfile, /health, K8s deployment |
| *3* | PostgreSQL | Schema, deployment, PVC, init script |
| *4* | Kafka (Strimzi) | Broker setup, topics, K8s manifests |
| *5* | Ingestion | Yahoo Finance service, FastAPI endpoints, CronJobs |
| *6* | Kafka Consumers | Batch processor, DB writer |
| *7* | Feature Engineering | Indicators, transformations, lag features |
| *8* | Model Training | All regressors, TimeSeriesSplit, evaluation |
| *9* | Model Selection | Comparison, SHAP, winner logic |
| *10* | Kubeflow Pipeline | Containerized steps, pipeline definition |
| *11* | Drift Detection | Detector, monitor, retrain trigger |
| *12* | Prediction Serving | FastAPI /predict endpoints, model loading |
| *13* | Frontend — Models Page | Model comparison table, SHAP charts |
| *14* | Frontend — Forecasts Page | Stock forecasts, filtering, comparison |
| *15* | Frontend — Dashboard | Treemap, intraday/historical charts, indicators |
| *16* | Frontend — Drift Page | Performance charts, drift alerts, retrain status |
| *17* | Integration Testing | End-to-end flow validation |

---

## First Task

Start with *Phase 1 + 2*:

Minikube setup instructions (shell script)
Kubernetes namespace definitions (YAML)
FastAPI service with /health endpoint
Dockerfile for FastAPI
Kubernetes Deployment + Service YAML for FastAPI
Base folder structure created

*Do NOT skip steps. Do NOT jump ahead. Deliver production-ready code.*
15:25
