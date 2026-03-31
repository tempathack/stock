---
phase: 73
status: complete
audit_date: 2026-03-31
total_requirements: 211
requirements_verified: 98
requirements_orphaned: 113
requirements_deferred: 11
gaps_critical: 0
gaps_missing_req: 2
gaps_missing_test: 0
gaps_stub: 0
gaps_note: 2
gaps_minor: 2
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

**Status:** COMPLETE
**Files Inspected:** 12 (8 routers, 1 main.py, 1 metrics.py, 1 rate_limit.py, 1 health_service.py)
**Test Files Found:** test_health.py, test_health_deep.py, test_ingest.py, test_predict.py, test_predict_horizon.py, test_market_router.py, test_market_service.py, test_models_router.py, test_streaming_features.py, test_sentiment_ws.py, test_analytics_router.py, test_analytics_feast.py, test_analytics_flink.py, test_analytics_kafka.py, test_analytics_argocd.py, test_candles_router.py, test_kserve.py, test_kafka_producer.py, test_yahoo_finance.py, test_prediction_service.py, test_model_metadata_cache.py, test_metrics.py, test_cronjob_triggers.py, conftest.py (24 test files)

#### Satisfied Requirements
| REQ-ID | Evidence | File |
|--------|----------|------|
| API-01 / API-02 | GET /health endpoint present, returns HealthResponse with status, service, version, db_pool, redis_status | routers/health.py:72 |
| API-05 | POST /ingest/intraday endpoint present, calls YahooFinanceService + OHLCVProducer (Kafka) | routers/ingest.py:73 |
| API-06 | POST /ingest/historical endpoint present, calls YahooFinanceService + OHLCVProducer (Kafka) | routers/ingest.py:91 |
| API-07 | GET /predict/{ticker}?horizon=N present, horizon validated against allowed list, calls get_live_prediction() | routers/predict.py:154 |
| API-08 | GET /predict/bulk present, calls get_bulk_live_predictions() with A/B model selection | routers/predict.py:66 |
| API-09 | GET /models/comparison endpoint present, queries model_registry table | routers/models.py:45 |
| API-10 | GET /models/drift endpoint present, queries drift_logs table | routers/models.py:129 |
| API-11 | GET /market/overview endpoint present, calls get_market_overview() | routers/market.py:32 |
| API-12 | GET /market/indicators/{ticker} endpoint present, calls get_ticker_indicators() | routers/market.py:57 |
| FENH-01 | WebSocket /ws/prices endpoint present, streams via broadcaster from price_feed.py | routers/ws.py:19 |
| FENH-04 | GET /backtest/{ticker} endpoint present, calls get_backtest_data() | routers/backtest.py:18 |
| PROD-04 | Custom RateLimitMiddleware (sliding window) registered in main.py with per-route overrides for /predict and /ingest; returns 429 with Retry-After header | main.py:109, rate_limit.py |
| PROD-05 | GET /health/deep endpoint present, runs DB (SELECT 1), Kafka (AdminClient), model freshness (model_registry), prediction staleness (predictions table) checks | routers/health.py:102, services/health_service.py |
| PROD-08 | GET /models/ab-results endpoint present, returns ABResultsResponse with per-model MAE/RMSE/directional_accuracy and traffic weights | routers/models.py:182 |
| MON-02 | 3 custom Prometheus metrics defined: prediction_requests_total (Counter), prediction_latency_seconds (Histogram), model_inference_errors_total (Counter) | app/metrics.py |

#### Gaps Found
| REQ-ID | Gap Class | Description | File Expected |
|--------|-----------|-------------|---------------|
| PROD-04 | NOTE | Rate limiting is implemented via custom RateLimitMiddleware (NOT slowapi/SlowAPI library). Functionally equivalent — sliding window per IP with per-route overrides. Library differs from plan specification. | main.py |

#### Stubs Detected
No true stubs found. The grep pattern matched files due to:
- `pass` in `except WebSocketDisconnect: pass` blocks in ws.py (legitimate exception handling)
- `pass` in `except asyncio.CancelledError: pass` in main.py (legitimate)
- `pass` in ORM base class `pass` (class body placeholder — standard SQLAlchemy pattern)
- `return None` in service files are DB-unavailable fallback paths, not stubs
- All `return None` paths have caller-side fallback logic (file-based, then DB)

**Conclusion:** No stub endpoints or TODO/FIXME/PLACEHOLDER markers found in any router or service file.

#### Wiring Issues
None found. All routers included in main.py:
- health, ingest, predict, models, market, ws, backtest, analytics all registered via `app.include_router()`
- All services imported and called (not referenced without calls)
- feast_online_service.py wired to both /market/streaming-features/{ticker} (GET) and /ws/sentiment/{ticker} (WebSocket)

