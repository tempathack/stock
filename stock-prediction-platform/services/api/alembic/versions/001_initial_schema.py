"""Initial schema matching db/init.sql

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    # 1. stocks — reference table (no FK deps)
    op.create_table(
        "stocks",
        sa.Column("ticker", sa.String(10), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("market_cap", sa.BigInteger, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # 2. model_registry — ML model catalog (no FK deps)
    op.create_table(
        "model_registry",
        sa.Column("model_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("metrics_json", JSONB, nullable=False),
        sa.Column("trained_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    # 3. ohlcv_daily — daily OHLCV bars (FK → stocks; becomes hypertable)
    op.create_table(
        "ohlcv_daily",
        sa.Column("ticker", sa.String(10), sa.ForeignKey("stocks.ticker"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("open", sa.Numeric(12, 4), nullable=True),
        sa.Column("high", sa.Numeric(12, 4), nullable=True),
        sa.Column("low", sa.Numeric(12, 4), nullable=True),
        sa.Column("close", sa.Numeric(12, 4), nullable=True),
        sa.Column("adj_close", sa.Numeric(12, 4), nullable=True),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column("vwap", sa.Numeric(12, 4), nullable=True),
        sa.PrimaryKeyConstraint("ticker", "date"),
    )

    # 4. ohlcv_intraday — intraday OHLCV bars (FK → stocks; becomes hypertable)
    op.create_table(
        "ohlcv_intraday",
        sa.Column("ticker", sa.String(10), sa.ForeignKey("stocks.ticker"), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(12, 4), nullable=True),
        sa.Column("high", sa.Numeric(12, 4), nullable=True),
        sa.Column("low", sa.Numeric(12, 4), nullable=True),
        sa.Column("close", sa.Numeric(12, 4), nullable=True),
        sa.Column("adj_close", sa.Numeric(12, 4), nullable=True),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column("vwap", sa.Numeric(12, 4), nullable=True),
        sa.PrimaryKeyConstraint("ticker", "timestamp"),
    )

    # 5. predictions — model predictions (FK → stocks, model_registry)
    op.create_table(
        "predictions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(10), sa.ForeignKey("stocks.ticker"), nullable=False),
        sa.Column("prediction_date", sa.Date, nullable=False),
        sa.Column("predicted_date", sa.Date, nullable=False),
        sa.Column("predicted_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("model_id", sa.Integer, sa.ForeignKey("model_registry.model_id"), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # 6. drift_logs — drift events (no FK deps)
    op.create_table(
        "drift_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("drift_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("details_json", JSONB, nullable=False),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # Convert OHLCV tables to TimescaleDB hypertables
    op.execute(
        "SELECT create_hypertable('ohlcv_daily', 'date', "
        "chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE)"
    )
    op.execute(
        "SELECT create_hypertable('ohlcv_intraday', 'timestamp', "
        "chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE)"
    )

    # Additional indexes matching init.sql
    op.create_index("idx_ohlcv_daily_ticker", "ohlcv_daily", ["ticker"])
    op.create_index("idx_ohlcv_intraday_ticker", "ohlcv_intraday", ["ticker"])
    op.create_index("idx_predictions_ticker", "predictions", ["ticker"])
    op.create_index("idx_predictions_model_id", "predictions", ["model_id"])
    op.create_index("idx_predictions_date", "predictions", ["prediction_date"])
    op.create_index("idx_drift_logs_drift_type", "drift_logs", ["drift_type"])
    op.create_index("idx_drift_logs_detected_at", "drift_logs", ["detected_at"])
    op.create_index("idx_model_registry_is_active", "model_registry", ["is_active"])

    # Trigger function for auto-updating updated_at on stocks
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trigger_stocks_updated_at
            BEFORE UPDATE ON stocks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trigger_stocks_updated_at ON stocks")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")

    # Drop indexes
    op.drop_index("idx_model_registry_is_active", table_name="model_registry")
    op.drop_index("idx_drift_logs_detected_at", table_name="drift_logs")
    op.drop_index("idx_drift_logs_drift_type", table_name="drift_logs")
    op.drop_index("idx_predictions_date", table_name="predictions")
    op.drop_index("idx_predictions_model_id", table_name="predictions")
    op.drop_index("idx_predictions_ticker", table_name="predictions")
    op.drop_index("idx_ohlcv_intraday_ticker", table_name="ohlcv_intraday")
    op.drop_index("idx_ohlcv_daily_ticker", table_name="ohlcv_daily")

    # Drop tables in reverse dependency order
    op.drop_table("drift_logs")
    op.drop_table("predictions")
    op.drop_table("ohlcv_intraday")
    op.drop_table("ohlcv_daily")
    op.drop_table("model_registry")
    op.drop_table("stocks")

    # Do NOT drop TimescaleDB extension (shared, may be used by other schemas)
