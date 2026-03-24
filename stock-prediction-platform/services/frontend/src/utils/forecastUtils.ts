import type {
  PredictionResponse,
  MarketOverviewEntry,
  ForecastRow,
  TrendDirection,
} from "@/api";

/**
 * Derive trend from expected return: > +1% = bullish, < -1% = bearish, else neutral.
 */
export function deriveTrend(returnPct: number): TrendDirection {
  if (returnPct > 1) return "bullish";
  if (returnPct < -1) return "bearish";
  return "neutral";
}

/**
 * Join bulk predictions with market overview by ticker.
 * Returns enriched ForecastRow[] with computed expected_return_pct and trend.
 */
export function joinForecastData(
  predictions: PredictionResponse[],
  stocks: MarketOverviewEntry[],
): ForecastRow[] {
  const stockMap = new Map(stocks.map((s) => [s.ticker, s]));

  return predictions.map((pred) => {
    const stock = stockMap.get(pred.ticker);
    const currentPrice = stock?.last_close ?? null;
    const expectedReturn =
      currentPrice != null && currentPrice > 0
        ? ((pred.predicted_price - currentPrice) / currentPrice) * 100
        : 0;

    return {
      ticker: pred.ticker,
      company_name: stock?.company_name ?? null,
      sector: stock?.sector ?? null,
      current_price: currentPrice,
      predicted_price: pred.predicted_price,
      expected_return_pct: expectedReturn,
      confidence: pred.confidence,
      daily_change_pct: stock?.daily_change_pct ?? null,
      trend: deriveTrend(expectedReturn),
      model_name: pred.model_name,
      prediction_date: pred.prediction_date,
      predicted_date: pred.predicted_date,
      horizon_days: pred.horizon_days ?? null,
    };
  });
}

/**
 * Extract unique sorted sector names from forecast rows (excluding null).
 */
export function extractSectors(rows: ForecastRow[]): string[] {
  const sectors = new Set(
    rows.map((r) => r.sector).filter(Boolean) as string[],
  );
  return Array.from(sectors).sort();
}
