# Phase 61: Playwright E2E Tests — Full Frontend Feature Coverage - Research

**Researched:** 2026-03-25
**Domain:** Playwright E2E testing, React/Vite frontend, axios/TanStack Query API interception
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-PW-01 | Playwright installed in frontend with playwright.config.ts and shared fixture factories typed against types.ts schemas | Standard install pattern documented; fixture shapes derived directly from types.ts |
| TEST-PW-02 | Navigation + Dashboard page tests: sidebar links, treemap click→select, metric cards, TA panel toggle, close detail | All interactive elements catalogued with exact selector strategy |
| TEST-PW-03 | Forecasts page tests: horizon toggle, filter controls, table rows, search, comparison panel, detail section open/close, export buttons | Component selectors and interaction flows documented |
| TEST-PW-04 | Models page tests (winner card, table click→detail panel, SHAP/beeswarm/fold charts, export) + Drift page tests (ActiveModelCard, RetrainStatusPanel, RollingPerformanceChart, DriftTimeline, FeatureDistributionChart) | Route map, API schemas, and component text patterns fully catalogued |
| TEST-PW-05 | Backtest page tests (ticker select, date inputs, horizon select, Run Backtest → chart + metrics summary, export) + CI npm script wiring | Backtest page structure fully read; npm script patterns documented |
</phase_requirements>

---

## Summary

The frontend is a React 18 + Vite 6 SPA with five pages (Dashboard, Forecasts, Models, Drift, Backtest) wired through TanStack Query v5 hooks and an axios client. All API calls go through a single `apiClient` instance whose `baseURL` is `import.meta.env.VITE_API_URL || "http://localhost:8000"`. Playwright's `page.route()` can intercept these calls at the network level, intercepting URLs like `**/market/overview`, `**/predict/bulk`, etc., meaning tests are completely independent of a live API.

There are **zero existing tests** in the frontend — no jest.config, no vitest.config, no spec files, no test scripts in package.json. The entire test infrastructure must be created from scratch. The Playwright install will add `@playwright/test` as a devDependency and produce a `playwright.config.ts`, an `e2e/` directory alongside `src/`, and new npm scripts (`test:e2e`, `test:e2e:ui`). The app's dev server runs on port 3000 via `vite --port 3000`, which is the `baseURL` for `playwright.config.ts`.

The critical architectural challenge is the app's mock-fallback pattern: every page falls back to generated mock data on API error (`isError ? generateMock...() : []`). Tests that fail to properly intercept routes will receive 404 errors from the dev server, which Playwright counts as network errors that may trigger the `isError` branch, causing mock data to appear in assertions rather than fixture data. The zero-tolerance rule means every test must assert on fixture-specific values (e.g., a specific ticker symbol from the fixture JSON, not any ticker that might appear in mock data).

**Primary recommendation:** Use `page.route('**/path', route => route.fulfill({ json: fixture }))` for every API endpoint a page calls on mount. Register routes before `page.goto()`. Verify fixture values are distinct from mock data defaults (e.g., use ticker "ZZZZ_TEST" or model name "test_ridge_standard" in fixtures).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @playwright/test | 1.58.2 | E2E test runner, browser automation, route interception | Official Playwright test package; includes expect, fixtures, page.route() |
| playwright | 1.58.2 | Browser binaries (Chromium, Firefox, WebKit) | Required alongside @playwright/test |

**Versions verified against npm registry on 2026-03-25.**

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @types/node | already in devDeps (^25.5.0) | Node type definitions | Already present — no new install needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @playwright/test | Cypress | Playwright has native `page.route()` with `route.fulfill()` for JSON interception; Cypress equivalent is more verbose. Playwright fits the Vite/React stack cleanly. |
| @playwright/test | Vitest + @testing-library | Unit/component testing, not E2E browser flows. Wrong tool for multi-page navigation flows. |

**Installation:**
```bash
cd stock-prediction-platform/services/frontend
npm install --save-dev @playwright/test@1.58.2
npx playwright install chromium
```

Chromium-only install is sufficient for CI; Firefox/WebKit are optional.

**Version verification:** `npm view @playwright/test version` returns `1.58.2` (verified 2026-03-25).

---

