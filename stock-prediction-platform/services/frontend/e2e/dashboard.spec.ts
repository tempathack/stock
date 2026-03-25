import { test, expect } from "@playwright/test";
import {
  healthFixture,
  marketOverviewFixture,
  tickerIndicatorsFixture,
  bulkPredictionsFixture,
  modelComparisonFixture,
  driftStatusFixture,
  rollingPerformanceFixture,
  retrainStatusFixture,
  backtestFixture,
  availableHorizonsFixture,
} from "./fixtures/api";

// Helper: stub all routes used across all pages (for nav tests that navigate away).
// Playwright matches routes in LIFO order (last registered = first matched).
// Register broad catch-all patterns FIRST so specific patterns registered LAST take priority.
async function stubAllRoutes(page: import("@playwright/test").Page) {
  // Broad catch-all for predict/:ticker — registered FIRST so specific routes below override it
  await page.route("**/predict/**", (route) =>
    route.fulfill({
      json: {
        ticker: "AAPL",
        prediction_date: "2026-03-25",
        predicted_date: "2026-04-01",
        predicted_price: 182.30,
        model_name: "fixture_stacking_ensemble_meta_ridge",
        confidence: 0.87,
        horizon_days: 7,
      },
    })
  );
  // Broad catch-all for models/drift — registered before more-specific sub-routes
  await page.route("**/models/drift", (route) => route.fulfill({ json: driftStatusFixture() }));
  // Specific routes registered LAST take priority (LIFO matching)
  await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
  await page.route("**/market/overview", (route) => route.fulfill({ json: marketOverviewFixture() }));
  await page.route("**/market/indicators/**", (route) => route.fulfill({ json: tickerIndicatorsFixture() }));
  await page.route("**/predict/horizons", (route) => route.fulfill({ json: availableHorizonsFixture() }));
  await page.route("**/predict/bulk**", (route) => route.fulfill({ json: bulkPredictionsFixture() }));
  await page.route("**/models/comparison", (route) => route.fulfill({ json: modelComparisonFixture() }));
  await page.route("**/models/drift/rolling-performance**", (route) => route.fulfill({ json: rollingPerformanceFixture() }));
  await page.route("**/models/retrain-status", (route) => route.fulfill({ json: retrainStatusFixture() }));
  await page.route("http://localhost:8000/backtest/**", (route) => route.fulfill({ json: backtestFixture() }));
}

test.describe("Navigation", () => {
  test("sidebar link to Forecasts navigates to /forecasts", async ({ page }) => {
    await stubAllRoutes(page);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();
    await page.getByRole("link", { name: "Forecasts" }).click();
    await expect(page).toHaveURL(/\/forecasts/);
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
  });

  test("sidebar link to Models navigates to /models", async ({ page }) => {
    await stubAllRoutes(page);
    await page.goto("/dashboard");
    await page.getByRole("link", { name: "Models" }).click();
    await expect(page).toHaveURL(/\/models/);
    await expect(page.getByRole("heading", { name: "Model Comparison" })).toBeVisible();
  });

  test("sidebar link to Drift navigates to /drift", async ({ page }) => {
    await stubAllRoutes(page);
    await page.goto("/dashboard");
    await page.getByRole("link", { name: "Drift" }).click();
    await expect(page).toHaveURL(/\/drift/);
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
  });

  test("sidebar link to Backtest navigates to /backtest", async ({ page }) => {
    await stubAllRoutes(page);
    await page.goto("/dashboard");
    await page.getByRole("link", { name: "Backtest" }).click();
    await expect(page).toHaveURL(/\/backtest/);
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
  });
});

test.describe("Dashboard page", () => {
  test.beforeEach(async ({ page }) => {
    // Suppress WebSocket connection errors (expected: dev server has no WS endpoint)
    page.on("websocket", (ws) => {
      ws.on("socketerror", () => {});
    });
  });

  test("treemap renders fixture tickers from /market/overview", async ({ page }) => {
    await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
    await page.route("**/market/overview", (route) => route.fulfill({ json: marketOverviewFixture() }));
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();
    // Assert on fixture tickers — both AAPL and MSFT appear from marketOverviewFixture
    await expect(page.getByText("AAPL")).toBeVisible();
    await expect(page.getByText("MSFT")).toBeVisible();
  });

  test("clicking treemap ticker opens detail view with metric cards", async ({ page }) => {
    await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
    await page.route("**/market/overview", (route) => route.fulfill({ json: marketOverviewFixture() }));
    await page.route("**/market/indicators/**", (route) =>
      route.fulfill({ json: tickerIndicatorsFixture("AAPL") })
    );
    await page.route("**/predict/**", (route) =>
      route.fulfill({
        json: {
          ticker: "AAPL",
          prediction_date: "2026-03-25",
          predicted_date: "2026-04-01",
          predicted_price: 182.30,
          model_name: "fixture_stacking_ensemble_meta_ridge",
          confidence: 0.87,
          horizon_days: 7,
        },
      })
    );
    await page.goto("/dashboard");
    await expect(page.getByText("AAPL")).toBeVisible();
    // Click the AAPL cell in the treemap
    await page.getByText("AAPL").first().click();
    // Detail view heading shows ticker name
    await expect(page.getByText("AAPL — Detail View")).toBeVisible();
    // Close button is present
    await expect(page.getByRole("button", { name: /✕ Close/i })).toBeVisible();
  });

  test("Show Technical Indicators button toggles TA panel", async ({ page }) => {
    await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
    await page.route("**/market/overview", (route) => route.fulfill({ json: marketOverviewFixture() }));
    await page.route("**/market/indicators/**", (route) =>
      route.fulfill({ json: tickerIndicatorsFixture("AAPL") })
    );
    await page.route("**/predict/**", (route) =>
      route.fulfill({
        json: {
          ticker: "AAPL",
          prediction_date: "2026-03-25",
          predicted_date: "2026-04-01",
          predicted_price: 182.30,
          model_name: "fixture_stacking_ensemble_meta_ridge",
          confidence: 0.87,
          horizon_days: 7,
        },
      })
    );
    await page.goto("/dashboard");
    await page.getByText("AAPL").first().click();
    await expect(page.getByText("AAPL — Detail View")).toBeVisible();
    // Initially TA panel is hidden — button says "Show"
    const showBtn = page.getByRole("button", { name: /Show Technical Indicators/i });
    await expect(showBtn).toBeVisible();
    await showBtn.click();
    // After click — button text changes to "Hide"
    await expect(page.getByRole("button", { name: /Hide Technical Indicators/i })).toBeVisible();
  });

  test("close button hides the detail section", async ({ page }) => {
    await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
    await page.route("**/market/overview", (route) => route.fulfill({ json: marketOverviewFixture() }));
    await page.route("**/market/indicators/**", (route) =>
      route.fulfill({ json: tickerIndicatorsFixture("AAPL") })
    );
    await page.route("**/predict/**", (route) =>
      route.fulfill({
        json: {
          ticker: "AAPL",
          prediction_date: "2026-03-25",
          predicted_date: "2026-04-01",
          predicted_price: 182.30,
          model_name: "fixture_stacking_ensemble_meta_ridge",
          confidence: 0.87,
          horizon_days: 7,
        },
      })
    );
    await page.goto("/dashboard");
    await page.getByText("AAPL").first().click();
    await expect(page.getByText("AAPL — Detail View")).toBeVisible();
    await page.getByRole("button", { name: /✕ Close/i }).click();
    // Detail view should be gone
    await expect(page.getByText("AAPL — Detail View")).not.toBeVisible();
  });
});
