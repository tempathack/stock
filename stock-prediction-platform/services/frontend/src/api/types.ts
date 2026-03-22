/* TypeScript interfaces mirroring FastAPI Pydantic schemas */

export interface HealthResponse {
  service: string;
  version: string;
  status: string;
}

export interface PredictionResponse {
  ticker: string;
  prediction_date: string;
  predicted_date: string;
  predicted_price: number;
  model_name: string;
  confidence: number | null;
}

export interface BulkPredictionResponse {
  predictions: PredictionResponse[];
  model_name: string | null;
  generated_at: string | null;
  count: number;
}

export interface ModelComparisonEntry {
  model_name: string;
  scaler_variant: string;
  version: number | null;
  is_winner: boolean;
  is_active: boolean;
  oos_metrics: Record<string, unknown>;
  fold_stability: number | null;
  best_params: Record<string, unknown>;
  saved_at: string | null;
}

export interface ModelComparisonResponse {
  models: ModelComparisonEntry[];
  winner: ModelComparisonEntry | null;
  count: number;
}

export interface DriftEventEntry {
  drift_type: string;
  is_drifted: boolean;
  severity: string;
  details: Record<string, unknown>;
  timestamp: string | null;
  features_affected: string[];
}

export interface DriftStatusResponse {
  events: DriftEventEntry[];
  any_recent_drift: boolean;
  latest_event: DriftEventEntry | null;
  count: number;
}

export interface MarketOverviewEntry {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  market_cap: number | null;
  last_close: number | null;
  daily_change_pct: number | null;
}

export interface MarketOverviewResponse {
  stocks: MarketOverviewEntry[];
  count: number;
}

export interface IndicatorValues {
  date: string | null;
  close: number | null;
  rsi_14: number | null;
  macd_line: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  stoch_k: number | null;
  stoch_d: number | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  ema_12: number | null;
  ema_26: number | null;
  adx: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
  atr: number | null;
  rolling_volatility_21: number | null;
  obv: number | null;
  vwap: number | null;
  volume_sma_20: number | null;
  ad_line: number | null;
  return_1d: number | null;
  return_5d: number | null;
  return_21d: number | null;
  log_return: number | null;
}

export interface TickerIndicatorsResponse {
  ticker: string;
  latest: IndicatorValues | null;
  series: IndicatorValues[];
  count: number;
}

/* ── SHAP & fold data (Phase 26) ──────────────────── */

export interface ShapFeatureImportance {
  feature: string;
  importance: number;
}

export interface ShapBeeswarmPoint {
  feature: string;
  feature_value: number;
  shap_value: number;
}

export interface FoldMetric {
  fold: number;
  rmse: number;
  mae: number;
  r2: number;
}

export interface ModelDetailData {
  model_name: string;
  shap_importance: ShapFeatureImportance[];
  shap_beeswarm: ShapBeeswarmPoint[];
  fold_metrics: FoldMetric[];
}

/* ── Forecast page types (Phase 27) ──────────────── */

export type TrendDirection = "bullish" | "bearish" | "neutral";

export interface ForecastRow {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  current_price: number | null;
  predicted_price: number;
  expected_return_pct: number;
  confidence: number | null;
  daily_change_pct: number | null;
  trend: TrendDirection;
  model_name: string;
  prediction_date: string;
  predicted_date: string;
}

export interface ForecastFiltersState {
  sector: string | null;
  minReturn: number | null;
  maxReturn: number | null;
  minConfidence: number | null;
  search: string;
}

/* ── Dashboard page types (Phase 28) ─────────────── */

/** Each cell in the S&P 500 treemap. */
export interface TreemapCell {
  ticker: string;
  name: string;
  sector: string;
  marketCap: number;
  dailyChangePct: number;
  lastClose: number;
}

/** Grouped treemap data by sector (Recharts nested treemap format). */
export interface TreemapSectorGroup {
  name: string;
  children: TreemapCell[];
}

/** Selectable timeframe for the historical OHLCV chart. */
export type Timeframe = "1D" | "1W" | "1M" | "3M" | "1Y";

/** A single OHLC candle (minute or daily granularity). */
export interface CandlePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** Summary metrics shown on the metric cards. */
export interface StockMetrics {
  ticker: string;
  companyName: string;
  sector: string;
  currentPrice: number;
  dailyChangePct: number;
  marketCap: number;
  volume: number;
  vwap: number | null;
  high52w: number | null;
  low52w: number | null;
}

/* ── Drift page types (Phase 29) ─────────────────── */

/** Parsed active model info for the drift page header card. */
export interface ActiveModelInfo {
  modelName: string;
  scalerVariant: string;
  version: number;
  trainedDate: string;
  isActive: boolean;
  oosRmse: number | null;
  oosMae: number | null;
  oosDirectionalAccuracy: number | null;
}

/** A single data point for the rolling performance time series. */
export interface RollingPerformancePoint {
  date: string;
  rmse: number | null;
  mae: number | null;
  directionalAccuracy: number | null;
}

/** Retrain event summary for the status panel. */
export interface RetrainStatus {
  lastRetrainDate: string | null;
  isRetraining: boolean;
  oldModel: { name: string; rmse: number; mae: number } | null;
  newModel: { name: string; rmse: number; mae: number } | null;
  improvementPct: number | null;
}

/** A single feature's distribution comparison (training vs recent). */
export interface FeatureDistribution {
  feature: string;
  trainingBins: { bin: string; count: number }[];
  recentBins: { bin: string; count: number }[];
  ksStat: number | null;
  psiValue: number | null;
  isDrifted: boolean;
}

/** Aggregated drift page data for the mock generator. */
export interface DriftPageData {
  activeModel: ActiveModelInfo | null;
  events: DriftEventEntry[];
  rollingPerformance: RollingPerformancePoint[];
  retrainStatus: RetrainStatus;
  featureDistributions: FeatureDistribution[];
}
