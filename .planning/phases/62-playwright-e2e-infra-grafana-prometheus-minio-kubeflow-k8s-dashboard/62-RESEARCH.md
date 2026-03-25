# Phase 62: Playwright E2E — Infra UI Coverage - Research

**Researched:** 2026-03-25
**Domain:** Playwright E2E testing for third-party infrastructure UIs (Grafana, Prometheus, MinIO, Kubeflow Pipelines, Kubernetes Dashboard)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Service availability policy**
- All 5 services use the same policy: HTTP probe in `beforeAll`, skip entire file if service is unreachable
- Probe timeout: 5 seconds (tolerant of slow port-forwards)
- Skip with a descriptive message: `test.skip(true, 'Grafana not reachable at http://localhost:3000')`
- This applies uniformly to Grafana, Prometheus, MinIO, Kubeflow, and K8s Dashboard — no "required vs optional" distinction
- Fail on test failures, not on connectivity failures

**Credential sourcing**
- Env vars with hardcoded dev defaults — zero config for standard local setup
- All credentials defined in `helpers/auth.ts`, which all spec files import
- Defaults: `GRAFANA_USER ?? 'admin'`, `GRAFANA_PASSWORD ?? 'admin'`, `MINIO_USER ?? 'minioadmin'`, `MINIO_PASSWORD ?? 'minioadmin123'`
- No dotenv/`.env.infra` file — plain env var reads with inline fallbacks

**K8s Dashboard auth**
- Token supplied via `KUBERNETES_DASHBOARD_TOKEN` env var
- If not set: `test.skip(true, 'KUBERNETES_DASHBOARD_TOKEN not set — run: kubectl -n kubernetes-dashboard create token kubernetes-dashboard')` — no Skip button fallback
- Dashboard URL: hardcoded default `http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/` with `K8S_DASHBOARD_URL` env var override
- `loginK8sDashboard(page, token)` helper in `helpers/auth.ts`

### Claude's Discretion
- Exact selector strategy for third-party UIs (role-based, text-based, or CSS selectors)
- Retry/wait logic within tests for slow-rendering panels (Grafana charts especially)
- Exact structure of `playwright.infra.config.ts` multi-project projects array

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-INFRA-01 | Grafana E2E: login + 3 dashboards (API Health, ML Performance, Kafka & Infrastructure) + 2 datasources (Prometheus, Loki) | Grafana deployment confirmed admin/admin creds; dashboard titles extracted from provisioning ConfigMaps; datasource names from grafana-datasource-configmap.yaml |
| TEST-INFRA-02 | Prometheus E2E: query execution + targets page + alerts page | Prometheus at port 9090; alert rules confirmed in prometheus-configmap.yaml; scrape jobs: kubernetes-pods |
| TEST-INFRA-03 | MinIO Console E2E: login + bucket existence (model-artifacts, drift-logs) + object navigation | MinIO at port 9001 with minioadmin/minioadmin123 creds; buckets confirmed in deploy-all.sh minio-init-job |
| TEST-INFRA-04 | Kubeflow Pipelines UI E2E: navigation of pipeline list, experiments, or runs UI | Kubeflow at port 8888 via svc/ml-pipeline-ui; no auth documented in stack; navigation-only tests appropriate |
| TEST-INFRA-05 | Kubernetes Dashboard E2E: token auth + cluster overview | kubectl proxy at port 8001; token via env var; skip if token not set; URL confirmed in deploy-all.sh |
</phase_requirements>

---

## Summary

Phase 62 writes Playwright E2E tests for the five infrastructure UIs exposed by deploy-all.sh port-forwarding. Unlike Phase 61 (React frontend tests with route interception), these tests hit live deployed services with no mocks. Each spec file has a `beforeAll` HTTP probe that skips the entire file if the service is unreachable — this is the central pattern enabling the suite to pass cleanly even when individual services are not running.

The test infrastructure lives entirely within the existing `stock-prediction-platform/services/frontend/` package. A new `playwright.infra.config.ts` is added at the same level as the existing `playwright.config.ts` (which must not be modified). Infra specs go in `tests/e2e/infra/` (a subdirectory under the existing `e2e/` directory — note: CONTEXT.md says `tests/e2e/infra/` but the existing structure uses `e2e/` directly; the planner should use `e2e/infra/` to stay consistent with the existing directory). A shared `helpers/auth.ts` centralizes all credential and login logic for all five services.

