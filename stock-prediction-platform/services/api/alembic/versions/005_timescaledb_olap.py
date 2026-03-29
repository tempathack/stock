"""TimescaleDB OLAP — continuous aggregates, compression & retention policies

Revision ID: 005timescaleolap
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005timescaleolap"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Compression on ohlcv_daily (TSDB-03) ──────────────────────────────
    # compress_after=7d > start_offset=3d for ohlcv_daily_agg — no overlap
    op.execute("""
        ALTER TABLE ohlcv_daily SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker',
            timescaledb.compress_orderby   = 'date DESC'
        )
    """)
    op.execute("""
        SELECT add_compression_policy(
            'ohlcv_daily',
            after         => INTERVAL '7 days',
            if_not_exists => TRUE
        )
    """)

    # ── 2. Compression on ohlcv_intraday (TSDB-04) ───────────────────────────
    # compress_after=3d > start_offset=2h for ohlcv_daily_1h_agg — no overlap
    op.execute("""
        ALTER TABLE ohlcv_intraday SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker',
            timescaledb.compress_orderby   = 'timestamp DESC'
        )
    """)
    op.execute("""
        SELECT add_compression_policy(
            'ohlcv_intraday',
            after         => INTERVAL '3 days',
            if_not_exists => TRUE
        )
    """)

    # ── 3. Continuous aggregate: ohlcv_intraday → 1-hour buckets (TSDB-01) ──
    # timescaledb.materialized_only=false ensures real-time tail is included
    # regardless of TimescaleDB version default (changed in 2.13)
    op.execute("""
        CREATE MATERIALIZED VIEW ohlcv_daily_1h_agg
        WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
        SELECT
            time_bucket('1 hour', timestamp) AS bucket,
            ticker,
            FIRST(open,  timestamp)          AS open,
            MAX(high)                        AS high,
            MIN(low)                         AS low,
            LAST(close,  timestamp)          AS close,
            SUM(volume)                      AS volume,
            LAST(vwap,   timestamp)          AS vwap
        FROM ohlcv_intraday
        GROUP BY bucket, ticker
        WITH NO DATA
    """)
    # Refresh every 30 minutes; start_offset=2h < compress_after=3d — safe
    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_daily_1h_agg',
            start_offset      => INTERVAL '2 hours',
            end_offset        => INTERVAL '30 minutes',
            schedule_interval => INTERVAL '30 minutes',
            if_not_exists     => TRUE
        )
    """)

    # ── 4. Continuous aggregate: ohlcv_daily → daily summary (TSDB-02) ──────
    # CRITICAL: ohlcv_daily.date is DATE not TIMESTAMPTZ — cast required
    # Workaround for TimescaleDB GitHub issue #6042 (open as of 2026-03)
    # timescaledb.materialized_only=false ensures real-time tail included
    op.execute("""
        CREATE MATERIALIZED VIEW ohlcv_daily_agg
        WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
        SELECT
            time_bucket('1 day', date::timestamptz) AS bucket,
            ticker,
            FIRST(open,      date::timestamptz)     AS open,
            MAX(high)                               AS high,
            MIN(low)                                AS low,
            LAST(close,      date::timestamptz)     AS close,
            SUM(volume)                             AS volume,
            LAST(vwap,       date::timestamptz)     AS vwap,
            LAST(adj_close,  date::timestamptz)     AS adj_close
        FROM ohlcv_daily
        GROUP BY bucket, ticker
        WITH NO DATA
    """)
    # Refresh every hour; start_offset=3d < compress_after=7d — safe
    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_daily_agg',
            start_offset      => INTERVAL '3 days',
            end_offset        => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists     => TRUE
        )
    """)

    # ── 5. Retention policies (TSDB-05) ──────────────────────────────────────
    # intraday: 90 days >> start_offset=2h — aggregate data safe at boundary
    op.execute("""
        SELECT add_retention_policy(
            'ohlcv_intraday',
            drop_after    => INTERVAL '90 days',
            if_not_exists => TRUE
        )
    """)
    # daily: 5 years >> start_offset=3 days — no risk
    op.execute("""
        SELECT add_retention_policy(
            'ohlcv_daily',
            drop_after    => INTERVAL '5 years',
            if_not_exists => TRUE
        )
    """)


def downgrade() -> None:
    # Remove in reverse order: retention → aggregates → compression
    op.execute("SELECT remove_retention_policy('ohlcv_daily',    if_not_exists => TRUE)")
    op.execute("SELECT remove_retention_policy('ohlcv_intraday', if_not_exists => TRUE)")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_daily_agg")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_daily_1h_agg")
    op.execute("SELECT remove_compression_policy('ohlcv_intraday', if_not_exists => TRUE)")
    op.execute("SELECT remove_compression_policy('ohlcv_daily',    if_not_exists => TRUE)")
    op.execute("ALTER TABLE ohlcv_intraday RESET (timescaledb.compress)")
    op.execute("ALTER TABLE ohlcv_daily    RESET (timescaledb.compress)")
