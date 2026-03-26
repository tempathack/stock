import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot,
} from "recharts";
import type { IndicatorValues } from "@/api";
import { Box, Paper, Typography } from "@mui/material";

interface StockDetailChartProps {
  ticker: string;
  series: IndicatorValues[];
  predictedPrice: number;
  predictedDate: string;
  currentPrice: number | null;
}

interface ChartPoint {
  date: string;
  close: number | null;
  sma_20: number | null;
  sma_50: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  forecast: number | null;
}

const fmtDate = (d: string) => {
  const dt = new Date(d);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

export default function StockDetailChart({
  ticker,
  series,
  predictedPrice,
  predictedDate,
  currentPrice,
}: StockDetailChartProps) {
  const data = useMemo<ChartPoint[]>(() => {
    const hist: ChartPoint[] = series.map((s) => ({
      date: s.date ?? "",
      close: s.close,
      sma_20: s.sma_20,
      sma_50: s.sma_50,
      bb_upper: s.bb_upper,
      bb_lower: s.bb_lower,
      forecast: null,
    }));

    // Add forecast point
    hist.push({
      date: predictedDate,
      close: null,
      sma_20: null,
      sma_50: null,
      bb_upper: null,
      bb_lower: null,
      forecast: predictedPrice,
    });

    // Connect the last historical close to the forecast
    if (hist.length >= 2) {
      const lastHist = hist[hist.length - 2];
      if (lastHist) {
        lastHist.forecast = lastHist.close;
      }
    }

    return hist;
  }, [series, predictedPrice, predictedDate]);

  const forecastIdx = data.length - 1;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
        {ticker} — Price History &amp; 7-Day Forecast
        {currentPrice != null && (
          <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
            Current: ${currentPrice.toFixed(2)}
          </Typography>
        )}
      </Typography>
      <Box>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart
            data={data}
            margin={{ left: 10, right: 20, top: 10, bottom: 5 }}
          >
            <defs>
              <linearGradient id="closeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e94560" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#e94560" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
            <XAxis
              dataKey="date"
              tickFormatter={fmtDate}
              tick={{ fill: "#a0a0a0", fontSize: 11 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <YAxis
              domain={["auto", "auto"]}
              tickFormatter={(v: number) => `$${v.toFixed(0)}`}
              tick={{ fill: "#a0a0a0", fontSize: 11 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f3460",
                border: "1px solid #2a2a4a",
                borderRadius: 6,
                color: "#e0e0e0",
                fontSize: 12,
              }}
              formatter={(value, name) => [
                `$${Number(value).toFixed(2)}`,
                name === "forecast" ? "Forecast" : String(name),
              ]}
              labelFormatter={(label) => fmtDate(String(label))}
            />

            {/* Bollinger Bands (dashed) */}
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
              stroke="#00d4aa"
              dot={false}
              strokeWidth={1}
              connectNulls={false}
              name="SMA 20"
            />
            <Line
              type="monotone"
              dataKey="sma_50"
              stroke="#ffa726"
              dot={false}
              strokeWidth={1}
              connectNulls={false}
              name="SMA 50"
            />

            {/* Close price area */}
            <Area
              type="monotone"
              dataKey="close"
              fill="url(#closeGrad)"
              stroke="#e94560"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              name="Close"
            />

            {/* Forecast line */}
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

            {/* Forecast dot */}
            <ReferenceDot
              x={data[forecastIdx]?.date ?? ""}
              y={predictedPrice}
              r={6}
              fill="#ffd700"
              stroke="#ffd700"
              label={{
                value: `$${predictedPrice.toFixed(2)}`,
                position: "top",
                fill: "#ffd700",
                fontSize: 11,
                fontWeight: 600,
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
}
