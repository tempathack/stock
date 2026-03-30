---
phase: 67-apache-flink-real-time-stream-processing
plan: "02"
subsystem: infra
tags: [apache-flink, pyflink, kafka, feast, redis, grafana, prometheus, rocksdb, ema, rsi, macd]

requires:
  - phase: 67-01
    provides: "Flink namespace RBAC, OHLCV Normalizer PyFlink job, intraday-data Kafka source DDL pattern"
  - phase: 66
    provides: "Feast feature_repo.py with technical_indicators_fv, PostgreSQLSource, Redis online store"

provides:
  - "indicator_udaf_logic.py: pure Python compute_rsi/compute_ema/compute_macd_signal (Wilder's EWM)"
  - "indicator_stream.py: PyFlink Table API job — HOP(5min,20min) window with RSI/EMA/MACD UDAFs writing to processed-features Kafka topic"
  - "feast_writer.py: PyFlink DataStream job — consumes processed-features, calls store.push(PushMode.ONLINE) to Redis"
  - "feature_repo.py: PushSource technical_indicators_push + stream_source on technical_indicators_fv"
  - "FlinkDeployment CRs for indicator-stream and feast-writer (RocksDB + MinIO checkpoints, Prometheus annotations)"
  - "Grafana ConfigMap grafana-dashboard-flink.yaml with Job Uptime (stat) + Records Out/sec (timeseries) panels"
  - "15 new unit tests (10 UDAF + 5 Feast push mock)"

affects:
  - phase-68-e2e-integration
  - phase-69-frontend-analytics

tech-stack:
  added:
    - "apache-flink==1.19.* (indicator_stream Dockerfile)"
    - "pandas + numpy (UDAF logic in indicator_stream)"
    - "feast[redis]==0.61.0 + Python 3.10 (feast_writer Dockerfile)"
  patterns:
    - "Pure Python logic helper pattern: split UDAF math into indicator_udaf_logic.py (no pyflink) for testability"
    - "Feast push pattern: module-level push_batch_to_feast() with store_path param so tests can mock FeatureStore"
    - "sys.modules mock pattern: mock feast at sys.modules level before import to avoid feast runtime in tests"

key-files:
  created:
    - stock-prediction-platform/services/flink-jobs/indicator_stream/indicator_udaf_logic.py
    - stock-prediction-platform/services/flink-jobs/indicator_stream/indicator_stream.py
    - stock-prediction-platform/services/flink-jobs/indicator_stream/Dockerfile
    - stock-prediction-platform/services/flink-jobs/indicator_stream/requirements.txt
    - stock-prediction-platform/services/flink-jobs/feast_writer/feast_writer.py
    - stock-prediction-platform/services/flink-jobs/feast_writer/Dockerfile
    - stock-prediction-platform/services/flink-jobs/feast_writer/requirements.txt
    - stock-prediction-platform/k8s/flink/flinkdeployment-indicator-stream.yaml
    - stock-prediction-platform/k8s/flink/flinkdeployment-feast-writer.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-dashboard-flink.yaml
    - stock-prediction-platform/tests/flink/test_indicator_stream.py
    - stock-prediction-platform/tests/flink/test_feast_writer.py
  modified:
    - stock-prediction-platform/ml/feature_store/feature_repo.py
    - stock-prediction-platform/k8s/monitoring/grafana-deployment.yaml

key-decisions:
  - "UDAF logic extracted into indicator_udaf_logic.py (pure Python, no pyflink) so unit tests run without Flink runtime"
  - "compute_rsi uses Wilder's smoothing (EWM alpha=1/14, adjust=False) matching Phase 10 ml/features/indicators.py"
  - "compute_macd_signal requires 35 prices minimum (26 for EMA-26 + 9 for signal EMA)"
  - "feast_writer.py uses Python 3.10 Dockerfile because Feast 0.61.0 requires Python 3.9+ and flink:1.19 ships Python 3.8"
  - "push_batch_to_feast() defined at module level with store_path parameter so tests can patch FeatureStore without pyflink"
  - "Feast test mocks feast at sys.modules level before importing feast_writer to avoid needing feast installed in test env"
  - "FlinkDeployment feast-writer adds FEAST_STORE_PATH=/opt/feast env var; feature_store.yaml mounted at runtime via ConfigMap volume"
  - "Grafana dashboard uses uid=flink-stream, datasource name 'Prometheus' matching existing grafana-datasource-configmap.yaml"

patterns-established:
  - "Pure Python helper pattern: Job logic file (no pyflink) + PyFlink wrapper that imports it — same as ohlcv_normalizer/normalizer_logic.py"
  - "Feast mock pattern for tests: set sys.modules['feast'] and sys.modules['feast.push_source'] to MagicMock before import"

requirements-completed:
  - FLINK-03
  - FLINK-04
  - FLINK-06
  - FLINK-07

