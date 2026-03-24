-- 002_rbac_roles.sql — Database RBAC for stock-prediction-platform
--
-- Role mapping:
--   stockuser      → admin (DDL, schema migrations via Alembic)
--   stock_readonly  → SELECT only (API reads, model serving)
--   stock_writer    → DML (Kafka consumer upserts, ML predictions, drift logs)
--
-- Passwords are set from environment variables during deploy.
-- This script uses placeholder passwords; deploy-all.sh overrides them.
--
-- Idempotent: safe to re-run.

BEGIN;

-- ============================================================
-- 1. Create roles (idempotent via DO block)
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'stock_readonly') THEN
        CREATE ROLE stock_readonly LOGIN PASSWORD 'readonly_changeme';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'stock_writer') THEN
        CREATE ROLE stock_writer LOGIN PASSWORD 'writer_changeme';
    END IF;
END
$$;

-- ============================================================
-- 2. stock_readonly — SELECT only
-- ============================================================
GRANT CONNECT ON DATABASE stockdb TO stock_readonly;
GRANT USAGE ON SCHEMA public TO stock_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO stock_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO stock_readonly;

-- ============================================================
-- 3. stock_writer — full DML (no DDL)
-- ============================================================
GRANT CONNECT ON DATABASE stockdb TO stock_writer;
GRANT USAGE ON SCHEMA public TO stock_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO stock_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO stock_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO stock_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO stock_writer;

COMMIT;
