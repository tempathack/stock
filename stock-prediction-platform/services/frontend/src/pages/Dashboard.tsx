import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import {
  Box,
  Container,
  Grid,
  Skeleton,
  Typography,
  Collapse,
} from "@mui/material";
import type { MarketOverviewEntry } from "@/api";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import SearchIcon from "@mui/icons-material/Search";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import BarChartIcon from "@mui/icons-material/BarChart";
import ElectricBoltIcon from "@mui/icons-material/ElectricBolt";
import { ErrorFallback } from "@/components/ui";
import {
  MarketTreemap,
  MetricCards,
  CandlestickChart,
  HistoricalChart,
  DashboardTAPanel,
  SentimentPanel,
  StreamingFeaturesPanel,
  TopMoversPanel,
} from "@/components/dashboard";
import { useMarketOverview, useTickerIndicators, usePrediction } from "@/api";
import { buildTreemapData, deriveStockMetrics } from "@/utils/dashboardUtils";
import { generateMockMarketOverview, generateMockIntradayCandles } from "@/utils/mockDashboardData";
import { generateMockIndicatorSeries } from "@/utils/mockIndicatorData";
import useWebSocket from "@/hooks/useWebSocket";
import type { WebSocketStatus } from "@/api";

const WS_DOT_COLOR: Record<WebSocketStatus, string> = {
  connected:    "#00FF87",
  connecting:   "#FFD60A",
  disconnected: "#FF2D78",
  error:        "#FF2D78",
};

/* ── Price Ticker Strip ─────────────────────────────────── */
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

  const renderItems = (keyPrefix: string) =>
    top20.map((s) => {
      const chg   = s.daily_change_pct ?? 0;
      const isPos = chg >= 0;
      const color = isPos ? "#00FF87" : "#FF2D78";
      const glow  = isPos ? "rgba(0,255,135,0.5)" : "rgba(255,45,120,0.5)";
      return (
        <Box
          key={`${keyPrefix}-${s.ticker}`}
          component="span"
          sx={{ display: "inline-flex", alignItems: "center", gap: "6px", mr: "36px", whiteSpace: "nowrap" }}
        >
          <Box component="span" sx={{ width: 3, height: 3, borderRadius: "50%", bgcolor: "rgba(191,90,242,0.4)", display: "inline-block", mr: "4px" }} />
          <Box component="span" sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 800, fontSize: "0.68rem", letterSpacing: "0.06em", color: "#BF5AF2" }}>
            {s.ticker}
          </Box>
          <Box component="span" sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.7rem", color: "#F0EEFF", fontWeight: 500 }}>
            ${s.last_close!.toFixed(2)}
          </Box>
          <Box component="span" sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.66rem", color, fontWeight: 600, textShadow: `0 0 6px ${glow}` }}>
            {isPos ? "+" : ""}{chg.toFixed(2)}%
          </Box>
        </Box>
      );
    });

  return (
    <Box
      sx={{
        overflow: "hidden",
        borderBottom: "1px solid rgba(124,58,237,0.15)",
        borderTop: "1px solid rgba(124,58,237,0.15)",
        background: "rgba(13,10,36,0.5)",
        backdropFilter: "blur(12px)",
        py: "8px",
        mb: 3,
        position: "relative",
        "&::before, &::after": { content: '""', position: "absolute", top: 0, bottom: 0, width: 60, zIndex: 1, pointerEvents: "none" },
        "&::before": { left: 0, background: "linear-gradient(to right, rgba(2,0,10,0.95), transparent)" },
        "&::after":  { right: 0, background: "linear-gradient(to left,  rgba(2,0,10,0.95), transparent)" },
      }}
    >
      <Box sx={{ display: "inline-block", whiteSpace: "nowrap", animation: "scroll-ticker 40s linear infinite" }}>
        {renderItems("a")}
        {renderItems("b")}
      </Box>
    </Box>
  );
}

