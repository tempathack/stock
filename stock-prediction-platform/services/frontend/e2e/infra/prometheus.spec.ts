import { test, expect, request } from "@playwright/test";
import { PROMETHEUS_URL } from "./helpers/auth";

// Service availability probe — skip entire file if Prometheus unreachable
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${PROMETHEUS_URL}/-/healthy`, { timeout: 5_000 });
    if (!res.ok()) {
      test.skip(true, `Prometheus not reachable at ${PROMETHEUS_URL}`);
    }
  } catch {
    test.skip(true, `Prometheus not reachable at ${PROMETHEUS_URL}`);
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service
test.describe.configure({ mode: "serial" });

// ── Query execution ───────────────────────────────────────────────────────────
test.describe("Prometheus query execution", () => {
  test("executes PromQL query 'up' and shows results", async ({ page }) => {
    await page.goto(`${PROMETHEUS_URL}/graph`);
    // CodeMirror 6 input — use .click() + keyboard.type() (page.fill() unreliable on CodeMirror)
    await page.locator(".cm-content").click();
    await page.keyboard.type("up");
    await page.getByRole("button", { name: /execute/i }).click();
    // Results appear as graph or table
    await expect(
      page.locator(".graph-root, table.table").first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Prometheus homepage loads", async ({ page }) => {
    await page.goto(`${PROMETHEUS_URL}/`);
    // Prometheus redirects / to /graph — wait for the Execute button rendered by the React SPA
    await expect(
      page.getByRole("button", { name: /execute/i })
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ── Targets ───────────────────────────────────────────────────────────────────
test.describe("Prometheus targets", () => {
  test("targets page shows kubernetes-pods scrape job", async ({ page }) => {
    await page.goto(`${PROMETHEUS_URL}/targets`);
    // Use the visible pool anchor link rather than the hidden dropdown button
    await expect(page.getByRole("link", { name: /kubernetes-pods/ }).first()).toBeVisible({ timeout: 10_000 });
  });
});

// ── Alerts ────────────────────────────────────────────────────────────────────
test.describe("Prometheus alerts", () => {
  test("alerts page is accessible and shows configured alert rules", async ({ page }) => {
    await page.goto(`${PROMETHEUS_URL}/alerts`);
    // Assert at least one known alert name is present — state (firing/pending) may vary
    await expect(
      page
        .getByText("HighDriftSeverity")
        .or(page.getByText("HighAPIErrorRate"))
        .or(page.getByText("HighConsumerLag"))
        .first()
    ).toBeVisible({ timeout: 10_000 });
  });
});
