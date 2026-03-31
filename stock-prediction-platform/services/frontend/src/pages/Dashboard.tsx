import { useState, useMemo } from "react";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
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
  SentimentPanel,
} from "@/components/dashboard";
import { useMarketOverview, useTickerIndicators, usePrediction } from "@/api";
import { buildTreemapData, deriveStockMetrics } from "@/utils/dashboardUtils";
import { generateMockMarketOverview, generateMockIntradayCandles } from "@/utils/mockDashboardData";
import { generateMockIndicatorSeries } from "@/utils/mockIndicatorData";
import useWebSocket from "@/hooks/useWebSocket";
import type { WebSocketStatus } from "@/api";
// eslint-disable-next-line @typescript-eslint/no-unused-vars

const WS_DOT_COLOR: Record<WebSocketStatus, string> = {
  connected:    "#22c983",
  connecting:   "#f59e0b",
  disconnected: "#e05454",
  error:        "#e05454",
};

function PriceTickerStrip({ stocks }: { stocks: MarketOverviewEntry[] }) {
  const top20 = useMemo(
    () =>
      [...stocks]
        .filter((s) => s.market_cap != null && s.last_close != null)
        .sort((a, b) => (b.market_cap ?? 0) - (a.market_cap ?? 0))
        .slice(0, 20),
    [stocks],
  );

  if (top20.length === 0) return null;

  // Duplicate for seamless infinite loop
  const renderItems = (keyPrefix: string) =>
    top20.map((s) => {
      const chg = s.daily_change_pct ?? 0;
      const isPos = chg >= 0;
      const color = isPos ? "#22c983" : "#e05454";
      const sign  = isPos ? "+" : "";
      return (
        <Box
          key={`${keyPrefix}-${s.ticker}`}
          component="span"
          sx={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            mr: "32px",
            whiteSpace: "nowrap",
          }}
        >
          {/* Separator dot */}
          <Box
            component="span"
            sx={{
              width: 3,
              height: 3,
              borderRadius: "50%",
              bgcolor: "rgba(232,164,39,0.3)",
              display: "inline-block",
              mr: "6px",
            }}
          />
          <Box
            component="span"
            sx={{
              fontFamily: '"Syne", sans-serif',
              fontWeight: 700,
              fontSize: "0.7rem",
              letterSpacing: "0.06em",
              color: "#e8a427",
            }}
          >
            {s.ticker}
          </Box>
          <Box
            component="span"
            sx={{
              fontFamily: '"DM Mono", monospace',
              fontSize: "0.72rem",
              color: "#f0f2f8",
              fontWeight: 400,
            }}
          >
            ${s.last_close!.toFixed(2)}
          </Box>
          <Box
            component="span"
            sx={{
              fontFamily: '"DM Mono", monospace',
              fontSize: "0.68rem",
              color,
              fontWeight: 500,
            }}
          >
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
        borderBottom: "1px solid rgba(232, 164, 39, 0.1)",
        borderTop: "1px solid rgba(232, 164, 39, 0.1)",
        bgcolor: "rgba(10, 14, 25, 0.8)",
        py: "7px",
        mb: 2.5,
        position: "relative",
        // Fade edges
        "&::before, &::after": {
          content: '""',
          position: "absolute",
          top: 0,
          bottom: 0,
          width: 48,
          zIndex: 1,
          pointerEvents: "none",
        },
        "&::before": {
          left: 0,
          background: "linear-gradient(to right, #07090f, transparent)",
        },
        "&::after": {
          right: 0,
          background: "linear-gradient(to left, #07090f, transparent)",
        },
      }}
    >
      <Box
        sx={{
          display: "inline-block",
          whiteSpace: "nowrap",
          animation: "scroll-ticker 40s linear infinite",
          "@keyframes scroll-ticker": {
            "0%":   { transform: "translateX(0)" },
            "100%": { transform: "translateX(-50%)" },
          },
        }}
      >
        {renderItems("a")}
        {renderItems("b")}
      </Box>
    </Box>
  );
}

