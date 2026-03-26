import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  BarChart,
  Line,
  Bar,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ReferenceArea,
  Legend,
} from "recharts";
import type { IndicatorValues } from "@/api";
import { Box, Paper, Stack, Typography } from "@mui/material";

interface DashboardTAPanelProps {
  series: IndicatorValues[];
  ticker: string;
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

const axisProps = {
  tick: { fill: "#a0a0a0", fontSize: 10 } as const,
  axisLine: { stroke: "#2a2a4a" },
};

const gridStroke = "#2a2a4a";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Paper sx={{ p: 1.5 }}>
      <Typography variant="caption" fontWeight={600} color="text.secondary" display="block" sx={{ mb: 1 }}>
        {title}
      </Typography>
      {children}
    </Paper>
  );
}

// -- Sub-chart: RSI --
function RsiChart({ series }: { series: IndicatorValues[] }) {
  const data = useMemo(
    () =>
      series
        .filter((s) => s.date != null && s.rsi_14 != null)
        .map((s) => ({ date: s.date!, rsi_14: s.rsi_14! })),
    [series],
  );

  return (
    <Section title="RSI (14)">
      <ResponsiveContainer width="100%" height={160}>
        <LineChart
          data={data}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tickFormatter={fmtDate} {...axisProps} />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 30, 50, 70, 100]}
            {...axisProps}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(l) => fmtDate(String(l))}
            formatter={(v) => [Number(v).toFixed(1), "RSI"]}
          />
          <ReferenceArea y1={30} y2={70} fill="#e94560" fillOpacity={0.05} />
          <ReferenceLine
            y={70}
            stroke="#dc2626"
            strokeDasharray="4 4"
            strokeWidth={1}
          />
          <ReferenceLine
            y={30}
            stroke="#16a34a"
            strokeDasharray="4 4"
            strokeWidth={1}
          />
          <Line
            type="monotone"
            dataKey="rsi_14"
            stroke="#e94560"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Section>
  );
}

// -- Sub-chart: MACD --
interface MacdPoint {
  date: string;
  macd_line: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  histColor: string;
}

function MacdChart({ series }: { series: IndicatorValues[] }) {
  const data = useMemo<MacdPoint[]>(
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
              ? "#16a34a"
              : "#dc2626",
        })),
    [series],
  );

  return (
    <Section title="MACD (12 / 26 / 9)">
      <ResponsiveContainer width="100%" height={160}>
        <ComposedChart
          data={data}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tickFormatter={fmtDate} {...axisProps} />
          <YAxis {...axisProps} />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(l) => fmtDate(String(l))}
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
            fill="#16a34a"
            opacity={0.6}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="macd_line"
            stroke="#3b82f6"
            strokeWidth={1.5}
            dot={false}
            name="macd_line"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="macd_signal"
            stroke="#f97316"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            dot={false}
            name="macd_signal"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Section>
  );
}

// -- Sub-chart: Bollinger Bands --
function BollingerChart({ series }: { series: IndicatorValues[] }) {
  const data = useMemo(
    () =>
      series
        .filter(
          (s) =>
            s.date != null && s.bb_upper != null && s.bb_lower != null,
        )
        .map((s) => ({
          date: s.date!,
          close: s.close,
          bb_upper: s.bb_upper,
          bb_middle: s.bb_middle,
          bb_lower: s.bb_lower,
        })),
    [series],
  );

  return (
    <Section title="Bollinger Bands">
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart
          data={data}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tickFormatter={fmtDate} {...axisProps} />
          <YAxis
            {...axisProps}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(l) => fmtDate(String(l))}
            formatter={(v, name) => [
              `$${Number(v).toFixed(2)}`,
              name === "bb_upper"
                ? "Upper"
                : name === "bb_middle"
                  ? "Middle"
                  : name === "bb_lower"
                    ? "Lower"
                    : "Close",
            ]}
          />
          <Area
            type="monotone"
            dataKey="bb_upper"
            stroke="transparent"
            fill="#4b5563"
            fillOpacity={0.1}
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="bb_lower"
            stroke="transparent"
            fill="#1a1a2e"
            fillOpacity={1}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="bb_upper"
            stroke="#6b7280"
            strokeDasharray="4 4"
            strokeWidth={1}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="bb_middle"
            stroke="#6b7280"
            strokeWidth={1}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="bb_lower"
            stroke="#6b7280"
            strokeDasharray="4 4"
            strokeWidth={1}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#e94560"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Section>
  );
}

