import type { BacktestMetrics } from "@/api";
import { Card, CardContent, Typography, Tooltip } from "@mui/material";
import Grid from "@mui/material/Grid";

interface BacktestMetricsSummaryProps {
  metrics: BacktestMetrics;
}

const cards = [
  {
    key: "rmse" as const,
    label: "Root Mean Squared Error",
    tooltip: "Lower is better — measures average prediction error magnitude",
    fmt: (v: number) => v.toFixed(4),
    color: "#e94560",
  },
  {
    key: "mae" as const,
    label: "Mean Absolute Error",
    tooltip: "Lower is better — average absolute difference between predicted and actual",
    fmt: (v: number) => v.toFixed(4),
    color: "#ffa726",
  },
  {
    key: "mape" as const,
    label: "Mean Abs % Error",
    tooltip: "Lower is better — error as a percentage of actual value",
    fmt: (v: number) => `${v.toFixed(2)}%`,
    color: "#ffa726",
  },
  {
    key: "r2" as const,
    label: "R² Score",
    tooltip: "Higher is better — proportion of variance explained (1.0 = perfect)",
    fmt: (v: number) => v.toFixed(4),
    colorFn: (v: number) => (v > 0.5 ? "#00d4aa" : "#e94560"),
  },
  {
    key: "directional_accuracy" as const,
    label: "Directional Accuracy",
    tooltip: "Higher is better — percentage of correct up/down direction predictions",
    fmt: (v: number) => `${v.toFixed(1)}%`,
    colorFn: (v: number) => (v > 50 ? "#00d4aa" : "#e94560"),
  },
  {
    key: "total_points" as const,
    label: "Total Data Points",
    tooltip: "Number of data points used in the backtest",
    fmt: (v: number) => String(v),
    color: "#3b82f6",
  },
] as const;

export default function BacktestMetricsSummary({
  metrics,
}: BacktestMetricsSummaryProps) {
  return (
    <Grid container spacing={2}>
      {cards.map((c) => {
        const value = metrics[c.key];
        const accent = "colorFn" in c ? c.colorFn(value) : c.color;
        return (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={c.key}>
            <Tooltip title={c.tooltip} placement="top">
              <Card
                sx={{ borderTop: `3px solid ${accent}`, cursor: "default" }}
              >
                <CardContent>
                  <Typography variant="h3" sx={{ color: accent, fontFamily: "monospace" }}>
                    {c.fmt(value)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {c.label}
                  </Typography>
                </CardContent>
              </Card>
            </Tooltip>
          </Grid>
        );
      })}
    </Grid>
  );
}
