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

export default function Dashboard() {
  const marketQuery = useMarketOverview();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [showTA, setShowTA] = useState(false);

  const indicatorQuery = useTickerIndicators(selectedTicker ?? "");
  const predictionQuery = usePrediction(selectedTicker ?? "");

  // Build treemap data — fall back to mock when API unavailable
  const stocks = marketQuery.data?.stocks ?? generateMockMarketOverview();
  const treemapData = useMemo(() => buildTreemapData(stocks), [stocks]);

  // Derive metric card data for selected stock
  const selectedStock = stocks.find((s) => s.ticker === selectedTicker) ?? null;

  const indicatorSeries = useMemo(() => {
    if (indicatorQuery.data?.series?.length) return indicatorQuery.data.series;
    if (selectedTicker) return generateMockIndicatorSeries(selectedTicker);
    return [];
  }, [indicatorQuery.data, selectedTicker]);

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
        subtitle="Real-time S&P 500 overview and stock analysis"
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
            <CandlestickChart candles={intradayCandles} ticker={selectedTicker} />
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