## Architecture Patterns

### Recommended Project Structure
```
services/frontend/
├── src/                     # existing app source
├── e2e/                     # NEW — Playwright test root
│   ├── fixtures/
│   │   └── api.ts           # typed fixture factories for all API responses
│   ├── dashboard.spec.ts
│   ├── forecasts.spec.ts
│   ├── models.spec.ts
│   ├── drift.spec.ts
│   └── backtest.spec.ts
├── playwright.config.ts     # NEW
└── package.json             # add test:e2e / test:e2e:ui scripts
```

### Pattern 1: Route Interception with page.route()

**What:** Before navigating to a page, register `page.route()` handlers for every URL the page fetches on mount. Use `route.fulfill({ json: fixture })` to return fixture data. The dev server must already be running (`webServer` in playwright.config.ts can start it automatically).

**When to use:** For every test. Never let a test rely on the live API or fall through to mock data.

**Example:**
```typescript
// e2e/fixtures/api.ts
import type { MarketOverviewResponse } from "../src/api/types";

export function marketOverviewFixture(): MarketOverviewResponse {
  return {
    stocks: [
      {
        ticker: "AAPL",
        company_name: "Apple Inc.",
        sector: "Technology",
        market_cap: 2_800_000_000_000,
        last_close: 178.50,
        daily_change_pct: 1.23,
      },
    ],
    count: 1,
  };
}
```

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from "@playwright/test";
import { marketOverviewFixture } from "./fixtures/api";

test("treemap renders fixture tickers", async ({ page }) => {
  await page.route("**/market/overview", (route) =>
    route.fulfill({ json: marketOverviewFixture() })
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { service: "stock-api", version: "1.0.0", status: "healthy" } })
  );
  await page.goto("/dashboard");
  await expect(page.getByText("AAPL")).toBeVisible();
});
```

### Pattern 2: playwright.config.ts with webServer

**What:** Use the `webServer` option to auto-start `vite --port 3000` before running tests. Set `baseURL` to `http://localhost:3000`.

**Example:**
```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run dev",
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
```

### Pattern 3: Intercepting axios via page.route()

**What:** The app uses axios with `baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"`. In dev, `VITE_API_URL` is unset, so axios calls go to `http://localhost:8000`. Playwright's `page.route()` matches by URL glob — use `"**/market/overview"` (double-star glob) which matches regardless of the origin. This works because Playwright intercepts at the browser network layer, catching all outbound requests including cross-origin axios calls.

**Critical detail:** The `**` glob prefix matches the scheme+host portion, so `"**/predict/bulk"` will match `http://localhost:8000/predict/bulk` correctly.

### Pattern 4: Fixture factories typed against types.ts

**What:** Every fixture factory function returns a value typed to the exact TypeScript interface from `src/api/types.ts`. This provides compile-time guarantee that fixture data matches what the app's components expect.

**Example:**
```typescript
import type {
  BulkPredictionResponse,
  ModelComparisonResponse,
  DriftStatusResponse,
  MarketOverviewResponse,
  RollingPerformanceResponse,
  RetrainStatusResponse,
  AvailableHorizonsResponse,
  BacktestResponse,
  TickerIndicatorsResponse,
  HealthResponse,
} from "../src/api/types";
```

All 10 API response types used by queries.ts must have corresponding fixture factories.

### Anti-Patterns to Avoid

