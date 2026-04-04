/**
 * MacroChart — Interactive 90-day FRED macro timeseries chart.
 *
 * Shows selected FRED indicators over time using Recharts LineChart.
 * Series picker via MUI Chip row — default: dgs10, t10y2y, dcoilwtico.
 */
import { useState } from "react";
import { Box, Chip, Skeleton, Typography } from "@mui/material";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useMacroHistory } from "@/hooks/useMacroHistory";
import type { MacroHistoryPoint } from "@/api/types";

/* ── Series config ───────────────────────────────────────── */

interface SeriesConfig {
  key: keyof Omit<MacroHistoryPoint, "as_of_date">;
  label: string;
  color: string;
  unit: string;
}

const SERIES_CONFIG: SeriesConfig[] = [
  { key: "dgs10",        label: "10Y Yield",      color: "#4fc3f7", unit: "%" },
  { key: "t10y2y",       label: "2-10 Spread",    color: "#f06292", unit: "%" },
  { key: "dgs2",         label: "2Y Yield",        color: "#81c784", unit: "%" },
  { key: "bamlh0a0hym2", label: "HY Spread",      color: "#ffb74d", unit: "bps" },
  { key: "dcoilwtico",   label: "WTI Crude",      color: "#ce93d8", unit: "$" },
  { key: "icsa",         label: "Jobless Claims",  color: "#80cbc4", unit: "K" },
];

const DEFAULT_SELECTED = new Set<string>(["dgs10", "t10y2y", "dcoilwtico"]);

/* ── X-axis date formatter — every 2 weeks ───────────────── */

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function shouldShowTick(dateStr: string): boolean {
  const d = new Date(dateStr);
  const day = d.getDate();
  // Show first occurrence of every ~14-day interval
  return day === 1 || day === 15;
}

/* ── Custom tooltip ──────────────────────────────────────── */

interface TooltipPayloadItem {
  dataKey: string;
  value: number | null;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
  selectedKeys: Set<string>;
}

function CustomTooltip({ active, payload, label, selectedKeys }: CustomTooltipProps) {
  if (!active || !payload || !label) return null;

  const activePayload = payload.filter((p) => selectedKeys.has(p.dataKey));
  if (activePayload.length === 0) return null;

  return (
    <Box
      sx={{
        background: "rgba(13,10,36,0.92)",
        border: "1px solid rgba(124,58,237,0.3)",
        borderRadius: "8px",
        p: 1.5,
        minWidth: 160,
      }}
    >
      <Typography
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: "0.62rem",
          color: "rgba(107,96,168,0.7)",
          mb: 0.75,
        }}
      >
        {formatDate(label)}
      </Typography>
      {activePayload.map((item) => {
        const cfg = SERIES_CONFIG.find((s) => s.key === item.dataKey);
        if (!cfg) return null;
        return (
          <Box key={item.dataKey} sx={{ display: "flex", justifyContent: "space-between", gap: 2, mb: 0.25 }}>
            <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.65rem", color: item.color }}>
              {cfg.label}
            </Typography>
            <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.65rem", color: "#F0EEFF" }}>
              {item.value != null ? `${item.value.toFixed(2)} ${cfg.unit}` : "—"}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
}

/* ── Main component ──────────────────────────────────────── */

export default function MacroChart() {
  const [selected, setSelected] = useState<Set<string>>(DEFAULT_SELECTED);
  const { data, loading, error } = useMacroHistory(90);

  function toggleSeries(key: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key); // keep at least 1 selected
      } else {
        next.add(key);
      }
      return next;
    });
  }

  // Filter X-axis ticks to show every ~2 weeks
  const tickDates = data
    .map((d) => d.as_of_date)
    .filter(shouldShowTick);

  if (loading) {
    return <Skeleton variant="rectangular" height={300} sx={{ borderRadius: "12px", bgcolor: "rgba(124,58,237,0.06)" }} />;
  }

  if (error) {
    return (
      <Box
        sx={{
          height: 300,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(13,10,36,0.5)",
          border: "1px solid rgba(124,58,237,0.12)",
          borderRadius: "12px",
        }}
      >
        <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.72rem", color: "rgba(107,96,168,0.5)" }}>
          Chart data unavailable
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Series picker */}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, mb: 2 }}>
        {SERIES_CONFIG.map((cfg) => (
          <Chip
            key={cfg.key}
            label={cfg.label}
            size="small"
            onClick={() => toggleSeries(cfg.key)}
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.62rem",
              height: 24,
              bgcolor: selected.has(cfg.key) ? `${cfg.color}22` : "rgba(13,10,36,0.6)",
              border: `1px solid ${selected.has(cfg.key) ? cfg.color : "rgba(124,58,237,0.2)"}`,
              color: selected.has(cfg.key) ? cfg.color : "rgba(107,96,168,0.6)",
              cursor: "pointer",
              "&:hover": {
                bgcolor: `${cfg.color}33`,
              },
            }}
          />
        ))}
      </Box>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(124,58,237,0.1)" />
          <XAxis
            dataKey="as_of_date"
            ticks={tickDates}
            tickFormatter={formatDate}
            tick={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10, fill: "rgba(107,96,168,0.6)" }}
            axisLine={{ stroke: "rgba(124,58,237,0.2)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10, fill: "rgba(107,96,168,0.6)" }}
            axisLine={false}
            tickLine={false}
            width={40}
          />
          <Tooltip
            content={<CustomTooltip selectedKeys={selected} />}
          />
          <Legend
            wrapperStyle={{ fontFamily: '"JetBrains Mono", monospace', fontSize: "0.65rem" }}
          />
          {SERIES_CONFIG.filter((cfg) => selected.has(cfg.key)).map((cfg) => (
            <Line
              key={cfg.key}
              type="monotone"
              dataKey={cfg.key}
              stroke={cfg.color}
              strokeWidth={2}
              dot={false}
              name={cfg.label}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}
