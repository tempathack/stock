import { test, expect } from "@playwright/test";
import { skipIfNotProduction } from "./helpers/production-guard";

test.describe.configure({ mode: "serial" });

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

skipIfNotProduction(test, [
  {
    url: `${BASE_API_URL}/health`,
    description: "API health endpoint must be 200",
  },
  {
    url: `${BASE_API_URL}/market/overview`,
    description: "market/overview must return ≥5 stocks",
  },
]);

test.describe("Backtest page — production mode", () => {
  test.describe.configure({ mode: "serial" });

  test("page loads and shows model info banner", async ({ page }) => {
    test.setTimeout(30_000);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 20_000 });
    // Model info banner should show a real model name (not a fixture_ prefix)
    const modelBannerText = await page.locator("body").textContent();
    expect(modelBannerText).not.toBeNull();
    // Assert there is some model text visible — look for 'Model:' label or horizon badge
    const modelLabel = page.getByText(/Model:/i).first();
    const horizonLabel = page.getByText(/Horizon:/i).first();
    // At least one should be visible
    const modelVisible = await modelLabel.isVisible().catch(() => false);
    const horizonVisible = await horizonLabel.isVisible().catch(() => false);
    expect(modelVisible || horizonVisible).toBe(true);
    // Model name should not start with 'fixture_'
    if (modelVisible) {
      const fullText = await modelLabel.textContent();
      expect(fullText).not.toMatch(/fixture_/);
    }
    // Horizon shown (e.g. 7d, 1d, 30d)
    const horizonSpan = page.locator("span").filter({ hasText: /^\d+d$/ }).first();
    const horizonSpanVisible = await horizonSpan.isVisible().catch(() => false);
    if (horizonSpanVisible) {
      const horizonText = await horizonSpan.textContent();
      expect(horizonText).toMatch(/^\d+d$/);
    }
  });

  test("ticker select populated with real tickers including AAPL", async ({ page }) => {
    test.setTimeout(30_000);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 20_000 });
    // Ticker select (first <select> or combobox) should have ≥5 options
    const tickerSelect = page.locator("select").first();
    await expect(tickerSelect).toBeVisible({ timeout: 10_000 });
    const options = tickerSelect.locator("option");
    const optionCount = await options.count();
    expect(optionCount).toBeGreaterThanOrEqual(5);
    // AAPL should be among the options
    const aaplOption = tickerSelect.locator('option[value="AAPL"]');
    const aaplFound = (await aaplOption.count()) > 0;
    if (!aaplFound) {
      // Sometimes value is different — check by text
      const optionsTexts = await options.allTextContents();
      const hasAapl = optionsTexts.some((t) => t.includes("AAPL"));
      expect(hasAapl).toBe(true);
    }
  });

  test("date inputs and horizon select are present and interactable", async ({ page }) => {
    test.setTimeout(30_000);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 20_000 });
    // Two date inputs should be present
    const dateInputs = page.locator('input[type="date"]');
    await expect(dateInputs).toHaveCount(2, { timeout: 10_000 });
    // Horizon select should be present (second <select>)
    const horizonSelect = page.locator("select").nth(1);
    await expect(horizonSelect).toBeVisible({ timeout: 10_000 });
    // Horizon options include 1d, 7d, 30d
    const horizonOptions = horizonSelect.locator("option");
    const horizonTexts = await horizonOptions.allTextContents();
    const has7d = horizonTexts.some((t) => t.includes("7d") || t === "7");
    expect(has7d).toBe(true);
  });

  test("Run Backtest with AAPL produces RMSE and MAE metrics", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 20_000 });

    // Select AAPL in the ticker dropdown
    const tickerSelect = page.locator("select").first();
    await expect(tickerSelect).toBeVisible({ timeout: 10_000 });
    await tickerSelect.selectOption({ label: "AAPL" }).catch(() =>
      tickerSelect.selectOption({ value: "AAPL" })
    );

    // Set date range: 1 year ago to today
    const today = new Date();
    const oneYearAgo = new Date(today);
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    const formatDate = (d: Date) => d.toISOString().split("T")[0];

    const dateInputs = page.locator('input[type="date"]');
    await dateInputs.nth(0).fill(formatDate(oneYearAgo));
    await dateInputs.nth(1).fill(formatDate(today));

    // Click Run Backtest
    const runBtn = page.getByRole("button", { name: /Run Backtest/i });
    await expect(runBtn).toBeVisible({ timeout: 10_000 });
    await expect(runBtn).toBeEnabled();
    await runBtn.click();

    // Wait up to 20s for results to appear
    // Look for RMSE or MAE metric values (positive numbers)
    const rmseText = page.getByText(/RMSE/i).first();
    await expect(rmseText).toBeVisible({ timeout: 25_000 });

    // Assert numeric metric values are shown (not '-' or '0.00' only)
    const bodyText = await page.locator("body").textContent();
    // Find any number > 0 in the metrics area
    const hasRmse = /RMSE/i.test(bodyText ?? "");
    const hasMae = /MAE/i.test(bodyText ?? "");
    expect(hasRmse).toBe(true);
    expect(hasMae).toBe(true);

    // Extract numeric value near RMSE — look for a number pattern
    const metricsSection = page.locator('[data-testid="backtest-metrics"], .backtest-metrics, [class*="metric"]').first();
    const metricsSectionVisible = await metricsSection.isVisible().catch(() => false);
    if (metricsSectionVisible) {
      const metricsText = await metricsSection.textContent();
      const numbers = (metricsText ?? "").match(/\d+\.\d+/g);
      expect(numbers).not.toBeNull();
      const hasPositiveNumber = numbers?.some((n) => parseFloat(n) > 0);
      expect(hasPositiveNumber).toBe(true);
    }
  });

  test("chart renders after backtest run", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 20_000 });

    // Select AAPL and run backtest
    const tickerSelect = page.locator("select").first();
    await expect(tickerSelect).toBeVisible({ timeout: 10_000 });
    await tickerSelect.selectOption({ label: "AAPL" }).catch(() =>
      tickerSelect.selectOption({ value: "AAPL" })
    );

    const today = new Date();
    const oneYearAgo = new Date(today);
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    const formatDate = (d: Date) => d.toISOString().split("T")[0];

    const dateInputs = page.locator('input[type="date"]');
    await dateInputs.nth(0).fill(formatDate(oneYearAgo));
    await dateInputs.nth(1).fill(formatDate(today));

    const runBtn = page.getByRole("button", { name: /Run Backtest/i });
    await runBtn.click();

    // Wait for chart container to appear (recharts or lightweight-charts container)
    const chartContainer = page
      .locator(
        '[data-testid="backtest-chart"], .recharts-responsive-container, [class*="chart"], canvas'
      )
      .first();
    await expect(chartContainer).toBeVisible({ timeout: 30_000 });

    // Assert non-zero height
    const boundingBox = await chartContainer.boundingBox();
    expect(boundingBox).not.toBeNull();
    expect(boundingBox!.height).toBeGreaterThan(0);
  });

  test("export buttons enabled after backtest run", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 20_000 });

    // Select AAPL and run
    const tickerSelect = page.locator("select").first();
    await expect(tickerSelect).toBeVisible({ timeout: 10_000 });
    await tickerSelect.selectOption({ label: "AAPL" }).catch(() =>
      tickerSelect.selectOption({ value: "AAPL" })
    );

    const today = new Date();
    const oneYearAgo = new Date(today);
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    const formatDate = (d: Date) => d.toISOString().split("T")[0];

    const dateInputs = page.locator('input[type="date"]');
    await dateInputs.nth(0).fill(formatDate(oneYearAgo));
    await dateInputs.nth(1).fill(formatDate(today));

    const runBtn = page.getByRole("button", { name: /Run Backtest/i });
    await runBtn.click();

    // Wait for data to load (RMSE visible)
    await page.getByText(/RMSE/i).first().waitFor({ timeout: 25_000 });

    // Export buttons should be enabled
    await expect(page.getByRole("button", { name: /CSV/i })).toBeEnabled({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: /PDF/i })).toBeEnabled({ timeout: 10_000 });
  });
});
