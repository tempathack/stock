import DataObjectIcon from "@mui/icons-material/DataObject";
import {
  Alert,
  Box,
  CircularProgress,
  LinearProgress,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useFeatureFreshness } from "../../api/queries";
import PlaceholderCard from "../ui/PlaceholderCard";

function getStalenessColor(s: number | null): "success" | "warning" | "error" | "inherit" {
  if (s === null) return "inherit";
  if (s < 15 * 60) return "success";   // <15min: green
  if (s < 60 * 60) return "warning";   // <1h: amber
  return "error";                        // >1h: red
}

function formatStaleness(s: number | null): string {
  if (s === null) return "—";
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

function getStalenessProgress(s: number | null): number {
  // 0 = fully fresh, 100 = 6h+ stale
  if (s === null) return 0;
  return Math.min(100, (s / (6 * 3600)) * 100);
}

export default function FeatureFreshnessPanel() {
  const { data, isLoading, isError } = useFeatureFreshness();
  const views = data?.views ?? [];

  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Box sx={{ display: "flex", alignItems: "center", mb: 2, gap: 1 }}>
        <DataObjectIcon sx={{ color: "primary.main", fontSize: 20 }} />
        <Typography variant="h6">Feature Freshness</Typography>
        <Box sx={{ ml: "auto" }}>
          {isLoading && <CircularProgress size={16} />}
        </Box>
      </Box>

      {isError && (
        <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
          Feast registry query failed — check FastAPI logs.
        </Alert>
      )}

      {!isLoading && views.length === 0 ? (
        <PlaceholderCard title="No feature views found" />
      ) : (
        <Stack spacing={2}>
          {views.map((view) => (
            <Tooltip
              key={view.view_name}
              title={`${view.view_name}: last materialized ${formatStaleness(view.staleness_seconds)}`}
            >
              <Box sx={{ opacity: view.staleness_seconds === null ? 0.45 : 1 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 0.5,
                  }}
                >
                  <Typography variant="body2">{view.view_name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatStaleness(view.staleness_seconds)}
                  </Typography>
                </Box>
                {view.staleness_seconds !== null && (
                  <LinearProgress
                    variant="determinate"
                    value={getStalenessProgress(view.staleness_seconds)}
                    color={getStalenessColor(view.staleness_seconds) as "success" | "warning" | "error"}
                    sx={{ height: 6, borderRadius: 1 }}
                  />
                )}
              </Box>
            </Tooltip>
          ))}
        </Stack>
      )}
    </Paper>
  );
}
