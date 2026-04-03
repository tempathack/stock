import { describe, it, expect } from "vitest";
import { joinMultiHorizonForecastData, deriveTrend } from "./forecastUtils";
import type { BulkPredictionResponse, MarketOverviewEntry } from "../api/types";

const makePred = (ticker: string, price: number, date: string) => ({
  ticker,
  prediction_date: "2026-04-03",
  predicted_date: date,
  predicted_price: price,
  model_name: "stacking_ensemble_meta_ridge",
  confidence: 0.85,
  horizon_days: null,
});

const makeStock = (ticker: string, lastClose: number): MarketOverviewEntry => ({
  ticker,
  company_name: `${ticker} Corp`,
  sector: "Technology",
  market_cap: 1_000_000,
  last_close: lastClose,
  daily_change_pct: 0.5,
});

const makeBulk = (
  horizon: number,
  preds: ReturnType<typeof makePred>[],
): { horizon: number; data: BulkPredictionResponse } => ({
  horizon,
  data: {
    predictions: preds,
    model_name: "stacking_ensemble_meta_ridge",
    generated_at: "2026-04-03T00:00:00Z",
    count: preds.length,
    horizon_days: horizon,
  },
});

describe("joinMultiHorizonForecastData", () => {
  it("merges two horizons into one row per ticker", () => {
    const input = [
      makeBulk(1, [makePred("AAPL", 180, "2026-04-04"), makePred("MSFT", 420, "2026-04-04")]),
      makeBulk(7, [makePred("AAPL", 180, "2026-04-10"), makePred("MSFT", 420, "2026-04-10")]),
    ];
    const stocks = [makeStock("AAPL", 175), makeStock("MSFT", 410)];
    const rows = joinMultiHorizonForecastData(input, stocks);
    expect(rows).toHaveLength(2);
    const aapl = rows.find((r) => r.ticker === "AAPL")!;
    expect(Object.keys(aapl.horizons)).toHaveLength(2);
    expect(aapl.horizons[1]).toBeDefined();
    expect(aapl.horizons[7]).toBeDefined();
  });

  it("includes row even if ticker is missing from one horizon", () => {
    const input = [
      makeBulk(1, [makePred("AAPL", 180, "2026-04-04")]),
      makeBulk(7, []),
    ];
    const stocks = [makeStock("AAPL", 175)];
    const rows = joinMultiHorizonForecastData(input, stocks);
    expect(rows).toHaveLength(1);
    expect(rows[0].horizons[1]).toBeDefined();
    expect(rows[0].horizons[7]).toBeUndefined();
  });

  it("calculates expected_return_pct correctly", () => {
    const input = [makeBulk(7, [makePred("AAPL", 182, "2026-04-10")])];
    const stocks = [makeStock("AAPL", 175)];
    const rows = joinMultiHorizonForecastData(input, stocks);
    const returnPct = rows[0].horizons[7].expected_return_pct;
    expect(returnPct).toBeCloseTo(((182 - 175) / 175) * 100, 4);
  });

  it("handles ticker with no market data — current_price null, expected_return_pct 0", () => {
    const input = [makeBulk(7, [makePred("XYZ", 50, "2026-04-10")])];
    const rows = joinMultiHorizonForecastData(input, []);
    expect(rows[0].current_price).toBeNull();
    expect(rows[0].horizons[7].expected_return_pct).toBe(0);
  });

  it("excludes ticker present in stocks but absent from all predictions (JNJ case)", () => {
    const input = [makeBulk(7, [makePred("AAPL", 180, "2026-04-10")])];
    const stocks = [makeStock("AAPL", 175), makeStock("JNJ", 150)];
    const rows = joinMultiHorizonForecastData(input, stocks);
    expect(rows.find((r) => r.ticker === "JNJ")).toBeUndefined();
  });

  it("derives trend correctly", () => {
    expect(deriveTrend(1.5)).toBe("bullish");
    expect(deriveTrend(-1.5)).toBe("bearish");
    expect(deriveTrend(0.5)).toBe("neutral");
  });
});
