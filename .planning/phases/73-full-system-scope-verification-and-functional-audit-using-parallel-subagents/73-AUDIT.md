---
phase: 73
status: in-progress
audit_date: 2026-03-31
total_requirements: 211
requirements_verified: 98
requirements_orphaned: 113
requirements_deferred: 11
gaps_critical: 0
gaps_missing_test: 0
gaps_stub: 0
---

# Phase 73 — Full System Audit

**Audit date:** 2026-03-31
**Audited by:** Parallel domain subagents (Plans 73-02 through 73-07)
**Platform:** Stock prediction platform — Phases 1–72

---

## Phase Completion Summary

| Phase | Name | Status | Plans Completed | Completion Date |
|-------|------|--------|-----------------|-----------------|
| 1 | Repo & Folder Scaffold | Complete | 3/3 | 2026-03-18 |
| 2 | Minikube & K8s Namespaces | Complete | 2/2 | 2026-03-18 |
| 3 | FastAPI Base Service | Complete | 2/2 (3 plans) | 2026-03-19 |
| 4 | PostgreSQL + TimescaleDB | Complete | 3/3 | 2026-03-19 |
| 5 | Kafka via Strimzi | Complete | 2/2 | 2026-03-19 |
| 6 | Yahoo Finance Ingestion Service | Complete | 2/2 | 2026-03-19 |
| 7 | FastAPI Ingestion Endpoints | Complete | 1/1 | 2026-03-19 |
| 8 | K8s CronJobs for Ingestion | Complete | 1/1 | 2026-03-19 |
| 9 | Kafka Consumers — Batch Writer | Complete | 2/2 | 2026-03-19 |
| 10 | Technical Indicators | Complete | 4/4 | 2026-03-19 |
| 11 | Lag Features & Transformer Pipelines | Complete | 2/2 | 2026-03-19 |
| 12 | Linear & Regularized Models | Complete | 3/3 | 2026-03-19 |
| 13 | Tree-Based & Boosting Models | Complete | 2/2 | 2026-03-19 |
| 14 | Distance, SVM & Neural Models | Complete | 2/2 | 2026-03-19 |
| 15 | Evaluation Framework & Model Selection | Complete | 3/3 | 2026-03-20 |
| 16 | SHAP Explainability | Complete | 1/1 | 2026-03-20 |
| 17 | Kubeflow Pipeline — Data & Feature Components | Complete | 2/2 | 2026-03-20 |
| 18 | Kubeflow Pipeline — Training & Eval Components | Complete | 2/2 | 2026-03-20 |
| 19 | Kubeflow Pipeline — Selection, Persistence & Deployment | Complete | 2/2 | 2026-03-20 |
| 20 | Kubeflow Pipeline — Full Definition & Trigger | Complete | 2/2 | 2026-03-20 |
| 21 | Drift Detection System | Complete | 2/2 | 2026-03-20 |
| 22 | Drift Auto-Retrain Trigger | Complete | 1/1 | 2026-03-20 |
| 23 | FastAPI Prediction & Model Endpoints | Complete | 1/1 | 2026-03-20 |
| 24 | FastAPI Market Endpoints | Complete | 1/1 | 2026-03-21 |
| 25 | React App Bootstrap & Navigation | Complete | — | 2026-03-21 |
| 26 | Frontend — /models Page | Complete | — | 2026-03-21 |
| 27 | Frontend — /forecasts Page | Complete | — | 2026-03-21 |
| 28 | Frontend — /dashboard Page | Complete | — | 2026-03-22 |
| 29 | Frontend — /drift Page | Complete | — | 2026-03-22 |
| 30 | Integration Testing & Seed Data | Complete | 5/5 | 2026-03-23 |
| 31 | Live Model Inference API | Complete | 3/3 | 2026-03-23 |
| 32 | Frontend Live Data Integration | Complete | 2/2 | 2026-03-23 |
| 33 | ML Pipeline Container & Config | Complete | 2/2 | 2026-03-23 |
| 34 | K8s ML CronJobs & Model Serving | Complete | 3/3 | 2026-03-23 |
| 35 | Alembic Migration System | Complete | 2/2 | 2026-03-23 |
| 36 | Secrets Management & DB RBAC | Complete | 2/2 | 2026-03-23 |
| 37 | Prometheus Metrics Instrumentation | Complete | 2/2 | 2026-03-23 |
| 38 | Grafana Dashboards & Alerting | Complete | 3/3 | 2026-03-23 |
| 39 | Structured Logging & Aggregation | Complete | 2/2 | 2026-03-23 |
| 40 | SQLAlchemy Connection Pooling | Complete | 2/2 | 2026-03-23 |
| 41 | Database Backup Strategy | Complete | 1/1 | 2026-03-23 |
| 42 | Ensemble Stacking | Complete | 2/2 | 2026-03-23 |
| 43 | Multi-Horizon Predictions | Complete | 3/3 | 2026-03-24 |
| 44 | Feature Store | Complete | 2/2 | 2026-03-24 |
| 45 | WebSocket Live Prices | Complete | 2/2 | 2026-03-24 |
| 46 | Backtesting UI | Complete | 2/2 | 2026-03-24 |
| 47 | Redis Caching Layer | Complete | 2/2 | 2026-03-24 |
| 48 | Rate Limiting & Deep Health Checks | Complete | 2/2 | 2026-03-24 |
| 49 | A/B Model Testing | Complete | 2/2 | 2026-03-24 |
| 50 | Export & Mobile Responsive | Complete | 2/2 | 2026-03-24 |
| 51 | MinIO Object Storage Deployment | Complete | 2/2 | 2026-03-24 |
| 52 | Model Registry S3 Backend | Complete | 2/2 | 2026-03-24 |
| 53 | Training & Drift Pipeline MinIO Integration | Complete | 2/2 | 2026-03-24 |
| 54 | KServe Installation & Configuration | Complete | 2/2 | 2026-03-24 |
| 55 | KServe InferenceService Deployment | Complete | 2/2 | 2026-03-25 |
| 56 | API & Frontend KServe Adaptation | Complete | 2/2 | 2026-03-25 |
| 57 | Migration Cleanup & E2E Validation | Complete | 2/2 | 2026-03-25 |
| 58 | Docker-Compose Runtime Fixes | Complete | 1/1 | 2026-03-25 |
| 59 | Minikube E2E Validation | Complete | 4/4 | 2026-03-25 |
| 60 | Fix model_name in predict response | Complete | 2/2 | 2026-03-25 |
| 61 | Playwright E2E — Frontend Coverage | Complete | 5/5 | 2026-03-25 |
| 62 | Playwright E2E — Infra Coverage | Complete | 5/5 | 2026-03-25 |
| 63 | Fix E2E Test Assertions | Complete | 1/1 | 2026-03-25 |
| 64 | TimescaleDB OLAP — Continuous Aggregates & Compression | Complete | 2/2 | 2026-03-29 |
| 65 | Argo CD — GitOps Deployment Pipeline | Complete | 2/2 | 2026-03-29 |
| 66 | Feast — Production Feature Store | Complete | 3/3 | 2026-03-30 |
| 67 | Apache Flink — Real-Time Stream Processing | Complete | 3/3 | 2026-03-30 |
| 68 | E2E Integration — v3.0 Stack Validation | Complete | 2/2 | 2026-03-30 |
| 69 | Frontend — /analytics Page | Complete | 2/2 | 2026-03-30 |
| 70 | Display Flink Computed Streaming Features | Complete | 2/2 | 2026-03-31 |
| 71 | High-Frequency Alternative Data Pipeline (Sentiment) | Complete | 4/4 | 2026-03-31 |
| 72 | Grafana Debug Dashboards with Flink Metrics | Complete | 2/2 | 2026-03-31 |

