import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import WarningIcon from "@mui/icons-material/Warning";
import { Box, CircularProgress, Grid, Paper, Typography } from "@mui/material";
import { useAnalyticsSummary } from "../../api/queries";

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  isLoading: boolean;
}

function MetricCard({ label, value, icon, isLoading }: MetricCardProps) {
  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Box sx={{ display: "flex", alignItems: "center", mb: 1, gap: 1 }}>
        {icon}
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        {isLoading && <CircularProgress size={12} sx={{ ml: "auto" }} />}
      </Box>
      <Typography variant="h6">{value}</Typography>
    </Paper>
  );
}

export default function SystemHealthSummary() {
  const { data, isLoading } = useAnalyticsSummary();

  const argoCdValue = data?.argocd_sync_status ?? "N/A";
  const flinkValue = data
    ? `${data.flink_running_jobs} running / ${data.flink_failed_jobs} failed`
    : "—";
  const feastValue =
    data?.feast_online_latency_ms != null
      ? `${data.feast_online_latency_ms.toFixed(1)} ms`
      : "N/A";
  const caValue = data?.ca_last_refresh
    ? new Date(data.ca_last_refresh).toLocaleTimeString()
    : "N/A";

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <MetricCard
          label="Argo CD Sync"
          value={argoCdValue}
          icon={
            argoCdValue === "Synced" ? (
              <CheckCircleIcon sx={{ color: "success.main", fontSize: 20 }} />
            ) : (
              <WarningIcon sx={{ color: "warning.main", fontSize: 20 }} />
            )
          }
          isLoading={isLoading}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <MetricCard
          label="Flink Cluster"
          value={flinkValue}
          icon={
            data != null
              ? <CheckCircleIcon sx={{ color: "primary.main", fontSize: 20 }} />
              : <HelpOutlineIcon sx={{ color: "text.disabled", fontSize: 20 }} />
          }
          isLoading={isLoading}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <MetricCard
          label="Feast Latency p99"
          value={feastValue}
          icon={
            data?.feast_online_latency_ms != null
              ? <CheckCircleIcon sx={{ color: "primary.main", fontSize: 20 }} />
              : <HelpOutlineIcon sx={{ color: "text.disabled", fontSize: 20 }} />
          }
          isLoading={isLoading}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <MetricCard
          label="CA Last Refresh"
          value={caValue}
          icon={
            data?.ca_last_refresh != null
              ? <CheckCircleIcon sx={{ color: "primary.main", fontSize: 20 }} />
              : <HelpOutlineIcon sx={{ color: "text.disabled", fontSize: 20 }} />
          }
          isLoading={isLoading}
        />
      </Grid>
    </Grid>
  );
}
