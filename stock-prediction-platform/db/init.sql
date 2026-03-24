-- init.sql — Stock Prediction Platform Database Schema
-- Executed by PostgreSQL docker-entrypoint on first initialization
--
-- IMPORTANT: CREATE EXTENSION is required here because the K8s ConfigMap
-- volume mount at /docker-entrypoint-initdb.d replaces the image's built-in
-- 000_install_timescaledb.sh script. Without this line, TimescaleDB is never enabled.

BEGIN;

-- ============================================================
-- Enable TimescaleDB extension
-- ============================================================
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- 1. stocks — Reference table for S&P 500 universe (no FK deps)
-- ============================================================
CREATE TABLE IF NOT EXISTS stocks (
    ticker       VARCHAR(10)  PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector       VARCHAR(100),
    industry     VARCHAR(100),
    market_cap   BIGINT,
    is_active    BOOLEAN      NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. model_registry — ML model catalog (no FK deps)
-- ============================================================
CREATE TABLE IF NOT EXISTS model_registry (
    model_id       SERIAL        PRIMARY KEY,
    model_name     VARCHAR(100)  NOT NULL,
    version        VARCHAR(50)   NOT NULL,
    metrics_json   JSONB         NOT NULL,
    trained_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    is_active      BOOLEAN       NOT NULL DEFAULT false,
    traffic_weight NUMERIC(5,4)  NOT NULL DEFAULT 0.0,
    CONSTRAINT chk_traffic_weight_range CHECK (traffic_weight >= 0.0 AND traffic_weight <= 1.0)
);

-- ============================================================
-- 3. ohlcv_daily — Daily OHLCV bars (FK -> stocks; becomes hypertable)
-- ============================================================
CREATE TABLE IF NOT EXISTS ohlcv_daily (
    ticker     VARCHAR(10)   NOT NULL REFERENCES stocks(ticker),
    date       DATE          NOT NULL,
    open       NUMERIC(12,4),
    high       NUMERIC(12,4),
    low        NUMERIC(12,4),
    close      NUMERIC(12,4),
    adj_close  NUMERIC(12,4),
    volume     BIGINT,
    vwap       NUMERIC(12,4),
    PRIMARY KEY (ticker, date)
);

-- ============================================================
-- 4. ohlcv_intraday — Intraday OHLCV bars (FK -> stocks; becomes hypertable)
-- ============================================================
CREATE TABLE IF NOT EXISTS ohlcv_intraday (
    ticker     VARCHAR(10)   NOT NULL REFERENCES stocks(ticker),
    timestamp  TIMESTAMPTZ   NOT NULL,
    open       NUMERIC(12,4),
    high       NUMERIC(12,4),
    low        NUMERIC(12,4),
    close      NUMERIC(12,4),
    adj_close  NUMERIC(12,4),
    volume     BIGINT,
    vwap       NUMERIC(12,4),
    PRIMARY KEY (ticker, timestamp)
);

-- ============================================================
-- 5. predictions — Model predictions (FK -> stocks, FK -> model_registry)
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions (
    id               BIGSERIAL    PRIMARY KEY,
    ticker           VARCHAR(10)  NOT NULL REFERENCES stocks(ticker),
    prediction_date  DATE         NOT NULL,
    predicted_date   DATE         NOT NULL,
    predicted_price  NUMERIC(12,4) NOT NULL,
    model_id         INTEGER      NOT NULL REFERENCES model_registry(model_id),
    confidence       NUMERIC(5,4),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 6. drift_logs — Model and data drift events (no FK deps)
-- ============================================================
CREATE TABLE IF NOT EXISTS drift_logs (
    id           BIGSERIAL    PRIMARY KEY,
    drift_type   VARCHAR(50)  NOT NULL,
    severity     VARCHAR(20)  NOT NULL,
    details_json JSONB        NOT NULL,
    detected_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Convert OHLCV tables to TimescaleDB hypertables
-- Must be called AFTER table creation.
-- if_not_exists => TRUE makes this idempotent on re-runs.
-- ============================================================
SELECT create_hypertable(
    'ohlcv_daily',
    'date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

SELECT create_hypertable(
    'ohlcv_intraday',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================
-- Additional indexes (composite PKs already create PK indexes)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_ohlcv_daily_ticker        ON ohlcv_daily (ticker);
CREATE INDEX IF NOT EXISTS idx_ohlcv_intraday_ticker     ON ohlcv_intraday (ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker        ON predictions (ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id      ON predictions (model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_date          ON predictions (prediction_date);
CREATE INDEX IF NOT EXISTS idx_drift_logs_drift_type     ON drift_logs (drift_type);
CREATE INDEX IF NOT EXISTS idx_drift_logs_detected_at    ON drift_logs (detected_at);
CREATE INDEX IF NOT EXISTS idx_model_registry_is_active  ON model_registry (is_active);
CREATE INDEX IF NOT EXISTS idx_model_registry_traffic_weight ON model_registry(traffic_weight) WHERE traffic_weight > 0;

-- ============================================================
-- 7. ab_test_assignments — A/B model test tracking (FK -> stocks, model_registry)
-- ============================================================
CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id              BIGSERIAL     PRIMARY KEY,
    ticker          VARCHAR(10)   NOT NULL REFERENCES stocks(ticker),
    model_id        INTEGER       NOT NULL REFERENCES model_registry(model_id),
    model_name      VARCHAR(100)  NOT NULL,
    predicted_price NUMERIC(12,4) NOT NULL,
    actual_price    NUMERIC(12,4),
    horizon_days    INTEGER       NOT NULL DEFAULT 7,
    assigned_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    evaluated_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ab_test_model_id    ON ab_test_assignments(model_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_ticker      ON ab_test_assignments(ticker);
CREATE INDEX IF NOT EXISTS idx_ab_test_assigned_at ON ab_test_assignments(assigned_at);

-- ============================================================
-- Auto-update updated_at on stocks row modification
-- ============================================================
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
    EXECUTE FUNCTION update_updated_at_column();pl

COMMIT;
