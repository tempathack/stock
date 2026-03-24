"""SQLAlchemy ORM models matching db/init.sql schema."""

from sqlalchemy import (
    BigInteger, Boolean, Date, Integer, Numeric, String, func, text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    market_cap: Mapped[int | None] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    metrics_json = mapped_column(JSONB, nullable=False)
    trained_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    traffic_weight = mapped_column(Numeric(5, 4), nullable=False, server_default=text("0.0"))


class OHLCVDaily(Base):
    __tablename__ = "ohlcv_daily"

    ticker: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.ticker"), primary_key=True)
    date = mapped_column(Date, primary_key=True)
    open = mapped_column(Numeric(12, 4))
    high = mapped_column(Numeric(12, 4))
    low = mapped_column(Numeric(12, 4))
    close = mapped_column(Numeric(12, 4))
    adj_close = mapped_column(Numeric(12, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    vwap = mapped_column(Numeric(12, 4))


class OHLCVIntraday(Base):
    __tablename__ = "ohlcv_intraday"

    ticker: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.ticker"), primary_key=True)
    timestamp = mapped_column(TIMESTAMP(timezone=True), primary_key=True)
    open = mapped_column(Numeric(12, 4))
    high = mapped_column(Numeric(12, 4))
    low = mapped_column(Numeric(12, 4))
    close = mapped_column(Numeric(12, 4))
    adj_close = mapped_column(Numeric(12, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    vwap = mapped_column(Numeric(12, 4))


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    prediction_date = mapped_column(Date, nullable=False)
    predicted_date = mapped_column(Date, nullable=False)
    predicted_price = mapped_column(Numeric(12, 4), nullable=False)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_registry.model_id"), nullable=False)
    confidence = mapped_column(Numeric(5, 4))
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class DriftLog(Base):
    __tablename__ = "drift_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drift_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    details_json = mapped_column(JSONB, nullable=False)
    detected_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class FeatureStore(Base):
    __tablename__ = "feature_store"

    ticker: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.ticker"), primary_key=True)
    date = mapped_column(Date, primary_key=True)
    feature_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    feature_value = mapped_column(Numeric(18, 8))
    computed_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class ABTestAssignment(Base):
    __tablename__ = "ab_test_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_registry.model_id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    predicted_price = mapped_column(Numeric(12, 4), nullable=False)
    actual_price = mapped_column(Numeric(12, 4), nullable=True)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("7"))
    assigned_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    evaluated_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
