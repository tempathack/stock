import type {
  MarketOverviewEntry,
  TreemapCell,
  TreemapSectorGroup,
  StockMetrics,
  IndicatorValues,
} from "@/api";

/**
 * Convert flat market overview entries into nested sector → stock tree
 * for Recharts Treemap consumption.
 */
export function buildTreemapData(
  stocks: MarketOverviewEntry[],
): TreemapSectorGroup[] {
  const sectorMap = new Map<string, TreemapCell[]>();

  for (const s of stocks) {
    const sector = s.sector ?? "Other";
    const cell: TreemapCell = {
      ticker: s.ticker,
      name: s.company_name ?? s.ticker,
      sector,
      marketCap: s.market_cap ?? 0,
      dailyChangePct: s.daily_change_pct ?? 0,
      lastClose: s.last_close ?? 0,
    };
    if (!sectorMap.has(sector)) sectorMap.set(sector, []);
    sectorMap.get(sector)!.push(cell);
  }

  return Array.from(sectorMap.entries())
    .map(([name, children]) => ({ name, children }))
    .sort((a, b) => {
      const aTotal = a.children.reduce((sum, c) => sum + c.marketCap, 0);
      const bTotal = b.children.reduce((sum, c) => sum + c.marketCap, 0);
      return bTotal - aTotal;
    });
}

/**
 * Map a daily change percentage to a hex colour.
 * Clamped at ±3%. Neutral → deep navy, gain → neon cyan, loss → bright purple.
 */
export function changePctToColor(pct: number): string {
  const MAX = 3;
  const clamped = Math.max(-MAX, Math.min(MAX, pct));
  if (clamped >= 0) {
    const t = clamped / MAX;
    return lerpColor("#110C2E", "#00C2D4", t);
  }
  const t = Math.abs(clamped) / MAX;
  return lerpColor("#110C2E", "#8B2FC9", t);
}

function lerpColor(a: string, b: string, t: number): string {
  const parse = (hex: string): [number, number, number] => [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
  const [r1, g1, b1] = parse(a);
  const [r2, g2, b2] = parse(b);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const bl = Math.round(b1 + (b2 - b1) * t);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${bl.toString(16).padStart(2, "0")}`;
}

/**
 * Derive key metric card data from market overview + indicator series.
 */
export function deriveStockMetrics(
  stock: MarketOverviewEntry,
  series: IndicatorValues[],
): StockMetrics {
  const closes = series
    .map((s) => s.close)
    .filter((c): c is number => c != null);
  const high52w = closes.length > 0 ? Math.max(...closes) : null;
  const low52w = closes.length > 0 ? Math.min(...closes) : null;
  const latest = series.length > 0 ? series[series.length - 1] : null;

  return {
    ticker: stock.ticker,
    companyName: stock.company_name ?? stock.ticker,
    sector: stock.sector ?? "Unknown",
    currentPrice: stock.last_close ?? 0,
    dailyChangePct: stock.daily_change_pct ?? 0,
    marketCap: stock.market_cap ?? 0,
    volume: latest?.volume_sma_20 ?? 0,
    vwap: latest?.vwap ?? null,
    high52w,
    low52w,
  };
}

/**
 * Format large numbers with B/M/K suffixes.
 */
export function formatMarketCap(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}
