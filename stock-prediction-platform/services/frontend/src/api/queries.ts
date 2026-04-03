import { useQuery, useQueries } from "@tanstack/react-query";
import apiClient from "./client";
import type {
  HealthResponse,
  K8sHealthResponse,
  PredictionResponse,
  BulkPredictionResponse,
  ModelComparisonResponse,
  DriftStatusResponse,
  MarketOverviewResponse,
  TickerIndicatorsResponse,
  RollingPerformanceResponse,
  RetrainStatusResponse,
  AvailableHorizonsResponse,
  BacktestResponse,
  FlinkJobsResponse,
  FeastFreshnessResponse,
  KafkaLagResponse,
  AnalyticsSummaryResponse,
  CandlePoint,
  StreamingFeaturesResponse,
  PredictionSearchResponse,
  ModelSearchResponse,
  DriftEventSearchResponse,
  StockSearchResponse,
} from "./types";

/* ── query key constants ───────────────────────────────── */

export const queryKeys = {
  health: ["health"] as const,
  healthK8s: ["health", "k8s"] as const,
  prediction: (ticker: string, horizon?: number) =>
    ["prediction", ticker, horizon ?? "default"] as const,
  bulkPredictions: (horizon?: number) =>
    ["predictions", "bulk", horizon ?? "default"] as const,
  horizons: ["predict", "horizons"] as const,
  modelComparison: ["models", "comparison"] as const,
  modelDrift: ["models", "drift"] as const,
  marketOverview: ["market", "overview"] as const,
  tickerIndicators: (ticker: string) => ["market", "indicators", ticker] as const,
  rollingPerformance: (days: number) => ["models", "drift", "rolling-performance", days] as const,
  retrainStatus: ["models", "retrain-status"] as const,
  backtest: (ticker: string, start?: string, end?: string, horizon?: number) =>
    ["backtest", ticker, start, end, horizon] as const,
};

/* ── query hooks ───────────────────────────────────────── */

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>("/health");
      return data;
    },
    retry: false,
    refetchInterval: 30_000,
  });
}

export function useK8sHealth() {
  return useQuery({
    queryKey: queryKeys.healthK8s,
    queryFn: async () => {
      const { data } = await apiClient.get<K8sHealthResponse>("/health/k8s");
      return data;
    },
    retry: false,
    refetchInterval: 60_000,
  });
}

export function usePrediction(ticker: string, horizon?: number) {
  return useQuery({
    queryKey: queryKeys.prediction(ticker, horizon),
    queryFn: async () => {
      const params = horizon != null ? { params: { horizon } } : {};
      const { data } = await apiClient.get<PredictionResponse>(
        `/predict/${encodeURIComponent(ticker)}`,
        params,
      );
      return data;
    },
    enabled: !!ticker,
  });
}

export function useBulkPredictions(horizon?: number) {
  return useQuery({
    queryKey: queryKeys.bulkPredictions(horizon),
    queryFn: async () => {
      const params = horizon != null ? { params: { horizon } } : {};
      const { data } = await apiClient.get<BulkPredictionResponse>(
        "/predict/bulk",
        params,
      );
      return data;
    },
  });
}

export function useAvailableHorizons() {
  return useQuery({
    queryKey: queryKeys.horizons,
    queryFn: async () => {
      const { data } = await apiClient.get<AvailableHorizonsResponse>(
        "/predict/horizons",
      );
      return data;
    },
    staleTime: 5 * 60_000,
  });
}

export function useModelComparison() {
  return useQuery({
    queryKey: queryKeys.modelComparison,
    queryFn: async () => {
      const { data } = await apiClient.get<ModelComparisonResponse>("/models/comparison");
      return data;
    },
  });
}

export function useModelDrift() {
  return useQuery({
    queryKey: queryKeys.modelDrift,
    queryFn: async () => {
      const { data } = await apiClient.get<DriftStatusResponse>("/models/drift");
      return data;
    },
  });
}

export function useMarketOverview() {
  return useQuery({
    queryKey: queryKeys.marketOverview,
    queryFn: async () => {
      const { data } = await apiClient.get<MarketOverviewResponse>("/market/overview");
      return data;
    },
    refetchInterval: 30_000,
  });
}

export function useTickerIndicators(ticker: string) {
  return useQuery({
    queryKey: queryKeys.tickerIndicators(ticker),
    queryFn: async () => {
      const { data } = await apiClient.get<TickerIndicatorsResponse>(
        `/market/indicators/${encodeURIComponent(ticker)}`,
      );
      return data;
    },
    enabled: !!ticker,
  });
}

export function useRollingPerformance(days = 30) {
  return useQuery({
    queryKey: queryKeys.rollingPerformance(days),
    queryFn: async () => {
      const { data } = await apiClient.get<RollingPerformanceResponse>(
        "/models/drift/rolling-performance",
        { params: { days } },
      );
      return data;
    },
  });
}

export function useRetrainStatus() {
  return useQuery({
    queryKey: queryKeys.retrainStatus,
    queryFn: async () => {
      const { data } = await apiClient.get<RetrainStatusResponse>(
        "/models/retrain-status",
      );
      return data;
    },
  });
}

