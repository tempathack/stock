import { test, expect, request } from "@playwright/test";
import {
  K8S_DASHBOARD_URL,
  K8S_DASHBOARD_TOKEN,
  loginK8sDashboard,
} from "./helpers/auth";

// Two-stage skip: token check first, then service probe
test.beforeAll(async () => {
  // Stage 1: Skip if token not provided — self-documenting with exact kubectl command
  if (!K8S_DASHBOARD_TOKEN) {
    test.skip(
      true,
      "KUBERNETES_DASHBOARD_TOKEN not set — run: kubectl -n kubernetes-dashboard create token kubernetes-dashboard"
    );
    return;
  }

  // Stage 2: Skip if dashboard service not reachable (kubectl proxy running but dashboard not installed)
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(K8S_DASHBOARD_URL, { timeout: 5_000 });
    // Non-200 means the dashboard is not reachable
    if (!res.ok()) {
      test.skip(
        true,
        `Kubernetes Dashboard service not found at ${K8S_DASHBOARD_URL} — ensure port-forward is running: kubectl port-forward -n kubernetes-dashboard pod/<dashboard-pod> 8443:9090`
      );
    }
  } catch {
    test.skip(
      true,
      `Kubernetes Dashboard not reachable at ${K8S_DASHBOARD_URL} — run: kubectl port-forward -n kubernetes-dashboard pod/<dashboard-pod> 8443:9090`
    );
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service; longer timeout for kubectl proxy latency
test.describe.configure({ mode: "serial" });
test.setTimeout(90_000);

// ── Token login and cluster overview ─────────────────────────────────────────
test.describe("Kubernetes Dashboard", () => {
  test("authenticates with bearer token and reaches the dashboard", async ({
    page,
  }) => {
    // K8S_DASHBOARD_TOKEN is guaranteed non-null here (beforeAll skips if undefined)
    await loginK8sDashboard(page, K8S_DASHBOARD_TOKEN!);
    // Post-login: assert cluster overview content visible
    await expect(
      page
        .getByText(/Cluster|Namespace|Workloads/i)
        .first()
    ).toBeVisible({ timeout: 15_000 });
  });

  test("cluster workloads section is accessible", async ({ page }) => {
    await loginK8sDashboard(page, K8S_DASHBOARD_TOKEN!);
    // Navigate to workloads section (either by sidebar click or URL)
    // Use text-based nav — CSS class selectors vary by dashboard version
    const workloadsLink = page.getByRole("link", { name: /workloads/i }).first();
    if (await workloadsLink.isVisible({ timeout: 5_000 })) {
      await workloadsLink.click();
    }
    // Assert some workload-related content renders
    await expect(
      page
        .getByText(/Deployments|Pods|ReplicaSets|Workloads/i)
        .first()
    ).toBeVisible({ timeout: 15_000 });
  });
});