duration: 5min
completed: 2026-03-30
---

# Phase 67 Plan 02: Indicator Stream + Feast Writer Summary

**PyFlink HOP-window indicator pipeline (EMA-20/RSI-14/MACD signal) with Feast Redis push via store.push(PushMode.ONLINE), completing the end-to-end real-time feature serving path**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-30T08:31:55Z
- **Completed:** 2026-03-30T08:37:08Z
- **Tasks:** 3
- **Files modified:** 14 (12 created, 2 modified)

## Accomplishments

- Indicator Stream PyFlink job with HOP(5min,20min) window TVF and three registered UDAFs (RSI-14, EMA-20, MACD signal) writing to processed-features Kafka topic
- Feast Writer PyFlink DataStream job consuming processed-features and pushing to Redis via Feast store.push(PushMode.ONLINE); feature_repo.py updated with PushSource
- 15 new unit tests (10 UDAF boundary conditions, 5 Feast push mock) all passing alongside 7 existing Plan 01 tests (22 total)
- Two FlinkDeployment CRs (indicator-stream + feast-writer) with RocksDB/MinIO checkpoints, Prometheus annotations, stateful upgrade mode
- Grafana ConfigMap with valid JSON dashboard (Job Uptime stat + Records Out/sec timeseries) mounted in grafana-deployment.yaml

## Task Commits

Each task was committed atomically:

1. **Task 1: Indicator Stream job — UDAF logic + tests + Dockerfile** - `361c185` (feat)
2. **Task 2: Feast Writer job + feature_repo.py PushSource + tests** - `886128c` (feat)
3. **Task 3: FlinkDeployment CRs + Grafana Flink dashboard** - `bad0ddd` (feat)

## Files Created/Modified

- `services/flink-jobs/indicator_stream/indicator_udaf_logic.py` - Pure Python RSI/EMA/MACD helpers (no pyflink)
- `services/flink-jobs/indicator_stream/indicator_stream.py` - PyFlink Table API job with HOP windows + registered UDAFs
- `services/flink-jobs/indicator_stream/Dockerfile` - flink:1.19 + pandas/numpy + kafka/jdbc JARs
- `services/flink-jobs/indicator_stream/requirements.txt` - apache-flink==1.19.*, pandas, numpy
- `services/flink-jobs/feast_writer/feast_writer.py` - DataStream job + module-level push_batch_to_feast()
- `services/flink-jobs/feast_writer/Dockerfile` - flink:1.19 + Python 3.10 + feast[redis]==0.61.0
- `services/flink-jobs/feast_writer/requirements.txt` - apache-flink==1.19.*, feast[redis]==0.61.0, pandas
- `k8s/flink/flinkdeployment-indicator-stream.yaml` - FlinkDeployment CR with RocksDB/MinIO/Prometheus config
- `k8s/flink/flinkdeployment-feast-writer.yaml` - FlinkDeployment CR + FEAST_STORE_PATH env var
- `k8s/monitoring/grafana-dashboard-flink.yaml` - ConfigMap with 2-panel Flink dashboard JSON
- `k8s/monitoring/grafana-deployment.yaml` - Added flink-stream.json volumeMount + volume
- `ml/feature_store/feature_repo.py` - Added PushSource + stream_source on technical_indicators_fv
- `tests/flink/test_indicator_stream.py` - 10 tests for RSI/EMA/MACD boundary conditions and None guards
- `tests/flink/test_feast_writer.py` - 5 tests with feast mocked at sys.modules level

## Decisions Made

- UDAF logic extracted into pure Python helper `indicator_udaf_logic.py` (no pyflink imports) following the same pattern established in Plan 01 with `normalizer_logic.py`. This allows unit tests to run without a Flink runtime.
- feast_writer Dockerfile uses Python 3.10 because Feast 0.61.0 requires Python 3.9+ but flink:1.19 base image ships with Python 3.8.
- `push_batch_to_feast()` defined at module level with a `store_path` parameter so unit tests can `patch('feast_writer.FeatureStore', ...)` without needing Feast installed.
- Feast tests mock `sys.modules['feast']` and `sys.modules['feast.push_source']` before importing `feast_writer` to avoid the feast package runtime dependency.
- Grafana dashboard uses datasource name `"Prometheus"` (matching existing `grafana-datasource-configmap.yaml`) and uid `flink-stream`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Feature_store.yaml is mounted at runtime via ConfigMap volume in the FlinkDeployment podTemplate.

## Next Phase Readiness

- Indicator Stream and Feast Writer jobs are complete — images can be built with `docker build` and loaded into Minikube
- FlinkDeployment CRs ready to apply once Flink Operator is running in the cluster
- Feast online store will serve real-time EMA/RSI/MACD features for the prediction API after Phase 68 integration testing

---
*Phase: 67-apache-flink-real-time-stream-processing*
*Completed: 2026-03-30*
