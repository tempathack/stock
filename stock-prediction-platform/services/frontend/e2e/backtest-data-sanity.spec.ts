/**
 * Backtest Data Sanity Tests
 *
 * These tests intercept the live /backtest API response and assert that the
 * values returned (and rendered) are numerically sane. They are diagnostic —
 * failures print the raw API payload so the ML pipeline bug is immediately
 * visible without opening DevTools.
 */
import { test, expect } from "@playwright/test";

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

async function isApiHealthy(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_API_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

function mean(values: number[]): number {
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function stdDev(values: number[]): number {
  const m = mean(values);
  return Math.sqrt(values.reduce((a, b) => a + (b - m) ** 2, 0) / values.length);
}

test.describe("Backtest API data sanity", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async () => {
    const healthy = await isApiHealthy();
    test.skip(!healthy, "API not reachable — skipping sanity checks");
  });

  test("RMSE is not dollar-scale (< 20% of mean actual price)", async ({ page }) => {
    // Intercept the backtest response before navigating
    const responsePromise = page.waitForResponse(
      (res) =>
        res.url().includes(BASE_API_URL) &&
        res.url().includes("/backtest/") &&
        res.status() === 200,
      { timeout: 30_000 },
    );

    await page.goto("/backtest");
    await page.getByRole("button", { name: /Run Backtest/i }).waitFor({ timeout: 15_000 });
    await page.getByRole("button", { name: /Run Backtest/i }).click();

    const response = await responsePromise;
    const data = await response.json();

    const { metrics, series } = data;
    const actualPrices: number[] = series.map((p: { actual_price: number }) => p.actual_price);
    const meanPrice = mean(actualPrices);

    console.log(`\n[backtest sanity] ticker=${data.ticker} horizon=${data.horizon}d`);
    console.log(`[backtest sanity] total_points=${metrics.total_points}`);
    console.log(`[backtest sanity] mean actual price: $${meanPrice.toFixed(2)}`);
    console.log(`[backtest sanity] RMSE: ${metrics.rmse}`);
    console.log(`[backtest sanity] MAE:  ${metrics.mae}`);
    console.log(`[backtest sanity] MAPE: ${metrics.mape}%`);
    console.log(`[backtest sanity] R²:   ${metrics.r2}`);
    console.log(`[backtest sanity] Dir.Acc: ${metrics.directional_accuracy}`);

    const threshold = 0.2 * meanPrice;
    expect(
      metrics.rmse,
      `RMSE=${metrics.rmse.toFixed(4)} is > 20% of mean price $${meanPrice.toFixed(2)} (threshold=$${threshold.toFixed(2)}). ` +
      `The model is likely predicting on un-normalized/raw prices instead of log-returns or scaled features.`,
    ).toBeLessThan(threshold);
  });

  test("Directional accuracy is between 0% and 100%", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes(BASE_API_URL) && res.url().includes("/backtest/") && res.status() === 200,
      { timeout: 30_000 },
    );

    await page.goto("/backtest");
    await page.getByRole("button", { name: /Run Backtest/i }).waitFor({ timeout: 15_000 });
    await page.getByRole("button", { name: /Run Backtest/i }).click();

    const response = await responsePromise;
    const data = await response.json();
    const da = data.metrics.directional_accuracy;

    console.log(`\n[backtest sanity] raw directional_accuracy from API: ${da}`);

    expect(
      da,
      `directional_accuracy=${da} is not in [0, 100]. ` +
      `If the value is > 100, the API is returning a fraction (0–1) but the component renders it as-is with a % suffix, ` +
      `or vice-versa.`,
    ).toBeGreaterThanOrEqual(0);

    expect(
      da,
      `directional_accuracy=${da} exceeds 100. ` +
      `If it should be a fraction (0–1), multiply by 100 before displaying.`,
    ).toBeLessThanOrEqual(100);
  });

  test("Predicted prices are not constant (model outputs vary)", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes(BASE_API_URL) && res.url().includes("/backtest/") && res.status() === 200,
      { timeout: 30_000 },
    );

    await page.goto("/backtest");
    await page.getByRole("button", { name: /Run Backtest/i }).waitFor({ timeout: 15_000 });
    await page.getByRole("button", { name: /Run Backtest/i }).click();

    const response = await responsePromise;
    const data = await response.json();
    const series = data.series as Array<{ predicted_price: number; actual_price: number }>;

    const predicted = series.map((p) => p.predicted_price);
    const actual = series.map((p) => p.actual_price);
    const meanActual = mean(actual);
    const sdPredicted = stdDev(predicted);
    const minPred = Math.min(...predicted);
    const maxPred = Math.max(...predicted);

    console.log(`\n[backtest sanity] predicted price range: $${minPred.toFixed(2)} – $${maxPred.toFixed(2)}`);
    console.log(`[backtest sanity] predicted std dev: ${sdPredicted.toFixed(4)}`);
    console.log(`[backtest sanity] mean actual price: $${meanActual.toFixed(2)}`);

    const minAllowedStdDev = 0.01 * meanActual; // 1% of mean price
    expect(
      sdPredicted,
      `Predicted prices std dev=${sdPredicted.toFixed(4)} is < 1% of mean actual price ($${meanActual.toFixed(2)}). ` +
      `Min predicted=$${minPred.toFixed(2)}, max predicted=$${maxPred.toFixed(2)}. ` +
      `The model appears to be outputting near-constant predictions for all dates.`,
    ).toBeGreaterThan(minAllowedStdDev);
  });

  test("Series contains no NaN or null price values", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes(BASE_API_URL) && res.url().includes("/backtest/") && res.status() === 200,
      { timeout: 30_000 },
    );

    await page.goto("/backtest");
    await page.getByRole("button", { name: /Run Backtest/i }).waitFor({ timeout: 15_000 });
    await page.getByRole("button", { name: /Run Backtest/i }).click();

    const response = await responsePromise;
    const data = await response.json();
    const series = data.series as Array<{ date: string; actual_price: number; predicted_price: number }>;

    expect(series.length, "Series must have at least 1 data point").toBeGreaterThan(0);

    const badActual = series.filter((p) => !Number.isFinite(p.actual_price));
    const badPredicted = series.filter((p) => !Number.isFinite(p.predicted_price));

    if (badActual.length > 0) {
      console.log(`[backtest sanity] Non-finite actual_price entries: ${JSON.stringify(badActual.slice(0, 5))}`);
    }
    if (badPredicted.length > 0) {
      console.log(`[backtest sanity] Non-finite predicted_price entries: ${JSON.stringify(badPredicted.slice(0, 5))}`);
    }

    expect(badActual.length, `Found ${badActual.length} non-finite actual_price values in series`).toBe(0);
    expect(badPredicted.length, `Found ${badPredicted.length} non-finite predicted_price values in series`).toBe(0);
  });

  test("Sufficient data points returned (>= 10)", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes(BASE_API_URL) && res.url().includes("/backtest/") && res.status() === 200,
      { timeout: 30_000 },
    );

    await page.goto("/backtest");
    await page.getByRole("button", { name: /Run Backtest/i }).waitFor({ timeout: 15_000 });
    await page.getByRole("button", { name: /Run Backtest/i }).click();

    const response = await responsePromise;
    const data = await response.json();
    const { metrics } = data;

    console.log(`\n[backtest sanity] total_points=${metrics.total_points}`);
    console.log(`[backtest sanity] period: ${data.start_date} → ${data.end_date}`);
    console.log(`[backtest sanity] model: ${data.model_name}`);

    expect(
      metrics.total_points,
      `Only ${metrics.total_points} data points for a 1-year backtest. ` +
      `Check that predictions are being saved to the DB during inference.`,
    ).toBeGreaterThanOrEqual(10);
  });

  test("Rendered metric cards match API payload values", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes(BASE_API_URL) && res.url().includes("/backtest/") && res.status() === 200,
      { timeout: 30_000 },
    );

    await page.goto("/backtest");
    await page.getByRole("button", { name: /Run Backtest/i }).waitFor({ timeout: 15_000 });
    await page.getByRole("button", { name: /Run Backtest/i }).click();

    const response = await responsePromise;
    const data = await response.json();
    const { metrics } = data;

    // Wait for metric cards to appear
    await page.getByText(/Root Mean Squared Error/i).first().waitFor({ timeout: 20_000 });

    // Extract all numeric text from metric cards
    const bodyText = (await page.locator("body").textContent()) ?? "";

    // Verify RMSE appears in rendered text (formatted to 4dp)
    const expectedRmse = metrics.rmse.toFixed(4);
    expect(
      bodyText,
      `Expected rendered RMSE "${expectedRmse}" (from API) to appear on page. ` +
      `Raw API metrics: ${JSON.stringify(metrics)}`,
    ).toContain(expectedRmse);

    // Verify directional accuracy appears (formatted as X.X%)
    const expectedDa = `${metrics.directional_accuracy.toFixed(1)}%`;
    expect(
      bodyText,
      `Expected rendered Dir.Acc "${expectedDa}" to appear on page. ` +
      `Raw API metrics: ${JSON.stringify(metrics)}`,
    ).toContain(expectedDa);
  });
});