export default function Dashboard() {
  const marketQuery = useMarketOverview();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [showTA, setShowTA] = useState(false);

  const wsUrl = `${(import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/^http/, "ws")}/ws/prices`;
  const { status: wsStatus, prices: livePrices } = useWebSocket(wsUrl);
  const livePrice = selectedTicker ? livePrices.get(selectedTicker) ?? null : null;

  const indicatorQuery  = useTickerIndicators(selectedTicker ?? "");
  const predictionQuery = usePrediction(selectedTicker ?? "");

  const stocks = marketQuery.data?.stocks
    ?? (marketQuery.isError ? generateMockMarketOverview() : []);
  const treemapData = useMemo(() => buildTreemapData(stocks), [stocks]);

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

  const wsDotColor = WS_DOT_COLOR[wsStatus];

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
          <Box component="span" sx={{ display: "inline-flex", alignItems: "center", gap: 1.25 }}>
            Real-time S&amp;P 500 overview and stock analysis
            <Box
              component="span"
              sx={{
                display: "inline-flex",
                alignItems: "center",
                gap: 0.6,
                border: "1px solid rgba(232,164,39,0.2)",
                borderRadius: "4px",
                px: "6px",
                py: "2px",
                ml: 0.5,
              }}
            >
              <Box
                component="span"
                sx={{
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  bgcolor: wsDotColor,
                  boxShadow: `0 0 4px ${wsDotColor}`,
                  animation: wsStatus === "connected" ? "none" : "pulse-dot 2s infinite",
                  display: "inline-block",
                  "@keyframes pulse-dot": {
                    "0%, 100%": { opacity: 1 },
                    "50%":      { opacity: 0.3 },
                  },
                }}
              />
              <Box
                component="span"
                sx={{
                  fontFamily: '"Syne", sans-serif',
                  fontWeight: 700,
                  fontSize: "0.6rem",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: wsDotColor,
                }}
              >
                WS {wsStatus}
              </Box>
            </Box>
          </Box>
        }
      />

      {/* ── Price Ticker Strip ── */}
      <PriceTickerStrip stocks={stocks} />

      {/* ── Treemap ── */}
      <Paper sx={{ p: 2.5, mb: 3 }}>
        {marketQuery.isLoading ? (
          <Skeleton variant="rectangular" height={480} sx={{ bgcolor: "rgba(232,164,39,0.05)", borderRadius: 1 }} />
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
        PaperProps={{
          sx: {
            width: { xs: "100%", sm: 500 },
            p: 3,
            bgcolor: "#0a0e19",
            borderLeft: "1px solid rgba(232,164,39,0.12)",
          },
        }}
      >
        {selectedTicker && (
          <Box sx={{ height: "100%", overflow: "auto" }}>
            {/* Drawer header */}
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
              <Box>
                <Typography
                  sx={{
                    fontFamily: '"Syne", sans-serif',
                    fontWeight: 800,
                    fontSize: "1.1rem",
                    color: "#f0f2f8",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {selectedTicker}
                </Typography>
                {selectedStock?.company_name && (
                  <Typography
                    sx={{
                      fontFamily: '"DM Mono", monospace',
                      fontSize: "0.7rem",
                      color: "rgba(107,122,159,0.7)",
                      mt: 0.25,
                    }}
                  >
                    {selectedStock.company_name}
                  </Typography>
                )}
              </Box>
              <Button
                size="small"
                startIcon={<CloseIcon sx={{ fontSize: "0.85rem !important" }} />}
                onClick={() => setSelectedTicker(null)}
                variant="outlined"
                sx={{
                  borderColor: "rgba(232,164,39,0.25)",
                  color: "rgba(107,122,159,0.8)",
                  "&:hover": { borderColor: "#e8a427", color: "#e8a427" },
                  fontFamily: '"Syne", sans-serif',
                  fontSize: "0.65rem",
                  py: 0.5,
                }}
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
              sx={{ bgcolor: "#0d1220" }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon sx={{ color: "rgba(107,122,159,0.6)", fontSize: "1rem" }} />}
                sx={{ minHeight: 40, "& .MuiAccordionSummary-content": { my: 0 } }}
              >
                <Typography
                  sx={{
                    fontFamily: '"Syne", sans-serif',
                    fontWeight: 700,
                    fontSize: "0.68rem",
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "rgba(107,122,159,0.8)",
                  }}
                >
                  Technical Indicators
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ pt: 0 }}>
                <DashboardTAPanel series={indicatorSeries} ticker={selectedTicker} />
              </AccordionDetails>
            </Accordion>

            {/* Reddit Sentiment — Phase 71 */}
            {selectedTicker && (
              <Accordion sx={{ bgcolor: "#0d1220", mt: 1 }}>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon sx={{ color: "rgba(107,122,159,0.6)", fontSize: "1rem" }} />}
                  sx={{ minHeight: 40, "& .MuiAccordionSummary-content": { my: 0 } }}
                >
                  <Typography
                    sx={{
                      fontFamily: '"Syne", sans-serif',
                      fontWeight: 700,
                      fontSize: "0.68rem",
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      color: "rgba(107,122,159,0.8)",
                    }}
                  >
                    Reddit Sentiment
                  </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ pt: 0 }}>
                  <SentimentPanel ticker={selectedTicker} />
                </AccordionDetails>
              </Accordion>
            )}
          </Box>
        )}
      </Drawer>
    </Container>
  );
}
