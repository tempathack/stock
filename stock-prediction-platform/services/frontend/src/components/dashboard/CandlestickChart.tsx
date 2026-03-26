import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";
import type { CandlePoint, WebSocketPriceUpdate } from "@/api";
import { Box, Paper, Typography } from "@mui/material";

interface CandlestickChartProps {
  candles: CandlePoint[];
  ticker: string;
  livePrice?: WebSocketPriceUpdate | null;
}

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 12,
};

const GREEN = "#16a34a";
const RED = "#dc2626";

const fmtTime = (iso: string) => {
  const d = new Date(iso);
  return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
};

interface CandleBarData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  /* For Recharts Bar: [bottom, top] range */
  bodyRange: [number, number];
  isUp: boolean;
}

/* Custom SVG shape for a single candlestick */
function CandleShape(props: Record<string, unknown>) {
  const {
    x: rawX,
    y: rawY,
    width: rawWidth,
    height: rawHeight,
    payload,
  } = props as {
    x: number;
    y: number;
    width: number;
    height: number;
    payload: CandleBarData;
  };

  if (!payload) return null;

  const { high, low, open, close, isUp } = payload;
  const color = isUp ? GREEN : RED;

  /* Recharts positions the bar using bodyRange, so y + height covers
     the body. We just need to draw wicks extending to high/low.
     The y-axis scale can be recovered from the bar positioning. */

  const bodyTop = rawY;
  const bodyBottom = rawY + Math.max(rawHeight, 1);
  const bodyMid = rawX + rawWidth / 2;

  /* Scale factor: pixels per dollar.
     bodyRange covers |open - close|. If height is 0 the candle is a doji. */
  const bodyDollarSpan = Math.abs(open - close) || 0.01;
  const pxPerDollar = Math.max(rawHeight, 1) / bodyDollarSpan;

  const bodyHighPrice = Math.max(open, close);
  const wickTopPx = bodyTop - (high - bodyHighPrice) * pxPerDollar;
  const bodyLowPrice = Math.min(open, close);
  const wickBottomPx = bodyBottom + (bodyLowPrice - low) * pxPerDollar;

  return (
    <g>
      {/* Upper wick */}
      <line
        x1={bodyMid}
        y1={wickTopPx}
        x2={bodyMid}
        y2={bodyTop}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body */}
      <rect
        x={rawX}
        y={bodyTop}
        width={rawWidth}
        height={Math.max(rawHeight, 1)}
        fill={color}
        stroke={color}
        strokeWidth={0.5}
      />
      {/* Lower wick */}
      <line
        x1={bodyMid}
        y1={bodyBottom}
        x2={bodyMid}
        y2={wickBottomPx}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
}

export default function CandlestickChart({
  candles,
  ticker,
  livePrice,
}: CandlestickChartProps) {
  const chartData = useMemo<CandleBarData[]>(() => {
    const data = candles.map((c) => ({
      ...c,
      bodyRange: [
        Math.min(c.open, c.close),
        Math.max(c.open, c.close),
      ] as [number, number],
      isUp: c.close >= c.open,
    }));

    // Update last candle with live price
    if (livePrice && data.length > 0) {
      const idx = data.length - 1;
      const src = data[idx]!;
      const close = livePrice.price;
      const high = Math.max(src.high, close);
      const low = Math.min(src.low, close);
      data[idx] = {
        ...src,
        close,
        high,
        low,
        bodyRange: [Math.min(src.open, close), Math.max(src.open, close)],
        isUp: close >= src.open,
      };
    }

    return data;
  }, [candles, livePrice]);

  const yDomain = useMemo<[number, number]>(() => {
    if (chartData.length === 0) return [0, 1];
    const lows = chartData.map((c) => c.low);
    const highs = chartData.map((c) => c.high);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const pad = (max - min) * 0.05 || 1;
    return [min - pad, max + pad];
  }, [chartData]);

  const dateLabel = candles.length > 0 ? candles[0]?.date.split("T")[0] ?? "" : "";

  if (candles.length === 0) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", border: "2px dashed", borderColor: "divider", borderRadius: 1, p: 6 }}>
        <Typography color="text.secondary">No intraday data available</Typography>
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        {ticker} — Intraday
        {livePrice && (
          <Box
            component="span"
            sx={{
              ml: 1,
              display: "inline-block",
              width: 8,
              height: 8,
              borderRadius: "50%",
              bgcolor: "success.main",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
            title="Live data active"
          />
        )}
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1.5 }}>
        {dateLabel}
      </Typography>
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart
          data={chartData}
          margin={{ left: 10, right: 10, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
          <XAxis
            dataKey="date"
            tickFormatter={fmtTime}
            tick={{ fill: "#a0a0a0", fontSize: 10 }}
            axisLine={{ stroke: "#2a2a4a" }}
            minTickGap={40}
          />
          <YAxis
            domain={yDomain}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            tick={{ fill: "#a0a0a0", fontSize: 10 }}
            axisLine={{ stroke: "#2a2a4a" }}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(label) => fmtTime(String(label))}
            formatter={(value, name, entry) => {
              const p = (entry as { payload?: CandleBarData }).payload;
              if (!p || String(name) !== "bodyRange") return [String(value), String(name)];
              return [
                `O: $${p.open.toFixed(2)}  H: $${p.high.toFixed(2)}  L: $${p.low.toFixed(2)}  C: $${p.close.toFixed(2)}`,
                "OHLC",
              ];
            }}
          />
          <Bar
            dataKey="bodyRange"
            shape={<CandleShape />}
            isAnimationActive={false}
          >
            {chartData.map((entry) => (
              <Cell
                key={entry.date}
                fill={entry.isUp ? GREEN : RED}
              />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </Paper>
  );
}
