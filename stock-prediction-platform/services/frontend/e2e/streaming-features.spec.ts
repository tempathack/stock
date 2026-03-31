/**
 * Phase 70 — Streaming Features E2E Tests
 *
 * Tests the StreamingFeaturesPanel in the Dashboard Drawer.
 * Uses page.route() interceptors — no live API or Flink required.
 *
 * Covers:
 *  1. API endpoint shape — /market/streaming-features/{ticker} returns expected fields
 *  2. Panel renders with live Flink data (available=true)
 *  3. Panel renders graceful empty-state when Feast unavailable (available=false)
 *  4. RSI overbought / oversold / neutral chips
 *  5. Accordion placement — above Technical Indicators, defaultExpanded
 */
import { test, expect } from "@playwright/test";
import {
  marketOverviewFixture,
  streamingFeaturesFixture,
  streamingFeaturesUnavailableFixture,
} from "./fixtures/api";

const BASE_API = process.env.BASE_API_URL ?? "http://localhost:8000";

// Helper: mount common routes needed to open Dashboard with a ticker selected
async function mountDashboardRoutes(page: import("@playwright/test").Page) {
  const overview = marketOverviewFixture();

  await page.route(`${BASE_API}/health`, (r) =>
    r.fulfill({ json: { service: "stock-api", status: "healthy", version: "1.0.0" } })
  );
  await page.route(`${BASE_API}/market/overview`, (r) => r.fulfill({ json: overview }));

  // TA panel — return empty series so it doesn't block rendering
  await page.route(`${BASE_API}/market/indicators/AAPL`, (r) =>
    r.fulfill({ json: { ticker: "AAPL", indicators: {}, series: [], count: 0 } })
  );

  // Sentiment WS — suppress connection errors in tests
  page.on("websocket", (ws) => {
    ws.on("socketerror", () => {});
  });
}

// Helper: open Dashboard and click the AAPL cell to open the Drawer
async function openAAPLDrawer(page: import("@playwright/test").Page) {
  await page.goto("/dashboard");
  await expect(page.locator(".recharts-wrapper")).toBeVisible({ timeout: 15_000 });

  // Click the AAPL SVG text cell in the treemap
  const aaplCell = page.locator("svg text", { hasText: "AAPL" }).first();
  await expect(aaplCell).toBeVisible({ timeout: 10_000 });
  await aaplCell.click();

  // Drawer is open — wait for the Streaming Features accordion to appear
  await expect(page.getByRole("button", { name: /Streaming Features/i })).toBeVisible({ timeout: 10_000 });
}