Key observations:
- Phases 1–72 all shown as Complete in STATE.md phase completion log
- Phases 1–30: SUMMARY.md frontmatter evidence exists for select phases (1–22); phases 23–30 complete per STATE.md log with no separate SUMMARY files
- Phases 31–57: Complete per STATE.md (v1.1 milestone) but only PLAN.md files exist — no SUMMARY.md frontmatter evidence; REQ-IDs for these phases are ORPHANED in this audit
- Phases 58–72: SUMMARY.md frontmatter evidence exists and confirms completion
- Phase 65 uses GITOPS-xx IDs (not present in REQUIREMENTS.md traceability — new requirement domain added during execution)
- Phase 70 uses TBD-xx IDs (placeholder IDs — new requirement domain not yet formalized)
- Phase 71 uses ALT-xx IDs (new requirement domain for alternative data)
- Phase 69 uses UI-RT-xx IDs (new requirement domain for real-time UI)
- Phase 68 uses V3INT-xx IDs (new requirement domain for v3.0 integration)
- Phase 64 uses TSDB-xx IDs (new requirement domain for TimescaleDB OLAP)
- Phase 67 uses FLINK-xx IDs (new requirement domain for Flink streaming)

---

## Requirements Traceability Table

Evidence key:
- **VERIFIED** — REQ-ID appears in a phase SUMMARY.md requirements-completed field
- **CHECKBOX-ONLY** — [x] in REQUIREMENTS.md but no SUMMARY.md frontmatter evidence
- **ORPHANED** — Assigned in traceability, no SUMMARY.md evidence found (phases 31–57 complete but no SUMMARY files)
- **DEFERRED** — Explicitly deferred in STATE.md Decisions or REQUIREMENTS.md

### INFRA Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| INFRA-01 | Minikube cluster initialized with 5 namespaces | Phase 2 | 02-01-SUMMARY.md, 02-02-SUMMARY.md | VERIFIED |
| INFRA-02 | K8s namespace YAML manifests | Phase 2 | 02-01-SUMMARY.md, 02-02-SUMMARY.md | VERIFIED |
| INFRA-03 | Base folder structure created | Phase 1 | 01-01-SUMMARY.md | VERIFIED |
| INFRA-04 | setup-minikube.sh script | Phase 2 | 02-01-SUMMARY.md | VERIFIED |
| INFRA-05 | deploy-all.sh orchestration script | Phase 2 | 02-01-SUMMARY.md | VERIFIED |
| INFRA-06 | docker-compose.yml for local dev | Phase 1 | 01-02-SUMMARY.md | VERIFIED |
| INFRA-07 | All services Dockerfiles with multi-stage builds | Phase 3/33 | No SUMMARY evidence (Phase 33 no SUMMARY) | ORPHANED |
| INFRA-08 | All configuration via env vars — zero hardcoded secrets | Phase 36 | No SUMMARY evidence (Phase 36 no SUMMARY) | ORPHANED |
| INFRA-09 | Structured JSON logging configured | Phase 1 | 01-03-SUMMARY.md | VERIFIED |

### API Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| API-01 | FastAPI app skeleton | Phase 3 | 03-01-SUMMARY.md | VERIFIED |
| API-02 | GET /health endpoint | Phase 3 | 03-01-SUMMARY.md | VERIFIED |
| API-03 | Dockerfile for FastAPI (multi-stage) | Phase 3 | 03-02-SUMMARY.md | VERIFIED |
| API-04 | K8s Deployment + Service YAML | Phase 3 | 03-02-SUMMARY.md | VERIFIED |
| API-05 | POST /ingest/intraday endpoint | Phase 7 | No SUMMARY (Phase 7 no SUMMARY file) | ORPHANED |
| API-06 | POST /ingest/historical endpoint | Phase 7 | No SUMMARY (Phase 7 no SUMMARY file) | ORPHANED |
| API-07 | GET /predict/{ticker} endpoint | Phase 23 | No SUMMARY (Phase 23 no SUMMARY file) | ORPHANED |
| API-08 | GET /predict/bulk endpoint | Phase 23 | No SUMMARY (Phase 23 no SUMMARY file) | ORPHANED |
| API-09 | GET /models/comparison endpoint | Phase 23 | No SUMMARY (Phase 23 no SUMMARY file) | ORPHANED |
| API-10 | GET /models/drift endpoint | Phase 23 | No SUMMARY (Phase 23 no SUMMARY file) | ORPHANED |
| API-11 | GET /market/overview endpoint | Phase 24 | No SUMMARY (Phase 24 no SUMMARY file) | ORPHANED |
| API-12 | GET /market/indicators/{ticker} endpoint | Phase 24 | No SUMMARY (Phase 24 no SUMMARY file) | ORPHANED |

### DB Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| DB-01 | PostgreSQL deployed in storage namespace | Phase 4 | 04-01-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |
| DB-02 | TimescaleDB extension enabled | Phase 4 | 04-01-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |
| DB-03 | init.sql with all table schemas | Phase 4 | 04-01-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |
| DB-04 | Composite primary keys | Phase 4 | 04-01-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |
| DB-05 | Indexes on ticker/date columns | Phase 4 | 04-01-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |
| DB-06 | Partitioning on date columns | Phase 4 | 04-01-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |
| DB-07 | K8s ConfigMap for PostgreSQL credentials | Phase 4 | 04-02-SUMMARY.md, 04-03-SUMMARY.md | VERIFIED |

### KAFKA Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| KAFKA-01 | Strimzi operator deployed | Phase 5 | 05-01-SUMMARY.md, 05-02-SUMMARY.md | VERIFIED |
| KAFKA-02 | Kafka broker with persistent storage | Phase 5 | 05-01-SUMMARY.md, 05-02-SUMMARY.md | VERIFIED |
| KAFKA-03 | intraday-data topic created | Phase 5 | 05-01-SUMMARY.md, 05-02-SUMMARY.md | VERIFIED |
| KAFKA-04 | historical-data topic created | Phase 5 | 05-01-SUMMARY.md, 05-02-SUMMARY.md | VERIFIED |
| KAFKA-05 | K8s manifests for Kafka/Strimzi | Phase 5 | 05-01-SUMMARY.md | VERIFIED |

### INGEST Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| INGEST-01 | yahoo_finance.py service | Phase 6 | 06-01-SUMMARY.md | VERIFIED |
| INGEST-02 | S&P 500 ticker list | Phase 6 | 06-01-SUMMARY.md | VERIFIED |
| INGEST-03 | kafka_producer.py | Phase 6 | 06-02-SUMMARY.md | VERIFIED |
| INGEST-04 | K8s CronJob intraday ingestion | Phase 8 | 08-01-SUMMARY.md | VERIFIED |
| INGEST-05 | K8s CronJob historical ingestion | Phase 8 | 08-01-SUMMARY.md | VERIFIED |
| INGEST-06 | Data validation and normalization | Phase 6 | 06-01-SUMMARY.md | VERIFIED |

### CONS Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| CONS-01 | Python Kafka consumer for intraday-data topic | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |
| CONS-02 | Python Kafka consumer for historical-data topic | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |
| CONS-03 | Micro-batch processing | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |
| CONS-04 | Idempotent upsert writes | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |
| CONS-05 | Retry logic with exponential backoff | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |
| CONS-06 | Dead-letter queue handling | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |
| CONS-07 | Dockerfile + K8s Deployment for consumer | Phase 9 | No SUMMARY (Phase 9 no SUMMARY file) | ORPHANED |

