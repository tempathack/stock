import type { Page } from "@playwright/test";

// ── URLs (env-var overrides with dev defaults) ──────────────────────────────
export const GRAFANA_URL =
  process.env.GRAFANA_URL ?? "http://localhost:3000";
export const PROMETHEUS_URL =
  process.env.PROMETHEUS_URL ?? "http://localhost:9090";
export const MINIO_URL =
  process.env.MINIO_URL ?? "http://localhost:9002";
export const KUBEFLOW_URL =
  process.env.KUBEFLOW_URL ?? "http://localhost:8888";
// Direct port-forward to dashboard pod (port 8443 → pod:9090) is far faster than
// the kubectl proxy path. Run: kubectl port-forward -n kubernetes-dashboard pod/<dashboard-pod> 8443:9090
export const K8S_DASHBOARD_URL =
  process.env.K8S_DASHBOARD_URL ?? "http://localhost:8443/";

// ── Credentials ─────────────────────────────────────────────────────────────
export const GRAFANA_USER =
  process.env.GRAFANA_USER ?? "admin";
export const GRAFANA_PASSWORD =
  process.env.GRAFANA_PASSWORD ?? "admin";

export const MINIO_USER =
  process.env.MINIO_USER ?? "minioadmin";
export const MINIO_PASSWORD =
  process.env.MINIO_PASSWORD ?? "minioadmin123";

// K8s Dashboard requires a token — no hardcoded default (must be supplied externally)
export const K8S_DASHBOARD_TOKEN =
  process.env.KUBERNETES_DASHBOARD_TOKEN;

// Argo CD UI — port-forward: kubectl port-forward svc/argocd-server -n argocd 8080:443
export const ARGOCD_URL =
  process.env.ARGOCD_URL ?? "http://localhost:8080";

export const ARGOCD_PASSWORD =
  process.env.ARGOCD_PASSWORD ?? "";

// Flink Web UI — port-forward: kubectl port-forward svc/flink-rest -n flink 8081:8081
// (or: kubectl port-forward deploy/flink-jobmanager -n flink 8081:8081)
export const FLINK_UI_URL =
  process.env.FLINK_UI_URL ?? "http://localhost:8081";

// ── Login helpers ────────────────────────────────────────────────────────────

export async function loginGrafana(page: Page): Promise<void> {
  await page.goto(`${GRAFANA_URL}/login`);
  await page.getByLabel("Email or username").fill(GRAFANA_USER);
  await page.locator('input[name="password"]').fill(GRAFANA_PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  // Wait for post-login redirect to home/dashboard
  await page.waitForURL(`${GRAFANA_URL}/**`, { timeout: 10_000 });
}

export async function loginMinIO(page: Page): Promise<void> {
  await page.goto(`${MINIO_URL}/login`);
  // MinIO Console login form — use stable ID-based locators as fallback
  const usernameInput =
    page.locator('input[id="accessKey"]').first().or(page.getByLabel("Username"));
  const passwordInput =
    page.locator('input[id="secretKey"]').first().or(page.getByLabel("Password"));
  await usernameInput.fill(MINIO_USER);
  await passwordInput.fill(MINIO_PASSWORD);
  await page.getByRole("button", { name: /login/i }).click();
  await page.waitForURL(`${MINIO_URL}/**`, { timeout: 10_000 });
}

export async function loginK8sDashboard(
  page: Page,
  token: string
): Promise<void> {
  await page.goto(K8S_DASHBOARD_URL);
  // Some minikube setups skip auth entirely — wait up to 20s for the Workloads
  // nav link to appear. If it appears, we're already in and skip token login.
  const alreadyIn = await page
    .locator('a[href*="workloads"]')
    .first()
    .waitFor({ state: "visible", timeout: 45_000 })
    .then(() => true)
    .catch(() => false);
  if (alreadyIn) return;

  // K8s Dashboard v2/v3: may show Kubeconfig vs Token radio choice first
  try {
    const tokenRadio = page.getByLabel("Token");
    if (await tokenRadio.isVisible({ timeout: 3_000 })) {
      await tokenRadio.click();
    }
  } catch {
    // No radio button — proceed directly to token input
  }
  // Fill token — try aria-label first, fall back to textarea
  const tokenField = page
    .getByLabel(/enter token/i)
    .or(page.locator("textarea#token, input#token"));
  await tokenField.fill(token);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL(/kubernetes-dashboard/, { timeout: 10_000 });
}
