import { useState, useMemo } from "react";
import { PageHeader } from "@/components/layout";
import { LoadingSpinner, ErrorFallback, ExportButtons } from "@/components/ui";
import {
  ForecastFilters,
  ForecastTable,
  StockComparisonPanel,
  StockDetailChart,
  IndicatorOverlayCharts,
  StockShapPanel,
  HorizonToggle,
} from "@/components/forecasts";
import { useBulkPredictions, useMarketOverview, useTickerIndicators, useAvailableHorizons } from "@/api";
import type { ForecastRow, ForecastFiltersState, IndicatorValues } from "@/api";
import { joinForecastData, extractSectors } from "@/utils/forecastUtils";
import { generateMockForecasts } from "@/utils/mockForecastData";
import { generateMockIndicatorSeries } from "@/utils/mockIndicatorData";
import { exportToCsv } from "@/utils/exportCsv";
import { exportTableToPdf } from "@/utils/exportPdf";

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
    if (indicatorQuery.isError) return generateMockIndicatorSeries(ticker);
    return [];
  }, [indicatorQuery.data, indicatorQuery.isError, ticker]);

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
  const [horizon, setHorizon] = useState<number>(7);
  const horizonsQuery = useAvailableHorizons();
  const bulkQuery = useBulkPredictions(horizon);
  const marketQuery = useMarketOverview();

  const [filters, setFilters] = useState<ForecastFiltersState>(DEFAULT_FILTERS);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);

  const availableHorizons = horizonsQuery.data?.horizons ?? [7];

  // Join predictions + market data; mock only on error (not while loading)
  const allRows = useMemo<ForecastRow[]>(() => {
    if (bulkQuery.data && marketQuery.data) {
      return joinForecastData(
        bulkQuery.data.predictions,
        marketQuery.data.stocks,
      );
    }
    if (bulkQuery.isError || marketQuery.isError) {
      return generateMockForecasts(horizon);
    }
    return [];
  }, [bulkQuery.data, marketQuery.data, bulkQuery.isError, marketQuery.isError, horizon]);

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
        subtitle={`${horizon}-day price predictions for S&P 500 tickers`}
      />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <HorizonToggle
          horizons={availableHorizons}
          selected={horizon}
          onChange={setHorizon}
          loading={bulkQuery.isFetching}
        />
        <ExportButtons
          disabled={filteredRows.length === 0}
          onExportCsv={() => {
            const today = new Date().toISOString().slice(0, 10);
            const headers = ["Ticker", "Company", "Sector", "Current Price", "Predicted Price", "Return %", "Confidence", "Daily Change %", "Trend"];
            const rows = filteredRows.map((r) => [
              r.ticker,
              r.company_name ?? "",
              r.sector ?? "",
              r.current_price != null ? r.current_price.toFixed(2) : "",
              r.predicted_price.toFixed(2),
              r.expected_return_pct.toFixed(2),
              r.confidence != null ? r.confidence.toFixed(2) : "",
              r.daily_change_pct != null ? r.daily_change_pct.toFixed(2) : "",
              r.trend,
            ]);
            exportToCsv(`forecasts_${horizon}d_${today}.csv`, headers, rows);
          }}
          onExportPdf={() => {
            const today = new Date().toISOString().slice(0, 10);
            const headers = ["Ticker", "Company", "Sector", "Current Price", "Predicted Price", "Return %", "Confidence", "Daily Change %", "Trend"];
            const rows = filteredRows.map((r) => [
              r.ticker,
              r.company_name ?? "",
              r.sector ?? "",
              r.current_price != null ? r.current_price.toFixed(2) : "",
              r.predicted_price.toFixed(2),
              r.expected_return_pct.toFixed(2),
              r.confidence != null ? r.confidence.toFixed(2) : "",
              r.daily_change_pct != null ? r.daily_change_pct.toFixed(2) : "",
              r.trend,
            ]);
            exportTableToPdf(
              `forecasts_${horizon}d_${today}.pdf`,
              `Stock Forecasts \u2014 ${horizon}d Predictions`,
              headers,
              rows,
              [`Generated: ${today}`, `Horizon: ${horizon} days`, `Rows: ${filteredRows.length}`],
            );
          }}
        />
      </div>

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
