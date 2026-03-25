import { test, expect } from "@playwright/test";
import {
  healthFixture,
  marketOverviewFixture,
  bulkPredictionsFixture,
  availableHorizonsFixture,
} from "./fixtures/api";

test.describe("Forecasts page", () => {
  test("stub: page loads with forecast fixture data", async ({ page }) => {
    await page.route("**/health", (route) =>
      route.fulfill({ json: healthFixture() })
    );
    await page.route("**/predict/horizons", (route) =>
      route.fulfill({ json: availableHorizonsFixture() })
    );
    await page.route("**/predict/bulk**", (route) =>
      route.fulfill({ json: bulkPredictionsFixture() })
    );
    await page.route("**/market/overview", (route) =>
      route.fulfill({ json: marketOverviewFixture() })
    );
    await page.goto("/forecasts");
    await expect(page.getByRole("heading", { name: "Stock Forecasts" })).toBeVisible();
  });
});