### FEAT Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FEAT-01 | RSI (14-period) computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-02 | MACD (12/26/9) computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-03 | Stochastic Oscillator computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-04 | SMA (20, 50, 200) computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-05 | EMA (12, 26) computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-06 | ADX computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-07 | Bollinger Bands computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-08 | ATR computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-09 | Rolling Volatility computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-10 | OBV computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-11 | VWAP computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-12 | Volume SMA computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-13 | Accumulation/Distribution computation | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-14 | Returns: 1d, 5d, 21d and log returns | Phase 10 | STATE.md Decisions (Phase 10 confirmed) | CHECKBOX-ONLY |
| FEAT-15 | Lag features: close price t-1 to t-21 | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |
| FEAT-16 | Rolling window stats over 5/10/21-day windows | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |
| FEAT-17 | StandardScaler pipeline variant | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |
| FEAT-18 | QuantileTransformer pipeline variant | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |
| FEAT-19 | MinMaxScaler pipeline variant | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |
| FEAT-20 | t+7 target label generation with no-leakage | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |
| FEAT-21 | Drop rows where target is unavailable | Phase 11 | STATE.md Decisions (Phase 11 confirmed) | CHECKBOX-ONLY |

### MODEL Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| MODEL-01 | LinearRegression training | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-02 | Ridge training with hyperparameter tuning | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-03 | Lasso training with hyperparameter tuning | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-04 | ElasticNet training with hyperparameter tuning | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-05 | BayesianRidge training | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-06 | HuberRegressor training | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-07 | RandomForestRegressor training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-08 | GradientBoostingRegressor training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-09 | HistGradientBoostingRegressor training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-10 | ExtraTreesRegressor training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-11 | DecisionTreeRegressor training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-12 | AdaBoostRegressor training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-13 | KNeighborsRegressor training | Phase 14 | No SUMMARY (Phase 14 no SUMMARY file) | ORPHANED |
| MODEL-14 | SVR (RBF kernel) training | Phase 14 | No SUMMARY (Phase 14 no SUMMARY file) | ORPHANED |
| MODEL-15 | MLPRegressor training | Phase 14 | No SUMMARY (Phase 14 no SUMMARY file) | ORPHANED |
| MODEL-16 | XGBoost training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-17 | LightGBM training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-18 | CatBoost training | Phase 13 | STATE.md Decisions (Phase 13 confirmed) | CHECKBOX-ONLY |
| MODEL-19 | TimeSeriesSplit CV with ≥5 folds | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-20 | RandomizedSearchCV or Optuna tuning | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |
| MODEL-21 | Hyperparameter search spaces per model family | Phase 12 | STATE.md Decisions (Phase 12 confirmed) | CHECKBOX-ONLY |

### EVAL Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| EVAL-01 | R² computed per model | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-02 | MAE computed per model | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-03 | RMSE computed per model | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-04 | MAPE computed per model | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-05 | Directional Accuracy computed | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-06 | Fold stability computed | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-07 | Models ranked by OOS RMSE | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-08 | High-variance models penalized | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-09 | ONE winner model selected | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-10 | Model artifact + metrics persisted to model_registry | Phase 15 | No SUMMARY (Phase 15 no SUMMARY file) | ORPHANED |
| EVAL-11 | SHAP values computed for top 5 models | Phase 16 | No SUMMARY (Phase 16 no SUMMARY file) | ORPHANED |
| EVAL-12 | SHAP feature importance stored for frontend | Phase 16 | No SUMMARY (Phase 16 no SUMMARY file) | ORPHANED |

### KF Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| KF-01 | Kubeflow Pipelines installed in ml namespace | Phase 17 | 17-01-SUMMARY.md | VERIFIED |
| KF-02 | data_loading component | Phase 17 | 17-01-SUMMARY.md | VERIFIED |
| KF-03 | feature_engineering component | Phase 17 | 17-02-SUMMARY.md | VERIFIED |
| KF-04 | label_generation component | Phase 17 | 17-02-SUMMARY.md | VERIFIED |
| KF-05 | train_models component | Phase 18 | 18-01-SUMMARY.md | VERIFIED |
| KF-06 | cross_validation component | Phase 18 | 18-02-SUMMARY.md | VERIFIED |
| KF-07 | evaluation component | Phase 18 | No SUMMARY evidence for KF-07 specifically | ORPHANED |
| KF-08 | model_comparison component | Phase 18 | No SUMMARY evidence for KF-08 specifically | ORPHANED |
| KF-09 | explainability component — SHAP | Phase 19 | 19-02-SUMMARY.md | VERIFIED |
| KF-10 | winner_selection component | Phase 19 | 19-02-SUMMARY.md | VERIFIED |
| KF-11 | model_persistence component | Phase 19 | 19-02-SUMMARY.md | VERIFIED |
| KF-12 | deployment component | Phase 19 | 19-01-SUMMARY.md, 19-02-SUMMARY.md | VERIFIED |
| KF-13 | Full pipeline definition (training_pipeline.py) | Phase 20 | 20-01-SUMMARY.md | VERIFIED |
| KF-14 | Pipeline is reproducible and versioned | Phase 20 | 20-01-SUMMARY.md | VERIFIED |
| KF-15 | Pipeline can be triggered manually or by drift | Phase 20 | 20-02-SUMMARY.md | VERIFIED |

### DRIFT Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| DRIFT-01 | Data drift detector (KS-test + PSI) | Phase 21 | 21-01-SUMMARY.md | VERIFIED |
| DRIFT-02 | Prediction drift detector | Phase 21 | 21-01-SUMMARY.md | VERIFIED |
| DRIFT-03 | Concept drift detector | Phase 21 | 21-01-SUMMARY.md | VERIFIED |
| DRIFT-04 | Daily drift check job | Phase 21 | 21-02-SUMMARY.md | VERIFIED |
| DRIFT-05 | Drift events logged to drift_logs table | Phase 21 | 21-02-SUMMARY.md | VERIFIED |
| DRIFT-06 | Auto-trigger Kubeflow retraining on drift | Phase 22 | 22-01-SUMMARY.md | VERIFIED |
| DRIFT-07 | Post-retrain: winner deployed, predictions regenerated | Phase 22 | 22-01-SUMMARY.md | VERIFIED |

### FE Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FE-01 | React app bootstrapped (Vite) | Phase 25 | No SUMMARY (Phase 25 no SUMMARY file) | ORPHANED |
| FE-02 | Dark theme (Bloomberg Terminal aesthetic) | Phase 25 | No SUMMARY (Phase 25 no SUMMARY file) | ORPHANED |
| FE-03 | Sidebar or top navigation | Phase 25 | No SUMMARY (Phase 25 no SUMMARY file) | ORPHANED |
| FE-04 | Responsive layout | Phase 25 | No SUMMARY (Phase 25 no SUMMARY file) | ORPHANED |
| FE-05 | API client layer (Zustand or React Query) | Phase 25 | No SUMMARY (Phase 25 no SUMMARY file) | ORPHANED |
| FE-06 | Dockerfile + K8s Deployment for frontend | Phase 25 | No SUMMARY (Phase 25 no SUMMARY file) | ORPHANED |

### FMOD Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FMOD-01 | Sortable, filterable model table | Phase 26 | No SUMMARY (Phase 26 no SUMMARY file) | ORPHANED |
| FMOD-02 | In-sample vs OOS metrics side-by-side | Phase 26 | No SUMMARY (Phase 26 no SUMMARY file) | ORPHANED |
| FMOD-03 | Winner model highlighted | Phase 26 | No SUMMARY (Phase 26 no SUMMARY file) | ORPHANED |
| FMOD-04 | SHAP feature importance bar charts | Phase 26 | No SUMMARY (Phase 26 no SUMMARY file) | ORPHANED |
| FMOD-05 | SHAP beeswarm plots | Phase 26 | No SUMMARY (Phase 26 no SUMMARY file) | ORPHANED |
| FMOD-06 | Fold-by-fold performance charts per model | Phase 26 | No SUMMARY (Phase 26 no SUMMARY file) | ORPHANED |

