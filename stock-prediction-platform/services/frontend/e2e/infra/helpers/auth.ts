import type { Page } from "@playwright/test";

// ── URLs (env-var overrides with dev defaults) ──────────────────────────────
export const GRAFANA_URL =
  process.env.GRAFANA_URL ?? "http://localhost:3000";
export const PROMETHEUS_URL =
  process.env.PROMETHEUS_URL ?? "http://localhost:9090";
export const MINIO_URL =
  process.env.MINIO_URL ?? "http://localhost:9001";
export const KUBEFLOW_URL =
  process.env.KUBEFLOW_URL ?? "http://localhost:8888";
export const K8S_DASHBOARD_URL =
  process.env.K8S_DASHBOARD_URL ??
  "http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/";

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

// ── Login helpers ────────────────────────────────────────────────────────────

export async function loginGrafana(page: Page): Promise<void> {
  await page.goto(`${GRAFANA_URL}/login`);
  await page.getByLabel("Email or username").fill(GRAFANA_USER);
  await page.getByLabel("Password").fill(GRAFANA_PASSWORD);
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
  const tokenInput = page
    .getByLabel(/enter token/i)
    .or(page.locator("textarea#token, input#token"));
  await tokenInput.fill(token);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL(/kubernetes-dashboard/, { timeout: 10_000 });
}
