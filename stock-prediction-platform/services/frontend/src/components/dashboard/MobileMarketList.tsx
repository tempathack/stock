import type { TreemapSectorGroup } from "@/api";
import { changePctToColor } from "@/utils/dashboardUtils";

interface MobileMarketListProps {
  data: TreemapSectorGroup[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
}

export default function MobileMarketList({
  data,
  selectedTicker,
  onSelectTicker,
}: MobileMarketListProps) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-border bg-bg-surface p-8 text-center text-text-secondary">
        No market data available
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.map((sector) => (
        <div
          key={sector.name}
          className="rounded-lg border border-border bg-bg-surface"
        >
          <div className="border-b border-border px-3 py-2">
            <span className="text-xs font-bold uppercase tracking-wide text-text-secondary">
              {sector.name}
            </span>
          </div>
          <div className="divide-y divide-border/50">
            {sector.children.map((stock) => {
              const isSelected = stock.ticker === selectedTicker;
              const pct = stock.dailyChangePct ?? 0;
              return (
                <button
                  key={stock.ticker}
                  onClick={() => onSelectTicker(stock.ticker)}
                  className={`flex w-full items-center justify-between px-3 py-2 text-left transition-colors hover:bg-bg-card/40 ${
                    isSelected
                      ? "border-l-2 border-l-accent bg-accent/10"
                      : ""
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <span className="font-semibold text-accent">
                      {stock.ticker}
                    </span>
                    <span className="ml-2 truncate text-xs text-text-secondary">
                      {stock.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-right">
                    <span className="font-mono text-sm text-text-primary">
                      ${stock.lastClose.toFixed(2)}
                    </span>
                    <span
                      className="min-w-[60px] text-right font-mono text-xs font-semibold"
                      style={{ color: changePctToColor(pct) }}
                    >
                      {pct >= 0 ? "+" : ""}
                      {pct.toFixed(2)}%
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
