import type {
  HealthResponse,
  BulkPredictionResponse,
  AvailableHorizonsResponse,
  ModelComparisonResponse,
  DriftStatusResponse,
  RollingPerformanceResponse,
  RetrainStatusResponse,
  MarketOverviewResponse,
  TickerIndicatorsResponse,
  BacktestResponse,
} from "../src/api/types";

// ── Sentinel values deliberately distinct from mock data defaults ──
// Mock data uses tickers like AAPL, MSFT, GOOGL, AMZN, NVDA.
// Fixtures use the same tickers but model names use "fixture_" prefix to
// detect false positives from mock fallback paths.

export const healthFixture = (): HealthResponse => ({
  service: "stock-api",
  version: "1.0.0",
  status: "healthy",
});

export const marketOverviewFixture = (): MarketOverviewResponse => ({
  stocks: [
    {
      ticker: "AAPL",
      company_name: "Apple Inc.",
      sector: "Technology",
      market_cap: 2_800_000_000_000,
      last_close: 178.50,
      daily_change_pct: 1.23,
    },
    {
      ticker: "MSFT",
      company_name: "Microsoft Corporation",
      sector: "Technology",
      market_cap: 3_100_000_000_000,
      last_close: 415.20,
      daily_change_pct: -0.54,
    },
  ],
  count: 2,
});

export const bulkPredictionsFixture = (horizon = 7): BulkPredictionResponse => ({
  predictions: [
    {
      ticker: "AAPL",
      prediction_date: "2026-03-25",
      predicted_date: "2026-04-01",
      predicted_price: 182.30,
      model_name: "fixture_stacking_ensemble_meta_ridge",
      confidence: 0.87,
      horizon_days: horizon,
    },
    {
      ticker: "MSFT",
      prediction_date: "2026-03-25",
      predicted_date: "2026-04-01",
      predicted_price: 420.10,
      model_name: "fixture_stacking_ensemble_meta_ridge",
      confidence: 0.91,
      horizon_days: horizon,
    },
  ],
  model_name: "fixture_stacking_ensemble_meta_ridge",
  generated_at: "2026-03-25T09:00:00Z",
  count: 2,
  horizon_days: horizon,
});

export const availableHorizonsFixture = (): AvailableHorizonsResponse => ({
  horizons: [1, 7, 30],
  default: 7,
});

export const modelComparisonFixture = (): ModelComparisonResponse => ({
  models: [
    {
      model_name: "fixture_stacking_ensemble_meta_ridge",
      scaler_variant: "standard",
      version: 3,
      is_winner: true,
      is_active: true,
      oos_metrics: { rmse: 0.012345, mae: 0.009876, r2: 0.8765, mape: 0.0234, directional_accuracy: 0.72 },
      fold_stability: 0.9123,
      best_params: {},
      saved_at: "2026-03-20T10:00:00Z",
    },
    {
      model_name: "fixture_ridge_quantile",
      scaler_variant: "quantile",
      version: 2,
      is_winner: false,
      is_active: false,
      oos_metrics: { rmse: 0.019876, mae: 0.015432, r2: 0.7654, mape: 0.0345, directional_accuracy: 0.65 },
      fold_stability: 0.8234,
      best_params: {},
      saved_at: "2026-03-18T08:00:00Z",
    },
  ],
  winner: {
    model_name: "fixture_stacking_ensemble_meta_ridge",
    scaler_variant: "standard",
    version: 3,
    is_winner: true,
    is_active: true,
    oos_metrics: { rmse: 0.012345, mae: 0.009876, r2: 0.8765, mape: 0.0234, directional_accuracy: 0.72 },
    fold_stability: 0.9123,
    best_params: {},
    saved_at: "2026-03-20T10:00:00Z",
  },
  count: 2,
});

export const driftStatusFixture = (): DriftStatusResponse => ({
  events: [
    {
      drift_type: "data_drift",
      is_drifted: true,
      severity: "medium",
      details: { ks_stat: 0.12, psi: 0.09 },
      timestamp: "2026-03-24T14:00:00Z",
      features_affected: ["rsi_14", "macd_line"],
    },
  ],
  any_recent_drift: true,
  latest_event: {
    drift_type: "data_drift",
    is_drifted: true,
    severity: "medium",
    details: {},
    timestamp: "2026-03-24T14:00:00Z",
    features_affected: ["rsi_14"],
  },
  count: 1,
});

export const rollingPerformanceFixture = (): RollingPerformanceResponse => ({
  entries: [
    { date: "2026-03-01", rmse: 0.011, mae: 0.009, directional_accuracy: 0.71, n_predictions: 5 },
    { date: "2026-03-15", rmse: 0.013, mae: 0.010, directional_accuracy: 0.69, n_predictions: 5 },
  ],
  model_name: "fixture_stacking_ensemble_meta_ridge",
  period_days: 30,
  count: 2,
});

export const retrainStatusFixture = (): RetrainStatusResponse => ({
  model_name: "fixture_stacking_ensemble_meta_ridge",
  version: "3",
  trained_at: "2026-03-20T10:00:00Z",
  is_active: true,
  oos_metrics: { oos_rmse: 0.012345, oos_mae: 0.009876 },
  previous_model: "fixture_ridge_quantile",
  previous_trained_at: "2026-03-18T08:00:00Z",
});

export const backtestFixture = (ticker = "AAPL"): BacktestResponse => ({
  ticker,
  model_name: "fixture_stacking_ensemble_meta_ridge",
  horizon: 7,
  start_date: "2025-03-25",
  end_date: "2026-03-25",
  metrics: {
    rmse: 3.45,
    mae: 2.87,
    mape: 1.92,
    directional_accuracy: 68.5,
    r2: 0.82,
    total_points: 252,
  },
  series: [
    { date: "2025-04-01", actual_price: 180.0, predicted_price: 182.3, error: -2.3, error_pct: -1.28 },
    { date: "2025-04-08", actual_price: 183.5, predicted_price: 181.0, error: 2.5, error_pct: 1.36 },
  ],
});

export const tickerIndicatorsFixture = (ticker = "AAPL"): TickerIndicatorsResponse => ({
  ticker,
  latest: {
    date: "2026-03-25",
    close: 178.50,
    rsi_14: 58.3,
    macd_line: 1.23,
    macd_signal: 0.98,
    macd_histogram: 0.25,
    stoch_k: 72.1,
    stoch_d: 68.4,
    sma_20: 176.2,
    sma_50: 171.8,
    sma_200: 165.4,
    ema_12: 177.1,
    ema_26: 174.5,
    adx: 28.7,
    bb_upper: 182.3,
    bb_middle: 176.2,
    bb_lower: 170.1,
    atr: 2.45,
    rolling_volatility_21: 0.018,
    obv: 123456789,
    vwap: 177.8,
    volume_sma_20: 87654321,
    ad_line: 987654,
    return_1d: 0.0123,
    return_5d: 0.0234,
    return_21d: 0.0456,
    log_return: 0.0122,
  },
  series: [],
  count: 0,
});
