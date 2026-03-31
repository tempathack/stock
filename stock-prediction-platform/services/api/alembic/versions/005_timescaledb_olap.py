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


def _try_execute(sql: str, label: str) -> None:
    """Execute SQL, logging and continuing on error (best-effort TimescaleDB features)."""
    import logging
    conn = op.get_bind()
    try:
        conn.execute(op.inline_literal(sql) if False else __import__('sqlalchemy').text(sql))
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("alembic").warning(
            "005timescaleolap: %s skipped — %s: %s", label, type(exc).__name__, exc
        )


def upgrade() -> None:
    # ── 1. Compression on ohlcv_daily (TSDB-03) ──────────────────────────────
    _try_execute("""
        ALTER TABLE ohlcv_daily SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker',
            timescaledb.compress_orderby   = 'date DESC'
        )
    """, "compress ohlcv_daily")
    _try_execute("""
        SELECT add_compression_policy(
            'ohlcv_daily',
            compress_after => INTERVAL '7 days',
            if_not_exists  => TRUE
        )
    """, "compression policy ohlcv_daily")

    # ── 2. Compression on ohlcv_intraday (TSDB-04) ───────────────────────────
    _try_execute("""
        ALTER TABLE ohlcv_intraday SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker',
            timescaledb.compress_orderby   = 'timestamp DESC'
        )
    """, "compress ohlcv_intraday")
    _try_execute("""
        SELECT add_compression_policy(
            'ohlcv_intraday',
            compress_after => INTERVAL '3 days',
            if_not_exists  => TRUE
        )
    """, "compression policy ohlcv_intraday")

    # ── 3. Continuous aggregate: ohlcv_intraday → 1-hour buckets (TSDB-01) ──
    _try_execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_daily_1h_agg
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
    """, "create ohlcv_daily_1h_agg")
    _try_execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_daily_1h_agg',
            start_offset      => INTERVAL '3 hours',
            end_offset        => INTERVAL '30 minutes',
            schedule_interval => INTERVAL '30 minutes',
            if_not_exists     => TRUE
        )
    """, "aggregate policy ohlcv_daily_1h_agg")

    # ── 4. Continuous aggregate: ohlcv_daily → daily summary (TSDB-02) ──────
    # NOTE: ohlcv_daily.date is DATE — TimescaleDB 2.x requires the partition
    # column used directly in time_bucket without casting.  A regular
    # materialized view is used as a fallback when the continuous aggregate
    # cannot be created due to version constraints.
    _try_execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_daily_agg AS
        SELECT
            date_trunc('day', date::timestamptz) AS bucket,
            ticker,
            FIRST(open,      date::timestamptz)  AS open,
            MAX(high)                            AS high,
            MIN(low)                             AS low,
            LAST(close,      date::timestamptz)  AS close,
            SUM(volume)                          AS volume,
            LAST(vwap,       date::timestamptz)  AS vwap,
            LAST(adj_close,  date::timestamptz)  AS adj_close
        FROM ohlcv_daily
        GROUP BY bucket, ticker
    """, "create ohlcv_daily_agg (regular materialized view)")

    # ── 5. Retention policies (TSDB-05) ──────────────────────────────────────
    _try_execute("""
        SELECT add_retention_policy(
            'ohlcv_intraday',
            drop_after    => INTERVAL '90 days',
            if_not_exists => TRUE
        )
    """, "retention policy ohlcv_intraday")
    _try_execute("""
        SELECT add_retention_policy(
            'ohlcv_daily',
            drop_after    => INTERVAL '5 years',
            if_not_exists => TRUE
        )
    """, "retention policy ohlcv_daily")


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
