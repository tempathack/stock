import type { MarketOverviewEntry } from "@/api";
import { Box, Skeleton, Typography } from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";

interface TopMoversPanelProps {
  stocks: MarketOverviewEntry[];
  loading?: boolean;
  onSelectTicker: (ticker: string) => void;
}

interface MoverRowProps {
  stock: MarketOverviewEntry;
  onSelect: (ticker: string) => void;
}

function MoverRow({ stock, onSelect }: MoverRowProps) {
  const pct = stock.daily_change_pct ?? 0;
  const isPos = pct >= 0;
  const color = isPos ? "#00FF87" : "#FF2D78";
  const glow = isPos ? "rgba(0,255,135,0.4)" : "rgba(255,45,120,0.4)";

  return (
    <Box
      onClick={() => onSelect(stock.ticker)}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        px: 1.5,
        py: 1,
        borderRadius: "10px",
        cursor: "pointer",
        transition: "background 0.12s ease",
        "&:hover": { background: "rgba(124,58,237,0.1)" },
      }}
    >
      <Typography
        sx={{
          fontFamily: '"Inter", sans-serif',
          fontWeight: 800,
          fontSize: "0.78rem",
          color: "#F0EEFF",
          width: 52,
          flexShrink: 0,
          letterSpacing: "0.02em",
        }}
      >
        {stock.ticker}
      </Typography>
      <Typography
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: "0.62rem",
          color: "rgba(107,96,168,0.65)",
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {stock.company_name ?? stock.ticker}
      </Typography>
      {stock.last_close != null && (
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.7rem",
            color: "rgba(240,238,255,0.55)",
            flexShrink: 0,
            width: 60,
            textAlign: "right",
          }}
        >
          ${stock.last_close.toFixed(2)}
        </Typography>
      )}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 0.4,
          width: 68,
          justifyContent: "flex-end",
          flexShrink: 0,
        }}
      >
        {isPos ? (
          <TrendingUpIcon sx={{ fontSize: "0.85rem", color }} />
        ) : (
          <TrendingDownIcon sx={{ fontSize: "0.85rem", color }} />
        )}
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontWeight: 700,
            fontSize: "0.75rem",
            color,
            textShadow: `0 0 8px ${glow}`,
          }}
        >
          {isPos ? "+" : ""}
          {pct.toFixed(2)}%
        </Typography>
      </Box>
    </Box>
  );
}

export default function TopMoversPanel({ stocks, loading, onSelectTicker }: TopMoversPanelProps) {
  const sorted = [...stocks]
    .filter((s) => s.daily_change_pct != null)
    .sort((a, b) => (b.daily_change_pct ?? 0) - (a.daily_change_pct ?? 0));

  const gainers = sorted.slice(0, 5);
  const losers = sorted.slice(-5).reverse();

  const skeletonRows = Array.from({ length: 5 });

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
        gap: 2,
        mb: 3,
      }}
    >
      {/* Top Gainers */}
      <Box
        sx={{
          background: "rgba(13,10,36,0.5)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(0,255,135,0.15)",
          borderRadius: "18px",
          p: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
          <Box
            sx={{
              width: 3,
              height: 18,
              borderRadius: "2px",
              background: "linear-gradient(180deg, #00FF87, transparent)",
              boxShadow: "0 0 8px rgba(0,255,135,0.5)",
              flexShrink: 0,
            }}
          />
          <TrendingUpIcon sx={{ color: "#00FF87", fontSize: "0.85rem" }} />
          <Typography
            sx={{
              fontFamily: '"Inter", sans-serif',
              fontWeight: 700,
              fontSize: "0.72rem",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "rgba(107,96,168,0.8)",
            }}
          >
            Top Gainers
          </Typography>
        </Box>
        {loading
          ? skeletonRows.map((_, i) => (
              <Skeleton
                key={i}
                variant="rectangular"
                height={36}
                sx={{ bgcolor: "rgba(0,255,135,0.04)", borderRadius: "10px", mb: 0.5 }}
              />
            ))
          : gainers.map((s) => (
              <MoverRow key={s.ticker} stock={s} onSelect={onSelectTicker} />
            ))}
      </Box>

      {/* Top Losers */}
      <Box
        sx={{
          background: "rgba(13,10,36,0.5)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255,45,120,0.15)",
          borderRadius: "18px",
          p: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
          <Box
            sx={{
              width: 3,
              height: 18,
              borderRadius: "2px",
              background: "linear-gradient(180deg, #FF2D78, transparent)",
              boxShadow: "0 0 8px rgba(255,45,120,0.5)",
              flexShrink: 0,
            }}
          />
          <TrendingDownIcon sx={{ color: "#FF2D78", fontSize: "0.85rem" }} />
          <Typography
            sx={{
              fontFamily: '"Inter", sans-serif',
              fontWeight: 700,
              fontSize: "0.72rem",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "rgba(107,96,168,0.8)",
            }}
          >
            Top Losers
          </Typography>
        </Box>
        {loading
          ? skeletonRows.map((_, i) => (
              <Skeleton
                key={i}
                variant="rectangular"
                height={36}
                sx={{ bgcolor: "rgba(255,45,120,0.04)", borderRadius: "10px", mb: 0.5 }}
              />
            ))
          : losers.map((s) => (
              <MoverRow key={s.ticker} stock={s} onSelect={onSelectTicker} />
            ))}
      </Box>
    </Box>
  );
}
