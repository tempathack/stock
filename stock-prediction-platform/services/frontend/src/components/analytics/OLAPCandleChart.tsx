import { useMemo, useState } from "react";
import BarChartIcon from "@mui/icons-material/BarChart";
import {
  Alert,
  Autocomplete,
  Box,
  CircularProgress,
  Paper,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CandlePoint } from "../../api/types";
import { useAnalyticsCandles, useMarketOverview } from "../../api/queries";
import PlaceholderCard from "../ui/PlaceholderCard";

// Only 1h and 1d supported (Phase 64 created these aggregates; 5m/4h do not exist)
type Interval = "1h" | "1d";

const GREEN = "#16a34a";
const RED = "#dc2626";

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 12,
};

interface CandleBarData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  bodyRange: [number, number];
  isUp: boolean;
}

// Custom SVG shape — replicates the CandlestickChart pattern
function CandleShape(props: Record<string, unknown>) {
  const { x: rawX, y: rawY, width: rawWidth, height: rawHeight, payload } = props as {
    x: number;
    y: number;
    width: number;
    height: number;
    payload: CandleBarData;
  };

  if (!payload) return null;

  const { high, low, open, close, isUp } = payload;
  const color = isUp ? GREEN : RED;

  const bodyTop = rawY;
  const bodyBottom = rawY + Math.max(rawHeight, 1);
  const bodyMid = rawX + rawWidth / 2;

  const bodyDollarSpan = Math.abs(open - close) || 0.01;
  const pxPerDollar = Math.max(rawHeight, 1) / bodyDollarSpan;

  const bodyHighPrice = Math.max(open, close);
  const wickTopPx = bodyTop - (high - bodyHighPrice) * pxPerDollar;
  const bodyLowPrice = Math.min(open, close);
  const wickBottomPx = bodyBottom + (bodyLowPrice - low) * pxPerDollar;

  return (
    <g>
      <line x1={bodyMid} y1={wickTopPx} x2={bodyMid} y2={bodyTop} stroke={color} strokeWidth={1} />
      <rect
        x={rawX}
        y={bodyTop}
        width={rawWidth}
        height={Math.max(rawHeight, 1)}
        fill={color}
        stroke={color}
        strokeWidth={0.5}
      />
      <line x1={bodyMid} y1={bodyBottom} x2={bodyMid} y2={wickBottomPx} stroke={color} strokeWidth={1} />
    </g>
  );
}

export default function OLAPCandleChart() {
  const [interval, setInterval] = useState<Interval>("1h");
  const [ticker, setTicker] = useState("AAPL");
  const marketQuery = useMarketOverview();
  const tickers = useMemo(() => {
    if (!marketQuery.data?.stocks?.length) return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"];
    return marketQuery.data.stocks.map((s) => s.ticker).sort();
  }, [marketQuery.data]);
  const { data, isLoading, isError } = useAnalyticsCandles(ticker, interval);

  const candles: CandlePoint[] = data?.candles ?? [];

  const chartData = useMemo<CandleBarData[]>(() => {
    return candles.map((c) => ({
      ...c,
      bodyRange: [
        Math.min(c.open, c.close),
        Math.max(c.open, c.close),
      ] as [number, number],
      isUp: c.close >= c.open,
    }));
  }, [candles]);

  const yDomain = useMemo<[number, number]>(() => {
    if (chartData.length === 0) return [0, 1];
    const lows = chartData.map((c) => c.low);
    const highs = chartData.map((c) => c.high);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const pad = (max - min) * 0.05 || 1;
    return [min - pad, max + pad];
  }, [chartData]);

  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Box sx={{ display: "flex", alignItems: "center", mb: 2, gap: 1 }}>
        <BarChartIcon sx={{ color: "primary.main", fontSize: 20 }} />
        <Typography variant="h6">OLAP Candle Chart</Typography>
        <Autocomplete
          options={tickers}
          value={ticker}
          onChange={(_, v) => v && setTicker(v)}
          size="small"
          disableClearable
          sx={{ width: 120, ml: 1 }}
          renderInput={(params) => <TextField {...params} label="Ticker" />}
        />
        <Box sx={{ ml: "auto", display: "flex", alignItems: "center", gap: 1 }}>
          {isLoading && <CircularProgress size={16} />}
          <ToggleButtonGroup
            exclusive
            size="small"
            value={interval}
            onChange={(_, v) => v && setInterval(v)}
            aria-label="Candle interval"
          >
            <ToggleButton value="1h">1H</ToggleButton>
            <ToggleButton value="1d">1D</ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Box>

      {isError && (
        <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
          Candle data endpoint returned an error — retrying.
        </Alert>
      )}

      {!isLoading && candles.length === 0 ? (
        <PlaceholderCard title="No candle data available" phase={69} />
      ) : (
        <Box
          role="img"
          aria-label={`OLAP candle chart for ${ticker} at ${interval} interval`}
          sx={{ height: 280 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono", monospace' }}
                tickLine={false}
                minTickGap={40}
              />
              <YAxis
                domain={yDomain}
                tickFormatter={(v: number) => `$${v.toFixed(0)}`}
                tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono", monospace' }}
                tickLine={false}
                width={52}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value, name, entry) => {
                  const p = (entry as { payload?: CandleBarData }).payload;
                  if (!p || String(name) !== "bodyRange") return [String(value), String(name)];
                  return [
                    `O: $${p.open.toFixed(2)}  H: $${p.high.toFixed(2)}  L: $${p.low.toFixed(2)}  C: $${p.close.toFixed(2)}`,
                    "OHLC",
                  ];
                }}
              />
              <Bar dataKey="bodyRange" shape={<CandleShape />} isAnimationActive={false}>
                {chartData.map((entry) => (
                  <Cell key={entry.date} fill={entry.isUp ? GREEN : RED} />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Paper>
  );
}
