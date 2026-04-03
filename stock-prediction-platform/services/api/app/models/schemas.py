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
    horizon_days: int | None = None
    assigned_model_id: int | None = None


class BulkPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    model_name: str | None = None
    generated_at: str | None = None
    count: int
    horizon_days: int | None = None


class AvailableHorizonsResponse(BaseModel):
    horizons: list[int]
    default: int


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
    traffic_weight: float = 0.0
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


# ── Rolling Performance & Retrain Status ─────────────────────────────────


class RollingPerfEntry(BaseModel):
    date: str
    rmse: float | None = None
    mae: float | None = None
    directional_accuracy: float | None = None
    n_predictions: int = 0


class RollingPerformanceResponse(BaseModel):
    entries: list[RollingPerfEntry] = []
    model_name: str | None = None
    period_days: int = 30
    count: int = 0


class RetrainStatusResponse(BaseModel):
    model_name: str | None = None
    version: str | None = None
    trained_at: str | None = None
    is_active: bool = False
    oos_metrics: dict = {}
    previous_model: str | None = None
    previous_trained_at: str | None = None
    previous_oos_metrics: dict = {}   # OOS metrics for the row before current


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


class CandleBar(BaseModel):
    ts: str                   # ISO-8601 UTC timestamp of the time_bucket
    ticker: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    vwap: float | None = None


class CandlesResponse(BaseModel):
    ticker: str
    interval: str
    candles: list[CandleBar]
    count: int


# ── Backtest ──────────────────────────────────────────────────────────────


class BacktestDataPoint(BaseModel):
    date: str
    actual_price: float
    predicted_price: float
    error: float
    error_pct: float


class BacktestMetrics(BaseModel):
    rmse: float
    mae: float
    mape: float
    directional_accuracy: float
    r2: float
    total_points: int


class BacktestResponse(BaseModel):
    ticker: str
    model_name: str
    horizon: int
    start_date: str
    end_date: str
    metrics: BacktestMetrics
    series: list[BacktestDataPoint]
    features_pit_correct: bool = False
    """True when predictions were generated via KServe Transformer + Feast (PIT-correct path)."""


# ── A/B Testing ───────────────────────────────────────────────────────────


class ABTestAssignmentEntry(BaseModel):
    id: int
    ticker: str
    model_id: int
    model_name: str
    predicted_price: float
    actual_price: float | None = None
    horizon_days: int = 7
    assigned_at: str
    evaluated_at: str | None = None


class ABResultsModelEntry(BaseModel):
    model_id: int
    model_name: str
    version: str | None = None
    traffic_weight: float = 0.0
    n_assignments: int = 0
    n_evaluated: int = 0
    mae: float | None = None
    rmse: float | None = None
    directional_accuracy: float | None = None


class ABResultsResponse(BaseModel):
    models: list[ABResultsModelEntry]
    total_assignments: int = 0
    total_evaluated: int = 0
    period_start: str | None = None
    period_end: str | None = None


# --- Analytics schemas (Phase 69) ---


class FlinkJobEntry(BaseModel):
    job_id: str
    name: str
    state: str
    start_time: int
    duration_ms: int
    tasks_running: int


class FlinkJobsResponse(BaseModel):
    jobs: list[FlinkJobEntry]
    total_running: int
    total_failed: int


class FeastViewFreshness(BaseModel):
    view_name: str
    last_updated: str | None = None
    staleness_seconds: int | None = None
    status: str


class FeastFreshnessResponse(BaseModel):
    views: list[FeastViewFreshness]
    registry_available: bool


class KafkaPartitionLag(BaseModel):
    partition: int
    current_offset: int
    end_offset: int
    lag: int


class KafkaLagResponse(BaseModel):
    topic: str
    consumer_group: str
    partitions: list[KafkaPartitionLag]
    total_lag: int
    sampled_at: str


class AnalyticsSummaryResponse(BaseModel):
    argocd_sync_status: str | None = None
    flink_running_jobs: int
    flink_failed_jobs: int
    feast_online_latency_ms: float | None = None
    ca_last_refresh: str | None = None


# ── Sentiment (Phase 71) ───────────────────────────────────────────────────


class SentimentFeaturesResponse(BaseModel):
    """Response schema for /ws/sentiment/{ticker} WebSocket messages."""
    ticker: str
    avg_sentiment: float | None = None
    mention_count: int | None = None
    positive_ratio: float | None = None
    negative_ratio: float | None = None
    top_subreddit: str | None = None
    available: bool
    sampled_at: str | None = None


# ── Streaming Features (Phase 70) ─────────────────────────────────────────

class StreamingFeaturesResponse(BaseModel):
    ticker: str
    ema_20: float | None = None
    rsi_14: float | None = None
    macd_signal: float | None = None
    available: bool = False
    source: str = "flink-indicator-stream"
    sampled_at: str | None = None  # ISO8601 UTC timestamp of the Redis query