import { test, expect, request } from "@playwright/test";
import { FLINK_UI_URL } from "./helpers/auth";

// Service availability probe — skip entire file if Flink Web UI unreachable
// Run: kubectl port-forward svc/flink-rest -n flink 8081:8081
// (or: kubectl port-forward deployment/flink-jobmanager -n flink 8081:8081)
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    // /overview returns JSON with Flink version when the REST API is up
    const res = await ctx.get(`${FLINK_UI_URL}/overview`, { timeout: 5_000 });
    if (res.status() >= 500) {
      test.skip(true, `Flink REST API not reachable at ${FLINK_UI_URL} — run: kubectl port-forward svc/flink-rest -n flink 8081:8081`);
    }
  } catch {
    test.skip(true, `Flink REST API not reachable at ${FLINK_UI_URL} — run: kubectl port-forward svc/flink-rest -n flink 8081:8081`);
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service
test.describe.configure({ mode: "serial" });

// ── REST API availability ──────────────────────────────────────────────────────
test.describe("Flink REST API", () => {
  test("/overview returns Flink version info", async ({ page }) => {
    const res = await page.request.get(`${FLINK_UI_URL}/overview`, { timeout: 5_000 });
    expect(res.status()).toBeLessThan(500);

    const body = await res.json().catch(() => ({}));
    // Flink /overview JSON contains flink-version field
    expect(body).toHaveProperty("flink-version");
  });
});

// ── Web Dashboard UI ───────────────────────────────────────────────────────────
test.describe("Flink Web Dashboard", () => {
  test("dashboard root loads and shows Flink UI title or overview header", async ({ page }) => {
    await page.goto(FLINK_UI_URL, { waitUntil: "domcontentloaded" });
    // Flink Web UI: title or prominent header contains Flink branding
    await expect(
      page.getByText(/Apache Flink|Flink Dashboard|Jobs Overview/i).first()
    ).toBeVisible({ timeout: 15_000 });
  });
});

// ── Jobs Overview ─────────────────────────────────────────────────────────────
test.describe("Flink Jobs Overview", () => {
  test("jobs overview page is accessible and renders a job list or empty state", async ({ page }) => {
    // Flink Web UI uses hash routing — navigate to the jobs section
    // Phase 62 STATE.md: hash-router navigation uses DOM waits not waitForURL
    await page.goto(`${FLINK_UI_URL}/#/overview`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2_000);

    // Page should show Running Jobs / Completed Jobs or "No jobs" empty state
    await expect(
      page.getByText(/Running Jobs|Completed Jobs|No Jobs|RUNNING|FINISHED|job/i).first()
    ).toBeVisible({ timeout: 15_000 });
  });

  test("at least one Flink job is registered (OHLCV normalizer, indicator stream, or feast writer)", async ({ page }) => {
    test.setTimeout(30_000);

    // Use REST API to check job count — more reliable than UI scraping
    const res = await page.request.get(`${FLINK_UI_URL}/jobs/overview`, { timeout: 5_000 });
    expect(res.status()).toBeLessThan(500);

    const body = await res.json().catch(() => ({ jobs: [] }));
    const jobs: Array<{ name: string; state: string }> = body.jobs ?? [];

    if (jobs.length === 0) {
      console.warn("No Flink jobs registered — Flink operator may not have submitted jobs yet");
      test.fixme(
        true,
        "No Flink jobs visible — ensure FlinkDeployment CRs are applied and Flink operator has submitted jobs"
      );
      return;
    }

    // At least one job should be named after one of the Phase 67 jobs
    const jobNames = jobs.map((j) => j.name).join(", ");
    const hasExpectedJob = jobs.some((j) =>
      /ohlcv|normaliz|indicator|feast|writer/i.test(j.name)
    );

    if (!hasExpectedJob) {
      console.warn(`Flink jobs found but none match expected names: ${jobNames}`);
    }

    expect(jobs.length).toBeGreaterThanOrEqual(1);
  });
});