- **Unintercepted routes:** Any route not intercepted returns a network error → `isError=true` → mock fallback data appears → test passes on mock values, not fixture values. Register ALL routes a page calls on mount.
- **Fixture values matching mock values:** If your fixture `ticker: "AAPL"` is the same as the mock default `"AAPL"`, an assertion `expect(page.getByText("AAPL")).toBeVisible()` could pass even on mock data. Use unique sentinel values in fixtures (e.g., `model_name: "fixture_ridge_standard"`) for assertions that must confirm real data loaded.
- **Missing WebSocket stub:** Dashboard calls `ws://localhost:8000/ws/prices`. Playwright cannot intercept WebSocket frames with `page.route()`. The WebSocket connection will fail gracefully (the `useWebSocket` hook sets `status: "disconnected"` on error), which is acceptable — do not assert on WebSocket-dependent values.
- **Asserting on Recharts canvas/SVG internals:** Recharts renders to SVG. Do not assert on SVG path `d` attributes or precise pixel positions. Instead assert on surrounding container text or aria labels.
- **Lazy-loaded route delays:** All 5 page components are `React.lazy()`. After `page.goto()`, wait for page-specific content with `await expect(page.getByText("...")).toBeVisible()` rather than using a fixed timeout.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP interception | Custom service worker or proxy server | `page.route()` + `route.fulfill()` | Built into Playwright; zero setup, works per-test |
| Waiting for React renders | `page.waitForTimeout(500)` | `await expect(locator).toBeVisible()` | Auto-retries up to `timeout` ms; no flaky sleeps |
| WebServer lifecycle | Shell scripts to start/stop dev server | `webServer` in playwright.config.ts | Playwright manages it; `reuseExistingServer` for local dev |
| TypeScript compilation | Separate tsc step before tests | Playwright uses `ts-node` / esbuild natively | `@playwright/test` transpiles TypeScript test files automatically |

---

## Complete API Route Map

All routes intercepted must cover what TanStack Query fires on each page's mount:

| Page | Routes fired on mount |
|------|-----------------------|
| All pages | `GET /health` (Sidebar useHealthCheck, 60s refetch) |
| Dashboard | `GET /market/overview`, `GET /market/indicators/:ticker` (after select), `GET /predict/:ticker` (after select) |
| Forecasts | `GET /predict/horizons`, `GET /predict/bulk?horizon=7`, `GET /market/overview`, `GET /market/indicators/:ticker` (after row click) |
| Models | `GET /models/comparison` |
| Drift | `GET /models/drift`, `GET /models/comparison`, `GET /models/drift/rolling-performance?days=30`, `GET /models/retrain-status` |
| Backtest | `GET /market/overview`, `GET /backtest/AAPL` (initial load with activeTicker="AAPL") |

Use `page.route("**/health", ...)` for health. Use glob patterns like `"**/market/indicators/**"` for parameterized routes.

---

## Selector Strategy

**Zero `data-testid` attributes exist in the codebase.** No components have been annotated. All selectors must use stable structural alternatives:

| Target Element | Selector Strategy | Source |
|----------------|-------------------|--------|
| Sidebar nav links | `page.getByRole("link", { name: "Forecasts" })` | NavLink renders as `<a>` |
| Horizon toggle buttons | `page.getByRole("radio", { name: "7D" })` | HorizonToggle uses `role="radio"` |
| Horizon radiogroup | `page.getByRole("radiogroup", { name: "Prediction horizon" })` | HorizonToggle uses `role="radiogroup"` aria-label |
| "Show Technical Indicators" button | `page.getByRole("button", { name: /Show Technical Indicators/i })` | Button text from Dashboard.tsx |
| "Hide Technical Indicators" button | `page.getByRole("button", { name: /Hide Technical Indicators/i })` | Button text from Dashboard.tsx |
| Close detail button | `page.getByRole("button", { name: /✕ Close/i })` | Button text from Dashboard.tsx |
| "Run Backtest" button | `page.getByRole("button", { name: "Run Backtest" })` | Button text from Backtest.tsx |
| Export CSV button | `page.getByRole("button", { name: /CSV/i })` | ExportButtons.tsx button text "📄 CSV" |
| Export PDF button | `page.getByRole("button", { name: /PDF/i })` | ExportButtons.tsx button text "📑 PDF" |
| Search input (Forecasts) | `page.getByPlaceholder("Ticker or company…")` | ForecastFilters.tsx placeholder text |
| Search input (Models) | `page.getByPlaceholder("Filter by model name…")` | ModelComparisonTable.tsx placeholder text |
| Sector select (Forecasts) | `page.getByLabel("Sector")` | `<label>` text in ForecastFilters.tsx |
| Ticker select (Backtest) | `page.getByLabel("Ticker")` | `<label>` text in Backtest.tsx |
| Start date input | `page.getByLabel("Start Date")` | `<label>` text in Backtest.tsx |
| End date input | `page.getByLabel("End Date")` | `<label>` text in Backtest.tsx |
| Horizon select (Backtest) | `page.getByLabel("Horizon (days)")` | `<label>` text in Backtest.tsx |
| Forecast table rows | `page.locator("table tbody tr")` | Standard HTML table structure |
| Model table rows | `page.locator("table tbody tr")` | Standard HTML table structure |
| Winner card | `page.getByText("Winner")` or `page.getByText(/🏆 Winner/)` | WinnerCard.tsx text |
| Active model badge | `page.getByText("Active")` | ActiveModelCard.tsx span text |
| Page headings | `page.getByRole("heading", { name: "..." })` | PageHeader renders `<h1>` |
| API status indicator | `page.getByText(/API Connected/i)` | Sidebar.tsx text |
| Treemap (mobile fallback) | `page.locator('[data-testid="mobile-market-list"]')` | Not present — need to use `page.setViewportSize` to stay desktop |

