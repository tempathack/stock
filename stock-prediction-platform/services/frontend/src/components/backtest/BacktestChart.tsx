import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import type { BacktestDataPoint } from "@/api";
import { Typography } from "@mui/material";

interface BacktestChartProps {
  series: BacktestDataPoint[];
  ticker: string;
}

export default function BacktestChart({ series, ticker }: BacktestChartProps) {
  const chartData = useMemo(
    () =>
      series.map((pt) => ({
        ...pt,
        upper: Math.max(pt.actual_price, pt.predicted_price),
        lower: Math.min(pt.actual_price, pt.predicted_price),
      })),
    [series],
  );

  const formatDate = (val: string) => {
    const d = new Date(val);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <>
      <Typography variant="subtitle2" gutterBottom>
        Actual vs Predicted — {ticker}
      </Typography>
      <ResponsiveContainer width="100%" height={380}>
        <ComposedChart
          data={chartData}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fill: "#a0a0a0", fontSize: 10 }}
            axisLine={{ stroke: "#2a2a4a" }}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "#a0a0a0", fontSize: 10 }}
            axisLine={{ stroke: "#2a2a4a" }}
            label={{
              value: "Price ($)",
              angle: -90,
              position: "insideLeft",
              fill: "#a0a0a0",
            }}
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
              String(name),
            ]}
            labelFormatter={(label) =>
              new Date(String(label)).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })
            }
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#a0a0a0" }} />

          {/* Error band */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#e94560"
            fillOpacity={0.1}
            isAnimationActive={false}
            legendType="none"
            tooltipType="none"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#0a1929"
            fillOpacity={1}
            isAnimationActive={false}
            legendType="none"
            tooltipType="none"
          />

          {/* Actual line */}
          <Line
            type="monotone"
            dataKey="actual_price"
            stroke="#00d4aa"
            strokeWidth={2}
            dot={false}
            name="Actual"
            isAnimationActive={false}
          />
          {/* Predicted line (dashed) */}
          <Line
            type="monotone"
            dataKey="predicted_price"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Predicted"
            strokeDasharray="6 3"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </>
  );
}
