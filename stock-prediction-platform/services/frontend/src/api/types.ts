/* TypeScript interfaces mirroring FastAPI Pydantic schemas */

export interface HealthResponse {
  service: string;
  version: string;
  status: string;
  redis_status?: string | null;
  db_pool?: {
    pool_size: number;
    checked_in: number;
    checked_out: number;
    overflow: number;
    invalid: string;
  } | null;
}

export interface K8sHealthResponse {
  available: boolean;
  running_pods?: number | null;
  namespaces?: string[];
}

export interface PredictionResponse {
  ticker: string;
  prediction_date: string;
  predicted_date: string;
  predicted_price: number;
  model_name: string;
  confidence: number | null;
  horizon_days?: number | null;
}

export interface BulkPredictionResponse {
  predictions: PredictionResponse[];
  model_name: string | null;
  generated_at: string | null;
  count: number;
  horizon_days?: number | null;
}

export interface AvailableHorizonsResponse {
  horizons: number[];
  default: number;
}

export type HorizonOption = 1 | 7 | 30;

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

/* ── Rolling Performance & Retrain Status (Phase 32) ─── */

export interface RollingPerfEntry {
  date: string;
  rmse: number | null;
  mae: number | null;
  directional_accuracy: number | null;
  n_predictions: number;
}

export interface RollingPerformanceResponse {
  entries: RollingPerfEntry[];
  model_name: string | null;
  period_days: number;
  count: number;
}

export interface RetrainStatusResponse {
  model_name: string | null;
  version: string | null;
  trained_at: string | null;
  is_active: boolean;
  oos_metrics: Record<string, unknown>;
  previous_model: string | null;
  previous_trained_at: string | null;
  previous_oos_metrics?: Record<string, number>;
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
  horizon_days?: number | null;
}

export interface ForecastFiltersState {
  sector: string | null;
  minReturn: number | null;
  maxReturn: number | null;
  minConfidence: number | null;
  search: string;
}

/* ── WebSocket types (Phase 45) ──────────────────── */

export interface WebSocketPriceUpdate {
  ticker: string;
  price: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

export type WebSocketMessage =
  | { type: "price_update"; prices: WebSocketPriceUpdate[] }
  | { type: "market_closed"; next_open: string };

export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

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
  oldModel: { name: string; rmse: number | null; mae: number | null } | null;
  newModel: { name: string; rmse: number | null; mae: number | null } | null;
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

/* ── Backtest types (Phase 46) ───────────────────── */

export interface BacktestDataPoint {
  date: string;
  actual_price: number;
  predicted_price: number;
  error: number;
  error_pct: number;
}

export interface BacktestMetrics {
  rmse: number;
  mae: number;
  mape: number;
  directional_accuracy: number;
  r2: number;
  total_points: number;
}

export interface BacktestResponse {
  ticker: string;
  model_name: string;
  horizon: number;
  start_date: string;
  end_date: string;
  metrics: BacktestMetrics;
  series: BacktestDataPoint[];
}

// --- Analytics interfaces (Phase 69) ---

export interface FlinkJobEntry {
  job_id: string;
  name: string;
  state: "RUNNING" | "FAILED" | "FAILING" | "RESTARTING" | "CANCELED" | "FINISHED" | string;
  start_time: number;
  duration_ms: number;
  tasks_running: number;
}

export interface FlinkJobsResponse {
  jobs: FlinkJobEntry[];
  total_running: number;
  total_failed: number;
}

export interface FeastViewFreshness {
  view_name: string;
  last_updated: string | null;
  staleness_seconds: number | null;
  status: "fresh" | "stale" | "unknown";
}

export interface FeastFreshnessResponse {
  views: FeastViewFreshness[];
  registry_available: boolean;
}

export interface KafkaPartitionLag {
  partition: number;
  current_offset: number;
  end_offset: number;
  lag: number;
}

export interface KafkaLagResponse {
  topic: string;
  consumer_group: string;
  partitions: KafkaPartitionLag[];
  total_lag: number;
  sampled_at: string;
}

export interface AnalyticsSummaryResponse {
  argocd_sync_status: string | null;
  flink_running_jobs: number;
  flink_failed_jobs: number;
  feast_online_latency_ms: number | null;
  ca_last_refresh: string | null;
}

// ── Streaming Features (Phase 70) ──────────────────────────────────────────

export interface StreamingFeaturesResponse {
  ticker: string;
  ema_20: number | null;
  rsi_14: number | null;
  macd_signal: number | null;
  available: boolean;
  source: string;
  sampled_at: string | null;
}

// ── Multi-Horizon Forecast types (Phase 88) ────────────────────────────────

export interface HorizonPrediction {
  predicted_price: number;
  expected_return_pct: number;
  confidence: number | null;
  predicted_date: string;
  trend: TrendDirection;
}

export interface MultiHorizonForecastRow {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  current_price: number | null;
  daily_change_pct: number | null;
  horizons: { [horizonDays: number]: HorizonPrediction };
  model_name: string;
}
