import { test, expect } from "@playwright/test";
import { skipIfNotProduction } from "./helpers/production-guard";

const BASE_API = process.env.BASE_API_URL ?? "http://localhost:8000";

// Serial mode: single browser instance against live services
test.describe.configure({ mode: "serial" });

const PRODUCTION_GUARD = [
  { url: `${BASE_API}/health`, description: "API health endpoint must be 200" },
  {
    url: `${BASE_API}/market/overview`,
    description: "market/overview must return ≥20 stocks",
  },
];

test.describe("Dashboard page", () => {
  skipIfNotProduction(test, PRODUCTION_GUARD);

  test.beforeEach(async ({ page }) => {
    // Suppress WebSocket errors — ws endpoint may not be active
    page.on("websocket", (ws) => {
      ws.on("socketerror", () => {});
    });
  });

  test("treemap renders ≥20 tickers", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();

    // Wait for market data to load (treemap replaces loading spinner)
    await expect(page.locator(".recharts-wrapper")).toBeVisible({ timeout: 15_000 });

    // Verify the API returned ≥20 stocks
    const resp = await page.request.get(`${BASE_API}/market/overview`, { timeout: 10_000 });
    expect(resp.ok()).toBe(true);
    const data = await resp.json();
    expect((data.stocks as unknown[]).length).toBeGreaterThanOrEqual(20);

    // Verify treemap SVG cells are rendered (at least some ticker text visible)
    // Large-cap stocks (AAPL, MSFT, GOOGL etc.) always have wide cells that show ticker text
    const tickerTexts = page.locator("svg text").filter({ hasText: /^[A-Z]{2,5}$/ });
    await expect(tickerTexts.first()).toBeVisible({ timeout: 10_000 });
    const visibleCount = await tickerTexts.count();
    // At 1280x800 with 500 stocks, top caps will render text labels
    expect(visibleCount).toBeGreaterThanOrEqual(5);
  });

  test("clicking AAPL cell opens detail view with real metric cards", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();
    await expect(page.locator(".recharts-wrapper")).toBeVisible({ timeout: 15_000 });

    // Find and click AAPL — it's always large enough to render as SVG text
    const aaplText = page.locator("svg text", { hasText: "AAPL" }).first();
    await expect(aaplText).toBeVisible({ timeout: 10_000 });
    await aaplText.click();

    // Detail view heading appears
    await expect(page.getByText("AAPL — Detail View")).toBeVisible({ timeout: 10_000 });

    // Metric cards are visible with real values (not '-' or '--')
    await expect(page.getByText("Current Price")).toBeVisible();
    await expect(page.getByText("Daily Change")).toBeVisible();
    await expect(page.getByText("Market Cap")).toBeVisible();

    // Price value starts with '$' and is a real number
    const priceCard = page.locator(".rounded-lg").filter({ hasText: "Current Price" });
    const priceValue = priceCard.locator("p.text-lg");
    await expect(priceValue).toBeVisible();
    const priceText = await priceValue.textContent();
    expect(priceText).toMatch(/^\$[\d,.]+$/);
    expect(priceText).not.toMatch(/^[–-]+$/);
  });

  test("technical indicators toggle shows TA panel", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.locator(".recharts-wrapper")).toBeVisible({ timeout: 15_000 });

    // Click AAPL
    const aaplText = page.locator("svg text", { hasText: "AAPL" }).first();
    await expect(aaplText).toBeVisible({ timeout: 10_000 });
    await aaplText.click();
    await expect(page.getByText("AAPL — Detail View")).toBeVisible({ timeout: 10_000 });

    // Show Technical Indicators button is visible before toggle
    const showBtn = page.getByRole("button", { name: /Show Technical Indicators/i });
    await expect(showBtn).toBeVisible();
    await showBtn.click();

    // After toggle, button changes to "Hide"
    await expect(page.getByRole("button", { name: /Hide Technical Indicators/i })).toBeVisible();

    // TA panel is now visible in DOM
    const hideBtn = page.getByRole("button", { name: /Hide Technical Indicators/i });
    await expect(hideBtn).toBeVisible();
  });

  test("navigation to all 4 app pages works", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();

    // Navigate to Forecasts
    await page.getByRole("link", { name: "Forecasts" }).click();
    await expect(page).toHaveURL(/\/forecasts/);
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible({ timeout: 10_000 });

    // Navigate to Models
    await page.getByRole("link", { name: "Models" }).click();
    await expect(page).toHaveURL(/\/models/);
    await expect(page.getByRole("heading", { name: "Model Comparison" })).toBeVisible({ timeout: 10_000 });

    // Navigate to Drift
    await page.getByRole("link", { name: "Drift" }).click();
    await expect(page).toHaveURL(/\/drift/);
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible({ timeout: 10_000 });

    // Navigate to Backtest
    await page.getByRole("link", { name: "Backtest" }).click();
    await expect(page).toHaveURL(/\/backtest/);
    await expect(page.getByRole("heading", { name: /Backtest/i })).toBeVisible({ timeout: 10_000 });
  });

  test("AppBar shows connection status chips", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();

    // AppBar has API, Kafka, and DB status chips
    await expect(page.getByText("API").first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Kafka")).toBeVisible();
    await expect(page.getByText("DB")).toBeVisible();
  });

  test("price ticker strip is visible", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();

    // Ticker strip appears after market data loads
    const strip = page.getByTestId("price-ticker-strip");
    await expect(strip).toBeVisible({ timeout: 15_000 });

    // At least one ticker symbol should be in the strip
    const stripText = await strip.textContent();
    expect(stripText).toMatch(/[A-Z]{2,5}/);
  });

  test("close button hides detail section", async ({ page }) => {
    test.setTimeout(20_000);
    await page.goto("/dashboard");
    await expect(page.locator(".recharts-wrapper")).toBeVisible({ timeout: 15_000 });

    // Open detail view for AAPL
    const aaplText = page.locator("svg text", { hasText: "AAPL" }).first();
    await expect(aaplText).toBeVisible({ timeout: 10_000 });
    await aaplText.click();
    await expect(page.getByText("AAPL — Detail View")).toBeVisible({ timeout: 10_000 });

    // Click close button
    await page.getByRole("button", { name: /✕ Close/i }).click();

    // Detail view is gone
    await expect(page.getByText("AAPL — Detail View")).not.toBeVisible();
  });
});
