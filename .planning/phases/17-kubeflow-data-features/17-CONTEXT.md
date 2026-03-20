# Phase 17: Kubeflow Pipeline — Data & Feature Components — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the first three steps of the 11-step Kubeflow training pipeline as standalone
Python component functions, **plus** the Kubeflow Pipelines SDK (`kfp`) infrastructure
needed to define and serialize them.

This phase does NOT deploy Kubeflow Pipelines to the cluster — KF installation
is a cluster-ops task that is orthogonal to the Python component code. The K8s
manifest for KFP standalone deployment will be scaffolded for later `kubectl apply`,
but the success criteria for this phase focus on the Python components and their tests.

### Pipeline steps owned by this phase (3 of 11)

| Step | Component | Input | Output |
|------|-----------|-------|--------|
| 1 | `data_loader` | DB connection params, ticker list | Per-ticker OHLCV DataFrames |
| 2 | `feature_engineer` | Raw OHLCV DataFrames | DataFrames with all indicators + lag features |
| 3 | `label_generator` | Feature DataFrames | Train-ready DataFrames with `target_7d` column, NaN-free |

### Files touched

- `ml/pipelines/components/data_loader.py` — **replace stub** with data loading component
- `ml/pipelines/components/feature_engineer.py` — **replace stub** with feature engineering component
- `ml/pipelines/components/label_generator.py` — **replace stub** with label generation component
- `ml/pipelines/components/__init__.py` — add exports for the 3 new components
- `ml/tests/test_data_loader.py` — **create** tests for data_loader
- `ml/tests/test_feature_engineer.py` — **create** tests for feature_engineer
- `ml/tests/test_label_generator.py` — **create** tests for label_generator
- `k8s/ml/kubeflow/kfp-standalone.yaml` — **create** KFP standalone deployment manifest (scaffold)

</domain>

<decisions>
## Decisions

### Component Architecture: Pure Python Functions (not KFP containers yet)

Each component is a **plain Python function** that orchestrates calls to the existing
`ml/features/` and `ml/features/lag_features` modules — exactly the same pattern
used by the completed Phase 15–16 components (evaluator, model_selector, explainer).

These functions will be wrapped in `@dsl.component` decorators in Phase 20 when
the full pipeline DSL is assembled. For now they are testable, importable functions
with no KFP SDK dependency — keeping the ML logic clean and framework-agnostic.

### Data Passing: DataFrames (in-process) → Parquet artifacts (Phase 20)

Within the Python orchestration layer, data passes as `pd.DataFrame` objects.
When the components are containerized in Phase 20, they will serialize to
Parquet via `dsl.Output[dsl.Dataset]`. This phase only deals with the
in-process DataFrame interface.

### data_loader: psycopg2 + pandas for DB reads

- Uses `psycopg2` (already a project dependency) with `pandas.read_sql_query()`
- Connection parameters via a settings dataclass with env-var defaults matching
  the existing `storage-config` ConfigMap (`POSTGRES_DB=stockdb`,
  `POSTGRES_USER=stockuser`, `POSTGRES_HOST=postgresql.storage.svc.cluster.local`,
  `POSTGRES_PORT=5432`)
- Queries `ohlcv_daily` table, filtering by ticker list and optional date range
- Returns a `dict[str, pd.DataFrame]` keyed by ticker symbol
- Each DataFrame has a DatetimeIndex and columns: open, high, low, close, volume

### feature_engineer: delegates to existing modules

- Calls `compute_all_indicators(df)` from `ml.features.indicators`
- Calls `compute_lag_features(df)` from `ml.features.lag_features`
- Calls `compute_rolling_stats(df)` from `ml.features.lag_features`
- Input/output: `dict[str, pd.DataFrame]` (per-ticker)
- Each DataFrame gains ~40+ indicator/lag/rolling columns

### label_generator: t+7 target with leakage prevention

- Calls `generate_target(df, horizon=7)` from `ml.features.lag_features`
- Calls `drop_incomplete_rows(df)` from `ml.features.lag_features`
- Critical: target is computed **per-ticker** to prevent cross-ticker leakage
- Output: `dict[str, pd.DataFrame]` where each DataFrame is NaN-free and has
  a `target_7d` column plus all feature columns
- Also returns `feature_names: list[str]` (all columns except the target)

### DB Settings Dataclass

```python
@dataclass
class DBSettings:
    host: str      # default: env POSTGRES_HOST or "postgresql.storage.svc.cluster.local"
    port: int      # default: env POSTGRES_PORT or 5432
    database: str  # default: env POSTGRES_DB or "stockdb"
    user: str      # default: env POSTGRES_USER or "stockuser"
    password: str  # default: env POSTGRES_PASSWORD or "devpassword123"
```

### KFP Standalone Manifest (scaffold only)

The `k8s/ml/kubeflow/kfp-standalone.yaml` will contain a reference to the
official KFP standalone deployment for Kubernetes, pinned to a stable version.
This is a scaffold — actual deployment is a cluster-ops step, not a code
deliverable.

### Test Strategy

All tests use mocked DB connections (no real PostgreSQL) and the shared
`sample_ohlcv_df` fixture from `ml/tests/conftest.py`. Tests verify:
- data_loader: SQL query construction, DataFrame shaping, error handling
- feature_engineer: all indicators applied, column count, no NaN in features
- label_generator: target column present, no NaN, no data leakage, correct row count

</decisions>

<canonical_refs>
## Canonical References

### Upstream (complete)
- `ml/features/indicators.py` — `compute_all_indicators(df)` → 14 indicator families
- `ml/features/lag_features.py` — `compute_lag_features(df)`, `compute_rolling_stats(df)`, `generate_target(df, horizon)`, `drop_incomplete_rows(df)`
- `ml/features/transformations.py` — `SCALER_VARIANTS`, `build_scaler_pipeline(variant)`
- `ml/features/__init__.py` — re-exports all feature functions
- `db/init.sql` — `ohlcv_daily(ticker, date, open, high, low, close, adj_close, volume, vwap)` table
- `services/kafka-consumer/consumer/config.py` — `DATABASE_URL` pattern
- `services/kafka-consumer/consumer/db_writer.py` — `psycopg2.pool` connection pattern
- `k8s/storage/configmap.yaml` — `POSTGRES_DB`, `POSTGRES_USER`

### Peer components (complete, pattern reference)
- `ml/pipelines/components/evaluator.py` — thin wrapper delegating to `ranking.rank_models()`
- `ml/pipelines/components/model_trainer.py` — `train_single_model()`, `train_linear_models()`, etc.
- `ml/pipelines/components/model_selector.py` — `select_and_persist_winner()`
- `ml/pipelines/components/explainer.py` — `explain_top_models()`

### Downstream (Phase 18–20)
- Phase 18: `train_models`, `cross_validation`, `evaluation`, `model_comparison` components
- Phase 19: `explainability`, `winner_selection`, `model_persistence`, `deployment` components
- Phase 20: Full KFP DSL pipeline definition wrapping all 11 components

### Test infrastructure
- `ml/tests/conftest.py` — `sample_ohlcv_df()` fixture (250-row synthetic OHLCV)
- `ml/tests/pytest.ini` — test configuration

</canonical_refs>
