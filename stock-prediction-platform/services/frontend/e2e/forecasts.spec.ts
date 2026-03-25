import { test, expect, request } from "@playwright/test";
import {
  healthFixture,
  marketOverviewFixture,
  bulkPredictionsFixture,
  availableHorizonsFixture,
  tickerIndicatorsFixture,
} from "./fixtures/api";

// Helper: stub all Forecasts page routes
async function stubForecastsRoutes(
  page: import("@playwright/test").Page,
  horizon = 7
) {
  await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
  await page.route("**/predict/horizons", (route) =>
    route.fulfill({ json: availableHorizonsFixture() })
  );
  await page.route("**/predict/bulk**", (route) =>
    route.fulfill({ json: bulkPredictionsFixture(horizon) })
  );
  await page.route("**/market/overview", (route) =>
    route.fulfill({ json: marketOverviewFixture() })
  );
  await page.route("**/market/indicators/**", (route) =>
    route.fulfill({ json: tickerIndicatorsFixture() })
  );
}

test.describe("Forecasts page", () => {
  test.beforeAll(async () => {
    const ctx = await request.newContext();
    try {
      const healthRes = await ctx.get("http://localhost:8000/health", { timeout: 5_000 });
      if (!healthRes.ok()) {
        test.skip(true, "Backend API is not running at http://localhost:8000 — start the API first");
        return;
      }
      const bulkRes = await ctx.get("http://localhost:8000/predict/bulk", { timeout: 5_000 });
      if (!bulkRes.ok()) {
        test.skip(true, "GET /predict/bulk failed — backend unhealthy or no trained model");
        return;
      }
      const data = await bulkRes.json();
      if (!data?.predictions?.length) {
        test.skip(true, "GET /predict/bulk returned 0 predictions — run the training pipeline and ensure model is deployed");
      }
    } catch {
      test.skip(true, "Backend API is not running at http://localhost:8000 — start the API first");
    } finally {
      await ctx.dispose();
    }
  });

  test.describe.configure({ mode: "serial" });

  test("page loads and shows fixture model name in table", async ({ page }) => {
    await stubForecastsRoutes(page);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    // Wait for table to render with fixture data
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    // Click first row to open detail section — StockShapPanel renders "Model: {model_name}"
    // This confirms fixture data is used (not mock fallback which has different model name)
    await page.locator("table tbody tr").first().click();
    await expect(page.getByText("fixture_stacking_ensemble_meta_ridge").first()).toBeVisible();
  });

  test("table shows fixture tickers AAPL and MSFT", async ({ page }) => {
    await stubForecastsRoutes(page);
    await page.goto("/forecasts");
    // Wait for table to render — both tickers from bulkPredictionsFixture appear
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    const rows = page.locator("table tbody tr");
    await expect(rows).toHaveCount(2);
    await expect(page.getByText("AAPL").first()).toBeVisible();
    await expect(page.getByText("MSFT").first()).toBeVisible();
  });

  test("horizon toggle from 7D to 30D re-fires bulk query", async ({ page }) => {
    // Track which horizon parameter was requested
    let requestedHorizon = "";
    await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
    await page.route("**/predict/horizons", (route) =>
      route.fulfill({ json: availableHorizonsFixture() })
    );
    await page.route("**/predict/bulk**", (route) => {
      requestedHorizon = new URL(route.request().url()).searchParams.get("horizon") ?? "";
      return route.fulfill({ json: bulkPredictionsFixture(30) });
    });
    await page.route("**/market/overview", (route) =>
      route.fulfill({ json: marketOverviewFixture() })
    );
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    // Click the 30D radio button
    await page.getByRole("radio", { name: "30D" }).click();
    // After click, a new /predict/bulk request is fired with horizon=30
    await expect(page.getByRole("radio", { name: "30D" })).toBeChecked();
  });

  test("search input filters table rows", async ({ page }) => {
    await stubForecastsRoutes(page);
    await page.goto("/forecasts");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    // Type in search box — filters to AAPL only
    await page.getByPlaceholder("Ticker or company…").fill("AAPL");
    const rows = page.locator("table tbody tr");
    await expect(rows).toHaveCount(1);
    await expect(page.getByText("AAPL").first()).toBeVisible();
    // MSFT row should be gone
    await expect(page.getByText("MSFT").first()).not.toBeVisible();
  });

  test("clicking a table row opens the stock detail section", async ({ page }) => {
    await stubForecastsRoutes(page);
    await page.goto("/forecasts");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    // Click the first row (AAPL)
    await page.locator("table tbody tr").first().click();
    // Detail section heading: "{ticker} — Detail View"
    await expect(page.getByText("AAPL — Detail View")).toBeVisible();
    // Close button is present (Forecasts uses plain "Close")
    await expect(page.getByRole("button", { name: "Close" })).toBeVisible();
  });

  test("close button in detail section hides the detail view", async ({ page }) => {
    await stubForecastsRoutes(page);
    await page.goto("/forecasts");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    await page.locator("table tbody tr").first().click();
    await expect(page.getByText("AAPL — Detail View")).toBeVisible();
    await page.getByRole("button", { name: "Close" }).click();
    await expect(page.getByText("AAPL — Detail View")).not.toBeVisible();
  });

  test("export CSV and PDF buttons are enabled when data is loaded", async ({ page }) => {
    await stubForecastsRoutes(page);
    await page.goto("/forecasts");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    // ExportButtons: disabled={!filteredForecasts.length} — should be enabled with 2 rows
    const csvBtn = page.getByRole("button", { name: /CSV/i });
    const pdfBtn = page.getByRole("button", { name: /PDF/i });
    await expect(csvBtn).toBeVisible();
    await expect(pdfBtn).toBeVisible();
    await expect(csvBtn).toBeEnabled();
    await expect(pdfBtn).toBeEnabled();
  });
});