### FFOR Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FFOR-01 | Forecast table for S&P 500 stocks | Phase 27 | No SUMMARY (Phase 27 no SUMMARY file) | ORPHANED |
| FFOR-02 | Filter by sector, return range, confidence | Phase 27 | No SUMMARY (Phase 27 no SUMMARY file) | ORPHANED |
| FFOR-03 | Multi-stock comparison view | Phase 27 | No SUMMARY (Phase 27 no SUMMARY file) | ORPHANED |
| FFOR-04 | Per-stock detail view with charts | Phase 27 | No SUMMARY (Phase 27 no SUMMARY file) | ORPHANED |
| FFOR-05 | Technical indicators overlay | Phase 27 | No SUMMARY (Phase 27 no SUMMARY file) | ORPHANED |
| FFOR-06 | SHAP explanation panel per stock | Phase 27 | No SUMMARY (Phase 27 no SUMMARY file) | ORPHANED |

### FDASH Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FDASH-01 | S&P 500 treemap by market cap | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-02 | Treemap cells clickable | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-03 | Dynamic dropdown to select stocks | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-04 | Intraday candlestick/line chart | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-05 | Historical OHLCV chart | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-06 | TA panel: RSI, MACD, Bollinger Bands | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-07 | Volume bars and VWAP overlay | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |
| FDASH-08 | Key metric cards | Phase 28 | No SUMMARY (Phase 28 no SUMMARY file) | ORPHANED |

### FDRFT Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FDRFT-01 | Active model info card | Phase 29 | No SUMMARY (Phase 29 no SUMMARY file) | ORPHANED |
| FDRFT-02 | Rolling performance chart | Phase 29 | No SUMMARY (Phase 29 no SUMMARY file) | ORPHANED |
| FDRFT-03 | Drift alert timeline | Phase 29 | No SUMMARY (Phase 29 no SUMMARY file) | ORPHANED |
| FDRFT-04 | Retraining status panel | Phase 29 | No SUMMARY (Phase 29 no SUMMARY file) | ORPHANED |
| FDRFT-05 | Feature distribution charts | Phase 29 | No SUMMARY (Phase 29 no SUMMARY file) | ORPHANED |

### TEST Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| TEST-01 | E2E: ingest → Kafka → PostgreSQL | Phase 30 | No SUMMARY (Phase 30 no SUMMARY file) | ORPHANED |
| TEST-02 | E2E: PostgreSQL → Kubeflow → model registry → serving | Phase 30 | No SUMMARY (Phase 30 no SUMMARY file) | ORPHANED |
| TEST-03 | E2E: FastAPI prediction → frontend | Phase 30 | No SUMMARY (Phase 30 no SUMMARY file) | ORPHANED |
| TEST-04 | Drift detection → retrain → redeploy cycle | Phase 30 | No SUMMARY (Phase 30 no SUMMARY file) | ORPHANED |
| TEST-05 | seed-data.sh script | Phase 30 | No SUMMARY (Phase 30 no SUMMARY file) | ORPHANED |

### LIVE Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| LIVE-01 | GET /predict/{ticker} live inference | Phase 31 | No SUMMARY (Phase 31 no SUMMARY file) | ORPHANED |
| LIVE-02 | GET /predict/bulk live inference | Phase 31 | No SUMMARY (Phase 31 no SUMMARY file) | ORPHANED |
| LIVE-03 | GET /models/comparison queries model_registry | Phase 31 | No SUMMARY (Phase 31 no SUMMARY file) | ORPHANED |
| LIVE-04 | GET /models/drift queries drift_logs | Phase 31 | No SUMMARY (Phase 31 no SUMMARY file) | ORPHANED |
| LIVE-05 | Graceful fallback to cached responses | Phase 31 | No SUMMARY (Phase 31 no SUMMARY file) | ORPHANED |
| LIVE-06 | Frontend loading spinner during API fetch | Phase 32 | No SUMMARY (Phase 32 no SUMMARY file) | ORPHANED |
| LIVE-07 | Frontend uses API as primary data source | Phase 32 | No SUMMARY (Phase 32 no SUMMARY file) | ORPHANED |
| LIVE-08 | /models/drift/rolling-performance + /models/retrain-status | Phase 32 | No SUMMARY (Phase 32 no SUMMARY file) | ORPHANED |
| LIVE-09 | Drift page powered by live API data | Phase 32 | No SUMMARY (Phase 32 no SUMMARY file) | ORPHANED |

### DEPLOY Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| DEPLOY-01 | ML pipeline Dockerfile | Phase 33 | No SUMMARY (Phase 33 no SUMMARY file) | ORPHANED |
| DEPLOY-02 | K8s ConfigMap for ML namespace | Phase 33 | No SUMMARY (Phase 33 no SUMMARY file) | ORPHANED |
| DEPLOY-03 | K8s CronJob weekly model retraining | Phase 34 | No SUMMARY (Phase 34 no SUMMARY file) | ORPHANED |
| DEPLOY-04 | K8s CronJob daily drift detection | Phase 34 | No SUMMARY (Phase 34 no SUMMARY file) | ORPHANED |
| DEPLOY-05 | PersistentVolumeClaim for model artifacts | Phase 34 | No SUMMARY (Phase 34 no SUMMARY file) | ORPHANED |
| DEPLOY-06 | model-serving Deployment uses PVC | Phase 34 | No SUMMARY (Phase 34 no SUMMARY file) | ORPHANED |
| DEPLOY-07 | deploy-all.sh phases 17–25 active | Phase 34 | No SUMMARY (Phase 34 no SUMMARY file) | ORPHANED |
| DEPLOY-08 | ml/drift/trigger.py CLI entry point | Phase 34 | No SUMMARY (Phase 34 no SUMMARY file) | ORPHANED |

### MON Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| MON-01 | FastAPI /metrics endpoint | Phase 37 | 37-01-SUMMARY.md | VERIFIED |
| MON-02 | Custom Prometheus metrics (prediction, latency, errors) | Phase 37 | 37-01-SUMMARY.md | VERIFIED |
| MON-03 | Kafka consumer /metrics on port 9090 | Phase 37 | 37-02-SUMMARY.md | VERIFIED |
| MON-04 | Prometheus server deployed | Phase 38 | 38-01-SUMMARY.md, 72-01-SUMMARY.md | VERIFIED |
| MON-05 | Grafana deployed with datasources and dashboards | Phase 38 | 38-01-SUMMARY.md, 72-01-SUMMARY.md, 72-02-SUMMARY.md | VERIFIED |
| MON-06 | API Health dashboard | Phase 38 | 38-02-SUMMARY.md, 72-01-SUMMARY.md, 72-02-SUMMARY.md | VERIFIED |
| MON-07 | ML Performance dashboard | Phase 38 | 38-02-SUMMARY.md, 72-02-SUMMARY.md | VERIFIED |
| MON-08 | Alert rules: drift severity, API error rate, Kafka lag | Phase 38 | 38-03-SUMMARY.md | VERIFIED |
| MON-09 | structlog JSON output for FastAPI and Kafka consumer | Phase 39 | No SUMMARY (Phase 39 no SUMMARY file) | ORPHANED |
| MON-10 | Centralized log aggregation via Loki + Promtail | Phase 39 | No SUMMARY (Phase 39 no SUMMARY file) | ORPHANED |

