import type {
  PredictionResponse,
  MarketOverviewEntry,
  ForecastRow,
  TrendDirection,
  MultiHorizonForecastRow,
  HorizonPrediction,
  BulkPredictionResponse,
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

/**
 * Merge per-horizon bulk prediction results into one row per ticker.
 * Input: array of { horizon: number; data: BulkPredictionResponse }
 * Output: MultiHorizonForecastRow[] — one row per ticker that appears in at least one horizon.
 * Tickers in market overview but absent from all predictions are NOT included.
 */
export function joinMultiHorizonForecastData(
  horizonResults: Array<{ horizon: number; data: BulkPredictionResponse }>,
  stocks: MarketOverviewEntry[],
): MultiHorizonForecastRow[] {
  const stockMap = new Map(stocks.map((s) => [s.ticker, s]));

  // Build ticker → { horizonDays → PredictionResponse } map
  const tickerHorizonMap = new Map<string, Record<number, PredictionResponse>>();
  for (const { horizon, data } of horizonResults) {
    for (const pred of data.predictions) {
      if (!tickerHorizonMap.has(pred.ticker)) {
        tickerHorizonMap.set(pred.ticker, {});
      }
      tickerHorizonMap.get(pred.ticker)![horizon] = pred;
    }
  }

  // Emit one row per ticker that appeared in at least one horizon prediction
  const rows: MultiHorizonForecastRow[] = [];
  for (const [ticker, horizonPreds] of tickerHorizonMap) {
    const stock = stockMap.get(ticker);
    const currentPrice = stock?.last_close ?? null;
    const horizons: MultiHorizonForecastRow["horizons"] = {};

    for (const [hStr, pred] of Object.entries(horizonPreds)) {
      const hNum = Number(hStr);
      const expectedReturn =
        currentPrice != null && currentPrice > 0
          ? ((pred.predicted_price - currentPrice) / currentPrice) * 100
          : 0;
      const hp: HorizonPrediction = {
        predicted_price: pred.predicted_price,
        expected_return_pct: expectedReturn,
        confidence: pred.confidence,
        predicted_date: pred.predicted_date,
        trend: deriveTrend(expectedReturn),
      };
      horizons[hNum] = hp;
    }

    const firstPred = Object.values(horizonPreds)[0];
    rows.push({
      ticker,
      company_name: stock?.company_name ?? null,
      sector: stock?.sector ?? null,
      current_price: currentPrice,
      daily_change_pct: stock?.daily_change_pct ?? null,
      horizons,
      model_name: firstPred?.model_name ?? "unknown",
    });
  }

  return rows;
}
