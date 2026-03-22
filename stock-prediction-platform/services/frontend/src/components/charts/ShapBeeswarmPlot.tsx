import { useMemo } from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts";
import type { ShapBeeswarmPoint } from "@/api";

interface ShapBeeswarmPlotProps {
  data: ShapBeeswarmPoint[];
  title?: string;
}

/** Interpolate blue (#4da6ff) → red (#e94560) by feature_value 0→1 */
function featureColor(featureValue: number): string {
  const t = Math.max(0, Math.min(1, featureValue));
  const r = Math.round(77 + t * (233 - 77));
  const g = Math.round(166 + t * (69 - 166));
  const b = Math.round(255 + t * (96 - 255));
  return `rgb(${r},${g},${b})`;
}

interface CustomDotPayload {
  feature_value?: number;
}

function CustomDot(props: {
  cx?: number;
  cy?: number;
  payload?: CustomDotPayload;
}) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null) return null;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={3.5}
      fill={featureColor(payload?.feature_value ?? 0.5)}
      fillOpacity={0.8}
    />
  );
}

export default function ShapBeeswarmPlot({
  data,
  title = "SHAP Value Distribution",
}: ShapBeeswarmPlotProps) {
  // Group by feature to get ordered unique features
  const features = useMemo(() => {
    const map = new Map<string, number>();
    for (const pt of data) {
      map.set(pt.feature, (map.get(pt.feature) ?? 0) + Math.abs(pt.shap_value));
    }
    return [...map.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([f]) => f);
  }, [data]);

  // Map feature to numeric y for scatter
  const scatterData = useMemo(
    () =>
      data.map((pt) => ({
        ...pt,
        y: features.indexOf(pt.feature),
      })),
    [data, features],
  );

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-4">
      <h3 className="mb-3 text-sm font-medium text-text-primary">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
          <XAxis
            type="number"
            dataKey="shap_value"
            tick={{ fill: "#a0a0a0", fontSize: 11 }}
            axisLine={{ stroke: "#2a2a4a" }}
            label={{ value: "SHAP Value", position: "insideBottomRight", offset: -5, fill: "#a0a0a0", fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            tick={{ fill: "#a0a0a0", fontSize: 11 }}
            axisLine={{ stroke: "#2a2a4a" }}
            width={130}
            domain={[-0.5, features.length - 0.5]}
            ticks={features.map((_, i) => i)}
            tickFormatter={(v: number) => features[v] ?? ""}
          />
          <ReferenceLine x={0} stroke="#2a2a4a" strokeDasharray="4 4" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f3460",
              border: "1px solid #2a2a4a",
              borderRadius: 6,
              color: "#e0e0e0",
              fontSize: 12,
            }}
            formatter={(value, name) => {
              const n = Number(value);
              if (name === "shap_value") return [n.toFixed(4), "SHAP Value"];
              if (name === "feature_value") return [n.toFixed(3), "Feature Value"];
              return [String(value), String(name)];
            }}
          />
          <Scatter
            data={scatterData}
            shape={<CustomDot />}
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Color legend */}
      <div className="mt-2 flex items-center justify-center gap-2 text-xs text-text-secondary">
        <span>Low</span>
        <div
          className="h-2 w-24 rounded"
          style={{ background: "linear-gradient(to right, #4da6ff, #e94560)" }}
        />
        <span>High</span>
        <span className="ml-1 text-text-secondary/60">Feature Value</span>
      </div>
    </div>
  );
}
