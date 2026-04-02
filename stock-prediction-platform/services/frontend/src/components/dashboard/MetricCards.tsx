import { Box, Grid, Typography } from "@mui/material";
import type { StockMetrics } from "@/api";
import { formatMarketCap } from "@/utils/dashboardUtils";

interface MetricCardsProps {
  metrics: StockMetrics;
}

interface CardItem {
  label: string;
  value: string;
  color?: string;
  glow?: string;
  accent?: string;
}

const CARD_ACCENTS = [
  { bg: "rgba(124,58,237,0.08)",  border: "rgba(124,58,237,0.35)",  glow: "rgba(124,58,237,0.2)" },
  { bg: "rgba(0,245,255,0.06)",   border: "rgba(0,245,255,0.3)",    glow: "rgba(0,245,255,0.15)" },
  { bg: "rgba(191,90,242,0.07)",  border: "rgba(191,90,242,0.32)",  glow: "rgba(191,90,242,0.18)" },
  { bg: "rgba(255,214,10,0.06)",  border: "rgba(255,214,10,0.28)",  glow: "rgba(255,214,10,0.14)" },
  { bg: "rgba(0,245,255,0.06)",   border: "rgba(0,245,255,0.3)",    glow: "rgba(0,245,255,0.15)" },
  { bg: "rgba(236,72,153,0.07)",  border: "rgba(236,72,153,0.3)",   glow: "rgba(236,72,153,0.15)" },
];

export default function MetricCards({ metrics }: MetricCardsProps) {
  const isPositive = metrics.dailyChangePct >= 0;
  const priceColor = isPositive ? "#00FF87" : "#FF2D78";
  const priceGlow  = isPositive ? "rgba(0,255,135,0.5)" : "rgba(255,45,120,0.5)";
  const changeSign = isPositive ? "+" : "";

  const cards: CardItem[] = [
    {
      label: "Current Price",
      value: `$${metrics.currentPrice.toFixed(2)}`,
      color: priceColor,
      glow:  priceGlow,
    },
    {
      label: "Daily Change",
      value: `${changeSign}${metrics.dailyChangePct.toFixed(2)}%`,
      color: priceColor,
      glow:  priceGlow,
    },
    {
      label: "Market Cap",
      value: formatMarketCap(metrics.marketCap),
      color: "#BF5AF2",
      glow:  "rgba(191,90,242,0.5)",
    },
    {
      label: "Volume (20d avg)",
      value: formatMarketCap(metrics.volume).replace("$", ""),
      color: "#FFD60A",
      glow:  "rgba(255,214,10,0.5)",
    },
    {
      label: "VWAP",
      value: metrics.vwap != null ? `$${metrics.vwap.toFixed(2)}` : "N/A",
      color: "#00F5FF",
      glow:  "rgba(0,245,255,0.5)",
    },
    {
      label: "52W Range",
      value:
        metrics.low52w != null && metrics.high52w != null
          ? `$${metrics.low52w.toFixed(0)} – $${metrics.high52w.toFixed(0)}`
          : "N/A",
      color: "#EC4899",
      glow:  "rgba(236,72,153,0.5)",
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 2.5 }}>
        <Typography
          variant="h6"
          sx={{
            fontFamily: '"Inter", sans-serif',
            fontWeight: 800,
            fontSize: "1.1rem",
            background: "linear-gradient(90deg, #F0EEFF, #BF5AF2)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          {metrics.companyName}
        </Typography>
        <Typography
          variant="body2"
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.68rem",
            color: "#6B60A8",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            mt: 0.25,
          }}
        >
          {metrics.sector}
        </Typography>
      </Box>

      <Grid container spacing={1.5}>
        {cards.map((card, i) => {
          const accent = CARD_ACCENTS[i % CARD_ACCENTS.length]!;
          return (
            <Grid size={{ xs: 6, sm: 4, lg: 2 }} key={card.label}>
              <Box
                sx={{
                  background: accent.bg,
                  backdropFilter: "blur(16px)",
                  border: `1px solid ${accent.border}`,
                  borderRadius: "14px",
                  p: "14px 16px",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease",
                  cursor: "default",
                  "&:hover": {
                    transform: "translateY(-2px)",
                    boxShadow: `0 0 24px ${accent.glow}, 0 8px 24px rgba(0,0,0,0.3)`,
                  },
                }}
              >
                <Typography
                  sx={{
                    fontFamily: '"Inter", sans-serif',
                    fontWeight: 600,
                    fontSize: "0.6rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "#6B60A8",
                    mb: 0.75,
                  }}
                >
                  {card.label}
                </Typography>
                <Typography
                  sx={{
                    fontFamily: '"JetBrains Mono", monospace',
                    fontWeight: 600,
                    fontSize: "1rem",
                    color: card.color ?? "#F0EEFF",
                    textShadow: card.glow ? `0 0 10px ${card.glow}` : "none",
                    lineHeight: 1.2,
                  }}
                >
                  {card.value}
                </Typography>
              </Box>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
