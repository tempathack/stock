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
    // 503 from kubectl proxy means the dashboard service is not deployed
    if (res.status() === 503) {
      test.skip(
        true,
        `Kubernetes Dashboard service not found at ${K8S_DASHBOARD_URL} — dashboard may not be installed. Install with: kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml`
      );
    }
  } catch {
    test.skip(
      true,
      `Kubernetes Dashboard not reachable at ${K8S_DASHBOARD_URL} — ensure kubectl proxy is running: kubectl proxy --port=8001`
    );
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service
test.describe.configure({ mode: "serial" });

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
    const workloadsLink = page.getByRole("link", { name: /workloads/i });
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