**Key insight on Treemap:** The Treemap SVG `<g>` elements are rendered by Recharts custom content. Clicking them requires `page.locator("text=AAPL")` within the SVG, or using `page.getByText("AAPL")`. However the treemap uses `isAnimationActive={false}`, so SVG is stable. Use viewport width > 640px to avoid `MobileMarketList` substitution (breakpoint is 640px via `useIsMobile`).

---

## Common Pitfalls

### Pitfall 1: Mock Fallback Masking Failed Interception
**What goes wrong:** Test asserts `expect(page.getByText("AAPL")).toBeVisible()`. Both real fixture data and mock data contain "AAPL". Test passes even when interception failed and mock data loaded.
**Why it happens:** Every page has `isError ? generateMock...() : []` branches. Mock data also contains AAPL, MSFT, etc.
**How to avoid:** Use fixture values not present in mock data for key assertions. E.g., fixture `model_name: "fixture_stacking_ensemble"` — mock data uses names like `"stacking_ensemble_meta_ridge"` from `generateModelDetail()`. Alternatively, assert on the absence of loading/error states AND presence of fixture-specific values.
**Warning signs:** Test passes even when `page.route()` is removed entirely.

### Pitfall 2: axios baseURL Interception
**What goes wrong:** `page.route("**/market/overview", ...)` fails because axios sends to `http://localhost:8000/market/overview` and the glob doesn't match.
**Why it happens:** `**` glob in Playwright matches any scheme+host prefix. This should work. The real failure mode is using a single `*` instead of `**`.
**How to avoid:** Always use `**` double-star prefix: `"**/market/overview"`. Confirm by adding `page.on("request", req => console.log(req.url()))` during debugging to see actual URLs.

### Pitfall 3: Multiple Simultaneous Queries on Drift Page
**What goes wrong:** Drift page fires 4 queries simultaneously: `/models/drift`, `/models/comparison`, `/models/drift/rolling-performance`, `/models/retrain-status`. Missing any one leaves `isLoading` or `isError` states.
**Why it happens:** `isAllLoading` is `driftQuery.isLoading && modelsQuery.isLoading && rollingPerfQuery.isLoading && retrainQuery.isLoading` — all four must not be loading. If one 404s, some state remains inconsistent.
**How to avoid:** Register all 4 routes before `page.goto("/drift")`.

### Pitfall 4: WebSocket Connection Noise
**What goes wrong:** Dashboard test logs WebSocket connection errors to `ws://localhost:8000/ws/prices`, causing spurious test output or unexpected error state.
**Why it happens:** `useWebSocket` connects on mount; the dev server does not serve WebSocket.
**How to avoid:** The `wsStatus` state falls back to `"disconnected"` — the Dashboard still renders. WebSocket status dot will be red, but no test assertions should check ws status color. If output is noisy, suppress with `page.on("websocket", ws => ws.on("socketerror", () => {}))`.

### Pitfall 5: Forecast page shows LoadingSpinner during test
**What goes wrong:** `isLoading = bulkQuery.isLoading || marketQuery.isLoading` — both must resolve before content renders. If either route is missing, the spinner stays.
**Why it happens:** Both `/predict/bulk` and `/market/overview` are required.
**How to avoid:** Always stub both routes for Forecasts page tests.