// -- Sub-chart: Moving Averages --
function MovingAveragesChart({ series }: { series: IndicatorValues[] }) {
  const data = useMemo(
    () =>
      series
        .filter((s) => s.date != null && s.close != null)
        .map((s) => ({
          date: s.date!,
          close: s.close,
          sma_20: s.sma_20,
          sma_50: s.sma_50,
          sma_200: s.sma_200,
          ema_12: s.ema_12,
          ema_26: s.ema_26,
        })),
    [series],
  );

  return (
    <Section title="Moving Averages">
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart
          data={data}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tickFormatter={fmtDate} {...axisProps} />
          <YAxis
            {...axisProps}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(l) => fmtDate(String(l))}
            formatter={(v, name) => [
              `$${Number(v).toFixed(2)}`,
              String(name).toUpperCase().replace("_", " "),
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 10, color: "#a0a0a0" }}
            formatter={(val) => String(val).toUpperCase().replace("_", " ")}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#e0e0e0"
            strokeWidth={2}
            dot={false}
            name="close"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="sma_20"
            stroke="#14b8a6"
            strokeWidth={1.5}
            dot={false}
            name="sma_20"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="sma_50"
            stroke="#f97316"
            strokeWidth={1.5}
            dot={false}
            name="sma_50"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="sma_200"
            stroke="#a855f7"
            strokeWidth={1.5}
            dot={false}
            name="sma_200"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="ema_12"
            stroke="#06b6d4"
            strokeDasharray="3 3"
            strokeWidth={1}
            dot={false}
            name="ema_12"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="ema_26"
            stroke="#eab308"
            strokeDasharray="3 3"
            strokeWidth={1}
            dot={false}
            name="ema_26"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Section>
  );
}

// -- Sub-chart: Volume --
function VolumeChart({ series }: { series: IndicatorValues[] }) {
  const data = useMemo(
    () =>
      series
        .filter((s) => s.date != null && s.volume_sma_20 != null)
        .map((s) => ({
          date: s.date!,
          volume_sma_20: s.volume_sma_20,
        })),
    [series],
  );

  const fmtVol = (v: number) => {
    if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
    return String(v);
  };

  return (
    <Section title="Volume (20-day SMA)">
      <ResponsiveContainer width="100%" height={140}>
        <BarChart
          data={data}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tickFormatter={fmtDate} {...axisProps} />
          <YAxis {...axisProps} tickFormatter={fmtVol} />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(l) => fmtDate(String(l))}
            formatter={(v) => [fmtVol(Number(v)), "Volume SMA 20"]}
          />
          <Bar
            dataKey="volume_sma_20"
            fill="#3b82f6"
            opacity={0.6}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </Section>
  );
}

// -- Sub-chart: VWAP --
function VwapChart({ series }: { series: IndicatorValues[] }) {
  const data = useMemo(
    () =>
      series
        .filter((s) => s.date != null && s.close != null)
        .map((s) => ({
          date: s.date!,
          close: s.close,
          vwap: s.vwap,
        })),
    [series],
  );

  return (
    <Section title="VWAP">
      <ResponsiveContainer width="100%" height={160}>
        <ComposedChart
          data={data}
          margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tickFormatter={fmtDate} {...axisProps} />
          <YAxis
            {...axisProps}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(l) => fmtDate(String(l))}
            formatter={(v, name) => [
              `$${Number(v).toFixed(2)}`,
              name === "vwap" ? "VWAP" : "Close",
            ]}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#e94560"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="vwap"
            stroke="#eab308"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Section>
  );
}

// -- Main Panel --
export default function DashboardTAPanel({
  series,
  ticker,
}: DashboardTAPanelProps) {
  if (series.length === 0) {
    return (
      <Box
        sx={{
          border: "2px dashed",
          borderColor: "divider",
          borderRadius: 1,
          p: 6,
          textAlign: "center",
        }}
      >
        <Typography color="text.secondary">
          Select a stock to view technical indicators
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={2}>
      <Typography variant="subtitle2" color="text.secondary">
        {ticker} — Technical Indicators
      </Typography>
      <RsiChart series={series} />
      <MacdChart series={series} />
      <BollingerChart series={series} />
      <MovingAveragesChart series={series} />
      <VolumeChart series={series} />
      <VwapChart series={series} />
    </Stack>
  );
}
