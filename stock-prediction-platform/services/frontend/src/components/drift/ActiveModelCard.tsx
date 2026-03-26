import type { ActiveModelInfo } from "@/api";
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  Box,
  CircularProgress,
  Tooltip,
} from "@mui/material";

interface ActiveModelCardProps {
  model: ActiveModelInfo | null;
}

function fmt(value: number | null, decimals: number): string {
  return value != null && Number.isFinite(value) ? value.toFixed(decimals) : "—";
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function ActiveModelCard({ model }: ActiveModelCardProps) {
  if (!model) {
    return (
      <Card sx={{ p: 3, textAlign: "center" }}>
        <Typography color="text.secondary">No active model detected</Typography>
      </Card>
    );
  }

  const borderColor = model.isActive ? "success.main" : "warning.main";

  return (
    <Card sx={{ borderLeft: "4px solid", borderLeftColor: borderColor }}>
      <CardContent>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          alignItems={{ xs: "flex-start", sm: "flex-start" }}
          spacing={2}
        >
          {/* Left — title + meta */}
          <Box>
            <Stack direction="row" alignItems="center" spacing={1} mb={0.5}>
              <Typography variant="h6">{model.modelName}</Typography>
              {model.isActive ? (
                <Chip label="Active" color="success" size="small" />
              ) : (
                <Chip
                  label="Retraining..."
                  color="warning"
                  size="small"
                  icon={<CircularProgress size={12} color="inherit" />}
                />
              )}
            </Stack>
            <Stack direction="row" spacing={2} flexWrap="wrap">
              <Typography variant="caption" color="text.secondary">
                Scaler:{" "}
                <Box component="span" sx={{ color: "text.primary", textTransform: "capitalize" }}>
                  {model.scalerVariant}
                </Box>
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Version:{" "}
                <Box component="span" sx={{ color: "text.primary" }}>
                  v{model.version}
                </Box>
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Trained:{" "}
                <Box component="span" sx={{ color: "text.primary" }}>
                  {fmtDate(model.trainedDate)}
                </Box>
              </Typography>
            </Stack>
          </Box>

          {/* Right — metric pills */}
          <Stack direction="row" spacing={1}>
            <Tooltip title="Out-of-sample Root Mean Squared Error">
              <Box sx={{ bgcolor: "background.default", borderRadius: 1, px: 1.5, py: 1, textAlign: "center" }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  RMSE
                </Typography>
                <Typography variant="body2" fontFamily="monospace" fontWeight={600}>
                  {fmt(model.oosRmse, 4)}
                </Typography>
              </Box>
            </Tooltip>
            <Tooltip title="Out-of-sample Mean Absolute Error">
              <Box sx={{ bgcolor: "background.default", borderRadius: 1, px: 1.5, py: 1, textAlign: "center" }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  MAE
                </Typography>
                <Typography variant="body2" fontFamily="monospace" fontWeight={600}>
                  {fmt(model.oosMae, 4)}
                </Typography>
              </Box>
            </Tooltip>
            <Tooltip title="Directional Accuracy — percentage of correct up/down predictions">
              <Box sx={{ bgcolor: "background.default", borderRadius: 1, px: 1.5, py: 1, textAlign: "center" }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  Dir. Acc
                </Typography>
                <Typography variant="body2" fontFamily="monospace" fontWeight={600}>
                  {model.oosDirectionalAccuracy != null
                    ? `${(model.oosDirectionalAccuracy * 100).toFixed(1)}%`
                    : "—"}
                </Typography>
              </Box>
            </Tooltip>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
