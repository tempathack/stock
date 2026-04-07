# Audit Section 3: Technology Integration Recommendations

Status: COMPLETE — 2026-04-07

---

## PRIORITY RANKING

Ranked by Impact × Feasibility (H=3, M=2, L=1):

| Rank | Technology | Impact | Feasibility | Score | Story |
|---|---|---|---|---|---|
| 1 | OpenTelemetry distributed tracing | H | H | 9 | US-077 |
| 2 | KEDA Kafka consumer autoscaling | H | H | 9 | US-082 |
| 3 | PgBouncer connection pooling | H | H | 9 | US-086 |
| 4 | MLflow experiment tracking | H | M | 6 | US-076 |
| 5 | Evidently AI model monitoring | H | M | 6 | US-078 |
| 6 | TimescaleDB continuous aggregates | M | H | 6 | US-084 |
| 7 | Feast Redis online store | M | H | 6 | US-089 |
| 8 | Claude API market commentary | M | M | 4 | US-080 |
| 9 | Great Expectations data quality | M | M | 4 | US-079 |
| 10 | OpenFeature feature flagging | M | M | 4 | US-085 |
| 11 | Argo Workflows ML orchestration | M | M | 4 | US-087 |
| 12 | dbt SQL transformation layer | L | H | 3 | US-083 |
| 13 | Qdrant vector database | L | M | 2 | US-081 |
| 14 | HashiCorp Vault secrets | L | M | 2 | US-088 |
| 15 | sktime statistical models | M | L | 2 | US-090 |

---

## MLflow for Experiment Tracking (US-076)

**Current state:** Training pipeline stores model artifacts in MinIO and run metadata in JSON files under `model_registry/runs/`. No centralized experiment comparison UI.

**Integration approach:**
- Add `mlflow` to `ml/requirements.txt`
- In `training_pipeline.py`: wrap each horizon training block with `mlflow.start_run(run_name=f"horizon_{h}d_{run_id}")`
- Log params: `mlflow.log_params({"horizon": h, "n_tickers": len(tickers), "linear_only": linear_only})`
- Log metrics: `mlflow.log_metrics({"rmse": winner_rmse, "mae": winner_mae})`
- Log model artifact: `mlflow.sklearn.log_model(winner_pipeline, "model")`
- Deploy MLflow Tracking Server as K8s Deployment with `MLFLOW_S3_ENDPOINT_URL=http://minio.storage:9000`

**Effort:** M (2–3 days) | **Recommendation:** HIGH — replaces ad-hoc JSON files, enables model comparison across runs.

---

## OpenTelemetry Distributed Tracing (US-077)

**Current state:** No distributed tracing. Logs are structured JSON but trace correlation across API → Kafka → Flink → DB is not possible.

**Integration approach:**
- `pip install opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp`
- Add `FastAPIInstrumentor().instrument_app(app)` in `main.py`
- Deploy Grafana Tempo in `monitoring` namespace as OTLP backend (integrates with existing Grafana)
- Set env: `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo.monitoring:4317`

**Effort:** S-M (1–2 days) | **Recommendation:** CRITICAL — enables trace correlation across all services using existing Grafana UI.

---

## Evidently AI for Automated ML Model Monitoring (US-078)

**Current state:** Custom drift detection in `ml/drift/` using KS test and PSI. No automated HTML report generation.

**Integration approach:**
- `pip install evidently` in `ml/requirements.txt`
- Replace custom KS/PSI in `drift_pipeline.py` with `ColumnDriftMetric` and `DataDriftPreset`
- Generate HTML reports: `report.save_html("drift_report.html")` → upload to MinIO `reports/` bucket
- Add Grafana panel linking to MinIO presigned URL

**Effort:** M (2–3 days) | **Recommendation:** HIGH — replaces custom drift code with battle-tested library, adds HTML audit trail.

---

## Great Expectations for Data Quality Gates (US-079)

**Current state:** No data quality validation on ingested data. Malformed records go to DLQ (US-068) but no upstream schema/range validation.

**Integration approach:**
- `pip install great-expectations`
- Define Expectation Suite on `feast_yfinance_macro`: `expect_column_values_to_be_between("vix", 0, 200)`, `expect_column_to_not_be_null("spy_return")`
- Run GX checkpoint in `data_loader.py` after each ingest — raise `DataQualityError` on failure
- GX DataDocs HTML published to MinIO `data-docs/` bucket

**Effort:** M (2–3 days) | **Recommendation:** MEDIUM — adds formal data contracts, valuable for FRED macro pipeline.

