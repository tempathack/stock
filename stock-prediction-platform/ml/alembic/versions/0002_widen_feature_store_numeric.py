"""Widen feature_store.feature_value from numeric(18,8) to numeric(24,8).

Revision ID: 0002_widen_feature_store_numeric
Revises: 0001_feast_wide_format
Create Date: 2026-04-08

Rationale:
    Cumulative volume indicators (OBV, Accumulation/Distribution Line) can
    accumulate to hundreds of billions for high-volume tickers (e.g. NVDA).
    The original numeric(18,8) column overflows at ~9.99e9 absolute value.
    numeric(24,8) raises the ceiling to ~9.99e15, accommodating all realistic
    cumulative volume values over a 5-year window.

Applied directly to the cluster on 2026-04-08 via:
    kubectl exec -n storage deployment/postgresql -- psql -U stockuser -d stockdb \\
        -c "ALTER TABLE feature_store ALTER COLUMN feature_value TYPE numeric(24,8);"
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_widen_feature_store_numeric"
down_revision = "0001_feast_wide_format"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "feature_store",
        "feature_value",
        type_=sa.Numeric(24, 8),
        existing_type=sa.Numeric(18, 8),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "feature_store",
        "feature_value",
        type_=sa.Numeric(18, 8),
        existing_type=sa.Numeric(24, 8),
        existing_nullable=True,
    )
