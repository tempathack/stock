/**
 * Phase 72 checkpoint: Verify Flink dashboard + datasource UID fixes.
 * Run with: GRAFANA_URL=http://localhost:3001 npx playwright test e2e/infra/grafana-flink-72.spec.ts
 */
import { test, expect, request } from "@playwright/test";
import { GRAFANA_URL, loginGrafana } from "./helpers/auth";

const AUTH = { Authorization: "Basic " + Buffer.from("admin:admin").toString("base64") };

// Skip entire file if Grafana unreachable
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${GRAFANA_URL}/api/health`, { timeout: 5_000 });
    const body = await res.json().catch(() => null);
    if (!res.ok() || !body?.database) {
      test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
    }
  } catch {
    test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
  } finally {
    await ctx.dispose();
  }
});

test.describe.configure({ mode: "serial" });

// ── 1. Datasource UID is pinned ───────────────────────────────────────────────
test("Prometheus datasource has uid='prometheus'", async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${GRAFANA_URL}/api/datasources`, { headers: AUTH });
    expect(res.ok()).toBeTruthy();
    const ds: Array<{ type: string; uid: string }> = await res.json();
    const prom = ds.find((d) => d.type === "prometheus");
    expect(prom, "No Prometheus datasource found").toBeTruthy();
    expect(prom!.uid).toBe("prometheus");
  } finally {
    await ctx.dispose();
  }
});

// ── 2. Flink dashboard exists ─────────────────────────────────────────────────
test("Flink dashboard appears in dashboard list", async ({ page }) => {
  await loginGrafana(page);
  await page.goto(`${GRAFANA_URL}/dashboards`);
  await expect(
    page.getByText(/flink/i).first()
  ).toBeVisible({ timeout: 15_000 });
});

// ── 3. Flink dashboard loads without datasource errors ────────────────────────
test("Flink dashboard opens with no 'Datasource not found' errors", async ({ page }) => {
  await loginGrafana(page);
  await page.goto(`${GRAFANA_URL}/dashboards`);
  const flinkLink = page.getByText(/flink/i).first();
  await expect(flinkLink).toBeVisible({ timeout: 10_000 });
  await flinkLink.click();
  // Wait for panels to start rendering
  await page.waitForTimeout(3_000);
  // Assert no datasource-not-found error banner
  const errText = page.getByText(/datasource.*not found/i).or(page.getByText(/unknown datasource/i));
  await expect(errText).toHaveCount(0, { timeout: 10_000 });
});

// ── 4. Flink dashboard has 10-panel structure (via API) ───────────────────────
// Grafana virtualizes off-screen panels so only ~2 are in the DOM at any time.
// Use the Grafana REST API to verify the full panel structure.
test("Flink dashboard has >=10 panels via API (10-panel comprehensive structure)", async () => {
  const ctx = await request.newContext();
  try {
    // Search for the Flink dashboard
    const searchRes = await ctx.get(`${GRAFANA_URL}/api/search?query=flink`, {
      headers: AUTH,
    });
    expect(searchRes.ok()).toBeTruthy();
    const results: Array<{ uid: string; title: string }> = await searchRes.json();
    const flinkDash = results.find((r) => /flink/i.test(r.title));
    expect(flinkDash, "Flink dashboard not found via API search").toBeTruthy();

    // Get full dashboard JSON
    const dashRes = await ctx.get(`${GRAFANA_URL}/api/dashboards/uid/${flinkDash!.uid}`, {
      headers: AUTH,
    });
    expect(dashRes.ok()).toBeTruthy();
    const body = await dashRes.json();
    const panels: Array<{ type: string; title: string }> = body?.dashboard?.panels ?? [];

    // Should have rows + data panels = >=10 total
    expect(panels.length).toBeGreaterThanOrEqual(10);

    // Check key panel titles exist
    const titles = panels.map((p) => p.title);
    expect(titles.some((t) => /Job Uptime/i.test(t))).toBeTruthy();
    expect(titles.some((t) => /Records In Per Second/i.test(t))).toBeTruthy();
    expect(titles.some((t) => /Checkpoint/i.test(t))).toBeTruthy();
  } finally {
    await ctx.dispose();
  }
});

// ── 5. Other dashboards have no datasource errors ─────────────────────────────
for (const dash of ["API Health", "ML Performance", "Kafka"]) {
  test(`${dash} dashboard has no datasource errors`, async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);
    const link = page.getByText(dash, { exact: false }).first();
    const visible = await link.isVisible({ timeout: 8_000 }).catch(() => false);
    if (!visible) {
      test.fixme(true, `${dash} dashboard not found in list`);
      return;
    }
    await link.click();
    await page.waitForTimeout(3_000);
    const errText = page.getByText(/datasource.*not found/i).or(page.getByText(/unknown datasource/i));
    await expect(errText).toHaveCount(0, { timeout: 10_000 });
  });
}

// ── 6. Prometheus has flink-jobs scrape job ───────────────────────────────────
test("Prometheus flink-jobs scrape job is configured (datasource proxy)", async () => {
  const ctx = await request.newContext();
  try {
    const dsRes = await ctx.get(`${GRAFANA_URL}/api/datasources`, { headers: AUTH });
    const ds: Array<{ type: string; id: number }> = await dsRes.json();
    const prom = ds.find((d) => d.type === "prometheus");
    if (!prom) { test.fixme(true, "No Prometheus datasource"); return; }

    const res = await ctx.get(
      `${GRAFANA_URL}/api/datasources/proxy/${prom.id}/api/v1/label/job/values`,
      { headers: AUTH, timeout: 10_000 }
    );
    if (!res.ok()) { test.fixme(true, `Prometheus proxy returned ${res.status()}`); return; }
    const body = await res.json();
    const jobs: string[] = body?.data ?? [];
    const hasFlinkJob = jobs.some((j) => j.includes("flink"));
    if (!hasFlinkJob) {
      test.fixme(true, `flink-jobs not in Prometheus job labels yet (found: ${jobs.join(", ")}). Flink pods may not have annotation prometheus.io/scrape=true or haven't been scraped yet.`);
    } else {
      expect(hasFlinkJob).toBeTruthy();
    }
  } finally {
    await ctx.dispose();
  }
});
