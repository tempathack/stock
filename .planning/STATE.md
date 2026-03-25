---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Phases — Production-Ready
status: unknown
stopped_at: Completed 62-04-PLAN.md
last_updated: "2026-03-25T14:07:15.202Z"
progress:
  total_phases: 62
  completed_phases: 14
  total_plans: 142
  completed_plans: 40
---

# STATE.md — Project Memory

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-18)

**Core value:** The winner ML model is always the best-performing, drift-aware regressor — automatically retrained and redeployed whenever prediction quality degrades.
**Current focus:** Phase 62 — playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard

## Current Status

- **Active phase:** v1.1 complete
- **Phase name:** Milestone v1.1 Production-Ready Complete
- **Phase plans:** 50/50 phases complete
- **Overall progress:** 50 / 50 phases complete

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

## Last Session

- **Stopped at:** Completed 62-04-PLAN.md
- **Timestamp:** 2026-03-22T13:30:00Z

## Notes

(Add notes here as work progresses)

### Roadmap Evolution

- Phase 58 added: Fix docker-compose runtime: kafka-consumer configurable broker + ml-pipeline entrypoint fix
- Phase 59 added: Minikube E2E validation: start cluster, deploy full stack, run ingest-train-serve flow

- Phase 60 added: Fix model_name unknown in predict response — fetch metadata from MinIO or DB on API startup
