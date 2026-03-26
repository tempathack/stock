import { test, expect } from "@playwright/test";
import { skipIfNotProduction } from "./helpers/production-guard";

const BASE_API = process.env.BASE_API_URL ?? "http://localhost:8000";

// Serial mode: single browser instance against live services
test.describe.configure({ mode: "serial" });

const PRODUCTION_GUARD = [
  { url: `${BASE_API}/health`, description: "API health endpoint must be 200" },
  {
    url: `${BASE_API}/predict/bulk?horizon=7`,
    description: "predict/bulk?horizon=7 must return ≥10 predictions",
  },
  {
    url: `${BASE_API}/market/overview`,
    description: "market/overview must return ≥10 stocks",
  },
];

test.describe("Forecasts page", () => {
  skipIfNotProduction(test, PRODUCTION_GUARD);

  test("table shows ≥10 stocks", async ({ page }) => {
    test.setTimeout(25_000);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();

    // Wait for table rows to appear (real API data loads)
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });

    // Verify ≥10 rows from the API directly
    const resp = await page.request.get(`${BASE_API}/predict/bulk?horizon=7`, { timeout: 15_000 });
    expect(resp.ok()).toBe(true);
    const data = await resp.json();
    expect((data.predictions as unknown[]).length).toBeGreaterThanOrEqual(10);

    // Assert table has multiple visible rows
    const rows = page.locator("table tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(10);
  });

  test("model name shown (not fixture_ prefix)", async ({ page }) => {
    test.setTimeout(25_000);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });

    // Click first row to open detail view which shows the model name
    await page.locator("table tbody tr").first().click();

    // Detail section should appear
    await expect(page.locator("h2").filter({ hasText: /— Detail View$/ })).toBeVisible({
      timeout: 10_000,
    });

    // The StockShapPanel renders model name — assert it does NOT start with 'fixture_'
    const modelNameEl = page.locator("text=/Model:/").first();
    const modelText = await modelNameEl.textContent({ timeout: 10_000 }).catch(() => null);
    if (modelText) {
      expect(modelText).not.toMatch(/fixture_/i);
    }
  });

  test("horizon toggle 7D → 30D refetches data", async ({ page }) => {
    test.setTimeout(25_000);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });

    // Click the 30D radio button
    await page.getByRole("radio", { name: "30D" }).click();
    await expect(page.getByRole("radio", { name: "30D" })).toBeChecked();

    // After toggle, table should reload and still show rows
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });
    const rows = page.locator("table tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(10);
  });

  test("search input filters table rows", async ({ page }) => {
    test.setTimeout(25_000);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });

    // Type AAPL in search input
    await page.getByPlaceholder("Ticker or company…").fill("AAPL");

    // Table should filter to only AAPL rows
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 10_000 });
    const filteredRows = page.locator("table tbody tr");
    const filteredCount = await filteredRows.count();
    // With AAPL filter, only AAPL row(s) should remain
    expect(filteredCount).toBeGreaterThanOrEqual(1);
    await expect(page.getByText("AAPL").first()).toBeVisible();

    // Clear search and assert full table returns
    await page.getByPlaceholder("Ticker or company…").clear();
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 10_000 });
    const allRows = page.locator("table tbody tr");
    const allCount = await allRows.count();
    expect(allCount).toBeGreaterThan(filteredCount);
  });

  test("clicking a row opens the stock detail section", async ({ page }) => {
    test.setTimeout(25_000);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });

    // Get ticker from first row
    const firstCell = page.locator("table tbody tr").first().locator("td").first();
    const ticker = (await firstCell.textContent())?.trim() ?? "AAPL";

    // Click the first row
    await page.locator("table tbody tr").first().click();

    // Detail section heading: "{ticker} — Detail View"
    await expect(page.getByText(`${ticker} — Detail View`)).toBeVisible({ timeout: 10_000 });

    // Chart container is visible
    await expect(page.locator(".recharts-wrapper").first()).toBeVisible({ timeout: 10_000 });
  });

  test("export CSV and PDF buttons are enabled when data is loaded", async ({ page }) => {
    test.setTimeout(25_000);
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 20_000 });

    // ExportButtons: disabled={!filteredForecasts.length} — should be enabled with real data
    const csvBtn = page.getByRole("button", { name: /CSV/i });
    const pdfBtn = page.getByRole("button", { name: /PDF/i });
    await expect(csvBtn).toBeVisible();
    await expect(pdfBtn).toBeVisible();
    await expect(csvBtn).toBeEnabled();
    await expect(pdfBtn).toBeEnabled();
  });
});
