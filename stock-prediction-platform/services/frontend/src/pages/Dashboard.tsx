import { useState, useMemo } from "react";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  Container,
  Drawer,
  Grid,
  Paper,
  Skeleton,
  Typography,
} from "@mui/material";
import type { MarketOverviewEntry } from "@/api";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CloseIcon from "@mui/icons-material/Close";
import { PageHeader } from "@/components/layout";
import { ErrorFallback } from "@/components/ui";
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

const WS_STATUS_COLOR: Record<WebSocketStatus, "success" | "warning" | "error"> = {
  connected: "success",
  connecting: "warning",
  disconnected: "error",
  error: "error",
};

function PriceTickerStrip({ stocks }: { stocks: MarketOverviewEntry[] }) {
  const top10 = useMemo(
    () =>
      [...stocks]
        .filter((s) => s.market_cap != null && s.last_close != null)
        .sort((a, b) => (b.market_cap ?? 0) - (a.market_cap ?? 0))
        .slice(0, 10),
    [stocks],
  );

  if (top10.length === 0) return null;

  const items = top10.map((s) => {
    const chg = s.daily_change_pct ?? 0;
    const color = chg >= 0 ? "#4caf50" : "#f44336";
    const sign = chg >= 0 ? "+" : "";
    return (
      <Box
        key={s.ticker}
        component="span"
        sx={{ mr: 4, display: "inline-block", whiteSpace: "nowrap" }}
      >
        <Box component="strong" sx={{ color: "primary.main", mr: 0.5 }}>
          {s.ticker}
        </Box>
        <Box component="span" sx={{ color: "text.primary", mr: 0.5 }}>
          ${s.last_close!.toFixed(2)}
        </Box>
        <Box component="span" sx={{ color }}>
          {sign}{chg.toFixed(2)}%
        </Box>
      </Box>
    );
  });

  return (
    <Box
      data-testid="price-ticker-strip"
      sx={{
        overflow: "hidden",
        whiteSpace: "nowrap",
        borderBottom: "1px solid rgba(0,188,212,0.2)",
        py: 0.5,
        mb: 2,
        bgcolor: "background.paper",
        borderRadius: 1,
      }}
    >
      <Box
        sx={{
          display: "inline-block",
          animation: "scroll-left 30s linear infinite",
        }}
      >
        {items}
      </Box>
    </Box>
  );
}

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

  if (marketQuery.isError && !marketQuery.data) {
    return (
      <ErrorFallback
        message="Failed to load market data"
        onRetry={() => marketQuery.refetch()}
      />
    );
  }

  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Market Dashboard"
        subtitle={
          <Box component="span" sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
            Real-time S&amp;P 500 overview and stock analysis
            <Chip
              size="small"
              label={`WS: ${wsStatus}`}
              color={WS_STATUS_COLOR[wsStatus]}
              sx={{ fontSize: "0.65rem", height: 18 }}
            />
          </Box>
        }
      />

      {/* ── Price Ticker Strip ── */}
      <PriceTickerStrip stocks={stocks} />

      {/* ── Treemap ── */}
      <Paper sx={{ p: 2, mb: 3 }}>
        {marketQuery.isLoading ? (
          <Skeleton variant="rectangular" height={400} />
        ) : (
          <MarketTreemap
            data={treemapData}
            selectedTicker={selectedTicker}
            onSelectTicker={setSelectedTicker}
          />
        )}
      </Paper>

      {/* ── Stock Detail Drawer ── */}
      <Drawer
        anchor="right"
        open={!!selectedTicker}
        onClose={() => setSelectedTicker(null)}
        PaperProps={{ sx: { width: { xs: "100%", sm: 480 }, p: 3, bgcolor: "background.default" } }}
      >
        {selectedTicker && (
          <Box sx={{ height: "100%", overflow: "auto" }}>
            {/* Header */}
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
              <Typography variant="h6" fontWeight={700}>
                {selectedTicker} — Detail View
              </Typography>
              <Button
                size="small"
                startIcon={<CloseIcon />}
                onClick={() => setSelectedTicker(null)}
                variant="outlined"
              >
                Close
              </Button>
            </Box>

            {/* Metric Cards */}
            {metrics && (
              <Box sx={{ mb: 3 }}>
                <MetricCards metrics={metrics} />
              </Box>
            )}

            {/* Charts */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid size={{ xs: 12 }}>
                <CandlestickChart
                  candles={intradayCandles}
                  ticker={selectedTicker}
                  livePrice={livePrice}
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <HistoricalChart
                  series={indicatorSeries}
                  ticker={selectedTicker}
                  predictedPrice={predictionQuery.data?.predicted_price ?? null}
                  predictedDate={predictionQuery.data?.predicted_date ?? null}
                />
              </Grid>
            </Grid>

            {/* TA Panel Accordion */}
            <Accordion
              expanded={showTA}
              onChange={(_, expanded) => setShowTA(expanded)}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="body2">Technical Indicators</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <DashboardTAPanel series={indicatorSeries} ticker={selectedTicker} />
              </AccordionDetails>
            </Accordion>
          </Box>
        )}
      </Drawer>
    </Container>
  );
}
