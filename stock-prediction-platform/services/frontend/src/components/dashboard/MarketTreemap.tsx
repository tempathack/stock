import { useMemo, useCallback } from "react";
import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import type { TreemapSectorGroup } from "@/api";
import { changePctToColor } from "@/utils/dashboardUtils";

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
    <div style={tooltipStyle} className="px-3 py-2">
      <p className="font-bold">
        {ticker} — {name}
      </p>
      <p className="text-xs opacity-80">{sector}</p>
      <p className="mt-1">
        ${lastClose.toFixed(2)}{" "}
        <span style={{ color: pct >= 0 ? "#16a34a" : "#dc2626" }}>
          ({pct >= 0 ? "+" : ""}
          {pct.toFixed(2)}%)
        </span>
      </p>
    </div>
  );
}

export default function MarketTreemap({
  data,
  selectedTicker,
  onSelectTicker,
  height = 480,
}: MarketTreemapProps) {
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
      <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-border bg-bg-surface p-12">
        <p className="text-text-secondary">No market data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">
          S&amp;P 500 Market Treemap
        </h3>
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span className="flex items-center gap-1">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: "#dc2626" }}
            />
            Loss
          </span>
          <span className="flex items-center gap-1">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: "#4b5563" }}
            />
            Flat
          </span>
          <span className="flex items-center gap-1">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: "#16a34a" }}
            />
            Gain
          </span>
        </div>
      </div>
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
    </div>
  );
}
