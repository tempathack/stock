import type { BacktestMetrics } from "@/api";

interface BacktestMetricsSummaryProps {
  metrics: BacktestMetrics;
}

const cards = [
  {
    key: "rmse" as const,
    label: "Root Mean Squared Error",
    fmt: (v: number) => v.toFixed(4),
    color: "#e94560",
  },
  {
    key: "mae" as const,
    label: "Mean Absolute Error",
    fmt: (v: number) => v.toFixed(4),
    color: "#ffa726",
  },
  {
    key: "mape" as const,
    label: "Mean Abs % Error",
    fmt: (v: number) => `${v.toFixed(2)}%`,
    color: "#ffa726",
  },
  {
    key: "r2" as const,
    label: "R² Score",
    fmt: (v: number) => v.toFixed(4),
    colorFn: (v: number) => (v > 0.5 ? "#00d4aa" : "#e94560"),
  },
  {
    key: "directional_accuracy" as const,
    label: "Directional Accuracy",
    fmt: (v: number) => `${v.toFixed(1)}%`,
    colorFn: (v: number) => (v > 50 ? "#00d4aa" : "#e94560"),
  },
  {
    key: "total_points" as const,
    label: "Total Data Points",
    fmt: (v: number) => String(v),
    color: "#3b82f6",
  },
] as const;

export default function BacktestMetricsSummary({
  metrics,
}: BacktestMetricsSummaryProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {cards.map((c) => {
        const value = metrics[c.key];
        const accent =
          "colorFn" in c ? c.colorFn(value) : c.color;
        return (
          <div
            key={c.key}
            className="rounded-lg border border-border bg-bg-surface p-4"
            style={{ borderTopWidth: 2, borderTopColor: accent }}
          >
            <p className="text-xl font-bold sm:text-2xl" style={{ color: accent }}>
              {c.fmt(value)}
            </p>
            <p className="mt-1 text-xs text-text-secondary">{c.label}</p>
          </div>
        );
      })}
    </div>
  );
}
