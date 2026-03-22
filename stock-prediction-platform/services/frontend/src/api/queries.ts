import { useQuery } from "@tanstack/react-query";
import apiClient from "./client";
import type {
  HealthResponse,
  PredictionResponse,
  BulkPredictionResponse,
  ModelComparisonResponse,
  DriftStatusResponse,
  MarketOverviewResponse,
  TickerIndicatorsResponse,
} from "./types";

/* ── query key constants ───────────────────────────────── */

export const queryKeys = {
  health: ["health"] as const,
  prediction: (ticker: string) => ["prediction", ticker] as const,
  bulkPredictions: ["predictions", "bulk"] as const,
  modelComparison: ["models", "comparison"] as const,
  modelDrift: ["models", "drift"] as const,
  marketOverview: ["market", "overview"] as const,
  tickerIndicators: (ticker: string) => ["market", "indicators", ticker] as const,
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
    refetchInterval: 60_000,
  });
}

export function usePrediction(ticker: string) {
  return useQuery({
    queryKey: queryKeys.prediction(ticker),
    queryFn: async () => {
      const { data } = await apiClient.get<PredictionResponse>(
        `/predict/${encodeURIComponent(ticker)}`,
      );
      return data;
    },
    enabled: !!ticker,
  });
}

export function useBulkPredictions() {
  return useQuery({
    queryKey: queryKeys.bulkPredictions,
    queryFn: async () => {
      const { data } = await apiClient.get<BulkPredictionResponse>("/predict/bulk");
      return data;
    },
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