---

## Claude API for Automated Market Commentary (US-080)

**Current state:** Forecasts page shows raw numerical predictions only. No natural language explanation of prediction drivers.

**Prompt template:**
```
Given {ticker} ({company_name}), predicted {horizon}d return of {predicted_return:.1%}
with confidence {confidence:.0%}, top drivers: {top_shap_features},
macro context: VIX={vix:.1f}, 10Y yield={dgs10:.2f}%.
Write a 2-sentence market commentary for a professional trader. Be concise and factual.
```

**Integration approach:**
- Add `anthropic` to `services/api/requirements.txt`
- New endpoint `GET /predict/{ticker}/commentary` using `claude-haiku-4-5-20251001`
- Cache commentary in Redis for 30 min
- Frontend: "AI Commentary" card on Forecasts page

**Effort:** S (1 day) | **Recommendation:** HIGH VALUE — differentiates the platform, minimal engineering effort.

---

## Qdrant Vector Database for Semantic Stock Search (US-081)

**Current state:** Search uses text prefix matching on ticker symbols. No semantic similarity search.

**Integration approach:**
- Deploy Qdrant in `storage` namespace
- Embed company description + sector + top SHAP features using `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- New endpoint `GET /search/similar/{ticker}?top_k=5`
- Frontend: "Similar Stocks" section in Search results

**Effort:** L (4–5 days) | **Recommendation:** LOW URGENCY — nice differentiator but not critical.

---

## KEDA for Kafka Consumer Autoscaling (US-082)

**Current state:** `kafka-consumer` has fixed `replicas: 2`. Consumer lag spikes during market open hours.

**KEDA ScaledObject:**
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: kafka-consumer-scaler
  namespace: processing
spec:
  scaleTargetRef:
    name: kafka-consumer
  minReplicaCount: 1
  maxReplicaCount: 5
  triggers:
  - type: kafka
    metadata:
      bootstrapServers: kafka.storage.svc.cluster.local:9092
      consumerGroup: stock-consumer-group
      topic: intraday-data
      lagThreshold: "1000"
```

**Effort:** S (half day) | **Recommendation:** CRITICAL — prevents consumer lag buildup; scales to 1 at night for cost savings.

---

## dbt for SQL Transformation Layer (US-083)

**Current state:** All SQL transformations embedded in Python services. No lineage tracking or incremental models.

**Key dbt models:**
- `marts/macro_unified.sql`: JOIN `macro_fred_daily` + `feast_yfinance_macro`
- `marts/predictions_with_accuracy.sql`: JOIN `predictions` + actuals from `ohlcv_daily`
- Run `dbt run` as K8s CronJob post-ingest

**Effort:** M (2–3 days) | **Recommendation:** LOW URGENCY — current volume doesn't require it yet.

---

## TimescaleDB Continuous Aggregates for Macro History (US-084)

**Current state:** TimescaleDB 2.25.2 active. `macro_fred_daily` queried raw for 90-day history.

**Recommended aggregate:**
```sql
CREATE MATERIALIZED VIEW macro_daily_30d_agg
WITH (timescaledb.continuous_aggregate = true) AS
SELECT time_bucket('1 day', as_of_date::timestamptz) AS bucket,
       series_id, AVG(value) AS avg_value
FROM macro_fred_daily
GROUP BY bucket, series_id;
```

**Effort:** S (half day) | **Recommendation:** MEDIUM — macro queries already fast (indexed), aggregate prevents full-table scans.

---

## OpenFeature for Feature Flagging (US-085)

**Current state:** Feature toggles are ad-hoc env vars (`AB_TESTING_ENABLED`, `KSERVE_ENABLED`, `LINEAR_ONLY`). No runtime toggling without redeployment.

**Integration approach:**
- `pip install openfeature-sdk`
- `app/feature_flags.py` with `OpenFeatureClient` backed by `EnvVarProvider`
- Replace `if settings.AB_TESTING_ENABLED:` with `if flag_client.get_boolean_value("ab-testing", False):`
- Future: swap `EnvVarProvider` for `FlagdProvider` without changing call sites

**Effort:** S (1 day) | **Recommendation:** MEDIUM — low effort, enables runtime flag changes via ConfigMap.

---

## PgBouncer for PostgreSQL Connection Pooling (US-086)

**Current state:** FastAPI uses SQLAlchemy async pool (pool_size=10, max_overflow=20). With multiple replicas, 30+ connections per pod quickly exhausts PostgreSQL `max_connections=100`.

