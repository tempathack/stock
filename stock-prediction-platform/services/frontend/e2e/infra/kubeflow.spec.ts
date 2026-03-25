import { test, expect, request } from "@playwright/test";
import { KUBEFLOW_URL } from "./helpers/auth";

// Service availability probe — skip if Kubeflow UI not reachable
// Note: KFP may not be installed on the cluster — the probe handles this gracefully
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(KUBEFLOW_URL, { timeout: 5_000 });
    if (res.status() >= 500) {
      test.skip(
        true,
        `Kubeflow Pipelines UI not reachable at ${KUBEFLOW_URL} — ensure KFP is deployed and port-forward is running: kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow`
      );
    }
  } catch {
    test.skip(
      true,
      `Kubeflow Pipelines UI not reachable at ${KUBEFLOW_URL} — ensure KFP is deployed and port-forward is running: kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow`
    );
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service
test.describe.configure({ mode: "serial" });

// ── Pipeline list ─────────────────────────────────────────────────────────────
test.describe("Kubeflow Pipelines UI", () => {
  test("pipeline list page renders (may be empty)", async ({ page }) => {
    // KFP uses hash routing — navigate to /#/pipelines
    await page.goto(`${KUBEFLOW_URL}/#/pipelines`);
    // CRITICAL: Do NOT use waitForURL for hash routing (Pitfall 3) — wait for DOM element
    // Assert list container or empty state renders — either is valid
    await expect(
      page
        .locator("h2, .page-content, [data-testid='pipeline-list']")
        .or(page.getByText(/No pipelines found|Pipelines/i))
        .first()
    ).toBeVisible({ timeout: 15_000 });
  });

  test("runs page renders (may be empty)", async ({ page }) => {
    await page.goto(`${KUBEFLOW_URL}/#/runs`);
    // Wait for DOM element — not URL (hash router)
    await expect(
      page
        .locator("h2, .page-content")
        .or(page.getByText(/No runs found|Runs/i))
        .first()
    ).toBeVisible({ timeout: 15_000 });
  });

  test("experiments page renders (may be empty)", async ({ page }) => {
    await page.goto(`${KUBEFLOW_URL}/#/experiments`);
    await expect(
      page
        .locator("h2, .page-content")
        .or(page.getByText(/No experiments found|Experiments/i))
        .first()
    ).toBeVisible({ timeout: 15_000 });
  });
});
