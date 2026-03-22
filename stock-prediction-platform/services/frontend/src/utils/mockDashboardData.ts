import type { MarketOverviewEntry, CandlePoint } from "@/api";

const MOCK_STOCKS: Array<{
  ticker: string;
  name: string;
  sector: string;
  price: number;
  marketCap: number;
}> = [
  { ticker: "AAPL",  name: "Apple Inc.",             sector: "Technology",             price: 178.50, marketCap: 2_800_000_000_000 },
  { ticker: "MSFT",  name: "Microsoft Corporation",  sector: "Technology",             price: 415.20, marketCap: 3_100_000_000_000 },
  { ticker: "GOOGL", name: "Alphabet Inc.",          sector: "Technology",             price: 141.80, marketCap: 1_780_000_000_000 },
  { ticker: "AMZN",  name: "Amazon.com Inc.",        sector: "Consumer Discretionary", price: 185.30, marketCap: 1_920_000_000_000 },
  { ticker: "NVDA",  name: "NVIDIA Corporation",     sector: "Technology",             price: 875.40, marketCap: 2_160_000_000_000 },
  { ticker: "META",  name: "Meta Platforms Inc.",     sector: "Technology",             price: 505.60, marketCap: 1_290_000_000_000 },
  { ticker: "TSLA",  name: "Tesla Inc.",             sector: "Consumer Discretionary", price: 175.20, marketCap: 556_000_000_000 },
  { ticker: "JPM",   name: "JPMorgan Chase",         sector: "Financials",             price: 198.70, marketCap: 572_000_000_000 },
  { ticker: "V",     name: "Visa Inc.",              sector: "Financials",             price: 278.40, marketCap: 568_000_000_000 },
  { ticker: "JNJ",   name: "Johnson & Johnson",      sector: "Healthcare",             price: 156.30, marketCap: 378_000_000_000 },
  { ticker: "UNH",   name: "UnitedHealth Group",     sector: "Healthcare",             price: 527.80, marketCap: 487_000_000_000 },
  { ticker: "PG",    name: "Procter & Gamble",       sector: "Consumer Staples",       price: 162.10, marketCap: 382_000_000_000 },
  { ticker: "XOM",   name: "Exxon Mobil",            sector: "Energy",                 price: 104.50, marketCap: 442_000_000_000 },
  { ticker: "CVX",   name: "Chevron Corporation",    sector: "Energy",                 price: 155.20, marketCap: 292_000_000_000 },
  { ticker: "HD",    name: "Home Depot",             sector: "Consumer Discretionary", price: 345.70, marketCap: 348_000_000_000 },
  { ticker: "PFE",   name: "Pfizer Inc.",            sector: "Healthcare",             price: 27.40,  marketCap: 155_000_000_000 },
  { ticker: "BAC",   name: "Bank of America",        sector: "Financials",             price: 37.50,  marketCap: 298_000_000_000 },
  { ticker: "DIS",   name: "Walt Disney",            sector: "Communication Services", price: 112.30, marketCap: 206_000_000_000 },
  { ticker: "NEE",   name: "NextEra Energy",         sector: "Utilities",              price: 68.90,  marketCap: 141_000_000_000 },
  { ticker: "LIN",   name: "Linde plc",             sector: "Materials",              price: 445.60, marketCap: 216_000_000_000 },
];

/** Seeded PRNG — same approach as mockForecastData.ts */
function seededRandom(seed: string): () => number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  }
  return () => {
    h |= 0;
    h = (h + 0x6d2b79f5) | 0;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Generate mock MarketOverviewEntry[] for treemap development.
 */
export function generateMockMarketOverview(): MarketOverviewEntry[] {
  const rng = seededRandom("dashboard_treemap_28");
  return MOCK_STOCKS.map(({ ticker, name, sector, price, marketCap }) => ({
    ticker,
    company_name: name,
    sector,
    market_cap: marketCap,
    last_close: price,
    daily_change_pct: Math.round((rng() - 0.45) * 8 * 100) / 100,
  }));
}

/**
 * Generate 390 mock minute-level candles (1 trading day = 6.5 h × 60 min).
 */
export function generateMockIntradayCandles(
  ticker: string,
  basePrice?: number,
): CandlePoint[] {
  const rng = seededRandom(`intraday_${ticker}`);
  const base = basePrice ?? 150;
  const candles: CandlePoint[] = [];
  let price = base;

  const today = new Date();
  const marketOpen = new Date(today);
  marketOpen.setHours(9, 30, 0, 0);

  for (let m = 0; m < 390; m++) {
    const time = new Date(marketOpen.getTime() + m * 60_000);
    const change = (rng() - 0.5) * 0.4;
    const open = price;
    const close = open * (1 + change / 100);
    const high = Math.max(open, close) * (1 + rng() * 0.1 / 100);
    const low = Math.min(open, close) * (1 - rng() * 0.1 / 100);
    const volume = Math.round(50_000 + rng() * 200_000);

    candles.push({
      date: time.toISOString(),
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume,
    });
    price = close;
  }
  return candles;
}
