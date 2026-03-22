import type { ForecastRow } from "@/api";
import { deriveTrend } from "./forecastUtils";

const MOCK_TICKERS: Array<{
  ticker: string;
  name: string;
  sector: string;
  price: number;
}> = [
  { ticker: "AAPL", name: "Apple Inc.", sector: "Technology", price: 178.5 },
  { ticker: "MSFT", name: "Microsoft Corporation", sector: "Technology", price: 415.2 },
  { ticker: "GOOGL", name: "Alphabet Inc.", sector: "Technology", price: 141.8 },
  { ticker: "AMZN", name: "Amazon.com Inc.", sector: "Consumer Discretionary", price: 185.3 },
  { ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", price: 875.4 },
  { ticker: "META", name: "Meta Platforms Inc.", sector: "Technology", price: 505.6 },
  { ticker: "TSLA", name: "Tesla Inc.", sector: "Consumer Discretionary", price: 175.2 },
  { ticker: "JPM", name: "JPMorgan Chase", sector: "Financials", price: 198.7 },
  { ticker: "V", name: "Visa Inc.", sector: "Financials", price: 278.4 },
  { ticker: "JNJ", name: "Johnson & Johnson", sector: "Healthcare", price: 156.3 },
  { ticker: "UNH", name: "UnitedHealth Group", sector: "Healthcare", price: 527.8 },
  { ticker: "PG", name: "Procter & Gamble", sector: "Consumer Staples", price: 162.1 },
  { ticker: "XOM", name: "Exxon Mobil", sector: "Energy", price: 104.5 },
  { ticker: "CVX", name: "Chevron Corporation", sector: "Energy", price: 155.2 },
  { ticker: "HD", name: "Home Depot", sector: "Consumer Discretionary", price: 345.7 },
  { ticker: "PFE", name: "Pfizer Inc.", sector: "Healthcare", price: 27.4 },
  { ticker: "BAC", name: "Bank of America", sector: "Financials", price: 37.5 },
  { ticker: "DIS", name: "Walt Disney", sector: "Communication Services", price: 112.3 },
  { ticker: "NEE", name: "NextEra Energy", sector: "Utilities", price: 68.9 },
  { ticker: "LIN", name: "Linde plc", sector: "Materials", price: 445.6 },
];

/** Simple seeded PRNG (mulberry32). */
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

export function generateMockForecasts(): ForecastRow[] {
  const rng = seededRandom("forecasts_phase27");
  const today = new Date().toISOString().split("T")[0]!;
  const futureDate = new Date(Date.now() + 7 * 86400000)
    .toISOString()
    .split("T")[0]!;

  return MOCK_TICKERS.map(({ ticker, name, sector, price }) => {
    const returnPct = (rng() - 0.4) * 12; // ~-5% to +7%
    const predictedPrice = price * (1 + returnPct / 100);
    const confidence = 0.5 + rng() * 0.45; // 0.50 – 0.95
    const dailyChange = (rng() - 0.5) * 4; // -2% to +2%

    return {
      ticker,
      company_name: name,
      sector,
      current_price: price,
      predicted_price: Math.round(predictedPrice * 100) / 100,
      expected_return_pct: Math.round(returnPct * 100) / 100,
      confidence: Math.round(confidence * 100) / 100,
      daily_change_pct: Math.round(dailyChange * 100) / 100,
      trend: deriveTrend(returnPct),
      model_name: "Ridge_standard",
      prediction_date: today,
      predicted_date: futureDate,
    };
  });
}
