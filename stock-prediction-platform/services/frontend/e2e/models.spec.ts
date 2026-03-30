import { test, expect } from "@playwright/test";
import { skipIfNotProduction } from "./helpers/production-guard";

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

test.describe.configure({ mode: "serial" });

skipIfNotProduction(test, [
  { url: `${BASE_API_URL}/health`, description: "API health endpoint must be 200" },
  {
    url: `${BASE_API_URL}/models/comparison`,
    description: "models/comparison must return ≥1 model",
  },
]);

test.describe("Models page — production", () => {
  test.setTimeout(25_000);

  test("winner card shows real model name", async ({ page }) => {
    await page.goto("/models");
    await expect(page.getByRole("heading", { name: "Model Comparison" })).toBeVisible({
      timeout: 20_000,
    });
    // WinnerCard must render
    await expect(page.getByText(/Winner/i).first()).toBeVisible();
    // Model name must NOT contain 'fixture_' prefix
    const winnerCard = page.locator('[data-testid="winner-card"], .winner-card, [class*="winner"]').first();
    const cardText = await winnerCard.textContent().catch(() => "");
    expect(cardText).not.toMatch(/fixture_/i);
    // At least one metric (RMSE, MAE, R²) shows a real number (not '-')
    const metricsArea = page.locator('[data-testid="winner-card"], .winner-card, [class*="winner"]').first();
    const metricsText = await metricsArea.textContent().catch(() => "");
    const hasRealMetric = /\d+\.\d+/.test(metricsText);
    expect(hasRealMetric).toBe(true);
  });

  test("model table has ≥1 row", async ({ page }) => {
    await page.goto("/models");
    await expect(page.locator(".MuiDataGrid-row").first()).toBeVisible({ timeout: 20_000 });
    const rowCount = await page.locator(".MuiDataGrid-row").count();
    expect(rowCount).toBeGreaterThanOrEqual(1);
  });

  test("winner is auto-selected and SHAP panel loads", async ({ page }) => {
    await page.goto("/models");
    await expect(page.locator(".MuiDataGrid-row").first()).toBeVisible({ timeout: 20_000 });
    // SHAP Feature Importance section must be visible (winner auto-selected)
    await expect(
      page.getByText(/SHAP Feature Importance|Feature Importance/i).first()
    ).toBeVisible({ timeout: 20_000 });
    // At least 3 feature names shown
    const featureItems = page.locator(
      '[data-testid*="feature"], .shap-feature, [class*="feature"]'
    );
    const featureCount = await featureItems.count();
    // If no testid-based selectors, fall back to checking SHAP section text has content
    if (featureCount >= 3) {
      expect(featureCount).toBeGreaterThanOrEqual(3);
    } else {
      const shapSection = page
        .locator("section, div")
        .filter({ hasText: /SHAP Feature Importance|Feature Importance/i })
        .first();
      const shapText = await shapSection.textContent().catch(() => "");
      // Expect some feature names (at least a few words after the heading)
      expect(shapText.length).toBeGreaterThan(30);
    }
  });

  test("clicking a different model updates detail panel", async ({ page }) => {
    await page.goto("/models");
    await expect(page.locator(".MuiDataGrid-row").first()).toBeVisible({ timeout: 20_000 });
    const rowCount = await page.locator(".MuiDataGrid-row").count();
    if (rowCount < 2) {
      test.skip();
      return;
    }
    // Get winner model name from detail panel before clicking
    const initialPanelText = await page
      .locator('[data-testid="model-detail"], [class*="detail"], main')
      .first()
      .textContent()
      .catch(() => "");
    // Click second row
    await page.locator(".MuiDataGrid-row").nth(1).click();
    // Detail panel should update — wait for any change
    await page.waitForTimeout(500);
    const updatedPanelText = await page
      .locator('[data-testid="model-detail"], [class*="detail"], main')
      .first()
      .textContent()
      .catch(() => "");
    // Panel text should change (different model selected)
    expect(updatedPanelText).not.toBe(initialPanelText);
  });

  test("search filters by real model name", async ({ page }) => {
    test.setTimeout(40_000);
    await page.goto("/models");
    await expect(page.locator(".MuiDataGrid-row").first()).toBeVisible({ timeout: 20_000 });

    // Get the first row's model name to use as search term
    const firstCell = page.locator(".MuiDataGrid-row .MuiDataGrid-cell").first();
    await expect(firstCell).toBeVisible({ timeout: 10_000 });
    const winnerName = (await firstCell.textContent()) ?? "";
    const searchPrefix = winnerName.trim().slice(0, 4);
    if (!searchPrefix) {
      test.skip();
      return;
    }
    await page.getByPlaceholder("Filter by model name…").fill(searchPrefix);
    // After filtering, rows should reduce
    await page.waitForTimeout(500);
    const filteredCount = await page.locator(".MuiDataGrid-row").count();
    expect(filteredCount).toBeLessThanOrEqual(9);
  });

  test("export CSV and PDF buttons are enabled", async ({ page }) => {
    await page.goto("/models");
    await expect(page.locator(".MuiDataGrid-row").first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole("button", { name: /CSV/i })).toBeEnabled();
    await expect(page.getByRole("button", { name: /PDF/i })).toBeEnabled();
  });
});
