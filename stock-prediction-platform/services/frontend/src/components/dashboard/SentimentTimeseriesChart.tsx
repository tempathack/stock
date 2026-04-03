/**
 * SentimentTimeseriesChart — recharts LineChart for 10h rolling sentiment history.
 *
 * Displays avg_sentiment on VADER compound scale [-1, +1] at 2-min intervals.
 * Reference lines at ±0.05 mark bullish/bearish thresholds.
 * Polls REST endpoint every 120s via useSentimentTimeseries hook.
 *
 * States:
 *   loading  → 3x MUI Skeleton bars
 *   empty    → unavailable placeholder (reuses SentimentPanel copy)
 *   data     → recharts LineChart
 */
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Paper from "@mui/material/Paper";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useSentimentTimeseries } from "@/hooks/useSentimentTimeseries";

interface SentimentTimeseriesChartProps {
  ticker: string;
}

function formatTime(t: string): string {
  return new Date(t).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SentimentTimeseriesChart({
  ticker,
}: SentimentTimeseriesChartProps) {
  const { data, isLoading } = useSentimentTimeseries(ticker);

  // Loading state
  if (isLoading) {
    return (
      <Stack spacing={1} sx={{ mt: 1 }}>
        <Skeleton variant="rectangular" height={20} sx={{ borderRadius: 0.5 }} />
        <Skeleton variant="rectangular" height={8} sx={{ borderRadius: 0.5 }} />
        <Skeleton variant="rectangular" height={16} sx={{ borderRadius: 0.5 }} />
      </Stack>
    );
  }

  // Empty state — no data yet or endpoint unavailable
  if (!data || data.points.length === 0) {
    return (
      <Paper
        sx={{
          p: 1.5,
          bgcolor: "rgba(10,14,25,0.6)",
          borderRadius: 1,
          mt: 1,
        }}
      >
        <Typography variant="caption" sx={{ color: "rgba(107,122,159,0.8)" }}>
          Sentiment history unavailable — pipeline may be starting
        </Typography>
      </Paper>
    );
  }

  const { points } = data;

  return (
    <Paper
      sx={{
        p: 1.5,
        bgcolor: "rgba(10,14,25,0.6)",
        borderRadius: 1,
        mt: 1,
      }}
    >
      {/* Header row */}
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ mb: 1 }}
      >
        <Typography
          variant="subtitle2"
          sx={{ fontSize: "0.65rem", fontWeight: 700, letterSpacing: "0.04em" }}
        >
          Sentiment — 10h History
        </Typography>
        <Typography variant="caption" sx={{ color: "rgba(107,122,159,0.8)" }}>
          {points.length} pts, 2-min intervals
        </Typography>
      </Stack>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={200}>
        <LineChart
          data={points}
          margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.05)"
          />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTime}
            interval="preserveStartEnd"
            tick={{ fill: "rgba(107,122,159,0.8)", fontSize: 10 }}
          />
          <YAxis
            domain={[-1, 1]}
            tickFormatter={(v: number) => v.toFixed(1)}
            width={36}
            tick={{ fill: "rgba(107,122,159,0.8)", fontSize: 10 }}
          />
          {/* Bullish threshold */}
          <ReferenceLine
            y={0.05}
            stroke="#22c983"
            strokeDasharray="4 2"
            strokeOpacity={0.4}
          />
          {/* Bearish threshold */}
          <ReferenceLine
            y={-0.05}
            stroke="#e05454"
            strokeDasharray="4 2"
            strokeOpacity={0.4}
          />
          <Tooltip
            formatter={(v) => [Number(v).toFixed(3), "Sentiment"]}
            labelFormatter={(t) => new Date(String(t)).toLocaleTimeString()}
            contentStyle={{
              backgroundColor: "#0f1c2e",
              border: "1px solid rgba(124,58,237,0.3)",
              fontSize: 11,
            }}
          />
          <Line
            type="monotone"
            dataKey="avg_sentiment"
            stroke="#BF5AF2"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
}
