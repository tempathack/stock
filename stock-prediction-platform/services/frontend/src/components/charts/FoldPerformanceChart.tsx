import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import type { FoldMetric } from "@/api";
import { Paper, Typography } from "@mui/material";

interface FoldPerformanceChartProps {
  data: FoldMetric[];
  modelName: string;
}

export default function FoldPerformanceChart({ data, modelName }: FoldPerformanceChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    name: `Fold ${d.fold}`,
  }));

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
        Fold-by-Fold Performance — {modelName}
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
          <XAxis
            dataKey="name"
            tick={{ fill: "#a0a0a0", fontSize: 11 }}
            axisLine={{ stroke: "#2a2a4a" }}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: "#a0a0a0", fontSize: 11 }}
            axisLine={{ stroke: "#2a2a4a" }}
            label={{ value: "RMSE / MAE", angle: -90, position: "insideLeft", fill: "#a0a0a0", fontSize: 11 }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[0, 1]}
            tick={{ fill: "#a0a0a0", fontSize: 11 }}
            axisLine={{ stroke: "#2a2a4a" }}
            label={{ value: "R²", angle: 90, position: "insideRight", fill: "#a0a0a0", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f3460",
              border: "1px solid #2a2a4a",
              borderRadius: 6,
              color: "#e0e0e0",
              fontSize: 12,
            }}
            formatter={(value, name) => [Number(value).toFixed(4), String(name).toUpperCase()]}
          />
          <Legend
            wrapperStyle={{ color: "#a0a0a0", fontSize: 12 }}
          />
          <Bar yAxisId="left" dataKey="rmse" fill="#e94560" name="RMSE" radius={[2, 2, 0, 0]} />
          <Bar yAxisId="left" dataKey="mae" fill="#ffa726" name="MAE" radius={[2, 2, 0, 0]} />
          <Bar yAxisId="right" dataKey="r2" fill="#00d4aa" name="R²" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}
