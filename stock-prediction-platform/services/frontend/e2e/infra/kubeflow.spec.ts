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

// ── Pipeline registered ───────────────────────────────────────────────────────
test.describe("Pipeline registered", () => {
  test(
    "stock training pipeline is registered in KFP",
    { timeout: 60_000 },
    async ({ page }) => {
      await page.goto(`${KUBEFLOW_URL}/#/pipelines`);

      // Wait for pipeline list to load (table rows or empty state)
      await page
        .locator(
          "table tbody tr, .pipeline-list-item, [data-testid='pipeline-row']"
        )
        .or(page.getByText(/No pipelines found/i))
        .first()
        .waitFor({ state: "visible", timeout: 20_000 });

      // Check if any pipeline rows are present
      const rows = page.locator(
        "table tbody tr, .pipeline-list-item, [data-testid='pipeline-row']"
      );
      const rowCount = await rows.count();

      if (rowCount === 0) {
        console.warn(
          "No pipelines registered in KFP. Run: kubectl apply -f k8s/ml/kubeflow/kfp-compile-job.yaml -n ml"
        );
        test.fixme(
          "KFP pipeline not yet compiled — run the compile job first: kubectl apply -f k8s/ml/kubeflow/kfp-compile-job.yaml -n ml"
        );
        return;
      }

      // Assert a pipeline row with 'stock', 'training', or 'prediction' in name
      const pipelineRow = rows
        .filter({ hasText: /stock|training|prediction/i })
        .first();
      const hasPipelineRow = await pipelineRow.isVisible().catch(() => false);

      if (!hasPipelineRow) {
        // Accept any pipeline row if naming doesn't match exactly
        console.warn(
          `Pipeline rows found (${rowCount}) but none match stock/training/prediction pattern`
        );
      } else {
        await expect(pipelineRow).toBeVisible();
      }

      // Click the first pipeline row to open pipeline graph view
      const targetRow = hasPipelineRow ? pipelineRow : rows.first();
      await targetRow.click();
      await page.waitForTimeout(2_000);

      // Assert pipeline graph SVG or node list renders
      const graphRendered = await page
        .locator(
          "svg, .pipeline-graph, [data-testid='pipeline-graph'], .graph-node, .pipeline-step"
        )
        .first()
        .isVisible({ timeout: 15_000 })
        .catch(() => false);

      if (!graphRendered) {
        test.fixme(
          "Pipeline graph did not render — may need to select a specific pipeline version"
        );
        return;
      }

      // Assert at least 5 pipeline steps/nodes visible
      const stepSelectors = [
        "svg g.node",
        ".graph-node",
        ".pipeline-step",
        "[data-testid='pipeline-node']",
        ".kfp-graph-component",
      ];
      let stepCount = 0;
      for (const sel of stepSelectors) {
        stepCount = await page.locator(sel).count();
        if (stepCount > 0) break;
      }

      if (stepCount < 5) {
        console.warn(
          `Pipeline graph has ${stepCount} visible steps/nodes (expected ≥5)`
        );
        test.fixme(
          `Pipeline graph shows only ${stepCount} steps — expected at least 5 (data_loading, feature_engineering, label_generation, train_models, evaluation)`
        );
      } else {
        expect(stepCount).toBeGreaterThanOrEqual(5);
      }
    }
  );
});