### Pitfall 6: Backtest page has enabled:false until ticker is truthy
**What goes wrong:** The `useBacktest` hook has `enabled: !!ticker`. With `activeTicker = "AAPL"` as default, the query fires on mount. But if the ticker select is changed to an unstubbed value, a new query fires that is not intercepted.
**How to avoid:** For tests that change the ticker, stub the new ticker's route before triggering the select change.

### Pitfall 7: Models page auto-selects winner on load
**What goes wrong:** `useEffect` in Models.tsx auto-sets `selectedModel` to `data.winner` on first load. This triggers rendering of `ModelDetailPanel`, `ShapBarChart`, etc. Tests that do not expect this may fail waiting for elements.
**Why it happens:** The auto-selection happens after data resolves — it is intentional behavior.
**How to avoid:** Be aware that the detail panel is shown automatically if `winner` is non-null in the fixture. The fixture for `/models/comparison` should include a non-null `winner` to test this path, or set `winner: null` to test the "no winner" path.

---

## Code Examples

### playwright.config.ts
```typescript
// Source: Playwright official docs — https://playwright.dev/docs/test-configuration
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    viewport: { width: 1280, height: 800 },
  },
  webServer: {
    command: "npm run dev",
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
});
```

### Shared fixture factory (e2e/fixtures/api.ts)
```typescript
// Types imported from the app's own types.ts — zero schema drift possible
import type {
  MarketOverviewResponse,
  BulkPredictionResponse,
  ModelComparisonResponse,
  DriftStatusResponse,
  RollingPerformanceResponse,
  RetrainStatusResponse,
  AvailableHorizonsResponse,
  TickerIndicatorsResponse,
  BacktestResponse,
  HealthResponse,
} from "../src/api/types";

export const healthFixture = (): HealthResponse => ({
  service: "stock-api",
  version: "1.0.0",
  status: "healthy",
});

export const marketOverviewFixture = (): MarketOverviewResponse => ({
  stocks: [
    {
      ticker: "AAPL",
      company_name: "Apple Inc.",
      sector: "Technology",
      market_cap: 2_800_000_000_000,
      last_close: 178.50,
      daily_change_pct: 1.23,
    },
    {
      ticker: "MSFT",
      company_name: "Microsoft Corporation",
      sector: "Technology",
      market_cap: 3_100_000_000_000,
      last_close: 415.20,
      daily_change_pct: -0.54,
    },
  ],
  count: 2,
});

export const bulkPredictionsFixture = (horizon = 7): BulkPredictionResponse => ({
  predictions: [
    {
      ticker: "AAPL",
      prediction_date: "2026-03-25",
      predicted_date: "2026-04-01",
      predicted_price: 182.30,
      model_name: "stacking_ensemble_meta_ridge",
      confidence: 0.87,
      horizon_days: horizon,
    },
    {
      ticker: "MSFT",
      prediction_date: "2026-03-25",
      predicted_date: "2026-04-01",
      predicted_price: 420.10,
      model_name: "stacking_ensemble_meta_ridge",
      confidence: 0.91,
      horizon_days: horizon,
    },
  ],
  model_name: "stacking_ensemble_meta_ridge",
  generated_at: "2026-03-25T09:00:00Z",
  count: 2,
  horizon_days: horizon,
});

export const availableHorizonsFixture = (): AvailableHorizonsResponse => ({
  horizons: [1, 7, 30],
  default: 7,
});

export const modelComparisonFixture = (): ModelComparisonResponse => ({
  models: [
    {
      model_name: "stacking_ensemble_meta_ridge",
      scaler_variant: "standard",
      version: 3,
      is_winner: true,
      is_active: true,
      oos_metrics: { rmse: 0.012345, mae: 0.009876, r2: 0.8765, mape: 0.0234, directional_accuracy: 0.72 },
      fold_stability: 0.9123,
      best_params: {},
      saved_at: "2026-03-20T10:00:00Z",
    },
    {
      model_name: "ridge",
      scaler_variant: "quantile",
      version: 2,
      is_winner: false,
      is_active: false,
      oos_metrics: { rmse: 0.019876, mae: 0.015432, r2: 0.7654, mape: 0.0345, directional_accuracy: 0.65 },
      fold_stability: 0.8234,
      best_params: {},
      saved_at: "2026-03-18T08:00:00Z",
    },
  ],
  winner: {
    model_name: "stacking_ensemble_meta_ridge",
    scaler_variant: "standard",
    version: 3,
    is_winner: true,
    is_active: true,
    oos_metrics: { rmse: 0.012345, mae: 0.009876, r2: 0.8765, mape: 0.0234, directional_accuracy: 0.72 },
    fold_stability: 0.9123,
    best_params: {},
    saved_at: "2026-03-20T10:00:00Z",
  },
  count: 2,
});

export const driftStatusFixture = (): DriftStatusResponse => ({
  events: [
    {
      drift_type: "data_drift",
      is_drifted: true,
      severity: "medium",
      details: { ks_stat: 0.12, psi: 0.09 },
      timestamp: "2026-03-24T14:00:00Z",
      features_affected: ["rsi_14", "macd_line"],
    },
  ],
  any_recent_drift: true,
  latest_event: {
    drift_type: "data_drift",
    is_drifted: true,
    severity: "medium",
    details: {},
    timestamp: "2026-03-24T14:00:00Z",
    features_affected: ["rsi_14"],
  },
  count: 1,
});

export const rollingPerformanceFixture = (): RollingPerformanceResponse => ({
  entries: [
    { date: "2026-03-01", rmse: 0.011, mae: 0.009, directional_accuracy: 0.71, n_predictions: 5 },
    { date: "2026-03-15", rmse: 0.013, mae: 0.010, directional_accuracy: 0.69, n_predictions: 5 },
  ],
  model_name: "stacking_ensemble_meta_ridge",
  period_days: 30,
  count: 2,
});

export const retrainStatusFixture = (): RetrainStatusResponse => ({
  model_name: "stacking_ensemble_meta_ridge",
  version: "3",
  trained_at: "2026-03-20T10:00:00Z",
  is_active: true,
  oos_metrics: { oos_rmse: 0.012345, oos_mae: 0.009876 },
  previous_model: "ridge",
  previous_trained_at: "2026-03-18T08:00:00Z",
});

export const backtestFixture = (ticker = "AAPL"): BacktestResponse => ({
  ticker,
  model_name: "stacking_ensemble_meta_ridge",
  horizon: 7,
  start_date: "2025-03-25",
  end_date: "2026-03-25",
  metrics: {
    rmse: 3.45,
    mae: 2.87,
    mape: 1.92,
    directional_accuracy: 68.5,
    r2: 0.82,
    total_points: 252,
  },
  series: [
    { date: "2025-04-01", actual_price: 180.0, predicted_price: 182.3, error: -2.3, error_pct: -1.28 },
    { date: "2025-04-08", actual_price: 183.5, predicted_price: 181.0, error: 2.5, error_pct: 1.36 },
  ],
});

export const tickerIndicatorsFixture = (ticker = "AAPL"): TickerIndicatorsResponse => ({
  ticker,
  latest: {
    date: "2026-03-25",
    close: 178.50,
    rsi_14: 58.3,
    macd_line: 1.23,
    macd_signal: 0.98,
    macd_histogram: 0.25,
    stoch_k: 72.1,
    stoch_d: 68.4,
    sma_20: 176.2,
    sma_50: 171.8,
    sma_200: 165.4,
    ema_12: 177.1,
    ema_26: 174.5,
    adx: 28.7,
    bb_upper: 182.3,
    bb_middle: 176.2,
    bb_lower: 170.1,
    atr: 2.45,
    rolling_volatility_21: 0.018,
    obv: 123456789,
    vwap: 177.8,
    volume_sma_20: 87654321,
    ad_line: 987654,
    return_1d: 0.0123,
    return_5d: 0.0234,
    return_21d: 0.0456,
    log_return: 0.0122,
  },
  series: [],
  count: 0,
});
```

