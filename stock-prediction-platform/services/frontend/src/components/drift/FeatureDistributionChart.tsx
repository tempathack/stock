import { useMemo } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  Tooltip,
} from "recharts";
import type { FeatureDistribution } from "@/api";

interface FeatureDistributionChartProps {
  distributions: FeatureDistribution[];
}

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 11,
};

function FeatureCard({ dist }: { dist: FeatureDistribution }) {
  const mergedData = useMemo(
    () =>
      dist.trainingBins.map((tb, i) => ({
        bin: tb.bin,
        training: tb.count,
        recent: dist.recentBins[i]?.count ?? 0,
      })),
    [dist],
  );

  return (
    <div
      className={`rounded-lg border p-3 ${
        dist.isDrifted ? "border-accent bg-bg-card" : "border-border bg-bg-card"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-mono text-text-primary">{dist.feature}</span>
        {dist.isDrifted ? (
          <span className="rounded bg-accent/20 px-1.5 py-0.5 text-xs font-semibold uppercase text-accent">
            Drifted
          </span>
        ) : (
          <span className="rounded bg-profit/20 px-1.5 py-0.5 text-xs font-semibold uppercase text-profit">
            OK
          </span>
        )}
      </div>

      {/* Stats */}
      <div className="mt-1 flex gap-3 text-xs font-mono text-text-secondary">
        <span>KS: {dist.ksStat?.toFixed(3) ?? "—"}</span>
        <span>PSI: {dist.psiValue?.toFixed(3) ?? "—"}</span>
      </div>

      {/* Histogram */}
      <div className="mt-2">
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={mergedData} barCategoryGap="15%">
            <XAxis
              dataKey="bin"
              tick={{ fontSize: 9, fill: "#a0a0a0" }}
              axisLine={{ stroke: "#2a2a4a" }}
              angle={-45}
              textAnchor="end"
              height={30}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value, name) => [
                Number(value),
                name === "training" ? "Training" : "Recent",
              ]}
            />
            <Bar dataKey="training" fill="#3b82f6" opacity={0.7} isAnimationActive={false} />
            <Bar dataKey="recent" fill="#e94560" opacity={0.7} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function FeatureDistributionChart({ distributions }: FeatureDistributionChartProps) {
  if (distributions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-bg-surface p-6 text-center text-text-secondary">
        No feature distribution data available
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-5">
      <h3 className="text-sm font-semibold text-text-primary">
        Feature Distributions — Training vs. Recent
      </h3>
      <p className="mt-0.5 text-xs text-text-secondary">
        {distributions.length} features monitored
      </p>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {distributions.map((dist) => (
          <FeatureCard key={dist.feature} dist={dist} />
        ))}
      </div>
    </div>
  );
}
