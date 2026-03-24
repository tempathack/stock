-- Migration 004: A/B Model Testing
-- Adds traffic_weight to model_registry and creates ab_test_assignments table.

BEGIN;

-- 1. Add traffic_weight column to model_registry
ALTER TABLE model_registry
  ADD COLUMN IF NOT EXISTS traffic_weight NUMERIC(5,4) NOT NULL DEFAULT 0.0;

ALTER TABLE model_registry
  ADD CONSTRAINT chk_traffic_weight_range
  CHECK (traffic_weight >= 0.0 AND traffic_weight <= 1.0);

COMMENT ON COLUMN model_registry.traffic_weight
  IS 'Fraction of prediction traffic routed to this model (0.0–1.0).';

-- 2. Partial index for fast lookup of models receiving traffic
CREATE INDEX IF NOT EXISTS idx_model_registry_traffic_weight
  ON model_registry(traffic_weight) WHERE traffic_weight > 0;

-- 3. Create ab_test_assignments table
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

-- 4. Indexes for ab_test_assignments
CREATE INDEX IF NOT EXISTS idx_ab_test_model_id    ON ab_test_assignments(model_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_ticker      ON ab_test_assignments(ticker);
CREATE INDEX IF NOT EXISTS idx_ab_test_assigned_at ON ab_test_assignments(assigned_at);

COMMIT;
