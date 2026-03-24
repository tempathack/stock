# Phase 35 — Alembic Migration System

## What This Phase Delivers

Database schema versioning with Alembic, SQLAlchemy declarative ORM models matching init.sql, and an initial migration that can create/destroy the full schema.

1. **alembic.ini + env.py + versions/** — Standard Alembic project structure in `services/api/`
2. **SQLAlchemy ORM models** — Declarative models for all 6 tables matching `db/init.sql` exactly
3. **Initial migration** — `alembic upgrade head` creates all tables, indexes, triggers; `alembic downgrade base` removes them
4. **API Dockerfile update** — Runs `alembic upgrade head` as startup init step before uvicorn

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| DBHARD-01 | Alembic configured with alembic.ini, env.py, versions/ directory | `services/api/alembic.ini`, `services/api/alembic/env.py`, `services/api/alembic/versions/` |
| DBHARD-02 | Initial migration matching db/init.sql (all 6 tables) | `services/api/alembic/versions/001_initial_schema.py` |
| DBHARD-03 | API Dockerfile runs `alembic upgrade head` on startup | `services/api/Dockerfile` (modified), `services/api/entrypoint.sh` |

## Architecture

### Current State (Phase 34)

```
┌─────────────────────────────────────────────────┐
│ Database Schema                                  │
│                                                  │
│  db/init.sql — executed once by PostgreSQL       │
│    docker-entrypoint-initdb.d on first boot      │
│                                                  │
│  No schema versioning                            │
│  No ORM layer                                    │
│  No migration history                            │
│  Schema changes = manual SQL edits + redeploy    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ API Service (services/api/)                      │
│                                                  │
│  app/config.py      → DATABASE_URL env var       │
│  app/models/schemas.py → Pydantic only (no ORM) │
│  requirements.txt   → already has:               │
│    sqlalchemy==2.0.30                            │
│    asyncpg==0.29.0                               │
│    alembic==1.13.1                               │
│                                                  │
│  Dockerfile CMD: uvicorn only (no migration)     │
└─────────────────────────────────────────────────┘
```

### Target State (Phase 35)

```
┌─────────────────────────────────────────────────┐
│ services/api/                                    │
│ ├── alembic.ini          ← Alembic config        │
│ ├── alembic/                                     │
│ │   ├── env.py           ← migration runner      │
│ │   ├── script.py.mako   ← template              │
│ │   └── versions/                                │
│ │       └── 001_initial_schema.py                │
│ ├── app/                                         │
│ │   ├── models/                                  │
│ │   │   ├── orm.py       ← SQLAlchemy models     │
│ │   │   └── schemas.py   ← Pydantic (unchanged) │
│ │   └── ...                                      │
│ ├── entrypoint.sh        ← alembic + uvicorn     │
│ └── Dockerfile           ← COPY + CMD updated    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Migration Flow                                   │
│                                                  │
│  1. Pod starts → entrypoint.sh runs              │
│  2. alembic upgrade head → applies pending       │
│  3. uvicorn starts → API ready                   │
│                                                  │
│  Dev workflow:                                    │
│    alembic revision --autogenerate -m "..."      │
│    alembic upgrade head                          │
│    alembic downgrade -1                          │
└─────────────────────────────────────────────────┘
```

### ORM ↔ init.sql Mapping

```
db/init.sql                  →  app/models/orm.py
─────────────────────────────────────────────────
CREATE TABLE stocks          →  class Stock(Base)
CREATE TABLE model_registry  →  class ModelRegistry(Base)
CREATE TABLE ohlcv_daily     →  class OHLCVDaily(Base)
CREATE TABLE ohlcv_intraday  →  class OHLCVIntraday(Base)
CREATE TABLE predictions     →  class Prediction(Base)
CREATE TABLE drift_logs      →  class DriftLog(Base)

TimescaleDB hypertables      →  Alembic op.execute() raw SQL
update_updated_at_column()   →  Alembic op.execute() raw SQL
Indexes                      →  Alembic op.create_index() calls
```

### Key Design Decisions

1. **Alembic lives in services/api/** — co-located with the API service that owns the DB connection; not in db/ to avoid coupling
2. **Sync Alembic driver** — Alembic's migration runner uses sync `psycopg2` (via `sqlalchemy.url` in alembic.ini), even though the app uses async `asyncpg`. This is standard practice.
3. **psycopg2-binary** — Must be added to requirements.txt for Alembic's sync connection (asyncpg cannot run sync migrations)
4. **TimescaleDB hypertables** — Cannot be expressed in ORM; handled as `op.execute()` raw SQL in migration upgrade/downgrade
5. **Trigger functions** — Same as hypertables: raw SQL in migration, not in ORM models
6. **entrypoint.sh pattern** — Shell script runs `alembic upgrade head` then `exec uvicorn ...`; replaces direct CMD in Dockerfile

### Dependency Note

Phase 40 (SQLAlchemy Connection Pooling) will reuse the ORM models created here. The `orm.py` module creates the `Base` and model classes; Phase 40 adds the async engine/session factory.

## Key References

| File | Purpose |
|------|---------|
| db/init.sql | Source of truth for all 6 tables, indexes, triggers, hypertables |
| services/api/requirements.txt | Already has sqlalchemy, asyncpg, alembic |
| services/api/Dockerfile | Current state: no migration step |
| services/api/app/config.py | DATABASE_URL env var |
| services/api/app/models/schemas.py | Pydantic schemas (unchanged by this phase) |
