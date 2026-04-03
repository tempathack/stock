/**
 * useSentimentTimeseries — REST polling hook for 10h sentiment history.
 *
 * Polls GET /market/sentiment/{ticker}/timeseries every 120 seconds (aligns
 * with Flink TUMBLE 2-min window emission rate). Returns SentimentTimeseriesResponse.
 *
 * Design decision: REST polling (not WebSocket) — the /ws/sentiment/{ticker}
 * WebSocket delivers only the latest scalar; history requires a REST endpoint
 * that queries the sentiment_timeseries TimescaleDB hypertable.
 */
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/api/client";
import type { SentimentTimeseriesResponse } from "@/api/types";

export function useSentimentTimeseries(ticker: string) {
  return useQuery<SentimentTimeseriesResponse>({
    queryKey: ["market", "sentiment-timeseries", ticker],
    queryFn: async () => {
      const { data } = await apiClient.get<SentimentTimeseriesResponse>(
        `/market/sentiment/${ticker}/timeseries`
      );
      return data;
    },
    enabled: !!ticker,
    refetchInterval: 120_000,  // 2 minutes — matches TUMBLE window interval
    staleTime: 110_000,        // stay fresh for 110s before background refetch
  });
}