#### Phase-Specific Checks
- Phase 70 /market/streaming-features/{ticker}: CONFIRMED — endpoint at market.py:135, calls `get_streaming_features()` from feast_online_service.py which reads `technical_indicators_fv` (ema_20, rsi_14, macd_signal) from Feast Redis online store; returns StreamingFeaturesResponse with `available` flag; graceful fallback to available=False on Feast error
- Phase 71 /ws/sentiment/{ticker}: CONFIRMED — WebSocket endpoint at ws.py:50, reads `reddit_sentiment_fv` from Feast Redis via `get_sentiment_features()`, returns avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit with `available` flag; 60s push interval
- Phase 69 /analytics/* endpoints: CONFIRMED — 4 endpoints present: GET /analytics/flink/jobs, GET /analytics/feast/freshness, GET /analytics/kafka/lag, GET /analytics/summary
- PROD-04 slowapi rate limiting: NOT FOUND (slowapi library not used) — CUSTOM EQUIVALENT: RateLimitMiddleware (sliding window, per-IP, per-route, 429 + Retry-After) implemented in app/rate_limit.py and registered in main.py
- PROD-05 deep health checks: CONFIRMED — GET /health/deep checks DB connectivity, Kafka broker reachability, model freshness (days since training), prediction staleness (hours since last prediction)
- MON-02 custom Prometheus metrics (>=3): CONFIRMED — 3 metrics: prediction_requests_total, prediction_latency_seconds, model_inference_errors_total (all with labels)

---

### Domain 2: ML Pipeline

**Audited by:** Plan 73-03
**Requirements scope:** FEAT-01–21, MODEL-01–21, EVAL-01–12, KF-01–15, DRIFT-01–07, ADVML-01–08

**Status:** COMPLETE
**Files Inspected:** 14 (features: 3, models: 5, evaluation: 4, drift: 3, pipelines: 1 + 10 components, feature_store: 2)
**Test Files Found:** test_indicators.py, test_lag_features.py, test_transformations.py, test_model_configs.py, test_model_trainer.py, test_ensemble.py, test_evaluator.py, test_ranking.py, test_metrics.py, test_cross_validation.py, test_shap_analysis.py, test_explainer.py, test_detector.py, test_monitor.py, test_trigger.py, test_drift_pipeline.py, test_drift_retrain_integration.py, test_feature_store.py, test_feast_definitions.py, test_feast_store.py, test_feast_apply.py, test_label_generator.py, test_multi_horizon.py, test_training_pipeline.py, test_pipeline_integration.py, test_model_selector.py, test_deployer.py, test_predictor.py, test_registry.py, test_serialization.py, test_s3_integration.py, test_storage_backends.py, test_data_loader.py, test_feature_engineer.py

#### Satisfied Requirements

| REQ-ID | Evidence | File |
|--------|----------|------|
| FEAT-01 | `compute_rsi` function present, Wilder's EWM smoothing | ml/features/indicators.py |
| FEAT-02 | `compute_macd` function present, MACD line, signal, histogram | ml/features/indicators.py |
| FEAT-03 | `compute_stochastic` function present, %K and %D | ml/features/indicators.py |
| FEAT-04 | `compute_sma` function present, periods [20, 50, 200] | ml/features/indicators.py |
| FEAT-05 | `compute_ema` function present, periods [12, 26] | ml/features/indicators.py |
| FEAT-06 | `compute_adx` function present, full DI+/DI- calculation | ml/features/indicators.py |
| FEAT-07 | `compute_bollinger` function present, upper/lower/bandwidth | ml/features/indicators.py |
| FEAT-08 | `compute_atr` function present, Wilder's ATR | ml/features/indicators.py |
| FEAT-09 | `compute_rolling_volatility` function present, annualized 21d | ml/features/indicators.py |
| FEAT-10 | `compute_obv` function present, cumulative OBV | ml/features/indicators.py |
| FEAT-11 | `compute_vwap` function present, cumulative VWAP | ml/features/indicators.py |
| FEAT-12 | `compute_volume_sma` function present, 20-period default | ml/features/indicators.py |
| FEAT-13 | `compute_ad_line` function present, A/D line | ml/features/indicators.py |
| FEAT-14 | `compute_returns` function present, periods [1,5,21] pct and log | ml/features/indicators.py |
| FEAT-15 | `compute_lag_features` present, lags [1,2,3,5,7,14,21] on close | ml/features/lag_features.py |
| FEAT-16 | `compute_rolling_stats` present, windows [5,10,21], mean/std/min/max | ml/features/lag_features.py |
| FEAT-17 | `build_scaler_pipeline("standard")` → StandardScaler | ml/features/transformations.py |
| FEAT-18 | `build_scaler_pipeline("quantile")` → QuantileTransformer | ml/features/transformations.py |
| FEAT-19 | `build_scaler_pipeline("minmax")` → MinMaxScaler | ml/features/transformations.py |
| FEAT-20 | `generate_target` present, `shift(-horizon)` used, no leakage | ml/features/lag_features.py |
| FEAT-21 | `drop_incomplete_rows` present, calls `df.dropna()` | ml/features/lag_features.py |
| MODEL-01 | `LinearRegression` in LINEAR_MODELS dict | ml/models/model_configs.py |
| MODEL-02 | `Ridge` in LINEAR_MODELS with alpha search space logspace(-3,3) | ml/models/model_configs.py |
| MODEL-03 | `Lasso` in LINEAR_MODELS with alpha search space | ml/models/model_configs.py |
| MODEL-04 | `ElasticNet` in LINEAR_MODELS with alpha+l1_ratio search space | ml/models/model_configs.py |
| MODEL-05 | `BayesianRidge` in LINEAR_MODELS | ml/models/model_configs.py |
| MODEL-06 | `HuberRegressor` in LINEAR_MODELS with epsilon search space | ml/models/model_configs.py |
| MODEL-07 | `RandomForestRegressor` in TREE_MODELS with full search space | ml/models/model_configs.py |
| MODEL-08 | `GradientBoostingRegressor` in TREE_MODELS | ml/models/model_configs.py |
| MODEL-09 | `HistGradientBoostingRegressor` in TREE_MODELS | ml/models/model_configs.py |
| MODEL-10 | `ExtraTreesRegressor` in TREE_MODELS | ml/models/model_configs.py |
| MODEL-11 | `DecisionTreeRegressor` in TREE_MODELS | ml/models/model_configs.py |
| MODEL-12 | `AdaBoostRegressor` in TREE_MODELS | ml/models/model_configs.py |
| MODEL-13 | `KNeighborsRegressor` in DISTANCE_NEURAL_MODELS | ml/models/model_configs.py |
| MODEL-14 | `SVR` in DISTANCE_NEURAL_MODELS with `kernel="rbf"` default | ml/models/model_configs.py |
| MODEL-15 | `MLPRegressor` in DISTANCE_NEURAL_MODELS with early_stopping | ml/models/model_configs.py |
| MODEL-16 | `XGBRegressor` in BOOSTER_MODELS via conditional import | ml/models/model_configs.py |
| MODEL-17 | `LGBMRegressor` in BOOSTER_MODELS via conditional import | ml/models/model_configs.py |
| MODEL-18 | `CatBoostRegressor` in BOOSTER_MODELS via conditional import | ml/models/model_configs.py |
| MODEL-19 | `TimeSeriesSplit` used in `create_time_series_cv(n_splits=5)` | ml/evaluation/cross_validation.py |
| MODEL-20 | `walk_forward_evaluate` implements per-fold CV with metrics | ml/evaluation/cross_validation.py |
| MODEL-21 | `search_space` dicts present for all tunable models (Ridge, Lasso, RF, etc.) | ml/models/model_configs.py |
| EVAL-01 | `compute_r2` in `compute_all_metrics` | ml/evaluation/metrics.py |
| EVAL-02 | `compute_mae` in `compute_all_metrics` | ml/evaluation/metrics.py |
| EVAL-03 | `compute_rmse` in `compute_all_metrics` | ml/evaluation/metrics.py |
| EVAL-04 | `compute_mape` in `compute_all_metrics` | ml/evaluation/metrics.py |
| EVAL-05 | `compute_directional_accuracy` in `compute_all_metrics` | ml/evaluation/metrics.py |
| EVAL-06 | `compute_fold_stability` (std dev of fold RMSEs) | ml/evaluation/metrics.py |
| EVAL-07 | `rank_models` ranks by composite score (oos_rmse + stability penalty) | ml/evaluation/ranking.py |
| EVAL-08 | `stability_penalty_weight=0.5` applied to `fold_stability` in composite score | ml/evaluation/ranking.py |
| EVAL-09 | `select_winner` returns `WinnerResult` with single winner | ml/evaluation/ranking.py |
| EVAL-10 | `ModelRegistry.save_model` persists pipeline + metadata JSON to registry | ml/models/registry.py |
| EVAL-11 | `compute_shap_values` with TreeExplainer/LinearExplainer/KernelExplainer | ml/evaluation/shap_analysis.py |
| EVAL-12 | `shap_importance.json` and `shap_values.json` written by `explain_top_models` | ml/pipelines/components/explainer.py |
| KF-01 | Kubeflow installed in ml namespace (VERIFIED per SUMMARY evidence) | Phase 17 SUMMARY |
| KF-02 | `load_data` component in ml/pipelines/components/data_loader.py | ml/pipelines/components/data_loader.py |
| KF-03 | `engineer_features` component in ml/pipelines/components/feature_engineer.py | ml/pipelines/components/feature_engineer.py |
| KF-04 | `generate_labels` component in ml/pipelines/components/label_generator.py | ml/pipelines/components/label_generator.py |
| KF-05 | `train_all_models` component in ml/pipelines/components/model_trainer.py | ml/pipelines/components/model_trainer.py |
| KF-06 | `walk_forward_evaluate` / `generate_cv_report` — CV step confirmed | ml/evaluation/cross_validation.py |
| KF-07 | `evaluate_models` component in ml/pipelines/components/evaluator.py — CONFIRMED | ml/pipelines/components/evaluator.py |
| KF-08 | `generate_comparison_report` component in ml/pipelines/components/evaluator.py — CONFIRMED | ml/pipelines/components/evaluator.py |
| KF-09 | `explain_top_models` in ml/pipelines/components/explainer.py | ml/pipelines/components/explainer.py |
| KF-10 | `select_and_persist_winner` in ml/pipelines/components/model_selector.py | ml/pipelines/components/model_selector.py |
| KF-11 | `ModelRegistry.save_model` persists artifacts | ml/models/registry.py |
| KF-12 | `deploy_winner_model` in ml/pipelines/components/deployer.py | ml/pipelines/components/deployer.py |
| KF-13 | `run_training_pipeline` in training_pipeline.py — 12-step pipeline | ml/pipelines/training_pipeline.py |
| KF-14 | `PIPELINE_VERSION = "1.2.0"` + `run_id` uuid per run; artifacts versioned | ml/pipelines/training_pipeline.py |
| KF-15 | `evaluate_and_trigger` in trigger.py calls `trigger_retraining` from drift_pipeline | ml/drift/trigger.py |
| DRIFT-01 | `DataDriftDetector` with KS-test (`ks_2samp`) and PSI computation | ml/drift/detector.py |
| DRIFT-02 | `PredictionDriftDetector` compares baseline vs recent errors (MAE ratio) | ml/drift/detector.py |
| DRIFT-03 | `ConceptDriftDetector` compares historical vs recent RMSE | ml/drift/detector.py |
| DRIFT-04 | `DriftMonitor.check` orchestrates all 3 detectors; CLI `__main__` entry point for CronJob | ml/drift/trigger.py |
| DRIFT-05 | `DriftLogger.log_event` writes JSONL to drift_logs (local or S3) | ml/drift/trigger.py |
| DRIFT-06 | `check_result.any_drift` flag returned from `DriftMonitor.check`; triggers retraining | ml/drift/monitor.py, trigger.py |
| DRIFT-07 | `evaluate_and_trigger` calls `trigger_retraining` from `drift_pipeline.py` on drift; post-retrain prediction regeneration also present | ml/drift/trigger.py |
| ADVML-01 | `StackingEnsemble` class using `sklearn.ensemble.StackingRegressor` with Ridge meta-learner | ml/models/ensemble.py |
| ADVML-02 | `StackingEnsemble` built and fitted in `run_training_pipeline` steps 8/12 (both single and multi-horizon modes) | ml/pipelines/training_pipeline.py |
| ADVML-03 | `generate_multi_horizon_labels` generates target_1d, target_7d, target_30d via `generate_target(df, horizon=h)` for h in [1,7,30] | ml/pipelines/components/label_generator.py |
| ADVML-04 | Per-horizon model training loop in `run_training_pipeline` with separate `h_registry_dir` per horizon | ml/pipelines/training_pipeline.py |
| ADVML-07 | Feature store PostgreSQL tables used via Feast offline store | ml/feature_store/feature_repo.py |
| ADVML-08 | `engineer_features(data_dict, use_feature_store=True)` code path in pipeline | ml/pipelines/training_pipeline.py |

#### Gaps Found

| REQ-ID | Gap Class | Description | File Expected |
|--------|-----------|-------------|---------------|
| MODEL-BAGGING | MISSING-REQ | `BaggingRegressor` mentioned in plan task description as MODEL-07–12 but NOT present in model_configs.py — TREE_MODELS has 6 entries (RF, GB, HistGB, ExtraTrees, DT, AdaBoost); BaggingRegressor is not among them | ml/models/model_configs.py |

#### Stubs Detected

No stub implementations found. Files with `return None` or `pass` statements are only empty `__init__.py` modules and `TYPE_CHECKING` blocks — no functional stubs. The grep scan for `raise NotImplementedError` returned no matches in functional code.

#### Wiring Issues

None. StackingEnsemble is defined AND registered/called in `run_training_pipeline` at step 8/12 in both single-horizon and multi-horizon execution paths. The `StackingEnsemble` result is appended to `results_list` and its pipeline is stored as `"stacking_ensemble_meta_ridge"` in the `pipelines` dict before winner selection.

#### Phase-Specific Checks

- ADVML-01 StackingRegressor: CONFIRMED — `StackingEnsemble` class in ml/models/ensemble.py uses `sklearn.ensemble.StackingRegressor` with `Ridge(alpha=1.0)` as meta-learner, top_n=5 base models by OOS RMSE
- ADVML-03 multi-horizon shift(-7) and shift(-30): CONFIRMED — `generate_multi_horizon_labels` in label_generator.py calls `generate_target(labelled, horizon=h)` for h in [1,7,30]; `generate_target` uses `df["close"].shift(-h)` for each horizon
- Phase 71 reddit_sentiment_fv FeatureView: CONFIRMED — `reddit_sentiment_fv = FeatureView(name="reddit_sentiment_fv", ...)` defined at line 143 of feature_repo.py with 5 schema fields (avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit), TTL=10 minutes, online=True
- Phase 70 streaming_features FeatureView: NOT FOUND as a FeatureView named "streaming_features" — Phase 70 uses `technical_indicators_fv` with `stream_source=technical_indicators_push` (a PushSource) as the streaming mechanism; dedicated "streaming_features" named view absent but streaming capability is confirmed via PushSource pattern
- DRIFT-07 auto-retrain trigger: CONFIRMED in Python — `evaluate_and_trigger` in trigger.py detects drift → calls `trigger_retraining` from ml/pipelines/drift_pipeline.py; post-retrain: `generate_predictions` + `save_predictions` called; CLI entry point `python -m ml.drift.trigger --auto-retrain` available for K8s CronJob
- KF-07/KF-08 (unchecked in REQUIREMENTS.md): CONFIRMED — pipeline has 12 components: (1) load_data, (2) engineer_features, (3) generate_labels, (4) prepare_training_data, (5) train_all_models, (6) cross_validation (generate_cv_report), (7) evaluate_models [KF-07 confirmed], (8) ensemble_stacking, (9) model_comparison (generate_comparison_report) [KF-08 confirmed], (10) explainability, (11) select_winner, (12) deploy_model. Note: docstring says "11-step" but implementation is 12-step — minor documentation inconsistency, not a functional gap.

---

### Domain 3: Kafka / Flink / Streaming

**Audited by:** Plan 73-04
**Requirements scope:** KAFKA-01–05, CONS-01–07, Phase 67 (Flink), Phase 71 (Reddit/sentiment)

```
**Status:** COMPLETE
**Files Inspected:** 20

#### Satisfied Requirements

| REQ-ID | Evidence | File |
|--------|----------|------|
| KAFKA-01 | KafkaCluster CR present — kind: Kafka, name: kafka, namespace: storage, Strimzi KRaft mode, version 3.7.0 | k8s/kafka/kafka-cluster.yaml |
| KAFKA-02 | KafkaTopic CR present — name: intraday-data, 3 partitions, 7-day retention | k8s/kafka/kafka-topics.yaml |
| KAFKA-03 | KafkaTopic CR present — name: historical-data, 3 partitions, 30-day retention | k8s/kafka/kafka-topics.yaml |
| KAFKA-04 (Phase 71) | KafkaTopic CR present — name: reddit-raw, 3 partitions, 1-day retention | k8s/kafka/kafka-topic-reddit.yaml |
| KAFKA-05 (Phase 71) | KafkaTopic CR present — name: sentiment-aggregated, 3 partitions, 7-day retention | k8s/kafka/kafka-topic-reddit.yaml |
| CONS-06 | Idempotent upserts confirmed — ON CONFLICT (ticker, timestamp) DO UPDATE in intraday path; ON CONFLICT (ticker, date) DO UPDATE in daily path; ON CONFLICT (ticker) DO NOTHING for stocks table | services/kafka-consumer/consumer/db_writer.py (lines 27, 38, 49) |
| FLINK-CR-01 | FlinkDeployment CR present — name: ohlcv-normalizer, job.args references /opt/flink/usrlib/ohlcv_normalizer.py, RocksDB state backend, EXACTLY_ONCE checkpointing to MinIO | k8s/flink/flinkdeployment-ohlcv-normalizer.yaml |
| FLINK-CR-02 | FlinkDeployment CR present — name: indicator-stream, job.args references /opt/flink/usrlib/indicator_stream.py | k8s/flink/flinkdeployment-indicator-stream.yaml |
| FLINK-CR-03 | FlinkDeployment CR present — name: feast-writer, job.args references /opt/flink/usrlib/feast_writer.py, FEAST_STORE_PATH env var set | k8s/flink/flinkdeployment-feast-writer.yaml |
| FLINK-CR-04 (Phase 71) | FlinkDeployment CR present — name: sentiment-stream, job.args references /opt/flink/usrlib/sentiment_stream.py | k8s/flink/flinkdeployment-sentiment-stream.yaml |
| FLINK-CR-05 (Phase 71) | FlinkDeployment CR present — name: sentiment-writer, job.args references /opt/flink/usrlib/sentiment_writer.py, FEAST_STORE_PATH env var set | k8s/flink/flinkdeployment-sentiment-writer.yaml |
| FLINK-PY-01 | Python file present — ohlcv_normalizer.py with normalizer_logic.py helper | services/flink-jobs/ohlcv_normalizer/ |
| FLINK-PY-02 | Python file present — indicator_stream.py with indicator_udaf_logic.py helper | services/flink-jobs/indicator_stream/ |
| FLINK-PY-03 | Python file present — feast_writer.py, calls store.push() with PushMode.ONLINE | services/flink-jobs/feast_writer/feast_writer.py |
| FLINK-PY-04 (Phase 71) | Python file present — sentiment_stream.py; VaderScoreUdf class confirmed; HOP window confirmed | services/flink-jobs/sentiment_stream/sentiment_stream.py |
| FLINK-PY-05 (Phase 71) | Python file present — sentiment_writer.py, calls store.push(push_source_name="reddit_sentiment_push") | services/flink-jobs/sentiment_writer/sentiment_writer.py |
| REDDIT-PROD | PRAW polling loop confirmed — import praw; reddit.subreddit(name).new(limit=N) in while True loop; producer.produce(topic=REDDIT_TOPIC, ...) where REDDIT_TOPIC="reddit-raw" | services/reddit-producer/reddit_producer.py |

#### Gaps Found

| REQ-ID | Gap Class | Description | File Expected |
|--------|-----------|-------------|---------------|
| — | — | No gaps found — all 5 FlinkDeployment CRs, 5 Flink Python files, 2 Phase 71 Kafka topic CRs, and Reddit producer are fully implemented | — |

#### Stubs Detected

None — grep for raise NotImplementedError, pass, TODO, FIXME, PLACEHOLDER across all streaming services returned no matches.

#### Wiring Issues

None detected:
- All 5 FlinkDeployment CRs reference correct Python file paths via job.args ("-py" flag)
- feast-writer and sentiment-writer both have FEAST_STORE_PATH env var set
- sentiment_writer.py push_source_name="reddit_sentiment_push" matches Feast PushSource name
- All 5 CRs use stock-flink-{job-name}:latest image names consistent with build convention
- kafka-consumer db_writer.py is labelled "idempotent upsert" in module docstring and implements ON CONFLICT in both intraday and daily paths

#### Phase-Specific Checks

- KAFKA-02 intraday-data topic CR: CONFIRMED (k8s/kafka/kafka-topics.yaml)
- KAFKA-03 historical-data topic CR: CONFIRMED (k8s/kafka/kafka-topics.yaml)
- Phase 71 reddit-raw topic CR: CONFIRMED (k8s/kafka/kafka-topic-reddit.yaml)
- Phase 71 sentiment-aggregated topic CR: CONFIRMED (k8s/kafka/kafka-topic-reddit.yaml)
- Phase 67 ohlcv-normalizer FlinkDeployment: CONFIRMED (k8s/flink/flinkdeployment-ohlcv-normalizer.yaml)
- Phase 67 indicator-stream FlinkDeployment: CONFIRMED (k8s/flink/flinkdeployment-indicator-stream.yaml)
- Phase 67 feast-writer FlinkDeployment: CONFIRMED (k8s/flink/flinkdeployment-feast-writer.yaml)
- Phase 71 sentiment-stream FlinkDeployment: CONFIRMED (k8s/flink/flinkdeployment-sentiment-stream.yaml)
- Phase 71 sentiment-writer FlinkDeployment: CONFIRMED (k8s/flink/flinkdeployment-sentiment-writer.yaml)
- Phase 71 VaderScoreUdf in sentiment_stream.py: CONFIRMED (class VaderScoreUdf(ScalarFunction) at line 34; registered as "vader_score" UDF at line 144)
- Phase 71 HOP window in sentiment_stream.py: CONFIRMED (HOP(TABLE reddit_unnested, DESCRIPTOR(event_time), ...) at line 235; 1-min hop / 5-min window per module docstring)
- Phase 71 reddit_sentiment_push in sentiment_writer.py: CONFIRMED (store.push(push_source_name="reddit_sentiment_push", ...) at line 50)
- CONS-06 idempotent upserts (ON CONFLICT): CONFIRMED (db_writer.py lines 27, 38, 49 — ON CONFLICT DO UPDATE for intraday and daily, DO NOTHING for stocks)
- Reddit PRAW producer polling loop: CONFIRMED (import praw; while True loop calling poll_subreddit() → sub.new(limit) → producer.produce(topic="reddit-raw"))
```

---

### Domain 4: Frontend

**Audited by:** Plan 73-05
**Requirements scope:** FE-01–06, FMOD-01–06, FFOR-01–06, FDASH-01–08, FDRFT-01–05, FENH-03–07

**Status:** COMPLETE
**Files Inspected:** 28
**E2E Spec Files Found:** analytics.spec.ts, api-health.spec.ts, backtest-data-sanity.spec.ts, backtest.spec.ts, dashboard.spec.ts, drift-data-sanity.spec.ts, drift.spec.ts, forecasts.spec.ts, models.spec.ts, streaming-features.spec.ts (app) + argocd.spec.ts, flink-web-ui.spec.ts, grafana-flink-72.spec.ts, grafana.spec.ts, k8s-dashboard.spec.ts, kubeflow.spec.ts, minio.spec.ts, prometheus.spec.ts (infra)

#### Satisfied Requirements
| REQ-ID | Evidence | File |
|--------|----------|------|
| FE-01 | React app with React Router BrowserRouter, lazy-loaded routes for all 6 pages | src/App.tsx |
| FE-02 | MUI dark theme via createTheme with `mode: 'dark'` | src/theme/index.ts |
| FE-03 | Sidebar (TopNav) navigation bar — Layout wraps all routes with Sidebar | src/components/layout/Sidebar.tsx, Layout.tsx |
| FE-04 | API client with typed hooks (useModelComparison, useBulkPredictions, etc.) | src/api/client.ts |
| FE-05 | K8s deployment.yaml and service.yaml present | k8s/frontend/deployment.yaml, service.yaml |
| FE-06 | Argo CD app manifest for frontend | k8s/argocd/app-frontend.yaml |
| FMOD-01 | ModelComparisonTable component imported and rendered in Models.tsx | src/pages/Models.tsx:12,127 |
| FMOD-02 | WinnerCard component with winner indicator | src/pages/Models.tsx:123 |
| FMOD-03 | ShapBarChart and ShapBeeswarmPlot components imported and used | src/pages/Models.tsx:13 |
| FMOD-04 | FoldPerformanceChart component present | src/components/charts/FoldPerformanceChart.tsx |
| FMOD-05 | ModelDetailPanel (SHAP detail panel) imported in Models.tsx | src/pages/Models.tsx:12 |
| FMOD-06 | ExportButtons component in Models.tsx with exportToCsv/exportTableToPdf | src/pages/Models.tsx:11,17-18 |
| FFOR-01 | ForecastTable with ForecastFilters — filter state and table component | src/pages/Forecasts.tsx:14-15 |
| FFOR-02 | StockDetailChart and IndicatorOverlayCharts for stock detail with TA | src/pages/Forecasts.tsx:16,18 |
| FFOR-03 | StockComparisonPanel present | src/pages/Forecasts.tsx:15 |
| FFOR-04 | ExportButtons with exportToCsv/exportTableToPdf | src/pages/Forecasts.tsx:12,27-28 |
| FFOR-05 | StockShapPanel for per-ticker SHAP | src/pages/Forecasts.tsx:19 |
| FFOR-06 | HorizonToggle component with useAvailableHorizons API hook | src/pages/Forecasts.tsx:20,22 |
| FDASH-01 | MarketTreemap component imported and rendered in Dashboard.tsx | src/pages/Dashboard.tsx:22,282 |
| FDASH-02 | CandlestickChart (intraday chart) imported and used in Drawer | src/pages/Dashboard.tsx:24,361 |
| FDASH-03 | HistoricalChart imported and used in Drawer | src/pages/Dashboard.tsx:25,368 |
| FDASH-04 | DashboardTAPanel (TA overlay) imported and used in Drawer | src/pages/Dashboard.tsx:26,434 |
| FDASH-05 | MetricCards panel imported and rendered | src/pages/Dashboard.tsx:23,354 |
| FDASH-06 | useWebSocket hook integrated in Dashboard.tsx with WS status dot | src/pages/Dashboard.tsx:34,38-43 |
| FDASH-07 | PriceTickerStrip component with live price display | src/pages/Dashboard.tsx:45 |
| FDASH-08 | MobileMarketList component present in dashboard index | src/components/dashboard/index.ts:8 |
| FDRFT-01 | ActiveModelCard imported and used in Drift.tsx | src/pages/Drift.tsx:14,~line 80+ |
| FDRFT-02 | RollingPerformanceChart imported and used | src/pages/Drift.tsx:16 |
| FDRFT-03 | DriftTimeline chart imported and rendered | src/pages/Drift.tsx:15,160 |
| FDRFT-04 | RetrainStatusPanel imported | src/pages/Drift.tsx:17 |
| FDRFT-05 | FeatureDistributionChart imported | src/pages/Drift.tsx:18 |
| FENH-03 | HorizonToggle in Forecasts.tsx with 1d/7d/30d-style horizon toggle state | src/pages/Forecasts.tsx:20,horizon state |
| FENH-04 | Backtest.tsx page exists with BacktestChart and BacktestMetricsSummary | src/pages/Backtest.tsx |
| FENH-05 | useBacktest API hook wired in Backtest.tsx | src/pages/Backtest.tsx:23 |
| FENH-06 | CSV export: exportToCsv util used in Models.tsx, Forecasts.tsx, Backtest.tsx | src/utils/exportCsv.ts (via imports) |
| FENH-06 | PDF export: exportTableToPdf used in Models.tsx, Forecasts.tsx, Backtest.tsx | src/utils/exportPdf.ts (confirmed exists) |
| FENH-07 | Responsive layout: useMediaQuery, xs:/sm:/md:/lg: grid breakpoints in 15+ files | src/pages/Dashboard.tsx, Layout.tsx, Forecasts.tsx, Models.tsx, Backtest.tsx, etc. |
| FENH-01 | useWebSocket hook exists | src/hooks/useWebSocket.ts |
| FENH-02 | Reconnection logic in useWebSocket: reconnectAttempts param, linear backoff on close (delay = reconnectInterval * attempt+1), max attempts guard | src/hooks/useWebSocket.ts:86-94 |
| Phase 69 | Analytics.tsx exists with OLAPCandleChart, StreamHealthPanel, FeatureFreshnessPanel, StreamLagMonitor, SystemHealthSummary | src/pages/Analytics.tsx |
| Phase 70 | StreamingFeaturesPanel.tsx exists and is exported from dashboard index | src/components/dashboard/StreamingFeaturesPanel.tsx, index.ts:7 |
| Phase 70 | StreamingFeaturesPanel imported in Dashboard.tsx line 28 and rendered at line 406 inside Drawer | src/pages/Dashboard.tsx:28,406 |
| Phase 71 | SentimentPanel.tsx exists and exported from dashboard index | src/components/dashboard/SentimentPanel.tsx, index.ts:9 |
| Phase 71 | SentimentPanel imported in Dashboard.tsx line 27 and rendered at line 459 inside Drawer | src/pages/Dashboard.tsx:27,459 |
| Phase 71 | useSentimentSocket hook exists with exponential backoff reconnection | src/hooks/useSentimentSocket.ts |

#### Gaps Found
| REQ-ID | Gap Class | Description | File Expected |
|--------|-----------|-------------|---------------|
| None | — | All frontend requirements satisfied. No gaps detected. | — |

#### Stubs Detected
None — all components render substantive content. No placeholder JSX observed in inspected files.

#### Wiring Issues
None — StreamingFeaturesPanel and SentimentPanel are both imported and actively rendered inside Dashboard.tsx Drawer at lines 406 and 459 respectively.

#### Phase-Specific Checks
- Phase 70 StreamingFeaturesPanel.tsx exists: YES
- Phase 70 StreamingFeaturesPanel in Dashboard.tsx: CONFIRMED IMPORTED (line 28) AND RENDERED (line 406 in Drawer)
- Phase 70 STATUS CONCLUSION: COMPLETE — file exists, exported from index, imported and rendered in Dashboard Drawer
- Phase 71 SentimentPanel.tsx exists: YES
- Phase 71 SentimentPanel in Dashboard.tsx: CONFIRMED IMPORTED (line 27) AND RENDERED (line 459 in Drawer)
- Phase 71 useSentimentSocket hook exists: YES — with exponential backoff (Math.pow(2, retryCount), max 30s delay, 5 retries)
- FENH-02 useWebSocket reconnection logic: CONFIRMED — has reconnectAttempts param (default 5), linear backoff (delay = reconnectInterval * attempt+1), closes cleanly on code 1000
- FENH-06 CSV/PDF export: CONFIRMED — exportToCsv and exportTableToPdf utilities imported in Models.tsx, Forecasts.tsx, Backtest.tsx; exportPdf.ts confirmed present
- FENH-07 mobile responsive layout: CONFIRMED — useMediaQuery and grid breakpoints (xs/sm/md/lg) used in 15+ component files including Dashboard, Layout, Forecasts, Models, Backtest
- Phase 69 Analytics page: CONFIRMED — Analytics.tsx with OLAPCandleChart (TimescaleDB), StreamHealthPanel (Flink), FeatureFreshnessPanel (Feast), StreamLagMonitor, SystemHealthSummary; routed at /analytics in App.tsx
- Playwright E2E: 10 app specs (analytics, api-health, backtest, backtest-data-sanity, dashboard, drift, drift-data-sanity, forecasts, models, streaming-features) + 8 infra specs (argocd, flink-web-ui, grafana-flink-72, grafana, k8s-dashboard, kubeflow, minio, prometheus) = 18 total spec files

---

### Domain 5: Observability

**Audited by:** Plan 73-06
**Requirements scope:** MON-01–10

**Status:** COMPLETE
**Files Inspected:** 10
**Grafana Dashboard ConfigMaps Found:** grafana-dashboard-api-health.yaml (12 panels), grafana-dashboard-flink.yaml (10 panels), grafana-dashboard-kafka.yaml (9 panels), grafana-dashboard-ml-perf.yaml (11 panels)

#### Satisfied Requirements
| REQ-ID | Evidence | File |
|--------|----------|------|
| MON-01 | Prometheus deployment manifest present | k8s/monitoring/prometheus-deployment.yaml |
| MON-02 | 3 custom metrics: prediction_requests_total (Counter), prediction_latency_seconds (Histogram), model_inference_errors_total (Counter) | services/api/app/metrics.py |
| MON-03 | API scrape job: kubernetes-pods (annotation-driven, covers FastAPI pods) | k8s/monitoring/prometheus-configmap.yaml |
| MON-04 | flink-jobs scrape job confirmed — job_name: flink-jobs, targets flink namespace | k8s/monitoring/prometheus-configmap.yaml |
| MON-05 | api-health Grafana dashboard ConfigMap present (12 panels) | k8s/monitoring/grafana-dashboard-api-health.yaml |
| MON-06 | ml-perf Grafana dashboard ConfigMap present (11 panels) | k8s/monitoring/grafana-dashboard-ml-perf.yaml |
| MON-07 | kafka Grafana dashboard ConfigMap present (9 panels) | k8s/monitoring/grafana-dashboard-kafka.yaml |
| MON-08 | 3 alert rules defined: HighDriftSeverity, HighAPIErrorRate, HighConsumerLag (drift, API 5xx, Kafka lag) | k8s/monitoring/prometheus-configmap.yaml (alert_rules.yml) |
| MON-09 | loki-configmap.yaml present (boltdb-shipper storage, filesystem backend, 168h retention); promtail-configmap.yaml present with pipeline_stages (cri parser) | k8s/monitoring/loki-configmap.yaml, k8s/monitoring/promtail-configmap.yaml |
| MON-10 | Loki datasource in grafana-datasource-configmap.yaml confirmed (type: loki, url: loki.monitoring.svc.cluster.local:3100) | k8s/monitoring/grafana-datasource-configmap.yaml |

#### Gaps Found
| REQ-ID | Gap Class | Description | File Expected |
|--------|-----------|-------------|---------------|
| MON-09 | Minor | promtail pipeline_stages uses `cri: {}` (CRI log format parsing) — not explicit JSON structlog parsing; structured JSON fields are parsed at the CRI layer, not a dedicated json stage | k8s/monitoring/promtail-configmap.yaml |
| MON-10 | Minor | Loki datasource has no `uid:` field set (unlike Prometheus which has `uid: prometheus`); not a blocking issue but uid is unset | k8s/monitoring/grafana-datasource-configmap.yaml |

#### Wiring Issues
None — all Grafana dashboard panels reference datasource uid `prometheus` (lowercase), consistent with the pinned datasource UID in grafana-datasource-configmap.yaml. No capital-P mismatch found.

#### Phase 72 Audit
- Phase 72-01 flink-jobs scrape job in prometheus-configmap.yaml: CONFIRMED — job_name: flink-jobs (targets flink namespace, port annotation-driven)
- Phase 72 datasource UID pinned to lowercase "prometheus": CONFIRMED — uid: prometheus in grafana-datasource-configmap.yaml; all dashboard panels reference uid: "prometheus"
- Phase 72-02 Flink dashboard panel count: 10 visualization panels found (3 stat + 6 timeseries + 1 stat) across 5 row groups — expected 10 — CONFIRMED

#### Phase-Specific Checks
- MON-02 custom metrics count: 3 metrics in metrics.py — names: prediction_requests_total, prediction_latency_seconds, model_inference_errors_total
- MON-03 API scrape job: CONFIRMED — kubernetes-pods job uses annotation prometheus.io/scrape=true (annotation-driven, not a dedicated fastapi job_name)
- MON-04 flink scrape job (Phase 72-01): CONFIRMED — job_name: flink-jobs present in scrape_configs
- MON-05–07 dashboard ConfigMaps: api-health: 12 panels, ml-perf: 11 panels, kafka: 9 panels, flink: 10 panels (no dedicated drift dashboard ConfigMap found — drift alerts covered in prometheus rules, not a separate Grafana dashboard)
- MON-08 alert rules (drift/API/Kafka): CONFIRMED — 3 rules found: HighDriftSeverity (model_inference_errors_total rate), HighAPIErrorRate (HTTP 5xx ratio >5%), HighConsumerLag (consumer_lag >1000)
- MON-09 Loki + Promtail configs: CONFIRMED — loki-configmap.yaml and promtail-configmap.yaml both present and configured; minor: CRI pipeline stage vs explicit JSON stage
- MON-10 Loki datasource in Grafana: CONFIRMED — type: loki datasource present; minor: no uid field for Loki (Prometheus uid is set, Loki uid is not)

---

### Domain 6: Infrastructure

**Audited by:** Plan 73-07
**Requirements scope:** INFRA-07–08, OBJST-01–12, KSERV-01–15, DEPLOY-01–08, PROD-01–03, DBHARD-01–08

**Status:** PARTIAL
**Files Inspected:** 22 (k8s/storage/: 8 manifests; k8s/ml/: 6 manifests + kserve/ 6 manifests; k8s/argocd/: root-app.yaml; ml/feature_store/feature_store.yaml; ml/Dockerfile; services/api/Dockerfile; services/kafka-consumer/Dockerfile; services/frontend/Dockerfile; services/flink-jobs/: 5 Dockerfiles; services/reddit-producer/Dockerfile; scripts/deploy-all.sh)

#### Satisfied Requirements
| REQ-ID | Evidence | File |
|--------|----------|------|
| OBJST-01 | MinIO Deployment CR present — `kind: Deployment name: minio namespace: storage`, image: `minio/minio:RELEASE.2024-06-13T22-53-53Z`, PVC-backed data volume | k8s/storage/minio-deployment.yaml |
| OBJST-02 | `model-artifacts` bucket created via `mc mb --ignore-existing local/model-artifacts` in init Job | k8s/storage/minio-init-job.yaml |
| OBJST-03 | `drift-logs` bucket created via `mc mb --ignore-existing local/drift-logs` in init Job | k8s/storage/minio-init-job.yaml |
| OBJST-04 | K8s Secret `minio-secrets` with `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` keys | k8s/storage/minio-secrets.yaml |
| OBJST-08 | `STORAGE_BACKEND: "s3"` in ml-pipeline ConfigMap AND `STORAGE_BACKEND: "s3"` env var injected directly into weekly-training CronJob spec | k8s/ml/configmap.yaml:15, k8s/ml/cronjob-training.yaml |
| KSERV-05 | InferenceService primary `storageUri: "s3://model-artifacts/serving/active"` — points to MinIO bucket | k8s/ml/kserve/kserve-inference-service.yaml |
| KSERV-05 (canary) | InferenceService canary `storageUri: "s3://model-artifacts/serving/canary"` — canary also points to MinIO | k8s/ml/kserve/kserve-inference-service-canary.yaml |
| KSERV-04 | `kind: ClusterServingRuntime` name: stock-sklearn-mlserver present | k8s/ml/kserve/sklearn-serving-runtime.yaml |
| KSERV-03 | KServe S3 Secret `kserve-s3-secret` with AWS_ACCESS_KEY_ID and MinIO endpoint annotation | k8s/ml/kserve/kserve-s3-secret.yaml |
| DEPLOY-01 | ML pipeline Dockerfile present — 2-stage build (builder: pip install; runtime: appuser + /data dirs) | ml/Dockerfile |
| DEPLOY-02 | ConfigMap `ml-pipeline-config` in ml namespace — MODEL_REGISTRY_DIR, SERVING_DIR, STORAGE_BACKEND, MinIO bucket env vars | k8s/ml/configmap.yaml |
| DEPLOY-03 | `kind: CronJob` name: weekly-training, schedule: `"0 3 * * 0"` (Sunday 03:00 UTC), calls `python -m ml.pipelines.training_pipeline` | k8s/ml/cronjob-training.yaml |
| DEPLOY-04 | `kind: CronJob` name: daily-drift, schedule: `"0 22 * * 1-5"` (weekdays 22:00 UTC), calls drift trigger | k8s/ml/cronjob-drift.yaml |
| DEPLOY-05 | `kind: PersistentVolumeClaim` name: model-artifacts-pvc, namespace: ml, 5Gi ReadWriteOnce | k8s/ml/model-pvc.yaml |
| DEPLOY-07 | deploy-all.sh Phase 33 (ML Docker build) and Phase 34 (ML CronJobs) are uncommented active commands — `kubectl apply -f k8s/ml/cronjob-training.yaml`, `kubectl apply -f k8s/ml/cronjob-drift.yaml` at lines 343–346 | scripts/deploy-all.sh:343–346 |
| DEPLOY-08 | `ml/drift/trigger.py` CLI entry point confirmed by Domain 2 audit; CronJob calls `python -m ml.drift.trigger` | k8s/ml/cronjob-drift.yaml |
| PROD-01 | Redis Deployment CR `kind: Deployment name: redis namespace: storage`, image: `redis:7-alpine` with maxmemory=256mb LRU policy | k8s/storage/redis-deployment.yaml |
| DBHARD-06 | K8s Secret `stock-platform-secrets` namespace: storage — POSTGRES_PASSWORD, DATABASE_URL, DATABASE_URL_READONLY, DATABASE_URL_WRITER | k8s/storage/secrets.yaml |
| DBHARD-07 | RBAC role passwords present: POSTGRES_READONLY_PASSWORD, POSTGRES_WRITER_PASSWORD in `stock-platform-secrets`; actual role CREATE statements confirmed by Phase 36 completion | k8s/storage/secrets.yaml |
| DBHARD-08 | `kind: CronJob` name: postgresql-backup, schedule: `"0 4 * * *"` (daily 04:00 UTC), runs `pg_dump -Fc` to `/backups/` directory | k8s/storage/cronjob-backup.yaml |
| Phase 65 | `kind: Application` name: root-app, `spec.source.repoURL: https://github.com/tempathack/stock.git`, spec.source.path: `stock-prediction-platform/k8s/argocd`, spec.destination.server: `https://kubernetes.default.svc`, syncPolicy.automated.selfHeal=true | k8s/argocd/root-app.yaml |
| Phase 66 | `online_store: type: redis`, `connection_string: "${REDIS_HOST}:${REDIS_PORT}"` — Redis online store configured with env-substituted connection string | ml/feature_store/feature_store.yaml |

#### Gaps Found
| REQ-ID | Gap Class | Description | File Expected |
|--------|-----------|-------------|---------------|
| INFRA-07 | MISSING-REQ | Only 4 of 10 Dockerfiles are multi-stage. Multi-stage: api/Dockerfile (builder+runtime), kafka-consumer/Dockerfile (builder+runtime), frontend/Dockerfile (build+nginx), ml/Dockerfile (builder+runtime). Single-stage (NOT multi-stage): 5 flink-jobs Dockerfiles (FROM flink:1.19 — single base image), services/reddit-producer/Dockerfile (FROM python:3.10-slim — single stage). INFRA-07 requires ALL services Dockerfiles to have multi-stage builds. | services/flink-jobs/*/Dockerfile, services/reddit-producer/Dockerfile |
| DEPLOY-06 | NOTE | DEPLOY-06 originally required model-serving Deployment to use PVC. This was superseded by KServe (Phase 55) which uses MinIO S3 storageUri instead of PVC. PVC (model-artifacts-pvc) still exists for legacy CronJob use. The old PVC-based model-serving Deployment was removed as part of Phase 57 migration. This is an intentional architecture change (PVC → MinIO/KServe), not a functional gap. | k8s/ml/ |

