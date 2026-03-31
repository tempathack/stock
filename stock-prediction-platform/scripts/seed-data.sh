#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# seed-data.sh — Populate all 6 PostgreSQL tables with
# realistic S&P 500 test data for development.
#
# Usage:
#   bash scripts/seed-data.sh
#
# Connection defaults match K8s storage-config ConfigMap.
# Override via environment variables.
# ============================================================

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-stockuser}"
PGPASSWORD="${PGPASSWORD:-devpassword123}"
PGDATABASE="${PGDATABASE:-stockdb}"
export PGPASSWORD

PSQL="psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -v ON_ERROR_STOP=1"

echo "=== Seeding database $PGDATABASE@$PGHOST:$PGPORT ==="

# ============================================================
# Section 1 — stocks (20 S&P 500 tickers)
# ============================================================
echo "  → stocks …"
$PSQL -q <<'SQL'
INSERT INTO stocks (ticker, company_name, sector, industry, market_cap) VALUES
('AAPL', 'Apple Inc.',             'Technology',              'Consumer Electronics',            3400000000000),
('MSFT', 'Microsoft Corp.',        'Technology',              'Software—Infrastructure',         3100000000000),
('GOOGL','Alphabet Inc.',          'Communication Services',  'Internet Content & Information',  2100000000000),
('AMZN', 'Amazon.com Inc.',        'Consumer Cyclical',       'Internet Retail',                 1900000000000),
('NVDA', 'NVIDIA Corp.',           'Technology',              'Semiconductors',                  2800000000000),
('META', 'Meta Platforms Inc.',    'Communication Services',  'Internet Content & Information',  1500000000000),
('TSLA', 'Tesla Inc.',             'Consumer Cyclical',       'Auto Manufacturers',               800000000000),
('BRK-B','Berkshire Hathaway Inc.','Financial Services',      'Insurance—Diversified',            900000000000),
('JPM',  'JPMorgan Chase & Co.',   'Financial Services',      'Banks—Diversified',                600000000000),
('JNJ',  'Johnson & Johnson',      'Healthcare',              'Drug Manufacturers—General',       380000000000),
('V',    'Visa Inc.',              'Financial Services',      'Credit Services',                  550000000000),
('PG',   'Procter & Gamble Co.',   'Consumer Defensive',      'Household & Personal Products',    370000000000),
('UNH',  'UnitedHealth Group Inc.','Healthcare',              'Healthcare Plans',                 450000000000),
('HD',   'The Home Depot Inc.',    'Consumer Cyclical',       'Home Improvement Retail',          350000000000),
('MA',   'Mastercard Inc.',        'Financial Services',      'Credit Services',                  420000000000),
('BAC',  'Bank of America Corp.',  'Financial Services',      'Banks—Diversified',                300000000000),
('XOM',  'Exxon Mobil Corp.',      'Energy',                  'Oil & Gas Integrated',             430000000000),
('PFE',  'Pfizer Inc.',            'Healthcare',              'Drug Manufacturers—General',       140000000000),
('ABBV', 'AbbVie Inc.',            'Healthcare',              'Drug Manufacturers—General',       310000000000),
('CVX',  'Chevron Corp.',          'Energy',                  'Oil & Gas Integrated',             280000000000)
ON CONFLICT (ticker) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    sector       = EXCLUDED.sector,
    industry     = EXCLUDED.industry,
    market_cap   = EXCLUDED.market_cap,
    is_active    = true;
SQL

# ============================================================
# Section 2 — ohlcv_daily (90 business days × 20 tickers)
# ============================================================
echo "  → ohlcv_daily …"
$PSQL -q <<'SQL'
DO $$
DECLARE
    tickers     text[]    := ARRAY['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','BRK-B','JPM','JNJ','V','PG','UNH','HD','MA','BAC','XOM','PFE','ABBV','CVX'];
    base_prices numeric[] := ARRAY[178.50, 425.30, 175.20, 185.40, 880.50, 510.20, 245.80, 415.60, 198.70, 155.30, 280.40, 162.50, 530.20, 355.80, 465.30, 38.50, 108.20, 27.80, 175.40, 152.30];
    t         text;
    bp        numeric;
    cur_price numeric;
    day_open  numeric;
    day_high  numeric;
    day_low   numeric;
    day_close numeric;
    day_vol   bigint;
    d         date;
