"""Pydantic response/request schemas for the stock prediction API."""

from __future__ import annotations

from pydantic import BaseModel


# ── Predictions ───────────────────────────────────────────────────────────


class PredictionResponse(BaseModel):
    ticker: str
    prediction_date: str
    predicted_date: str
    predicted_price: float
    model_name: str
    confidence: float | None = None


class BulkPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    model_name: str | None = None
    generated_at: str | None = None
    count: int


# ── Ingestion ─────────────────────────────────────────────────────────────


class IngestRequest(BaseModel):
    tickers: list[str] | None = None


class IngestResponse(BaseModel):
    status: str
    mode: str
    tickers_requested: int
    records_fetched: int
    records_produced: int


# ── Models ────────────────────────────────────────────────────────────────


class ModelComparisonEntry(BaseModel):
    model_name: str
    scaler_variant: str
    version: int | None = None
    is_winner: bool
    is_active: bool
    oos_metrics: dict = {}
    fold_stability: float | None = None
    best_params: dict = {}
    saved_at: str | None = None


class ModelComparisonResponse(BaseModel):
    models: list[ModelComparisonEntry]
    winner: ModelComparisonEntry | None = None
    count: int


class DriftEventEntry(BaseModel):
    drift_type: str
    is_drifted: bool
    severity: str
    details: dict = {}
    timestamp: str | None = None
    features_affected: list[str] = []


class DriftStatusResponse(BaseModel):
    events: list[DriftEventEntry]
    any_recent_drift: bool
    latest_event: DriftEventEntry | None = None
    count: int


# ── Market ────────────────────────────────────────────────────────────────


class MarketOverviewEntry(BaseModel):
    ticker: str
    company_name: str | None = None
    sector: str | None = None
    market_cap: int | None = None
    last_close: float | None = None
    daily_change_pct: float | None = None


class MarketOverviewResponse(BaseModel):
    stocks: list[MarketOverviewEntry]
    count: int


class IndicatorValues(BaseModel):
    date: str | None = None
    close: float | None = None
    rsi_14: float | None = None
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_12: float | None = None
    ema_26: float | None = None
    adx: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    atr: float | None = None
    rolling_volatility_21: float | None = None
    obv: float | None = None
    vwap: float | None = None
    volume_sma_20: float | None = None
    ad_line: float | None = None
    return_1d: float | None = None
    return_5d: float | None = None
    return_21d: float | None = None
    log_return: float | None = None


class TickerIndicatorsResponse(BaseModel):
    ticker: str
    latest: IndicatorValues | None = None
    series: list[IndicatorValues] = []
    count: int