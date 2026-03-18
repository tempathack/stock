# Phase 4: PostgreSQL + TimescaleDB - Research

**Researched:** 2026-03-19
**Domain:** PostgreSQL 15 with TimescaleDB extension, Kubernetes deployment, SQL DDL
**Confidence:** HIGH

## Summary

Phase 4 implements the full database schema for the stock prediction platform. The work is concentrated in three files: `db/init.sql` (full schema with 6 tables, hypertables, and indexes), additions to `setup-minikube.sh` (secret + ConfigMap creation), and uncommenting the Phase 4 section in `deploy-all.sh`. The Kubernetes manifests (Deployment, PVC, storage ConfigMap) were already scaffolded in Phase 1 and must NOT be modified.

The most significant technical finding is around TimescaleDB's constraint model: hypertable primary keys and unique constraints MUST include the partitioning column. The schema in CONTEXT.md already accounts for this with composite PKs `(ticker, date)` and `(ticker, timestamp)`. A second critical finding is that the existing Deployment mounts the `postgresql-init-sql` ConfigMap as a full volume to `/docker-entrypoint-initdb.d`, which overwrites the image's built-in `000_install_timescaledb.sh` script. Therefore, the `init.sql` MUST explicitly run `CREATE EXTENSION IF NOT EXISTS timescaledb;` since the image's auto-install script will be hidden. A third finding is that hypertables can hold foreign keys TO regular tables (e.g., `ohlcv_daily.ticker REFERENCES stocks(ticker)`) but regular tables CANNOT have foreign keys TO hypertables -- this direction is not an issue for this schema since `predictions` references `stocks` (regular table) not any hypertable.

**Primary recommendation:** Write init.sql with explicit `CREATE EXTENSION timescaledb`, create all 6 tables in dependency order, convert ohlcv tables to hypertables AFTER table creation, and add indexes. The init.sql must be self-contained since the volume mount replaces the image's init directory.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- 6 tables with exact column definitions: stocks, ohlcv_daily, ohlcv_intraday, predictions, model_registry, drift_logs
- TimescaleDB hypertables: ohlcv_daily (1 month chunks), ohlcv_intraday (1 day chunks)
- No compression at this phase
- No space partitioning by ticker -- single-dimension hypertables only
- Secret created via kubectl in setup-minikube.sh (idempotent `--dry-run=client -o yaml | kubectl apply -f -` pattern)
- init.sql loaded as ConfigMap `postgresql-init-sql` in setup-minikube.sh
- deploy-all.sh Phase 4 section uncommented
- Database name: `stockdb`, user: `stockuser` (from existing storage-config ConfigMap)
- Dev password: `devpassword123` -- clearly commented as dev-only
- Existing K8s manifests (Deployment, PVC, storage ConfigMap) are NOT modified

