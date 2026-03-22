import type { IndicatorValues } from "@/api";

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

const round2 = (n: number) => Math.round(n * 100) / 100;

/**
 * Generate 90 days of mock indicator data for a given ticker.
 */
export function generateMockIndicatorSeries(
  ticker: string,
): IndicatorValues[] {
  const rng = seededRandom(ticker + "_indicators");
  const days = 90;
  let price = 100 + rng() * 400;

  return Array.from({ length: days }, (_, i) => {
    const date = new Date(Date.now() - (days - i) * 86400000)
      .toISOString()
      .split("T")[0]!;

    price *= 1 + (rng() - 0.48) * 0.03;
    const close = round2(price);
    const sma20 = close * (0.98 + rng() * 0.04);
    const sma50 = close * (0.96 + rng() * 0.08);
    const sma200 = close * (0.9 + rng() * 0.2);
    const ema12 = close * (0.99 + rng() * 0.02);
    const ema26 = close * (0.98 + rng() * 0.04);

    return {
      date,
      close,
      rsi_14: round2(30 + rng() * 40),
      macd_line: round2((rng() - 0.5) * 2),
      macd_signal: round2((rng() - 0.5) * 1.5),
      macd_histogram: round2((rng() - 0.5) * 1),
      stoch_k: round2(20 + rng() * 60),
      stoch_d: round2(20 + rng() * 60),
      sma_20: round2(sma20),
      sma_50: round2(sma50),
      sma_200: round2(sma200),
      ema_12: round2(ema12),
      ema_26: round2(ema26),
      adx: round2(15 + rng() * 35),
      bb_upper: round2(close * 1.04),
      bb_middle: round2(sma20),
      bb_lower: round2(close * 0.96),
      atr: round2(close * 0.015),
      rolling_volatility_21: round2(0.1 + rng() * 0.3),
      obv: Math.round(1000000 + rng() * 5000000),
      vwap: round2(close * (0.99 + rng() * 0.02)),
      volume_sma_20: Math.round(500000 + rng() * 2000000),
      ad_line: Math.round((rng() - 0.5) * 1000000),
      return_1d: round2((rng() - 0.5) * 4),
      return_5d: round2((rng() - 0.5) * 8),
      return_21d: round2((rng() - 0.5) * 15),
      log_return: round2((rng() - 0.5) * 0.04),
    };
  });
}
