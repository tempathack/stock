"""Create Feast wide-format source tables.

Revision ID: 0001_feast_wide_format
Revises:
Create Date: 2026-03-30

These tables are the offline store data sources for Feast FeatureViews.
feast apply registers the DataSource metadata but does NOT create these tables —
they must exist before feast materialize-incremental is called.

Run via:
    alembic -c ml/alembic/alembic.ini upgrade head
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_feast_wide_format"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # feast_ohlcv_stats — OHLCV data + basic stats
    op.create_table(
        "feast_ohlcv_stats",
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float, nullable=True),
        sa.Column("high", sa.Float, nullable=True),
        sa.Column("low", sa.Float, nullable=True),
        sa.Column("close", sa.Float, nullable=True),
        sa.Column("volume", sa.Float, nullable=True),
        sa.Column("daily_return", sa.Float, nullable=True),
        sa.Column("vwap", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ticker", "timestamp"),
    )
    op.create_index("ix_feast_ohlcv_stats_ticker", "feast_ohlcv_stats", ["ticker"])
    op.create_index("ix_feast_ohlcv_stats_timestamp", "feast_ohlcv_stats", ["timestamp"])

    # feast_technical_indicators — computed indicator values
    op.create_table(
        "feast_technical_indicators",
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rsi_14", sa.Float, nullable=True),
        sa.Column("macd_line", sa.Float, nullable=True),
        sa.Column("macd_signal", sa.Float, nullable=True),
        sa.Column("bb_upper", sa.Float, nullable=True),
        sa.Column("bb_lower", sa.Float, nullable=True),
        sa.Column("atr_14", sa.Float, nullable=True),
        sa.Column("adx_14", sa.Float, nullable=True),
        sa.Column("ema_20", sa.Float, nullable=True),
        sa.Column("obv", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ticker", "timestamp"),
    )
    op.create_index(
        "ix_feast_technical_indicators_ticker", "feast_technical_indicators", ["ticker"]
    )
    op.create_index(
        "ix_feast_technical_indicators_timestamp",
        "feast_technical_indicators",
        ["timestamp"],
    )

    # feast_lag_features — lag and rolling window features
    op.create_table(
        "feast_lag_features",
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lag_1", sa.Float, nullable=True),
        sa.Column("lag_2", sa.Float, nullable=True),
        sa.Column("lag_3", sa.Float, nullable=True),
        sa.Column("lag_5", sa.Float, nullable=True),
        sa.Column("lag_7", sa.Float, nullable=True),
        sa.Column("lag_10", sa.Float, nullable=True),
        sa.Column("lag_14", sa.Float, nullable=True),
        sa.Column("lag_21", sa.Float, nullable=True),
        sa.Column("rolling_mean_5", sa.Float, nullable=True),
        sa.Column("rolling_mean_10", sa.Float, nullable=True),
        sa.Column("rolling_mean_21", sa.Float, nullable=True),
        sa.Column("rolling_std_5", sa.Float, nullable=True),
        sa.Column("rolling_std_10", sa.Float, nullable=True),
        sa.Column("rolling_std_21", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ticker", "timestamp"),
    )
    op.create_index("ix_feast_lag_features_ticker", "feast_lag_features", ["ticker"])
    op.create_index("ix_feast_lag_features_timestamp", "feast_lag_features", ["timestamp"])


def downgrade() -> None:
    op.drop_table("feast_lag_features")
    op.drop_table("feast_technical_indicators")
    op.drop_table("feast_ohlcv_stats")
