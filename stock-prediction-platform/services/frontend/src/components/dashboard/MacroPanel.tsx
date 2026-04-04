/**
 * MacroPanel — Dashboard Macro Environment section.
 *
 * Displays a responsive 3-col / 2-col / 1-col grid of 9 macro indicator cards.
 * Each card shows: indicator label, formatted value + unit, colored status dot.
 * Auto-refreshes every 60 s via useMacroLatest (React Query).
 * Shows loading skeletons while fetching and graceful "—" for null values.
 */
import { Box, Grid, Skeleton, Typography } from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import RemoveIcon from "@mui/icons-material/Remove";
import { useMacroLatest } from "@/api";
import type { MacroLatest } from "@/api";

/* ── Indicator config ────────────────────────────────────── */

type FormatSpec = "0.2f" | "+0.2%" | "0.1f" | "+0.2f" | "0,0" | "0.3f";

interface IndicatorConfig {
  label: string;
  field: keyof MacroLatest;
  format: FormatSpec;
  unit: string;
  description: string;
  colorFn: (v: number | null) => "green" | "red" | "gray";
}

const MACRO_INDICATORS: IndicatorConfig[] = [
  {
    label: "VIX",
    field: "vix",
    format: "0.2f",
    unit: "",
    description: "Volatility Index",
    colorFn: (v) => {
      if (v == null) return "gray";
      if (v > 20) return "red";
      if (v < 15) return "green";
      return "gray";
    },
  },
  {
    label: "SPY Return",
    field: "spy_return",
    format: "+0.2%",
    unit: "",
    description: "S&P 500 daily return",
    colorFn: (v) => {
      if (v == null) return "gray";
      if (v > 0) return "green";
      if (v < 0) return "red";
      return "gray";
    },
  },
  {
    label: "10Y Yield",
    field: "dgs10",
    format: "0.2f",
    unit: "%",
    description: "10-Year Treasury",
    colorFn: () => "gray",
  },
  {
    label: "2-10 Spread",
    field: "t10y2y",
    format: "+0.2f",
    unit: "%",
    description: "Yield curve spread",
    colorFn: (v) => {
      if (v == null) return "gray";
      if (v < 0) return "red";
      if (v > 0.5) return "green";
      return "gray";
    },
  },
  {
    label: "HY Spread",
    field: "baml_hy_oas",
    format: "0.2f",
    unit: "%",
    description: "High yield OAS",
    colorFn: (v) => {
      if (v == null) return "gray";
      if (v > 500) return "red";
      if (v < 300) return "green";
      return "gray";
    },
  },
  {
    label: "WTI Crude",
    field: "wti_crude",
    format: "0.2f",
    unit: "$",
    description: "Oil price ($/bbl)",
    colorFn: () => "gray",
  },
  {
    label: "USD Index",
    field: "usd_broad",
    format: "0.1f",
    unit: "",
    description: "Broad dollar index",
    colorFn: () => "gray",
  },
  {
    label: "Initial Claims",
    field: "icsa",
    format: "0,0",
    unit: "K",
    description: "Weekly jobless claims",
    colorFn: () => "gray",
  },
  {
    label: "Core PCE",
    field: "core_pce",
    format: "0.3f",
    unit: " idx",
    description: "Fed inflation gauge",
    colorFn: () => "gray",
  },
];

/* ── Color palette ───────────────────────────────────────── */

const COLOR_MAP = {
  green: { dot: "#00FF87", glow: "rgba(0,255,135,0.5)", text: "#00FF87" },
  red: { dot: "#FF2D78", glow: "rgba(255,45,120,0.5)", text: "#FF2D78" },
  gray: { dot: "rgba(107,96,168,0.6)", glow: "transparent", text: "rgba(107,96,168,0.6)" },
};

/* ── Value formatter ─────────────────────────────────────── */

function formatValue(value: number | null, format: FormatSpec): string {
  if (value == null) return "—";

  switch (format) {
    case "0.2f":
      return value.toFixed(2);
    case "+0.2%": {
      const pct = value * 100;
      return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
    }
    case "0.1f":
      return value.toFixed(1);
    case "+0.2f":
      return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
    case "0,0":
      return Math.round(value).toLocaleString("en-US");
    case "0.3f":
      return value.toFixed(3);
    default:
      return String(value);
  }
}

/* ── Single indicator card ───────────────────────────────── */

interface IndicatorCardProps {
  config: IndicatorConfig;
  value: number | null;
}

