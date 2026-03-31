/**
 * StreamingFeaturesPanel — displays live Flink-computed EMA-20, RSI-14, MACD signal
 * from the Feast Redis online store. Polls every 5s via useStreamingFeatures hook.
 */
import { Chip, Divider, Paper, Skeleton, Stack, Tooltip, Typography } from "@mui/material";
import { useStreamingFeatures } from "@/api";

interface FeatureRowProps {
  label: string;
  value: number | null;
  rsiContext?: boolean;
}

function FeatureRow({ label, value, rsiContext = false }: FeatureRowProps) {
  const displayValue = value !== null ? value.toFixed(4) : "—";

  let contextChip: React.ReactNode = null;
  if (rsiContext && value !== null) {
    if (value > 70) {
      contextChip = (
        <Chip label="Overbought" size="small" color="warning" sx={{ height: 16, fontSize: "0.6rem", ml: 1 }} />
      );
    } else if (value < 30) {
      contextChip = (
        <Chip label="Oversold" size="small" color="success" sx={{ height: 16, fontSize: "0.6rem", ml: 1 }} />
      );
    } else {
      contextChip = (
        <Chip label="Neutral" size="small" sx={{ height: 16, fontSize: "0.6rem", ml: 1 }} />
      );
    }
  }

  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between">
      <Stack direction="row" alignItems="center">
        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 90 }}>
          {label}
        </Typography>
        {contextChip}
      </Stack>
      <Typography variant="caption" fontFamily="monospace" color="text.primary">
        {displayValue}
      </Typography>
    </Stack>
  );
}

interface StreamingFeaturesPanelProps {
  ticker: string;
}

export default function StreamingFeaturesPanel({ ticker }: StreamingFeaturesPanelProps) {
  const { data, isLoading, isError } = useStreamingFeatures(ticker);

  if (!ticker) return null;

  if (isLoading) {
    return <Skeleton variant="rectangular" height={100} sx={{ borderRadius: 1 }} />;
  }

  if (isError || !data?.available) {
    return (
      <Paper
        variant="outlined"
        sx={{ p: 2, borderColor: "divider" }}
        data-testid="streaming-features-empty"
      >
        <Typography variant="caption" color="text.secondary">
          No live Flink data yet — intraday data ingestion must be active and the
          indicator_stream Flink job must be running.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 2, borderColor: "divider" }} data-testid="streaming-features-panel">
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="subtitle2" fontWeight={700}>
          Streaming Indicators
        </Typography>
        <Tooltip title="Powered by Apache Flink indicator_stream job via Feast Redis online store">
          <Chip label="LIVE — Flink" size="small" color="success" sx={{ fontSize: "0.65rem", height: 18 }} />
        </Tooltip>
      </Stack>
      <Divider sx={{ mb: 1.5 }} />
      <Stack spacing={0.75}>
        <FeatureRow label="EMA-20" value={data.ema_20} />
        <FeatureRow label="RSI-14" value={data.rsi_14} rsiContext />
        <FeatureRow label="MACD Signal" value={data.macd_signal} />
      </Stack>
      {data.sampled_at && (
        <Typography variant="caption" color="text.disabled" sx={{ mt: 1, display: "block" }}>
          sampled {new Date(data.sampled_at).toLocaleTimeString()}
        </Typography>
      )}
    </Paper>
  );
}
