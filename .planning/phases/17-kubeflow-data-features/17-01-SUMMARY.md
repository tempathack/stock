---
phase: 17-kubeflow-data-features
plan: "01"
subsystem: ml
tags: [kubeflow, kfp, postgresql, psycopg2, pandas, data-loading, ohlcv]

# Dependency graph
requires:
  - phase: 4-postgresql-timescaledb
    provides: ohlcv_daily table schema and PostgreSQL connection pattern
  - phase: 9-kafka-consumers-batch-writer
    provides: OHLCV data written to ohlcv_daily table
provides:
  - DBSettings dataclass with env-var-driven K8s defaults
  - load_ticker_data() — parameterized SQL per-ticker data fetch
  - load_data() — multi-ticker orchestration with connection lifecycle management
  - kfp-standalone.yaml — KFP v2.3.0 standalone deployment scaffold manifest
affects: [18-kubeflow-training-eval, 20-kubeflow-pipeline-full-definition]

# Tech tracking
tech-stack:
  added: [psycopg2, pandas DatetimeIndex, KFP v2.3.0 standalone reference]
  patterns:
    - DBSettings dataclass with os.environ.get() defaults (no pydantic in ml/)
    - psycopg2.connect() per-call (short-lived batch job, not pooled)
    - Parameterized SQL with %s placeholders, never string interpolation
    - Empty ticker warning-and-skip (not error) pattern
    - connection.close() in finally block for guaranteed cleanup

key-files:
  created:
    - stock-prediction-platform/ml/pipelines/components/data_loader.py
    - stock-prediction-platform/ml/tests/test_data_loader.py
    - stock-prediction-platform/k8s/ml/kubeflow/kfp-standalone.yaml
  modified:
    - stock-prediction-platform/ml/pipelines/components/__init__.py

key-decisions:
  - "DBSettings dataclass uses os.environ.get() defaults matching K8s storage-config ConfigMap — no pydantic in ml/"
  - "psycopg2.connect() per load_data() call (not pooled) — pipeline components are short-lived batch jobs"
  - "load_ticker_data uses parameterized SQL (%s placeholders) — no string interpolation, injection-safe"
  - "Tickers returning 0 rows are logged as warning and omitted from result dict (not an error)"
  - "KFP standalone manifest is scaffold only (ConfigMap reference to v2.3.0) — not applied to cluster in this phase"

patterns-established:
  - "Component as pure Python function: no @dsl.component wrapping — deferred to Phase 20"
  - "Data passes as pd.DataFrame in-process; Parquet serialization deferred to Phase 20"

requirements-completed: [KF-01, KF-02]

# Metrics
duration: 15min
completed: 2026-03-20
---

# Phase 17 Plan 01: Data Loading Component + KFP Scaffold Summary

**PostgreSQL OHLCV data loader with env-var-driven DBSettings, parameterized SQL, per-ticker DataFrame output with DatetimeIndex, and KFP v2.3.0 standalone deployment scaffold**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-20T00:00:00Z
- **Completed:** 2026-03-20T00:15:00Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments
- DBSettings dataclass with K8s-ready defaults (postgresql.storage.svc.cluster.local, stockdb, stockuser)
- load_ticker_data() with parameterized SQL, date-range filtering, and DatetimeIndex output
- load_data() multi-ticker orchestration with guaranteed connection cleanup via finally block
- KFP v2.3.0 standalone manifest scaffold with install instructions in k8s/ml/kubeflow/
- 18 tests covering settings, per-ticker loading, multi-ticker orchestration, and error handling — all passing

## Task Commits

All tasks were committed atomically as part of the Phase 15-23 bulk commit:

1. **Task 1: Write tests for data_loader (RED)** - `fbc1e78` (test)
2. **Task 2: Implement data_loader.py (GREEN)** - `fbc1e78` (feat)
3. **Task 3: Scaffold KFP standalone manifest** - `fbc1e78` (chore)
4. **Task 4: Update components __init__.py + regression check** - `fbc1e78` (feat)

## Files Created/Modified
- `stock-prediction-platform/ml/pipelines/components/data_loader.py` - DBSettings dataclass + load_ticker_data() + load_data()
- `stock-prediction-platform/ml/tests/test_data_loader.py` - 18 tests for data loading component
- `stock-prediction-platform/k8s/ml/kubeflow/kfp-standalone.yaml` - KFP v2.3.0 deployment scaffold with install instructions
- `stock-prediction-platform/ml/pipelines/components/__init__.py` - Added DBSettings, load_data, load_ticker_data exports

## Decisions Made
- DBSettings dataclass uses os.environ.get() defaults — no pydantic dependency in the ml/ package
- psycopg2.connect() per call (not pooled) — pipeline components are short-lived batch jobs
- Parameterized SQL with %s placeholders (cursor.execute(sql, params)) — no string interpolation
- Empty tickers logged as warning and omitted from result dict (not raised as error)
- KFP manifest scaffold only — not applied to cluster; manual install documented in YAML comments

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- load_data() output format (dict[str, pd.DataFrame] with DatetimeIndex) ready for feature_engineer.py consumption
- DBSettings available for use by downstream components requiring DB access
- KFP standalone scaffold in place for Phase 20 full pipeline definition

---
*Phase: 17-kubeflow-data-features*
*Completed: 2026-03-20*