### DBHARD Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| DBHARD-01 | Alembic configured | Phase 35 | No SUMMARY (Phase 35 no SUMMARY file) | ORPHANED |
| DBHARD-02 | Initial Alembic migration | Phase 35 | No SUMMARY (Phase 35 no SUMMARY file) | ORPHANED |
| DBHARD-03 | API Dockerfile runs alembic upgrade head | Phase 35 | No SUMMARY (Phase 35 no SUMMARY file) | ORPHANED |
| DBHARD-04 | SQLAlchemy async engine with connection pooling | Phase 40 | No SUMMARY (Phase 40 no SUMMARY file) | ORPHANED |
| DBHARD-05 | market_service.py migrated to SQLAlchemy async | Phase 40 | No SUMMARY (Phase 40 no SUMMARY file) | ORPHANED |
| DBHARD-06 | K8s Secrets replace hardcoded credentials | Phase 36 | No SUMMARY (Phase 36 no SUMMARY file) | ORPHANED |
| DBHARD-07 | Database RBAC roles | Phase 36 | No SUMMARY (Phase 36 no SUMMARY file) | ORPHANED |
| DBHARD-08 | Daily pg_dump backup CronJob | Phase 41 | No SUMMARY (Phase 41 no SUMMARY file) | ORPHANED |

### ADVML Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| ADVML-01 | StackingRegressor ensemble | Phase 42 | No SUMMARY (Phase 42 no SUMMARY file) | ORPHANED |
| ADVML-02 | Ensemble integrated into training_pipeline.py | Phase 42 | No SUMMARY (Phase 42 no SUMMARY file) | ORPHANED |
| ADVML-03 | Multi-horizon target generation (1d, 7d, 30d) | Phase 43 | No SUMMARY (Phase 43 no SUMMARY file) | ORPHANED |
| ADVML-04 | Separate model suite per prediction horizon | Phase 43 | No SUMMARY (Phase 43 no SUMMARY file) | ORPHANED |
| ADVML-05 | GET /predict/{ticker}?horizon=1|7|30 | Phase 43 | No SUMMARY (Phase 43 no SUMMARY file) | ORPHANED |
| ADVML-06 | Frontend horizon toggle (1D/7D/30D) | Phase 43 | No SUMMARY (Phase 43 no SUMMARY file) | ORPHANED |
| ADVML-07 | feature_store PostgreSQL table with daily CronJob | Phase 44 | No SUMMARY (Phase 44 no SUMMARY file) | ORPHANED |
| ADVML-08 | Training pipeline reads from feature store | Phase 44 | No SUMMARY (Phase 44 no SUMMARY file) | ORPHANED |

### FENH Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FENH-01 | WebSocket /ws/prices pushing price updates | Phase 45 | No SUMMARY (Phase 45 no SUMMARY file) | ORPHANED |
| FENH-02 | useWebSocket.ts custom React hook | Phase 45 | No SUMMARY (Phase 45 no SUMMARY file) | ORPHANED |
| FENH-03 | Dashboard CandlestickChart live updates via WebSocket | Phase 45 | No SUMMARY (Phase 45 no SUMMARY file) | ORPHANED |
| FENH-04 | GET /backtest/{ticker} endpoint | Phase 46 | No SUMMARY (Phase 46 no SUMMARY file) | ORPHANED |
| FENH-05 | Backtest.tsx page with dual-line chart | Phase 46 | No SUMMARY (Phase 46 no SUMMARY file) | ORPHANED |
| FENH-06 | CSV and PDF export buttons | Phase 50 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |
| FENH-07 | Mobile responsive layout | Phase 50 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |

### PROD Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| PROD-01 | Redis deployed in storage namespace | Phase 47 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |
| PROD-02 | API response caching with configurable TTL | Phase 47 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |
| PROD-03 | Cache invalidation on model retrain | Phase 47 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |
| PROD-04 | API rate limiting via slowapi | Phase 48 | No SUMMARY (Phase 48 no SUMMARY file) | ORPHANED |
| PROD-05 | Deep health checks | Phase 48 | No SUMMARY (Phase 48 no SUMMARY file) | ORPHANED |
| PROD-06 | A/B model testing with traffic_weight field | Phase 49 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |
| PROD-07 | ab_test_assignments table | Phase 49 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |
| PROD-08 | GET /models/ab-results endpoint | Phase 49 | REQUIREMENTS.md checkbox [x] | CHECKBOX-ONLY |

### OBJST Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| OBJST-01 | MinIO deployed in storage namespace | Phase 51 | No SUMMARY (Phase 51 no SUMMARY file) | ORPHANED |
| OBJST-02 | S3 buckets created: model-artifacts, drift-logs | Phase 51 | No SUMMARY (Phase 51 no SUMMARY file) | ORPHANED |
| OBJST-03 | K8s Secret for MinIO root credentials | Phase 51 | No SUMMARY (Phase 51 no SUMMARY file) | ORPHANED |
| OBJST-04 | K8s ConfigMap with MINIO_ENDPOINT | Phase 51 | No SUMMARY (Phase 51 no SUMMARY file) | ORPHANED |
| OBJST-05 | boto3 or minio SDK added to requirements.txt | Phase 52 | No SUMMARY (Phase 52 no SUMMARY file) | ORPHANED |
| OBJST-06 | ModelRegistry save/load via S3-compatible API | Phase 52 | No SUMMARY (Phase 52 no SUMMARY file) | ORPHANED |
| OBJST-07 | Model artifacts stored at s3://model-artifacts/ | Phase 52 | No SUMMARY (Phase 52 no SUMMARY file) | ORPHANED |
| OBJST-08 | STORAGE_BACKEND env var toggle | Phase 52 | No SUMMARY (Phase 52 no SUMMARY file) | ORPHANED |
| OBJST-09 | Training pipeline persists artifacts to MinIO | Phase 53 | No SUMMARY (Phase 53 no SUMMARY file) | ORPHANED |
| OBJST-10 | Deployer uploads winner model to MinIO serving | Phase 53 | No SUMMARY (Phase 53 no SUMMARY file) | ORPHANED |
| OBJST-11 | Drift pipeline reads/writes from MinIO | Phase 53 | No SUMMARY (Phase 53 no SUMMARY file) | ORPHANED |
| OBJST-12 | K8s CronJobs use MinIO env vars | Phase 53 | No SUMMARY (Phase 53 no SUMMARY file) | ORPHANED |

### KSERV Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| KSERV-01 | KServe controller deployed | Phase 54 | No SUMMARY (Phase 54 no SUMMARY file) | ORPHANED |
| KSERV-02 | KServe CRDs installed | Phase 54 | No SUMMARY (Phase 54 no SUMMARY file) | ORPHANED |
| KSERV-03 | KServe configured with S3 credentials for MinIO | Phase 54 | No SUMMARY (Phase 54 no SUMMARY file) | ORPHANED |
| KSERV-04 | ClusterServingRuntime for sklearn deployed | Phase 54 | No SUMMARY (Phase 54 no SUMMARY file) | ORPHANED |
| KSERV-05 | InferenceService CR pointing to MinIO serving | Phase 55 | No SUMMARY (Phase 55 no SUMMARY file) | ORPHANED |
| KSERV-06 | KServe predictor downloads model from MinIO | Phase 55 | No SUMMARY (Phase 55 no SUMMARY file) | ORPHANED |
| KSERV-07 | V2 inference protocol endpoint operational | Phase 55 | No SUMMARY (Phase 55 no SUMMARY file) | ORPHANED |
| KSERV-08 | Autoscaling configured (scale-to-zero) | Phase 55 | No SUMMARY (Phase 55 no SUMMARY file) | ORPHANED |
| KSERV-09 | prediction_service.py calls KServe V2 | Phase 56 | No SUMMARY (Phase 56 no SUMMARY file) | ORPHANED |
| KSERV-10 | KSERVE_INFERENCE_URL configurable via ConfigMap | Phase 56 | No SUMMARY (Phase 56 no SUMMARY file) | ORPHANED |
| KSERV-11 | Prediction API response backward-compatible | Phase 56 | No SUMMARY (Phase 56 no SUMMARY file) | ORPHANED |
| KSERV-12 | A/B testing uses KServe canary traffic splitting | Phase 56 | No SUMMARY (Phase 56 no SUMMARY file) | ORPHANED |
| KSERV-13 | Legacy model-serving.yaml removed | Phase 57 | No SUMMARY (Phase 57 no SUMMARY file) | ORPHANED |
| KSERV-14 | deploy-all.sh updated with MinIO + KServe steps | Phase 57 | No SUMMARY (Phase 57 no SUMMARY file) | ORPHANED |
| KSERV-15 | E2E flow validated: train → MinIO → KServe → predict → drift | Phase 57/59 | 59-01,02,03,04-SUMMARY.md | VERIFIED |

