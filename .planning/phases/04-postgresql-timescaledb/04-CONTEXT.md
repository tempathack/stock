# Phase 4: PostgreSQL + TimescaleDB - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Write `db/init.sql` with all 6 table schemas (TimescaleDB hypertables, composite PKs, indexes, date partitioning). Add secret and ConfigMap creation to `setup-minikube.sh`. Uncomment the Phase 4 storage section in `deploy-all.sh`. The PostgreSQL Deployment, PVC, and storage ConfigMap manifests were already fully scaffolded in Phase 1 — they are applied by deploy-all.sh, not modified here.

</domain>

<decisions>
## Implementation Decisions

### Schema — Column Definitions

**`stocks` table** (reference table for S&P 500 universe):
- `ticker VARCHAR(10) PRIMARY KEY`
- `company_name VARCHAR(255) NOT NULL`
- `sector VARCHAR(100)`
- `industry VARCHAR(100)`
- `market_cap BIGINT`
- `is_active BOOLEAN NOT NULL DEFAULT true`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

**`ohlcv_daily` table** (daily OHLCV bars):
- `ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker)`
- `date DATE NOT NULL`
- `open NUMERIC(12,4)`, `high NUMERIC(12,4)`, `low NUMERIC(12,4)`, `close NUMERIC(12,4)`
- `adj_close NUMERIC(12,4)` — split/dividend-adjusted close
- `volume BIGINT`
- `vwap NUMERIC(12,4)` — pre-computed VWAP
- Composite PK: `(ticker, date)`

**`ohlcv_intraday` table** (intraday OHLCV bars):
- `ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker)`
- `timestamp TIMESTAMPTZ NOT NULL`
- `open NUMERIC(12,4)`, `high NUMERIC(12,4)`, `low NUMERIC(12,4)`, `close NUMERIC(12,4)`
- `adj_close NUMERIC(12,4)`
- `volume BIGINT`
- `vwap NUMERIC(12,4)`
- Composite PK: `(ticker, timestamp)`

**`predictions` table**:
- `id BIGSERIAL PRIMARY KEY`
- `ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker)`
- `prediction_date DATE NOT NULL` — when prediction was made
- `predicted_date DATE NOT NULL` — t+7 target date
- `predicted_price NUMERIC(12,4) NOT NULL`
- `model_id INTEGER NOT NULL REFERENCES model_registry(model_id)`
- `confidence NUMERIC(5,4)` — 0.0–1.0
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

**`model_registry` table**:
- `model_id SERIAL PRIMARY KEY`
- `model_name VARCHAR(100) NOT NULL`
- `version VARCHAR(50) NOT NULL`
- `metrics_json JSONB NOT NULL` — R², MAE, RMSE, MAPE, directional accuracy, fold stability
- `trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `is_active BOOLEAN NOT NULL DEFAULT false`

**`drift_logs` table**:
- `id BIGSERIAL PRIMARY KEY`
- `drift_type VARCHAR(50) NOT NULL` — 'data', 'prediction', 'concept'
- `severity VARCHAR(20) NOT NULL` — 'low', 'medium', 'high'
- `details_json JSONB NOT NULL`
- `detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### TimescaleDB Hypertables & Partitioning
- `ohlcv_daily` → `SELECT create_hypertable('ohlcv_daily', 'date', chunk_time_interval => INTERVAL '1 month');`
- `ohlcv_intraday` → `SELECT create_hypertable('ohlcv_intraday', 'timestamp', chunk_time_interval => INTERVAL '1 day');`
- No compression at this phase — defer to when data accumulates
- No space partitioning by ticker — single-dimension hypertables only

### Secrets Management
- Add to `setup-minikube.sh` (idempotent, after namespace creation):
  ```bash
  kubectl create secret generic stock-platform-secrets \
    --from-literal=POSTGRES_PASSWORD=devpassword123 \
    -n storage \
    --dry-run=client -o yaml | kubectl apply -f -
  ```
- Default dev password: `devpassword123` — clearly commented as dev-only in the script
- Secret never stored in any YAML file or committed to git

### Init SQL Delivery
- Add to `setup-minikube.sh` (after secret creation, idempotent):
  ```bash
  kubectl create configmap postgresql-init-sql \
    --from-file=init.sql=stock-prediction-platform/db/init.sql \
    -n storage \
    --dry-run=client -o yaml | kubectl apply -f -
  ```
- `db/init.sql` remains the canonical source — single place to edit
- Deployment, PVC, and storage ConfigMap are applied by `deploy-all.sh` (Phase 4 section to be uncommented)
- `setup-minikube.sh` is responsible for: Secret + init-sql ConfigMap only
- `deploy-all.sh` Phase 4 section: applies `k8s/storage/configmap.yaml`, `k8s/storage/postgresql-pvc.yaml`, `k8s/storage/postgresql-deployment.yaml`

### Claude's Discretion
- Exact index names (e.g. `idx_ohlcv_daily_ticker_date`)
- Whether to add a trigger for `stocks.updated_at` auto-update
- Transaction wrapping in init.sql (single transaction vs per-statement)
- Whether `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;` or without CASCADE

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing scaffold (read, do not recreate)
- `stock-prediction-platform/k8s/storage/postgresql-deployment.yaml` — fully wired deployment; mounts `postgresql-init-sql` ConfigMap and `stock-platform-secrets` Secret
- `stock-prediction-platform/k8s/storage/postgresql-pvc.yaml` — 20Gi PVC, no edits needed
- `stock-prediction-platform/k8s/storage/configmap.yaml` — POSTGRES_DB=stockdb, POSTGRES_USER=stockuser
- `stock-prediction-platform/scripts/setup-minikube.sh` — add Secret + ConfigMap creation here
- `stock-prediction-platform/scripts/deploy-all.sh` — uncomment Phase 4 storage section

### Files to implement
- `stock-prediction-platform/db/init.sql` — full schema stub, implement all 6 tables

### Requirements
- `.planning/REQUIREMENTS.md` §DB-01 through DB-07 — full acceptance criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `k8s/storage/postgresql-deployment.yaml` — already references `storage-config` ConfigMap (POSTGRES_DB, POSTGRES_USER, PGDATA), `postgresql-pvc` PVC, and mounts `postgresql-init-sql` to `/docker-entrypoint-initdb.d`; no edits needed
- `k8s/storage/configmap.yaml` — already has `POSTGRES_DB: stockdb`, `POSTGRES_USER: stockuser` — use these values in init.sql DDL (e.g. `\connect stockdb`)
- `services/api/app/config.py` — already defines `DATABASE_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` as Optional — these will be populated once PostgreSQL is running

### Established Patterns
- Phase 2 secret/configmap pattern: idempotent `--dry-run=client -o yaml | kubectl apply -f -` — replicate exactly in Phase 4 additions to setup-minikube.sh
- Phase 1 scaffold uses `timescale/timescaledb:latest-pg15` image — init.sql must be compatible with PostgreSQL 15

### Integration Points
- `setup-minikube.sh` additions are prerequisites for `deploy-all.sh` Phase 4 section (Secret and ConfigMap must exist before Deployment starts)
- Once PostgreSQL is Running, `DATABASE_URL=postgresql://stockuser:devpassword123@postgresql.storage.svc.cluster.local:5432/stockdb` can be injected into the FastAPI service (Phase 3's `config.py` is already ready for it)

</code_context>

<specifics>
## Specific Ideas

- No special UI references — this is a pure storage/infrastructure phase
- Database name `stockdb`, user `stockuser` are already established in the storage ConfigMap — do not deviate

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-postgresql-timescaledb*
*Context gathered: 2026-03-19*
