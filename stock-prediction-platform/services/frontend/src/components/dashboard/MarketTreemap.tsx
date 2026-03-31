import { useMemo, useCallback, useState, useEffect } from "react";
import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import { Box, Paper, Stack, Typography } from "@mui/material";
import type { TreemapSectorGroup } from "@/api";
import { changePctToColor } from "@/utils/dashboardUtils";
import MobileMarketList from "./MobileMarketList";

interface MarketTreemapProps {
  data: TreemapSectorGroup[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
  height?: number;
}

/* Custom tooltip */
function TreemapTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Record<string, unknown> }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as Record<string, unknown> | undefined;
  if (!d) return null;
  const ticker = d.ticker as string | undefined;
  if (!ticker) return null;

  const name      = d.name as string;
  const sector    = d.sector as string;
  const lastClose = d.lastClose as number;
  const pct       = d.dailyChangePct as number;
  const isPos    = pct >= 0;
  const pctColor = isPos ? "#22c983" : "#e05454";

  return (
    <Box
      sx={{
        bgcolor: "#0A1120",
        border: `1px solid ${isPos ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
        borderRadius: "8px",
        px: 1.75,
        py: 1.25,
        boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
        backdropFilter: "blur(12px)",
      }}
    >
      <Typography
        sx={{
          fontFamily: '"IBM Plex Sans", sans-serif',
          fontWeight: 700,
          fontSize: "0.95rem",
          color: "#E2E8F0",
          letterSpacing: "0.04em",
        }}
      >
        {ticker}
      </Typography>
      <Typography
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: "0.65rem",
          color: "rgba(100,116,139,0.9)",
          mb: 0.75,
          maxWidth: 200,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {name} · {sector}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1 }}>
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.88rem",
            fontWeight: 500,
            color: "#E2E8F0",
          }}
        >
          ${lastClose.toFixed(2)}
        </Typography>
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.8rem",
            fontWeight: 600,
            color: pctColor,
          }}
        >
          {isPos ? "+" : ""}{pct.toFixed(2)}%
        </Typography>
      </Box>
    </Box>
  );
}

/* Treemap cell renderer */
function TreemapContent(props: Record<string, unknown>) {
  const {
    x, y, width, height,
    ticker, name, dailyChangePct,
    depth, selectedTicker, onSelectTicker,
  } = props as {
    x: number; y: number; width: number; height: number;
    ticker?: string; name?: string; dailyChangePct?: number;
    depth: number;
    selectedTicker: string | null;
    onSelectTicker: (t: string) => void;
  };

  if (depth === 0) return null;

  /* ── depth=1: sector group border + label ── */
  if (depth === 1) {
    const sectorLabel = (name ?? "").toUpperCase();
    return (
      <g pointerEvents="none">
        {/* Hard sector border */}
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill="rgba(0,0,0,0.45)"
          stroke="#050A14"
          strokeWidth={2}
        />
        {/* Sector name label strip */}
        <rect
          x={x}
          y={y}
          width={width}
          height={16}
          fill="rgba(0,0,0,0.55)"
        />
        <text
          x={x + 4}
          y={y + 10}
          fill="white"
          fontSize={9}
          fontWeight="bold"
          fontFamily="IBM Plex Sans, sans-serif"
          dominantBaseline="middle"
        >
          {sectorLabel}
        </text>
      </g>
    );
  }

  /* ── depth=2: individual stock tile ── */
  if (depth !== 2 || !ticker) return null;

  const pct        = dailyChangePct ?? 0;
  const fill       = changePctToColor(pct);
  const isSelected = selectedTicker === ticker;
  const isPos      = pct >= 0;

  const pad    = 4;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;

  const tickerFontSize = Math.min(18, Math.max(9, innerW / 3.5));
  const pctFontSize    = tickerFontSize * 0.75;

  return (
    <g
      onClick={() => onSelectTicker(ticker)}
      style={{ cursor: "pointer" }}
    >
      {/* Base fill */}
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fill}
        stroke={isSelected ? "#0EA5E9" : "rgba(5,10,20,0.6)"}
        strokeWidth={isSelected ? 2 : 0.75}
        rx={2}
      />

      {/* Bottom gradient shadow */}
      <rect
        x={x}
        y={y + height * 0.6}
        width={width}
        height={height * 0.4}
        fill="rgba(0,0,0,0.18)"
        pointerEvents="none"
      />

      {/* Selected glow border */}
      {isSelected && (
        <rect
          x={x + 1}
          y={y + 1}
          width={width - 2}
          height={height - 2}
          fill="none"
          stroke="rgba(14,165,233,0.6)"
          strokeWidth={2.5}
          rx={2}
          pointerEvents="none"
        />
      )}

      {/* Ticker symbol */}
      {innerW > 30 && innerH > 16 && (
        <text
          x={x + width / 2}
          y={y + height / 2 - (innerH > 40 ? pctFontSize / 2 + 2 : 0)}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#ffffff"
          fontSize={tickerFontSize}
          fontWeight="700"
          fontFamily="IBM Plex Sans, sans-serif"
          style={{ letterSpacing: "0.05em" }}
        >
          {ticker}
        </text>
      )}

      {/* Percentage */}
      {innerW > 40 && innerH > 30 && (
        <text
          x={x + width / 2}
          y={y + height / 2 + tickerFontSize / 2 + 3}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(255,255,255,0.95)"
          fontSize={pctFontSize}
          fontWeight="600"
          fontFamily="JetBrains Mono, monospace"
        >
          {isPos ? "+" : ""}{pct.toFixed(2)}%
        </text>
      )}

      {/* Company name — only when tall enough */}
      {innerH > 60 && innerW > 60 && name && (
        <text
          x={x + width / 2}
          y={y + height / 2 + tickerFontSize / 2 + pctFontSize + 6}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(255,255,255,0.50)"
          fontSize={7}
          fontFamily="JetBrains Mono, monospace"
        >
          {name.length > 20 ? name.slice(0, 18) + "…" : name}
        </text>
      )}
    </g>
  );
}

function useIsMobile(breakpoint = 640) {
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth < breakpoint : false,
  );
  useEffect(() => {
    const mql     = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    setIsMobile(mql.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);
  return isMobile;
}

export default function MarketTreemap({
  data,
  selectedTicker,
  onSelectTicker,
  height = 560,
}: MarketTreemapProps) {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <MobileMarketList
        data={data}
        selectedTicker={selectedTicker}
        onSelectTicker={onSelectTicker}
      />
    );
  }

  const treemapData = useMemo(
    () =>
      data.map((group) => ({
        name: group.name,
        children: group.children.map((child) => ({
          ...child,
          size: child.marketCap,
        })),
      })),
    [data],
  );

  const renderContent = useCallback(
    (props: Record<string, unknown>) => (
      <TreemapContent
        {...props}
        selectedTicker={selectedTicker}
        onSelectTicker={onSelectTicker}
      />
    ),
    [selectedTicker, onSelectTicker],
  );

  if (data.length === 0) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "1px dashed rgba(14,165,233,0.15)",
          borderRadius: "6px",
          p: 6,
        }}
      >
        <Typography sx={{ color: "rgba(100,116,139,0.5)", fontFamily: '"JetBrains Mono", monospace', fontSize: "0.8rem" }}>
          No market data available
        </Typography>
      </Box>
    );
  }

  return (
    <Paper
      elevation={0}
      sx={{ bgcolor: "#050A14", p: 1, border: "none", borderRadius: "4px" }}
    >
      {/* Header row */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 1, px: 0.5 }}
      >
        <Box>
          <Typography
            sx={{
              fontFamily: '"IBM Plex Sans", sans-serif',
              fontWeight: 700,
              fontSize: "0.72rem",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "#E2E8F0",
            }}
          >
            S&amp;P 500 Market Treemap
          </Typography>
          <Typography
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.65rem",
              color: "rgba(100,116,139,0.7)",
              mt: 0.25,
            }}
          >
            Click any cell to inspect stock details
          </Typography>
        </Box>
      </Stack>

      {/* Treemap */}
      <Box sx={{ borderRadius: "2px", overflow: "hidden" }}>
        <ResponsiveContainer width="100%" height={height}>
          <Treemap
            data={treemapData}
            dataKey="size"
            stroke="rgba(5,10,20,0.8)"
            content={renderContent}
            isAnimationActive={false}
          >
            <Tooltip content={<TreemapTooltipContent />} />
          </Treemap>
        </ResponsiveContainer>
      </Box>

      {/* Color legend */}
      <Box sx={{ mt: 1, px: 0.5 }}>
        <Box
          sx={{
            height: 7,
            borderRadius: "3px",
            background:
              "linear-gradient(to right, #EF4444 0%, #7f1d1d 20%, #1E2A3A 50%, #14532d 80%, #22C55E 100%)",
          }}
        />
        <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.4 }}>
          {["-3%", "-2%", "-1%", "0%", "+1%", "+2%", "+3%"].map((label) => (
            <Typography
              key={label}
              sx={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: "0.58rem",
                color: "rgba(100,116,139,0.65)",
              }}
            >
              {label}
            </Typography>
          ))}
        </Stack>
      </Box>
    </Paper>
  );
}
