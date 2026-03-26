import type { DriftEventEntry } from "@/api";
import { Box, Chip, Paper, Typography } from "@mui/material";
import Timeline from "@mui/lab/Timeline";
import TimelineItem from "@mui/lab/TimelineItem";
import TimelineSeparator from "@mui/lab/TimelineSeparator";
import TimelineConnector from "@mui/lab/TimelineConnector";
import TimelineContent from "@mui/lab/TimelineContent";
import TimelineDot from "@mui/lab/TimelineDot";
import TimelineOppositeContent from "@mui/lab/TimelineOppositeContent";

interface DriftTimelineProps {
  events: DriftEventEntry[];
}

const DRIFT_TYPE_COLORS: Record<string, "info" | "secondary" | "warning"> = {
  data_drift: "info",
  prediction_drift: "secondary",
  concept_drift: "warning",
};

const DRIFT_TYPE_LABELS: Record<string, string> = {
  data_drift: "Data",
  prediction_drift: "Prediction",
  concept_drift: "Concept",
};

const SEVERITY_DOT_COLORS: Record<string, "success" | "warning" | "error" | "grey"> = {
  none: "grey",
  low: "success",
  medium: "warning",
  high: "error",
};

function fmtTimestamp(iso: string | null): string {
  if (!iso) return "Unknown";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function DriftTimeline({ events }: DriftTimelineProps) {
  if (events.length === 0) {
    return (
      <Paper
        sx={{
          p: 3,
          textAlign: "center",
          border: "1px dashed",
          borderColor: "divider",
        }}
      >
        <Typography color="text.secondary">No drift events recorded</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        Drift Event Timeline
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {events.length} events detected
      </Typography>

      <Timeline sx={{ p: 0, mt: 1 }}>
        {events.map((evt, idx) => {
          const dotColor = SEVERITY_DOT_COLORS[evt.severity] ?? "grey";
          const typeColor = DRIFT_TYPE_COLORS[evt.drift_type] ?? "info";
          const typeLabel = DRIFT_TYPE_LABELS[evt.drift_type] ?? evt.drift_type;

          return (
            <TimelineItem key={`${evt.drift_type}-${evt.timestamp}-${idx}`}>
              <TimelineOppositeContent
                sx={{ flex: 0.3, py: "12px", fontSize: "0.72rem", color: "text.secondary" }}
              >
                {fmtTimestamp(evt.timestamp)}
              </TimelineOppositeContent>
              <TimelineSeparator>
                <TimelineDot color={dotColor} />
                {idx < events.length - 1 && <TimelineConnector />}
              </TimelineSeparator>
              <TimelineContent sx={{ py: "6px", px: 2 }}>
                <Paper elevation={0} sx={{ p: 1.5, bgcolor: "background.default", border: "1px solid", borderColor: "divider" }}>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 0.5 }}>
                    <Chip label={typeLabel} color={typeColor} size="small" />
                    <Chip
                      label={evt.severity.charAt(0).toUpperCase() + evt.severity.slice(1)}
                      size="small"
                      variant="outlined"
                    />
                    {evt.is_drifted && (
                      <Chip label="Drifted" color="primary" size="small" variant="outlined" />
                    )}
                  </Box>
                  {evt.features_affected.length > 0 && (
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
                      {evt.features_affected.map((f) => (
                        <Chip
                          key={f}
                          label={f}
                          size="small"
                          variant="outlined"
                          sx={{ fontFamily: "monospace", fontSize: "0.7rem" }}
                        />
                      ))}
                    </Box>
                  )}
                </Paper>
              </TimelineContent>
            </TimelineItem>
          );
        })}
      </Timeline>
    </Paper>
  );
}
