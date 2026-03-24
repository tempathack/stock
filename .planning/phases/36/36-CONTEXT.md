# Phase 36 — Secrets Management & DB RBAC

## What This Phase Delivers

Eliminate all hardcoded database credentials from K8s configmaps, application defaults, and committed files. Introduce database role-based access control so each service connects with least-privilege credentials.

1. **K8s Secret manifest** — `stock-platform-secrets` containing `POSTGRES_PASSWORD` and per-role `DATABASE_URL` values
2. **Credential removal** — All configmaps, docker-compose, alembic.ini, Python defaults scrubbed of plaintext passwords
3. **DB RBAC roles** — `stock_readonly` (API reads), `stock_writer` (consumer + ML pipeline), enforced via per-service DATABASE_URL
4. **Gitignore + docs** — Secret YAML gitignored; README documents Sealed Secrets workflow

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| DBHARD-06 | K8s Secrets replace hardcoded credentials in configmaps | `k8s/storage/secrets.yaml` (gitignored), updated configmaps & deployments |
| DBHARD-07 | Database RBAC roles: stock_readonly (API), stock_writer (consumer + ML) | `db/migrations/002_rbac_roles.sql`, per-service SECRET_KEY references |

## Architecture

### Current State (Phase 35)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Credential Distribution — INSECURE                                  │
│                                                                     │
│  k8s/ml/configmap.yaml                                              │
│    DATABASE_URL: "postgresql://stockuser:stockpass@..."              │
│    ↑ plaintext password in a ConfigMap (viewable by any pod)        │
│                                                                     │
│  docker-compose.yml                                                 │
│    DATABASE_URL=postgresql://stockuser:stockpass@...                 │
│    ↑ hardcoded in committed file                                    │
│                                                                     │
│  services/kafka-consumer/consumer/config.py                         │
│    DATABASE_URL default: "...devpassword123..."                     │
│    ↑ password in source code                                        │
│                                                                     │
│  services/api/alembic.ini                                           │
│    sqlalchemy.url = "...devpassword123..."                          │
│    ↑ password in committed config                                   │
│                                                                     │
│  ml/pipelines/components/data_loader.py                             │
│    POSTGRES_PASSWORD default: "devpassword123"                      │
│    ↑ password as Python default value                               │
│                                                                     │
│  db/init.sql                                                        │
│    -- DEV NOTE: ... Password: devpassword123                        │
│    ↑ password in SQL comment                                        │
│                                                                     │
│  SINGLE USER: stockuser owns everything — no role separation        │
└─────────────────────────────────────────────────────────────────────┘

What's already correct:
  ✓ k8s/storage/postgresql-deployment.yaml  → POSTGRES_PASSWORD from secretKeyRef
  ✓ k8s/processing/kafka-consumer-deployment.yaml → secretRef: stock-platform-secrets
  ✓ k8s/ml/model-serving.yaml → secretRef: stock-platform-secrets
  ✓ k8s/ml/cronjob-training.yaml → secretRef: stock-platform-secrets (optional: true)
  ✓ k8s/ml/cronjob-drift.yaml → secretRef: stock-platform-secrets (optional: true)
  ✓ services/api/app/config.py → DATABASE_URL: Optional[str] = None (no hardcoded default)
```

### Target State (Phase 36)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Credential Distribution — SECURE                                    │
│                                                                     │
│  k8s/storage/secrets.yaml (GITIGNORED — never committed)            │
│    POSTGRES_PASSWORD: <base64>                                      │
│    DATABASE_URL_READONLY: postgresql://stock_readonly:...@.../stockdb│
│    DATABASE_URL_WRITER:   postgresql://stock_writer:...@.../stockdb │
│    DATABASE_URL_ADMIN:    postgresql://stockuser:...@.../stockdb    │
│                                                                     │
│  k8s/storage/secrets.yaml.example (committed — template, no values) │
│                                                                     │
│  k8s/ml/configmap.yaml → DATABASE_URL REMOVED                      │
│  docker-compose.yml    → uses .env file (gitignored)                │
│  alembic.ini           → placeholder only (env.py overrides)        │
│  consumer/config.py    → DATABASE_URL default = "" (fail fast)      │
│  data_loader.py        → POSTGRES_PASSWORD no fallback (required)   │
│  db/init.sql           → password comment removed                   │
│                                                                     │
│  deploy-all.sh         → applies secrets.yaml first                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ Database RBAC                                                       │
│                                                                     │
│  db/migrations/002_rbac_roles.sql                                   │
│    CREATE ROLE stock_readonly LOGIN PASSWORD '<from_env>';          │
│    GRANT CONNECT, SELECT on all tables → stock_readonly             │
│                                                                     │
│    CREATE ROLE stock_writer LOGIN PASSWORD '<from_env>';            │
│    GRANT CONNECT, SELECT, INSERT, UPDATE, DELETE → stock_writer     │
│                                                                     │
│  Service → Role mapping:                                            │
│    stock-api (ingestion)     → stock_readonly (read-only queries)   │
│    model-serving (ml)        → stock_readonly (read-only queries)   │
│    kafka-consumer (processing) → stock_writer (upserts to OHLCV)   │
│    cronjob-training (ml)     → stock_writer (writes predictions)   │
│    cronjob-drift (ml)        → stock_writer (writes drift_logs)    │
│    alembic migrations        → stockuser (admin — DDL operations)  │
└─────────────────────────────────────────────────────────────────────┘
```

