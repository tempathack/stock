import type { MarketOverviewEntry, CandlePoint } from "@/api";

const MOCK_STOCKS: Array<{
  ticker: string;
  name: string;
  sector: string;
  price: number;
  marketCap: number;
}> = [
  // Technology
  { ticker: "AAPL",  name: "Apple Inc.",              sector: "Technology",             price: 252.62, marketCap: 3_800_000_000_000 },
  { ticker: "MSFT",  name: "Microsoft Corp.",         sector: "Technology",             price: 358.06, marketCap: 3_100_000_000_000 },
  { ticker: "NVDA",  name: "NVIDIA Corp.",            sector: "Technology",             price: 164.56, marketCap: 4_020_000_000_000 },
  { ticker: "GOOGL", name: "Alphabet Inc.",           sector: "Technology",             price: 290.93, marketCap: 1_780_000_000_000 },
  { ticker: "META",  name: "Meta Platforms",          sector: "Technology",             price: 534.07, marketCap: 1_350_000_000_000 },
  { ticker: "AVGO",  name: "Broadcom Inc.",           sector: "Technology",             price: 195.40, marketCap: 910_000_000_000 },
  { ticker: "ORCL",  name: "Oracle Corp.",            sector: "Technology",             price: 172.30, marketCap: 475_000_000_000 },
  { ticker: "CRM",   name: "Salesforce Inc.",         sector: "Technology",             price: 287.50, marketCap: 278_000_000_000 },
  { ticker: "AMD",   name: "Advanced Micro Devices",  sector: "Technology",             price: 121.80, marketCap: 197_000_000_000 },
  { ticker: "INTC",  name: "Intel Corp.",             sector: "Technology",             price: 21.40,  marketCap: 91_000_000_000 },
  // Healthcare
  { ticker: "UNH",   name: "UnitedHealth Group",      sector: "Healthcare",             price: 261.10, marketCap: 487_000_000_000 },
  { ticker: "LLY",   name: "Eli Lilly & Co.",         sector: "Healthcare",             price: 798.40, marketCap: 758_000_000_000 },
  { ticker: "JNJ",   name: "Johnson & Johnson",       sector: "Healthcare",             price: 242.13, marketCap: 378_000_000_000 },
  { ticker: "ABBV",  name: "AbbVie Inc.",             sector: "Healthcare",             price: 207.18, marketCap: 366_000_000_000 },
  { ticker: "MRK",   name: "Merck & Co.",             sector: "Healthcare",             price: 98.70,  marketCap: 250_000_000_000 },
  { ticker: "TMO",   name: "Thermo Fisher",           sector: "Healthcare",             price: 512.30, marketCap: 196_000_000_000 },
  { ticker: "ABT",   name: "Abbott Laboratories",     sector: "Healthcare",             price: 132.40, marketCap: 230_000_000_000 },
  { ticker: "PFE",   name: "Pfizer Inc.",             sector: "Healthcare",             price: 27.68,  marketCap: 155_000_000_000 },
  // Financials
  { ticker: "JPM",   name: "JPMorgan Chase",          sector: "Financials",             price: 282.91, marketCap: 815_000_000_000 },
  { ticker: "V",     name: "Visa Inc.",               sector: "Financials",             price: 298.82, marketCap: 568_000_000_000 },
  { ticker: "MA",    name: "Mastercard Inc.",         sector: "Financials",             price: 492.51, marketCap: 460_000_000_000 },
  { ticker: "BAC",   name: "Bank of America",         sector: "Financials",             price: 48.75,  marketCap: 298_000_000_000 },
  { ticker: "WFC",   name: "Wells Fargo",             sector: "Financials",             price: 79.20,  marketCap: 262_000_000_000 },
  { ticker: "GS",    name: "Goldman Sachs",           sector: "Financials",             price: 582.40, marketCap: 196_000_000_000 },
  { ticker: "MS",    name: "Morgan Stanley",          sector: "Financials",             price: 132.60, marketCap: 217_000_000_000 },
  { ticker: "BLK",   name: "BlackRock Inc.",          sector: "Financials",             price: 1048.30, marketCap: 158_000_000_000 },
  // Consumer Discretionary
  { ticker: "AMZN",  name: "Amazon.com Inc.",         sector: "Consumer Discretionary", price: 211.71, marketCap: 2_240_000_000_000 },
  { ticker: "TSLA",  name: "Tesla Inc.",              sector: "Consumer Discretionary", price: 352.87, marketCap: 1_130_000_000_000 },
  { ticker: "HD",    name: "Home Depot",              sector: "Consumer Discretionary", price: 322.92, marketCap: 348_000_000_000 },
  { ticker: "MCD",   name: "McDonald's Corp.",        sector: "Consumer Discretionary", price: 298.50, marketCap: 217_000_000_000 },
  { ticker: "NKE",   name: "Nike Inc.",               sector: "Consumer Discretionary", price: 76.40,  marketCap: 114_000_000_000 },
  { ticker: "LOW",   name: "Lowe's Companies",        sector: "Consumer Discretionary", price: 241.80, marketCap: 134_000_000_000 },
  // Industrials
  { ticker: "GE",    name: "GE Aerospace",            sector: "Industrials",            price: 198.70, marketCap: 216_000_000_000 },
  { ticker: "HON",   name: "Honeywell Intl.",         sector: "Industrials",            price: 214.30, marketCap: 138_000_000_000 },
  { ticker: "CAT",   name: "Caterpillar Inc.",        sector: "Industrials",            price: 362.40, marketCap: 178_000_000_000 },
  { ticker: "BA",    name: "Boeing Co.",              sector: "Industrials",            price: 178.90, marketCap: 138_000_000_000 },
  { ticker: "RTX",   name: "RTX Corp.",               sector: "Industrials",            price: 134.60, marketCap: 178_000_000_000 },
  // Consumer Staples
  { ticker: "PG",    name: "Procter & Gamble",        sector: "Consumer Staples",       price: 144.88, marketCap: 382_000_000_000 },
  { ticker: "KO",    name: "Coca-Cola Co.",           sector: "Consumer Staples",       price: 71.40,  marketCap: 308_000_000_000 },
  { ticker: "PEP",   name: "PepsiCo Inc.",            sector: "Consumer Staples",       price: 148.20, marketCap: 204_000_000_000 },
  { ticker: "COST",  name: "Costco Wholesale",        sector: "Consumer Staples",       price: 1024.80, marketCap: 455_000_000_000 },
  { ticker: "WMT",   name: "Walmart Inc.",            sector: "Consumer Staples",       price: 98.40,  marketCap: 792_000_000_000 },
  // Energy
  { ticker: "XOM",   name: "Exxon Mobil Corp.",       sector: "Energy",                 price: 171.75, marketCap: 442_000_000_000 },
  { ticker: "CVX",   name: "Chevron Corp.",           sector: "Energy",                 price: 205.15, marketCap: 292_000_000_000 },
  { ticker: "COP",   name: "ConocoPhillips",          sector: "Energy",                 price: 108.30, marketCap: 128_000_000_000 },
  { ticker: "SLB",   name: "SLB (Schlumberger)",      sector: "Energy",                 price: 42.80,  marketCap: 61_000_000_000 },
  // Communication Services
  { ticker: "NFLX",  name: "Netflix Inc.",            sector: "Communication Services", price: 948.20, marketCap: 407_000_000_000 },
  { ticker: "DIS",   name: "Walt Disney Co.",         sector: "Communication Services", price: 112.30, marketCap: 206_000_000_000 },
  { ticker: "CMCSA", name: "Comcast Corp.",           sector: "Communication Services", price: 34.80,  marketCap: 141_000_000_000 },
  // Real Estate
  { ticker: "PLD",   name: "Prologis Inc.",           sector: "Real Estate",            price: 112.40, marketCap: 106_000_000_000 },
  { ticker: "AMT",   name: "American Tower",          sector: "Real Estate",            price: 198.60, marketCap: 93_000_000_000 },
  // Utilities
  { ticker: "NEE",   name: "NextEra Energy",          sector: "Utilities",              price: 68.90,  marketCap: 141_000_000_000 },
  { ticker: "DUK",   name: "Duke Energy Corp.",       sector: "Utilities",              price: 114.20, marketCap: 88_000_000_000 },
  // Materials
  { ticker: "LIN",   name: "Linde plc",              sector: "Materials",              price: 445.60, marketCap: 216_000_000_000 },
  { ticker: "APD",   name: "Air Products",            sector: "Materials",              price: 298.40, marketCap: 66_000_000_000 },
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