**Integration approach:**
- Deploy PgBouncer as Deployment in `storage` namespace
- `pool_mode = transaction`, `max_client_conn = 200`, `default_pool_size = 20`
- Point `DATABASE_URL` ConfigMap to `pgbouncer.storage:5432`
- Reduce SQLAlchemy `pool_size=5`

**Effort:** S (half day) | **Recommendation:** CRITICAL — connection exhaustion is a real production failure mode.

---

## Argo Workflows for ML Pipeline Orchestration (US-087)

**Current state:** 17 pods in `kubeflow` namespace (Argo-based). Weekly training is a single-container CronJob with no DAG, retries, or parallel horizon training.

**Integration approach:**
- Argo Workflows already available (part of Kubeflow stack)
- Define `WorkflowTemplate` with DAG: `load-data → engineer-features → [train-h1, train-h7, train-h14, train-h30] (parallel) → deploy-winners`
- Replace `cronjob-weekly-training.yaml` with `CronWorkflow`

**Effort:** M (2–3 days) | **Recommendation:** MEDIUM — parallel horizon training = 4x wall-clock speedup. Argo already installed.

---

## HashiCorp Vault for Secrets Management (US-088)

**Current state:** Secrets in K8s Secrets (`stock-platform-secrets`, `minio-secrets`, `grafana-secrets`). Base64-encoded, not encrypted at rest.

**Current secrets:** `POSTGRES_PASSWORD`, `REDIS_URL`, `MINIO_ACCESS_KEY/SECRET_KEY`, `GRAFANA_ADMIN_PASSWORD`.

**Integration approach:**
- Deploy Vault in `vault` namespace with K8s auth backend
- Vault Agent Injector: annotate pods with `vault.hashicorp.com/agent-inject-secret-*` annotations
- Migrate secrets from K8s Secrets to Vault KV store gradually

**Effort:** L (3–5 days) | **Recommendation:** LOW for dev cluster, HIGH for production.

---

## Feast on Redis for Real-time Feature Serving (US-089)

**Current state:** Feast online store uses PostgreSQL backend (`type: postgres`). PostgreSQL not optimized for sub-millisecond key-value reads.

**Migration (zero new infra):**
- Update `feature_store.yaml`: `online_store: {type: redis, connection_string: "redis://redis.storage:6379"}`
- Run `feast apply`
- Update feast_writer Flink job env: `ONLINE_STORE_TYPE=redis`
- Redis already deployed in `storage` namespace

**Expected improvement:** Feature read latency: PostgreSQL ~5ms → Redis ~0.5ms (10x)

**Effort:** S (1 day) | **Recommendation:** HIGH — zero new infrastructure, 10x feature read latency improvement.

---

## sktime Statistical Forecasting Models — Phase 96 Readiness (US-090)

**Phase plans found:** 5 files (96-01 through 96-05-PLAN.md) in `.planning/phases/96-sktime-statistical-forecasting-models/`.

**Models planned:** ARIMA, ExponentialSmoothing (Holt-Winters), TBATS, Prophet, sktime ensemble.

**Readiness assessment:**
- `sktime` in `ml/requirements.txt` — confirmed by `include_sktime` / `include_sktime_regression` flags in training pipeline
- Training pipeline infrastructure ready
- **Blocker:** minikube node OOM prevents test runs (confirmed US-069)
- **Recommendation:** Phase 96 ready to execute once memory constraint resolved (increase minikube to 8GB+ RAM)

**Effort:** L (pre-planned) | **Recommendation:** MEDIUM — blocked by compute, not code.

---

## COMPLETE TECH INTEGRATION REPORT (US-091)

**Generated:** 2026-04-07

All 15 technology integration research stories (US-076–US-090) completed.

### Quick Wins (≤1 day, high impact):
1. **Feast → Redis online store** (US-089): Config change only, 10x feature read improvement
2. **KEDA autoscaling** (US-082): One YAML file, prevents consumer lag spikes
3. **OpenTelemetry** (US-077): 2 lines in main.py, full distributed tracing in Grafana Tempo
4. **Claude API commentary** (US-080): 1 day, high user-facing differentiation

### Must-Have for Production:
- PgBouncer (US-086): Connection exhaustion is a real failure mode at scale
- OpenTelemetry (US-077): Essential for debugging cross-service issues
- KEDA (US-082): Consumer lag already visible in Grafana

### Defer Until Scale Demands It:
- Qdrant (US-081), Vault (US-088), dbt (US-083): Valid technologies, not current bottlenecks
