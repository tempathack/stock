import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import type { RollingPerformancePoint } from "@/api";

interface RollingPerformanceChartProps {
  data: RollingPerformancePoint[];
}

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 12,
};

const fmtDate = (d: string) => {
  const dt = new Date(d);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

export default function RollingPerformanceChart({ data }: RollingPerformanceChartProps) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-bg-surface p-6 text-center text-text-secondary">
        No performance data available
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-5">
      <h3 className="text-sm font-semibold text-text-primary">Rolling Model Performance</h3>
      <p className="mt-0.5 text-xs text-text-secondary">
        30-day rolling RMSE, MAE, and Directional Accuracy
      </p>

      <div className="mt-4">
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={data} margin={{ left: 10, right: 20, top: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
            <XAxis
              dataKey="date"
              tickFormatter={fmtDate}
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
            />
            <YAxis
              yAxisId="left"
              domain={["auto", "auto"]}
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
              label={{ value: "Error", angle: -90, position: "insideLeft", fill: "#a0a0a0", fontSize: 11 }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 1]}
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              tick={{ fill: "#a0a0a0", fontSize: 10 }}
              axisLine={{ stroke: "#2a2a4a" }}
              label={{ value: "Accuracy", angle: 90, position: "insideRight", fill: "#a0a0a0", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelFormatter={(label) => fmtDate(String(label))}
              formatter={(value, name) => {
                const v = Number(value);
                if (name === "directionalAccuracy") {
                  return [`${(v * 100).toFixed(1)}%`, "Dir. Accuracy"];
                }
                return [v.toFixed(4), String(name).toUpperCase()];
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: 11, color: "#a0a0a0" }}
              formatter={(value: string) => {
                if (value === "rmse") return "RMSE";
                if (value === "mae") return "MAE";
                if (value === "directionalAccuracy") return "Directional Accuracy";
                return value;
              }}
            />
            <Line
              type="monotone"
              dataKey="rmse"
              stroke="#e94560"
              strokeWidth={2}
              dot={false}
              yAxisId="left"
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="mae"
              stroke="#ffa726"
              strokeWidth={2}
              dot={false}
              yAxisId="left"
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="directionalAccuracy"
              stroke="#00d4aa"
              strokeWidth={2}
              dot={false}
              yAxisId="right"
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