The key implementation challenge is selector strategy for third-party UIs that don't use semantic HTML the way React apps do. Grafana 10.4.0, Prometheus, MinIO Console, Kubeflow Pipelines, and the Kubernetes Dashboard each have distinct HTML structures — some use data-testid attributes, many rely on CSS class selectors or visible text. The research below documents confirmed selectors and authentication flows for each service from official sources and current documentation.

**Primary recommendation:** Use `page.getByText()` for navigation items and headings (most stable across third-party UI versions), fall back to `page.locator('a[href*="..."]')` CSS attribute selectors for link navigation, and use `page.waitForSelector()` with `{ state: 'visible' }` for slow-rendering Grafana panels.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @playwright/test | ^1.58.2 (already installed) | Test runner, browser automation | Already in package.json; no new install needed |
| TypeScript | ~5.6.2 (already installed) | Type-safe test authoring | Already configured in the project |

### Supporting
No new dependencies required. All tooling is already present in `stock-prediction-platform/services/frontend/`.

**Installation:** None required — `@playwright/test` is already in devDependencies at `^1.58.2`.

**Version verification:** `npm view @playwright/test version` — current is 1.50.x; project pins `^1.58.2` which is above current stable; the `^` allows any compatible newer version.

---

## Architecture Patterns

### Recommended Project Structure
```
stock-prediction-platform/services/frontend/
├── playwright.config.ts              # Existing — DO NOT MODIFY
├── playwright.infra.config.ts        # NEW — infra-specific config
├── e2e/                              # Existing directory
│   ├── fixtures/api.ts               # Existing — DO NOT MODIFY
│   ├── dashboard.spec.ts             # Existing Phase 61
│   ├── drift.spec.ts                 # Existing Phase 61
│   ├── forecasts.spec.ts             # Existing Phase 61
│   ├── models.spec.ts                # Existing Phase 61
│   ├── backtest.spec.ts              # Existing Phase 61
│   └── infra/                        # NEW directory for Phase 62
│       ├── helpers/
│       │   └── auth.ts               # NEW — shared auth helpers
│       ├── grafana.spec.ts           # NEW
│       ├── prometheus.spec.ts        # NEW
│       ├── minio.spec.ts             # NEW
│       ├── kubeflow.spec.ts          # NEW
│       └── k8s-dashboard.spec.ts    # NEW
```

### Pattern 1: playwright.infra.config.ts Structure
**What:** Standalone Playwright config with one project per service, no webServer block
**When to use:** All infra tests — this config is used exclusively for infra tests via `--config playwright.infra.config.ts`

```typescript
// playwright.infra.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/infra",
  fullyParallel: false,      // live services, shared state
  retries: 0,
  workers: 1,
  reporter: "html",
  use: {
    trace: "on-first-retry",
    viewport: { width: 1280, height: 800 },
    // No baseURL — each spec sets its own origin
  },
  projects: [
    { name: "grafana",        testMatch: "**/grafana.spec.ts" },
    { name: "prometheus",     testMatch: "**/prometheus.spec.ts" },
    { name: "minio",          testMatch: "**/minio.spec.ts" },
    { name: "kubeflow",       testMatch: "**/kubeflow.spec.ts" },
    { name: "k8s-dashboard",  testMatch: "**/k8s-dashboard.spec.ts" },
  ],
  // No webServer block — infra services are already running
});
```

### Pattern 2: Service Probe in beforeAll (Canonical Pattern)
**What:** HTTP probe using Playwright `request` fixture to skip the entire file if service is unreachable
**When to use:** Every spec file, once per describe block at the outer level