### PRED-MNAME Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| PRED-MNAME-01 | model_name not 'unknown' in predict response | Phase 60 | 60-01-SUMMARY.md, 60-02-SUMMARY.md | VERIFIED |
| PRED-MNAME-02 | boto3 async thread pool for MinIO fetch | Phase 60 | 60-01-SUMMARY.md | VERIFIED |
| PRED-MNAME-03 | serving_config.json read at lifespan startup | Phase 60 | 60-01-SUMMARY.md | VERIFIED |
| PRED-MNAME-04 | MinIO env vars injected via ConfigMap+Secret | Phase 60 | 60-01-SUMMARY.md, 60-02-SUMMARY.md | VERIFIED |
| PRED-MNAME-05 | Graceful degradation when MinIO unavailable | Phase 60 | 60-01-SUMMARY.md | VERIFIED |

### TEST-PW Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| TEST-PW-01 | Playwright E2E — Dashboard page | Phase 61 | 61-01-SUMMARY.md | VERIFIED |
| TEST-PW-02 | Playwright E2E — Forecasts page | Phase 61 | 61-02-SUMMARY.md | VERIFIED |
| TEST-PW-03 | Playwright E2E — Models page | Phase 61 | 61-03-SUMMARY.md | VERIFIED |
| TEST-PW-04 | Playwright E2E — Drift page | Phase 61 | 61-04-SUMMARY.md | VERIFIED |
| TEST-PW-05 | Playwright E2E — Backtest page | Phase 61 | 61-05-SUMMARY.md | VERIFIED |

### TEST-INFRA Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| TEST-INFRA-01 | Playwright E2E — Grafana | Phase 62 | 62-01-SUMMARY.md, 62-02-SUMMARY.md | VERIFIED |
| TEST-INFRA-02 | Playwright E2E — Prometheus | Phase 62 | 62-01-SUMMARY.md, 62-03-SUMMARY.md | VERIFIED |
| TEST-INFRA-03 | Playwright E2E — MinIO | Phase 62 | 62-01-SUMMARY.md, 62-04-SUMMARY.md | VERIFIED |
| TEST-INFRA-04 | Playwright E2E — Kubeflow | Phase 62 | 62-01-SUMMARY.md, 62-05-SUMMARY.md | VERIFIED |
| TEST-INFRA-05 | Playwright E2E — K8s Dashboard | Phase 62 | 62-01-SUMMARY.md, 62-05-SUMMARY.md | VERIFIED |

### TEST-E2E Requirements

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| TEST-E2E-01 | Real API data guards in all spec beforeAll blocks | Phase 63 | 63-01-SUMMARY.md (requirements: []) | ORPHANED |

### v3.0 New Requirement Domains (added during Phases 64–72 execution)

These requirement IDs were assigned during execution and do not appear in REQUIREMENTS.md v1/v1.1 sections.

#### TSDB Requirements (Phase 64)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| TSDB-01 | Continuous aggregate ohlcv_daily_agg | Phase 64 | 64-01-SUMMARY.md | VERIFIED |
| TSDB-02 | Continuous aggregate ohlcv_intraday_agg | Phase 64 | 64-01-SUMMARY.md | VERIFIED |
| TSDB-03 | TimescaleDB compression policy | Phase 64 | 64-01-SUMMARY.md | VERIFIED |
| TSDB-04 | Candle API endpoint using continuous aggregates | Phase 64 | 64-01-SUMMARY.md | VERIFIED |
| TSDB-05 | Retention policy | Phase 64 | 64-01-SUMMARY.md | VERIFIED |
| TSDB-06 | Grafana TimescaleDB datasource | Phase 64 | 64-02-SUMMARY.md | VERIFIED |

#### GITOPS Requirements (Phase 65)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| GITOPS-01 | Argo CD installed | Phase 65 | 65-01-SUMMARY.md | VERIFIED |
| GITOPS-02 | App-of-Apps pattern | Phase 65 | 65-01-SUMMARY.md | VERIFIED |
| GITOPS-03 | All platform namespaces managed by Argo CD | Phase 65 | 65-01-SUMMARY.md | VERIFIED |
| GITOPS-04 | Lua health checks for Strimzi/KServe | Phase 65 | 65-02-SUMMARY.md | VERIFIED |
| GITOPS-05 | validate-argocd.sh passes 32 checks | Phase 65 | 65-02-SUMMARY.md | VERIFIED |

#### FEAST Requirements (Phase 66)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FEAST-01 | Feast feature definitions | Phase 66 | 66-01-SUMMARY.md | VERIFIED |
| FEAST-02 | Feast offline store (PostgreSQL) | Phase 66 | 66-01-SUMMARY.md | VERIFIED |
| FEAST-03 | Feast online store (Redis) | Phase 66 | 66-01-SUMMARY.md | VERIFIED |
| FEAST-04 | Historical feature retrieval for training | Phase 66 | 66-01-SUMMARY.md | VERIFIED |
| FEAST-05 | Online feature serving integration | Phase 66 | 66-01-SUMMARY.md | VERIFIED |
| FEAST-06 | Feast feature server deployment (K8s) | Phase 66 | 66-02-SUMMARY.md | VERIFIED |
| FEAST-07 | Feast materialize CronJob | Phase 66 | 66-03-SUMMARY.md | VERIFIED |
| FEAST-08 | Prediction service uses Feast online features | Phase 66 | 66-03-SUMMARY.md | VERIFIED |

#### FLINK Requirements (Phase 67)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| FLINK-01 | Flink operator installed (Helm) | Phase 67 | 67-01-SUMMARY.md | VERIFIED |
| FLINK-02 | ohlcv-normalizer FlinkDeployment | Phase 67 | 67-01-SUMMARY.md | VERIFIED |
| FLINK-03 | indicator-stream FlinkDeployment | Phase 67 | 67-02-SUMMARY.md | VERIFIED |
| FLINK-04 | feast-writer FlinkDeployment | Phase 67 | 67-02-SUMMARY.md | VERIFIED |
| FLINK-05 | processed-features Kafka topic | Phase 67 | 67-01-SUMMARY.md | VERIFIED |
| FLINK-06 | Flink checkpoints in MinIO | Phase 67 | 67-02-SUMMARY.md, 67-03-SUMMARY.md | VERIFIED |
| FLINK-07 | Flink jobs visible in Flink Web UI | Phase 67 | 67-02-SUMMARY.md, 67-03-SUMMARY.md | VERIFIED |
| FLINK-08 | JDBC upsert sink to PostgreSQL | Phase 67 | 67-03-SUMMARY.md | VERIFIED |

