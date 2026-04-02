# Stock Prediction Platform

## What This Is

A production-grade, scalable stock prediction platform for the S&P 500 universe. It ingests real-time and historical market data via a Kafka streaming pipeline, trains and evaluates all major scikit-learn regression models through an automated Kubeflow ML pipeline, and serves 7-day price forecasts through a React dashboard with Bloomberg Terminal aesthetics.

## Core Value

The winner ML model is always the best-performing, drift-aware regressor — automatically retrained and redeployed whenever prediction quality degrades, with every decision visible in the dashboard.

## Requirements

### Validated

- [x] Minikube-based Kubernetes cluster with namespace separation (ingestion, processing, storage, ml, frontend) — Validated in Phase 2
- [x] Every service has a Dockerfile with multi-stage builds — Validated in Phase 3
- [x] All config via environment variables — no hardcoded secrets — Validated in Phase 3
- [x] FastAPI service with /health endpoint — Validated in Phase 3
- [x] PostgreSQL with TimescaleDB: stocks, ohlcv_daily, ohlcv_intraday, predictions, model_registry, drift_logs tables — Validated in Phase 4: live cluster confirmed 6 tables, hypertables, indexes, TimescaleDB 2.25.2

### Active

- [ ] FastAPI service full endpoints: /ingest/intraday, /ingest/historical, /predict/{ticker}, /predict/bulk, /models/comparison, /models/drift, /market/overview, /market/indicators/{ticker}
- [x] Kafka via Strimzi: intraday-data and historical-data topics — Validated in Phase 5: KRaft mode, Strimzi 0.40, both topics produce/consume confirmed
- [ ] K8s CronJobs for intraday (daily, market hours) and historical (weekly) ingestion
- [ ] Yahoo Finance ingestion for all S&P 500 stocks (dev: 20 stocks subset)
- [ ] Kafka consumers with micro-batch processing, idempotent upserts, retry/dead-letter handling
- [ ] Feature engineering: RSI, MACD, Stochastic, SMA/EMA/ADX, Bollinger/ATR/volatility, OBV/VWAP/A-D, lag features (t-1 to t-21), rolling stats
- [ ] Multiple sklearn-compatible transformation pipeline variants (StandardScaler, QuantileTransformer, MinMaxScaler)
- [ ] t+7 target label generation with no data leakage
- [ ] Train all sklearn regressors: Linear, Ridge, Lasso, ElasticNet, BayesianRidge, HuberRegressor, RF, GBM, HistGBM, ExtraTrees, DT, AdaBoost, KNN, SVR, MLP, optionally XGBoost/LightGBM/CatBoost
- [ ] TimeSeriesSplit CV (≥5 folds), no shuffling, no leakage
- [ ] RandomizedSearchCV or Optuna hyperparameter tuning per model family
- [ ] Evaluation metrics: R², MAE, RMSE, MAPE, Directional Accuracy, fold stability
- [ ] Model comparison: rank by OOS RMSE, penalize variance, select ONE winner
- [ ] SHAP values for top 5 models (TreeExplainer / KernelExplainer fallback)
- [ ] 11-step Kubeflow pipeline: data_loading → feature_engineering → label_generation → train_models → cross_validation → evaluation → model_comparison → explainability → winner_selection → model_persistence → deployment
- [ ] Each Kubeflow step is a separate container, reproducible, versioned
- [ ] Drift detection: data drift (KS-test, PSI), prediction drift (rolling error threshold), concept drift (performance degradation)
- [ ] Daily drift checks, drift_logs table, auto-retrain trigger
- [ ] React frontend (Vite or Next.js, Tailwind, Recharts/Lightweight Charts, Zustand/React Query)
- [ ] Page 1 /models: sortable model comparison table, SHAP charts, fold-by-fold charts, winner highlighted
- [ ] Page 2 /forecasts: all S&P 500 forecasts, filtering by sector/return/confidence, stock comparison, per-stock detail with TA overlay and SHAP
- [ ] Page 3 /dashboard: treemap by market cap (color by daily perf), intraday candlestick, historical chart, TA panel (RSI/MACD/BBands/MAs/Volume/VWAP), metric cards
- [ ] Page 4 /drift: active model info, rolling performance charts, drift alert timeline, retraining status, feature distribution charts

### Out of Scope

- Live trading / order execution — prediction only, no brokerage integration
- Non-S&P 500 universes — scoped to S&P 500 for v1
- Real-time sub-second streaming to frontend — polling/REST sufficient for v1
- Authentication / multi-user — single-user internal tool
- Cloud deployment (AWS/GCP/Azure) — Minikube local for v1

## Context

- Local Kubernetes via Minikube; all services as K8s manifests or Helm charts
- Structured JSON logging throughout; comprehensive error handling with retries
- Type hints and docstrings on all Python public functions
- Implementation order strictly follows the 17-phase sequence in Project_scope.md
- Dev phase uses 20-stock subset before scaling to full S&P 500 universe

## Constraints

- **Infrastructure**: Minikube only — no cloud K8s for v1
- **Data Source**: Yahoo Finance (yfinance) only — no paid data providers
- **ML Framework**: scikit-learn primary; XGBoost/LightGBM/CatBoost optional boosters
- **Time Series CV**: TimeSeriesSplit mandatory — no random splits ever
- **Code Quality**: Production-ready — no pseudo-code, no placeholders, no skipped steps

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Minikube for local K8s | No cloud costs, full K8s feature parity for dev | — Pending |
| Kafka via Strimzi operator | Production-grade operator, K8s-native | Deployed — 0.40.0, KRaft mode, storage namespace, OOMKill fix: operator 768Mi / entity-op 512Mi |
| TimescaleDB extension on PostgreSQL | Time-series query optimization for large OHLCV tables | Deployed — 2.25.2, 6 tables, 2 hypertables |
| Kubeflow for ML pipeline | Containerized, reproducible, versionable pipeline steps | — Pending |
| SHAP for explainability | Industry standard, supports tree and kernel explainers | — Pending |
| Bloomberg Terminal dark aesthetic | Professional trading tool UX standard | Validated in Phase 69 |

---
*Last updated: 2026-04-02 — Phase 75 complete (Data quality fixes — Drift page null RMSE now renders as em-dash via previous_oos_metrics API field, Analytics integrations wired (ArgoCD K8s CRD, Feast latency cached 60s), OOS prefix stripping confirmed correct with regression tests, confidence variation guard added for constant-score ML output)*
