import { useState, useMemo, useEffect, useRef } from "react";
import {
  Alert,
  Box,
  Button,
  Container,
  Drawer,
  Grid,
  Skeleton,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { PageHeader } from "@/components/layout";
import { ErrorFallback, ExportButtons } from "@/components/ui";
import {
  ForecastFilters,
  ForecastTable,
  StockComparisonPanel,
  StockDetailChart,
  IndicatorOverlayCharts,
  StockShapPanel,
  HorizonToggle,
} from "@/components/forecasts";
import {
  useBulkPredictions,
  useMarketOverview,
  useTickerIndicators,
  useAvailableHorizons,
  useAllHorizonsPredictions,
} from "@/api";
import type {
  ForecastRow,
  ForecastFiltersState,
  IndicatorValues,
  MultiHorizonForecastRow,
} from "@/api";
import {
  joinForecastData,
  joinMultiHorizonForecastData,
  extractSectors,
} from "@/utils/forecastUtils";
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
    <Box sx={{ height: "100%", overflow: "auto", p: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6" fontWeight={700}>
          {ticker} — Detail View
        </Typography>
        <Button size="small" startIcon={<CloseIcon />} onClick={onClose} variant="outlined">
          Close
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, xl: 6 }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <StockDetailChart
              ticker={ticker}
              series={series}
              predictedPrice={forecastRow?.predicted_price ?? 0}
              predictedDate={forecastRow?.predicted_date ?? ""}
              currentPrice={forecastRow?.current_price ?? null}
            />
            <IndicatorOverlayCharts series={series} />
          </Box>
        </Grid>
        <Grid size={{ xs: 12, xl: 6 }}>
          <StockShapPanel ticker={ticker} modelName={forecastRow?.model_name ?? "Unknown"} />
        </Grid>
      </Grid>
    </Box>
  );
}

/* ── Main Forecasts Page ─────────────────────────── */

