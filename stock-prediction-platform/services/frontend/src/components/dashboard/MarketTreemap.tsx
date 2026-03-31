import { useMemo, useCallback, useState, useEffect } from "react";
import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import { Box, Stack, Typography } from "@mui/material";
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

  if (depth !== 2 || !ticker) return null;

  const pct        = dailyChangePct ?? 0;
  const fill       = changePctToColor(pct);
  const isSelected = selectedTicker === ticker;
  const isPos      = pct >= 0;

  // Inner padding for text
  const pad = 4;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;

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
        stroke={isSelected ? "#0EA5E9" : "rgba(5,10,20,0.8)"}
        strokeWidth={isSelected ? 2 : 1}
        rx={3}
      />

      {/* Top-edge highlight for depth */}
      <rect
        x={x + 1}
        y={y + 1}
        width={width - 2}
        height={Math.min(height * 0.3, 16)}
        fill="rgba(255,255,255,0.06)"
        rx={2}
        pointerEvents="none"
      />

      {/* Bottom gradient shadow */}
      <rect
        x={x}
        y={y + height * 0.6}
        width={width}
        height={height * 0.4}
        fill="rgba(0,0,0,0.22)"
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
          rx={3}
          pointerEvents="none"
        />
      )}

      {/* Ticker symbol */}
      {innerW > 30 && innerH > 16 && (
        <text
          x={x + width / 2}
          y={y + height / 2 - (innerH > 40 ? 8 : 0)}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#ffffff"
          fontSize={Math.min(13, Math.max(8, innerW / 5))}
          fontWeight="700"
          fontFamily="IBM Plex Sans, sans-serif"
          style={{ letterSpacing: "0.05em" }}
        >
          {ticker}
        </text>
      )}

      {/* Percentage */}
      {innerW > 44 && innerH > 32 && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 10}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(255,255,255,0.92)"
          fontSize={Math.min(11, Math.max(7, innerW / 7))}
          fontWeight="600"
          fontFamily="JetBrains Mono, monospace"
        >
          {isPos ? "+" : ""}{pct.toFixed(2)}%
        </text>
      )}

      {/* Company name */}
      {innerW > 80 && innerH > 52 && name && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 24}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(255,255,255,0.45)"
          fontSize={8}
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
    <>
      {/* Header row */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 2 }}
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

        <Stack direction="row" spacing={2} alignItems="center">
          {[
            { color: "#EF4444", label: "Loss" },
            { color: "#1E2A3A", label: "Flat" },
            { color: "#22C55E", label: "Gain" },
          ].map(({ color, label }) => (
            <Stack key={label} direction="row" spacing={0.6} alignItems="center">
              <Box
                sx={{
                  width: 9,
                  height: 9,
                  borderRadius: "2px",
                  bgcolor: color,
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              />
              <Typography
                sx={{
                  fontFamily: '"JetBrains Mono", monospace',
                  fontSize: "0.65rem",
                  color: "rgba(100,116,139,0.8)",
                  letterSpacing: "0.04em",
                }}
              >
                {label}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </Stack>

      <Box sx={{ borderRadius: "4px", overflow: "hidden" }}>
        <ResponsiveContainer width="100%" height={height}>
          <Treemap
            data={treemapData}
            dataKey="size"
            stroke="rgba(7,9,15,0.7)"
            content={renderContent}
            isAnimationActive={false}
          >
            <Tooltip content={<TreemapTooltipContent />} />
          </Treemap>
        </ResponsiveContainer>
      </Box>
    </>
  );
}
