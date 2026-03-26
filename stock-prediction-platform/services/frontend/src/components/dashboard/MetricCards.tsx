import { Box, Card, CardContent, Grid, Typography } from "@mui/material";
import type { StockMetrics } from "@/api";
import { formatMarketCap } from "@/utils/dashboardUtils";

interface MetricCardsProps {
  metrics: StockMetrics;
}

interface CardItem {
  label: string;
  value: string;
  color?: string;
}

export default function MetricCards({ metrics }: MetricCardsProps) {
  const priceColor =
    metrics.dailyChangePct >= 0 ? "success.main" : "error.main";
  const changeSign = metrics.dailyChangePct >= 0 ? "+" : "";

  const cards: CardItem[] = [
    {
      label: "Current Price",
      value: `$${metrics.currentPrice.toFixed(2)}`,
      color: priceColor,
    },
    {
      label: "Daily Change",
      value: `${changeSign}${metrics.dailyChangePct.toFixed(2)}%`,
      color: priceColor,
    },
    {
      label: "Market Cap",
      value: formatMarketCap(metrics.marketCap),
    },
    {
      label: "Volume (20d avg)",
      value: formatMarketCap(metrics.volume).replace("$", ""),
    },
    {
      label: "VWAP",
      value: metrics.vwap != null ? `$${metrics.vwap.toFixed(2)}` : "N/A",
    },
    {
      label: "52W Range",
      value:
        metrics.low52w != null && metrics.high52w != null
          ? `$${metrics.low52w.toFixed(0)} – $${metrics.high52w.toFixed(0)}`
          : "N/A",
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" fontWeight={700}>
          {metrics.companyName}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {metrics.sector}
        </Typography>
      </Box>
      <Grid container spacing={2}>
        {cards.map((card) => (
          <Grid size={{ xs: 6, sm: 4, lg: 2 }} key={card.label}>
            <Card>
              <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ textTransform: "uppercase", letterSpacing: "0.05em" }}
                >
                  {card.label}
                </Typography>
                <Typography
                  variant="h6"
                  sx={{
                    color: card.color ?? "text.primary",
                    fontFamily: "monospace",
                    mt: 0.5,
                    fontSize: "1rem",
                  }}
                >
                  {card.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
