import StreamIcon from "@mui/icons-material/Stream";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useFlinkJobs } from "../../api/queries";
import PlaceholderCard from "../ui/PlaceholderCard";

const STATUS_COLOR: Record<string, "success" | "error" | "warning" | "default"> = {
  RUNNING: "success",
  FAILED: "error",
  FAILING: "error",
  RESTARTING: "warning",
  CANCELLING: "warning",
};

export default function StreamHealthPanel() {
  const { data, isLoading, isError } = useFlinkJobs();
  const jobs = data?.jobs ?? [];

  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Box sx={{ display: "flex", alignItems: "center", mb: 2, gap: 1 }}>
        <StreamIcon sx={{ color: "primary.main", fontSize: 20 }} />
        <Typography variant="h6">Stream Health</Typography>
        <Box sx={{ ml: "auto" }}>
          {isLoading && <CircularProgress size={16} />}
        </Box>
      </Box>

      {isError && (
        <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
          Flink REST API is currently unreachable — displaying last known data.
        </Alert>
      )}

      {!isLoading && jobs.length === 0 ? (
        <PlaceholderCard title="No stream jobs detected" />
      ) : (
        <Stack spacing={1}>
          {jobs.map((job) => (
            <Box
              key={job.job_id}
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Typography variant="body2" noWrap sx={{ maxWidth: "60%" }}>
                {job.name}
              </Typography>
              <Chip
                size="small"
                label={job.state}
                color={STATUS_COLOR[job.state] ?? "default"}
                aria-label={`${job.state} status`}
              />
            </Box>
          ))}
        </Stack>
      )}
    </Paper>
  );
}
