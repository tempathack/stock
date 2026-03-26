import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: ["**/*.spec.ts"],
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "html",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    viewport: { width: 1280, height: 800 },
    testIdAttribute: "data-testid",
  },
  timeout: 30_000,
  navigationTimeout: 45_000,
  // No webServer block — stack already running via kubectl port-forwards
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
});