function IndicatorCard({ config, value }: IndicatorCardProps) {
  const signal = config.colorFn(value);
  const colors = COLOR_MAP[signal];
  const formatted = formatValue(value, config.format);

  const isPositive = signal === "green";
  const isNegative = signal === "red";

  return (
    <Box
      sx={{
        background: "rgba(13,10,36,0.7)",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(124,58,237,0.18)",
        borderRadius: "12px",
        p: 2,
        display: "flex",
        flexDirection: "column",
        gap: 0.75,
        position: "relative",
        overflow: "hidden",
        transition: "border-color 0.2s ease",
        "&:hover": {
          borderColor: "rgba(124,58,237,0.35)",
        },
        "&::before": {
          content: '""',
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "2px",
          background: signal !== "gray"
            ? `linear-gradient(90deg, ${colors.dot}, transparent)`
            : "transparent",
        },
      }}
    >
      {/* Label row */}
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: "0.62rem",
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "rgba(107,96,168,0.7)",
          }}
        >
          {config.label}
        </Typography>

        {/* Status indicator */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          {isPositive && <TrendingUpIcon sx={{ fontSize: "0.85rem", color: colors.dot, filter: `drop-shadow(0 0 4px ${colors.glow})` }} />}
          {isNegative && <TrendingDownIcon sx={{ fontSize: "0.85rem", color: colors.dot, filter: `drop-shadow(0 0 4px ${colors.glow})` }} />}
          {!isPositive && !isNegative && <RemoveIcon sx={{ fontSize: "0.85rem", color: colors.dot }} />}
        </Box>
      </Box>

      {/* Value row */}
      <Box sx={{ display: "flex", alignItems: "baseline", gap: "3px" }}>
        <Typography
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontWeight: 700,
            fontSize: "1.2rem",
            letterSpacing: "-0.02em",
            color: value != null ? "#F0EEFF" : "rgba(107,96,168,0.4)",
            lineHeight: 1.1,
          }}
        >
          {formatted}
        </Typography>
        {value != null && config.unit && (
          <Typography
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.65rem",
              color: "rgba(107,96,168,0.6)",
              lineHeight: 1,
            }}
          >
            {config.unit}
          </Typography>
        )}
      </Box>

      {/* Description */}
      <Typography
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: "0.58rem",
          color: "rgba(107,96,168,0.45)",
          mt: "auto",
        }}
      >
        {config.description}
      </Typography>
    </Box>
  );
}

/* ── Loading skeleton ────────────────────────────────────── */

function MacroPanelSkeleton() {
  return (
    <Grid container spacing={1.5}>
      {Array.from({ length: 9 }).map((_, i) => (
        <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
          <Box
            sx={{
              background: "rgba(13,10,36,0.7)",
              border: "1px solid rgba(124,58,237,0.12)",
              borderRadius: "12px",
              p: 2,
            }}
          >
            <Skeleton variant="text" width="45%" sx={{ bgcolor: "rgba(124,58,237,0.08)", mb: 1 }} />
            <Skeleton variant="text" width="60%" height={32} sx={{ bgcolor: "rgba(124,58,237,0.06)" }} />
            <Skeleton variant="text" width="80%" sx={{ bgcolor: "rgba(124,58,237,0.05)", mt: 0.5 }} />
          </Box>
        </Grid>
      ))}
    </Grid>
  );
}

/* ── Main component ──────────────────────────────────────── */

export default function MacroPanel() {
  const { data, isLoading, isError } = useMacroLatest();

  return (
    <Box>
      {isLoading ? (
        <MacroPanelSkeleton />
      ) : isError ? (
        <Box
          sx={{
            py: 3,
            textAlign: "center",
            background: "rgba(13,10,36,0.5)",
            border: "1px solid rgba(124,58,237,0.12)",
            borderRadius: "12px",
          }}
        >
          <Typography
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.72rem",
              color: "rgba(107,96,168,0.5)",
            }}
          >
            Macro data unavailable
          </Typography>
          <Typography
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.62rem",
              color: "rgba(107,96,168,0.35)",
              mt: 0.5,
            }}
          >
            FRED & market data pipeline may be starting
          </Typography>
        </Box>
      ) : (
        <>
          <Grid container spacing={1.5}>
            {MACRO_INDICATORS.map((cfg) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={cfg.field}>
                <IndicatorCard
                  config={cfg}
                  value={data ? (data[cfg.field] as number | null) : null}
                />
              </Grid>
            ))}
          </Grid>

          {/* "As of" caption */}
          <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 1.5 }}>
            <Typography
              sx={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: "0.58rem",
                color: "rgba(107,96,168,0.4)",
              }}
            >
              {data?.as_of_date
                ? `As of ${data.as_of_date}`
                : "No date available"}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
}
