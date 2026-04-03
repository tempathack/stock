---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Phases — Production-Ready
status: unknown
stopped_at: Completed 90-02-PLAN.md
last_updated: "2026-04-03T10:05:24.112Z"
progress:
  total_phases: 63
  completed_phases: 26
  total_plans: 144
  completed_plans: 60
---

# STATE.md — Project Memory

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-18)

**Core value:** The winner ML model is always the best-performing, drift-aware regressor — automatically retrained and redeployed whenever prediction quality degrades.
**Current focus:** Phase 90 — debezium-cdc-and-elasticsearch-integration

## Current Status

- **Active phase:** v3.0 milestone planned — ready to execute Phase 64
- **Phase name:** Phase 64 — TimescaleDB OLAP (next)
- **Phase plans:** 63/69 phases complete (6 new phases added: 64–69)
- **Overall progress:** 63 / 69 phases complete

## v3.0 New Phases

| Phase | Name | Technology | Status |
|-------|------|-----------|--------|
| 64 | TimescaleDB OLAP — Continuous Aggregates & Compression | TimescaleDB | Planned |
| 65 | Argo CD — GitOps Deployment Pipeline | Argo CD | Planned |
| 66 | Feast — Production Feature Store | Feast | Planned |
| 67 | Apache Flink — Real-Time Stream Processing | Apache Flink | Planned |
| 68 | E2E Integration — v3.0 Stack Validation | All v3.0 | Planned |
| 69 | Frontend — /analytics Page | React + MUI | Complete (2/2 plans) |

## Phase Completion Log

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 1 | Repo & Folder Scaffold | Complete (3/3 plans) | 2026-03-18 |
| 2 | Minikube & K8s Namespaces | Complete (2/2 plans) | 2026-03-18 |
| 3 | FastAPI Base Service | Complete (3/3 plans) | 2026-03-19 |
| 4 | PostgreSQL + TimescaleDB | Complete (3/3 plans) | 2026-03-19 |
| 5 | Kafka via Strimzi | Complete (2/2 plans) | 2026-03-19 |
| 6 | Yahoo Finance Ingestion Service | Complete (2/2 plans) | 2026-03-19 |
| 7 | FastAPI Ingestion Endpoints | Complete (1/1 plans) | 2026-03-19 |
| 8 | K8s CronJobs for Ingestion | Complete (1/1 plans) | 2026-03-19 |
| 9 | Kafka Consumers — Batch Writer | Complete (2/2 plans) | 2026-03-19 |
| 10 | Technical Indicators | Complete (4/4 plans) | 2026-03-19 |
| 11 | Lag Features & Transformer Pipelines | Complete (2/2 plans) | 2026-03-19 |
| 12 | Linear & Regularized Models | Complete (3/3 plans) | 2026-03-19 |
| 13 | Tree-Based & Boosting Models | Complete (2/2 plans) | 2026-03-19 |
| 14 | Distance, SVM & Neural Models | Complete (2/2 plans) | 2026-03-19 |
| 15 | Evaluation Framework & Model Selection | Complete (3/3 plans) | 2026-03-20 |
| 16 | SHAP Explainability | Complete (1/1 plans) | 2026-03-20 |
| 17 | Kubeflow Pipeline — Data & Feature Components | Complete (2/2 plans) | 2026-03-20 |
| 18 | Kubeflow Pipeline — Training & Eval Components | Complete (2/2 plans) | 2026-03-20 |
| 19 | Kubeflow Pipeline — Selection, Persistence & Deployment | Complete (2/2 plans) | 2026-03-20 |
| 20 | Kubeflow Pipeline — Full Definition & Trigger | Complete (2/2 plans) | 2026-03-20 |
| 21 | Drift Detection System | Complete (2/2 plans) | 2026-03-20 |
| 22 | Drift Auto-Retrain Trigger | Complete (1/1 plans) | 2026-03-20 |
| 23 | FastAPI Prediction & Model Endpoints | Complete (1/1 plans) | 2026-03-20 |
| 24 | FastAPI Market Endpoints | Complete (1/1 plans) | 2026-03-21 |
| 25 | React App Bootstrap & Navigation | Complete | 2026-03-21 |
| 26 | Frontend — /models Page | Complete | 2026-03-21 |
| 27 | Frontend — /forecasts Page | Complete | 2026-03-21 |
| 28 | Frontend — /dashboard Page | Complete | 2026-03-22 |
| 29 | Frontend — /drift Page | Complete | 2026-03-22 |
| 30 | Integration Testing & Seed Data | Complete (5/5 plans) | 2026-03-23 |
| 31 | Live Model Inference API | Complete (3/3 plans) | 2026-03-23 |
| 32 | Frontend Live Data Integration | Complete (2/2 plans) | 2026-03-23 |
| 33 | ML Pipeline Container & Config | Complete (2/2 plans) | 2026-03-23 |
| 34 | K8s ML CronJobs & Model Serving | Complete (3/3 plans) | 2026-03-23 |
| 35 | Alembic Migration System | Complete (2/2 plans) | 2026-03-23 |
| 36 | Secrets Management & DB RBAC | Complete (2/2 plans) | 2026-03-23 |
| 37 | Prometheus Metrics Instrumentation | Complete (2/2 plans) | 2026-03-23 |
| 38 | Grafana Dashboards & Alerting | Complete (3/3 plans) | 2026-03-23 |
| 39 | Structured Logging & Aggregation | Complete (2/2 plans) | 2026-03-23 |
| 40 | SQLAlchemy Connection Pooling | Complete (2/2 plans) | 2026-03-23 |
| 41 | Database Backup Strategy | Complete (1/1 plans) | 2026-03-23 |
| 42 | Ensemble Stacking | Complete (2/2 plans) | 2026-03-23 |
| 43 | Multi-Horizon Predictions | Complete (3/3 plans) | 2026-03-24 |
| 44 | Feature Store | Complete (2/2 plans) | 2026-03-24 |
| 45 | WebSocket Live Prices | Complete (2/2 plans) | 2026-03-24 |
| 46 | Backtesting UI | Complete (2/2 plans) | 2026-03-24 |
| 47 | Redis Caching Layer | Complete (2/2 plans) | 2026-03-24 |
| 48 | Rate Limiting & Deep Health Checks | Complete (2/2 plans) | 2026-03-24 |
| 49 | A/B Model Testing | Complete (2/2 plans) | 2026-03-24 |
| 50 | Export & Mobile Responsive | Complete (2/2 plans) | 2026-03-24 |

## Decisions

