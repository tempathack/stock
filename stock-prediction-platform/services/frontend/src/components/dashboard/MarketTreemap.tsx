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

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 12,
};

/* Recharts Treemap custom content renderer */
function TreemapContent(props: Record<string, unknown>) {
  const {
    x,
    y,
    width,
    height,
    ticker,
    name,
    dailyChangePct,
    depth,
    selectedTicker,
    onSelectTicker,
  } = props as {
    x: number;
    y: number;
    width: number;
    height: number;
    ticker?: string;
    name?: string;
    dailyChangePct?: number;
    depth: number;
    selectedTicker: string | null;
    onSelectTicker: (t: string) => void;
  };

  // Only render leaf nodes (depth === 2 for nested data)
  if (depth !== 2 || !ticker) return null;

  const fill = changePctToColor(dailyChangePct ?? 0);
  const isSelected = selectedTicker === ticker;
  const changePct = dailyChangePct ?? 0;

  return (
    <g
      onClick={() => onSelectTicker(ticker)}
      style={{ cursor: "pointer" }}
    >
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fill}
        stroke={isSelected ? "#e94560" : "#1a1a2e"}
        strokeWidth={isSelected ? 2 : 0.5}
        rx={2}
      />
      {width > 40 && height > 20 && (
        <text
          x={x + width / 2}
          y={y + height / 2 - (width > 80 ? 6 : 0)}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#ffffff"
          fontSize={width > 80 ? 12 : 10}
          fontWeight="bold"
        >
          {ticker}
        </text>
      )}
      {width > 60 && height > 35 && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 10}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#ffffffcc"
          fontSize={10}
        >
          {changePct >= 0 ? "+" : ""}
          {changePct.toFixed(2)}%
        </text>
      )}
      {width > 100 && height > 50 && name && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 24}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#ffffff99"
          fontSize={9}
        >
          {name.length > 18 ? name.slice(0, 16) + "…" : name}
        </text>
      )}
    </g>
  );
}

/* Custom tooltip content */
function TreemapTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Record<string, unknown> }>;
}) {
  if (!active || !payload?.length) return null;
  const first = payload[0];
  if (!first) return null;
  const d = first.payload;
  const ticker = d.ticker as string | undefined;
  if (!ticker) return null;
  const name = d.name as string;
  const sector = d.sector as string;
  const lastClose = d.lastClose as number;
  const pct = d.dailyChangePct as number;

  return (
    <Box style={tooltipStyle} sx={{ px: 1.5, py: 1 }}>
      <Typography variant="body2" fontWeight={700}>
        {ticker} — {name}
      </Typography>
      <Typography variant="caption" sx={{ opacity: 0.8 }}>{sector}</Typography>
      <Typography variant="body2" sx={{ mt: 0.5 }}>
        ${lastClose.toFixed(2)}{" "}
        <Box component="span" sx={{ color: pct >= 0 ? "#16a34a" : "#dc2626" }}>
          ({pct >= 0 ? "+" : ""}
          {pct.toFixed(2)}%)
        </Box>
      </Typography>
    </Box>
  );
}

function useIsMobile(breakpoint = 640) {
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth < breakpoint : false,
  );
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
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
  height = 480,
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
  // Flatten sector groups into Recharts-compatible nested format
  const treemapData = useMemo(() => {
    return data.map((group) => ({
      name: group.name,
      children: group.children.map((child) => ({
        ...child,
        // Recharts uses "size" or a dataKey for sizing
        size: child.marketCap,
      })),
    }));
  }, [data]);

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
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", border: "2px dashed", borderColor: "divider", borderRadius: 1, p: 6 }}>
        <Typography color="text.secondary">No market data available</Typography>
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="subtitle2">S&amp;P 500 Market Treemap</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          {[{ color: "#dc2626", label: "Loss" }, { color: "#4b5563", label: "Flat" }, { color: "#16a34a", label: "Gain" }].map(({ color, label }) => (
            <Stack key={label} direction="row" spacing={0.5} alignItems="center">
              <Box sx={{ width: 10, height: 10, borderRadius: 0.5, bgcolor: color }} />
              <Typography variant="caption" color="text.secondary">{label}</Typography>
            </Stack>
          ))}
        </Stack>
      </Stack>
      <ResponsiveContainer width="100%" height={height}>
        <Treemap
          data={treemapData}
          dataKey="size"
          stroke="#1a1a2e"
          content={renderContent}
          isAnimationActive={false}
        >
          <Tooltip content={<TreemapTooltipContent />} />
        </Treemap>
      </ResponsiveContainer>
    </Paper>
  );
}
