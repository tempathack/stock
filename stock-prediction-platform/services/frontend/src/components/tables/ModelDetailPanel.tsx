import {
  Box,
  Chip,
  Divider,
  Grid,
  Paper,
  Typography,
} from "@mui/material";
import type { ModelComparisonEntry } from "@/api";

interface ModelDetailPanelProps {
  model: ModelComparisonEntry;
}

function fmt(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(decimals) : "—";
}

function stabilityColor(val: number | null): string {
  if (val === null) return "text.secondary";
  if (val < 0.01) return "success.main";
  if (val < 0.05) return "warning.main";
  return "error.main";
}

function metricColor(key: string, value: number): string {
  if (key === "r2" || key === "directional_accuracy") {
    return value > 0.8 ? "success.main" : value > 0.5 ? "warning.main" : "error.main";
  }
  return "text.primary";
}

export default function ModelDetailPanel({ model }: ModelDetailPanelProps) {
  const params = model.best_params ?? {};
  const metrics = model.oos_metrics ?? {};

  return (
    <Paper sx={{ p: 2 }}>
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexWrap: "wrap" }}>
        <Typography variant="h6" fontWeight={700}>
          {model.model_name}
        </Typography>
        {model.version != null && (
          <Chip label={`v${model.version}`} size="small" variant="outlined" />
        )}
        <Chip
          label={model.is_active ? "Active" : "Inactive"}
          color={model.is_active ? "success" : "default"}
          size="small"
        />
      </Box>

      {/* Metadata grid */}
      <Grid container spacing={2} sx={{ mt: 1 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Typography variant="caption" color="text.secondary">
            Scaler
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500, textTransform: "capitalize" }}>
            {model.scaler_variant}
          </Typography>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Typography variant="caption" color="text.secondary">
            Saved At
          </Typography>
          <Typography variant="body2" fontWeight={500}>
            {model.saved_at ? new Date(model.saved_at).toLocaleString() : "—"}
          </Typography>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Typography variant="caption" color="text.secondary">
            Fold Stability
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
              fontWeight: 500,
              color: stabilityColor(model.fold_stability),
            }}
          >
            {fmt(model.fold_stability, 4)}
          </Typography>
        </Grid>
      </Grid>

      {/* Hyperparameters */}
      {Object.keys(params).length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}
          >
            Hyperparameters
          </Typography>
          <Divider sx={{ my: 0.5 }} />
          <Grid container spacing={1} sx={{ mt: 0.5 }}>
            {Object.entries(params).map(([key, value]) => (
              <Grid size={{ xs: 6, sm: 4, lg: 3 }} key={key}>
                <Typography variant="caption" color="text.secondary">
                  {key}
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* OOS Metrics */}
      {Object.keys(metrics).length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}
          >
            OOS Metrics
          </Typography>
          <Divider sx={{ my: 0.5 }} />
          <Grid container spacing={1} sx={{ mt: 0.5 }}>
            {Object.entries(metrics).map(([key, value]) => {
              const n = Number(value);
              return (
                <Grid size={{ xs: 6, sm: 4, lg: "auto" }} key={key}>
                  <Typography variant="caption" color="text.secondary">
                    {key}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: "monospace",
                      fontWeight: 500,
                      color: Number.isFinite(n)
                        ? metricColor(key, n)
                        : "text.secondary",
                    }}
                  >
                    {fmt(value, 4)}
                  </Typography>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}
    </Paper>
  );
}
