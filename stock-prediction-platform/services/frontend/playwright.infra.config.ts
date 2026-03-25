import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/infra",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "html",
  use: {
    trace: "on-first-retry",
    viewport: { width: 1280, height: 800 },
    // No baseURL — each spec sets its own origin via GRAFANA_URL / PROMETHEUS_URL etc.
  },
  projects: [
    { name: "grafana",       testMatch: "**/grafana.spec.ts" },
    { name: "prometheus",    testMatch: "**/prometheus.spec.ts" },
    { name: "minio",         testMatch: "**/minio.spec.ts" },
    { name: "kubeflow",      testMatch: "**/kubeflow.spec.ts" },
    { name: "k8s-dashboard", testMatch: "**/k8s-dashboard.spec.ts" },
  ],
  // No webServer block — infra services are already running via kubectl port-forward
});
