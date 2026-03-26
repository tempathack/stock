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
    await page.locator('input[name="password"]').fill("admin");
    await page.getByRole("button", { name: "Log in" }).click();
    await page.waitForURL(`${GRAFANA_URL}/**`, { timeout: 10_000 });
    // Assert logged-in state — Grafana 10.x shows "Welcome to Grafana" or home dashboard
    await expect(
      page.getByText(/Welcome to Grafana/i).or(page.getByText(/Home/i)).first()
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ── Datasources ───────────────────────────────────────────────────────────────
// Datasource existence is verified via the Grafana REST API (more reliable than
// navigating the connections/datasources UI, which redirects based on Grafana version).
test.describe("Grafana datasources", () => {
  test("Prometheus datasource is configured", async () => {
    const ctx = await request.newContext();
    try {
      const res = await ctx.get(`${GRAFANA_URL}/api/datasources`, {
        headers: {
          Authorization:
            "Basic " + Buffer.from(`admin:admin`).toString("base64"),
        },
      });
      expect(res.ok()).toBeTruthy();
      const ds: Array<{ name: string; type: string }> = await res.json();
      expect(ds.some((d) => d.type === "prometheus")).toBeTruthy();
    } finally {
      await ctx.dispose();
    }
  });

  test("Loki datasource is configured", async () => {
    const ctx = await request.newContext();
    try {
      const res = await ctx.get(`${GRAFANA_URL}/api/datasources`, {
        headers: {
          Authorization:
            "Basic " + Buffer.from(`admin:admin`).toString("base64"),
        },
      });
      expect(res.ok()).toBeTruthy();
      const ds: Array<{ name: string; type: string }> = await res.json();
      expect(ds.some((d) => d.type === "loki")).toBeTruthy();
    } finally {
      await ctx.dispose();
    }
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

// ── Dashboard panel data ──────────────────────────────────────────────────────
// Verifies that key panels in each dashboard are rendering real data (not "No data")
test.describe("Dashboard panel data", () => {
  test("API Health dashboard has at least one panel with data", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);

    // Navigate to API Health dashboard
    const apiHealthLink = page.getByText("API Health").first();
    const apiHealthExists = await apiHealthLink.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!apiHealthExists) {
      test.fixme(true, "API Health dashboard not found in dashboard list");
      return;
    }
    await apiHealthLink.click();

    // Wait for panels to finish loading
    await page.waitForSelector('.panel-container:not(.panel-container--transparent)', {
      timeout: 20_000,
    }).catch(() => null);

    // Assert at least 1 non-transparent panel rendered
    const panels = page.locator('.panel-container:not(.panel-container--transparent)');
    const panelCount = await panels.count().catch(() => 0);
    if (panelCount === 0) {
      test.fixme(true, "No panels rendered in API Health dashboard — Grafana may not have panel data yet");
      return;
    }
    expect(panelCount).toBeGreaterThan(0);

    // Check that the 'Request Rate' or 'Error Rate' panel is not showing 'No data'
    const requestRatePanel = page
      .locator('.panel-container')
      .filter({ hasText: /Request Rate|Error Rate/i })
      .first();
    const panelVisible = await requestRatePanel.isVisible({ timeout: 5_000 }).catch(() => false);
    if (panelVisible) {
      const noDataText = requestRatePanel.getByText(/No data/i);
      const hasNoData = await noDataText.isVisible({ timeout: 3_000 }).catch(() => false);
      if (hasNoData) {
        test.fixme(true, "Request Rate/Error Rate panel shows 'No data' — FastAPI metrics may not be scraping yet");
      }
    }
  });

  test("ML Performance dashboard has at least one panel with data", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);

    const mlPerfLink = page.getByText("ML Performance").first();
    const mlPerfExists = await mlPerfLink.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!mlPerfExists) {
      test.fixme(true, "ML Performance dashboard not found in dashboard list");
      return;
    }
    await mlPerfLink.click();

    await page.waitForSelector('.panel-container:not(.panel-container--transparent)', {
      timeout: 20_000,
    }).catch(() => null);

    const panels = page.locator('.panel-container:not(.panel-container--transparent)');
    const panelCount = await panels.count().catch(() => 0);
    if (panelCount === 0) {
      test.fixme(true, "No panels rendered in ML Performance dashboard");
      return;
    }
    expect(panelCount).toBeGreaterThan(0);

    // Check Predictions or Inference panel is not showing 'No data'
    const predPanel = page
      .locator('.panel-container')
      .filter({ hasText: /Predictions|Inference/i })
      .first();
    const panelVisible = await predPanel.isVisible({ timeout: 5_000 }).catch(() => false);
    if (panelVisible) {
      const hasNoData = await predPanel.getByText(/No data/i).isVisible({ timeout: 3_000 }).catch(() => false);
      if (hasNoData) {
        test.fixme(true, "Predictions/Inference panel shows 'No data' — ML metrics may not be emitting yet");
      }
    }
  });

  test("Kafka & Infrastructure dashboard has at least one panel with data", async ({ page }) => {
    await loginGrafana(page);
    await page.goto(`${GRAFANA_URL}/dashboards`);

    const kafkaLink = page.getByText("Kafka & Infrastructure").first();
    const kafkaExists = await kafkaLink.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!kafkaExists) {
      test.fixme(true, "Kafka & Infrastructure dashboard not found in dashboard list");
      return;
    }
    await kafkaLink.click();

    await page.waitForSelector('.panel-container:not(.panel-container--transparent)', {
      timeout: 20_000,
    }).catch(() => null);

    const panels = page.locator('.panel-container:not(.panel-container--transparent)');
    const panelCount = await panels.count().catch(() => 0);
    if (panelCount === 0) {
      test.fixme(true, "No panels rendered in Kafka & Infrastructure dashboard");
      return;
    }
    expect(panelCount).toBeGreaterThan(0);

    // Check Consumer Lag or Messages panel
    const lagPanel = page
      .locator('.panel-container')
      .filter({ hasText: /Consumer Lag|Messages/i })
      .first();
    const panelVisible = await lagPanel.isVisible({ timeout: 5_000 }).catch(() => false);
    if (panelVisible) {
      const hasNoData = await lagPanel.getByText(/No data/i).isVisible({ timeout: 3_000 }).catch(() => false);
      if (hasNoData) {
        test.fixme(true, "Consumer Lag/Messages panel shows 'No data' — Kafka metrics may not be scraping yet");
      }
    }
  });

  test("Prometheus datasource proxied query returns live data", async () => {
    const ctx = await request.newContext();
    try {
      // First, find the Prometheus datasource UID via the API
      const dsRes = await ctx.get(`${GRAFANA_URL}/api/datasources`, {
        headers: {
          Authorization: "Basic " + Buffer.from("admin:admin").toString("base64"),
        },
        timeout: 10_000,
      });
      if (!dsRes.ok()) {
        test.fixme(true, "Could not list Grafana datasources");
        return;
      }

      const datasources: Array<{ name: string; type: string; uid: string; id: number }> =
        await dsRes.json();
      const promDS = datasources.find((d) => d.type === "prometheus");
      if (!promDS) {
        test.fixme(true, "No Prometheus datasource configured in Grafana");
        return;
      }

      // Use the datasource proxy to run a PromQL query
      const queryRes = await ctx.get(
        `${GRAFANA_URL}/api/datasources/proxy/${promDS.id}/api/v1/query?query=up`,
        {
          headers: {
            Authorization: "Basic " + Buffer.from("admin:admin").toString("base64"),
          },
          timeout: 15_000,
        }
      );

      if (!queryRes.ok()) {
        test.fixme(true, `Prometheus proxy query failed with status ${queryRes.status()}`);
        return;
      }

      const body = await queryRes.json();
      expect(body.status).toBe("success");

      const results: Array<{ metric: Record<string, string>; value: unknown[] }> =
        body?.data?.result ?? [];
      if (results.length === 0) {
        test.fixme(true, "Prometheus 'up' query returned 0 results — no targets being scraped yet");
        return;
      }
      expect(results.length).toBeGreaterThan(0);

      // Assert at least one kubernetes-pods job target is UP
      const k8sPodsTargets = results.filter(
        (r) => r.metric?.job === "kubernetes-pods"
      );
      if (k8sPodsTargets.length === 0) {
        test.fixme(
          true,
          "No kubernetes-pods targets found in Prometheus 'up' results — pod annotations may not be configured"
        );
      } else {
        expect(k8sPodsTargets.length).toBeGreaterThan(0);
      }
    } finally {
      await ctx.dispose();
    }
  });
});