### Routing all calls for a single test
```typescript
// Pattern for tests that need complete isolation
async function stubAllRoutes(page: Page, overrides?: Partial<Record<string, unknown>>) {
  await page.route("**/health", route => route.fulfill({ json: healthFixture() }));
  await page.route("**/market/overview", route => route.fulfill({ json: marketOverviewFixture() }));
  await page.route("**/predict/bulk**", route => route.fulfill({ json: bulkPredictionsFixture() }));
  await page.route("**/predict/horizons", route => route.fulfill({ json: availableHorizonsFixture() }));
  await page.route("**/models/comparison", route => route.fulfill({ json: modelComparisonFixture() }));
  await page.route("**/models/drift/rolling-performance**", route =>
    route.fulfill({ json: rollingPerformanceFixture() })
  );
  await page.route("**/models/drift", route => route.fulfill({ json: driftStatusFixture() }));
  await page.route("**/models/retrain-status", route => route.fulfill({ json: retrainStatusFixture() }));
  await page.route("**/backtest/**", route => route.fulfill({ json: backtestFixture() }));
  await page.route("**/market/indicators/**", route => route.fulfill({ json: tickerIndicatorsFixture() }));
  await page.route("**/predict/**", route => route.fulfill({ json: {
    ticker: "AAPL", prediction_date: "2026-03-25", predicted_date: "2026-04-01",
    predicted_price: 182.30, model_name: "stacking_ensemble_meta_ridge",
    confidence: 0.87, horizon_days: 7,
  }}));
}
```