### Secret Flow — Per-Service

```
stock-platform-secrets (K8s Secret in storage namespace)
  │
  ├── POSTGRES_PASSWORD  → postgresql-deployment.yaml (admin init)
  ├── DATABASE_URL       → stock-api (admin for alembic, readonly for app)
  ├── DATABASE_URL       → kafka-consumer (stock_writer)
  ├── DATABASE_URL       → model-serving (stock_readonly)
  ├── DATABASE_URL       → cronjob-training (stock_writer)
  └── DATABASE_URL       → cronjob-drift (stock_writer)

Each namespace needs its own copy of the Secret (K8s Secrets are namespace-scoped):
  - storage:    stock-platform-secrets (POSTGRES_PASSWORD)
  - ingestion:  stock-platform-secrets (DATABASE_URL with stock_readonly)
  - processing: stock-platform-secrets (DATABASE_URL with stock_writer)
  - ml:         stock-platform-secrets (DATABASE_URL with stock_writer)
```

### Key Design Decisions

1. **Namespace-scoped secrets** — K8s Secrets don't cross namespaces; `secrets.yaml` creates one Secret per namespace with the appropriate DATABASE_URL per service role
2. **DATABASE_URL in Secret, not ConfigMap** — The full connection string (including password) lives in the Secret; ConfigMaps retain only non-sensitive config (Kafka brokers, topics, log level)
3. **Three DB roles** — `stockuser` (admin/DDL), `stock_readonly` (SELECT only), `stock_writer` (DML only). Alembic migrations use admin; API reads use readonly; consumer/ML writes use writer
4. **secrets.yaml.example** — A committed template with placeholder values so developers know the expected keys without leaking actual passwords
5. **.env for docker-compose** — Local dev uses a .env file (already .gitignored) with passwords; docker-compose.yml references `${POSTGRES_PASSWORD}` etc.
6. **CronJob secretRef not optional** — Remove `optional: true` from ML CronJob secretRef since the Secret is now required, not optional
7. **SQL migration for roles** — A `db/migrations/002_rbac_roles.sql` script creates roles and grants; runs once during setup

## Credential Inventory — Changes Required

| File | Current Issue | Fix |
|------|--------------|-----|
| k8s/ml/configmap.yaml | DATABASE_URL with password `stockpass` | Remove DATABASE_URL line |
| docker-compose.yml | Hardcoded `stockpass` in DATABASE_URL | Use `${POSTGRES_PASSWORD}` from .env |
| services/kafka-consumer/consumer/config.py | Default `devpassword123` | Default empty string, fail fast |
| services/api/alembic.ini | Hardcoded `devpassword123` | Use `driver://` placeholder |
| ml/pipelines/components/data_loader.py | Default `devpassword123` | Remove fallback, require env var |
| db/init.sql | Password in comment | Remove comment |

## Key References

| File | Purpose |
|------|---------|
| k8s/storage/postgresql-deployment.yaml | Already uses secretKeyRef correctly |
| k8s/processing/kafka-consumer-deployment.yaml | Already uses secretRef correctly |
| k8s/ml/model-serving.yaml | Already uses secretRef correctly |
| services/api/app/config.py | DATABASE_URL = None (already correct) |
| scripts/deploy-all.sh | Needs to apply secrets.yaml before deployments |
| .gitignore | Already has `.env`; needs `**/secrets.yaml` pattern |
