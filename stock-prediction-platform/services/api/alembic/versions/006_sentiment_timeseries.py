"""Add sentiment_timeseries hypertable

Revision ID: 006sentimentts
Revises: 005timescaleolap
Create Date: 2026-04-03
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006sentimentts"
down_revision: Union[str, None] = "005timescaleolap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_timeseries (
            ticker         VARCHAR(10)      NOT NULL,
            window_start   TIMESTAMPTZ      NOT NULL,
            avg_sentiment  DOUBLE PRECISION,
            mention_count  INTEGER,
            positive_ratio DOUBLE PRECISION,
            negative_ratio DOUBLE PRECISION,
            PRIMARY KEY (ticker, window_start)
        )
    """)

    # Convert to TimescaleDB hypertable — best-effort (no-op if TimescaleDB unavailable)
    try:
        op.execute("""
            SELECT create_hypertable(
                'sentiment_timeseries', 'window_start',
                if_not_exists => TRUE
            )
        """)
    except Exception:
        pass

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sentiment_ts_ticker_time
        ON sentiment_timeseries (ticker, window_start DESC)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sentiment_timeseries")