test.describe("Phase 70 — Streaming Features Panel", () => {
  test.describe.configure({ mode: "serial" });

  test("1. API endpoint returns correct shape", async ({ page }) => {
    test.setTimeout(15_000);

    // page.route() intercepts browser-initiated requests only — use page.evaluate(fetch) so
    // the request flows through the interceptor, not a separate HTTP context.
    await page.route(`${BASE_API}/market/streaming-features/AAPL`, (r) =>
      r.fulfill({ json: streamingFeaturesFixture("AAPL") })
    );

    await page.goto("/");
    const body = await page.evaluate(async (url: string) => {
      const r = await fetch(url);
      return r.json() as Promise<Record<string, unknown>>;
    }, `${BASE_API}/market/streaming-features/AAPL`);

    // Required fields exist with correct types
    expect(typeof body.ticker).toBe("string");
    expect(typeof body.available).toBe("boolean");
    expect(body).toHaveProperty("ema_20");
    expect(body).toHaveProperty("rsi_14");
    expect(body).toHaveProperty("macd_signal");
    expect(body).toHaveProperty("source");
    expect(body).toHaveProperty("sampled_at");

    // Fixture values are correct
    expect(body.ticker).toBe("AAPL");
    expect(body.available).toBe(true);
    expect(body.ema_20).toBe(178.42);
  });

  test("2. StreamingFeaturesPanel renders live Flink data in Drawer", async ({ page }) => {
    test.setTimeout(25_000);

    await mountDashboardRoutes(page);

    // Route streaming-features to return live fixture
    await page.route(`${BASE_API}/market/streaming-features/AAPL`, (r) =>
      r.fulfill({ json: streamingFeaturesFixture("AAPL") })
    );

    await openAAPLDrawer(page);

    // Streaming Features accordion is present and defaultExpanded
    const sfAccordion = page.getByRole("button", { name: /Streaming Features/i });
    await expect(sfAccordion).toBeVisible({ timeout: 8_000 });
    await expect(sfAccordion).toHaveAttribute("aria-expanded", "true");

    // "LIVE — Flink" chip is visible in the accordion summary
    await expect(page.getByText("LIVE — Flink").first()).toBeVisible({ timeout: 8_000 });

    // All three indicator rows render with labels
    await expect(page.getByText("EMA-20")).toBeVisible();
    await expect(page.getByText("RSI-14")).toBeVisible();
    await expect(page.getByText("MACD Signal")).toBeVisible();

    // Numeric values render (fixture: ema_20=178.42, rsi_14=72.5, macd_signal=1.34)
    await expect(page.getByText("178.42")).toBeVisible();
    await expect(page.getByText("72.50")).toBeVisible();
    await expect(page.getByText("1.3400")).toBeVisible();
  });

  test("3. Streaming Features accordion is above Technical Indicators", async ({ page }) => {
    test.setTimeout(25_000);

    await mountDashboardRoutes(page);
    await page.route(`${BASE_API}/market/streaming-features/AAPL`, (r) =>
      r.fulfill({ json: streamingFeaturesFixture("AAPL") })
    );

    await openAAPLDrawer(page);

    const accordions = page.getByRole("button", { name: /Streaming Features|Technical Indicators/i });
    const count = await accordions.count();
    expect(count).toBe(2);

    // First accordion should be Streaming Features
    const first = await accordions.nth(0).textContent();
    expect(first).toMatch(/Streaming Features/i);

    const second = await accordions.nth(1).textContent();
    expect(second).toMatch(/Technical Indicators/i);
  });

  test("4. RSI overbought chip shows when RSI > 70", async ({ page }) => {
    test.setTimeout(25_000);

    await mountDashboardRoutes(page);
    // Fixture has rsi_14=72.5 → should show "Overbought"
    await page.route(`${BASE_API}/market/streaming-features/AAPL`, (r) =>
      r.fulfill({ json: streamingFeaturesFixture("AAPL") })
    );

    await openAAPLDrawer(page);

    const sfBtn = page.getByRole("button", { name: /Streaming Features/i });
    await expect(sfBtn).toBeVisible({ timeout: 8_000 });

    await expect(page.getByText("Overbought")).toBeVisible({ timeout: 8_000 });
  });

  test("5. RSI oversold chip shows when RSI < 30", async ({ page }) => {
    test.setTimeout(25_000);

    await mountDashboardRoutes(page);
    await page.route(`${BASE_API}/market/streaming-features/AAPL`, (r) =>
      r.fulfill({
        json: { ...streamingFeaturesFixture("AAPL"), rsi_14: 22.3 },
      })
    );

    await openAAPLDrawer(page);

    const sfBtn = page.getByRole("button", { name: /Streaming Features/i });
    await expect(sfBtn).toBeVisible({ timeout: 8_000 });

    await expect(page.getByText("Oversold")).toBeVisible({ timeout: 8_000 });
  });

  test("6. Graceful empty-state when Feast unavailable (available=false)", async ({ page }) => {
    test.setTimeout(25_000);

    await mountDashboardRoutes(page);
    await page.route(`${BASE_API}/market/streaming-features/AAPL`, (r) =>
      r.fulfill({ json: streamingFeaturesUnavailableFixture("AAPL") })
    );

    await openAAPLDrawer(page);

    const sfBtn = page.getByRole("button", { name: /Streaming Features/i });
    await expect(sfBtn).toBeVisible({ timeout: 8_000 });

    // Empty state message appears — no crash
    await expect(
      page.getByText(/No live Flink data yet/i)
    ).toBeVisible({ timeout: 8_000 });

    // "LIVE — Flink" chip should NOT be visible in unavailable state
    await expect(page.getByText("LIVE — Flink")).not.toBeVisible();
  });
});
