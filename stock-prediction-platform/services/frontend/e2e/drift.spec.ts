import { test, expect } from "@playwright/test";
import {
  healthFixture,
  driftStatusFixture,
  modelComparisonFixture,
  rollingPerformanceFixture,
  retrainStatusFixture,
} from "./fixtures/api";

test.describe("Drift page", () => {
  test("stub: page loads with all drift fixture data", async ({ page }) => {
    await page.route("**/health", (route) =>
      route.fulfill({ json: healthFixture() })
    );
    // Register rolling-performance BEFORE models/drift (longer path must match first)
    await page.route("**/models/drift/rolling-performance**", (route) =>
      route.fulfill({ json: rollingPerformanceFixture() })
    );
    await page.route("**/models/drift", (route) =>
      route.fulfill({ json: driftStatusFixture() })
    );
    await page.route("**/models/comparison", (route) =>
      route.fulfill({ json: modelComparisonFixture() })
    );
    await page.route("**/models/retrain-status", (route) =>
      route.fulfill({ json: retrainStatusFixture() })
    );
    await page.goto("/drift");
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
  });
});
