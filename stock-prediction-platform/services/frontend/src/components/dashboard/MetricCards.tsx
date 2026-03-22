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
    metrics.dailyChangePct >= 0 ? "text-profit" : "text-loss";
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
    <div>
      <div className="mb-3">
        <h3 className="text-xl font-bold text-text-primary">
          {metrics.companyName}
        </h3>
        <p className="text-sm text-text-secondary">{metrics.sector}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-lg border border-border bg-bg-card p-4"
          >
            <p className="text-xs uppercase tracking-wider text-text-secondary">
              {card.label}
            </p>
            <p
              className={`mt-1 text-lg font-semibold ${card.color ?? "text-text-primary"}`}
            >
              {card.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
