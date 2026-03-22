import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  AreaChart,
  Line,
  Bar,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import type { IndicatorValues } from "@/api";

interface IndicatorOverlayChartsProps {
  series: IndicatorValues[];
}

const fmtDate = (d: string) => {
  const dt = new Date(d);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 12,
};

interface MacdPoint {
  date: string;
  macd_line: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  histColor: string;
}

export default function IndicatorOverlayCharts({
  series,
}: IndicatorOverlayChartsProps) {
  const rsiData = useMemo(
    () =>
      series
        .filter((s) => s.date != null && s.rsi_14 != null)
        .map((s) => ({ date: s.date!, rsi_14: s.rsi_14! })),
    [series],
  );

  const macdData = useMemo<MacdPoint[]>(
    () =>
      series
        .filter((s) => s.date != null)
        .map((s) => ({
          date: s.date!,
          macd_line: s.macd_line,
          macd_signal: s.macd_signal,
          macd_histogram: s.macd_histogram,
          histColor:
            s.macd_histogram != null && s.macd_histogram >= 0
              ? "#00d4aa"
              : "#e94560",
        })),
    [series],
  );

  const bbWidthData = useMemo(
    () =>
      series
        .filter(
          (s) =>
            s.date != null && s.bb_upper != null && s.bb_lower != null,
        )
        .map((s) => ({
          date: s.date!,
          bb_width: Math.round((s.bb_upper! - s.bb_lower!) * 100) / 100,
        })),
    [series],
  );

  return (
    <div className="space-y-4">
      {/* RSI Chart */}
      <div className="rounded-lg border border-border bg-bg-surface p-4">
        <h4 className="mb-2 text-xs font-medium text-text-primary">
          RSI (14)
        </h4>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart
            data={rsiData}
            margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
            <XAxis
              dataKey="date"
              tickFormatter={fmtDate}
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <YAxis
              domain={[0, 100]}
              ticks={[0, 30, 50, 70, 100]}
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelFormatter={(label) => fmtDate(String(label))}
              formatter={(v) => [Number(v).toFixed(1), "RSI"]}
            />
            <ReferenceArea
              y1={30}
              y2={70}
              fill="#e94560"
              fillOpacity={0.04}
            />
            <ReferenceLine
              y={70}
              stroke="#e94560"
              strokeDasharray="4 4"
              strokeWidth={1}
            />
            <ReferenceLine
              y={30}
              stroke="#00d4aa"
              strokeDasharray="4 4"
              strokeWidth={1}
            />
            <Line
              type="monotone"
              dataKey="rsi_14"
              stroke="#e94560"
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* MACD Chart */}
      <div className="rounded-lg border border-border bg-bg-surface p-4">
        <h4 className="mb-2 text-xs font-medium text-text-primary">
          MACD (12/26/9)
        </h4>
        <ResponsiveContainer width="100%" height={180}>
          <ComposedChart
            data={macdData}
            margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
            <XAxis
              dataKey="date"
              tickFormatter={fmtDate}
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <YAxis
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelFormatter={(label) => fmtDate(String(label))}
              formatter={(v, name) => [
                Number(v).toFixed(3),
                name === "macd_histogram"
                  ? "Histogram"
                  : name === "macd_line"
                    ? "MACD"
                    : "Signal",
              ]}
            />
            <ReferenceLine y={0} stroke="#a0a0a0" strokeWidth={0.5} />
            <Bar
              dataKey="macd_histogram"
              name="macd_histogram"
              fill="#00d4aa"
              opacity={0.6}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="macd_line"
              stroke="#e94560"
              strokeWidth={1.5}
              dot={false}
              name="macd_line"
            />
            <Line
              type="monotone"
              dataKey="macd_signal"
              stroke="#a0a0a0"
              strokeDasharray="4 4"
              strokeWidth={1}
              dot={false}
              name="macd_signal"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Bollinger Band Width */}
      <div className="rounded-lg border border-border bg-bg-surface p-4">
        <h4 className="mb-2 text-xs font-medium text-text-primary">
          Bollinger Band Width
        </h4>
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart
            data={bbWidthData}
            margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
          >
            <defs>
              <linearGradient id="bbWidthGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e94560" stopOpacity={0.2} />
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
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
              tickFormatter={(v: number) => `$${v.toFixed(1)}`}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelFormatter={(label) => fmtDate(String(label))}
              formatter={(v) => [`$${Number(v).toFixed(2)}`, "BB Width"]}
            />
            <Area
              type="monotone"
              dataKey="bb_width"
              fill="url(#bbWidthGrad)"
              stroke="#e94560"
              strokeWidth={1.5}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