BEGIN
    FOR i IN 1..array_length(tickers, 1) LOOP
        t  := tickers[i];
        bp := base_prices[i];
        cur_price := bp;

        FOR d IN
            SELECT dd::date
            FROM generate_series(
                CURRENT_DATE - INTERVAL '500 days',
                CURRENT_DATE - INTERVAL '1 day',
                '1 day'
            ) AS dd
        LOOP
            -- Skip weekends
            IF EXTRACT(DOW FROM d) IN (0, 6) THEN CONTINUE; END IF;

            day_open  := round(cur_price * (1 + (hashtext(t || d::text) % 200 - 100)::numeric / 10000), 4);
            day_close := round(cur_price * (1 + (hashtext(d::text || t) % 200 - 100)::numeric / 10000), 4);
            day_high  := round(greatest(day_open, day_close) * (1 + abs(hashtext(t || 'h' || d::text) % 50)::numeric / 10000), 4);
            day_low   := round(least(day_open, day_close) * (1 - abs(hashtext(t || 'l' || d::text) % 50)::numeric / 10000), 4);
            day_vol   := 1000000 + abs(hashtext(t || 'v' || d::text) % 50000000);

            INSERT INTO ohlcv_daily (ticker, date, open, high, low, close, adj_close, volume, vwap)
            VALUES (
                t, d, day_open, day_high, day_low, day_close, day_close, day_vol,
                round((day_high + day_low + day_close) / 3, 4)
            )
            ON CONFLICT (ticker, date) DO UPDATE SET
                open      = EXCLUDED.open,
                high      = EXCLUDED.high,
                low       = EXCLUDED.low,
                close     = EXCLUDED.close,
                adj_close = EXCLUDED.adj_close,
                volume    = EXCLUDED.volume,
                vwap      = EXCLUDED.vwap;

            cur_price := day_close;
        END LOOP;
    END LOOP;
END $$;
SQL

# ============================================================
# Section 3 — ohlcv_intraday (5 business days × ~78 bars × 20 tickers)
# ============================================================
echo "  → ohlcv_intraday …"
$PSQL -q <<'SQL'
DO $$
DECLARE
    tickers     text[]    := ARRAY['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','BRK-B','JPM','JNJ','V','PG','UNH','HD','MA','BAC','XOM','PFE','ABBV','CVX'];
    base_prices numeric[] := ARRAY[178.50, 425.30, 175.20, 185.40, 880.50, 510.20, 245.80, 415.60, 198.70, 155.30, 280.40, 162.50, 530.20, 355.80, 465.30, 38.50, 108.20, 27.80, 175.40, 152.30];
    t         text;
    cur_price numeric;
    bar_open  numeric;
    bar_high  numeric;
    bar_low   numeric;
    bar_close numeric;
    bar_vol   bigint;
    d         date;
    ts        timestamptz;
    bar_start time;
BEGIN
    FOR i IN 1..array_length(tickers, 1) LOOP
        t := tickers[i];
        cur_price := base_prices[i];

        FOR d IN
            SELECT dd::date
            FROM generate_series(
                CURRENT_DATE - INTERVAL '7 days',
                CURRENT_DATE - INTERVAL '1 day',
                '1 day'
            ) AS dd
        LOOP
            IF EXTRACT(DOW FROM d) IN (0, 6) THEN CONTINUE; END IF;

            -- 5-min bars from 14:30 UTC (09:30 ET) to 20:55 UTC (15:55 ET) = 78 bars
            FOR bar_start IN
                SELECT (TIME '14:30' + (n * INTERVAL '5 minutes'))
                FROM generate_series(0, 77) AS n
            LOOP
                ts := d + bar_start AT TIME ZONE 'UTC';

                bar_open  := round(cur_price * (1 + (hashtext(t || ts::text) % 100 - 50)::numeric / 100000), 4);
                bar_close := round(cur_price * (1 + (hashtext(ts::text || t) % 100 - 50)::numeric / 100000), 4);
                bar_high  := round(greatest(bar_open, bar_close) * (1 + abs(hashtext(t || 'h' || ts::text) % 20)::numeric / 100000), 4);
                bar_low   := round(least(bar_open, bar_close) * (1 - abs(hashtext(t || 'l' || ts::text) % 20)::numeric / 100000), 4);
                bar_vol   := 5000 + abs(hashtext(t || 'v' || ts::text) % 500000);

                INSERT INTO ohlcv_intraday (ticker, timestamp, open, high, low, close, volume)
                VALUES (t, ts, bar_open, bar_high, bar_low, bar_close, bar_vol)
                ON CONFLICT (ticker, timestamp) DO UPDATE SET
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume;

                cur_price := bar_close;
            END LOOP;
        END LOOP;
    END LOOP;
END $$;
SQL

# ============================================================
# Section 4 — model_registry (3 entries)
# ============================================================
echo "  → model_registry …"
$PSQL -q <<'SQL'
INSERT INTO model_registry (model_name, version, metrics_json, trained_at, is_active) VALUES
(
    'CatBoost_standard', '1',
    '{"oos_rmse": 0.0234, "oos_mae": 0.0187, "oos_r2": 0.847, "oos_mape": 0.0312, "oos_directional_accuracy": 0.62, "fold_stability": 0.0089, "scaler_variant": "standard", "is_winner": true, "best_params": {"depth": 6, "learning_rate": 0.05, "iterations": 500}}'::jsonb,
    NOW() - INTERVAL '2 days', true
),
(
    'Ridge_quantile', '1',
    '{"oos_rmse": 0.0412, "oos_mae": 0.0334, "oos_r2": 0.725, "oos_mape": 0.0521, "oos_directional_accuracy": 0.55, "fold_stability": 0.0124, "scaler_variant": "quantile", "is_winner": false, "best_params": {"alpha": 1.5}}'::jsonb,
    NOW() - INTERVAL '5 days', false
),
(
    'RandomForest_minmax', '1',
    '{"oos_rmse": 0.0356, "oos_mae": 0.0289, "oos_r2": 0.783, "oos_mape": 0.0445, "oos_directional_accuracy": 0.58, "fold_stability": 0.0156, "scaler_variant": "minmax", "is_winner": false, "best_params": {"n_estimators": 200, "max_depth": 12}}'::jsonb,
    NOW() - INTERVAL '5 days', false
)
ON CONFLICT DO NOTHING;
SQL