#### Phase-Specific Checks
- INFRA-07 multi-stage Dockerfiles: PARTIAL — 4 of 10 Dockerfiles are multi-stage (api, kafka-consumer, frontend, ml); missing: services/flink-jobs/ohlcv_normalizer/Dockerfile, services/flink-jobs/indicator_stream/Dockerfile, services/flink-jobs/feast_writer/Dockerfile, services/flink-jobs/sentiment_stream/Dockerfile, services/flink-jobs/sentiment_writer/Dockerfile (all single FROM flink:1.19), services/reddit-producer/Dockerfile (single FROM python:3.10-slim)
- OBJST-01 MinIO Deployment: CONFIRMED — Deployment + ClusterIP Service in k8s/storage/minio-deployment.yaml
- OBJST-02 model-artifacts bucket: CONFIRMED — mc mb --ignore-existing local/model-artifacts in minio-init-job.yaml
- OBJST-03 drift-logs bucket: CONFIRMED — mc mb --ignore-existing local/drift-logs in minio-init-job.yaml
- OBJST-08 STORAGE_BACKEND env var toggle: CONFIRMED — `STORAGE_BACKEND: "s3"` in k8s/ml/configmap.yaml and direct env in cronjob-training.yaml; model_metadata_cache.py also reads STORAGE_BACKEND for MinIO vs local dispatch
- KSERV-05 InferenceService points to MinIO: CONFIRMED — storageUri: "s3://model-artifacts/serving/active" (primary), "s3://model-artifacts/serving/canary" (canary)
- DEPLOY-03 training CronJob: CONFIRMED — k8s/ml/cronjob-training.yaml (weekly-training, Sunday 03:00 UTC)
- DEPLOY-04 drift check CronJob: CONFIRMED — k8s/ml/cronjob-drift.yaml (daily-drift, weekdays 22:00 UTC)
- DEPLOY-07 deploy-all.sh ML phases 17–25 uncommented: CONFIRMED — Phase 33 (ML Docker build), Phase 34 (ML CronJobs: kubectl apply cronjob-training.yaml, cronjob-drift.yaml), Phase 20 (Kubeflow Pipelines install), Phase 54 (KServe), Phase 55 (InferenceService) are all active uncommented commands in scripts/deploy-all.sh
- PROD-01 Redis K8s manifest: CONFIRMED — k8s/storage/redis-deployment.yaml (redis:7-alpine, 256mb maxmemory, LRU policy)
- DBHARD-08 pg_dump CronJob: CONFIRMED — k8s/storage/cronjob-backup.yaml (postgresql-backup, daily 04:00 UTC, pg_dump -Fc)
- Phase 65 Argo CD Application CR: CONFIRMED — repoURL: https://github.com/tempathack/stock.git; app-of-apps pattern with root-app.yaml + 8 child Application CRs (app-ml.yaml, app-storage.yaml, app-flink.yaml, app-frontend.yaml, app-ingestion.yaml, app-kafka.yaml, app-monitoring.yaml, app-processing.yaml)
- Phase 66 Feast feature_store.yaml Redis online store: CONFIRMED — online_store: type: redis, connection_string: "${REDIS_HOST}:${REDIS_PORT}"

