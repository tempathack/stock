import { test, expect, request } from "@playwright/test";
import { ARGOCD_URL, ARGOCD_PASSWORD } from "./helpers/auth";

// Service availability probe — skip entire file if Argo CD UI unreachable
// Run: kubectl port-forward svc/argocd-server -n argocd 8080:443
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${ARGOCD_URL}/healthz`, { timeout: 5_000 });
    // /healthz returns 200 when healthy; 5xx or ECONNREFUSED means not reachable
    if (res.status() >= 500) {
      test.skip(true, `Argo CD not reachable at ${ARGOCD_URL} — run: kubectl port-forward svc/argocd-server -n argocd 8080:443`);
    }
  } catch {
    test.skip(true, `Argo CD not reachable at ${ARGOCD_URL} — run: kubectl port-forward svc/argocd-server -n argocd 8080:443`);
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service, login state shared between tests
test.describe.configure({ mode: "serial" });

// ── Availability ──────────────────────────────────────────────────────────────
test.describe("Argo CD UI availability", () => {
  test("health endpoint returns non-5xx", async ({ page }) => {
    const res = await page.request.get(`${ARGOCD_URL}/healthz`, { timeout: 5_000 });
    expect(res.status()).toBeLessThan(500);
  });

  test("root URL redirects to login page", async ({ page }) => {
    await page.goto(ARGOCD_URL, { waitUntil: "domcontentloaded" });
    // Argo CD redirects / to /login — wait for login form to appear
    await expect(
      page.getByLabel(/username/i).or(page.locator('input[name="username"]')).first()
    ).toBeVisible({ timeout: 15_000 });
  });
});

// ── Login ─────────────────────────────────────────────────────────────────────
test.describe("Argo CD UI login", () => {
  test("logs in as admin and reaches Applications list", async ({ page }) => {
    test.skip(
      !ARGOCD_PASSWORD,
      "ARGOCD_PASSWORD env var not set — skipping login test. Set via: export ARGOCD_PASSWORD=$(argocd admin initial-password -n argocd | head -1)"
    );

    await page.goto(`${ARGOCD_URL}/login`, { waitUntil: "domcontentloaded" });

    // Fill credentials — Argo CD login form uses Username/Password labels
    const usernameInput = page
      .getByLabel(/username/i)
      .or(page.locator('input[name="username"]'))
      .first();
    const passwordInput = page
      .getByLabel(/password/i)
      .or(page.locator('input[name="password"]'))
      .first();

    await usernameInput.fill("admin");
    await passwordInput.fill(ARGOCD_PASSWORD);

    await page.getByRole("button", { name: /sign in/i }).click();

    // Post-login: Applications list page should show
    await expect(
      page.getByText(/Applications|root-app/i).first()
    ).toBeVisible({ timeout: 20_000 });
  });
});

// ── Application list ───────────────────────────────────────────────────────────
test.describe("Argo CD Applications", () => {
  test("root-app Application is visible in the UI after login", async ({ page }) => {
    test.skip(
      !ARGOCD_PASSWORD,
      "ARGOCD_PASSWORD env var not set — skipping login-dependent test"
    );

    await page.goto(`${ARGOCD_URL}/login`, { waitUntil: "domcontentloaded" });
    const usernameInput = page
      .getByLabel(/username/i)
      .or(page.locator('input[name="username"]'))
      .first();
    const passwordInput = page
      .getByLabel(/password/i)
      .or(page.locator('input[name="password"]'))
      .first();
    await usernameInput.fill("admin");
    await passwordInput.fill(ARGOCD_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();

    // Navigate to Applications if not already there
    await page.goto(`${ARGOCD_URL}/applications`, { waitUntil: "domcontentloaded" });

    await expect(
      page.getByText("root-app").first()
    ).toBeVisible({ timeout: 20_000 });
  });
});
