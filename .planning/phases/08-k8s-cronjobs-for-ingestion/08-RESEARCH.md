# Phase 8: K8s CronJobs for Ingestion — Research

**Gathered:** 2026-03-25
**Status:** Complete

## RESEARCH COMPLETE

---

## Domain Overview

Phase 8 delivers K8s CronJob manifests and their trigger scripts that call the FastAPI
`/ingest/intraday` and `/ingest/historical` endpoints on a schedule. Phase 7 wired those
endpoints; Phase 8 makes them run automatically inside the cluster.

---

## What Already Exists

A full implementation is already present in the repository:

### K8s Manifests — `stock-prediction-platform/k8s/ingestion/`

| File | Description |
|---|---|
| `cronjob-intraday.yaml` | CronJob `intraday-ingestion`, schedule `*/5 14-21 * * 1-5` (ET), Forbid concurrency |
| `cronjob-historical.yaml` | CronJob `historical-ingestion`, schedule `0 2 * * 0` (Sunday 02:00 UTC), Forbid concurrency |
| `configmap.yaml` | `ingestion-config` ConfigMap wiring Kafka, API base URL, and all env vars |
| `fastapi-deployment.yaml` | Stock-API Deployment that CronJobs call |

### Trigger Scripts — `stock-prediction-platform/services/api/app/jobs/`

| File | Entry point |
|---|---|
| `trigger_intraday.py` | `python -m app.jobs.trigger_intraday` — POSTs to `/ingest/intraday`, exits 0/1 |
| `trigger_historical.py` | `python -m app.jobs.trigger_historical` — POSTs to `/ingest/historical`, exits 0/1 |

Both use `httpx.post()` with a timeout from `TRIGGER_TIMEOUT_SECONDS` env var and log
structured JSON via `structlog`.

---

## Schedule Design

### Intraday CronJob
- **Schedule:** `*/5 14-21 * * 1-5` — every 5 minutes Mon-Fri 14:00–21:00 UTC
- **timeZone:** `America/New_York` — aligns with NYSE market hours (09:30–16:05 ET)
- **concurrencyPolicy:** `Forbid` — prevents overlapping runs during slow markets
- **startingDeadlineSeconds:** 60 — skip if missed by > 60s
- **backoffLimit:** 3 with `restartPolicy: OnFailure`
- **Timeout:** 300s (`TRIGGER_TIMEOUT_SECONDS`)

### Historical CronJob
- **Schedule:** `0 2 * * 0` — weekly Sunday 02:00 UTC (after market close, quiet window)
- **No timeZone field** (defaults to cluster UTC)
- **concurrencyPolicy:** Forbid
- **startingDeadlineSeconds:** 300
- **Timeout:** 600s (historical fetch is heavier — full S&P 500 OHLCV)

---

## ConfigMap Values (ingestion-config)

```yaml
API_BASE_URL: "http://stock-api.ingestion.svc.cluster.local:8000"
KAFKA_BOOTSTRAP_SERVERS: "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
INTRADAY_TOPIC: "intraday-data"
HISTORICAL_TOPIC: "historical-data"
```

CronJob containers use `envFrom: configMapRef: ingestion-config` for all env injection.

---

## Requirements Mapping

| Req ID | Description | Status |
|---|---|---|
| INGEST-04 | K8s CronJob for intraday ingestion (daily, market hours) | Implemented |
| INGEST-05 | K8s CronJob for historical ingestion (weekly) | Implemented |

---

## Validation Architecture

### Functional Tests
- `kubectl apply -f cronjob-intraday.yaml` exits 0
- `kubectl apply -f cronjob-historical.yaml` exits 0
- `kubectl get cronjob -n ingestion` shows both CronJobs in ACTIVE state
- Manual trigger: `kubectl create job --from=cronjob/intraday-ingestion test-intraday -n ingestion`
- Job pod logs contain `trigger_intraday_complete` JSON entry

### Structural Tests
- `cronjob-intraday.yaml` contains `schedule: "*/5 14-21 * * 1-5"`
- `cronjob-historical.yaml` contains `schedule: "0 2 * * 0"`
- Both contain `concurrencyPolicy: Forbid`
- Both reference `configMapRef: ingestion-config`
- Both have `restartPolicy: OnFailure`
- Trigger scripts exit 0 on HTTP 200 and 1 on non-200 / request error

---

## Technical Patterns

### CronJob → API Pattern
```
CronJob pod (stock-api:latest image)
  → python -m app.jobs.trigger_intraday
    → httpx.POST http://stock-api.ingestion.svc.cluster.local:8000/ingest/intraday
      → FastAPI YahooFinanceService.fetch_intraday()
        → OHLCVProducer.produce_records() → Kafka
```

### Resource Sizing
- Intraday trigger: 100m CPU / 256Mi RAM (requests), 500m / 512Mi (limits)
- Historical trigger: 200m CPU / 512Mi RAM (requests), 1000m / 1Gi (limits)

### Job History
- `successfulJobsHistoryLimit: 3` on both CronJobs
- `failedJobsHistoryLimit: 3` on both CronJobs

---

## Key Decisions for Planning

1. Both CronJob YAMLs already exist — plan tasks are to verify correctness and ensure
   deployment steps are wired into `deploy-all.sh`.
2. Trigger scripts already exist in `app/jobs/` — plan tasks are to verify the module
   entrypoints work (`python -m app.jobs.trigger_intraday`).
3. `app/jobs/__init__.py` already exists.
4. `httpx` must be in the API service's `requirements.txt`.
5. The phase plan must cover: YAML correctness, trigger script correctness, `deploy-all.sh`
   integration, and smoke-test verification.
