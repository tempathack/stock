import { useEffect, useRef, useState } from "react";
import SpeedIcon from "@mui/icons-material/Speed";
import { Alert, Box, CircularProgress, Paper, Typography } from "@mui/material";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useKafkaLag } from "../../api/queries";
import type { KafkaPartitionLag } from "../../api/types";
import PlaceholderCard from "../ui/PlaceholderCard";

// 30 minutes at 15s poll interval = 120 samples max
const MAX_SAMPLES = 120;

interface LagSample {
  timestamp: string;
  [partitionKey: string]: number | string;
}

export default function StreamLagMonitor() {
  const { data, isLoading, isError } = useKafkaLag();

  // Accumulate snapshots across polls — never reset on re-render
  const samplesRef = useRef<LagSample[]>([]);
  const [chartData, setChartData] = useState<LagSample[]>([]);

  useEffect(() => {
    if (!data || data.partitions.length === 0) return;

    const now = new Date();
    const label = now.toLocaleTimeString("en-US", { hour12: false });

    const sample: LagSample = { timestamp: label };
    data.partitions.forEach((p: KafkaPartitionLag) => {
      sample[`p${p.partition}`] = p.lag;
    });

    const updated = [...samplesRef.current, sample];
    if (updated.length > MAX_SAMPLES) {
      updated.splice(0, updated.length - MAX_SAMPLES);
    }
    samplesRef.current = updated;
    setChartData([...updated]);
  }, [data]);

  const partitionKeys =
    chartData.length > 0
      ? Object.keys(chartData[chartData.length - 1]!).filter((k) => k !== "timestamp")
      : [];

  const LINE_COLORS = ["#00bcd4", "#4caf50", "#ff9800", "#f44336", "#9fa8da"];

  const hasData = chartData.length > 0 && partitionKeys.length > 0;

  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Box sx={{ display: "flex", alignItems: "center", mb: 2, gap: 1 }}>
        <SpeedIcon sx={{ color: "primary.main", fontSize: 20 }} />
        <Typography variant="h6">Kafka Stream Lag</Typography>
        <Box sx={{ ml: "auto" }}>
          {isLoading && <CircularProgress size={16} />}
        </Box>
      </Box>

      {isError && (
        <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
          Kafka lag endpoint returned an error — retrying in 15s.
        </Alert>
      )}

      {!isLoading && !hasData ? (
        <PlaceholderCard title="Lag data unavailable" />
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Total lag: {data?.total_lag ?? 0} messages
          </Typography>
          <Box
            role="img"
            aria-label="Kafka consumer lag per partition (30-min rolling window)"
            sx={{ height: 220 }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 4, right: 8, bottom: 4, left: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono", monospace' }}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  label={{
                    value: "Lag (messages)",
                    angle: -90,
                    position: "insideLeft",
                    fontSize: 10,
                    fontFamily: '"IBM Plex Mono", monospace',
                  }}
                  tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono", monospace' }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111827",
                    border: "1px solid rgba(0,188,212,0.12)",
                    fontSize: 11,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                {partitionKeys.map((key, idx) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={LINE_COLORS[idx % LINE_COLORS.length]}
                    dot={false}
                    strokeWidth={2}
                    name={key.toUpperCase()}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </>
      )}
    </Paper>
  );
}
