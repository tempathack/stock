import { useQuery } from "@tanstack/react-query";
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
