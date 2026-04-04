---
phase: 94-fred-macro-feature-pipeline
plan: "02"
subsystem: ml-pipeline
tags: [fred, macro-features, data-loader, ingestion, k8s]
dependency_graph:
  requires: [94-01]
  provides: [feast_fred_macro-table, fetch_fred_macro-functions, FRED-ingestion-pipeline]
  affects: [training_pipeline, historical-ingestion-cronjob, feast-feature-store]
tech_stack:
  added: [fredapi==0.5.2]
  patterns: [psycopg2-upsert, ON-CONFLICT-timestamp, TimescaleDB-hypertable, secretKeyRef]
key_files:
  created: []
  modified:
    - stock-prediction-platform/ml/requirements.txt
    - stock-prediction-platform/services/api/requirements.txt
    - stock-prediction-platform/ml/pipelines/components/data_loader.py
    - stock-prediction-platform/ml/pipelines/training_pipeline.py
    - stock-prediction-platform/k8s/ml/cronjob-training.yaml
    - stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml
    - stock-prediction-platform/services/api/app/services/yahoo_finance.py
    - stock-prediction-platform/services/api/app/routers/ingest.py
decisions:
  - "Implemented FRED functions inline in yahoo_finance.py (not cross-service import) to avoid coupling services/api to ml layer"
  - "Wired FRED fetch into _run_ingestion_task() under historical mode guard to avoid FRED calls on intraday runs"
  - "Added Step 1c in training_pipeline.py after yfinance Step 1b; wrapped in try/except to prevent FRED failures from blocking training"
metrics:
  duration_seconds: 296
  completed_date: "2026-04-04"
  tasks_completed: 3
  files_modified: 8
---

# Phase 94 Plan 02: FRED Macro Collector Implementation Summary

**One-liner:** fredapi-based 14-series FRED collector with psycopg2 upsert into feast_fred_macro hypertable wired into both training and historical ingestion pipelines.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add fredapi to requirements and implement FRED collector in data_loader.py | 39ffea5 | data_loader.py, ml/requirements.txt, services/api/requirements.txt, training_pipeline.py |
| 2 | Wire FRED_API_KEY secretKeyRef into K8s CronJob YAMLs | 8c6c354 | cronjob-training.yaml, cronjob-historical.yaml |
| 3 | Add fetch_fred_macro to yahoo_finance.py and wire into ingest.py | 37f1595 | yahoo_finance.py, ingest.py |

## What Was Built

### Task 1: FRED Collector in data_loader.py

Added to `ml/pipelines/components/data_loader.py`:
- `fetch_fred_macro(start_date, end_date)` — fetches 14 FRED series via fredapi, builds daily DatetimeIndex, forward-fills with no limit, index.name="date"
- `create_fred_macro_table()` — creates feast_fred_macro TimescaleDB hypertable (timestamp PRIMARY KEY, no ticker column) with IF NOT EXISTS
- `write_fred_macro_to_db(df)` — upserts rows ON CONFLICT (timestamp) DO UPDATE, returns row count
- `_FRED_SERIES`, `_FRED_COLS`, `_CREATE_FRED_MACRO_TABLE_SQL`, `_UPSERT_FRED_SQL` module-level constants
- `from fredapi import Fred` and `import time as _time` added to top-level imports

Wired into `training_pipeline.py` as Step 1c after the existing yfinance macro Step 1b. Both `_start`/`_end` variables from Step 1b are reused for the FRED window.

Added `fredapi==0.5.2` to both `ml/requirements.txt` and `services/api/requirements.txt`.

### Task 2: K8s FRED_API_KEY secretKeyRef

- `cronjob-training.yaml`: FRED_API_KEY env entry inserted between POSTGRES_PASSWORD and POSTGRES_USER, referencing `stock-platform-secrets`
- `cronjob-historical.yaml`: FRED_API_KEY env entry added after TRIGGER_TIMEOUT_SECONDS
- Both YAMLs validated as syntactically valid via `yaml.safe_load`

Note: Operator must add the FRED_API_KEY value to the `stock-platform-secrets` Kubernetes Secret separately.

### Task 3: Ingestion-Layer FRED Functions

Added to `yahoo_finance.py`:
- `fetch_fred_macro()` — ingestion-service counterpart, same signature and contract as ml-layer version
- `create_fred_macro_table()` — uses env vars for DB connection (no DBSettings dependency)
- `write_fred_macro_to_db()` — same upsert pattern; importable from yahoo_finance module
- `os`, `psycopg2`, `Fred` added to imports

Wired into `ingest.py _run_ingestion_task()`:
- FRED functions imported explicitly from `app.services.yahoo_finance`
- FRED block runs after OHLCV loop completes, under `if mode == "historical"` guard
- Uses 5-year lookback matching OHLCV period; wrapped in try/except to prevent blocking

## Verification

All 33 test_data_loader.py tests pass (including all 10 new FRED test classes from Plan 01):
- TestFetchFredMacro (4 tests)
- TestFetchFredMacroMissingKey (1 test)
- TestCreateFredMacroTable (3 tests)
- TestWriteFredMacroToDB (2 tests)

Both K8s YAMLs validated as syntactically valid.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Installed fredapi in test environment**
- **Found during:** Task 1 verification
- **Issue:** fredapi not installed in local test environment; ModuleNotFoundError on import
- **Fix:** `pip install fredapi==0.5.2` to enable test execution
- **Files modified:** None (environment only)
- **Commit:** N/A (not committed — pip install is environment setup)

**2. [Rule 3 - Blocking Issue] Added missing imports to yahoo_finance.py**
- **Found during:** Task 3
- **Issue:** `os`, `psycopg2`, and `fredapi` were not imported in yahoo_finance.py but needed by FRED functions
- **Fix:** Added all three imports to the file's import block
- **Files modified:** stock-prediction-platform/services/api/app/services/yahoo_finance.py
- **Commit:** 37f1595

**3. [Rule 2 - Missing Critical Functionality] Added `datetime` import to ingest.py**
- **Found during:** Task 3
- **Issue:** ingest.py needed `datetime` and `timedelta` to compute the FRED date window dynamically
- **Fix:** Added `from datetime import datetime, timedelta, timezone` to ingest.py imports
- **Files modified:** stock-prediction-platform/services/api/app/routers/ingest.py
- **Commit:** 37f1595

## Self-Check: PASSED

Files exist:
- FOUND: stock-prediction-platform/ml/pipelines/components/data_loader.py
- FOUND: stock-prediction-platform/services/api/app/services/yahoo_finance.py
- FOUND: stock-prediction-platform/services/api/app/routers/ingest.py
- FOUND: stock-prediction-platform/k8s/ml/cronjob-training.yaml
- FOUND: stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml

Commits exist:
- FOUND: 39ffea5 (Task 1)
- FOUND: 8c6c354 (Task 2)
- FOUND: 37f1595 (Task 3)

Tests: 33 passed, 0 failed.
