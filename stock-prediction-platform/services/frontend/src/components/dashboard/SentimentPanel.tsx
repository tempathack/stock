/**
 * SentimentPanel — Reddit sentiment display panel for Dashboard stock detail Drawer.
 *
 * Shows avg_sentiment as a color-coded LinearProgress gauge (red/amber/green),
 * mention count, positive/negative ratio, top subreddit, and last update timestamp.
 *
 * Shows MUI Skeleton while connecting, PlaceholderCard when data unavailable.
 * Follows Bloomberg Terminal dark aesthetic: #0d1220 background, DM Mono font.
 */
import {
  Chip,
  Divider,
  LinearProgress,
  Paper,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useSentimentSocket } from "@/hooks/useSentimentSocket";

// Convert VADER compound score [-1, +1] to LinearProgress value [0, 100]
const scoreToPercent = (s: number | null): number =>
  s == null ? 50 : Math.round(((s + 1) / 2) * 100);

// Color thresholds: bearish red < 40%, neutral amber 40-60%, bullish green > 60%
const progressColor = (pct: number): string => {
  if (pct < 40) return "#e05454";  // red — bearish
  if (pct < 60) return "#f59e0b";  // amber — neutral
  return "#22c983";                 // green — bullish
};

interface SentimentPanelProps {
  ticker: string;
}

export default function SentimentPanel({ ticker }: SentimentPanelProps) {
  const { data, status } = useSentimentSocket(ticker);

  // Loading skeleton while WebSocket is connecting and no data yet
  if (status === "connecting" || (status === "connected" && !data)) {
    return (
      <Stack spacing={1}>
        <Skeleton variant="rectangular" height={20} sx={{ borderRadius: 1, bgcolor: "rgba(255,255,255,0.05)" }} />
        <Skeleton variant="rectangular" height={8} sx={{ borderRadius: 1, bgcolor: "rgba(255,255,255,0.05)" }} />
        <Skeleton variant="rectangular" height={16} sx={{ borderRadius: 1, bgcolor: "rgba(255,255,255,0.05)" }} />
      </Stack>
    );
  }

  // Unavailable state: WebSocket disconnected, error, or available=false from server
  if (!data || !data.available) {
    return (
      <Paper sx={{ p: 1.5, bgcolor: "rgba(10,14,25,0.6)", borderRadius: 1 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem" }}
        >
          Sentiment data unavailable — pipeline may be starting
        </Typography>
      </Paper>
    );
  }

  const pct = scoreToPercent(data.avg_sentiment);
  const color = progressColor(pct);

  return (
    <Paper sx={{ p: 1.5, bgcolor: "rgba(10,14,25,0.6)", borderRadius: 1 }}>
      {/* Header row: title + LIVE chip */}
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography
          variant="subtitle2"
          fontWeight={700}
          sx={{ fontFamily: '"Syne", sans-serif', fontSize: "0.68rem", letterSpacing: "0.04em" }}
        >
          Reddit Sentiment
        </Typography>
        <Chip
          label="LIVE — Reddit"
          size="small"
          sx={{ bgcolor: "#22c983", color: "#000", fontSize: "0.6rem", height: 18, fontWeight: 700 }}
        />
      </Stack>

      <Divider sx={{ mb: 1.5, borderColor: "rgba(232,164,39,0.1)" }} />

      {/* Sentiment gauge: LinearProgress + score value */}
      <Stack spacing={0.5} sx={{ mb: 1.5 }}>
        <Stack direction="row" justifyContent="space-between">
          <Typography
            variant="caption"
            sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem", color: "rgba(107,122,159,0.8)" }}
          >
            Sentiment Score
          </Typography>
          <Typography
            variant="caption"
            sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem", color, fontWeight: 700 }}
          >
            {data.avg_sentiment != null ? data.avg_sentiment.toFixed(3) : "—"}
          </Typography>
        </Stack>
        <LinearProgress
          variant="determinate"
          value={pct}
          sx={{
            height: 6,
            borderRadius: 3,
            bgcolor: "rgba(255,255,255,0.08)",
            "& .MuiLinearProgress-bar": { bgcolor: color, borderRadius: 3 },
          }}
        />
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.58rem" }}>
            Bearish −1
          </Typography>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.58rem" }}>
            Bullish +1
          </Typography>
        </Stack>
      </Stack>

      {/* Mention stats row */}
      <Stack direction="row" spacing={2} sx={{ mb: 0.5 }}>
        <Typography
          variant="caption"
          sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.65rem", color: "rgba(107,122,159,0.8)" }}
        >
          Mentions:{" "}
          <strong style={{ color: "#e8e8e8" }}>{data.mention_count ?? "—"}</strong>
        </Typography>
        <Typography variant="caption" sx={{ fontSize: "0.65rem", color: "#22c983" }}>
          +{((data.positive_ratio ?? 0) * 100).toFixed(0)}%
        </Typography>
        <Typography variant="caption" sx={{ fontSize: "0.65rem", color: "#e05454" }}>
          −{((data.negative_ratio ?? 0) * 100).toFixed(0)}%
        </Typography>
      </Stack>

      {/* Top subreddit */}
      {data.top_subreddit && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ fontFamily: '"DM Mono", monospace', fontSize: "0.6rem", display: "block" }}
        >
          Top: r/{data.top_subreddit}
        </Typography>
      )}

      {/* Freshness timestamp */}
      {data.sampled_at && (
        <Typography
          variant="caption"
          color="text.disabled"
          sx={{ display: "block", fontSize: "0.58rem", mt: 0.5 }}
        >
          Updated: {new Date(data.sampled_at).toLocaleTimeString()}
        </Typography>
      )}
    </Paper>
  );
}
