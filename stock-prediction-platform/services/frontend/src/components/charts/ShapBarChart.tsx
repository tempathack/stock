import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { ShapFeatureImportance } from "@/api";

interface ShapBarChartProps {
  data: ShapFeatureImportance[];
  title?: string;
}

export default function ShapBarChart({
  data,
  title = "Feature Importance (SHAP)",
}: ShapBarChartProps) {
  const top15 = [...data].sort((a, b) => b.importance - a.importance).slice(0, 15);

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-4">
      <h3 className="mb-3 text-sm font-medium text-text-primary">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={top15} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" horizontal={false} />
          <XAxis type="number" tick={{ fill: "#a0a0a0", fontSize: 11 }} axisLine={{ stroke: "#2a2a4a" }} />
          <YAxis
            type="category"
            dataKey="feature"
            width={130}
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
            formatter={(value) => [Number(value).toFixed(4), "Importance"]}
          />
          <Bar dataKey="importance" fill="#e94560" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
