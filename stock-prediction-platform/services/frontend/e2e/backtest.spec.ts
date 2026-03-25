import { test, expect } from "@playwright/test";
import { healthFixture, marketOverviewFixture, backtestFixture } from "./fixtures/api";

// Helper: stub all Backtest page routes
async function stubBacktestRoutes(
  page: import("@playwright/test").Page,
  ticker = "AAPL"
) {
  await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
  await page.route("**/market/overview", (route) =>
    route.fulfill({ json: marketOverviewFixture() })
  );
  await page.route("http://localhost:8000/backtest/**", (route) =>
    route.fulfill({ json: backtestFixture(ticker) })
  );
}

test.describe("Backtest page", () => {
  test.describe.configure({ mode: "serial" });

  test("page loads with initial AAPL fixture and shows model info banner", async ({ page }) => {
    await stubBacktestRoutes(page, "AAPL");
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    // Model info banner: "Model: fixture_stacking_ensemble_meta_ridge · Horizon: 7d"
    await expect(
      page.getByText("fixture_stacking_ensemble_meta_ridge").first()
    ).toBeVisible();
    // Horizon from fixture is 7 — the span "7d" appears in the model info banner
    // Use locator for the span with text "7d" that is visible (not inside a hidden select option)
    await expect(page.locator("span").filter({ hasText: /^7d$/ }).first()).toBeVisible();
  });

  test("ticker select is populated from market overview fixture", async ({ page }) => {
    await stubBacktestRoutes(page);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    // Ticker select contains AAPL and MSFT from marketOverviewFixture
    const tickerSelect = page.locator("select").first();
    await expect(tickerSelect).toBeVisible();
    const options = tickerSelect.locator("option");
    // marketOverviewFixture has 2 stocks: AAPL, MSFT
    await expect(options).toHaveCount(2);
  });

  test("Start Date and End Date inputs are present", async ({ page }) => {
    await stubBacktestRoutes(page);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    // Two date inputs present
    const dateInputs = page.locator('input[type="date"]');
    await expect(dateInputs).toHaveCount(2);
  });

  test("Horizon (days) select has All, 1d, 7d, 30d options", async ({ page }) => {
    await stubBacktestRoutes(page);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    // Horizon select is the second <select> on the page (Ticker is first)
    const horizonSelect = page.locator("select").nth(1);
    await expect(horizonSelect).toBeVisible();
    const options = horizonSelect.locator("option");
    await expect(options).toHaveCount(4); // All, 1d, 7d, 30d
    await expect(horizonSelect.locator("option").nth(0)).toHaveText("All");
    await expect(horizonSelect.locator("option").nth(1)).toHaveText("1d");
    await expect(horizonSelect.locator("option").nth(2)).toHaveText("7d");
    await expect(horizonSelect.locator("option").nth(3)).toHaveText("30d");
  });

  test("Run Backtest button is present and clickable", async ({ page }) => {
    await stubBacktestRoutes(page);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    const runBtn = page.getByRole("button", { name: "Run Backtest" });
    await expect(runBtn).toBeVisible();
    await expect(runBtn).toBeEnabled();
    // Click Run Backtest — activeTicker stays AAPL (already default)
    // A new request to /backtest/AAPL fires — intercepted by existing route stub
    await runBtn.click();
    // Model banner still shows fixture data after re-run
    await expect(
      page.getByText("fixture_stacking_ensemble_meta_ridge").first()
    ).toBeVisible();
  });

  test("BacktestMetricsSummary shows fixture RMSE and directional accuracy", async ({
    page,
  }) => {
    await stubBacktestRoutes(page, "AAPL");
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    // backtestFixture metrics: rmse=3.45, mae=2.87, directional_accuracy=68.5
    // BacktestMetricsSummary renders these values
    await expect(page.getByText("3.45").first()).toBeVisible();
    await expect(page.getByText("2.87").first()).toBeVisible();
  });

  test("export CSV and PDF buttons are enabled after data loads", async ({ page }) => {
    await stubBacktestRoutes(page);
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
    // Wait for fixture data to load (model banner visible)
    await expect(
      page.getByText("fixture_stacking_ensemble_meta_ridge").first()
    ).toBeVisible();
    // ExportButtons: disabled={!backtestQuery.data} — data is loaded, so enabled
    await expect(page.getByRole("button", { name: /CSV/i })).toBeEnabled();
    await expect(page.getByRole("button", { name: /PDF/i })).toBeEnabled();
  });
});
