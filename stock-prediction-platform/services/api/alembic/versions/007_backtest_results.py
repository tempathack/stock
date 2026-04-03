"""Add backtest_results table

Revision ID: 007backtestresults
Revises: 006sentimentts
Create Date: 2026-04-03
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007backtestresults"
down_revision: Union[str, None] = "006sentimentts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
            id                   SERIAL PRIMARY KEY,
            ticker               VARCHAR(10)      NOT NULL,
            start_date           DATE             NOT NULL,
            end_date             DATE             NOT NULL,
            horizon_days         INTEGER          NOT NULL DEFAULT 7,
            total_return_pct     DOUBLE PRECISION,
            benchmark_return_pct DOUBLE PRECISION,
            sharpe_ratio         DOUBLE PRECISION,
            max_drawdown         DOUBLE PRECISION,
            win_rate             DOUBLE PRECISION,
            trade_count          INTEGER,
            created_at           TIMESTAMPTZ      NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_backtest_results_ticker_dates
        ON backtest_results (ticker, start_date, end_date, horizon_days)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS backtest_results")