**Route ordering note:** `/models/drift/rolling-performance` must be registered before `/models/drift` because `page.route()` matches in registration order and the longer path must take precedence. Register specific before general.

### npm scripts to add to package.json
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report"
  }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Cypress for React E2E | Playwright as first-class React/Vite choice | ~2023 | Playwright has native TS support, no iframe restrictions, true multi-tab |
| `page.waitForTimeout()` | `await expect(locator).toBeVisible()` | Playwright v1.x | Eliminates flaky fixed delays |
| Separate `ts-jest` config | Playwright natively runs TypeScript test files | Playwright v1.20+ | No separate tsconfig or transform config needed |
| Manual browser launch | `webServer` in playwright.config.ts | Playwright v1.22+ | Zero-config dev server lifecycle |

**Deprecated/outdated:**
- `page.waitForSelector()`: Replaced by `page.locator().waitFor()` or `expect(locator).toBeVisible()`
- `page.fill()` for inputs: Still valid but `page.getByLabel().fill()` is preferred for better accessibility alignment

---

## Open Questions

1. **Playwright CI environment**
   - What we know: `.planning/config.json` has `nyquist_validation: true` and `commit_docs: true`; no CI YAML file was found in the project
   - What's unclear: Whether a GitHub Actions / CI pipeline file exists where the npm scripts should be wired
   - Recommendation: Plan 61-05 should add the npm scripts to package.json; note in plan that CI integration is pending Phase 62's CI scope

2. **TypeScript path aliases in e2e/ imports**
   - What we know: `vite.config.ts` defines `"@": resolve(__dirname, "./src")`; Playwright uses its own TypeScript handling (not Vite)
   - What's unclear: Whether `@/api/types` imports work inside `e2e/` files without a separate tsconfig
   - Recommendation: Use relative imports (`"../src/api/types"`) in `e2e/fixtures/api.ts` rather than `@` aliases to avoid needing a separate `tsconfig.playwright.json`

