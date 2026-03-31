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

/* ── Tooltip ───────────────────────────────────────────── */
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
  const isPos     = pct >= 0;
  const pctColor  = isPos ? "#00FF87" : "#FF2D78";
  const pctGlow   = isPos ? "rgba(0,255,135,0.6)" : "rgba(255,45,120,0.6)";

  return (
    <Box
      sx={{
        background: "rgba(13,10,36,0.95)",
        backdropFilter: "blur(20px)",
        border: `1px solid ${isPos ? "rgba(0,255,135,0.3)" : "rgba(255,45,120,0.3)"}`,
        borderRadius: "12px",
        px: 2,
        py: 1.5,
        boxShadow: `0 8px 32px rgba(0,0,0,0.7), 0 0 20px ${isPos ? "rgba(0,255,135,0.1)" : "rgba(255,45,120,0.1)"}`,
      }}
    >
      <Typography
        sx={{
          fontFamily: '"Inter", sans-serif',
          fontWeight: 800,
          fontSize: "1rem",
          color: "#F0EEFF",
          letterSpacing: "0.05em",
        }}
      >
        {ticker}
      </Typography>
      <Typography
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: "0.62rem",
          color: "rgba(107,96,168,0.9)",
          mb: 1,
          maxWidth: 200,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {name} · {sector}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.25 }}>
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.9rem",
            fontWeight: 600,
            color: "#F0EEFF",
          }}
        >
          ${lastClose.toFixed(2)}
        </Typography>
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.85rem",
            fontWeight: 700,
            color: pctColor,
            textShadow: `0 0 8px ${pctGlow}`,
          }}
        >
          {isPos ? "+" : ""}{pct.toFixed(2)}%
        </Typography>
      </Box>
    </Box>
  );
}

