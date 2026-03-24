import { useState, useMemo } from "react";
import { PageHeader } from "@/components/layout";
import { LoadingSpinner, ErrorFallback } from "@/components/ui";
import {
  MarketTreemap,
  MetricCards,
  CandlestickChart,
  HistoricalChart,
  DashboardTAPanel,
} from "@/components/dashboard";
import { useMarketOverview, useTickerIndicators, usePrediction } from "@/api";
import { buildTreemapData, deriveStockMetrics } from "@/utils/dashboardUtils";
import { generateMockMarketOverview, generateMockIntradayCandles } from "@/utils/mockDashboardData";
import { generateMockIndicatorSeries } from "@/utils/mockIndicatorData";
import useWebSocket from "@/hooks/useWebSocket";
import type { WebSocketStatus } from "@/api";

const STATUS_COLORS: Record<WebSocketStatus, string> = {
  connected: "bg-green-500",
  connecting: "bg-yellow-500",
  disconnected: "bg-red-500",
  error: "bg-red-500",
};

export default function Dashboard() {
  const marketQuery = useMarketOverview();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [showTA, setShowTA] = useState(false);

  // WebSocket live prices
  const wsUrl = `${(import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/^http/, "ws")}/ws/prices`;
  const { status: wsStatus, prices: livePrices } = useWebSocket(wsUrl);
  const livePrice = selectedTicker ? livePrices.get(selectedTicker) ?? null : null;

  const indicatorQuery = useTickerIndicators(selectedTicker ?? "");
  const predictionQuery = usePrediction(selectedTicker ?? "");

  // Build treemap data — mock only on error (not while loading)
  const stocks = marketQuery.data?.stocks
    ?? (marketQuery.isError ? generateMockMarketOverview() : []);
  const treemapData = useMemo(() => buildTreemapData(stocks), [stocks]);

  // Derive metric card data for selected stock
  const selectedStock = stocks.find((s) => s.ticker === selectedTicker) ?? null;

  const indicatorSeries = useMemo(() => {
    if (indicatorQuery.data?.series?.length) return indicatorQuery.data.series;
    if (selectedTicker && indicatorQuery.isError) return generateMockIndicatorSeries(selectedTicker);
    return [];
  }, [indicatorQuery.data, indicatorQuery.isError, selectedTicker]);

  const metrics = useMemo(() => {
    if (!selectedStock) return null;
    return deriveStockMetrics(selectedStock, indicatorSeries);
  }, [selectedStock, indicatorSeries]);

  const intradayCandles = useMemo(() => {
    if (!selectedTicker) return [];
    return generateMockIntradayCandles(selectedTicker, selectedStock?.last_close ?? undefined);
  }, [selectedTicker, selectedStock]);

  if (marketQuery.isLoading) return <LoadingSpinner />;
  if (marketQuery.isError && !marketQuery.data) {
    return (
      <ErrorFallback
        message="Failed to load market data"
        onRetry={() => marketQuery.refetch()}
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Market Dashboard"
        subtitle={
          <span className="inline-flex items-center gap-2">
            Real-time S&amp;P 500 overview and stock analysis
            <span
              className={`inline-block h-2 w-2 rounded-full ${STATUS_COLORS[wsStatus]}`}
              title={`WebSocket: ${wsStatus}`}
            />
          </span>
        }
      />

      {/* ── Treemap ── */}
      <MarketTreemap
        data={treemapData}
        selectedTicker={selectedTicker}
        onSelectTicker={setSelectedTicker}
      />

      {/* ── Metric Cards (visible when stock selected) ── */}
      {metrics && (
        <div className="mt-6">
          <MetricCards metrics={metrics} />
        </div>
      )}

      {/* ── Stock Detail Section ── */}
      {selectedTicker && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text-primary">
              {selectedTicker} — Detail View
            </h2>
            <button
              onClick={() => setSelectedTicker(null)}
              className="rounded-lg border border-border bg-bg-card px-3 py-1 text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              ✕ Close
            </button>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <CandlestickChart candles={intradayCandles} ticker={selectedTicker} livePrice={livePrice} />
            <HistoricalChart
              series={indicatorSeries}
              ticker={selectedTicker}
              predictedPrice={predictionQuery.data?.predicted_price ?? null}
              predictedDate={predictionQuery.data?.predicted_date ?? null}
            />
          </div>

          {/* ── TA Panel Toggle ── */}
          <button
            onClick={() => setShowTA((prev) => !prev)}
            className="rounded-lg border border-border bg-bg-card px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            {showTA ? "Hide" : "Show"} Technical Indicators
          </button>

          {showTA && (
            <DashboardTAPanel series={indicatorSeries} ticker={selectedTicker} />
          )}
        </div>
      )}
    </>
  );
}
