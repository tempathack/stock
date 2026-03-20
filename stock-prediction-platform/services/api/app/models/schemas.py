"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    """Optional request body for ingestion endpoints."""

    tickers: list[str] | None = Field(
        default=None,
        description="Ticker symbols to ingest. If omitted, uses the configured default list.",
    )


class IngestResponse(BaseModel):
    """Response model for ingestion endpoints."""

    status: str
    mode: str
    tickers_requested: int
    records_fetched: int
    records_produced: int


class ErrorResponse(BaseModel):
    """Structured error response."""

    status: str = "error"
    detail: str


# ---------------------------------------------------------------------------
# Predictions (Phase 23)
# ---------------------------------------------------------------------------


class PredictionResponse(BaseModel):
    """Single ticker prediction."""

    model_config = ConfigDict(protected_namespaces=())

    ticker: str
    prediction_date: str
    predicted_date: str
    predicted_price: float
    model_name: str
    confidence: float | None = None


class BulkPredictionResponse(BaseModel):
    """Response for /predict/bulk — all ticker forecasts."""

    model_config = ConfigDict(protected_namespaces=())

    predictions: list[PredictionResponse]
    model_name: str | None = None
    generated_at: str | None = None
    count: int


# ---------------------------------------------------------------------------
# Models (Phase 23)
# ---------------------------------------------------------------------------


class ModelComparisonEntry(BaseModel):
    """A single model in the comparison table."""

    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    scaler_variant: str
    version: int | None = None
    is_winner: bool = False
    is_active: bool = False
    oos_metrics: dict = Field(default_factory=dict)
    fold_stability: float | None = None
    best_params: dict = Field(default_factory=dict)
    saved_at: str | None = None


class ModelComparisonResponse(BaseModel):
    """Response for /models/comparison."""

    models: list[ModelComparisonEntry]
    winner: ModelComparisonEntry | None = None
    count: int


# ---------------------------------------------------------------------------
# Drift (Phase 23)
# ---------------------------------------------------------------------------


class DriftEventEntry(BaseModel):
    """A single drift event from the log."""

    drift_type: str
    is_drifted: bool
    severity: str
    details: dict = Field(default_factory=dict)
    timestamp: str | None = None
    features_affected: list[str] = Field(default_factory=list)


class DriftStatusResponse(BaseModel):
    """Response for /models/drift."""

    events: list[DriftEventEntry]
    any_recent_drift: bool = False
    latest_event: DriftEventEntry | None = None
    count: int


# ---------------------------------------------------------------------------
# Market (Phase 24)
# ---------------------------------------------------------------------------


class MarketOverviewEntry(BaseModel):
    """A single stock in the market overview treemap."""

    ticker: str
    company_name: str | None = None
    sector: str | None = None
    market_cap: int | None = None
    last_close: float | None = None
    daily_change_pct: float | None = None


class MarketOverviewResponse(BaseModel):
    """Response for /market/overview."""

    stocks: list[MarketOverviewEntry]
    count: int


class IndicatorValues(BaseModel):
    """Technical indicator values for a single row (latest or time series)."""

    model_config = ConfigDict(protected_namespaces=())

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
    """Response for /market/indicators/{ticker}."""

    ticker: str
    latest: IndicatorValues | None = None
    series: list[IndicatorValues] = Field(default_factory=list)
    count: int
