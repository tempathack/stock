import { test, expect } from "@playwright/test";
import { skipIfNotProduction } from "./helpers/production-guard";

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

test.describe.configure({ mode: "serial" });

test.describe("/analytics page", () => {
  skipIfNotProduction(test, [
    {
      url: `${BASE_API_URL}/health`,
      description: "API health endpoint must be 200",
    },
    {
      url: `${BASE_API_URL}/analytics/summary`,
      description: "analytics/summary endpoint must be 200",
    },
  ]);

  test.beforeEach(async ({ page }) => {
    await page.goto("/analytics");
  });

  test("renders /analytics route without crash", async ({ page }) => {
    test.setTimeout(20_000);
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 15_000 });
  });

  test("SystemHealthSummary panel is visible", async ({ page }) => {
    test.setTimeout(20_000);
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByText(/argo cd sync|flink cluster|feast latency|ca last refresh/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("StreamHealthPanel is visible", async ({ page }) => {
    test.setTimeout(20_000);
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /^stream health$/i })).toBeVisible({ timeout: 10_000 });
  });

  test("FeatureFreshnessPanel is visible", async ({ page }) => {
    test.setTimeout(20_000);
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/feature freshness/i)).toBeVisible({ timeout: 10_000 });
  });

  test("OLAPCandleChart is visible with 1H/1D toggle", async ({ page }) => {
    test.setTimeout(20_000);
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/olap candle chart/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: /1h/i })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: /1d/i })).toBeVisible({ timeout: 10_000 });
  });

  test("StreamLagMonitor is visible", async ({ page }) => {
    test.setTimeout(20_000);
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/kafka stream lag/i)).toBeVisible({ timeout: 10_000 });
  });
});