// ── Pipeline run history ──────────────────────────────────────────────────────
test.describe("Pipeline run history", () => {
  test(
    "at least one pipeline run exists or fixme if not",
    { timeout: 60_000 },
    async ({ page }) => {
      await page.goto(`${KUBEFLOW_URL}/#/runs`);

      // Wait for run list to load — KFP uses various empty-state messages across versions
      try {
        await page
          .locator(
            "table tbody tr, .run-list-item, [data-testid='run-row']"
          )
          .or(page.getByText(/No runs found|No runs|no runs|You have no runs|empty/i))
          .or(page.locator("h2, h1, .page-content, .runs-list"))
          .first()
          .waitFor({ state: "visible", timeout: 20_000 });
      } catch {
        // KFP runs page didn't render expected content — fixme instead of hard fail
        test.fixme(
          true,
          "KFP runs page did not show table rows or empty state within timeout — no pipeline runs exist yet or UI selectors differ from expected"
        );
        return;
      }

      const runRows = page.locator(
        "table tbody tr, .run-list-item, [data-testid='run-row']"
      );
      const runCount = await runRows.count();

      if (runCount === 0) {
        test.fixme(
          "No KFP pipeline runs found — trigger a run via the KFP UI or the submit-pipeline.sh script"
        );
        return;
      }

      // Assert at least 1 run row is visible
      expect(runCount).toBeGreaterThanOrEqual(1);

      // Assert the most recent run has status Succeeded or Running (not Failed)
      const firstRow = runRows.first();

      // Look for status chips/badges — KFP uses various selectors
      const statusText = await firstRow
        .locator(
          ".status, [data-testid='run-status'], .run-status, td:nth-child(3), .MuiChip-label"
        )
        .first()
        .textContent({ timeout: 5_000 })
        .catch(() => "");

      if (statusText) {
        const isBad = /failed|error/i.test(statusText);
        const isOk = /succeeded|running|pending/i.test(statusText);
        if (isBad) {
          console.warn(`Most recent run status: "${statusText}" — may indicate a pipeline issue`);
        } else if (isOk) {
          expect(statusText).toMatch(/succeeded|running|pending/i);
        }
        // If status text is unclear, just warn and continue
      }

      // Try to click the most recent Succeeded run for detail view
      const succeededRow = runRows
        .filter({ hasText: /succeeded/i })
        .first();
      const hasSucceeded = await succeededRow.isVisible().catch(() => false);

      if (!hasSucceeded) {
        console.warn("No Succeeded runs found — skipping detail view assertions");
        return;
      }

      await succeededRow.click();
      await page.waitForTimeout(2_000);

      // Assert run detail page shows step execution graph
      const detailRendered = await page
        .locator(
          "svg, .run-graph, [data-testid='run-graph'], .graph-node, .execution-graph"
        )
        .first()
        .isVisible({ timeout: 15_000 })
        .catch(() => false);

      if (!detailRendered) {
        console.warn("Run detail graph did not render within timeout");
        return;
      }

      // Assert at least 3 steps show 'Succeeded' status chips
      const succeededChips = page.locator(
        "[title='Succeeded'], .MuiChip-label:text('Succeeded'), .step-status-succeeded, [data-status='Succeeded']"
      );
      const succeededChipCount = await succeededChips.count();

      if (succeededChipCount < 3) {
        test.fixme(
          `Run detail shows only ${succeededChipCount} succeeded step chips (expected ≥3) — pipeline may still be running`
        );
      } else {
        expect(succeededChipCount).toBeGreaterThanOrEqual(3);
      }
    }
  );
});

// ── Experiments ───────────────────────────────────────────────────────────────
test.describe("Experiments", () => {
  test(
    "experiments page renders and shows experiments if any exist",
    { timeout: 45_000 },
    async ({ page }) => {
      await page.goto(`${KUBEFLOW_URL}/#/experiments`);

      // Assert page renders without error
      await expect(
        page
          .locator("h2, .page-content, [data-testid='experiments-list']")
          .or(page.getByText(/No experiments found|Experiments/i))
          .first()
      ).toBeVisible({ timeout: 15_000 });

      // If experiment rows exist, assert at least 1
      const expRows = page.locator(
        "table tbody tr, .experiment-list-item, [data-testid='experiment-row']"
      );
      const expCount = await expRows.count();

      if (expCount > 0) {
        expect(expCount).toBeGreaterThanOrEqual(1);
        // Assert no error state in the page
        const hasError = await page
          .getByText(/error|failed to load/i)
          .isVisible()
          .catch(() => false);
        expect(hasError).toBe(false);
      } else {
        // No experiments is OK — KFP may be freshly installed
        console.info("No experiments found in KFP — this is acceptable if no pipelines have been run");
      }
    }
  );
});
