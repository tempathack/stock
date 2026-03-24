-- 003_feature_store.sql — Feature store — precomputed technical indicators and lag features
--
-- Stores (ticker, date, feature_name, feature_value) in EAV format.
-- Populated daily by CronJob after US market close.
-- Composite PK ensures idempotent upserts.

BEGIN;

-- ============================================================
-- feature_store — Precomputed features keyed by (ticker, date, feature_name)
-- ============================================================
CREATE TABLE IF NOT EXISTS feature_store (
    ticker        VARCHAR(10)    NOT NULL REFERENCES stocks(ticker),
    date          DATE           NOT NULL,
    feature_name  VARCHAR(100)   NOT NULL,
    feature_value NUMERIC(18,8),
    computed_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (ticker, date, feature_name)
);

COMMENT ON TABLE feature_store IS
    'Precomputed features keyed by (ticker, date, feature_name). Populated daily by CronJob.';

-- ============================================================
-- Indexes for efficient lookups
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_feature_store_ticker_date
    ON feature_store (ticker, date);

CREATE INDEX IF NOT EXISTS idx_feature_store_feature_name
    ON feature_store (feature_name);

CREATE INDEX IF NOT EXISTS idx_feature_store_computed_at
    ON feature_store (computed_at);

COMMIT;
