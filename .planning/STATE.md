---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
stopped_at: Completed Phase 13
last_updated: "2026-03-19T23:30:00.000Z"
progress:
  total_phases: 30
  completed_phases: 13
  total_plans: 29
  completed_plans: 29
---

# STATE.md — Project Memory

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-18)

**Core value:** The winner ML model is always the best-performing, drift-aware regressor — automatically retrained and redeployed whenever prediction quality degrades.
**Current focus:** Phase 14 — Distance, SVM & Neural Models

## Current Status

- **Active phase:** 14
- **Phase name:** Distance, SVM & Neural Models
- **Overall progress:** 13 / 30 phases complete

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
| 14 | Distance, SVM & Neural Models | Not started | — |
| 15 | Evaluation Framework & Model Selection | Not started | — |
| 16 | SHAP Explainability | Not started | — |
| 17 | Kubeflow Pipeline — Data & Feature Components | Not started | — |
| 18 | Kubeflow Pipeline — Training & Eval Components | Not started | — |
| 19 | Kubeflow Pipeline — Selection, Persistence & Deployment | Not started | — |
| 20 | Kubeflow Pipeline — Full Definition & Trigger | Not started | — |
| 21 | Drift Detection System | Not started | — |
| 22 | Drift Auto-Retrain Trigger | Not started | — |
| 23 | FastAPI Prediction & Model Endpoints | Not started | — |
| 24 | FastAPI Market Endpoints | Not started | — |
| 25 | React App Bootstrap & Navigation | Not started | — |
| 26 | Frontend — /models Page | Not started | — |
| 27 | Frontend — /forecasts Page | Not started | — |
| 28 | Frontend — /dashboard Page | Not started | — |
| 29 | Frontend — /drift Page | Not started | — |
| 30 | Integration Testing & Seed Data | Not started | — |

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

## Last Session

- **Stopped at:** Completed Phase 11 — Lag Features & Transformer Pipelines
- **Timestamp:** 2026-03-19T21:00:00Z

## Notes

(Add notes here as work progresses)
