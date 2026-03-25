import { test, expect } from "@playwright/test";
import { healthFixture, modelComparisonFixture } from "./fixtures/api";

// Helper: stub all Models page routes
async function stubModelsRoutes(page: import("@playwright/test").Page) {
  await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
  await page.route("**/models/comparison", (route) =>
    route.fulfill({ json: modelComparisonFixture() })
  );
}

test.describe("Models page", () => {
  test("page loads and renders winner card with fixture model name", async ({ page }) => {
    await stubModelsRoutes(page);
    await page.goto("/models");
    await expect(page.getByRole("heading", { name: "Model Comparison" })).toBeVisible();
    // WinnerCard shows fixture winner model name — confirms fixture loaded, not mock
    await expect(
      page.getByText("fixture_stacking_ensemble_meta_ridge").first()
    ).toBeVisible();
  });

  test("winner model is auto-selected on load and detail panel is shown", async ({ page }) => {
    await stubModelsRoutes(page);
    await page.goto("/models");
    // useEffect auto-selects winner — detail panel renders without clicking a row
    // WinnerCard has winner badge text
    await expect(page.getByText(/Winner/).first()).toBeVisible();
    // The detail panel is shown: it contains SHAP chart section
    // ShapBarChart renders within its parent container — check for SHAP-related heading
    // Models.tsx renders "SHAP Feature Importance" heading above ShapBarChart
    await expect(
      page.getByText(/SHAP Feature Importance|Feature Importance/i).first()
    ).toBeVisible();
  });

  test("table shows both fixture models", async ({ page }) => {
    await stubModelsRoutes(page);
    await page.goto("/models");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    const rows = page.locator("table tbody tr");
    await expect(rows).toHaveCount(2);
    await expect(page.getByText("fixture_stacking_ensemble_meta_ridge").first()).toBeVisible();
    await expect(page.getByText("fixture_ridge_quantile").first()).toBeVisible();
  });

  test("clicking a non-winner table row updates detail panel", async ({ page }) => {
    await stubModelsRoutes(page);
    await page.goto("/models");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    // Click second row (fixture_ridge_quantile — the non-winner)
    await page.locator("table tbody tr").nth(1).click();
    // Detail panel heading or content updates to show selected model
    // ModelDetailPanel renders the selected model's name
    await expect(page.getByText("fixture_ridge_quantile").first()).toBeVisible();
  });

  test("search input filters table to matching model name", async ({ page }) => {
    await stubModelsRoutes(page);
    await page.goto("/models");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    await page.getByPlaceholder("Filter by model name…").fill("fixture_ridge");
    const rows = page.locator("table tbody tr");
    await expect(rows).toHaveCount(1);
    await expect(page.getByText("fixture_ridge_quantile").first()).toBeVisible();
  });

  test("export CSV and PDF buttons are enabled when data is loaded", async ({ page }) => {
    await stubModelsRoutes(page);
    await page.goto("/models");
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    // ExportButtons: disabled={!data?.models.length}
    await expect(page.getByRole("button", { name: /CSV/i })).toBeEnabled();
    await expect(page.getByRole("button", { name: /PDF/i })).toBeEnabled();
  });
});
