---
phase: 58-fix-docker-compose-runtime-kafka-consumer-configurable-broker-ml-pipeline-entrypoint-fix
plan: "01"
subsystem: infrastructure
tags: [docker-compose, kafka-consumer, ml-pipeline, bug-fix, tdd]
dependency_graph:
  requires: []
  provides: [FIX-KAFKA, FIX-ML]
  affects: [docker-compose-local-stack]
tech_stack:
  added: []
  patterns: [pydantic-settings env override, os.environ.get fallback pattern]
key_files:
  created: []
  modified:
    - stock-prediction-platform/services/kafka-consumer/consumer/config.py
    - stock-prediction-platform/ml/pipelines/training_pipeline.py
    - stock-prediction-platform/docker-compose.yml
    - stock-prediction-platform/services/kafka-consumer/tests/test_main.py
    - stock-prediction-platform/ml/tests/test_training_pipeline.py
    - stock-prediction-platform/services/kafka-consumer/pytest.ini
    - stock-prediction-platform/ml/tests/pytest.ini
decisions:
  - "Changed KAFKA_BOOTSTRAP_SERVERS default to kafka:9092 — K8s ConfigMap still overrides at runtime so no K8s regression"
  - "Used tickers_str = args.tickers or os.environ.get('TICKERS') two-liner — minimal diff, preserves CLI-arg precedence"
  - "Added :-stockpassword default fallback to DATABASE_URL in ml-pipeline to match postgres service pattern"
  - "Added -p no:logfire to pytest.ini in both kafka-consumer and ml/tests to fix pre-existing logfire plugin crash"
metrics:
  duration_minutes: 3
  tasks_completed: 2
  files_modified: 7
  completed_date: "2026-03-24"
---

# Phase 58 Plan 01: Fix Docker-Compose Runtime Crashes Summary

**One-liner:** Fixed two docker-compose runtime crashes — kafka-consumer now defaults to `kafka:9092` broker and ml-pipeline reads `TICKERS` env var instead of raising ValueError when no CLI args are passed.

## Tasks Completed

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Fix kafka-consumer broker default + docker-compose env injection | b1a4d94 | Complete |
| 2 | Fix ml-pipeline __main__ to read TICKERS env var + inject TICKERS in docker-compose | d70a766 | Complete |

## What Was Built

### Task 1: kafka-consumer broker default fix

**Problem:** `ConsumerSettings.KAFKA_BOOTSTRAP_SERVERS` defaulted to `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` — the Strimzi K8s DNS name — which fails in docker-compose where the broker service is named `kafka`. Additionally, no `environment` block existed in the docker-compose kafka-consumer service, so no env vars were injected.

**Fix:**
- `consumer/config.py` line 17: changed default to `"kafka:9092"`
- `docker-compose.yml`: added `environment` block with `KAFKA_BOOTSTRAP_SERVERS=kafka:9092` and `DATABASE_URL` (with `:-stockpassword` default fallback), plus `depends_on: [kafka, postgres]`
- K8s ConfigMap at `k8s/processing/configmap.yaml` still injects `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` at runtime — overrides the Python default. No K8s regression.

**Tests added:** `TestConsumerSettingsDefaults` (3 tests — default value, env override, DATABASE_URL default).

### Task 2: ml-pipeline entrypoint TICKERS env var

**Problem:** `training_pipeline.py` `__main__` block ran `tickers = args.tickers.split(",") if args.tickers else None`. When the Dockerfile CMD runs with no CLI args, `args.tickers` is `None`, so `tickers` stays `None`, and `run_training_pipeline(tickers=None)` raises `ValueError`.

**Fix:**
- `training_pipeline.py` line 455: replaced `tickers = args.tickers.split(",") if args.tickers else None` with the two-line env-var-fallback pattern:
  ```python
  tickers_str = args.tickers or os.environ.get("TICKERS")
  tickers = tickers_str.split(",") if tickers_str else None
  ```
- `docker-compose.yml` ml-pipeline environment: added `TICKERS=AAPL,MSFT,...20 tickers...` and fixed `DATABASE_URL` to use `:-stockpassword` default fallback.

**Tests added:** `TestMainEntrypointTickerResolution` (3 tests — env var used when no CLI arg, None when neither set, CLI arg takes precedence over env var).

## Verification Results

All acceptance criteria met:

- `grep "KAFKA_BOOTSTRAP_SERVERS" consumer/config.py` → `kafka:9092`
- `grep -A8 "kafka-consumer:" docker-compose.yml` → shows full environment block
- `grep "KAFKA_BOOTSTRAP_SERVERS" k8s/processing/configmap.yaml` → `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` (unchanged)
- `grep "os.environ.get" training_pipeline.py` → line 455 shows `os.environ.get("TICKERS")`
- `grep "TICKERS=" docker-compose.yml` → 20-ticker list under ml-pipeline
- 3 `TestConsumerSettingsDefaults` tests: PASSED
- 3 `TestMainEntrypointTickerResolution` tests: PASSED

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Config] Added -p no:logfire to pytest.ini files**
- **Found during:** Task 1 (RED phase test run)
- **Issue:** Both `kafka-consumer/pytest.ini` and `ml/tests/pytest.ini` lacked `addopts = -p no:logfire`, causing the broken logfire pytest plugin to crash the test runner entirely before any test could run.
- **Fix:** Added `addopts = -p no:logfire` to both pytest.ini files. This matches the established pattern from Phase 3 Plan 01 decisions.
- **Files modified:** `stock-prediction-platform/services/kafka-consumer/pytest.ini`, `stock-prediction-platform/ml/tests/pytest.ini`
- **Commit:** b1a4d94 (kafka-consumer), d70a766 (ml tests)

### Pre-existing Issues (Out of Scope)

9 tests in `test_main.py` (TestConsumerSubscription, TestConsumerProcessing, TestConsumerErrorHandling, TestGracefulShutdown) fail with `OSError: [Errno 98] Address already in use` on port 9090. This is caused by the prometheus metrics server binding port 9090 in the first test and the port remaining occupied. These failures are pre-existing and unrelated to this plan's changes — logged to deferred-items.

## Self-Check

- [x] `stock-prediction-platform/services/kafka-consumer/consumer/config.py` exists and contains `kafka:9092`
- [x] `stock-prediction-platform/ml/pipelines/training_pipeline.py` contains `os.environ.get("TICKERS")`
- [x] `stock-prediction-platform/docker-compose.yml` contains `KAFKA_BOOTSTRAP_SERVERS=kafka:9092` and `TICKERS=AAPL`
- [x] `stock-prediction-platform/k8s/processing/configmap.yaml` still contains `kafka-kafka-bootstrap.storage.svc.cluster.local:9092`
- [x] Commit b1a4d94 exists
- [x] Commit d70a766 exists