#### V3INT Requirements (Phase 68)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| V3INT-01 | TimescaleDB OLAP integration test | Phase 68 | 68-01-SUMMARY.md | VERIFIED |
| V3INT-02 | Argo CD integration test | Phase 68 | 68-01-SUMMARY.md | VERIFIED |
| V3INT-03 | Feast feature retrieval integration test | Phase 68 | 68-01-SUMMARY.md | VERIFIED |
| V3INT-04 | Flink streaming integration test | Phase 68 | 68-01-SUMMARY.md | VERIFIED |
| V3INT-05 | updated_at 30-second freshness check | Phase 68 | 68-01-SUMMARY.md | VERIFIED |

#### UI-RT Requirements (Phase 69)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| UI-RT-01 | /analytics page with 5 panels | Phase 69 | 69-02-SUMMARY.md | VERIFIED |
| UI-RT-02 | StreamHealthPanel | Phase 69 | 69-02-SUMMARY.md | VERIFIED |
| UI-RT-03 | FeatureFreshnessPanel | Phase 69 | 69-02-SUMMARY.md | VERIFIED |
| UI-RT-04 | OLAPCandleChart | Phase 69 | 69-02-SUMMARY.md | VERIFIED |
| UI-RT-05 | StreamLagMonitor | Phase 69 | 69-02-SUMMARY.md | VERIFIED |
| UI-RT-06 | SystemHealthSummary panel | Phase 69 | 69-02-SUMMARY.md | VERIFIED |
| UI-RT-07 | 3 new API endpoints backing /analytics | Phase 69 | 69-02-SUMMARY.md | VERIFIED |

#### ALT Requirements (Phase 71)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| ALT-01 | Reddit PRAW producer service | Phase 71 | 71-01-SUMMARY.md | VERIFIED |
| ALT-02 | reddit-raw Kafka topic | Phase 71 | 71-01-SUMMARY.md | VERIFIED |
| ALT-03 | reddit-secrets K8s Secret | Phase 71 | 71-01-SUMMARY.md | VERIFIED |
| ALT-04 | sentiment-stream FlinkDeployment | Phase 71 | 71-02-SUMMARY.md | VERIFIED |
| ALT-05 | VADER sentiment scoring | Phase 71 | 71-02-SUMMARY.md | VERIFIED |
| ALT-06 | sentiment-aggregated Kafka topic | Phase 71 | 71-02-SUMMARY.md | VERIFIED |
| ALT-07 | sentiment-writer FlinkDeployment → Feast | Phase 71 | 71-03-SUMMARY.md | VERIFIED |
| ALT-08 | Feast sentiment features online store | Phase 71 | 71-03-SUMMARY.md | VERIFIED |
| ALT-09 | /ws/sentiment/{ticker} WebSocket endpoint | Phase 71 | 71-04-SUMMARY.md | VERIFIED |
| ALT-10 | useSentimentSocket React hook + UI panel | Phase 71 | 71-04-SUMMARY.md | VERIFIED |

#### TBD Requirements (Phase 70 — placeholder IDs)

| REQ-ID | Description | Assigned Phase | SUMMARY Evidence | Status |
|--------|-------------|----------------|-----------------|--------|
| TBD-01 | GET /market/streaming-features/{ticker} endpoint | Phase 70 | 70-01-SUMMARY.md | VERIFIED |
| TBD-02 | StreamingFeaturesPanel React component | Phase 70 | 70-02-SUMMARY.md | VERIFIED |
| TBD-03 | Dashboard Drawer accordion integration | Phase 70 | 70-02-SUMMARY.md | VERIFIED |
| TBD-04 | Feast Redis online store integration | Phase 70 | 70-02-SUMMARY.md | VERIFIED |
| TBD-05 | Graceful Feast unavailability fallback | Phase 70 | 70-02-SUMMARY.md | VERIFIED |

---

## Orphaned Requirements

These REQ-IDs have no requirements-completed evidence in any SUMMARY.md frontmatter. They are NOT confirmed as unimplemented — phases 7–16, 23–57 are all marked Complete in STATE.md. The absence of SUMMARY.md files is a documentation gap, not necessarily an implementation gap. Domain auditors (Wave 2) will inspect actual code to classify as CRITICAL gap or false-positive.

| REQ-ID | Group | Assigned Phase | Gap Type |
|--------|-------|----------------|----------|
| INFRA-07 | INFRA | Phase 3/33 | ORPHANED — no SUMMARY.md evidence |
| INFRA-08 | INFRA | Phase 36 | ORPHANED — no SUMMARY.md evidence |
| API-05 | API | Phase 7 | ORPHANED — no SUMMARY.md evidence |
| API-06 | API | Phase 7 | ORPHANED — no SUMMARY.md evidence |
| API-07 | API | Phase 23 | ORPHANED — no SUMMARY.md evidence |
| API-08 | API | Phase 23 | ORPHANED — no SUMMARY.md evidence |
| API-09 | API | Phase 23 | ORPHANED — no SUMMARY.md evidence |
| API-10 | API | Phase 23 | ORPHANED — no SUMMARY.md evidence |
| API-11 | API | Phase 24 | ORPHANED — no SUMMARY.md evidence |
| API-12 | API | Phase 24 | ORPHANED — no SUMMARY.md evidence |
| CONS-01 through CONS-07 | CONS | Phase 9 | ORPHANED — no SUMMARY.md evidence |
| EVAL-01 through EVAL-12 | EVAL | Phase 15-16 | ORPHANED — no SUMMARY.md evidence |
| KF-07, KF-08 | KF | Phase 18 | ORPHANED — no SUMMARY.md evidence for these IDs specifically |
| MODEL-13, MODEL-14, MODEL-15 | MODEL | Phase 14 | ORPHANED — no SUMMARY.md evidence |
| FE-01 through FE-06 | FE | Phase 25 | ORPHANED — no SUMMARY.md evidence |
| FMOD-01 through FMOD-06 | FMOD | Phase 26 | ORPHANED — no SUMMARY.md evidence |
| FFOR-01 through FFOR-06 | FFOR | Phase 27 | ORPHANED — no SUMMARY.md evidence |
| FDASH-01 through FDASH-08 | FDASH | Phase 28 | ORPHANED — no SUMMARY.md evidence |
| FDRFT-01 through FDRFT-05 | FDRFT | Phase 29 | ORPHANED — no SUMMARY.md evidence |
| TEST-01 through TEST-05 | TEST | Phase 30 | ORPHANED — no SUMMARY.md evidence |
| LIVE-01 through LIVE-09 | LIVE | Phase 31-32 | ORPHANED — no SUMMARY.md evidence |
| DEPLOY-01 through DEPLOY-08 | DEPLOY | Phase 33-34 | ORPHANED — no SUMMARY.md evidence |
| MON-09, MON-10 | MON | Phase 39 | ORPHANED — no SUMMARY.md evidence |
| DBHARD-01 through DBHARD-08 | DBHARD | Phase 35-36, 40-41 | ORPHANED — no SUMMARY.md evidence |
| ADVML-01 through ADVML-08 | ADVML | Phase 42-44 | ORPHANED — no SUMMARY.md evidence |
| FENH-01 through FENH-05 | FENH | Phase 45-46 | ORPHANED — no SUMMARY.md evidence |
| PROD-04, PROD-05 | PROD | Phase 48 | ORPHANED — no SUMMARY.md evidence |
| OBJST-01 through OBJST-12 | OBJST | Phase 51-53 | ORPHANED — no SUMMARY.md evidence |
| KSERV-01 through KSERV-14 | KSERV | Phase 54-57 | ORPHANED — no SUMMARY.md evidence |
| TEST-E2E-01 | TEST-E2E | Phase 63 | ORPHANED — SUMMARY.md shows requirements: [] |

