import { test, expect, request } from "@playwright/test";
import {
  healthFixture,
  driftStatusFixture,
  modelComparisonFixture,
  rollingPerformanceFixture,
  retrainStatusFixture,
} from "./fixtures/api";

// Helper: stub all Drift page routes
// CRITICAL: rolling-performance MUST be registered BEFORE models/drift
async function stubDriftRoutes(page: import("@playwright/test").Page) {
  await page.route("**/health", (route) => route.fulfill({ json: healthFixture() }));
  // Register more-specific path FIRST (Playwright matches in registration order)
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
}

test.describe("Drift page", () => {
  test.beforeAll(async () => {
    const ctx = await request.newContext();
    try {
      const healthRes = await ctx.get("http://localhost:8000/health", { timeout: 5_000 });
      if (!healthRes.ok()) {
        test.skip(true, "Backend API is not running at http://localhost:8000 — start the API first");
        return;
      }
      // Drift page requires both models comparison data (for ActiveModelCard) and drift events
      const compRes = await ctx.get("http://localhost:8000/models/comparison", { timeout: 5_000 });
      if (!compRes.ok()) {
        test.skip(true, "GET /models/comparison failed — backend unhealthy");
        return;
      }
      const compData = await compRes.json();
      if (!compData?.models?.length) {
        test.skip(true, "GET /models/comparison returned 0 models — run the training pipeline first");
        return;
      }
      const driftRes = await ctx.get("http://localhost:8000/models/drift", { timeout: 5_000 });
      if (!driftRes.ok()) {
        test.skip(true, "GET /models/drift failed — backend unhealthy");
        return;
      }
      const driftData = await driftRes.json();
      if (!driftData?.events?.length) {
        test.skip(true, "GET /models/drift returned 0 events — run the drift detection pipeline first");
      }
    } catch {
      test.skip(true, "Backend API is not running at http://localhost:8000 — start the API first");
    } finally {
      await ctx.dispose();
    }
  });

  test.describe.configure({ mode: "serial" });

  test("page loads with all 4 fixtures and renders heading", async ({ page }) => {
    await stubDriftRoutes(page);
    await page.goto("/drift");
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
  });

  test("ActiveModelCard shows winner model from fixture (fixture_stacking_ensemble_meta_ridge)", async ({
    page,
  }) => {
    await stubDriftRoutes(page);
    await page.goto("/drift");
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
    // ActiveModelCard: winner from modelComparisonFixture
    await expect(
      page.getByText("fixture_stacking_ensemble_meta_ridge").first()
    ).toBeVisible();
    // ActiveModelCard shows "Active" badge
    await expect(page.getByText("Active").first()).toBeVisible();
  });

  test("RetrainStatusPanel shows fixture model and previous model", async ({ page }) => {
    await stubDriftRoutes(page);
    await page.goto("/drift");
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
    // retrainStatusFixture.model_name = "fixture_stacking_ensemble_meta_ridge"
    // retrainStatusFixture.previous_model = "fixture_ridge_quantile"
    // Both should appear in the RetrainStatusPanel section
    await expect(
      page.getByText("fixture_stacking_ensemble_meta_ridge").first()
    ).toBeVisible();
    await expect(page.getByText("fixture_ridge_quantile").first()).toBeVisible();
  });

  test("DriftTimeline shows drift event type from fixture", async ({ page }) => {
    await stubDriftRoutes(page);
    await page.goto("/drift");
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
    // driftStatusFixture events[0].drift_type = "data_drift"
    // DriftTimeline renders the label "Data" (from DRIFT_TYPE_STYLES map) not the raw "data_drift" key
    // Also confirm the timeline heading is visible
    await expect(page.getByRole("heading", { name: "Drift Event Timeline" })).toBeVisible();
    await expect(page.getByText("Data").first()).toBeVisible();
  });

  test("RollingPerformanceChart container is visible", async ({ page }) => {
    await stubDriftRoutes(page);
    await page.goto("/drift");
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
    // RollingPerformanceChart renders inside a card with heading text
    // Do not assert on SVG internals — assert on chart container or label text
    await expect(
      page.getByText(/Rolling.*Performance|Performance Over Time/i).first()
    ).toBeVisible();
  });

  test("page does not show loading spinner after all 4 routes resolve", async ({ page }) => {
    await stubDriftRoutes(page);
    await page.goto("/drift");
    // LoadingSpinner renders <div role="status"> or a specific class
    // If any route was not stubbed, spinner stays — confirm it's gone
    await expect(page.getByRole("heading", { name: "Drift Monitoring" })).toBeVisible();
    // Drift page should NOT be showing loading state
    await expect(page.getByText("Loading...")).not.toBeVisible();
  });
});
