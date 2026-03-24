#!/bin/bash
set -e

# Use admin URL for migrations (DDL requires full privileges)
ALEMBIC_DB_URL="${DATABASE_URL_ADMIN:-$DATABASE_URL}"

# Run Alembic migrations if a database URL is configured
if [ -n "$ALEMBIC_DB_URL" ]; then
    echo "[entrypoint] Checking database migration state..."
    # If the schema was bootstrapped via db/init.sql (tables exist but no alembic_version),
    # stamp the current head so subsequent runs apply only incremental migrations.
    TABLES_EXIST=$(DATABASE_URL="$ALEMBIC_DB_URL" python -c "
import os, psycopg2
url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://').replace('asyncpg://', 'postgresql://')
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute(\"SELECT to_regclass('public.stocks')\")
    stocks_exists = cur.fetchone()[0] is not None
    cur.execute(\"SELECT to_regclass('public.alembic_version')\")
    alembic_exists = cur.fetchone()[0] is not None
    conn.close()
    print('stamped' if alembic_exists else ('needs_stamp' if stocks_exists else 'empty'))
except Exception as e:
    print('empty')
" 2>/dev/null || echo 'empty')

    if [ "$TABLES_EXIST" = "needs_stamp" ]; then
        echo "[entrypoint] Schema already exists (bootstrapped via init.sql) — stamping Alembic head..."
        DATABASE_URL="$ALEMBIC_DB_URL" alembic stamp head
        echo "[entrypoint] Stamp complete."
    fi

    echo "[entrypoint] Running database migrations..."
    DATABASE_URL="$ALEMBIC_DB_URL" alembic upgrade head
    echo "[entrypoint] Migrations complete."
else
    echo "[entrypoint] DATABASE_URL not set — skipping migrations."
fi

# Start the API server (DATABASE_URL is the readonly connection)
echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
