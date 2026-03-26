import { Paper, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
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
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {title}
      </Typography>
      <BarChart
        layout="horizontal"
        dataset={top15 as unknown as Record<string, unknown>[]}
        yAxis={[{ scaleType: "band", dataKey: "feature" }]}
        series={[
          {
            dataKey: "importance",
            label: "Importance",
            color: "#e94560",
          },
        ]}
        height={400}
        margin={{ left: 140, right: 20, top: 10, bottom: 30 }}
      />
    </Paper>
  );
}