```typescript
// Source: CONTEXT.md decision + Playwright docs on test.skip
import { test, expect, request } from "@playwright/test";

const GRAFANA_URL = process.env.GRAFANA_URL ?? "http://localhost:3000";

test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${GRAFANA_URL}/api/health`, { timeout: 5000 });
    if (!res.ok()) {
      test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
    }
  } catch {
    test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
  } finally {
    await ctx.dispose();
  }
});
```

**Key detail:** `request` is imported directly from `@playwright/test` for use outside of test body. The `request.newContext()` call creates a standalone API context. The `finally` block disposes of it to avoid resource leaks.

### Pattern 3: helpers/auth.ts — Centralized Credential and Login Helpers
**What:** Single module exporting credentials and login functions for all 5 services
**When to use:** Imported by every infra spec file

```typescript
// e2e/infra/helpers/auth.ts
import type { Page } from "@playwright/test";

// ── Credentials (env-var overrides with dev defaults) ──
export const GRAFANA_URL      = process.env.GRAFANA_URL      ?? "http://localhost:3000";
export const GRAFANA_USER     = process.env.GRAFANA_USER     ?? "admin";
export const GRAFANA_PASSWORD = process.env.GRAFANA_PASSWORD ?? "admin";

export const PROMETHEUS_URL   = process.env.PROMETHEUS_URL   ?? "http://localhost:9090";

export const MINIO_URL        = process.env.MINIO_URL        ?? "http://localhost:9001";
export const MINIO_USER       = process.env.MINIO_USER       ?? "minioadmin";
export const MINIO_PASSWORD   = process.env.MINIO_PASSWORD   ?? "minioadmin123";

export const KUBEFLOW_URL     = process.env.KUBEFLOW_URL     ?? "http://localhost:8888";

export const K8S_DASHBOARD_URL = process.env.K8S_DASHBOARD_URL
  ?? "http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/";
export const K8S_DASHBOARD_TOKEN = process.env.KUBERNETES_DASHBOARD_TOKEN;

