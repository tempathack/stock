import type { RetrainStatus } from "@/api";
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  Divider,
  Box,
  CircularProgress,
} from "@mui/material";
import Grid from "@mui/material/Grid";

interface RetrainStatusPanelProps {
  status: RetrainStatus;
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZoneName: "short",
  });
}

export default function RetrainStatusPanel({ status }: RetrainStatusPanelProps) {
  const hasComparison = status.oldModel && status.newModel;

  let statusChip: React.ReactNode;
  if (status.isRetraining) {
    statusChip = (
      <Chip
        label="Retraining…"
        color="warning"
        size="small"
        icon={<CircularProgress size={12} color="inherit" />}
      />
    );
  } else if (status.lastRetrainDate) {
    statusChip = <Chip label="Up to Date" color="success" size="small" />;
  } else {
    statusChip = <Chip label="Never Retrained" size="small" />;
  }

  return (
    <Card>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="subtitle2">Retraining Status</Typography>
          {statusChip}
        </Stack>

        <Typography variant="caption" color="text.secondary">
          {status.lastRetrainDate
            ? `Last retrained: ${fmtDate(status.lastRetrainDate)}`
            : "Never retrained"}
        </Typography>

        {status.isRetraining && (
          <Typography variant="caption" color="warning.main" display="block" sx={{ mt: 0.5 }}>
            Model retraining in progress…
          </Typography>
        )}

        {hasComparison ? (
          <Grid container spacing={2} alignItems="stretch" sx={{ mt: 1 }}>
            {/* Previous Model */}
            <Grid size={{ xs: 5 }}>
              <Box sx={{ bgcolor: "background.default", borderRadius: 1, p: 1.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Previous Model
                </Typography>
                <Typography variant="body2" fontWeight={600} sx={{ mt: 0.5 }}>
                  {status.oldModel!.name}
                </Typography>
                <Typography
                  variant="h6"
                  fontFamily="monospace"
                  color="error.main"
                >
                  {status.oldModel!.rmse != null ? status.oldModel!.rmse.toFixed(4) : "—"}
                </Typography>
                <Typography variant="caption" fontFamily="monospace" color="text.secondary">
                  MAE {status.oldModel!.mae != null ? status.oldModel!.mae.toFixed(4) : "—"}
                </Typography>
              </Box>
            </Grid>

            {/* Divider */}
            <Grid size={{ xs: 2 }} sx={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
              <Divider orientation="vertical" flexItem />
            </Grid>

            {/* New Model */}
            <Grid size={{ xs: 5 }}>
              <Box sx={{ bgcolor: "background.default", borderRadius: 1, p: 1.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Current Model
                </Typography>
                <Typography variant="body2" fontWeight={600} sx={{ mt: 0.5 }}>
                  {status.newModel!.name}
                </Typography>
                <Typography
                  variant="h6"
                  fontFamily="monospace"
                  color="success.main"
                >
                  {status.newModel!.rmse != null ? status.newModel!.rmse.toFixed(4) : "—"}
                </Typography>
                <Typography variant="caption" fontFamily="monospace" color="text.secondary">
                  MAE {status.newModel!.mae != null ? status.newModel!.mae.toFixed(4) : "—"}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        ) : (
          <Box
            sx={{
              mt: 2,
              p: 2,
              border: "1px dashed",
              borderColor: "divider",
              borderRadius: 1,
              textAlign: "center",
            }}
          >
            <Typography variant="body2" color="text.secondary">
              No retraining history available
            </Typography>
          </Box>
        )}

        {status.improvementPct != null && (
          <Box sx={{ mt: 2, textAlign: "center" }}>
            <Typography
              variant="h4"
              fontWeight={700}
              color={status.improvementPct > 0 ? "success.main" : "error.main"}
            >
              {status.improvementPct > 0 ? "+" : ""}
              {status.improvementPct.toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              RMSE Improvement
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
