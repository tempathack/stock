import { test, expect } from "@playwright/test";
import { healthFixture, modelComparisonFixture } from "./fixtures/api";

test.describe("Models page", () => {
  test("stub: page loads with model comparison fixture data", async ({ page }) => {
    await page.route("**/health", (route) =>
      route.fulfill({ json: healthFixture() })
    );
    await page.route("**/models/comparison", (route) =>
      route.fulfill({ json: modelComparisonFixture() })
    );
    await page.goto("/models");
    await expect(page.getByRole("heading", { name: "Model Comparison" })).toBeVisible();
  });
});