/* ── Stock Selector Dropdown ────────────────────────────── */
function StockSelector({
  stocks,
  selected,
  onSelect,
}: {
  stocks: MarketOverviewEntry[];
  selected: string | null;
  onSelect: (ticker: string | null) => void;
}) {
  const [open, setOpen]       = useState(false);
  const [query, setQuery]     = useState("");
  const ref                   = useRef<HTMLDivElement>(null);

  const sorted = useMemo(
    () => [...stocks].sort((a, b) => (b.market_cap ?? 0) - (a.market_cap ?? 0)),
    [stocks],
  );

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return sorted;
    return sorted.filter(
      (s) =>
        s.ticker.toLowerCase().includes(q) ||
        (s.company_name ?? "").toLowerCase().includes(q),
    );
  }, [sorted, query]);

  const selectedStock = stocks.find((s) => s.ticker === selected) ?? null;

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const pct     = selectedStock?.daily_change_pct ?? 0;
  const isPos   = pct >= 0;
  const pctColor = isPos ? "#00FF87" : "#FF2D78";

  return (
    <Box ref={ref} sx={{ position: "relative", mb: 3 }}>
      {/* Trigger button */}
      <Box
        onClick={() => setOpen((p) => !p)}
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          px: 2.5,
          py: 1.75,
          background: open
            ? "rgba(124,58,237,0.12)"
            : "rgba(13,10,36,0.7)",
          backdropFilter: "blur(20px)",
          border: `1px solid ${open ? "rgba(124,58,237,0.5)" : "rgba(124,58,237,0.25)"}`,
          borderRadius: "14px",
          cursor: "pointer",
          transition: "all 0.2s ease",
          boxShadow: open ? "0 0 24px rgba(124,58,237,0.2)" : "none",
          "&:hover": {
            borderColor: "rgba(124,58,237,0.45)",
            background: "rgba(124,58,237,0.1)",
            boxShadow: "0 0 20px rgba(124,58,237,0.15)",
          },
          userSelect: "none",
        }}
      >
        {/* Icon */}
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: "10px",
            background: "linear-gradient(135deg, rgba(124,58,237,0.3), rgba(0,245,255,0.2))",
            border: "1px solid rgba(124,58,237,0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <ShowChartIcon sx={{ fontSize: "1.1rem", color: "#BF5AF2" }} />
        </Box>

        {selected && selectedStock ? (
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: "flex", alignItems: "baseline", gap: 1 }}>
              <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 800, fontSize: "1rem", color: "#F0EEFF", letterSpacing: "0.02em" }}>
                {selected}
              </Typography>
              <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.72rem", color: pctColor, fontWeight: 600, textShadow: `0 0 8px ${pctColor}60` }}>
                {isPos ? "+" : ""}{pct.toFixed(2)}%
              </Typography>
            </Box>
            <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.65rem", color: "rgba(107,96,168,0.8)", mt: 0.1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {selectedStock.company_name} · {selectedStock.sector}
            </Typography>
          </Box>
        ) : (
          <Box sx={{ flex: 1 }}>
            <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 600, fontSize: "0.9rem", color: "rgba(107,96,168,0.7)" }}>
              Select a stock to analyze
            </Typography>
            <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.62rem", color: "rgba(107,96,168,0.45)", mt: 0.1 }}>
              Choose from {stocks.length} S&P 500 stocks
            </Typography>
          </Box>
        )}

        {selected && (
          <Box
            onClick={(e) => { e.stopPropagation(); onSelect(null); setOpen(false); }}
            sx={{
              px: 1, py: 0.3, borderRadius: "6px",
              border: "1px solid rgba(255,45,120,0.2)",
              color: "rgba(255,45,120,0.6)",
              fontSize: "0.6rem",
              fontFamily: '"Inter", sans-serif',
              fontWeight: 700,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              "&:hover": { borderColor: "#FF2D78", color: "#FF2D78", background: "rgba(255,45,120,0.08)" },
              transition: "all 0.15s ease",
              mr: 0.5,
              flexShrink: 0,
            }}
          >
            Clear
          </Box>
        )}

        <KeyboardArrowDownIcon
          sx={{
            color: "rgba(107,96,168,0.6)",
            fontSize: "1.2rem",
            flexShrink: 0,
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
          }}
        />
      </Box>

      {/* Dropdown panel */}
      {open && (
        <Box
          sx={{
            position: "absolute",
            top: "calc(100% + 8px)",
            left: 0,
            right: 0,
            zIndex: 1400,
            background: "rgba(10,7,28,0.97)",
            backdropFilter: "blur(24px)",
            border: "1px solid rgba(124,58,237,0.35)",
            borderRadius: "14px",
            boxShadow: "0 20px 60px rgba(0,0,0,0.7), 0 0 40px rgba(124,58,237,0.1)",
            overflow: "hidden",
          }}
        >
          {/* Search input */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1.25,
              px: 2,
              py: 1.25,
              borderBottom: "1px solid rgba(124,58,237,0.15)",
            }}
          >
            <SearchIcon sx={{ color: "rgba(107,96,168,0.6)", fontSize: "1rem", flexShrink: 0 }} />
            <Box
              component="input"
              autoFocus
              value={query}
              onChange={(e) => setQuery((e.target as HTMLInputElement).value)}
              placeholder="Search ticker or company name…"
              sx={{
                flex: 1,
                background: "none",
                border: "none",
                outline: "none",
                color: "#F0EEFF",
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: "0.8rem",
                "::placeholder": { color: "rgba(107,96,168,0.45)" },
              }}
            />
          </Box>

          {/* Results list */}
          <Box sx={{ maxHeight: 320, overflowY: "auto" }}>
            {filtered.length === 0 ? (
              <Box sx={{ px: 2.5, py: 3, textAlign: "center" }}>
                <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.75rem", color: "rgba(107,96,168,0.5)" }}>
                  No results for "{query}"
                </Typography>
              </Box>
            ) : (
              filtered.slice(0, 60).map((s) => {
                const chg    = s.daily_change_pct ?? 0;
                const isP    = chg >= 0;
                const col    = isP ? "#00FF87" : "#FF2D78";
                const isAct  = s.ticker === selected;
                return (
                  <Box
                    key={s.ticker}
                    onClick={() => { onSelect(s.ticker); setOpen(false); setQuery(""); }}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      px: 2,
                      py: 1,
                      gap: 1.5,
                      cursor: "pointer",
                      background: isAct ? "rgba(124,58,237,0.15)" : "transparent",
                      borderLeft: isAct ? "2px solid #7C3AED" : "2px solid transparent",
                      transition: "background 0.12s ease",
                      "&:hover": { background: "rgba(124,58,237,0.1)" },
                    }}
                  >
                    <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 700, fontSize: "0.8rem", color: isAct ? "#BF5AF2" : "#F0EEFF", width: 56, flexShrink: 0 }}>
                      {s.ticker}
                    </Typography>
                    <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.65rem", color: "rgba(107,96,168,0.7)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {s.company_name}
                    </Typography>
                    <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.7rem", color: col, fontWeight: 600, flexShrink: 0, textShadow: `0 0 6px ${col}50` }}>
                      {isP ? "+" : ""}{chg.toFixed(2)}%
                    </Typography>
                    {s.last_close != null && (
                      <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.68rem", color: "rgba(240,238,255,0.6)", flexShrink: 0, width: 68, textAlign: "right" }}>
                        ${s.last_close.toFixed(2)}
                      </Typography>
                    )}
                  </Box>
                );
              })
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
}

