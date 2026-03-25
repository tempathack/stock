import { test, expect } from "@playwright/test";
import { healthFixture, marketOverviewFixture } from "./fixtures/api";

test.describe("Dashboard page", () => {
  test("stub: page loads with market overview fixture", async ({ page }) => {
    // Routes MUST be registered before page.goto()
    await page.route("**/health", (route) =>
      route.fulfill({ json: healthFixture() })
    );
    await page.route("**/market/overview", (route) =>
      route.fulfill({ json: marketOverviewFixture() })
    );
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Market Dashboard" })).toBeVisible();
  });
});