Note: REQUIREMENTS.md checkboxes are NOT reliable ground truth (known to be inconsistently updated). An orphaned REQ-ID is NOT confirmed as unimplemented. Domain auditors (Wave 2) will inspect actual code to classify as CRITICAL gap or false-positive.

---

## Tech Debt Register

Items explicitly deferred in STATE.md Decisions or mentioned as deferred in REQUIREMENTS.md. These are NOT gaps — they were intentional deferrals.

| Item | Deferred In | Phase | Notes |
|------|-------------|-------|-------|
| @dsl.component wrapping for KFP components | Phase 17 decisions | 17 | Components are pure Python functions; @dsl.component wrapping deferred to Phase 20 |
| Parquet serialization for inter-component transfer | Phase 17 decisions | 17 | Data passes in-process; Parquet deferred to Phase 20. Phase 20 added Parquet via pyarrow for KFP mode |
| User auth, watchlists, alerts | Phase 31–50 Planning | 31–50 | Deferred to v2 — plain K8s CronJobs for ML training/drift, KFP containerization deferred |
| Sentiment data | Phase 31–50 Planning | 31–50 | Deferred to v2 in original plan — later implemented in Phase 71 |
| Sector models | v2 Requirements | — | Sector-level model training (separate model suites per GICS sector) deferred to v2 |
| Portfolio optimization | v2 Requirements | — | Markowitz mean-variance, risk-parity deferred to v2 |
| Deep learning models (LSTM, Transformer) | v2 Requirements | — | Deferred to v2 |
| KFP containerized pipeline components | v2 Requirements / Phase 17-18 | 17–18 | Replace plain K8s CronJobs — deferred to v2 |
| Live trading / order execution | v2 Requirements | — | Prediction platform only, no brokerage integration |
| Cloud deployment (AWS/GCP/Azure) | Out of Scope | — | Minikube local only for v1 |
| Canary deployment with Istio | v2 Requirements | — | KServe uses percentTraffic for A/B, Istio canary deferred |
| Argo CD GitOps K8s Secret provisioning for Grafana | Phase 64 decisions | 64 | Grafana TimescaleDB password env var substitution; K8s Secret provisioning deferred to Phase 65 GitOps |
| OLAPCandleChart 5m/4h timeframes | Phase 69 decisions | 69 | Phase 64 created only 1h/1d TimescaleDB continuous aggregates; 5m/4h deferred |

---

## Cross-Phase E2E Data Flow Chains

Status for each chain: DOCUMENTED (coordinator traced the path) — domain auditors will verify each link exists in code.

### Chain 1: Ingest Chain

Yahoo Finance → `services/api/app/services/yahoo_finance.py` → `services/api/app/services/kafka_producer.py` → `intraday-data` Kafka topic → `services/kafka-consumer/` → `ohlcv_intraday` PostgreSQL table

**Audited by:** Domain 1 (FastAPI API), Domain 3 (Kafka/Flink)

### Chain 2: ML Training Chain

`ohlcv_daily` PostgreSQL table → Kubeflow pipeline (`ml/pipelines/training_pipeline.py`) → model registry (`ml/evaluation/`) → KServe InferenceService (`k8s/ml/inferenceservice.yaml`) → `/predict/{ticker}` API endpoint

**Audited by:** Domain 2 (ML Pipeline), Domain 1 (FastAPI API), Domain 6 (Infrastructure)

### Chain 3: Drift Chain

Drift check CronJob (`k8s/ml/`) → `drift_logs` table → auto-trigger → Kubeflow retrain → new winner deployed via KServe

**Audited by:** Domain 2 (ML Pipeline), Domain 6 (Infrastructure)

### Chain 4: Flink Streaming Chain

`ohlcv_intraday` table → `ohlcv-normalizer` FlinkDeployment → `indicator-stream` FlinkDeployment → Feast Redis online store → `/market/streaming-features/{ticker}` API endpoint

**Audited by:** Domain 3 (Kafka/Flink), Domain 1 (FastAPI API), Domain 6 (Infrastructure)

### Chain 5: Sentiment Chain

Reddit PRAW producer (`services/reddit-producer/`) → `reddit-raw` Kafka topic → `sentiment-stream` FlinkDeployment → `sentiment-aggregated` Kafka topic → `sentiment-writer` FlinkDeployment → Feast Redis → `/ws/sentiment/{ticker}` WebSocket

**Audited by:** Domain 3 (Kafka/Flink), Domain 1 (FastAPI API)

### Chain 6: Frontend Consumption Chain

React app → FastAPI API → all chains above (dashboard polls REST + WebSocket endpoints)

**Audited by:** Domain 4 (Frontend), Domain 1 (FastAPI API)

---

## Domain Audit Reports

*These sections are populated by Wave 2 plans (73-02 through 73-07). Each domain auditor appends its structured gap report into the matching section below.*

### Domain 1: FastAPI API Layer

**Audited by:** Plan 73-02
**Requirements scope:** API-01–12, LIVE-01–09, FENH-01–05, PROD-04–08

```
[PENDING — Plan 73-02 populates this section]
```

---

### Domain 2: ML Pipeline

**Audited by:** Plan 73-03
**Requirements scope:** FEAT-01–21, MODEL-01–21, EVAL-01–12, KF-01–15, DRIFT-01–07, ADVML-01–08

```
[PENDING — Plan 73-03 populates this section]
```

---

### Domain 3: Kafka / Flink / Streaming

**Audited by:** Plan 73-04
**Requirements scope:** KAFKA-01–05, CONS-01–07, Phase 67 (Flink), Phase 71 (Reddit/sentiment)

```
[PENDING — Plan 73-04 populates this section]
```

---

### Domain 4: Frontend

**Audited by:** Plan 73-05
**Requirements scope:** FE-01–06, FMOD-01–06, FFOR-01–06, FDASH-01–08, FDRFT-01–05, FENH-03–07

```
[PENDING — Plan 73-05 populates this section]
```

---

### Domain 5: Observability

**Audited by:** Plan 73-06
**Requirements scope:** MON-01–10

```
[PENDING — Plan 73-06 populates this section]
```

---

### Domain 6: Infrastructure

**Audited by:** Plan 73-07
**Requirements scope:** INFRA-07–08, OBJST-01–12, KSERV-01–15, DEPLOY-01–08, PROD-01–03, DBHARD-01–08

```
[PENDING — Plan 73-07 populates this section]
```

---

## Consolidated Gap Table

*Populated after all domain auditors complete (Wave 2 final step — see Plan 73-07 which runs last alphabetically and should update this table after all others finish, or use /gsd:verify-work to aggregate manually).*

| REQ-ID | Gap Class | Description | Domain | File Expected | Action Needed |
|--------|-----------|-------------|--------|---------------|---------------|
| [TBD] | [CRITICAL/MISSING-TEST/STUB/ORPHANED] | [description] | [domain] | [path] | [fix/document/verify] |

Gap classes:
- **CRITICAL** — Required by v1/v1.1/v2/v3 spec, no implementation found
- **MISSING-TEST** — Implementation exists but no test coverage
- **STUB** — File exists but contains placeholder (pass, return None, TODO, NotImplementedError)
- **ORPHANED** — Assigned in traceability, no SUMMARY or code evidence found
- **DEFERRED** — Explicitly deferred — not a gap, documented above

---

## Audit Sign-Off

- [ ] All 6 domain sections populated by Wave 2 auditors
- [ ] Consolidated Gap Table updated
- [ ] YAML frontmatter counts updated (requirements_verified, gaps_critical, etc.)
- [ ] Phase 70 TBD-xx requirement IDs formalized into permanent IDs
- [ ] Tech debt items confirmed against code (no accidental deferred → critical reclassification)
- [ ] Phases 7–16, 23–57 ORPHANED items classified by domain auditors via code inspection