/* ── Cell renderer ─────────────────────────────────────── */
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

  /* depth=1: sector group */
  if (depth === 1) {
    return (
      <g pointerEvents="none">
        <rect
          x={x} y={y} width={width} height={height}
          fill="transparent"
          stroke="rgba(13,10,36,0.9)"
          strokeWidth={3}
        />
        {/* Sector label pill */}
        {width > 60 && (
          <>
            <rect
              x={x + 4} y={y + 4}
              width={Math.min(width - 8, (name?.length ?? 0) * 6.5 + 12)}
              height={16}
              fill="rgba(13,10,36,0.75)"
              rx={4}
            />
            <text
              x={x + 10}
              y={y + 13}
              fill="rgba(191,90,242,0.9)"
              fontSize={8}
              fontWeight="700"
              fontFamily="Inter, sans-serif"
              letterSpacing="0.08em"
            >
              {(name ?? "").toUpperCase()}
            </text>
          </>
        )}
      </g>
    );
  }

  /* depth=2: stock tile */
  if (depth !== 2 || !ticker) return null;

  const pct        = dailyChangePct ?? 0;
  const fill       = changePctToColor(pct);
  const isSelected = selectedTicker === ticker;
  const isPos      = pct >= 0;

  const pad    = 3;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;

  const tickerFontSize = Math.min(18, Math.max(9, innerW / 3.5));
  const pctFontSize    = tickerFontSize * 0.72;

  return (
    <g onClick={() => onSelectTicker(ticker)} style={{ cursor: "pointer" }}>
      <defs>
        <filter id="tile-text-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="0" stdDeviation="1.5" floodColor="rgba(0,0,0,0.9)" floodOpacity="1" />
        </filter>
      </defs>
      {/* Base tile */}
      <rect
        x={x} y={y} width={width} height={height}
        fill={fill}
        stroke="rgba(13,10,36,0.8)"
        strokeWidth={1}
        rx={3}
      />

      {/* Subtle top-edge shine */}
      <rect
        x={x + 1} y={y + 1} width={width - 2} height={2}
        fill="rgba(255,255,255,0.08)"
        rx={2}
        pointerEvents="none"
      />

      {/* Bottom gradient overlay for text contrast */}
      <rect
        x={x} y={y + height * 0.55}
        width={width} height={height * 0.45}
        fill="rgba(0,0,0,0.22)"
        pointerEvents="none"
      />

      {/* Selected: neon cyan border */}
      {isSelected && (
        <>
          <rect
            x={x + 1} y={y + 1}
            width={width - 2} height={height - 2}
            fill="rgba(0,245,255,0.06)"
            stroke="#00F5FF"
            strokeWidth={2}
            rx={3}
            pointerEvents="none"
          />
          {/* Glow filter approximation via extra strokes */}
          <rect
            x={x + 2} y={y + 2}
            width={width - 4} height={height - 4}
            fill="none"
            stroke="rgba(0,245,255,0.3)"
            strokeWidth={1.5}
            rx={2}
            pointerEvents="none"
          />
        </>
      )}

      {/* Ticker */}
      {innerW > 30 && innerH > 16 && (
        <text
          x={x + width / 2}
          y={y + height / 2 - (innerH > 38 ? pctFontSize / 2 + 2 : 0)}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#FFFFFF"
          fontSize={tickerFontSize}
          fontWeight="800"
          fontFamily="Inter, sans-serif"
          filter="url(#tile-text-shadow)"
          style={{ letterSpacing: "0.04em" }}
        >
          {ticker}
        </text>
      )}

      {/* Pct change */}
      {innerW > 38 && innerH > 28 && (
        <text
          x={x + width / 2}
          y={y + height / 2 + tickerFontSize / 2 + 4}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#FFFFFF"
          fontSize={pctFontSize}
          fontWeight="700"
          fontFamily="JetBrains Mono, monospace"
          filter="url(#tile-text-shadow)"
        >
          {isPos ? "+" : ""}{pct.toFixed(2)}%
        </text>
      )}

      {/* Company name */}
      {innerH > 62 && innerW > 60 && name && (
        <text
          x={x + width / 2}
          y={y + height / 2 + tickerFontSize / 2 + pctFontSize + 7}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(191,90,242,0.8)"
          fontSize={7}
          fontFamily="Inter, sans-serif"
          filter="url(#tile-text-shadow)"
          style={{ letterSpacing: "0.03em" }}
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
          border: "1px dashed rgba(124,58,237,0.2)",
          borderRadius: "12px",
          p: 6,
        }}
      >
        <Typography sx={{ color: "rgba(107,96,168,0.5)", fontFamily: '"JetBrains Mono", monospace', fontSize: "0.8rem" }}>
          No market data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        background: "rgba(13,10,36,0.55)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(124,58,237,0.22)",
        borderRadius: "18px",
        p: 2,
        transition: "border-color 0.3s ease",
        "&:hover": { borderColor: "rgba(0,245,255,0.25)" },
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 1.5, px: 0.5 }}
      >
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 3,
                height: 18,
                borderRadius: "2px",
                background: "linear-gradient(180deg, #7C3AED, #00F5FF)",
                boxShadow: "0 0 8px rgba(124,58,237,0.7)",
                flexShrink: 0,
              }}
            />
            <Typography
              sx={{
                fontFamily: '"Inter", sans-serif',
                fontWeight: 800,
                fontSize: "0.85rem",
                letterSpacing: "-0.01em",
                background: "linear-gradient(90deg, #F0EEFF, #BF5AF2)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              S&amp;P 500 Market Treemap
            </Typography>
          </Box>
          <Typography
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.62rem",
              color: "rgba(107,96,168,0.65)",
              mt: 0.3,
              pl: "19px",
              letterSpacing: "0.02em",
            }}
          >
            Click any cell to inspect stock details
          </Typography>
        </Box>

        {/* Legend chips */}
        <Stack direction="row" spacing={1} alignItems="center">
          {[
            { label: "Loss", color: "#FF2D78", bg: "rgba(255,45,120,0.12)" },
            { label: "Flat", color: "rgba(191,90,242,0.6)", bg: "rgba(191,90,242,0.08)" },
            { label: "Gain", color: "#00FF87", bg: "rgba(0,255,135,0.12)" },
          ].map(({ label, color, bg }) => (
            <Box
              key={label}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.5,
                px: 1,
                py: 0.35,
                borderRadius: "6px",
                background: bg,
                border: `1px solid ${color}30`,
              }}
            >
              <Box sx={{ width: 6, height: 6, borderRadius: "50%", bgcolor: color, boxShadow: `0 0 4px ${color}` }} />
              <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.58rem", color, fontWeight: 600 }}>
                {label}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Stack>

      {/* Treemap */}
      <Box sx={{ borderRadius: "12px", overflow: "hidden" }}>
        <ResponsiveContainer width="100%" height={height}>
          <Treemap
            data={treemapData}
            dataKey="size"
            stroke="rgba(13,10,36,0.8)"
            content={renderContent}
            isAnimationActive={false}
          >
            <Tooltip content={<TreemapTooltipContent />} />
          </Treemap>
        </ResponsiveContainer>
      </Box>

      {/* Color scale bar */}
      <Box sx={{ mt: 1.5, px: 0.5 }}>
        <Box
          sx={{
            height: 5,
            borderRadius: "3px",
            background: "linear-gradient(to right, #CC1F5A 0%, #6B2040 25%, #110C2E 50%, #0A5C35 75%, #00CC6E 100%)",
            boxShadow: "0 0 12px rgba(0,0,0,0.4)",
          }}
        />
        <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
          {["-3%", "-2%", "-1%", "0%", "+1%", "+2%", "+3%"].map((label) => (
            <Typography
              key={label}
              sx={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: "0.55rem",
                color: "rgba(107,96,168,0.55)",
              }}
            >
              {label}
            </Typography>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
