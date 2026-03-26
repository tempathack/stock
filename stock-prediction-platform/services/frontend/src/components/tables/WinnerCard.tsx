import { Box, Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import type { ModelComparisonEntry } from "@/api";

interface WinnerCardProps {
  winner: ModelComparisonEntry | null;
}

function fmt(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(decimals) : "—";
}

export default function WinnerCard({ winner }: WinnerCardProps) {
  if (!winner) {
    return (
      <Card sx={{ border: "1px dashed", borderColor: "divider" }}>
        <CardContent>
          <Typography color="text.secondary" align="center">
            No winner model selected
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ border: "2px solid", borderColor: "primary.main" }}>
      <CardContent>
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", sm: "flex-start" },
            gap: 2,
          }}
        >
          {/* Left — title */}
          <Box>
            <Chip
              icon={<EmojiEventsIcon />}
              label="Winner"
              color="primary"
              size="small"
            />
            <Typography
              variant="h5"
              sx={{ mt: 1, color: "primary.main", fontWeight: 700 }}
            >
              {winner.model_name}
            </Typography>
          </Box>

          {/* Right — key metrics */}
          <Grid container spacing={2} sx={{ maxWidth: 320 }}>
            <Grid size={{ xs: 6 }}>
              <Typography variant="caption" color="text.secondary">
                OOS RMSE
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: "monospace", fontWeight: 500 }}>
                {fmt(winner.oos_metrics.rmse, 6)}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Typography variant="caption" color="text.secondary">
                OOS R²
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: "monospace", fontWeight: 500 }}>
                {fmt(winner.oos_metrics.r2, 4)}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Typography variant="caption" color="text.secondary">
                Fold Stability
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: "monospace", fontWeight: 500 }}>
                {fmt(winner.fold_stability, 4)}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Typography variant="caption" color="text.secondary">
                Scaler
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500, textTransform: "capitalize" }}>
                {winner.scaler_variant}
              </Typography>
            </Grid>
          </Grid>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: "block" }}>
          Selected based on lowest OOS RMSE with stable cross-validation performance
        </Typography>
      </CardContent>
    </Card>
  );
}
