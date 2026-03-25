import { test, expect } from "@playwright/test";
import { healthFixture, marketOverviewFixture, backtestFixture } from "./fixtures/api";

test.describe("Backtest page", () => {
  test("stub: page loads with backtest fixture data", async ({ page }) => {
    await page.route("**/health", (route) =>
      route.fulfill({ json: healthFixture() })
    );
    await page.route("**/market/overview", (route) =>
      route.fulfill({ json: marketOverviewFixture() })
    );
    await page.route("http://localhost:8000/backtest/**", (route) =>
      route.fulfill({ json: backtestFixture() })
    );
    await page.goto("/backtest");
    await expect(page.getByRole("heading", { name: "Backtest" })).toBeVisible();
  });
});
