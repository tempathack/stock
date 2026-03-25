import { test, expect, request } from "@playwright/test";
import {
  MINIO_URL,
  MINIO_USER,
  MINIO_PASSWORD,
  loginMinIO,
} from "./helpers/auth";

// Service availability probe — skip entire file if MinIO Console unreachable
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    // Probe the console port (9001) — redirect to /login is fine (not ok() but reachable)
    const res = await ctx.get(MINIO_URL, { timeout: 5_000 });
    // 200 or 3xx from the root URL means the console is up; 5xx means broken
    if (res.status() >= 500) {
      test.skip(true, `MinIO Console not reachable at ${MINIO_URL}`);
    }
  } catch {
    test.skip(true, `MinIO Console not reachable at ${MINIO_URL}`);
  } finally {
    await ctx.dispose();
  }
});

// Serial mode — live service, login state shared between tests
test.describe.configure({ mode: "serial" });

// ── Login ────────────────────────────────────────────────────────────────────
test.describe("MinIO Console login", () => {
  test("logs in with minioadmin credentials and reaches bucket browser", async ({ page }) => {
    // Use stable input IDs (accessKey/secretKey) as primary selectors per RESEARCH.md Pitfall 2
    await page.goto(`${MINIO_URL}/login`);
    await page.locator('input[id="accessKey"]').fill(MINIO_USER);
    await page.locator('input[id="secretKey"]').fill(MINIO_PASSWORD);
    await page.getByRole("button", { name: /login/i }).click();
    // Post-login redirect to /browser
    await page.waitForURL(`${MINIO_URL}/**`, { timeout: 10_000 });
    // Assert we reached the bucket browser — look for "Buckets" heading or browser content
    await expect(
      page.getByText(/Buckets|Browse/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ── Bucket existence ──────────────────────────────────────────────────────────
test.describe("MinIO bucket existence", () => {
  test("model-artifacts bucket exists", async ({ page }) => {
    await loginMinIO(page);
    await page.goto(`${MINIO_URL}/browser`);
    await expect(page.getByText("model-artifacts")).toBeVisible({ timeout: 20_000 });
  });

  test("drift-logs bucket exists", async ({ page }) => {
    await loginMinIO(page);
    await page.goto(`${MINIO_URL}/browser`);
    await expect(page.getByText("drift-logs")).toBeVisible({ timeout: 20_000 });
  });
});

// ── Bucket navigation ─────────────────────────────────────────────────────────
test.describe("MinIO bucket navigation", () => {
  test("clicking model-artifacts bucket opens the object browser", async ({ page }) => {
    await loginMinIO(page);
    await page.goto(`${MINIO_URL}/browser`);
    // Wait for bucket list to render before clicking
    const bucketLink = page.getByText("model-artifacts");
    await expect(bucketLink).toBeVisible({ timeout: 20_000 });
    await bucketLink.click();
    // Object browser renders — even if empty, the container/header should appear
    await expect(
      page.getByText(/Objects|No Objects|Upload/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });
});