export default function Forecasts() {
  // Multi-horizon queries for the main table
  const allHorizonsQuery = useAllHorizonsPredictions();
  // Single-horizon (7d) query for detail drawer + comparison panel (ForecastRow consumers)
  const bulkQuery7d = useBulkPredictions(7);
  const marketQuery = useMarketOverview();
  // HorizonToggle in detail drawer still needs available horizons
  const [detailHorizon, setDetailHorizon] = useState<number>(7);
  const horizonsQuery = useAvailableHorizons();
  const availableHorizons = horizonsQuery.data?.horizons ?? [7];

  const [filters, setFilters] = useState<ForecastFiltersState>(DEFAULT_FILTERS);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);
  const [timedOut, setTimedOut] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Multi-horizon rows for the main table
  const allMultiRows = useMemo<MultiHorizonForecastRow[]>(() => {
    if (allHorizonsQuery.loadedHorizons.length > 0) {
      const marketStocks = marketQuery.data?.stocks ?? [];
      return joinMultiHorizonForecastData(allHorizonsQuery.loadedHorizons, marketStocks);
    }
    return [];
  }, [allHorizonsQuery.loadedHorizons, marketQuery.data]);

  // Single-horizon ForecastRow[] for comparison panel + detail drawer
  const allSingleRows = useMemo<ForecastRow[]>(() => {
    if (bulkQuery7d.data) {
      const marketStocks = marketQuery.data?.stocks ?? [];
      return joinForecastData(bulkQuery7d.data.predictions, marketStocks);
    }
    return [];
  }, [bulkQuery7d.data, marketQuery.data]);

  const sectors = useMemo(() => {
    // extractSectors accepts ForecastRow[]; use the single-horizon rows for sector extraction
    return extractSectors(allSingleRows);
  }, [allSingleRows]);

  // Apply filters to multi-horizon rows
  // minReturn/maxReturn apply to the 7d return column (matches default sort)
  const filteredMultiRows = useMemo(() => {
    return allMultiRows.filter((row) => {
      if (filters.sector && row.sector !== filters.sector) return false;
      const ret7d = row.horizons[7]?.expected_return_pct ?? null;
      if (filters.minReturn != null && (ret7d == null || ret7d < filters.minReturn)) return false;
      if (filters.maxReturn != null && (ret7d == null || ret7d > filters.maxReturn)) return false;
      const conf7d = row.horizons[7]?.confidence ?? null;
      if (filters.minConfidence != null && (conf7d == null || conf7d < filters.minConfidence)) return false;
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
  }, [allMultiRows, filters]);

  const handleToggleCompare = (ticker: string) => {
    setComparisonTickers((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker],
    );
  };

  const isLoading = allHorizonsQuery.isLoading || marketQuery.isLoading;

  // 15-second timeout guard — prevents infinite skeleton when API is unreachable
  useEffect(() => {
    if (isLoading && !timedOut) {
      timeoutRef.current = setTimeout(() => setTimedOut(true), 15_000);
    } else if (!isLoading) {
      setTimedOut(false);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

  const refetch = () => {
    setTimedOut(false);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    allHorizonsQuery.results.forEach((r) => { void r.refetch(); });
    marketQuery.refetch();
  };

  if (isLoading && !timedOut) {
    return (
      <Container maxWidth="xl">
        <PageHeader
          title="Stock Forecasts"
          subtitle="Multi-horizon price predictions for S&P 500 tickers"
        />
        <Box sx={{ mt: 2 }}>
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} variant="rectangular" height={52} sx={{ mb: 0.5, borderRadius: 1 }} />
          ))}
        </Box>
        <Box sx={{ textAlign: "center", mt: 2, color: "text.secondary", fontSize: "0.875rem" }}>
          Loading forecasts for all horizons…
        </Box>
      </Container>
    );
  }

  if (allHorizonsQuery.isError || timedOut) {
    return (
      <ErrorFallback
        message="Failed to load forecast data. Check that the prediction service is running."
        onRetry={refetch}
      />
    );
  }

  const selectedSingleRow =
    selectedTicker != null
      ? allSingleRows.find((r) => r.ticker === selectedTicker) ?? null
      : null;

  const today = new Date().toISOString().slice(0, 10);

  // CSV export: flatten all 4 horizons as columns
  const handleExportCsv = () => {
    const headers = [
      "Ticker", "Company", "Sector", "Current Price", "Daily Change %",
      "1D Pred. Price", "1D Return %",
      "7D Pred. Price", "7D Return %",
      "14D Pred. Price", "14D Return %",
      "30D Pred. Price", "30D Return %",
    ];
    const csvRows = filteredMultiRows.map((r) => [
      r.ticker,
      r.company_name ?? "",
      r.sector ?? "",
      r.current_price != null ? r.current_price.toFixed(2) : "",
      r.daily_change_pct != null ? r.daily_change_pct.toFixed(2) : "",
      r.horizons[1]?.predicted_price.toFixed(2) ?? "",
      r.horizons[1]?.expected_return_pct.toFixed(2) ?? "",
      r.horizons[7]?.predicted_price.toFixed(2) ?? "",
      r.horizons[7]?.expected_return_pct.toFixed(2) ?? "",
      r.horizons[14]?.predicted_price.toFixed(2) ?? "",
      r.horizons[14]?.expected_return_pct.toFixed(2) ?? "",
      r.horizons[30]?.predicted_price.toFixed(2) ?? "",
      r.horizons[30]?.expected_return_pct.toFixed(2) ?? "",
    ]);
    exportToCsv(`forecasts_all_horizons_${today}.csv`, headers, csvRows);
  };

  // PDF export: flatten all 4 horizons
  const handleExportPdf = () => {
    const headers = [
      "Ticker", "Company", "Sector",
      "1D Pred.", "1D Ret%",
      "7D Pred.", "7D Ret%",
      "14D Pred.", "14D Ret%",
      "30D Pred.", "30D Ret%",
    ];
    const pdfRows = filteredMultiRows.map((r) => [
      r.ticker,
      r.company_name ?? "",
      r.sector ?? "",
      r.horizons[1]?.predicted_price.toFixed(2) ?? "—",
      r.horizons[1]?.expected_return_pct.toFixed(2) ?? "—",
      r.horizons[7]?.predicted_price.toFixed(2) ?? "—",
      r.horizons[7]?.expected_return_pct.toFixed(2) ?? "—",
      r.horizons[14]?.predicted_price.toFixed(2) ?? "—",
      r.horizons[14]?.expected_return_pct.toFixed(2) ?? "—",
      r.horizons[30]?.predicted_price.toFixed(2) ?? "—",
      r.horizons[30]?.expected_return_pct.toFixed(2) ?? "—",
    ]);
    exportTableToPdf(
      `forecasts_all_horizons_${today}.pdf`,
      "Stock Forecasts — All Horizons",
      headers,
      pdfRows,
      [`Generated: ${today}`, `Rows: ${filteredMultiRows.length}`],
    );
  };

  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Stock Forecasts"
        subtitle="Multi-horizon price predictions for S&P 500 tickers"
      />

      {allHorizonsQuery.isPartialError && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Some forecast horizons are unavailable. Showing partial data for{" "}
          {allHorizonsQuery.loadedHorizons.length} of 4 horizons.
        </Alert>
      )}

      <Box
        sx={{
          mb: 2,
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "flex-end",
          gap: 2,
        }}
      >
        <ExportButtons
          disabled={filteredMultiRows.length === 0}
          onExportCsv={handleExportCsv}
          onExportPdf={handleExportPdf}
        />
      </Box>

      <Box sx={{ mb: 2 }}>
        <ForecastFilters filters={filters} onFilterChange={setFilters} sectors={sectors} />
      </Box>

      <ForecastTable
        rows={filteredMultiRows}
        selectedTicker={selectedTicker}
        onSelectTicker={setSelectedTicker}
      />

      {/* Comparison Panel — uses single-horizon ForecastRow[] */}
      <StockComparisonPanel
        rows={allSingleRows}
        comparisonTickers={comparisonTickers}
        onRemove={handleToggleCompare}
        onSelectDetail={setSelectedTicker}
      />

      {/* Detail Drawer — HorizonToggle still lives here */}
      <Drawer
        anchor="right"
        open={!!selectedTicker}
        onClose={() => setSelectedTicker(null)}
        PaperProps={{
          sx: {
            width: { xs: "100%", md: "60vw", xl: 900 },
            bgcolor: "background.default",
          },
        }}
      >
        {selectedTicker && (
          <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
            <HorizonToggle
              horizons={availableHorizons}
              selected={detailHorizon}
              onChange={setDetailHorizon}
              loading={false}
            />
          </Box>
        )}
        {selectedTicker && (
          <StockDetailSection
            ticker={selectedTicker}
            forecastRow={selectedSingleRow}
            onClose={() => setSelectedTicker(null)}
          />
        )}
      </Drawer>
    </Container>
  );
}