3. **Feature distribution chart (Drift page) uses mock data only**
   - What we know: `const featureDistributions = mockData.featureDistributions` — the Drift page always uses mock data for feature distributions (line 77 of Drift.tsx), regardless of API success
   - What's unclear: Whether a future API endpoint will be added for feature distributions
   - Recommendation: The FeatureDistributionChart test must assert on mock data values (not fixture values), since this component ignores API entirely

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | @playwright/test 1.58.2 |
| Config file | `services/frontend/playwright.config.ts` — Wave 0 creates this |
| Quick run command | `cd stock-prediction-platform/services/frontend && npx playwright test --project=chromium e2e/dashboard.spec.ts` |
| Full suite command | `cd stock-prediction-platform/services/frontend && npx playwright test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-PW-01 | Playwright installed, config valid, fixture factories compile | smoke | `npx playwright test --list` | ❌ Wave 0 |
| TEST-PW-02 | Navigation sidebar links work; Dashboard treemap click selects ticker; metric cards appear; TA panel toggles; close button hides detail | e2e | `npx playwright test e2e/dashboard.spec.ts` | ❌ Wave 0 |
| TEST-PW-03 | Forecasts: horizon toggle changes query; filters reduce rows; search filters by ticker; comparison panel; detail section opens/closes; export buttons present | e2e | `npx playwright test e2e/forecasts.spec.ts` | ❌ Wave 0 |
| TEST-PW-04 | Models: winner card renders; table row click shows detail panel + SHAP charts; export buttons. Drift: ActiveModelCard, RetrainStatusPanel, RollingPerformanceChart, DriftTimeline render with fixture data | e2e | `npx playwright test e2e/models.spec.ts e2e/drift.spec.ts` | ❌ Wave 0 |
| TEST-PW-05 | Backtest: ticker select, date inputs, horizon select, Run Backtest button triggers query; chart + metrics summary visible; export buttons enabled | e2e | `npx playwright test e2e/backtest.spec.ts` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `npx playwright test --project=chromium <spec_file> --reporter=line`
- **Per wave merge:** `npx playwright test` (full suite, all 5 spec files)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `services/frontend/playwright.config.ts` — Playwright configuration
- [ ] `services/frontend/e2e/fixtures/api.ts` — typed fixture factories
- [ ] `services/frontend/e2e/dashboard.spec.ts` — covers TEST-PW-02
- [ ] `services/frontend/e2e/forecasts.spec.ts` — covers TEST-PW-03
- [ ] `services/frontend/e2e/models.spec.ts` — covers TEST-PW-04 (Models)
- [ ] `services/frontend/e2e/drift.spec.ts` — covers TEST-PW-04 (Drift)
- [ ] `services/frontend/e2e/backtest.spec.ts` — covers TEST-PW-05
- [ ] Framework install: `npm install --save-dev @playwright/test@1.58.2 && npx playwright install chromium`
- [ ] npm scripts: `test:e2e`, `test:e2e:ui`, `test:e2e:headed`, `test:e2e:report` in package.json

---

## Sources

### Primary (HIGH confidence)
- npm registry `npm view @playwright/test version` — confirmed 1.58.2 on 2026-03-25
- `services/frontend/src/api/types.ts` — exact TypeScript schemas for all API responses
- `services/frontend/src/api/queries.ts` — exact API endpoints and query key patterns
- `services/frontend/src/api/client.ts` — axios baseURL pattern confirming interception target
- `services/frontend/src/pages/Dashboard.tsx` — exact mock fallback pattern and component tree
- `services/frontend/src/pages/Forecasts.tsx` — all interactive elements and query dependencies
- `services/frontend/src/pages/Models.tsx` — auto-select winner useEffect, chart dependencies
- `services/frontend/src/pages/Drift.tsx` — all 4 query dependencies + hardcoded featureDistributions mock
- `services/frontend/src/pages/Backtest.tsx` — activeTicker state, Run Backtest flow
- `services/frontend/src/App.tsx` — routes: /dashboard, /models, /forecasts, /drift, /backtest
- `services/frontend/src/components/forecasts/HorizonToggle.tsx` — confirms `role="radiogroup"` aria-label
- `services/frontend/src/components/layout/Sidebar.tsx` — NavLink renders as `<a>` with exact labels
- `services/frontend/src/components/ui/ExportButtons.tsx` — exact button text for selectors
- `services/frontend/package.json` — no testing tools present; confirmed zero test infrastructure
- `services/frontend/vite.config.ts` — confirmed port 3000, `@` alias points to `src/`
- `stock-prediction-platform/k8s/frontend/service.yaml` — NodePort 30080 (K8s) vs port 3000 (dev)

### Secondary (MEDIUM confidence)
- Playwright docs pattern for `webServer` and `page.route()` — consistent with version 1.58.x API

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — version confirmed from npm registry
- Architecture: HIGH — derived directly from reading all 5 page components and API client
- Pitfalls: HIGH — identified from direct code analysis (mock fallback branches, route ordering, WebSocket, lazy routes)
- Selectors: HIGH — derived from actual component source (aria labels, button text, placeholder text)
- Fixture shapes: HIGH — typed directly against types.ts interfaces

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (Playwright releases frequently but the page.route() API is stable)