---

## Consolidated Gap Table

*Aggregated from all 6 domain sections by Plan 73-07 (Wave 2 final step). Sorted by gap class severity.*

| REQ-ID | Gap Class | Description | Domain | File Expected | Action Needed |
|--------|-----------|-------------|--------|---------------|---------------|
| INFRA-07 | MISSING-REQ | 6 of 10 Dockerfiles are single-stage (not multi-stage). Single-stage: 5 flink-jobs Dockerfiles (FROM flink:1.19) and services/reddit-producer/Dockerfile (FROM python:3.10-slim). Multi-stage Dockerfiles (confirmed): api, kafka-consumer, frontend, ml. INFRA-07 requires ALL service Dockerfiles to be multi-stage. | 6-Infrastructure | services/flink-jobs/*/Dockerfile, services/reddit-producer/Dockerfile | Convert single-stage Dockerfiles to multi-stage (builder + runtime) |
| MODEL-BAGGING | MISSING-REQ | BaggingRegressor mentioned in Phase 13 plan task description but NOT present in ml/models/model_configs.py; TREE_MODELS has 6 entries (RF, GB, HistGB, ExtraTrees, DT, AdaBoost) — BaggingRegressor absent | 2-ML Pipeline | ml/models/model_configs.py | Add BaggingRegressor to model_configs.py TREE_MODELS or document intentional omission |
| PROD-04 | NOTE | Rate limiting implemented via custom RateLimitMiddleware (sliding window, NOT slowapi library). Functionally equivalent; per-IP per-route 429+Retry-After behavior matches spec. Library differs from plan spec but is not a functional gap. | 1-API | services/api/app/main.py | No action required — document as intentional implementation choice |
| MON-09 | MINOR | promtail pipeline_stages uses `cri: {}` (CRI format parser) — not an explicit JSON structlog parsing stage; structured JSON fields are parsed at CRI layer, not a dedicated json stage | 5-Observability | k8s/monitoring/promtail-configmap.yaml | Add explicit JSON pipeline stage if structured field extraction is needed |
| MON-10 | MINOR | Loki datasource in Grafana has no `uid:` field set (unlike Prometheus which has `uid: prometheus`); prevents dashboard panels from referencing Loki by UID | 5-Observability | k8s/monitoring/grafana-datasource-configmap.yaml | Add `uid: loki` to Loki datasource ConfigMap entry |
| DEPLOY-06 | NOTE | DEPLOY-06 originally required model-serving Deployment to use PVC. Superseded by KServe (Phase 55): serving uses `s3://model-artifacts/serving/active` MinIO storageUri. model-artifacts-pvc still exists for ML CronJob local use. Intentional architecture evolution. | 6-Infrastructure | k8s/ml/ | No action required — intentional architecture change (PVC → MinIO/KServe) |

Gap classes:
- **CRITICAL** — Required by v1/v1.1/v2/v3 spec, no implementation found
- **MISSING-REQ** — Required feature present but deviates from spec (partial implementation or wrong library)
- **MISSING-TEST** — Implementation exists but no test coverage
- **STUB** — File exists but contains placeholder (pass, return None, TODO, NotImplementedError)
- **ORPHANED** — Assigned in traceability, no SUMMARY or code evidence found
- **NOTE** — Implementation differs from plan spec but is functionally equivalent; no remediation required
- **MINOR** — Low-severity configuration gap; non-blocking

**Summary by class:**
- CRITICAL: 0
- MISSING-REQ: 2 (INFRA-07, MODEL-BAGGING)
- MISSING-TEST: 0
- STUB: 0
- NOTE: 2 (PROD-04, DEPLOY-06)
- MINOR: 2 (MON-09, MON-10)

---

## Audit Sign-Off

- [x] All 6 domain sections populated by Wave 2 auditors
- [x] Consolidated Gap Table updated
- [x] YAML frontmatter counts updated (requirements_verified, gaps_critical, etc.)
- [ ] Phase 70 TBD-xx requirement IDs formalized into permanent IDs (deferred — TBD-01–05 are functionally confirmed by Domain 2 and Domain 1 audits)
- [x] Tech debt items confirmed against code (no accidental deferred → critical reclassification — all Tech Debt Register items are confirmed deferred or superseded by architecture evolution)
- [x] Phases 7–16, 23–57 ORPHANED items classified by domain auditors via code inspection — Domain auditors (1–6) confirmed the vast majority of ORPHANED items as implemented in code; ORPHANED status reflects documentation gap (no SUMMARY.md files for phases 7–16, 23–57), NOT implementation gaps