// ── Login helpers ──
export async function loginGrafana(page: Page): Promise<void> {
  await page.goto(`${GRAFANA_URL}/login`);
  await page.getByLabel("Email or username").fill(GRAFANA_USER);
  await page.getByLabel("Password").fill(GRAFANA_PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  // Wait for post-login redirect to home
  await page.waitForURL(`${GRAFANA_URL}/**`, { timeout: 10_000 });
}

export async function loginMinIO(page: Page): Promise<void> {
  await page.goto(`${MINIO_URL}/login`);
  await page.getByLabel("Username").fill(MINIO_USER);
  await page.getByLabel("Password").fill(MINIO_PASSWORD);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL(`${MINIO_URL}/**`, { timeout: 10_000 });
}

export async function loginK8sDashboard(page: Page, token: string): Promise<void> {
  await page.goto(K8S_DASHBOARD_URL);
  // Select "Token" radio if presented with auth method choice
  const tokenRadio = page.getByLabel("Token");
  if (await tokenRadio.isVisible({ timeout: 3000 })) {
    await tokenRadio.click();
  }
  await page.getByLabel("Enter token").fill(token);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL(/kubernetes-dashboard/, { timeout: 10_000 });
}
```

### Pattern 4: Grafana-Specific Wait Strategy for Panels
**What:** Grafana chart panels load asynchronously after page navigation — need explicit waits
**When to use:** After navigating to any Grafana dashboard page

```typescript
// Wait for panel container to be visible, then wait for spinner to clear
await page.waitForSelector('[data-testid="data-testid Panel header"]', { state: 'visible', timeout: 15_000 });
// Or use panel title text:
await expect(page.getByText("Request Rate")).toBeVisible({ timeout: 15_000 });
```

**Grafana 10.x data-testid attributes (HIGH confidence — verified against Grafana source):**
- Panel header container: `[data-testid="data-testid Panel header {title}"]`
- Dashboard search: `[data-testid="data-testid Search section"]`
- Nav sidebar: `[data-testid="data-testid navigation mega-menu"]`
- Datasource list item: visible text matches datasource name

### Anti-Patterns to Avoid
- **Navigating to Grafana dashboard by UID without knowing it:** Dashboard UIDs are generated at import time. Use the dashboard list (`/dashboards`) and click by title text instead.
- **Expecting Kubeflow to require login:** In this dev stack, Kubeflow Pipelines is deployed without Dex/OIDC auth — the UI is unauthenticated. Do not add auth logic for Kubeflow.
- **Using `page.click()` on Prometheus query input:** The Prometheus expression input uses CodeMirror — use `page.locator('.cm-editor').click()` then `page.keyboard.type()` for reliable input.
- **Hardcoding MinIO console paths:** MinIO console URL paths changed between versions. Use UI navigation (click Buckets in sidebar) rather than direct URL navigation to bucket pages.
- **Expecting K8s Dashboard token input to always be visible:** The skip-button / token flow UI differs by k8s-dashboard version. The `loginK8sDashboard` helper should handle both flows with `isVisible()` guards.

---

## Service-by-Service Reference Data

### Grafana (port 3000)
- **Image:** `grafana/grafana:10.4.0` (pinned in grafana-deployment.yaml)
- **Auth:** `GF_SECURITY_ADMIN_PASSWORD=admin`, `GF_AUTH_ANONYMOUS_ENABLED=true`
- **Credentials:** admin / admin (hardcoded in deployment, matches CONTEXT.md decision)
- **Login probe endpoint:** `GET /api/health` — returns `{"database":"ok","version":"10.4.0",...}`
- **Dashboards (3):**
  | Title | Source File | Key Panels |
  |-------|-------------|-----------|
  | API Health | grafana-dashboard-api-health.yaml → api-health.json | "Request Rate", "Error Rate %", "Latency", "Predictions" |
  | ML Performance | grafana-dashboard-ml-perf.yaml → ml-performance.json | "Predictions by Model", "Inference Errors Over Time" |
  | Kafka & Infrastructure | grafana-dashboard-kafka.yaml → kafka-infra.json | "Messages Consumed Rate", "Consumer Lag" |
- **Datasources (2):**
  | Name | Type | UID |
  |------|------|-----|
  | Prometheus | prometheus | prometheus |
  | Loki | loki | loki |
- **Dashboard list page:** `GET /dashboards` — shows all provisioned dashboards as cards
- **Datasource list page:** `GET /connections/datasources` — lists configured datasources
- **Anonymous access enabled** — tests can skip login entirely for read-only views; but login is required by TEST-INFRA-01 spec

### Prometheus (port 9090)
- **Probe endpoint:** `GET /-/healthy` — returns 200 with body "Prometheus Server is Healthy."
- **Query UI:** `GET /graph` — contains PromQL expression input
- **Targets page:** `GET /targets` — lists all scrape jobs; this stack has job: `kubernetes-pods`
- **Alerts page:** `GET /alerts` — lists rules from alert_rules.yml; defined alerts: `HighDriftSeverity`, `HighAPIErrorRate`, `HighConsumerLag`
- **Expression input selector:** CodeMirror editor inside `.expression-input` or `[aria-label="Metrics Explorer"]`
- **No authentication** — Prometheus is open in this deployment

### MinIO Console (port 9001)
- **Image:** `minio/minio:RELEASE.2024-06-13T22-53-53Z`
- **Credentials:** `MINIO_ROOT_USER=minioadmin`, `MINIO_ROOT_PASSWORD=minioadmin123`
  - **IMPORTANT:** CONTEXT.md says defaults `CHANGEME/CHANGEME` but minio-secrets.yaml decodes to `minioadmin`/`minioadmin123`. Use `minioadmin`/`minioadmin123` as the actual dev defaults in `helpers/auth.ts`.
- **Probe endpoint:** `GET /minio/health/live` (port 9000, not 9001) — but for console probe, use `GET http://localhost:9001/` (200 redirect to login)
- **Buckets confirmed in stack:** `model-artifacts`, `drift-logs` (created by minio-init-job.yaml in deploy-all.sh)
- **Console login URL:** `http://localhost:9001/login`
- **Post-login redirect:** to `http://localhost:9001/browser` (bucket browser)

### Kubeflow Pipelines UI (port 8888)
- **Port-forward:** `kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow`
- **No authentication** in this dev stack (Dex/OIDC not configured — standard for minikube dev deployments)
- **Probe endpoint:** `GET http://localhost:8888/` — returns 200 if pipeline UI is running
- **Key pages:**
  - Pipeline list: `/#/pipelines` — shows uploaded pipelines
  - Runs: `/#/runs` — shows pipeline run history
  - Experiments: `/#/experiments` — shows experiment groups
- **Note:** Kubeflow KFP may not have any pipelines or runs if training hasn't been executed — navigate to the list pages and assert the list container renders, not that specific pipelines exist

### Kubernetes Dashboard (port 8001)
- **Access via:** `kubectl proxy --port=8001` (already in deploy-all.sh)
- **Full URL:** `http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/`
- **Auth:** Bearer token only — token env var `KUBERNETES_DASHBOARD_TOKEN`
- **Token generation command:** `kubectl -n kubernetes-dashboard create token kubernetes-dashboard`
- **Skip condition:** If `KUBERNETES_DASHBOARD_TOKEN` is not set in env, skip with message including the kubectl command
- **Post-login path:** Cluster overview or namespace list
- **Note:** K8s Dashboard version deployed may affect the login page HTML — use text-based selectors ("Token", "Sign In") rather than CSS class selectors

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP service probe | Custom Node.js `http.get()` | `request.newContext()` from `@playwright/test` | Stays in Playwright's request context, handles TLS, cookies, timeouts |
| Parallel test isolation | Manual mutex/lock | `fullyParallel: false` + `workers: 1` | Live services have shared state; serialization prevents race conditions |
| Grafana login state | Storing localStorage manually | Re-login in each test or use `storageState` | Grafana sessions expire; simpler to login per-describe than cache |
| PromQL execution | HTTP API calls to `/api/v1/query` | Navigate `/graph`, enter expression in UI, click Execute | Tests the actual UI, not just the API |

**Key insight:** Infra UI testing is fundamentally different from React unit/component testing. The UIs are black boxes with no controlled fixtures — tests must navigate real UI flows, assert visible elements, and tolerate rendering delays. Playwright's `waitForSelector` and role-based locators are the right tools.

---

## Common Pitfalls

### Pitfall 1: Grafana Anonymous Access Bypasses Login Flow
**What goes wrong:** `GF_AUTH_ANONYMOUS_ENABLED=true` means Grafana serves pages without requiring login. If a test navigates directly to `/` it gets a logged-in-looking UI. But if the test then navigates to `/login`, it redirects back to home. The login test must use `GF_AUTH_ANONYMOUS_ENABLED=false` OR use the `/login` page directly with credentials. In this stack, anonymous is enabled.
**Why it happens:** The deployment YAML sets `GF_AUTH_ANONYMOUS_ENABLED=true` unconditionally.
**How to avoid:** Navigate directly to `/login`, fill credentials, click Log in. The server will create an authenticated session even though anonymous access is also available. Verify the session by asserting the username appears in the top bar after login.
**Warning signs:** Test navigates to `/` and sees content without filling credentials — anonymous access is working.

### Pitfall 2: MinIO Console Login Field Labels
**What goes wrong:** MinIO Console's login form field labels changed across versions. `getByLabel("Username")` may not find the input if the label text differs.
**Why it happens:** MinIO Console front-end is rebuilt with each release.
**How to avoid:** Use `page.locator('input[id="accessKey"]')` or `page.locator('input[placeholder*="username" i]')` as fallback selectors. The input IDs `accessKey` and `secretKey` are stable in MinIO Console.
**Warning signs:** `getByLabel` times out on the login page.

### Pitfall 3: Kubeflow UI Uses Hash Routing — waitForURL Doesn't Match
**What goes wrong:** Kubeflow Pipelines UI uses hash-based routing (`/#/pipelines`). `page.waitForURL('/pipelines')` will never match because the actual URL remains `http://localhost:8888/` — only the hash changes.
**Why it happens:** KFP UI is a React SPA with hash router.
**How to avoid:** After clicking a nav item, wait for a DOM element that appears on the target page to become visible rather than waiting for the URL. Example: after clicking "Pipelines", wait for `page.getByText('No pipelines found').isVisible()` or for a `h2` heading.
**Warning signs:** `waitForURL` times out even though the correct page is rendered.

### Pitfall 4: K8s Dashboard Token Input Hidden Until Method Selected
**What goes wrong:** Newer versions of kubernetes-dashboard present a "Kubeconfig" vs "Token" radio choice before showing the token textarea. The token input is hidden until the user selects "Token".
**Why it happens:** Dashboard v2.x/v3.x login flow UI design.
**How to avoid:** The `loginK8sDashboard` helper must check for the radio button with `isVisible()` and click it before attempting to fill the token. Always wrap in a try/catch with fallback directly filling the token input.
**Warning signs:** `fill()` fails on the token input because it's hidden or not yet rendered.

### Pitfall 5: Grafana Dashboard Navigation by UID
**What goes wrong:** Grafana assigns UIDs to provisioned dashboards at startup. The UIDs in the JSON files may be null or auto-generated, making direct URL navigation (`/d/{uid}/...`) fragile.
**Why it happens:** Dashboard UIDs are null in the provisioned JSON (`"id": null`), so Grafana generates them.
**How to avoid:** Navigate to `/dashboards`, search or click the dashboard by its title text. Assert dashboard title visible after navigation.
**Warning signs:** Direct URL `/d/...` returns 404 or redirects to search.

### Pitfall 6: Prometheus CodeMirror Input Requires Special Handling
**What goes wrong:** Standard `page.fill()` does not work reliably on CodeMirror-based inputs because they intercept keyboard events.
**Why it happens:** Prometheus 2.x uses CodeMirror 6 for the expression input.
**How to avoid:** Use `page.locator('[aria-label="Metrics Explorer"]').click()` then `page.keyboard.type('up')` or use `page.evaluate()` to set the CodeMirror content programmatically. Alternatively, use `page.locator('.cm-content').fill()` which works in some versions.
**Warning signs:** `.fill()` succeeds but nothing appears in the expression box, or the expression is not sent when pressing Execute.

---

## Code Examples

Verified patterns from project inspection and official Playwright docs:

### Service Probe Pattern (Grafana)
```typescript
// Source: CONTEXT.md + Playwright request API
import { test, request } from "@playwright/test";
import { GRAFANA_URL } from "./helpers/auth";

test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${GRAFANA_URL}/api/health`, { timeout: 5000 });
    if (!res.ok()) test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
  } catch {
    test.skip(true, `Grafana not reachable at ${GRAFANA_URL}`);
  } finally {
    await ctx.dispose();
  }
});
```

### Grafana Login Test
```typescript
// Source: Project grafana-deployment.yaml (admin/admin confirmed)
test("logs in to Grafana with admin credentials", async ({ page }) => {
  await page.goto(`${GRAFANA_URL}/login`);
  await page.getByLabel("Email or username").fill(GRAFANA_USER);
  await page.getByLabel("Password").fill(GRAFANA_PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  // After login, Grafana redirects to home — assert Welcome heading or user avatar
  await expect(page.getByText(/Welcome to Grafana|Home/)).toBeVisible({ timeout: 10_000 });
});
```

### Grafana Dashboard Navigation by Title
```typescript
// Navigate to dashboards list and click by title — avoids UID fragility
test("API Health dashboard renders panels", async ({ page }) => {
  await loginGrafana(page);
  await page.goto(`${GRAFANA_URL}/dashboards`);
  await page.getByText("API Health").click();
  // Wait for panel to render — Grafana panels load asynchronously
  await expect(page.getByText("Request Rate")).toBeVisible({ timeout: 15_000 });
});
```

### Prometheus Query Execution
```typescript
// Source: Prometheus UI pattern for expression input
test("executes a PromQL query and sees results", async ({ page }) => {
  await page.goto(`${PROMETHEUS_URL}/graph`);
  // Click the expression input (CodeMirror)
  await page.locator(".cm-content").click();
  await page.keyboard.type("up");
  await page.getByRole("button", { name: "Execute" }).click();
  // Results table or graph appears
  await expect(page.locator(".graph-root, table.table")).toBeVisible({ timeout: 10_000 });
});
```

### MinIO Bucket Existence Check
```typescript
// Source: MinIO Console known navigation pattern
test("model-artifacts bucket exists", async ({ page }) => {
  await loginMinIO(page);
  // MinIO Console shows bucket list at /browser
  await page.goto(`${MINIO_URL}/browser`);
  await expect(page.getByText("model-artifacts")).toBeVisible({ timeout: 10_000 });
});
```

### Kubeflow Navigation (Hash Router)
```typescript
// Source: KFP UI is hash-router SPA — wait for DOM element, not URL
test("pipeline list page renders", async ({ page }) => {
  await page.goto(`${KUBEFLOW_URL}/#/pipelines`);
  // Wait for some element that indicates page loaded — even empty state is valid
  await expect(
    page.locator("h2, [data-testid='pipeline-list'], .page-content")
  ).toBeVisible({ timeout: 15_000 });
});
```

### K8s Dashboard Token Auth + Skip
```typescript
// Source: CONTEXT.md K8s Dashboard auth decision
import { K8S_DASHBOARD_TOKEN, K8S_DASHBOARD_URL } from "./helpers/auth";

test.beforeAll(async () => {
  if (!K8S_DASHBOARD_TOKEN) {
    test.skip(
      true,
      "KUBERNETES_DASHBOARD_TOKEN not set — run: kubectl -n kubernetes-dashboard create token kubernetes-dashboard"
    );
  }
});

test("cluster overview loads after token login", async ({ page }) => {
  await loginK8sDashboard(page, K8S_DASHBOARD_TOKEN!);
  await expect(page.getByText(/Cluster|Namespace|Workloads/i)).toBeVisible({ timeout: 15_000 });
});
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Grafana provisioning via JSON files in pod | ConfigMap-mounted JSON provisioning | Grafana 5.x+ | Dashboards auto-load from K8s ConfigMaps at pod startup |
| MinIO standalone console at :9001 | MinIO built-in console on `--console-address :9001` | MinIO RELEASE.2021-xx | Port 9001 is the official console port; 9000 is the S3 API |
| Prometheus `console_libraries` UI | Prometheus built-in graph UI at `/graph` | Prometheus 2.x | Clean expression browser with direct URL |
| KFP Argo-based UI | KFP v2.x UI | KFP 2.0 | New React-based UI with hash routing |

**Deprecated/outdated:**
- Grafana `data-testid` attributes changed between versions — Grafana 10.x uses `data-testid="data-testid {thing}"` (note the redundant prefix), which is different from Grafana 9.x

---

## Credential Discrepancy Note

CONTEXT.md states MinIO defaults as `MINIO_USER ?? 'CHANGEME'`, `MINIO_PASSWORD ?? 'CHANGEME'`. However, the actual `minio-secrets.yaml` file contains base64-encoded values that decode to `minioadmin` / `minioadmin123`. The `helpers/auth.ts` implementation **must use** `minioadmin` / `minioadmin123` as the actual defaults (not CHANGEME) to connect to the deployed stack. The planner should note this discrepancy and use the correct credentials from the secrets file.

---

## Open Questions

1. **Kubeflow Pipelines — is it deployed?**
   - What we know: deploy-all.sh port-forwards `svc/ml-pipeline-ui` on port 8888 in the `kubeflow` namespace
   - What's unclear: KFP installation is in REQUIREMENTS.md as KF-01 (unchecked — not yet complete). KFP may not be installed on the live cluster.
   - Recommendation: The service probe pattern handles this correctly — the test skips if KFP is not reachable. The planner should document this dependency explicitly in the test file's skip message.

2. **K8s Dashboard — is it deployed in the cluster?**
   - What we know: deploy-all.sh runs `kubectl proxy --port=8001` but does not apply any kubernetes-dashboard manifests
   - What's unclear: The kubernetes-dashboard itself may not be installed. `kubectl proxy` succeeds regardless of whether the dashboard is deployed.
   - Recommendation: The HTTP probe for k8s-dashboard should hit the full proxy URL and check for a 200/301/302. A 503 from kubectl proxy means the dashboard service isn't deployed. The skip message should note that kubernetes-dashboard needs to be installed separately.

3. **Grafana Anonymous Access vs. Authenticated Session**
   - What we know: `GF_AUTH_ANONYMOUS_ENABLED=true` in the deployment YAML
   - What's unclear: Whether TEST-INFRA-01 "login" means an explicit form login or just arriving at Grafana content
   - Recommendation: Implement the login form test as a genuine form submission — navigate to `/login`, fill credentials, submit. This validates that the auth system works even though anonymous access would also allow reading dashboards.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright 1.58.2 (already installed) |
| Config file | `stock-prediction-platform/services/frontend/playwright.infra.config.ts` (Wave 0 creation) |
| Quick run command | `npm run test:infra -- --project=grafana` (single service) |
| Full suite command | `npm run test:infra` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-INFRA-01 | Grafana: login + 3 dashboards + 2 datasources | E2E live | `npm run test:infra -- --project=grafana` | Wave 0 |
| TEST-INFRA-02 | Prometheus: query + targets + alerts | E2E live | `npm run test:infra -- --project=prometheus` | Wave 0 |
| TEST-INFRA-03 | MinIO: login + 2 buckets + navigation | E2E live | `npm run test:infra -- --project=minio` | Wave 0 |
| TEST-INFRA-04 | Kubeflow: UI navigation | E2E live | `npm run test:infra -- --project=kubeflow` | Wave 0 |
| TEST-INFRA-05 | K8s Dashboard: token auth + cluster overview | E2E live | `npm run test:infra -- --project=k8s-dashboard` | Wave 0 |

### Sampling Rate
- **Per task commit:** `npm run test:infra -- --project={service}` (single service being worked on)
- **Per wave merge:** `npm run test:infra` (all 5 services)
- **Phase gate:** Full suite passes (with allowed skips for unreachable services) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `stock-prediction-platform/services/frontend/playwright.infra.config.ts` — new config file
- [ ] `stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts` — shared auth/credential helpers
- [ ] `package.json` — add `"test:infra": "playwright test --config playwright.infra.config.ts"` script
- [ ] `e2e/infra/` directory — does not exist yet

---

## Sources

### Primary (HIGH confidence)
- Project file: `stock-prediction-platform/k8s/monitoring/grafana-deployment.yaml` — Grafana version 10.4.0, admin password, anonymous access
- Project file: `stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml` — datasource names (Prometheus, Loki) and UIDs
- Project file: `stock-prediction-platform/k8s/monitoring/grafana-dashboard-api-health.yaml` — dashboard title "API Health", panel titles
- Project file: `stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml` — dashboard title "ML Performance"
- Project file: `stock-prediction-platform/k8s/monitoring/grafana-dashboard-kafka.yaml` — dashboard title "Kafka & Infrastructure"
- Project file: `stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml` — scrape jobs, alert rule names
- Project file: `stock-prediction-platform/k8s/storage/minio-deployment.yaml` — MinIO image version, port assignments, secret reference
- Project file: `stock-prediction-platform/k8s/storage/minio-secrets.yaml` — actual credentials (minioadmin/minioadmin123)
- Project file: `stock-prediction-platform/scripts/deploy-all.sh` — port assignments, kubectl proxy setup, Kubeflow port-forward
- Project file: `stock-prediction-platform/services/frontend/playwright.config.ts` — existing config structure to replicate
- Project file: `stock-prediction-platform/services/frontend/package.json` — existing scripts pattern, @playwright/test version
- Project context: Phase 61 spec files — established test patterns (serial mode, beforeAll probe pattern, describe structure)

### Secondary (MEDIUM confidence)
- Playwright official docs: `request.newContext()` API for standalone HTTP requests outside test body
- Grafana 10.x: `data-testid` attribute conventions, `/api/health` probe endpoint, `/dashboards` list page URL
- MinIO Console: login form field IDs (`accessKey`, `secretKey`), bucket browser at `/browser`
- Prometheus: `/-/healthy` endpoint, CodeMirror-based expression input behavior
- Kubeflow Pipelines: hash-router SPA pattern, unauthenticated dev deployment pattern

### Tertiary (LOW confidence — needs runtime validation)
- K8s Dashboard: exact token input selector (`[aria-label="Enter token"]`) — varies by dashboard version installed
- Grafana: exact heading text after login ("Welcome to Grafana" vs "Home") — may vary by version

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; existing Playwright setup confirmed
- Architecture: HIGH — file structure and config pattern derived directly from existing project files
- Service details: HIGH — credentials, ports, dashboard titles all extracted from deployed K8s manifests
- Pitfalls: MEDIUM — CodeMirror input and K8s Dashboard selector details are based on known third-party UI behavior patterns
- Kubeflow/K8s Dashboard deployment status: LOW — these services may not actually be deployed on the target cluster (service probe handles this gracefully)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable stack; Grafana/MinIO/Prometheus versions pinned in manifests)
