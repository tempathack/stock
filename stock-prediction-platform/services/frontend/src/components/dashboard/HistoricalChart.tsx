import { useState, useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceDot,
} from "recharts";
import type { IndicatorValues, Timeframe } from "@/api";
import TimeframeSelector from "./TimeframeSelector";
import { Box, Paper, Stack, Typography } from "@mui/material";

interface HistoricalChartProps {
  series: IndicatorValues[];
  ticker: string;
  predictedPrice: number | null;
  predictedDate: string | null;
}

const TIMEFRAME_DAYS: Record<Timeframe, number> = {
  "1D": 1,
  "1W": 5,
  "1M": 21,
  "3M": 63,
  "1Y": 252,
};

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 12,
};

interface ChartPoint {
  date: string;
  close: number | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  forecast: number | null;
}

const fmtDate = (d: string) => {
  const dt = new Date(d);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

export default function HistoricalChart({
  series,
  ticker,
  predictedPrice,
  predictedDate,
}: HistoricalChartProps) {
  const [timeframe, setTimeframe] = useState<Timeframe>("3M");

  const data = useMemo<ChartPoint[]>(() => {
    const days = TIMEFRAME_DAYS[timeframe];
    const sliced = series.slice(-days);

    const hist: ChartPoint[] = sliced.map((s) => ({
      date: s.date ?? "",
      close: s.close,
      sma_20: s.sma_20,
      sma_50: s.sma_50,
      sma_200: s.sma_200,
      bb_upper: s.bb_upper,
      bb_lower: s.bb_lower,
      forecast: null,
    }));

    if (predictedPrice != null && predictedDate) {
      // Connect last close to forecast
      if (hist.length > 0) {
        const last = hist[hist.length - 1];
        if (last) last.forecast = last.close;
      }
      hist.push({
        date: predictedDate,
        close: null,
        sma_20: null,
        sma_50: null,
        sma_200: null,
        bb_upper: null,
        bb_lower: null,
        forecast: predictedPrice,
      });
    }

    return hist;
  }, [series, timeframe, predictedPrice, predictedDate]);

  if (series.length === 0) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", border: "2px dashed", borderColor: "divider", borderRadius: 1, p: 6 }}>
        <Typography color="text.secondary">No historical data available</Typography>
      </Box>
    );
  }

  const forecastIdx = data.length - 1;

  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="subtitle2">{ticker} — Historical</Typography>
        <TimeframeSelector value={timeframe} onChange={setTimeframe} />
      </Stack>
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart
          data={data}
          margin={{ left: 10, right: 20, top: 10, bottom: 5 }}
        >
          <defs>
            <linearGradient id="histCloseGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#e94560" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#e94560" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
          <XAxis
            dataKey="date"
            tickFormatter={fmtDate}
            tick={{ fill: "#a0a0a0", fontSize: 10 }}
            axisLine={{ stroke: "#2a2a4a" }}
          />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            tick={{ fill: "#a0a0a0", fontSize: 10 }}
            axisLine={{ stroke: "#2a2a4a" }}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(label) => fmtDate(String(label))}
            formatter={(value, name) => [
              `$${Number(value).toFixed(2)}`,
              String(name) === "forecast" ? "Forecast" : String(name),
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#a0a0a0" }}
          />

          {/* Bollinger Bands */}
          <Line
            type="monotone"
            dataKey="bb_upper"
            stroke="#a0a0a0"
            strokeDasharray="4 4"
            dot={false}
            strokeWidth={1}
            connectNulls={false}
            name="BB Upper"
          />
          <Line
            type="monotone"
            dataKey="bb_lower"
            stroke="#a0a0a0"
            strokeDasharray="4 4"
            dot={false}
            strokeWidth={1}
            connectNulls={false}
            name="BB Lower"
          />

          {/* SMA lines */}
          <Line
            type="monotone"
            dataKey="sma_20"
            stroke="#14b8a6"
            dot={false}
            strokeWidth={1.5}
            connectNulls={false}
            name="SMA 20"
          />
          <Line
            type="monotone"
            dataKey="sma_50"
            stroke="#f97316"
            dot={false}
            strokeWidth={1.5}
            connectNulls={false}
            name="SMA 50"
          />
          <Line
            type="monotone"
            dataKey="sma_200"
            stroke="#a855f7"
            dot={false}
            strokeWidth={1.5}
            connectNulls={false}
            name="SMA 200"
          />

          {/* Close price area */}
          <Area
            type="monotone"
            dataKey="close"
            fill="url(#histCloseGrad)"
            stroke="#e94560"
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            name="Close"
          />

          {/* Forecast line */}
          {predictedPrice != null && (
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#ffd700"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
              connectNulls
              name="forecast"
            />
          )}

          {/* Forecast dot */}
          {predictedPrice != null && data[forecastIdx] && (
            <ReferenceDot
              x={data[forecastIdx]!.date}
              y={predictedPrice}
              r={6}
              fill="#ffd700"
              stroke="#1a1a2e"
              strokeWidth={2}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </Paper>
  );
}
