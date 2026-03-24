#!/bin/bash
set -e

# Use admin URL for migrations (DDL requires full privileges)
ALEMBIC_DB_URL="${DATABASE_URL_ADMIN:-$DATABASE_URL}"

# Run Alembic migrations if a database URL is configured
if [ -n "$ALEMBIC_DB_URL" ]; then
    echo "[entrypoint] Running database migrations..."
    DATABASE_URL="$ALEMBIC_DB_URL" alembic upgrade head
    echo "[entrypoint] Migrations complete."
else
    echo "[entrypoint] DATABASE_URL not set — skipping migrations."
fi

# Start the API server (DATABASE_URL is the readonly connection)
echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
