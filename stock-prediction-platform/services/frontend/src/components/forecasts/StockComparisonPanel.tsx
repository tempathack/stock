import type { ForecastRow } from "@/api";

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

const trendColor = (t: ForecastRow["trend"]) =>
  t === "bullish" ? "text-profit" : t === "bearish" ? "text-loss" : "text-text-secondary";

export default function StockComparisonPanel({
  rows,
  comparisonTickers,
  onRemove,
  onSelectDetail,
}: StockComparisonPanelProps) {
  if (comparisonTickers.length < 2) {
    return (
      <p className="mt-4 text-center text-sm text-text-secondary">
        Select 2+ stocks in the table to compare side by side.
      </p>
    );
  }

  const selected = comparisonTickers
    .map((t) => rows.find((r) => r.ticker === t))
    .filter(Boolean) as ForecastRow[];

  return (
    <div className="mt-4 rounded-lg border border-border bg-bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">
          Comparing {selected.length} stocks
        </h3>
        <button
          onClick={() => comparisonTickers.forEach(onRemove)}
          className="text-xs text-text-secondary transition-colors hover:text-loss"
        >
          Clear all
        </button>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-2">
        {selected.map((row) => (
          <div
            key={row.ticker}
            className="min-w-[220px] shrink-0 rounded-lg border border-border bg-bg-card p-4"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-semibold text-accent">{row.ticker}</span>
              <button
                onClick={() => onRemove(row.ticker)}
                className="text-text-secondary transition-colors hover:text-loss"
                aria-label={`Remove ${row.ticker}`}
              >
                ✕
              </button>
            </div>
            <p className="mb-3 truncate text-xs text-text-secondary">
              {row.company_name}
            </p>

            <dl className="space-y-1 text-xs">
              <div className="flex justify-between">
                <dt className="text-text-secondary">Current</dt>
                <dd className="font-mono">{fmt(row.current_price, 2, "$")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-text-secondary">Predicted</dt>
                <dd className="font-mono">{fmt(row.predicted_price, 2, "$")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-text-secondary">Return</dt>
                <dd
                  className={`font-mono font-semibold ${
                    row.expected_return_pct > 0
                      ? "text-profit"
                      : row.expected_return_pct < 0
                        ? "text-loss"
                        : "text-text-secondary"
                  }`}
                >
                  {row.expected_return_pct > 0 ? "+" : ""}
                  {row.expected_return_pct.toFixed(2)}%
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-text-secondary">Confidence</dt>
                <dd className="font-mono">{fmt(row.confidence, 2)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-text-secondary">Trend</dt>
                <dd className={trendColor(row.trend)}>
                  {trendIcon(row.trend)} {row.trend}
                </dd>
              </div>
            </dl>

            <button
              onClick={() => onSelectDetail(row.ticker)}
              className="mt-3 w-full rounded bg-accent/20 py-1 text-xs font-medium text-accent transition-colors hover:bg-accent/30"
            >
              View Detail
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