### Claude's Discretion
- Exact index names (e.g., `idx_ohlcv_daily_ticker_date`)
- Whether to add a trigger for `stocks.updated_at` auto-update
- Transaction wrapping in init.sql (single transaction vs per-statement)
- Whether `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;` or without CASCADE

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DB-01 | PostgreSQL deployed in storage namespace with PVC | Deployment + PVC already scaffolded; deploy-all.sh Phase 4 section applies them |
| DB-02 | TimescaleDB extension enabled | init.sql must CREATE EXTENSION explicitly (volume mount overwrites image's auto-install script) |
| DB-03 | init.sql with all table schemas: stocks, ohlcv_daily, ohlcv_intraday, predictions, model_registry, drift_logs | Full column specs in CONTEXT.md; dependency order and FK constraints documented below |
| DB-04 | Composite primary keys on (ticker, date) and (ticker, timestamp) | TimescaleDB requires partitioning column in PK -- composite PKs satisfy this |
| DB-05 | Indexes on (ticker, date) and (ticker, timestamp) | Composite PKs already create indexes; additional single-column indexes recommended |
| DB-06 | Partitioning on date columns for ohlcv_daily and ohlcv_intraday | create_hypertable with chunk_time_interval; must be called AFTER table creation |
| DB-07 | K8s ConfigMap for PostgreSQL credentials | storage-config ConfigMap already exists; Secret for password created in setup-minikube.sh |
</phase_requirements>

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|-------------|---------|---------|--------------|
| PostgreSQL | 15 | Relational database | Specified by existing image `timescale/timescaledb:latest-pg15` |
| TimescaleDB | latest (bundled with image) | Time-series hypertable partitioning | Specified in CONTEXT.md; auto-chunks by time dimension |
| kubectl | (cluster version) | K8s resource management | Existing project pattern for secrets and configmaps |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `--dry-run=client -o yaml \| kubectl apply -f -` | Idempotent secret/configmap creation | Established project pattern from Phase 2 |

### Alternatives Considered
None -- all choices are locked by CONTEXT.md and existing scaffold.

## Architecture Patterns

### Table Creation Order (Dependency Chain)

Tables must be created in this exact order due to foreign key references:

```
1. stocks              (no FK dependencies)
2. model_registry      (no FK dependencies)
3. ohlcv_daily         (FK -> stocks)
4. ohlcv_intraday      (FK -> stocks)
5. predictions         (FK -> stocks, FK -> model_registry)
6. drift_logs          (no FK dependencies)
```

After table creation:
```
7. Convert ohlcv_daily to hypertable
8. Convert ohlcv_intraday to hypertable
9. Create additional indexes
```

### Pattern 1: Hypertable Creation After Table Definition

**What:** Create the table with standard DDL first, then call `create_hypertable()` to convert it.
**When to use:** Always -- TimescaleDB requires the table to exist before conversion.
**Example:**
```sql
-- Source: TimescaleDB official docs + GitHub issues
CREATE TABLE ohlcv_daily (
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    date DATE NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    adj_close NUMERIC(12,4),
    volume BIGINT,
    vwap NUMERIC(12,4),
    PRIMARY KEY (ticker, date)
);

SELECT create_hypertable('ohlcv_daily', 'date', chunk_time_interval => INTERVAL '1 month');
```

### Pattern 2: Idempotent init.sql with IF NOT EXISTS

**What:** Use `CREATE TABLE IF NOT EXISTS` and `CREATE EXTENSION IF NOT EXISTS` for idempotency.
**When to use:** Docker entrypoint scripts should be safe to conceptually re-run (though PostgreSQL only runs them on first init).
**Example:**
```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### Pattern 3: updated_at Trigger Function

**What:** Auto-update `updated_at` column on row modification.
**Recommendation (Claude's discretion):** YES -- add a trigger. It is a standard PostgreSQL pattern and prevents stale timestamps.
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_stocks_updated_at
    BEFORE UPDATE ON stocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Pattern 4: Transaction Wrapping

**Recommendation (Claude's discretion):** Wrap the entire init.sql in a single transaction (`BEGIN; ... COMMIT;`). This ensures either all schema objects are created or none are, preventing a half-initialized database. The `create_hypertable` function is safe inside transactions.

### Pattern 5: CASCADE vs No CASCADE for Extension

**Recommendation (Claude's discretion):** Use `CREATE EXTENSION IF NOT EXISTS timescaledb;` WITHOUT CASCADE. The `CASCADE` flag installs dependent extensions automatically, but TimescaleDB on the official Docker image has no unmet dependencies. Avoiding CASCADE is more explicit and predictable.

### Anti-Patterns to Avoid
- **Creating hypertable before defining the table:** `create_hypertable` requires an existing table
- **Omitting partitioning column from PK/unique constraints:** TimescaleDB will reject this with "cannot create a unique index without the column used in partitioning"
- **Adding FK from regular table TO a hypertable:** Not supported by TimescaleDB; fortunately this schema does not require it
- **Mounting ConfigMap as full directory without accounting for existing files:** Already done in Phase 1 scaffold -- init.sql must compensate by including `CREATE EXTENSION`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Time-series partitioning | Custom table inheritance / partition schemes | `create_hypertable()` | Handles chunk management, query optimization, retention automatically |
| Idempotent K8s resources | Custom check-then-create bash logic | `--dry-run=client -o yaml \| kubectl apply -f -` | Established project pattern, atomic, handles create and update |
| Auto-updating timestamps | Application-level updated_at setting | PostgreSQL trigger function | Database-level guarantee, works regardless of client |

## Common Pitfalls

### Pitfall 1: Volume Mount Overwrites TimescaleDB Init Script
**What goes wrong:** The Deployment mounts `postgresql-init-sql` ConfigMap to `/docker-entrypoint-initdb.d`, replacing the image's built-in `000_install_timescaledb.sh` script. TimescaleDB extension is never created.
**Why it happens:** Kubernetes ConfigMap volume mounts replace the entire directory contents.
**How to avoid:** Include `CREATE EXTENSION IF NOT EXISTS timescaledb;` at the top of init.sql. This is MANDATORY.
**Warning signs:** Tables create successfully but `create_hypertable()` fails with "function does not exist".

### Pitfall 2: Wrong Table Creation Order
**What goes wrong:** FK constraint violations during init if tables referencing other tables are created first.
**Why it happens:** `predictions` references both `stocks` and `model_registry`; `ohlcv_*` reference `stocks`.
**How to avoid:** Follow the dependency order: stocks, model_registry, then ohlcv tables, then predictions, then drift_logs.
**Warning signs:** `ERROR: relation "stocks" does not exist` during container startup.

### Pitfall 3: create_hypertable on Table with Incompatible PK
**What goes wrong:** If PK does not include the time partitioning column, hypertable creation fails.
**Why it happens:** TimescaleDB requires partition column in all unique/PK constraints for chunk-level enforcement.
**How to avoid:** Use composite PKs: `(ticker, date)` for ohlcv_daily, `(ticker, timestamp)` for ohlcv_intraday -- both include the partition column.
**Warning signs:** Error "cannot create a unique index without the column used in partitioning".

### Pitfall 4: deploy-all.sh Has Wrong File Names
**What goes wrong:** The commented Phase 4 section in deploy-all.sh references `postgres-pvc.yaml`, `postgres-deployment.yaml`, `postgres-service.yaml`, `postgres-configmap.yaml` -- but the actual files are `postgresql-pvc.yaml`, `postgresql-deployment.yaml`, and `configmap.yaml`. Also, the Service is bundled inside `postgresql-deployment.yaml`, not a separate file.
**Why it happens:** Phase 1 scaffold used different naming than the placeholder comments assumed.
**How to avoid:** When uncommenting, fix the paths to match actual files:
```bash
kubectl apply -f "$PROJECT_ROOT/k8s/storage/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-deployment.yaml"
```
**Warning signs:** `kubectl apply` errors about missing files.

### Pitfall 5: Init Script Runs Only on First Database Init
**What goes wrong:** If the PVC already has data from a previous run, `/docker-entrypoint-initdb.d` scripts are skipped entirely.
**Why it happens:** PostgreSQL Docker entrypoint only runs init scripts when `PGDATA` directory is empty.
**How to avoid:** For development iteration, delete the PVC or the pod's data to force re-initialization. Document this in verification steps.
**Warning signs:** Schema changes in init.sql don't take effect after pod restart.

### Pitfall 6: ConfigMap Key Name Mismatch
**What goes wrong:** The ConfigMap key determines the filename inside the mounted directory. If the key does not end in `.sql`, PostgreSQL will not execute it.
**Why it happens:** `kubectl create configmap --from-file=init.sql=path/to/init.sql` creates a key named `init.sql`. This is correct. But if the flag syntax is wrong, the key name could be the full path.
**How to avoid:** Use the exact pattern from CONTEXT.md: `--from-file=init.sql=stock-prediction-platform/db/init.sql`
**Warning signs:** Pod starts but tables don't exist; check `kubectl describe configmap postgresql-init-sql -n storage` to verify key name.

## Code Examples

### Complete init.sql Structure
```sql
-- init.sql -- Stock Prediction Platform Database Schema
-- Executed by PostgreSQL docker-entrypoint on first initialization
-- IMPORTANT: CREATE EXTENSION is required here because the K8s ConfigMap
-- volume mount overwrites the image's built-in 000_install_timescaledb.sh

BEGIN;

-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1. stocks (reference table, no FK deps)
CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. model_registry (no FK deps)
CREATE TABLE IF NOT EXISTS model_registry (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    metrics_json JSONB NOT NULL,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT false
);

-- 3. ohlcv_daily (FK -> stocks, will become hypertable)
CREATE TABLE IF NOT EXISTS ohlcv_daily (
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    date DATE NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    adj_close NUMERIC(12,4),
    volume BIGINT,
    vwap NUMERIC(12,4),
    PRIMARY KEY (ticker, date)
);

-- 4. ohlcv_intraday (FK -> stocks, will become hypertable)
CREATE TABLE IF NOT EXISTS ohlcv_intraday (
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    adj_close NUMERIC(12,4),
    volume BIGINT,
    vwap NUMERIC(12,4),
    PRIMARY KEY (ticker, timestamp)
);

-- 5. predictions (FK -> stocks, FK -> model_registry)
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    prediction_date DATE NOT NULL,
    predicted_date DATE NOT NULL,
    predicted_price NUMERIC(12,4) NOT NULL,
    model_id INTEGER NOT NULL REFERENCES model_registry(model_id),
    confidence NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. drift_logs (no FK deps)
CREATE TABLE IF NOT EXISTS drift_logs (
    id BIGSERIAL PRIMARY KEY,
    drift_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    details_json JSONB NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to TimescaleDB hypertables
SELECT create_hypertable('ohlcv_daily', 'date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

SELECT create_hypertable('ohlcv_intraday', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Additional indexes
CREATE INDEX IF NOT EXISTS idx_ohlcv_daily_ticker ON ohlcv_daily (ticker);
CREATE INDEX IF NOT EXISTS idx_ohlcv_intraday_ticker ON ohlcv_intraday (ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON predictions (ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions (model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_prediction_date ON predictions (prediction_date);
CREATE INDEX IF NOT EXISTS idx_drift_logs_drift_type ON drift_logs (drift_type);
CREATE INDEX IF NOT EXISTS idx_drift_logs_detected_at ON drift_logs (detected_at);
CREATE INDEX IF NOT EXISTS idx_model_registry_is_active ON model_registry (is_active);

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_stocks_updated_at
    BEFORE UPDATE ON stocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
```

### setup-minikube.sh Additions (after namespace apply, before verification)
```bash
# --- Phase 4: PostgreSQL secrets and init SQL ---
echo "=== Creating PostgreSQL secret (dev-only password) ==="
kubectl create secret generic stock-platform-secrets \
  --from-literal=POSTGRES_PASSWORD=devpassword123 \
  -n storage \
  --dry-run=client -o yaml | kubectl apply -f -

echo "=== Creating PostgreSQL init SQL ConfigMap ==="
kubectl create configmap postgresql-init-sql \
  --from-file=init.sql="$PROJECT_ROOT/db/init.sql" \
  -n storage \
  --dry-run=client -o yaml | kubectl apply -f -
```

### deploy-all.sh Phase 4 Section (corrected file paths)
```bash
# --- Phase 4: Storage (PostgreSQL + TimescaleDB) ---
echo "[Phase 4] Deploying PostgreSQL + TimescaleDB..."
kubectl apply -f "$PROJECT_ROOT/k8s/storage/configmap.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-pvc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s/storage/postgresql-deployment.yaml"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `create_hypertable(relation, time_column_name)` positional args | Same API, but `if_not_exists => TRUE` parameter available | TimescaleDB 2.0+ | Enables idempotent hypertable creation |
| Manual partitioning with PG table inheritance | `create_hypertable()` with `chunk_time_interval` | TimescaleDB 1.0+ | Fully automated chunk management |
| Separate `CREATE INDEX` for time column | Hypertable auto-creates time index | TimescaleDB 1.0+ | No need for explicit time-column index on hypertables |

**Note:** TimescaleDB docs recently moved from `docs.timescale.com` to `tigerdata.com/docs` (301 redirect). The API remains the same.

## Open Questions

1. **create_hypertable IF NOT EXISTS behavior with existing hypertable**
   - What we know: `if_not_exists => TRUE` parameter prevents errors when re-running
   - What's unclear: Behavior if table exists as regular table (not hypertable) from a failed partial init
   - Recommendation: Use `BEGIN/COMMIT` transaction wrapping so partial states cannot occur

2. **TimescaleDB version in `latest-pg15` tag**
   - What we know: The image tag is `timescale/timescaledb:latest-pg15`, which pulls the latest TimescaleDB compatible with PG15
   - What's unclear: Exact TimescaleDB version (could be 2.x)
   - Recommendation: Not critical for this phase; `create_hypertable` API is stable across 2.x versions

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | bash + kubectl (infrastructure validation) |
| Config file | none -- shell-based verification |
| Quick run command | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "\\dt"` |
| Full suite command | See per-requirement commands below |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DB-01 | PostgreSQL pod running in storage namespace | smoke | `kubectl get pods -n storage -l app=postgresql -o jsonpath='{.items[0].status.phase}'` (expect "Running") | N/A -- CLI |
| DB-02 | TimescaleDB extension enabled | smoke | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "SELECT extname FROM pg_extension WHERE extname='timescaledb';"` | N/A -- CLI |
| DB-03 | All 6 tables exist | smoke | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"` (expect 6 tables) | N/A -- CLI |
| DB-04 | Composite PKs on ohlcv tables | smoke | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "SELECT conname FROM pg_constraint WHERE contype='p' AND conrelid='ohlcv_daily'::regclass;"` | N/A -- CLI |
| DB-05 | Indexes on ticker columns | smoke | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "SELECT indexname FROM pg_indexes WHERE tablename IN ('ohlcv_daily','ohlcv_intraday') ORDER BY indexname;"` | N/A -- CLI |
| DB-06 | Hypertables with correct chunk intervals | smoke | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "SELECT hypertable_name, chunk_time_interval FROM timescaledb_information.hypertables;"` | N/A -- CLI |
| DB-07 | Secret and ConfigMap exist in storage namespace | smoke | `kubectl get secret stock-platform-secrets -n storage && kubectl get configmap postgresql-init-sql -n storage && kubectl get configmap storage-config -n storage` | N/A -- CLI |

### Sampling Rate
- **Per task commit:** Verify init.sql syntax with `psql -f` dry-run if local psql available, otherwise review only
- **Per wave merge:** Full deployment to Minikube + all smoke commands above
- **Phase gate:** All 7 smoke tests pass on running cluster

### Wave 0 Gaps
None -- this phase uses kubectl CLI verification against a running cluster, not a test framework. No test files to create.

## Sources

### Primary (HIGH confidence)
- [TimescaleDB create_hypertable docs](https://docs.timescale.com/api/latest/hypertable/create_hypertable/) - PK must include partition column, if_not_exists parameter
- [TimescaleDB constraint docs](https://docs.timescale.com/use-timescale/latest/schema-management/about-constraints/) - Unique/PK constraint rules
- [TimescaleDB Docker 000_install_timescaledb.sh](https://github.com/timescale/timescaledb-docker/blob/main/docker-entrypoint-initdb.d/000_install_timescaledb.sh) - Image auto-installs extension via this script
- Existing project files (Deployment YAML, ConfigMap, PVC, setup-minikube.sh, deploy-all.sh) - actual scaffold code

### Secondary (MEDIUM confidence)
- [TimescaleDB GitHub Issue #1394](https://github.com/timescale/timescaledb/issues/1394) - FK constraints to hypertables not supported
- [TimescaleDB GitHub Issue #6452](https://github.com/timescale/timescaledb/issues/6452) - Converting FK-referenced table to hypertable breaks inserts
- [TimescaleDB GitHub Issue #3386](https://github.com/timescale/timescaledb/issues/3386) - Hypertable PK requirements
- [Kubernetes ConfigMap volume mount behavior](https://kubernetes.io/docs/concepts/storage/volumes/) - Full directory replacement confirmed

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - image and tools are fixed by existing scaffold
- Architecture: HIGH - schema is fully specified in CONTEXT.md, TimescaleDB constraints verified via official docs and GitHub
- Pitfalls: HIGH - volume mount overwrite and FK limitations confirmed by multiple sources

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable domain, PostgreSQL 15 + TimescaleDB API unlikely to change)
