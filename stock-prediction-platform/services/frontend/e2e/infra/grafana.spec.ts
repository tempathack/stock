import { test, expect, request } from "@playwright/test";
import {
  GRAFANA_URL,
  loginGrafana,
} from "./helpers/auth";

// Service availability probe — skip entire file if Grafana unreachable
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${GRAFANA_URL}/api/health`, { timeout: 5_000 });
    if (!res.ok()) {
      test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
    }
  } catch {
    test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service, shared state
test.describe.configure({ mode: "serial" });

// ── Login ────────────────────────────────────────────────────────────────────
test.describe("Grafana login", () => {
  test("logs in with admin credentials and lands on home", async ({ page }) => {
    await page.goto(`${GRAFANA_URL}/login`);
    await page.getByLabel("Email or username").fill("admin");
    await page.getByLabel("Password").fill("admin");
    await page.getByRole("button", { name: "Log in" }).click();
    await page.waitForURL(`${GRAFANA_URL}/**`, { timeout: 10_000 });
    // Assert logged-in state — Grafana 10.x shows "Welcome to Grafana" or home dashboard
    await expect(
      page.getByText(/Welcome to Grafana/i).or(page.getByText(/Home/i)).first()
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ── Datasources ───────────────────────────────────────────────────────────────
test.describe("Grafana datasources", () => {
  test("Prometheus datasource is configured", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/connections/datasources`);
    await expect(page.getByText("Prometheus")).toBeVisible({ timeout: 10_000 });
  });

  test("Loki datasource is configured", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/connections/datasources`);
    await expect(page.getByText("Loki")).toBeVisible({ timeout: 10_000 });
  });
});

// ── Dashboards ────────────────────────────────────────────────────────────────
test.describe("Grafana dashboards", () => {
  test("API Health dashboard renders", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);
    // Navigate by title text — avoids UID fragility
    await page.getByText("API Health").click();
    // Grafana panels load async — wait for a known panel title
    await expect(
      page.getByText("Request Rate").or(page.getByText("Error Rate %")).first()
    ).toBeVisible({ timeout: 20_000 });
  });

  test("ML Performance dashboard renders", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);
    await page.getByText("ML Performance").click();
    await expect(
      page.getByText("Predictions by Model").or(page.getByText("Inference Errors")).first()
    ).toBeVisible({ timeout: 20_000 });
  });

  test("Kafka & Infrastructure dashboard renders", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);
    await page.getByText("Kafka & Infrastructure").click();
    await expect(
      page.getByText("Messages Consumed Rate").or(page.getByText("Consumer Lag")).first()
    ).toBeVisible({ timeout: 20_000 });
  });
});
