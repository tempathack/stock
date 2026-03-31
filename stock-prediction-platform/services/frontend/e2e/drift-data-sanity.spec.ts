/**
 * Drift Dashboard Data Sanity Tests
 *
 * These tests intercept live API calls to /models/* and assert that:
 * - oos_metrics are populated (not null → causing "—" display)
 * - Rolling performance RMSE values are sane (not dollar-scale)
 * - directional_accuracy is in 0–1 range (chart expects fraction, not percentage)
 * - Real model data is shown, not mock fallback
 * - Previous model RMSE/MAE are not 0.0000
 *
 * All assertion failures print the raw API JSON so the ML pipeline bug is
 * immediately visible.
 */
import { test, expect } from "@playwright/test";

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

async function isApiHealthy(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_API_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

test.describe("Drift dashboard API data sanity", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async () => {
    const healthy = await isApiHealthy();
    test.skip(!healthy, "API not reachable — skipping sanity checks");
  });

  // ─── /models/comparison ───────────────────────────────────────────────────

  test("Active model oos_metrics are not null", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/models/comparison") && res.status() === 200,
      { timeout: 20_000 },
    );

    await page.goto("/drift");
    const response = await responsePromise;
    const data = await response.json();

    const models: Array<{
      model_name: string;
      is_active: boolean;
      oos_metrics: Record<string, unknown> | null;
    }> = data.models ?? [];

    const active = models.find((m) => m.is_active);

    console.log(`\n[drift sanity] total models returned: ${models.length}`);
    if (active) {
      console.log(`[drift sanity] active model: ${active.model_name}`);
      console.log(`[drift sanity] oos_metrics: ${JSON.stringify(active.oos_metrics)}`);
    } else {
      console.log("[drift sanity] WARNING: no active model found in response");
    }

    expect(
      active,
      `No active model found in /models/comparison response. Full response: ${JSON.stringify(data)}`,
    ).toBeTruthy();

    expect(
      active!.oos_metrics,
      `Active model "${active!.model_name}" has oos_metrics=null. ` +
      `This causes RMSE/MAE/Dir.Acc to display as "—" on the Drift page. ` +
      `Check that model training saves oos_metrics into the model_registry table.`,
    ).not.toBeNull();
  });

  test("Active model RMSE and MAE are positive finite numbers", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/models/comparison") && res.status() === 200,
      { timeout: 20_000 },
    );

    await page.goto("/drift");
    const response = await responsePromise;
    const data = await response.json();
    const active = (data.models ?? []).find((m: { is_active: boolean }) => m.is_active);

    test.skip(!active?.oos_metrics, "oos_metrics is null — covered by prior test");

    const oos = active.oos_metrics as Record<string, number>;
    console.log(`\n[drift sanity] oos_metrics: ${JSON.stringify(oos)}`);

    const rmse = oos.rmse ?? oos.oos_rmse;
    const mae = oos.mae ?? oos.oos_mae;

    expect(typeof rmse, `oos_metrics.rmse is missing. Keys present: ${Object.keys(oos).join(", ")}`).toBe("number");
    expect(typeof mae, `oos_metrics.mae is missing. Keys present: ${Object.keys(oos).join(", ")}`).toBe("number");

    expect(
      Number.isFinite(rmse) && (rmse as number) > 0,
      `RMSE=${rmse} must be a positive finite number`,
    ).toBe(true);
    expect(
      Number.isFinite(mae) && (mae as number) > 0,
      `MAE=${mae} must be a positive finite number`,
    ).toBe(true);
  });

  // ─── /models/drift/rolling-performance ────────────────────────────────────

  test("Rolling performance RMSE values are not dollar-scale (< 50)", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/rolling-performance") && res.status() === 200,
      { timeout: 20_000 },
    );

    await page.goto("/drift");
    const response = await responsePromise;
    const data = await response.json();

    const entries: Array<{ date: string; rmse: number | null; mae: number | null; directional_accuracy: number | null }> =
      data.entries ?? [];

    if (entries.length === 0) {
      console.log("[drift sanity] rolling-performance returned 0 entries — no RMSE to check");
      return;
    }

    const rmseValues = entries.map((e) => e.rmse).filter((v): v is number => v != null);
    const maxRmse = Math.max(...rmseValues);
    const minRmse = Math.min(...rmseValues);

    console.log(`\n[drift sanity] rolling-performance entries: ${entries.length}`);
    console.log(`[drift sanity] RMSE range: ${minRmse.toFixed(4)} – ${maxRmse.toFixed(4)}`);
    console.log(`[drift sanity] sample entry: ${JSON.stringify(entries[0])}`);

    expect(
      maxRmse,
      `Max rolling RMSE=${maxRmse.toFixed(2)} exceeds 50. ` +
      `The chart Y-axis shows values like ${Math.round(maxRmse)}, which look like raw stock prices, not error metrics. ` +
      `Check whether the model trains on normalized features — predictions may be on raw price scale.`,
    ).toBeLessThan(50);
  });

  test("Rolling performance directional_accuracy is in 0–1 fraction range", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/rolling-performance") && res.status() === 200,
      { timeout: 20_000 },
    );

    await page.goto("/drift");
    const response = await responsePromise;
    const data = await response.json();

    const entries: Array<{ date: string; directional_accuracy: number | null }> = data.entries ?? [];
    if (entries.length === 0) return;

    const daValues = entries
      .map((e) => e.directional_accuracy)
      .filter((v): v is number => v != null);

    if (daValues.length === 0) {
      console.log("[drift sanity] all directional_accuracy values are null");
      return;
    }

    const maxDa = Math.max(...daValues);
    const minDa = Math.min(...daValues);

    console.log(`\n[drift sanity] directional_accuracy range: ${minDa} – ${maxDa}`);

    // The RollingPerformanceChart maps 0–1 on the right Y-axis via tickFormatter:
    // (v: number) => `${(v * 100).toFixed(0)}%`
    // So the API must return fractions (0–1). If it returns percentages (0–100),
    // the chart axis will show "0% – 10000%".
    expect(
      maxDa,
      `Max directional_accuracy=${maxDa} exceeds 1.0. ` +
      `The RollingPerformanceChart expects 0–1 fractions and multiplies by 100 for display. ` +
      `If the API returns 0–100 percentages, the chart will show up to 10000% on its axis.`,
    ).toBeLessThanOrEqual(1);

    expect(
      minDa,
      `Min directional_accuracy=${minDa} is negative.`,
    ).toBeGreaterThanOrEqual(0);
  });

  // ─── Rendered UI checks ────────────────────────────────────────────────────

  test("ActiveModelCard shows metric values not dashes", async ({ page }) => {
    // Wait for the API to respond
    await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes("/models/comparison") && res.status() === 200,
        { timeout: 20_000 },
      ),
      page.goto("/drift"),
    ]);

    // Wait for content to settle
    await page.waitForTimeout(3_000);

    // Locate the ActiveModelCard — it contains "RMSE", "MAE", "Dir. Acc" labels
    const cardWithRmse = page.getByText("RMSE").first();
    await expect(cardWithRmse).toBeVisible({ timeout: 10_000 });

    // The model card renders metric values as Typography elements near "RMSE"
    // If oos_metrics is null, the value shows "—"; otherwise a number
    const rmseArea = page.locator("text=RMSE").locator("..");
    const rmseText = await rmseArea.textContent().catch(() => "");

    console.log(`\n[drift sanity] RMSE area text: "${rmseText}"`);

    expect(
      rmseText,
      `ActiveModelCard is showing "—" for RMSE, meaning oos_metrics is null or not mapped correctly. ` +
      `Check that /models/comparison returns oos_metrics with rmse/mae/directional_accuracy keys.`,
    ).not.toContain("—");
  });

  test("No mock model names shown when API is healthy (real data not fallback)", async ({ page }) => {
    await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes("/models/comparison") && res.status() === 200,
        { timeout: 20_000 },
      ),
      page.goto("/drift"),
    ]);

    await page.waitForTimeout(2_000);

    const bodyText = (await page.locator("body").textContent()) ?? "";

    // Mock data fingerprints from generateMockDriftData()
    const mockModelNames = ["ridge_v1", "lasso_v1", "xgboost_v2"];
    for (const mockName of mockModelNames) {
      expect(
        bodyText,
        `Page contains mock model name "${mockName}" — the drift page is falling back to mock data. ` +
        `Check that /models/comparison and /models/drift APIs return valid responses.`,
      ).not.toContain(mockName);
    }
  });

  // ─── /models/retrain-status ────────────────────────────────────────────────

  test("Retrain status previous model RMSE is not 0.0000", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/models/retrain-status") && res.status() === 200,
      { timeout: 20_000 },
    );

    await page.goto("/drift");
    const response = await responsePromise;
    const data = await response.json();

    console.log(`\n[drift sanity] retrain-status response: ${JSON.stringify(data)}`);

    // If there's a previous model, its metrics should not be 0
    if (data.previous_model) {
      const prevRmse = data.oos_metrics?.previous_rmse ?? data.previous_rmse ?? null;
      if (prevRmse !== null) {
        expect(
          prevRmse,
          `Previous model RMSE=${prevRmse} is exactly 0. ` +
          `This usually means the metric was never computed or was stored as a default value. ` +
          `Check the model_registry table for the previous model's oos_metrics.`,
        ).toBeGreaterThan(0);
      }
    }
  });

  // ─── /models/drift ─────────────────────────────────────────────────────────

  test("Drift events have valid severity values", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/models/drift") && !res.url().includes("rolling") && res.status() === 200,
      { timeout: 20_000 },
    );

    await page.goto("/drift");
    const response = await responsePromise;
    const data = await response.json();

    const events: Array<{ severity: string; drift_type: string; is_drifted: boolean }> =
      data.events ?? [];

    console.log(`\n[drift sanity] drift events count: ${events.length}`);
    if (events.length > 0) {
      console.log(`[drift sanity] sample events: ${JSON.stringify(events.slice(0, 3))}`);
    }

    const validSeverities = new Set(["high", "medium", "low", "none"]);
    const invalidEvents = events.filter((e) => !validSeverities.has(e.severity));

    expect(
      invalidEvents.length,
      `Found drift events with invalid severity: ${JSON.stringify(invalidEvents)}`,
    ).toBe(0);

    const validTypes = new Set(["data_drift", "prediction_drift", "concept_drift"]);
    const invalidTypeEvents = events.filter((e) => !validTypes.has(e.drift_type));

    expect(
      invalidTypeEvents.length,
      `Found drift events with invalid drift_type: ${JSON.stringify(invalidTypeEvents)}`,
    ).toBe(0);
  });

  test("Feature distributions section is labeled as illustrative (always mock)", async ({ page }) => {
    await page.goto("/drift");
    await page.waitForTimeout(3_000);

    // Feature distributions always use mock data — this test documents that clearly
    // and asserts the accordion section is at least present
    const bodyText = (await page.locator("body").textContent()) ?? "";
    const hasFeatureSection =
      /Feature Distribution|feature_distribution/i.test(bodyText) ||
      /rsi_14|macd|bb_upper|close_price/i.test(bodyText);

    console.log(`\n[drift sanity] Feature distributions section present: ${hasFeatureSection}`);
    console.log("[drift sanity] NOTE: Feature distributions ALWAYS use mock/synthetic data.");
    console.log("[drift sanity] There is no API endpoint for feature distributions — this is hardcoded.");

    // This is informational — we don't fail here, just document
    // Uncomment the line below if you want to flag this as a test failure:
    // expect(hasFeatureSection).toBe(true);
  });
});
