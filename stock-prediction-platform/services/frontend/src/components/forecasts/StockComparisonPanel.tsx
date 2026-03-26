import type { ForecastRow } from "@/api";
import { Box, Button, ButtonBase, Chip, Paper, Stack, Typography } from "@mui/material";

interface StockComparisonPanelProps {
  rows: ForecastRow[];
  comparisonTickers: string[];
  onRemove: (ticker: string) => void;
  onSelectDetail: (ticker: string) => void;
}

const fmt = (n: number | null, decimals = 2, prefix = "") =>
  n != null ? `${prefix}${n.toFixed(decimals)}` : "—";

const trendIcon = (t: ForecastRow["trend"]) =>
  t === "bullish" ? "▲" : t === "bearish" ? "▼" : "—";

export default function StockComparisonPanel({
  rows,
  comparisonTickers,
  onRemove,
  onSelectDetail,
}: StockComparisonPanelProps) {
  if (comparisonTickers.length < 2) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: "center" }}>
        Select 2+ stocks in the table to compare side by side.
      </Typography>
    );
  }

  const selected = comparisonTickers
    .map((t) => rows.find((r) => r.ticker === t))
    .filter(Boolean) as ForecastRow[];

  return (
    <Paper sx={{ mt: 2, p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="subtitle2">Comparing {selected.length} stocks</Typography>
        <Button
          size="small"
          color="error"
          variant="text"
          onClick={() => comparisonTickers.forEach(onRemove)}
        >
          Clear all
        </Button>
      </Stack>

      <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1 }}>
        {selected.map((row) => {
          const returnPct = row.expected_return_pct;
          const returnColor =
            returnPct > 0 ? "success.main" : returnPct < 0 ? "error.main" : "text.secondary";
          const trendChipColor =
            row.trend === "bullish" ? "success" : row.trend === "bearish" ? "error" : "default";

          return (
            <Paper
              key={row.ticker}
              elevation={2}
              sx={{ minWidth: 220, flexShrink: 0, p: 2 }}
            >
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="body2" fontWeight={700} color="primary.main">
                  {row.ticker}
                </Typography>
                <ButtonBase
                  onClick={() => onRemove(row.ticker)}
                  aria-label={`Remove ${row.ticker}`}
                  sx={{ borderRadius: 1, px: 0.5, color: "text.secondary", fontSize: "0.75rem" }}
                >
                  ✕
                </ButtonBase>
              </Stack>
              <Typography variant="caption" color="text.secondary" display="block" noWrap sx={{ mb: 1.5 }}>
                {row.company_name}
              </Typography>

              <Stack spacing={0.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">Current</Typography>
                  <Typography variant="caption" fontFamily="monospace">{fmt(row.current_price, 2, "$")}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">Predicted</Typography>
                  <Typography variant="caption" fontFamily="monospace">{fmt(row.predicted_price, 2, "$")}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">Return</Typography>
                  <Typography variant="caption" fontFamily="monospace" fontWeight={600} color={returnColor}>
                    {returnPct > 0 ? "+" : ""}{returnPct.toFixed(2)}%
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">Confidence</Typography>
                  <Typography variant="caption" fontFamily="monospace">{fmt(row.confidence, 2)}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption" color="text.secondary">Trend</Typography>
                  <Chip
                    label={`${trendIcon(row.trend)} ${row.trend}`}
                    color={trendChipColor as "success" | "error" | "default"}
                    size="small"
                    sx={{ height: 18, fontSize: "0.65rem" }}
                  />
                </Stack>
              </Stack>

              <Button
                fullWidth
                size="small"
                variant="outlined"
                color="primary"
                onClick={() => onSelectDetail(row.ticker)}
                sx={{ mt: 1.5 }}
              >
                View Detail
              </Button>
            </Paper>
          );
        })}
      </Box>
    </Paper>
  );
}