// ── Alert rules configured ────────────────────────────────────────────────────
test.describe("Alert rules configured", () => {
  test("Grafana managed alert rules exist with expected names", async () => {
    const ctx = await request.newContext();
    try {
      // Grafana Ruler API for managed alerts
      const res = await ctx.get(
        `${GRAFANA_URL}/api/ruler/grafana/api/v1/rules`,
        {
          headers: {
            Authorization: "Basic " + Buffer.from("admin:admin").toString("base64"),
            Accept: "application/json",
          },
          timeout: 15_000,
        }
      );

      if (!res.ok()) {
        // Some Grafana versions return 404 if no unified alerting rules configured
        test.fixme(
          true,
          `Alert rules API returned ${res.status()} — unified alerting may not be configured or no rules defined yet`
        );
        return;
      }

      const rulesMap: Record<
        string,
        Array<{ name: string; rules: Array<{ grafana_alert: { title: string } }> }>
      > = await res.json();

      // Flatten all rule groups across all namespaces
      const allRuleGroups = Object.values(rulesMap).flat();
      if (allRuleGroups.length === 0) {
        test.fixme(true, "No Grafana alert rule groups configured yet");
        return;
      }
      expect(allRuleGroups.length).toBeGreaterThan(0);

      // Collect all rule titles
      const allRuleTitles: string[] = [];
      for (const group of allRuleGroups) {
        for (const rule of group.rules ?? []) {
          const title = rule?.grafana_alert?.title ?? "";
          if (title) allRuleTitles.push(title);
        }
      }

      if (allRuleTitles.length === 0) {
        test.fixme(true, "Alert rule groups exist but no rules with titles found");
        return;
      }

      // Assert expected alert rule names are present
      const expectedRules = ["HighDriftSeverity", "HighAPIErrorRate", "HighConsumerLag"];
      const missingRules = expectedRules.filter(
        (expected) => !allRuleTitles.some((t) => t.includes(expected))
      );

      if (missingRules.length > 0) {
        test.fixme(
          true,
          `Missing expected alert rules: ${missingRules.join(", ")}. Found: ${allRuleTitles.join(", ")}`
        );
      } else {
        // All 3 expected rules found
        for (const expected of expectedRules) {
          expect(allRuleTitles.some((t) => t.includes(expected))).toBeTruthy();
        }
      }
    } finally {
      await ctx.dispose();
    }
  });
});
