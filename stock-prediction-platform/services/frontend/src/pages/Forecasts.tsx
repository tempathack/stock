import { useState, useMemo } from "react";
import { PageHeader } from "@/components/layout";
import { LoadingSpinner, ErrorFallback } from "@/components/ui";
import {
  ForecastFilters,
  ForecastTable,
  StockComparisonPanel,
  StockDetailChart,
  IndicatorOverlayCharts,
  StockShapPanel,
} from "@/components/forecasts";
import { useBulkPredictions, useMarketOverview, useTickerIndicators } from "@/api";
import type { ForecastRow, ForecastFiltersState, IndicatorValues } from "@/api";
import { joinForecastData, extractSectors } from "@/utils/forecastUtils";
import { generateMockForecasts } from "@/utils/mockForecastData";
import { generateMockIndicatorSeries } from "@/utils/mockIndicatorData";

const DEFAULT_FILTERS: ForecastFiltersState = {
  sector: null,
  minReturn: null,
  maxReturn: null,
  minConfidence: null,
  search: "",
};

/* ── Detail section for a selected stock ─────────── */

function StockDetailSection({
  ticker,
  forecastRow,
  onClose,
}: {
  ticker: string;
  forecastRow: ForecastRow | null;
  onClose: () => void;
}) {
  const indicatorQuery = useTickerIndicators(ticker);

  const series: IndicatorValues[] = useMemo(() => {
    if (indicatorQuery.data?.series && indicatorQuery.data.series.length > 0) {
      return indicatorQuery.data.series;
    }
    return generateMockIndicatorSeries(ticker);
  }, [indicatorQuery.data, ticker]);

  return (
    <div className="mt-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">
          {ticker} — Detail View
        </h2>
        <button
          onClick={onClose}
          className="rounded bg-bg-card px-3 py-1 text-sm text-text-secondary transition-colors hover:bg-border hover:text-text-primary"
        >
          Close
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Left: Price chart + indicator overlays */}
        <div className="space-y-4">
          <StockDetailChart
            ticker={ticker}
            series={series}
            predictedPrice={forecastRow?.predicted_price ?? 0}
            predictedDate={forecastRow?.predicted_date ?? ""}
            currentPrice={forecastRow?.current_price ?? null}
          />
          <IndicatorOverlayCharts series={series} />
        </div>

        {/* Right: SHAP panel */}
        <div>
          <StockShapPanel
            ticker={ticker}
            modelName={forecastRow?.model_name ?? "Unknown"}
          />
        </div>
      </div>
    </div>
  );
}

/* ── Main Forecasts Page ─────────────────────────── */

export default function Forecasts() {
  const bulkQuery = useBulkPredictions();
  const marketQuery = useMarketOverview();

  const [filters, setFilters] = useState<ForecastFiltersState>(DEFAULT_FILTERS);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);

  // Join predictions + market data; fall back to mock data during development
  const allRows = useMemo<ForecastRow[]>(() => {
    if (bulkQuery.data && marketQuery.data) {
      return joinForecastData(
        bulkQuery.data.predictions,
        marketQuery.data.stocks,
      );
    }
    return generateMockForecasts();
  }, [bulkQuery.data, marketQuery.data]);

  const sectors = useMemo(() => extractSectors(allRows), [allRows]);

  // Apply filters
  const filteredRows = useMemo(() => {
    return allRows.filter((row) => {
      if (filters.sector && row.sector !== filters.sector) return false;
      if (
        filters.minReturn != null &&
        row.expected_return_pct < filters.minReturn
      )
        return false;
      if (
        filters.maxReturn != null &&
        row.expected_return_pct > filters.maxReturn
      )
        return false;
      if (
        filters.minConfidence != null &&
        (row.confidence ?? 0) < filters.minConfidence
      )
        return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        if (
          !row.ticker.toLowerCase().includes(q) &&
          !row.company_name?.toLowerCase().includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [allRows, filters]);

  const handleToggleCompare = (ticker: string) => {
    setComparisonTickers((prev) =>
      prev.includes(ticker)
        ? prev.filter((t) => t !== ticker)
        : [...prev, ticker],
    );
  };

  const isLoading = bulkQuery.isLoading || marketQuery.isLoading;
  const isError = bulkQuery.isError && marketQuery.isError;
  const refetch = () => {
    bulkQuery.refetch();
    marketQuery.refetch();
  };

  if (isLoading) return <LoadingSpinner />;
  if (isError)
    return (
      <ErrorFallback
        message="Failed to load forecast data"
        onRetry={refetch}
      />
    );

  const selectedRow =
    selectedTicker != null
      ? allRows.find((r) => r.ticker === selectedTicker) ?? null
      : null;

  return (
    <>
      <PageHeader
        title="Stock Forecasts"
        subtitle="7-day price predictions for S&P 500 tickers"
      />

      <ForecastFilters
        filters={filters}
        onFilterChange={setFilters}
        sectors={sectors}
      />

      <div className="mt-4">
        <ForecastTable
          rows={filteredRows}
          selectedTicker={selectedTicker}
          comparisonTickers={comparisonTickers}
          onSelectTicker={setSelectedTicker}
          onToggleCompare={handleToggleCompare}
        />
      </div>

      {/* Comparison Panel */}
      <StockComparisonPanel
        rows={allRows}
        comparisonTickers={comparisonTickers}
        onRemove={handleToggleCompare}
        onSelectDetail={setSelectedTicker}
      />

      {/* Detail Section */}
      {selectedTicker && (
        <StockDetailSection
          ticker={selectedTicker}
          forecastRow={selectedRow}
          onClose={() => setSelectedTicker(null)}
        />
      )}
    </>
  );
}
