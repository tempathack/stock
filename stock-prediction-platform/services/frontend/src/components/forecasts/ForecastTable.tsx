import { useState, useMemo } from "react";
import type { ForecastRow } from "@/api";

type SortKey = keyof Pick<
  ForecastRow,
  | "ticker"
  | "company_name"
  | "sector"
  | "current_price"
  | "predicted_price"
  | "expected_return_pct"
  | "confidence"
  | "daily_change_pct"
>;

interface ForecastTableProps {
  rows: ForecastRow[];
  selectedTicker: string | null;
  comparisonTickers: string[];
  onSelectTicker: (ticker: string) => void;
  onToggleCompare: (ticker: string) => void;
}

const fmt = (n: number | null, decimals = 2, prefix = "") =>
  n != null ? `${prefix}${n.toFixed(decimals)}` : "—";

const pctClass = (v: number | null) =>
  v == null ? "text-text-secondary" : v > 0 ? "text-profit" : v < 0 ? "text-loss" : "text-text-secondary";

const trendBadge = (t: ForecastRow["trend"]) => {
  const map = {
    bullish: { icon: "▲", cls: "text-profit" },
    bearish: { icon: "▼", cls: "text-loss" },
    neutral: { icon: "—", cls: "text-text-secondary" },
  } as const;
  const { icon, cls } = map[t];
  return <span className={`text-xs font-semibold ${cls}`}>{icon} {t}</span>;
};

const COLUMNS: Array<{ key: SortKey; label: string; hideOnSm?: boolean }> = [
  { key: "ticker", label: "Ticker" },
  { key: "company_name", label: "Company", hideOnSm: true },
  { key: "sector", label: "Sector", hideOnSm: true },
  { key: "current_price", label: "Price" },
  { key: "predicted_price", label: "Predicted" },
  { key: "expected_return_pct", label: "Return %" },
  { key: "confidence", label: "Conf." },
  { key: "daily_change_pct", label: "Daily Δ" },
];

export default function ForecastTable({
  rows,
  selectedTicker,
  comparisonTickers,
  onSelectTicker,
  onToggleCompare,
}: ForecastTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("expected_return_pct");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-bg-surface p-8 text-center text-text-secondary">
        No forecasts match the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-bg-surface">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-bg-card/50">
            <th className="w-10 px-2 py-3 text-center">
              <span className="sr-only">Compare</span>
            </th>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className={`cursor-pointer select-none whitespace-nowrap px-3 py-3 text-xs font-medium uppercase tracking-wider text-text-secondary hover:text-text-primary ${
                  col.hideOnSm ? "hidden sm:table-cell" : ""
                }`}
                onClick={() => toggleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>
                )}
              </th>
            ))}
            <th className="px-3 py-3 text-xs font-medium uppercase tracking-wider text-text-secondary">
              Trend
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const isSelected = row.ticker === selectedTicker;
            const isCompare = comparisonTickers.includes(row.ticker);
            return (
              <tr
                key={row.ticker}
                onClick={() => onSelectTicker(row.ticker)}
                className={`cursor-pointer border-b border-border/50 transition-colors hover:bg-bg-card/40 ${
                  isSelected ? "border-l-2 border-l-accent bg-accent/10" : ""
                } ${isCompare && !isSelected ? "border-l-2 border-l-accent/50" : ""}`}
              >
                <td className="px-2 py-2 text-center">
                  <input
                    type="checkbox"
                    checked={isCompare}
                    onChange={(e) => {
                      e.stopPropagation();
                      onToggleCompare(row.ticker);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="accent-accent"
                  />
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-semibold text-accent">
                  {row.ticker}
                </td>
                <td className="hidden max-w-[180px] truncate px-3 py-2 text-text-secondary sm:table-cell">
                  {row.company_name ?? "—"}
                </td>
                <td className="hidden whitespace-nowrap px-3 py-2 text-text-secondary sm:table-cell">
                  {row.sector ?? "—"}
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-mono">
                  {fmt(row.current_price, 2, "$")}
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-mono">
                  {fmt(row.predicted_price, 2, "$")}
                </td>
                <td
                  className={`whitespace-nowrap px-3 py-2 font-mono font-semibold ${pctClass(row.expected_return_pct)}`}
                >
                  {row.expected_return_pct > 0 ? "+" : ""}
                  {row.expected_return_pct.toFixed(2)}%
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-mono text-text-secondary">
                  {fmt(row.confidence, 2)}
                </td>
                <td
                  className={`whitespace-nowrap px-3 py-2 font-mono text-xs ${pctClass(row.daily_change_pct)}`}
                >
                  {row.daily_change_pct != null
                    ? `${row.daily_change_pct > 0 ? "+" : ""}${row.daily_change_pct.toFixed(2)}%`
                    : "—"}
                </td>
                <td className="whitespace-nowrap px-3 py-2">{trendBadge(row.trend)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