export function useBacktest(
  ticker: string,
  start?: string,
  end?: string,
  horizon?: number,
) {
  return useQuery({
    queryKey: queryKeys.backtest(ticker, start, end, horizon),
    queryFn: async () => {
      const params: Record<string, string | number> = {};
      if (start) params.start = start;
      if (end) params.end = end;
      if (horizon != null) params.horizon = horizon;
      const { data } = await apiClient.get<BacktestResponse>(
        `/backtest/${encodeURIComponent(ticker)}`,
        { params },
      );
      return data;
    },
    enabled: !!ticker,
  });
}

// --- Analytics hooks (Phase 69) ---

export function useFlinkJobs() {
  return useQuery({
    queryKey: ["analytics", "flink", "jobs"],
    queryFn: async () => {
      const { data } = await apiClient.get<FlinkJobsResponse>("/analytics/flink/jobs");
      return data;
    },
    refetchInterval: 10_000,
    retry: false,
  });
}

export function useFeatureFreshness() {
  return useQuery({
    queryKey: ["analytics", "feast", "freshness"],
    queryFn: async () => {
      const { data } = await apiClient.get<FeastFreshnessResponse>("/analytics/feast/freshness");
      return data;
    },
    refetchInterval: 30_000,
    retry: false,
  });
}

export function useKafkaLag() {
  return useQuery({
    queryKey: ["analytics", "kafka", "lag"],
    queryFn: async () => {
      const { data } = await apiClient.get<KafkaLagResponse>("/analytics/kafka/lag");
      return data;
    },
    refetchInterval: 15_000,
    retry: false,
  });
}

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<AnalyticsSummaryResponse>("/analytics/summary");
      return data;
    },
    refetchInterval: 30_000,
    retry: false,
  });
}

export function useAnalyticsCandles(ticker: string, interval: "1h" | "1d") {
  return useQuery({
    queryKey: ["analytics", "candles", ticker, interval],
    queryFn: async () => {
      const { data } = await apiClient.get<{ candles: CandlePoint[] }>(
        "/market/candles",
        { params: { ticker, interval, limit: 100 } }
      );
      return data;
    },
    retry: false,
  });
}

// ── Streaming Features (Phase 70) ──────────────────────────────────────────

export function useStreamingFeatures(ticker: string) {
  return useQuery({
    queryKey: ["market", "streaming-features", ticker.toUpperCase()],
    queryFn: async () => {
      const { data } = await apiClient.get<StreamingFeaturesResponse>(
        `/market/streaming-features/${encodeURIComponent(ticker.toUpperCase())}`,
      );
      return data;
    },
    enabled: !!ticker,
    refetchInterval: 5_000,   // 5s poll — matches Flink HOP window output rate
    staleTime: 4_000,
  });
}

// ── Multi-Horizon Predictions (Phase 88) ───────────────────────────────────

const ALL_HORIZONS = [1, 7, 14, 30] as const;

export function useAllHorizonsPredictions() {
  const results = useQueries({
    queries: ALL_HORIZONS.map((h) => ({
      queryKey: queryKeys.bulkPredictions(h),
      queryFn: async () => {
        const { data } = await apiClient.get<BulkPredictionResponse>(
          "/predict/bulk",
          { params: { horizon: h } },
        );
        return data;
      },
      staleTime: 60_000,
      retry: false,
    })),
  });

  const isLoading = results.some((r) => r.isPending);
  const isError = results.every((r) => r.isError);
  const isPartialError = !isLoading && results.some((r) => r.isError) && !isError;
  const loadedHorizons = results
    .map((r, i) => ({ horizon: ALL_HORIZONS[i] as number, data: r.data! }))
    .filter((entry) => entry.data != null);

  return { results, isLoading, isError, isPartialError, loadedHorizons };
}

// ── Search hooks (Phase 90) ────────────────────────────────────────────────

export interface SearchParams {
  q?: string;
  page?: number;
  page_size?: number;
  ticker?: string;
  model_id?: number;
  confidence_min?: number;
  date_from?: string;
  date_to?: string;
  status?: string;
  r2_min?: number;
  rmse_max?: number;
  mae_max?: number;
  drift_type?: string;
  severity?: string;
  sector?: string;
  exchange?: string;
}

export function useSearchPredictions(params: SearchParams, enabled: boolean = false) {
  return useQuery({
    queryKey: ["search", "predictions", params],
    queryFn: async () => {
      const { data } = await apiClient.get<PredictionSearchResponse>("/search/predictions", { params });
      return data;
    },
    staleTime: 30_000,
    enabled,
  });
}

export function useSearchModels(params: SearchParams, enabled: boolean = false) {
  return useQuery({
    queryKey: ["search", "models", params],
    queryFn: async () => {
      const { data } = await apiClient.get<ModelSearchResponse>("/search/models", { params });
      return data;
    },
    staleTime: 30_000,
    enabled,
  });
}

export function useSearchDriftEvents(params: SearchParams, enabled: boolean = false) {
  return useQuery({
    queryKey: ["search", "drift-events", params],
    queryFn: async () => {
      const { data } = await apiClient.get<DriftEventSearchResponse>("/search/drift-events", { params });
      return data;
    },
    staleTime: 30_000,
    enabled,
  });
}

export function useSearchStocks(params: SearchParams, enabled: boolean = false) {
  return useQuery({
    queryKey: ["search", "stocks", params],
    queryFn: async () => {
      const { data } = await apiClient.get<StockSearchResponse>("/search/stocks", { params });
      return data;
    },
    staleTime: 30_000,
    enabled,
  });
}