/* ── Section label ──────────────────────────────────────── */
function SectionLabel({ icon, label, accent = "#7C3AED" }: { icon: React.ReactNode; label: string; accent?: string }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
      <Box sx={{ width: 3, height: 18, borderRadius: "2px", background: `linear-gradient(180deg, ${accent}, transparent)`, boxShadow: `0 0 8px ${accent}90`, flexShrink: 0 }} />
      <Box sx={{ color: accent, display: "flex", alignItems: "center", "& svg": { fontSize: "0.85rem" } }}>{icon}</Box>
      <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 700, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(107,96,168,0.8)" }}>
        {label}
      </Typography>
    </Box>
  );
}

/* ── Main Dashboard ─────────────────────────────────────── */
export default function Dashboard() {
  const marketQuery     = useMarketOverview();
  const [selected, setSelected] = useState<string | null>(null);
  const detailRef       = useRef<HTMLDivElement>(null);

  const wsUrl = `${(import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/^http/, "ws")}/ws/prices`;
  const { status: wsStatus, prices: livePrices } = useWebSocket(wsUrl);
  const livePrice = selected ? livePrices.get(selected) ?? null : null;

  const indicatorQuery  = useTickerIndicators(selected ?? "");
  const predictionQuery = usePrediction(selected ?? "");

  const stocks = marketQuery.data?.stocks
    ?? (marketQuery.isError ? generateMockMarketOverview() : []);
  const treemapData = useMemo(() => buildTreemapData(stocks), [stocks]);

  const selectedStock = stocks.find((s) => s.ticker === selected) ?? null;

  const indicatorSeries = useMemo(() => {
    if (indicatorQuery.data?.series?.length) return indicatorQuery.data.series;
    if (selected && indicatorQuery.isError) return generateMockIndicatorSeries(selected);
    return [];
  }, [indicatorQuery.data, indicatorQuery.isError, selected]);

  const metrics = useMemo(() => {
    if (!selectedStock) return null;
    return deriveStockMetrics(selectedStock, indicatorSeries);
  }, [selectedStock, indicatorSeries]);

  const intradayCandles = useMemo(() => {
    if (!selected) return [];
    return generateMockIntradayCandles(selected, selectedStock?.last_close ?? undefined);
  }, [selected, selectedStock]);

  // Scroll to detail panel when stock is selected
  const handleSelect = useCallback((ticker: string | null) => {
    setSelected(ticker);
    if (ticker) {
      setTimeout(() => {
        detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }, []);

  const wsDotColor = WS_DOT_COLOR[wsStatus];
  const pct        = selectedStock?.daily_change_pct ?? 0;
  const isPos      = pct >= 0;

  if (marketQuery.isError && !marketQuery.data) {
    return <ErrorFallback message="Failed to load market data" onRetry={() => marketQuery.refetch()} />;
  }

  return (
    <Container maxWidth="xl">
      {/* ── Page Header ── */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Box sx={{ width: 4, height: 28, borderRadius: "3px", background: "linear-gradient(180deg, #7C3AED 0%, #00F5FF 100%)", boxShadow: "0 0 12px rgba(124,58,237,0.7)", flexShrink: 0 }} />
            <Typography
              sx={{
                fontFamily: '"Inter", sans-serif',
                fontWeight: 800,
                fontSize: { xs: "1.4rem", sm: "1.75rem" },
                letterSpacing: "-0.03em",
                background: "linear-gradient(90deg, #F0EEFF 0%, #BF5AF2 50%, #00F5FF 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Market Dashboard
            </Typography>
          </Box>

          {/* WS status badge */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, px: 1.5, py: 0.6, borderRadius: "8px", background: "rgba(13,10,36,0.7)", border: `1px solid ${wsDotColor}25` }}>
            <Box sx={{ width: 6, height: 6, borderRadius: "50%", bgcolor: wsDotColor, boxShadow: `0 0 6px ${wsDotColor}`, animation: wsStatus === "connected" ? "none" : "pulse-dot 2s infinite" }} />
            <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.62rem", color: wsDotColor, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>
              WS {wsStatus}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ mt: 1.5, height: "1px", background: "linear-gradient(to right, rgba(124,58,237,0.6), rgba(0,245,255,0.3), transparent)" }} />
      </Box>

      {/* ── Ticker Strip ── */}
      <PriceTickerStrip stocks={stocks} />

      {/* ── Treemap ── */}
      <Box sx={{ mb: 3 }}>
        {marketQuery.isLoading ? (
          <Box sx={{ background: "rgba(13,10,36,0.55)", border: "1px solid rgba(124,58,237,0.22)", borderRadius: "18px", p: 2 }}>
            <Skeleton variant="rectangular" height={480} sx={{ bgcolor: "rgba(124,58,237,0.06)", borderRadius: "12px" }} />
          </Box>
        ) : (
          <MarketTreemap
            data={treemapData}
            selectedTicker={selected}
            onSelectTicker={handleSelect}
          />
        )}
      </Box>

      {/* ── Top Movers ── */}
      <TopMoversPanel
        stocks={stocks}
        loading={marketQuery.isLoading}
        onSelectTicker={handleSelect}
      />

      {/* ── Stock Selector ── */}
      <StockSelector
        stocks={stocks}
        selected={selected}
        onSelect={handleSelect}
      />

      {/* ── Stock Detail Panel ── */}
      <Collapse in={!!selected} timeout={400}>
        <Box ref={detailRef}>
          {selected && selectedStock && (
            <Box
              sx={{
                background: "rgba(13,10,36,0.5)",
                backdropFilter: "blur(20px)",
                border: "1px solid rgba(124,58,237,0.22)",
                borderRadius: "18px",
                p: 3,
                mb: 3,
              }}
            >
              {/* Stock identity header */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  mb: 3,
                  pb: 2,
                  borderBottom: "1px solid rgba(124,58,237,0.15)",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Box
                    sx={{
                      px: 2.5,
                      py: 1,
                      borderRadius: "12px",
                      background: "linear-gradient(135deg, rgba(124,58,237,0.25), rgba(0,245,255,0.12))",
                      border: "1px solid rgba(124,58,237,0.4)",
                      boxShadow: "0 0 20px rgba(124,58,237,0.2)",
                    }}
                  >
                    <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 900, fontSize: "1.5rem", letterSpacing: "0.04em", background: "linear-gradient(90deg, #F0EEFF, #BF5AF2)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
                      {selected}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 600, fontSize: "0.9rem", color: "#F0EEFF" }}>
                      {selectedStock.company_name}
                    </Typography>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.25 }}>
                      <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.62rem", color: "rgba(107,96,168,0.7)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                        {selectedStock.sector}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                <Box sx={{ textAlign: "right" }}>
                  <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 700, fontSize: "1.6rem", color: "#F0EEFF", letterSpacing: "-0.02em" }}>
                    ${selectedStock.last_close?.toFixed(2) ?? "—"}
                  </Typography>
                  <Box sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 0.75, mt: 0.25 }}>
                    {isPos ? (
                      <TrendingUpIcon sx={{ fontSize: "1rem", color: "#00FF87" }} />
                    ) : (
                      <TrendingDownIcon sx={{ fontSize: "1rem", color: "#FF2D78" }} />
                    )}
                    <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 700, fontSize: "0.95rem", color: isPos ? "#00FF87" : "#FF2D78", textShadow: `0 0 10px ${isPos ? "rgba(0,255,135,0.6)" : "rgba(255,45,120,0.6)"}` }}>
                      {isPos ? "+" : ""}{pct.toFixed(2)}%
                    </Typography>
                  </Box>
                </Box>
              </Box>

              {/* Metric Cards */}
              {metrics && (
                <Box sx={{ mb: 3 }}>
                  <SectionLabel icon={<BarChartIcon />} label="Key Metrics" />
                  <MetricCards metrics={metrics} />
                </Box>
              )}

              {/* Charts */}
              <Box sx={{ mb: 3 }}>
                <SectionLabel icon={<ShowChartIcon />} label="Price Charts" accent="#00F5FF" />
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, lg: 6 }}>
                    <CandlestickChart
                      candles={intradayCandles}
                      ticker={selected}
                      livePrice={livePrice}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, lg: 6 }}>
                    <HistoricalChart
                      series={indicatorSeries}
                      ticker={selected}
                      predictedPrice={predictionQuery.data?.predicted_price ?? null}
                      predictedDate={predictionQuery.data?.predicted_date ?? null}
                    />
                  </Grid>
                </Grid>
              </Box>

              {/* Streaming Features */}
              <Box sx={{ mb: 3 }}>
                <SectionLabel icon={<ElectricBoltIcon />} label="Streaming Features" accent="#FFD60A" />
                <Box sx={{ background: "rgba(7,4,26,0.5)", border: "1px solid rgba(255,214,10,0.12)", borderRadius: "12px", p: 2 }}>
                  <StreamingFeaturesPanel ticker={selected} />
                </Box>
              </Box>

              {/* Technical Indicators */}
              <Box sx={{ mb: 3 }}>
                <SectionLabel icon={<ShowChartIcon />} label="Technical Indicators" accent="#BF5AF2" />
                <Box sx={{ background: "rgba(7,4,26,0.5)", border: "1px solid rgba(191,90,242,0.15)", borderRadius: "12px", p: 2 }}>
                  <DashboardTAPanel series={indicatorSeries} ticker={selected} />
                </Box>
              </Box>

              {/* Reddit Sentiment */}
              <Box>
                <SectionLabel icon={<ElectricBoltIcon />} label="Reddit Sentiment" accent="#EC4899" />
                <Box sx={{ background: "rgba(7,4,26,0.5)", border: "1px solid rgba(236,72,153,0.15)", borderRadius: "12px", p: 2 }}>
                  <SentimentPanel ticker={selected} />
                </Box>
              </Box>
            </Box>
          )}
        </Box>
      </Collapse>
    </Container>
  );
}