- **Phase 70 Plan 01:** run_in_threadpool wraps synchronous Feast Redis client so get_streaming_features() is safe to call from async FastAPI handlers
- **Phase 70 Plan 01:** available=True only when at least one of ema_20/rsi_14/macd_signal is non-None — handles Flink job not yet producing data
- **Phase 70 Plan 01:** STREAMING_FEATURES_TTL=5 declared locally in market.py; separate from MARKET_INDICATORS_TTL=30
- **Phase 1 Plan 01:** Created __init__.py for all ml/ subdirectories to ensure importability as Python packages
- **Phase 1 Plan 01:** Used minimal stub pattern (docstring + future annotations only) per specification
- [Phase 01]: Replaced full docker-compose.yml with stub-only definitions (image+ports) per plan specification
- [Phase 01]: Used stdlib LoggerFactory instead of PrintLoggerFactory for filter_by_level compatibility
- [Phase 02]: Used 120s timeout for kubectl wait node readiness
- [Phase 02]: Plain echo output with === separators, no colour codes for CI compatibility
- [Phase 02]: check_command function in setup-minikube.sh, inline checks in deploy-all.sh
- [Phase 02 Plan 02]: No code changes needed -- scripts from Plan 01 executed correctly on first run against live cluster
- [Phase 03 Plan 01]: Used lifespan context manager (not deprecated on_startup/on_shutdown)
- [Phase 03 Plan 01]: Added -p no:logfire to pytest.ini to work around broken logfire plugin in environment
- [Phase 03 Plan 02]: Used imagePullPolicy: Never for local Minikube development (no registry needed)
- [Phase 03 Plan 02]: Installed curl in runtime Docker stage for HEALTHCHECK command
- [Phase 03 Plan 02]: Copied /usr/local/bin from builder to ensure uvicorn binary available in runtime stage
- [Phase 04]: Used dry-run=client -o yaml | kubectl apply pattern for idempotent Secret and ConfigMap creation
- [Phase 04]: Removed phantom postgres-service.yaml reference from deploy-all.sh — Service is embedded in postgresql-deployment.yaml
- [Phase 04]: Corrected deploy-all.sh file names: postgres-* prefix -> postgresql-*, postgres-configmap.yaml -> configmap.yaml
- [Phase 04-01]: CREATE EXTENSION without CASCADE: TimescaleDB image has no unmet dependencies; explicit is more predictable
- [Phase 04-01]: Transaction wrapping (BEGIN/COMMIT) in init.sql prevents half-initialized database state
- [Phase 04-01]: updated_at trigger on stocks table provides database-level updated_at guarantee
- [Phase 04-03]: No file changes needed in Plan 03 — artefacts from Plans 01 and 02 deployed correctly on first run
- [Phase 04-03]: Human checkpoint used as final DB gate — automated smoke tests cover CI, human visual confirms full schema correctness
- [Phase 05]: Strimzi operator YAML downloaded and committed for offline reproducibility (not fetched at runtime)
- [Phase 05]: Used targeted sed (namespace: myproject -> storage) to avoid replacing unrelated namespace refs
- [Phase 05]: Operator install in setup-minikube.sh with 300s wait; workloads in deploy-all.sh (established pattern)
- [Phase 05-02]: Increased Strimzi operator memory limit to 512Mi and entity operator to 384Mi for Minikube stability
- [Phase 05-02]: Human checkpoint used as final Kafka gate -- 6-check verification covers operator, broker, entity operator, both topics produce/consume
- [Phase 06-01]: Used yfinance.download with MultiIndex column droplevel(1) for yfinance >= 1.0 compatibility
- [Phase 06-01]: Tenacity retry targets requests exceptions (ConnectionError, Timeout, HTTPError) not yfinance-specific
- [Phase 06-01]: Volume=0 explicitly valid per must_haves (pre-market/after-hours bars)
- [Phase 06]: Used defaultdict grouping by ticker for batched flush instead of itertools.groupby
- [Phase 07]: Endpoints return 502 with structured detail on Yahoo Finance or Kafka failures (not 500)
- [Phase 07]: IngestRequest body is optional — omitting body uses default ticker list from settings
- [Phase 07]: Zero records fetched returns 200 (completed) with counts=0; Kafka producer not instantiated
- [Phase 10]: Hand-rolled pandas/numpy for all 14 indicator families — no TA-Lib or pandas-ta
- [Phase 16]: Three-tier explainer routing: TreeExplainer for tree/boosters, LinearExplainer for linear family, KernelExplainer fallback for distance/neural
- [Phase 16]: SHAP results stored as JSON (shap_importance.json + shap_values.json) in same registry folder as pipeline.pkl
- [Phase 16]: KernelExplainer capped at 200 samples + kmeans(50) background for compute tractability
- [Phase 16]: Created numba shim in venv to resolve shap 0.51 / numpy 2.4 compatibility (numba 0.64 requires numpy<2.0)
- [Phase 10]: Wilder's smoothing (EWM alpha=1/period) for RSI and ATR
- [Phase 10]: _true_range shared helper used by both compute_atr and compute_adx
- [Phase 10]: OBV first row is NaN due to close.diff() — tests skip first row for comparison
- [Phase 10]: Rolling volatility annualized with sqrt(252); VWAP is cumulative (not session-reset)
- [Phase 10]: compute_all_indicators orchestrator calls all 14 functions and adds 27 columns
- [Phase 12]: Train each model with all 3 scaler variants (standard, quantile, minmax) — 18 runs total
- [Phase 12]: RandomizedSearchCV for hyperparameter tuning (not Optuna) with TimeSeriesSplit as cv
- [Phase 12]: Search spaces: Ridge/Lasso alpha logspace, ElasticNet alpha+l1_ratio, Huber epsilon linspace
- [Phase 12]: LinearRegression and BayesianRidge skip tuning (no configurable hyperparameters)
- [Phase 12]: Results stored as JSON artifacts to disk — DB persistence deferred to Phase 15
- [Phase 12]: Pipeline structure: Pipeline([("scaler", ...), ("model", ...)]) — scaler fits inside CV folds
- [Phase 12]: Kubeflow component stubs left untouched — those are Phases 17–19
- [Phase 12]: register_model_family extensibility pattern for Phases 13–14 to add tree/neural configs
- [Phase 10]: 54 tests covering all indicator families + orchestrator, 0.84s runtime
- [Phase 11]: Target is percentage return (pct_change), not raw future price
- [Phase 11]: Lags and rolling stats on close column only
- [Phase 11]: dropna() removes both warm-up NaN rows and tail NaN rows (FEAT-21)
- [Phase 11]: QuantileTransformer uses output_distribution="normal" for regression compatibility
- [Phase 11]: build_scaler_pipeline factory returns Pipeline([('scaler', Scaler)]) — model appended in Phase 12
- [Phase 11]: Had to force-reinstall scipy (corrupt .pyd binary on Windows) to fix sklearn import
- [Phase 13]: TREE_MODELS dict with 6 sklearn tree/ensemble regressors + search spaces
- [Phase 13]: BOOSTER_MODELS dict with conditional imports (xgboost, lightgbm, catboost)
- [Phase 13]: All boosters use verbose=0/-1 to suppress training output
- [Phase 13]: RF and GBM get n_iter=50; other tree models use default 30
- [Phase 13]: All tree models set random_state=42 for reproducibility
- [Phase 13]: register_model_family("tree", TREE_MODELS) at module load; boosters auto-registered if available
- [Phase 13]: train_tree_models() supports include_boosters=False flag; train_all_models() combines linear + tree
- [Phase 13]: Upgraded xgboost→3.2.0, lightgbm→4.6.0, catboost→1.2.10, pyarrow→23.0.1 for NumPy 2.x compat
- [Phase 11]: 41 tests (27 lag/rolling/target/drop + 14 scaler pipeline), 6.08s runtime
- [Phase 17]: Components are pure Python functions (not KFP containers) — @dsl.component wrapping deferred to Phase 20
- [Phase 17]: Data passes as pd.DataFrame in-process; Parquet serialization deferred to Phase 20
- [Phase 17]: DBSettings dataclass uses os.environ.get() defaults matching K8s storage-config ConfigMap
- [Phase 17]: load_ticker_data uses parameterized SQL (%s placeholders) — no string interpolation
- [Phase 17]: feature_engineer processes each ticker independently to prevent cross-ticker contamination
- [Phase 17]: label_generator target computed per-ticker via shift(-horizon) to prevent leakage
- [Phase 17]: Tickers with empty/insufficient data skipped with warning log, not error
- [Phase 17]: KFP standalone manifest is scaffold only (ConfigMap reference to v2.3.0) — not applied to cluster
- [Phase 17]: Fixed shap/numba import crash (numba requires numpy<2.0) with lazy import in evaluation/__init__.py and explainer.py
- [Phase 17]: 43 new tests (18 data_loader + 11 feature_engineer + 14 label_generator), 285 total non-shap tests passing
- [Phase 18]: Components are pure Python functions matching Phase 17 pattern — @dsl.component wrapping deferred to Phase 20
- [Phase 18]: prepare_training_data() orchestrates feature engineering + label generation + train/test split in one call
- [Phase 18]: train_all_models_pipeline() delegates to existing train_all_models() and wraps results with registry_dir param
- [Phase 18]: generate_cv_report() produces JSON comparison of fold metrics across all models
- [Phase 18]: evaluate_models() wraps rank_models() + generates RankedModel list for downstream components
- [Phase 18]: generate_comparison_report() produces JSON model comparison with metrics, ranking, and stability
- [Phase 30]: Completed integration testing and seed data — all 5 plans executed successfully
- [Phase 31–50 Planning]: Phases 31–50 designed as v1.1 milestone; 4 waves (Foundation, Observability, Features, Hardening)
- [Phase 31–50 Planning]: Plain K8s CronJobs for ML training/drift (Phase 33–34); KFP containerization deferred to v2
- [Phase 31–50 Planning]: Phase 31 adds live inference with raw psycopg2 (matching market_service.py); SQLAlchemy migration deferred to Phase 40
- [Phase 31–50 Planning]: User auth, watchlists, alerts, sentiment data, sector models, portfolio optimization deferred to v2
- [Phase 31–50 Planning]: 7 new requirement domains added: LIVE-, DEPLOY-, MON-, DBHARD-, ADVML-, FENH-, PROD-
- [Phase 19]: KF-09 (explainability) and KF-10/KF-11 (winner selection + persistence) already complete from Phases 15-16 — no changes needed
- [Phase 19]: Three new ModelRegistry methods: activate_model(), deactivate_all(), get_active_model() for is_active tracking
- [Phase 19]: is_active is distinct from is_winner — a model can be winner but not yet deployed (pre-deployment) or active but not latest winner (between retrain cycles)
- [Phase 19]: deploy_winner_model() orchestrates: find winner → deactivate all → copy artifacts to serving dir → write serving_config.json → activate in registry
- [Phase 19]: Serving directory is flat (pipeline.pkl, metadata.json, features.json, SHAP files, serving_config.json) — flattened from registry versioned layout
- [Phase 19]: Deployment is idempotent — serving dir cleared via shutil.rmtree before each deploy
- [Phase 19]: Integration test chains select_and_persist_winner → explain_top_models → deploy_winner_model with round-trip pipeline.predict() validation
- [Phase 19]: SHAP-dependent integration tests guarded with _shap_available flag (numba/numpy 2.x incompatibility in test env)
- [Phase 19]: 21 new tests (8 registry activation + 10 deployer + 3 integration), 46 phase-specific tests passing
- [Phase 20]: Two-layer pipeline — pure Python orchestrator (run_training_pipeline) + KFP DSL wrapper (compile_kfp_pipeline)
- [Phase 20]: Parquet serialization via pyarrow for inter-component data transfer in KFP mode; in-memory passing for local orchestrator
- [Phase 20]: PipelineRunResult dataclass captures full audit trail (run_id, timestamps, steps_completed, winner_info, deploy_info)
- [Phase 20]: _rebuild_pipelines() reconstructs fitted sklearn Pipelines from TrainingResult list for selection/explanation steps
- [Phase 20]: trigger_retraining() entry point with reason tracking (manual/data_drift/prediction_drift/concept_drift/scheduled)
- [Phase 20]: Retraining log appended as JSONL to {registry_dir}/runs/retraining_log.jsonl
- [Phase 20]: DBSettings import uses TYPE_CHECKING guard to avoid psycopg2 requirement at module level
- [Phase 20]: components/__init__.py uses graceful psycopg2 import fallback for data_loader exports
- [Phase 20]: 22 new tests (8 serialization + 8 training pipeline + 6 drift pipeline); integration tests confirmed passing but slow (~10min for full model suite)
- [Phase 21]: Three detector classes: DataDriftDetector (KS-test + PSI), PredictionDriftDetector (error multiplier), ConceptDriftDetector (RMSE degradation)
- [Phase 21]: DriftResult dataclass as common return type for all detectors with severity levels (none/low/medium/high)
- [Phase 21]: PSI hand-rolled with quantile-based binning and clipping (no external drift library)
- [Phase 21]: DriftMonitor orchestrates all three detectors in a single check() call → DriftCheckResult
- [Phase 21]: DriftLogger persists events to JSONL file; DB persistence gated behind psycopg2 availability
- [Phase 21]: evaluate_and_trigger() bridges detection → logging → trigger_retraining() with auto_retrain flag
- [Phase 21]: 36 new tests (20 detector + 7 monitor + 9 trigger), all passing in ~35s
- [Phase 22]: evaluate_and_trigger() extended with regenerate_predictions parameter for post-retrain prediction refresh
- [Phase 22]: predictor.py generates predictions from active serving directory (pipeline.pkl + features.json + metadata.json)
- [Phase 22]: save_predictions() writes latest.json to registry predictions/ folder
- [Phase 22]: 7 new predictor tests + 9 trigger tests updated, 43 drift-related tests pass in ~10s
- [Phase 23]: Four new endpoints: GET /predict/{ticker}, GET /predict/bulk, GET /models/comparison, GET /models/drift
- [Phase 23]: File-based service layer (prediction_service.py) reads cached predictions, model metadata, and drift logs
- [Phase 23]: /predict/bulk registered before /{ticker} to prevent path variable capture of "bulk"
- [Phase 23]: Protected namespaces disabled on schemas with model_name field (Pydantic v2 compat)
- [Phase 23]: 25 new API tests (7 predict + 8 models + 10 service), 74 total API tests passing
- [Phase 24]: DB-backed endpoints — market overview reads from PostgreSQL via LATERAL join; indicators reuse ml.features.indicators
- [Phase 24]: Graceful degradation — get_market_overview returns [] and get_ticker_indicators returns None when DB unavailable
- [Phase 24]: psycopg2 lazy import inside functions so API starts even without psycopg2
- [Phase 24]: NaN/inf → None sanitization for JSON serialization of indicator values
- [Phase 24]: Added repo root to services/api/tests/conftest.py sys.path so ml.* imports work from API test directory
- [Phase 24]: 14 new tests (7 router + 7 service), all passing
- [Phase 58]: Changed KAFKA_BOOTSTRAP_SERVERS default to kafka:9092 — K8s ConfigMap overrides at runtime, no K8s regression
- [Phase 58]: Used tickers_str = args.tickers or os.environ.get('TICKERS') in __main__ — minimal diff, preserves CLI-arg precedence
- [Phase 59]: SKIP_KSERVE_WAIT=true env var guards Phase 55 kubectl wait — backward-compatible, default false
- [Phase 59]: stock-api Docker build added before Phase 3 FastAPI kubectl apply — matches kafka-consumer/ml-pipeline pattern
- [Phase 59]: KServe ClusterServingRuntime container must be named 'kserve-container' not 'mlserver'
- [Phase 59]: API Docker build context must be project root to include ml/features for KServe inference
- [Phase 59]: Model predicts percentage return; convert to abs price via last_close * (1 + return)
- [Phase 59]: cronjob-drift.yaml was missing TICKERS, POSTGRES_PASSWORD, POSTGRES_USER env vars — added to fix drift job execution
- [Phase 60]: boto3 sync call wrapped in asyncio.to_thread() — boto3 not async-native; thread pool avoids blocking event loop
- [Phase 60]: os.environ used in _sync_fetch_from_minio (runs in thread pool, cannot use FastAPI DI); value matches Settings.MINIO_SERVING_PREFIX default
- [Phase 60]: Model metadata is cosmetic — graceful degradation on MinIO+DB failure logs WARNING, API always starts
- [Phase 60]: minio-secrets copied from storage to ingestion namespace — K8s secretRef cannot reference cross-namespace Secrets
- [Phase 60]: Stock-api image rebuilt in minikube Docker context to include Plan 01 model_metadata_cache.py — pre-Plan-01 image was running
- [Phase 60]: minio-secrets copied from storage to ingestion namespace — K8s secretRef cannot reference cross-namespace Secrets
- [Phase 60]: ConfigMap carries MINIO_ENDPOINT/BUCKET/PREFIX; secretRef injects MINIO_ROOT_USER and MINIO_ROOT_PASSWORD matching boto3 env var names
- [Phase 61]: Drift page heading is 'Drift Monitoring' not 'Drift Monitor' — spec corrected to match actual PageHeader title
- [Phase 61]: backtest.spec.ts uses http://localhost:8000/backtest/** (specific origin) to avoid intercepting Vite source module http://localhost:3000/src/pages/Backtest.tsx
- [Phase 61]: fixture_ prefix in model_name fields distinguishes E2E fixture data from mock fallback values
- [Phase 61]: Playwright LIFO route matching: routes registered LAST match FIRST; broad catch-alls must be registered before specific routes so specific ones win (predict/** before predict/bulk**)
- [Phase 61]: Serial mode for dashboard.spec.ts: 8 parallel browser instances overwhelm single Vite dev server; test.describe.configure({ mode: 'serial' }) required
- [Phase 61]: fixture_stacking_ensemble_meta_ridge asserted via StockShapPanel after row click — ForecastTable does not render model_name column
- [Phase 61]: Use .first() on getByText for tickers that appear in both desktop table td and mobile card span
- [Phase 61]: DriftTimeline renders label 'Data' from DRIFT_TYPE_STYLES map not raw 'data_drift' — assert on rendered label
- [Phase 61]: Serial mode required for models.spec.ts (same pattern as dashboard.spec.ts) — parallel overload of Vite dev server when multiple specs run together
- [Phase 61]: backtest.spec.ts uses http://localhost:8000/backtest/** (specific origin) to avoid Vite source module interception
- [Phase 61]: All 5 spec files now use serial mode — forecasts.spec.ts was missing it, causing full suite TimeoutError
- [Phase 62]: No webServer block in playwright.infra.config.ts — infra services are already running via kubectl port-forward
- [Phase 62]: No baseURL in playwright.infra.config.ts — each spec sets its own origin via named URL exports from auth.ts
- [Phase 62]: K8S_DASHBOARD_TOKEN references KUBERNETES_DASHBOARD_TOKEN env var with no hardcoded default — must be supplied externally
- [Phase 62]: grafana.spec.ts dashboard navigation uses getByText by title (not UID) to avoid fragility; panels use .or() for version tolerance; beforeAll probe uses Playwright request API
- [Phase 62]: CodeMirror 6 input handled via .cm-content.click() + keyboard.type() — page.fill() unreliable on CodeMirror editors
- [Phase 62]: Alert tests assert rule names (HighDriftSeverity, HighAPIErrorRate, HighConsumerLag) not alert state — state depends on live metrics
- [Phase 62]: Probe checks status >= 500 (not !res.ok()) — MinIO redirects / to /login (302) which is reachable but not 'ok'
- [Phase 62]: Bucket navigation test clicks bucket row by text — avoids hardcoded /browser/{name} URL anti-pattern
- [Phase 62]: Hash-router navigation uses DOM waits not waitForURL — KFP uses /#/ routing; waitForURL does not fire on hash changes
- [Phase 62]: Two-stage skip for K8s Dashboard: missing token skips first (before HTTP probe) — ordering matters for UX
- [Phase 62]: K8s Dashboard skip messages embed exact kubectl commands (port-forward, create token, proxy) for operator self-service
- [Phase 08]: timeZone America/New_York on intraday CronJob aligns schedule with NYSE hours; historical CronJob uses UTC default for weekly quiet-window run
- [Phase 63]: beforeAll blocks placed inside each test.describe block so test.skip() scopes correctly to that suite
- [Phase 63]: dashboard.spec.ts gets 2 beforeAll blocks (Navigation + Dashboard page) — both describe blocks navigate and need live data
- [Phase 63]: drift.spec.ts guards both /models/comparison and /models/drift — ActiveModelCard needs comparison data, DriftTimeline needs drift events
- [Phase 18]: prepare_training_data() uses pd.concat().sort_index() for temporal ordering across multi-ticker DataFrames
- [Phase 18]: train_all_models_pipeline() delegates to train_all_models() then reconstructs fitted Pipelines via best_params
- [Phase 18]: generate_cv_report() is purely additive — existing evaluate_models() and generate_comparison_report() untouched
- [Phase 19]: is_active distinct from is_winner — model can win without being deployed, or be active between retrain cycles
- [Phase 19]: deploy_winner_model() supports local and S3 backends via STORAGE_BACKEND env var; serving dir cleared via shutil.rmtree for idempotency
- [Phase 20]: compile_kfp_pipeline() writes KFP v2.1.0 IR YAML directly — avoids @dsl.component inspect.getsource failure for inline closures
- [Phase 21]: DataDriftDetector uses KS-test + hand-rolled PSI; severity based on fraction of features drifted
- [Phase 21]: DriftLogger file backend always available; DB gated behind psycopg2 for importability
- [Phase 22]: evaluate_and_trigger() extended with regenerate_predictions parameter for post-retrain prediction refresh
- [Phase 22]: predictor.py generates predictions from active serving directory (pipeline.pkl + features.json + metadata.json)
- [Phase 22]: save_predictions() writes latest.json to registry predictions/ folder
- [Phase 22]: 7 new predictor tests + 9 trigger tests updated, 43 drift-related tests pass in ~10s
- [Phase 64-01]: date::timestamptz cast required in ohlcv_daily_agg for TimescaleDB DATE column in continuous aggregates (issue #6042)
- [Phase 64-01]: timescaledb.materialized_only=false set on both views for real-time tail visibility regardless of TimescaleDB version
- [Phase 64-01]: compress_after > start_offset pairs ensure safe overlap: intraday (3d vs 2h), daily (7d vs 3d)
- [Phase 64]: View name from _CANDLE_VIEW_MAP dict (not user input) — text(f-string) safe because view is whitelist-validated
- [Phase 64]: Grafana TimescaleDB password uses ${TIMESCALEDB_PASSWORD} env var substitution — K8s Secret provisioning deferred to Phase 65 GitOps
- [Phase 65]: argocd CLI installed to ~/.local/bin/ instead of /usr/local/bin/ (sudo not available in non-interactive shell)
- [Phase 65]: app-kafka destination namespace is storage — Strimzi CRs deploy into storage namespace, not a kafka namespace
- [Phase 65]: app-ml uses directory.recurse=false to exclude kserve/ and kubeflow/ subdirs from Argo CD reconciliation (operator-managed)
- [Phase 65]: Files must be pushed to origin/master before root-app sync — Argo CD reads from remote git targetRevision: HEAD
- [Phase 65]: kubectl get applications.argoproj.io required (not application) — two Application CRDs coexist: argoproj.io (Argo CD) and app.k8s.io (Kubeflow); unqualified name resolves to Kubeflow CRD
- [Phase 65]: argocd-cm server-side apply with --force-conflicts merges health check keys without overwriting existing Argo CD ConfigMap fields
- [Phase 66]: feast[postgres,redis]==0.61.0 requires numpy>=2.0.0 — bumped xgboost 3.2.0, lightgbm 4.6.0, catboost 1.2.10, shap 0.51.0 for numpy 2.x compatibility
- [Phase 66]: Feast Entity.join_key is singular str not join_keys list in Feast 0.61.0 — test corrected to use ticker.join_key
- [Phase 66]: PostgreSQLSource exposes get_table_query_string() method not .query attribute — test corrected to call method
- [Phase 66]: TTL=timedelta(days=365) on all FeatureViews — not research default 7 days — so full-year historical training data retrieval works
- [Phase 66]: Module-level alias get_historical_features = _feast_get_historical allows patch target ml.pipelines.components.feature_engineer.get_historical_features to work without internal import
- [Phase 66-02]: use_feast branch inserted BEFORE use_feature_store branch so Feast path takes precedence when explicitly enabled; exception fallback broad (except Exception) so any Feast infrastructure failure falls back silently
- [Phase 66]: Feast import guard at module level via try/except ImportError with _FEAST_AVAILABLE flag — API starts even if feast package not installed
- [Phase 66]: get_online_features module-level alias so tests can patch app.services.prediction_service.get_online_features cleanly
- [Phase 66]: feast-feature-store-config ConfigMap embeds feature_store.yaml with dollar-sign VAR placeholders — Feast resolves env vars at runtime natively
- [Phase 67]: PyFlink job split into normalizer_logic.py (pure Python) + ohlcv_normalizer.py (Flink Table API) so unit tests exercise filter logic without pyflink runtime installed
- [Phase 67]: JDBC upsert mode triggered by PRIMARY KEY (ticker, timestamp) NOT ENFORCED on sink table DDL — maps to INSERT ON CONFLICT DO UPDATE in PostgreSQL
- [Phase 67]: s3.access.key/s3.secret.key omitted from flinkConfiguration — flink-s3-fs-presto plugin resolves from AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars injected via minio-secrets secretRef
- [Phase 67]: stock-platform-secrets and minio-secrets must be copied to flink namespace in deploy-all.sh before FlinkDeployment apply — documented as inline YAML comments with exact kubectl commands
- [Phase 67]: UDAF logic extracted into indicator_udaf_logic.py (pure Python, no pyflink) — testable without Flink runtime, same pattern as normalizer_logic.py
- [Phase 67]: feast_writer Dockerfile uses Python 3.10 — Feast 0.61.0 requires Python 3.9+ but flink:1.19 ships Python 3.8
- [Phase 67]: push_batch_to_feast() defined at module level with store_path param so tests can patch FeatureStore without feast installed
- [Phase 67]: Feast tests mock sys.modules['feast'] before import to avoid feast package runtime dependency in test environment
- [Phase 67]: Use webhook.create=false for Flink Operator Helm install to avoid cert-manager certificate pressure on Minikube (cert-manager already used by Phase 54 KServe)
- [Phase 67]: MinIO flink-checkpoints prefix created via echo | mc pipe placeholder object — MinIO has no explicit subdirectory creation API
- [Phase 68]: ARGOCD_PASSWORD defaults to empty string — login tests skip gracefully when env var not set
- [Phase 68]: Flink spec probes /overview REST endpoint (not UI) for beforeAll skip — hash-routing makes UI probes unreliable
- [Phase 68]: playwright.infra.config.ts now has 7 project entries (5 original + argocd + flink-web-ui)
- [Phase 68-01]: validate/last-checked annotation patched with python3 inline heredoc (no yq dependency)
- [Phase 68-01]: Argo CD poll checks both operationState.phase=Succeeded AND sync.revision matches NEW_HEAD prefix — prevents false-positive on prior sync
- [Phase 68-01]: V3INT-05 uses updated_at column for 30-second window (not timestamp column) — avoids yfinance stale timestamp false negatives
- [Phase 69]: Move confluent_kafka and get_engine imports to module level in service files so test patch paths resolve at app.services.* attribute
- [Phase 69]: Use _dt_type alias bound at import time for isinstance checks to survive datetime module mock in unit tests
- [Phase 69-02]: OLAPCandleChart delivers 1H/1D only — 5m/4h deferred because Phase 64 created only 1h/1d TimescaleDB continuous aggregates
- [Phase 69-02]: Recharts used for candlestick chart over Lightweight Charts — Recharts already in codebase (CandlestickChart.tsx pattern), avoids second charting library
- [Phase 69-02]: useRef ring buffer (max 120 samples) for StreamLagMonitor — avoids useState re-render churn on 15s Kafka polling, caps memory
- [Phase 69-02]: Per-panel ErrorBoundary on all 5 analytics panels — fault isolation prevents single failing backend from blanking /analytics page
- [Phase 71]: BLOCKLIST applied after SP500_SET check to suppress false positives (IT, AI, DD) that are valid tickers but common English words in Reddit text
- [Phase 71]: reddit-secrets K8s Secret created manually by operator — REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET never committed to git
- [Phase 71]: window_start aliased as event_timestamp in sentiment_stream sink DDL to match Feast push column contract without rename in sentiment_writer
- [Phase 71]: sentiment_stream uses python3 (not 3.10) since no Feast dependency; sentiment_writer mirrors feast_writer pattern with only 4 value changes
- [Phase 71]: Used run_in_threadpool for synchronous Feast reads inside async WS handler
- [Phase 71]: Added FEAST_STORE_PATH to config.py Settings (Group 15) — required for FeatureStore instantiation
- [Phase 71]: useSentimentSocket is independent hook (not useWebSocket wrapper) — per-ticker WS with exponential backoff and code-1000 cleanup
- [Phase 71]: VADER compound score [-1, +1] mapped to LinearProgress [0, 100] via (score+1)/2*100 — neutral at 50% midpoint
- [Phase 71]: useSentimentSocket is an independent hook (not a useWebSocket wrapper) — single-ticker focus, exponential backoff with code-1000 cleanup suppresses reconnect storms on drawer close
- [Phase 72-01]: Dedicated flink-jobs Prometheus scrape job scoped to flink namespace avoids double-scrape confusion and gives clean job label separation
- [Phase 72-01]: Grafana Prometheus datasource UID pinned to 'prometheus' in provisioning YAML to ensure dashboard JSON uid references resolve correctly via GitOps
- [Phase 72]: Used kubectl delete+create for ConfigMap update because kubectl apply/replace left stale content in cluster
- [Phase 72]: api-health, ml-perf, kafka dashboards already had correct lowercase prometheus uid — no content changes needed
- [Phase 70]: StreamingFeaturesPanel is self-contained — calls useStreamingFeatures internally rather than receiving data as props
- [Phase 70]: Dashboard.tsx Streaming Features accordion uses defaultExpanded so panel is visible immediately when Drawer opens
- [Phase 72]: Lowercase uid='prometheus' pattern: all Grafana dashboard ConfigMaps must use this exact UID value to match pinned datasource
- [Phase 72]: Flink dashboard: kubectl delete+create required instead of apply/replace when ConfigMap was not originally managed by apply
- [Phase 70]: StreamingFeaturesPanel is self-contained — calls useStreamingFeatures internally, no prop-drilling from Dashboard.tsx
- [Phase 73]: Phase 73-01: Phases 31-57 have no SUMMARY.md files — all ~60 requirements for those phases are ORPHANED in audit (documentation gap, not implementation gap)
- [Phase 73]: Phase 73-01: v3.0 requirement domains (TSDB, GITOPS, FEAST, FLINK, V3INT, UI-RT, ALT, TBD) appear in SUMMARY.md frontmatter but absent from REQUIREMENTS.md — VERIFIED via SUMMARY evidence
- [Phase 73]: Domain 1 FastAPI API rated COMPLETE: all 12 endpoints confirmed wired to live services; PROD-04 custom RateLimitMiddleware (not slowapi) functionally equivalent
- [Phase 73-03]: streaming_features FeatureView absent by name — Phase 70 uses PushSource on technical_indicators_fv for streaming; capability confirmed, named view absent
- [Phase 73-03]: BaggingRegressor not in model_configs.py TREE_MODELS — 6 tree models present (RF, GB, HistGB, ExtraTrees, DT, AdaBoost); minor gap documented in Domain 2 audit
- [Phase 73-03]: KF-07/KF-08 orphaned in REQUIREMENTS.md but confirmed present: evaluate_models and generate_comparison_report both in ml/pipelines/components/evaluator.py
- [Phase 73]: Domain 3 Kafka/Flink audit: COMPLETE status — all 5 FlinkDeployment CRs, 5 Flink Python jobs, 4 KafkaTopic CRs, Phase 71 sentiment pipeline all confirmed
- [Phase 73]: Phase 70 STATUS CONCLUSION: COMPLETE — StreamingFeaturesPanel confirmed imported and rendered in Dashboard.tsx Drawer by code inspection
- [Phase 73]: Phase 71 STATUS: COMPLETE — SentimentPanel.tsx and useSentimentSocket.ts both exist and wired in Dashboard.tsx Drawer with exponential backoff reconnection
- [Phase 73]: Phase 72 deliverables confirmed in 73-06 audit: flink-jobs scrape job present, datasource UID pinned to lowercase prometheus, Flink dashboard at 10 panels
- [Phase 73]: INFRA-07 classified as MISSING-REQ (not CRITICAL): flink-jobs single-stage Dockerfiles (FROM flink:1.19) and reddit-producer single-stage; 4 of 10 service Dockerfiles are multi-stage; platform operates correctly
- [Phase 73]: 73-AUDIT.md complete: 0 CRITICAL gaps, 2 MISSING-REQ gaps (INFRA-07, MODEL-BAGGING), 2 MINOR gaps (MON-09/10), 2 NOTE gaps (PROD-04, DEPLOY-06); all 6 infrastructure domains confirmed
- [Phase 74]: Use row.saved_at as secondary fallback in getRowId to prevent DataGrid row deduplication with null versions
- [Phase 74]: Wrap handleSelect in useCallback with empty deps to prevent stale closure in Recharts Treemap content renderer
- [Phase 74]: 74-02: Use #FFFFFF unconditionally for treemap pct text with SVG feDropShadow filter — eliminates WCAG contrast failures on all tile colors including dark crimson AAPL #831849
- [Phase 75-01]: Used lazy import inside test body for Wave 0 RED tests to prevent collection-time ImportError blocking existing passing tests
- [Phase 75]: ArgoCD status reads from kubernetes.client.CustomObjectsApi (K8s CRD) instead of ARGOCD_TOKEN/httpx — works without a running ArgoCD HTTP API
- [Phase 75]: Feast latency cached 60s via build_key('analytics','feast','latency') to avoid timing overhead on every analytics summary request
- [Phase 75]: previous_model_rmse stored in drift event details_json JSONB dict — not a new column
- [Phase 75]: Drift.tsx null RMSE uses ?? null pattern — RetrainStatusPanel renders null as em-dash
- [Phase 75]: previous_model_rmse stored inside details_json JSONB dict (not a new column) — matches existing schema design
- [Phase 75]: Null-safe pattern established: (field as number) ?? null with conditional .toFixed(4) or em-dash rendering
- [Phase 75-04]: OOS metrics: DB has oos_ prefixed keys, local code strips correctly with k[4:] — running pod was stale; no source change needed
- [Phase 75-04]: Forecast confidence: predictions table empty (path 3) — implemented defensive constant-confidence guard mapping price spread to [0.70, 0.98]
- [Phase 76]: OLAPCandleChart uses disableClearable Autocomplete to prevent 404s from unknown tickers; freeSolo excluded
- [Phase 76-ux-polish]: Sort stocks once descending by daily_change_pct; gainers are first 5, losers are last 5 reversed
- [Phase 76-ux-polish]: TopMoversPanel placed between treemap and StockSelector, outside any Collapse — always visible
- [Phase 76-01]: null activeTicker guard: useState<string|null>(null) + activeTicker ?? '' disables query on initial Backtest mount
- [Phase 76-01]: Tooltip audit: all icon-only buttons already wrapped; ExportButtons has text labels; nav has icon+text
- [Phase 76-ux-polish]: 76-03: AVAILABLE_HORIZONS='1,7,14,30'; horizons.json seeded for immediate HorizonToggle; db_writer enriches stocks table via yfinance for Forecasts Company/Sector columns
- [Phase 77]: bulkQuery.isError alone gates ErrorFallback — marketQuery failure degrades table to em-dash, not error page
- [Phase 77]: generateMockForecasts removed from production code path — partial failure uses empty array fallback instead
- [Phase 77]: Phase 77 Plan 02: minio-s3-credentials provides AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY required by flink-s3-fs-presto; minio-secrets provides wrong env var names (MINIO_ROOT_USER/PASSWORD) — always use minio-s3-credentials for Flink checkpoint bucket access
- [Phase 78-fix-frontend-broken-page-error-states]: ErrorFallback enhanced in-place with ErrorOutlineIcon, preserving props interface so all callers get improvement automatically
- [Phase 78]: Models.tsx: 8 skeleton rows + centered ErrorFallback with PageHeader in both loading and error states
- [Phase 78]: Removed CandlestickChart entirely from Dashboard; intraday data was mock-only, replaced with dashed-border empty state
- [Phase 78]: Used void livePrices to suppress unused variable TS error while retaining WebSocket hook for wsStatus badge
- [Phase 78-04]: FeatureDistributionChart receives empty array on Drift page after mock removal — component handles gracefully without deletion
- [Phase 78-04]: retrainStatus fallback returns typed empty object instead of mock: { lastRetrainDate: null, isRetraining: false, oldModel: null, newModel: null, improvementPct: null }
- [Phase 79]: Grafana K8s Secret with secretKeyRef — placeholder base64 password in manifest, override via kubectl --dry-run pattern
- [Phase 79]: docker-compose uses ${GRAFANA_ADMIN_PASSWORD} with no default fallback to fail loudly if not set
- [Phase 80]: Remove phase prop entirely from PlaceholderCard rather than conditionally hiding the Chip badge
- [Phase 80]: Use HelpOutlineIcon with text.disabled to signal unavailable data in SystemHealthSummary metric cards
- [Phase 81]: Grafana null+nan mapping: use type=special mappings in fieldConfig.defaults to override no-data color to blue — noValue field alone only changes text, not threshold-driven color
- [Phase 81]: kubectl replace vs apply: use kubectl replace when ConfigMap was originally created without apply annotations, preventing apply from updating the resource
- [Phase 82]: thresholdsStyle.mode=line goes inside Grafana custom block; thresholds object at defaults level for SLO reference lines
- [Phase 82]: Prometheus histogram alert uses prediction_latency_seconds_bucket with sum by (le) for correct histogram_quantile aggregation
- [Phase 82]: Used 4 levels of .parent from test file path to locate stock-prediction-platform/k8s/monitoring/ root
- [Phase 82]: All 5 dashboard tests passed green immediately since plan 01 changes were already applied to grafana-dashboard-ml-perf.yaml
- [Phase 83]: No RBAC changes needed: existing ClusterRole is cluster-scoped covering all namespaces including processing
- [Phase 83]: Used ClusterIP Service (not NodePort/LoadBalancer) for kafka-consumer metrics — internal scraping only
- [Phase 84-fix-loki-alerting-datasource-misconfiguration-alert-rules-fail-to-load-from-loki]: K8S_MONITORING resolved via 4x pathlib parent from tests/ — consistent with test_dashboard_json.py pattern
- [Phase 85]: Replace ErrorFallback (red icon + text) with neutral Box for non-alarming no-data UX on Backtest page
- [Phase 85]: Use shared ExportButtons component on Backtest for consistency with Models and Forecasts pages
- [Phase 84-02]: Used uid: loki (stable, pinned) for Loki datasource — prevents auto-generated UID changes on pod restart from breaking alert rule references
- [Phase 84-02]: Alert rule datasourceUid: loki matches pinned UID — cross-link is explicit and survives Grafana restarts
- [Phase 86]: Replaced four chart-motif nav icons with PsychologyIcon/WaterDropIcon/HistoryIcon/InsightsIcon for silhouette-distinct TopNav
- [Phase 87-01]: HTTP 400 (kserve.errors.InvalidInput) on all-None features, not HTTP 503: unresolvable entity is a client error not a transient service failure
- [Phase 87-01]: FeatureStore singleton in FeastTransformer.__init__ avoids 50-200ms per-request registry fetch
- [Phase 88]: 88-01: Used useQueries for parallel horizon fetching with shared queryKeys.bulkPredictions cache keys
- [Phase 88]: 88-01: isPending (not isLoading) used for useQueries state — React Query v5 semantics
- [Phase 88]: Used relative imports in test file to avoid vitest alias configuration complexity
- [Phase 88]: Added MultiHorizonForecastRow and HorizonPrediction types as Rule 3 auto-fix for Plan 01 missing types
- [Phase 87]: Use America/New_York tz_convert(UTC) in build_entity_df_for_backtest to handle DST transitions for all prediction dates
- [Phase 87]: assert_no_future_leakage accepts empty result_df silently — no data before Feast cutoff is valid, not leakage
- [Phase 88]: ForecastTable uses flat field mapping from MultiHorizonForecastRow.horizons — columnGroupingModel with 4 groups (1-Day, 7-Day, 14-Day, 30-Day); dual-query pattern keeps useBulkPredictions(7) for ForecastRow consumers alongside useAllHorizonsPredictions
- [Phase 88-03]: useAllHorizonsPredictions queryFn returns raw BulkPredictionResponse (not wrapped { horizon, data }) — prevents cache collision with shared bulkPredictions queryKey; horizon derived from ALL_HORIZONS index in select function
- [Phase 87]: KSERVE_INFERENCE_URL must use InferenceService hostname (no -predictor suffix) to route requests through the Transformer before the Predictor
- [Phase 87]: features_pit_correct defaults to False for backward compatibility with pre-Transformer predictions
- [Phase 89]: StatementSet for dual-sink Flink job so Kafka and JDBC inserts run as a single Flink execution graph
- [Phase 89]: TUMBLE(2-min) chosen over HOP to produce non-overlapping windows matching sentiment_timeseries primary key (ticker, window_start)
- [Phase 89]: REST polling (useQuery 120s) used for sentiment timeseries — WebSocket delivers only latest scalar, history requires REST against TimescaleDB hypertable
- [Phase 89]: REST polling (useQuery 120s) used for sentiment timeseries history — WebSocket delivers only latest scalar
- [Phase 89]: SentimentTimeseriesChart wired into both WS-connected and WS-unavailable branches of SentimentPanel to prevent silent chart omission
- [Phase 90]: Elasticsearch StatefulSet uses external PVC (not volumeClaimTemplates) for simpler single-replica dev lifecycle
- [Phase 90]: PostgreSQL WAL args injected via Deployment args[] — requires pod restart after apply
- [Phase 90-02]: KafkaTopic CRs in storage namespace (Strimzi Topic Operator watches where Kafka CR lives)
- [Phase 90-02]: strimzi.io/use-connector-resources: true annotation required for KafkaConnector CR reconciliation
- [Phase 90-02]: imagePullPolicy: Never for Minikube — custom image loaded via minikube image load, no registry needed

## Last Session

- **Stopped at:** Completed 90-02-PLAN.md
- **Timestamp:** 2026-03-30T14:00:00Z

## Notes

### v3.0 Technology Integration Summary

- **Phase 64 (TimescaleDB OLAP):** No new services. Pure schema + query layer — continuous aggregates, compression, retention, candle API endpoint.
- **Phase 65 (Argo CD):** New `argocd` namespace. Replaces manual `kubectl apply` with GitOps reconciliation. App-of-Apps pattern for all existing namespaces.
- **Phase 66 (Feast):** New `ml/feature_store/` directory. Offline store = existing PostgreSQL. Online store = existing Redis. Replaces `ml/features/store.py`. Adds `feast` namespace CronJob + feature server Deployment.
- **Phase 67 (Apache Flink):** New `flink` namespace. 3 PyFlink jobs (OHLCV normalizer, indicator stream, Feast writer). New `processed-features` Kafka topic. Replaces kafka-consumer batch writer for intraday path.
- **Phase 68 (E2E):** Integration tests + Playwright spec additions for Argo CD UI and Flink Web UI.
- **Phase 69 (/analytics UI):** New React page with 5 panels: StreamHealthPanel, FeatureFreshnessPanel, OLAPCandleChart, StreamLagMonitor, SystemHealthSummary. Backed by 3 new API endpoints.

### Execution Order

Recommended wave execution:

- **Wave 1 (parallel):** Phase 64 + Phase 65 — independent, no new services touching each other
- **Wave 2 (parallel):** Phase 66 + Phase 67 — both depend on Phase 64 (TimescaleDB schema must exist for Flink upserts + Feast offline store queries)
- **Wave 3 (sequential):** Phase 68 (integration tests require 64+65+66+67 complete) → Phase 69 (UI requires Phase 68 API endpoints)

### Roadmap Evolution

- Phase 58 added: Fix docker-compose runtime: kafka-consumer configurable broker + ml-pipeline entrypoint fix
- Phase 59 added: Minikube E2E validation: start cluster, deploy full stack, run ingest-train-serve flow
- Phase 60 added: Fix model_name unknown in predict response — fetch metadata from MinIO or DB on API startup
- Phase 63 added: Fix E2E test assertions — require real API data, not mock/empty fallbacks
- Phases 64–69 added: v3.0 milestone — TimescaleDB OLAP, Argo CD GitOps, Feast feature store, Apache Flink stream processing, E2E integration, /analytics UI page
- Phase 70 added: Display Flink-computed streaming features in the dashboard
- Phase 71 added: High-frequency alternative data pipeline: news sentiment ingestion into Kafka, Flink streaming analysis, live dashboard
- Phase 72 added: Grafana debug dashboards with Flink metrics integration
- Phase 73 added: Full system scope verification and functional audit using parallel subagents
- Phase 77 added: Fix Flink pipeline health and Forecasts blank screen (ohlcv_normalizer crash-loop 1160 restarts, zero completed checkpoints, 3K+ failed checkpoints, Forecasts page blank with no error/loading state)
- Phase 78 added: Fix frontend broken-page error states — Dashboard, Models, Drift tiny error box in black void
- Phase 79 added: Grafana security hardening — change default admin/admin password
- Phase 80 added: Analytics page cleanup — remove Phase 69 placeholder badges, fix N/A green checkmarks
- Phase 81 added: Fix Grafana No-data-on-green panels — API Health Error Rate and Inference Errors
- Phase 82 added: Fix ML prediction latency alerting — 8-10s p95 threshold, verify real vs synthetic metrics
- Phase 83 added: Fix Kafka consumer metrics scraping — all consumer/writer panels showing No data
- Phase 84 added: Fix Loki alerting datasource misconfiguration
- Phase 85 added: Backtest UX polish — neutral empty state, label orphaned icon buttons
- Phase 86 added: Frontend sidebar icon differentiation
- Phase 87 added: Point-in-time correct feature serving via Feast and KServe Transformer — eliminate lookahead leakage in backtest
- Phase 88 added: Add all prediction forecasts to the table in the forecasts dashboard tab
- Phase 89 added: Live sentiment timeseries chart in Dashboard tab — Flink-streamed Reddit/news sentiment per stock, 2-min intervals, 10-hour rolling window, replaces static unavailable placeholder
- Phase 90 added: Debezium CDC and Elasticsearch integration — Debezium Connect capturing PostgreSQL WAL (predictions, drift_logs, model_registry), Kafka CDC topics, ES Sink Connector, FastAPI /search/* endpoints, React analytics updates
- Phase 92 added: Feast-powered prediction pipeline — retrain ML model on Feast features (OHLCV indicators + Reddit sentiment + Flink real-time indicators) and wire Feast online store into the API inference path