# ============================================================
# Section 5 — predictions (20 tickers × 7 days = 140 rows)
# ============================================================
echo "  → predictions …"
$PSQL -q <<'SQL'
DO $$
DECLARE
    tickers text[] := ARRAY['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','BRK-B','JPM','JNJ','V','PG','UNH','HD','MA','BAC','XOM','PFE','ABBV','CVX'];
    active_model_id integer;
    t          text;
    last_close numeric;
    pred_price numeric;
    d          integer;
BEGIN
    SELECT model_id INTO active_model_id
    FROM model_registry WHERE is_active = true
    LIMIT 1;

    IF active_model_id IS NULL THEN
        RAISE NOTICE 'No active model found — skipping predictions';
        RETURN;
    END IF;

    FOR i IN 1..array_length(tickers, 1) LOOP
        t := tickers[i];

        SELECT close INTO last_close
        FROM ohlcv_daily
        WHERE ticker = t
        ORDER BY date DESC
        LIMIT 1;

        IF last_close IS NULL THEN CONTINUE; END IF;

        FOR d IN 1..7 LOOP
            pred_price := round(
                last_close * (1 + (hashtext(t || d::text || 'pred') % 100 - 30)::numeric / 10000),
                4
            );

            INSERT INTO predictions (ticker, prediction_date, predicted_date, predicted_price, model_id, confidence)
            VALUES (
                t,
                CURRENT_DATE,
                CURRENT_DATE + d,
                pred_price,
                active_model_id,
                round(0.55 + (abs(hashtext(t || d::text)) % 30)::numeric / 100, 4)
            )
            ON CONFLICT DO NOTHING;
        END LOOP;
    END LOOP;
END $$;
SQL

# ============================================================
# Section 6 — drift_logs (5 entries)
# ============================================================
echo "  → drift_logs …"
$PSQL -q <<'SQL'
INSERT INTO drift_logs (drift_type, severity, details_json, detected_at) VALUES
(
    'data_drift', 'medium',
    '{"n_features_checked": 27, "n_features_drifted": 3, "per_feature": {"rsi_14": {"ks_statistic": 0.15, "ks_pvalue": 0.003, "psi": 0.28, "drifted": true}, "macd_line": {"ks_statistic": 0.12, "ks_pvalue": 0.01, "psi": 0.22, "drifted": true}}}'::jsonb,
    NOW() - INTERVAL '12 hours'
),
(
    'prediction_drift', 'low',
    '{"baseline_rmse": 0.022, "recent_rmse": 0.028, "threshold": 0.033, "error_ratio": 1.27, "previous_model_rmse": 0.022}'::jsonb,
    NOW() - INTERVAL '1 day'
),
(
    'concept_drift', 'high',
    '{"historical_rmse": 0.021, "recent_rmse": 0.038, "degradation_ratio": 1.81, "threshold": 1.3, "previous_model_rmse": 0.021}'::jsonb,
    NOW() - INTERVAL '3 days'
),
(
    'data_drift', 'low',
    '{"n_features_checked": 27, "n_features_drifted": 1, "per_feature": {"bb_upper": {"ks_statistic": 0.09, "ks_pvalue": 0.04, "psi": 0.15, "drifted": true}}}'::jsonb,
    NOW() - INTERVAL '5 days'
),
(
    'prediction_drift', 'medium',
    '{"baseline_rmse": 0.022, "recent_rmse": 0.034, "threshold": 0.033, "error_ratio": 1.55, "previous_model_rmse": 0.022}'::jsonb,
    NOW() - INTERVAL '7 days'
)
ON CONFLICT DO NOTHING;
SQL

# ============================================================
# Summary
# ============================================================
echo ""
echo "=== Seed Data Summary ==="
$PSQL -t -c "SELECT 'stocks:          ' || count(*) FROM stocks;"
$PSQL -t -c "SELECT 'ohlcv_daily:     ' || count(*) FROM ohlcv_daily;"
$PSQL -t -c "SELECT 'ohlcv_intraday:  ' || count(*) FROM ohlcv_intraday;"
$PSQL -t -c "SELECT 'model_registry:  ' || count(*) FROM model_registry;"
$PSQL -t -c "SELECT 'predictions:     ' || count(*) FROM predictions;"
$PSQL -t -c "SELECT 'drift_logs:      ' || count(*) FROM drift_logs;"
echo "=== Seed complete ==="
