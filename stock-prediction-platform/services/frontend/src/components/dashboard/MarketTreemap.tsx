import { useMemo, useCallback, useState, useEffect } from "react";
import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import { Box, Chip, Stack, Typography } from "@mui/material";
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
  const pctColor  = isPos ? "#00E5FF" : "#BF5AF2";
  const pctGlow   = isPos ? "rgba(0,229,255,0.6)" : "rgba(191,90,242,0.6)";

  return (
    <Box
      sx={{
        background: "rgba(13,10,36,0.96)",
        backdropFilter: "blur(20px)",
        border: `1px solid ${isPos ? "rgba(0,229,255,0.3)" : "rgba(191,90,242,0.3)"}`,
        borderRadius: "12px",
        px: 2,
        py: 1.5,
        boxShadow: `0 8px 32px rgba(0,0,0,0.7), 0 0 20px ${isPos ? "rgba(0,229,255,0.1)" : "rgba(191,90,242,0.1)"}`,
      }}
    >
      <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 800, fontSize: "1rem", color: "#F0EEFF", letterSpacing: "0.05em" }}>
        {ticker}
      </Typography>
      <Typography sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.62rem", color: "rgba(107,96,168,0.9)", mb: 1, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {name} · {sector}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.25 }}>
        <Typography sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.9rem", fontWeight: 600, color: "#F0EEFF" }}>
          ${lastClose.toFixed(2)}
        </Typography>
        <Typography sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.85rem", fontWeight: 700, color: pctColor, textShadow: `0 0 8px ${pctGlow}` }}>
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
        <rect x={x} y={y} width={width} height={height} fill="transparent" stroke="rgba(13,10,36,0.9)" strokeWidth={3} />
        {width > 60 && (
          <>
            <rect x={x + 4} y={y + 4} width={Math.min(width - 8, (name?.length ?? 0) * 6.5 + 12)} height={16} fill="rgba(13,10,36,0.75)" rx={4} />
            <text x={x + 10} y={y + 13} fill="rgba(191,90,242,0.9)" fontSize={8} fontWeight="700" fontFamily="Inter, sans-serif" letterSpacing="0.08em">
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
        <filter id="tile-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="0" stdDeviation="1.5" floodColor="rgba(0,0,0,0.9)" floodOpacity="1" />
        </filter>
      </defs>

      <rect x={x} y={y} width={width} height={height} fill={fill} stroke="rgba(13,10,36,0.8)" strokeWidth={1} rx={3} />
      <rect x={x + 1} y={y + 1} width={width - 2} height={2} fill="rgba(255,255,255,0.07)" rx={2} pointerEvents="none" />
      <rect x={x} y={y + height * 0.55} width={width} height={height * 0.45} fill="rgba(0,0,0,0.2)" pointerEvents="none" />

      {isSelected && (
        <>
          <rect x={x + 1} y={y + 1} width={width - 2} height={height - 2} fill="rgba(0,245,255,0.06)" stroke="#00F5FF" strokeWidth={2} rx={3} pointerEvents="none" />
          <rect x={x + 2} y={y + 2} width={width - 4} height={height - 4} fill="none" stroke="rgba(0,245,255,0.3)" strokeWidth={1.5} rx={2} pointerEvents="none" />
        </>
      )}

      {innerW > 30 && innerH > 16 && (
        <text x={x + width / 2} y={y + height / 2 - (innerH > 38 ? pctFontSize / 2 + 2 : 0)}
          textAnchor="middle" dominantBaseline="central"
          fill="rgba(255,255,255,0.95)" fontSize={tickerFontSize} fontWeight="700"
          fontFamily="Inter, sans-serif" filter="url(#tile-shadow)"
          style={{ letterSpacing: "0.06em" }}>
          {ticker}
        </text>
      )}

      {innerW > 38 && innerH > 28 && (
        <text x={x + width / 2} y={y + height / 2 + tickerFontSize / 2 + 4}
          textAnchor="middle" dominantBaseline="central"
          fill="rgba(255,255,255,0.72)" fontSize={pctFontSize} fontWeight="500"
          fontFamily="Inter, sans-serif" filter="url(#tile-shadow)"
          style={{ letterSpacing: "0.02em" }}>
          {isPos ? "+" : ""}{pct.toFixed(2)}%
        </text>
      )}

      {innerH > 62 && innerW > 60 && name && (
        <text x={x + width / 2} y={y + height / 2 + tickerFontSize / 2 + pctFontSize + 7}
          textAnchor="middle" dominantBaseline="central"
          fill="rgba(200,180,255,0.6)" fontSize={7}
          fontFamily="Inter, sans-serif" filter="url(#tile-shadow)"
          style={{ letterSpacing: "0.04em" }}>
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
      <MobileMarketList data={data} selectedTicker={selectedTicker} onSelectTicker={onSelectTicker} />
    );
  }

  const treemapData = useMemo(
    () => data.map((group) => ({
      name: group.name,
      children: group.children.map((child) => ({ ...child, size: child.marketCap })),
    })),
    [data],
  );

  const renderContent = useCallback(
    (props: Record<string, unknown>) => (
      <TreemapContent {...props} selectedTicker={selectedTicker} onSelectTicker={onSelectTicker} />
    ),
    [selectedTicker, onSelectTicker],
  );

  const gainers = data.flatMap((g) => g.children).filter((s) => s.dailyChangePct > 0).length;
  const losers  = data.flatMap((g) => g.children).filter((s) => s.dailyChangePct < 0).length;

  if (data.length === 0) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", border: "1px dashed rgba(124,58,237,0.2)", borderRadius: "12px", p: 6 }}>
        <Typography sx={{ color: "rgba(107,96,168,0.5)", fontFamily: '"Inter", sans-serif', fontSize: "0.8rem" }}>
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
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5, px: 0.5 }}>
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box sx={{ width: 3, height: 18, borderRadius: "2px", background: "linear-gradient(180deg, #7C3AED, #00F5FF)", boxShadow: "0 0 8px rgba(124,58,237,0.7)", flexShrink: 0 }} />
            <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 800, fontSize: "0.85rem", letterSpacing: "-0.01em", background: "linear-gradient(90deg, #F0EEFF, #BF5AF2)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
              S&amp;P 500 Market Treemap
            </Typography>
          </Box>
          <Typography sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.62rem", color: "rgba(107,96,168,0.65)", mt: 0.3, pl: "19px" }}>
            Click any cell to inspect stock details
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} alignItems="center">
          <Chip label={`${gainers} Gainers`} size="small" sx={{ bgcolor: "rgba(0,194,212,0.12)", color: "#00C2D4", border: "1px solid rgba(0,194,212,0.25)", fontFamily: '"Inter", sans-serif', fontSize: "0.65rem", height: 22 }} />
          <Chip label={`${losers} Losers`} size="small" sx={{ bgcolor: "rgba(139,47,201,0.12)", color: "#BF5AF2", border: "1px solid rgba(139,47,201,0.25)", fontFamily: '"Inter", sans-serif', fontSize: "0.65rem", height: 22 }} />
        </Stack>
      </Stack>

      {/* Treemap */}
      <Box sx={{ borderRadius: "12px", overflow: "hidden" }}>
        <ResponsiveContainer width="100%" height={height}>
          <Treemap data={treemapData} dataKey="size" stroke="rgba(13,10,36,0.8)" content={renderContent} isAnimationActive={false}>
            <Tooltip content={<TreemapTooltipContent />} />
          </Treemap>
        </ResponsiveContainer>
      </Box>

      {/* Colour scale bar */}
      <Box sx={{ mt: 1.5, px: 0.5 }}>
        <Box sx={{ height: 5, borderRadius: "3px", background: "linear-gradient(to right, #8B2FC9 0%, #3D1A6B 25%, #110C2E 50%, #0A3040 75%, #00C2D4 100%)", boxShadow: "0 0 12px rgba(0,0,0,0.4)" }} />
        <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
          {["-3%", "-2%", "-1%", "0%", "+1%", "+2%", "+3%"].map((label) => (
            <Typography key={label} sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.55rem", color: "rgba(107,96,168,0.55)" }}>
              {label}
            </Typography>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
