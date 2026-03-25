# Phase 63 Research: Fix E2E Test Assertions — Require Real API Data, Not Mock/Empty Fallbacks

**Researched:** 2026-03-25
**Phase:** 63

---

## Problem Statement

The Playwright E2E tests in `stock-prediction-platform/services/frontend/e2e/` currently pass even when the backend returns no real data. This is because:

1. The frontend pages use `generateMock*` functions as fallbacks when API calls fail or return empty
2. The E2E tests use `page.route()` fixture interceptors — but the test assertions are on data that also appears in mock fallbacks
3. Tests assert on `"AAPL"/"MSFT"` tickers which appear in both fixture data AND mock fallback data
4. `models.spec.ts` asserts `rows=2` and `"Winner"` text which come from mock data if the API returns nothing
5. No `beforeAll` API health check guards the suite from running against an unhealthy backend

---

## Current E2E Test File Analysis

### Files affected:
- `e2e/dashboard.spec.ts` — stubs `**/health` + `**/market/overview` via fixtures
- `e2e/forecasts.spec.ts` — stubs health, horizons, bulk, market/overview, indicators
- `e2e/models.spec.ts` — stubs health + models/comparison via fixtures
- `e2e/drift.spec.ts` — stubs health, drift, comparison, rolling-performance, retrain-status
- `e2e/fixtures/api.ts` — fixture factories (all export functions returning typed data)

### Root causes:

**dashboard.spec.ts (lines 99-101):**
```typescript
await expect(page.getByText("AAPL")).toBeVisible();
await expect(page.getByText("MSFT")).toBeVisible();
```
These tickers appear in `generateMockMarketOverview()` (Dashboard.tsx line 40) AND in `marketOverviewFixture()`. So tests pass whether the stub fires or the mock fallback runs.

**models.spec.ts (lines 43-44):**
```typescript
const rows = page.locator("table tbody tr");
await expect(rows).toHaveCount(2);
```
Count=2 comes from `modelComparisonFixture()` with 2 models — but if backend returns empty, `Models.tsx` shows "No models trained yet" state (lines 31-46), NOT mock data. So this test would actually fail on empty DB for the right reason — BUT the test also passes on mock data because the stub always fires during the test.

**Key insight:** The real problem is not that tests pass on empty backend — it's that the tests have NO mechanism to verify the stub actually fired vs the mock fallback ran. If `page.route()` never intercepts (e.g., due to URL mismatch), the mock fallback kicks in and tests still pass.

**drift.spec.ts (lines 38-39):**
```typescript
const events = driftQuery.data?.events
  ?? (driftQuery.isError ? mockData.events : []);
```
If no stub fires AND no error (e.g., network returns 200 with empty), events=[] and the test for "Data" drift type would fail. But if the stub fires wrongly (URL mismatch), events=mockData.events="data_drift" and the test passes via mock.

---

## Frontend Mock Fallback Paths

### Dashboard.tsx
- Line 40: `?? (marketQuery.isError ? generateMockMarketOverview() : [])` — mock only on error
- Line 48: `if (indicatorQuery.isError) return generateMockIndicatorSeries(selectedTicker)` — mock on error
- Line 59: `generateMockIntradayCandles(selectedTicker, ...)` — **ALWAYS mocks** (no real intraday API)

### Forecasts.tsx
- Lines 111-113: `if (bulkQuery.isError || marketQuery.isError) return generateMockForecasts(horizon)` — mock on error

### Drift.tsx
- Line 25: `if (!active) return modelsQuery.isError ? mockData.activeModel : null` — mock on error
- Line 39: `?? (driftQuery.isError ? mockData.events : [])` — mock on error
- Line 50: `if (rollingPerfQuery.isError) return mockData.rollingPerformance` — mock on error
- Line 73-74: `if (retrainQuery.isError) return mockData.retrainStatus` — **ALWAYS falls back to mockData.retrainStatus even with no error** (line 74 is the default case)

### Models.tsx
- `generateModelDetail(selectedModel.model_name)` — always mocks SHAP data (no real SHAP endpoint)
- Returns "No models trained yet" state for empty `data?.models.length` — this is proper graceful degradation

---

## Fix Strategy

### Option A: Add `beforeAll` API health check + real-data guards (Recommended)
The correct fix is **two-pronged**:

1. **`beforeAll` guard**: Make each spec file check the real backend is reachable and has data. If backend is unhealthy or has no data, `test.skip()` the suite. This ensures tests ONLY run when real data is available.

2. **Replace mock-tolerant assertions with real-data guards**: Instead of asserting on data values that also appear in mocks (AAPL/MSFT/Winner), assert on properties that prove the stub fired: response counts from real API, sentinel values that only exist in fixtures (the `fixture_` prefix).

The existing fixture data already uses `fixture_` prefix on model names as sentinels. The AAPL/MSFT tickers are the weak link.

### Option B: Remove frontend mock fallbacks (Too broad)
Removing `generateMock*` calls from page components would break UX for offline development. Out of scope.

### Chosen Approach: Option A

**For each spec file, add:**

```typescript
test.beforeAll(async ({ request }) => {
  // 1. Health check
  const health = await request.get("http://localhost:8000/health").catch(() => null);
  if (!health || !health.ok()) {
    test.skip(true, "Backend API is not running at http://localhost:8000");
    return;
  }
  // 2. Data availability guard (per-page)
  const overview = await request.get("http://localhost:8000/market/overview").catch(() => null);
  if (!overview?.ok()) {
    test.skip(true, "Backend returned no market data — seed data required");
    return;
  }
  const data = await overview.json();
  if (!data?.stocks?.length) {
    test.skip(true, `Market overview returned 0 stocks — seed data required`);
    return;
  }
});
```

**Replace assertions:**
- `getByText("AAPL")` / `getByText("MSFT")` → assert real API stock count ≥ 1 (use `count` from response)
- `rows.toHaveCount(2)` → `rows.toHaveCount(data.count)` or `await expect(rows.count()).toBeGreaterThan(0)`
- `getByText("Winner")` → keep (fixture uses `is_winner: true` which renders "Winner", mock also has it — but now guarded by beforeAll)

**Per-spec guards:**
- `dashboard.spec.ts` → guard on `GET /market/overview` stocks.length > 0
- `models.spec.ts` → guard on `GET /models/comparison` models.length > 0
- `drift.spec.ts` → guard on `GET /models/drift` events.length > 0 OR `GET /models/comparison` models.length > 0
- `forecasts.spec.ts` → guard on `GET /predict/bulk` predictions.length > 0

---

## Playwright API: `request` in `beforeAll`

Playwright provides `request` fixture for HTTP calls without a browser. In `test.describe` + `test.beforeAll`:

```typescript
test.describe("Suite", () => {
  test.beforeAll(async ({ request }) => {
    const res = await request.get("http://localhost:8000/health");
    if (!res.ok()) test.skip();
  });
});
```

**Note:** `request` in `beforeAll` is the `APIRequestContext` — it uses the `baseURL` from config but can also use absolute URLs.

**`test.skip()` in `beforeAll`**: Calling `test.skip()` inside `beforeAll` skips all tests in the describe block. This is the standard Playwright pattern for suite-level guards.

---

## Assertion Hardening

### dashboard.spec.ts
Current: asserts `"AAPL"` visible (appears in mock too).

Fix: The fixture stubs fire reliably in the test — the real issue is that if stubs DON'T fire, mock fills in with the same tickers. The `beforeAll` health+data guard makes the test environment pre-validated. AAPL/MSFT assertions are fine as long as the guard ensures real data. Alternatively, switch assertions to use fixture-specific sentinel values.

Since all tests already stub routes with `page.route()` and use fixtures with `fixture_` prefix model names, the real gap is:
- **Dashboard tests** assert on `"AAPL"/"MSFT"` which appear in both fixture AND mock — `beforeAll` guard doesn't help here because tests stub the routes anyway.
- The actual problem: if routes aren't stubbed at all (e.g., stub fails), mock fires and AAPL/MSFT still pass.

**Real fix for dashboard**: The tests that stub routes should assert on `fixture_stacking_ensemble_meta_ridge` (from prediction fixture) when possible, OR use the fixture structure to verify count matches fixture data (count=2).

### models.spec.ts
- `rows.toHaveCount(2)` — This is fine when stub fires (fixture has 2 models). Becomes fragile if stub misses.
- `getByText("Winner")` — appears in both fixture and mock.

Fix: Assert `getByText("fixture_stacking_ensemble_meta_ridge")` (already done in most tests). The count=2 is fine as a fixture contract assertion.

### drift.spec.ts
- `getByText("Data")` — from drift_type="data_drift" rendered as "Data". This is already fixture-specific enough (mock might also have data_drift events).

Fix: assert on specific fixture sentinel like "fixture_stacking_ensemble_meta_ridge" visible (already done).

---

## Validation Architecture

### Test Strategy: beforeAll guards + fixture-specific assertions

1. **Health gate**: `GET /health` returns `{"status": "healthy"}` → otherwise skip suite
2. **Data gate per spec**: Check relevant endpoint has data before running fixture-stubbed tests
3. **Fixture sentinels**: Existing `fixture_` prefix model names are already good sentinels — extend their use

### Verification Commands

```bash
# Run the specific spec with --project chromium
npx playwright test e2e/dashboard.spec.ts --project chromium

# Confirm test passes only when backend has real data:
# 1. Start backend with empty DB → tests should skip
# 2. Start backend with seed data → tests should pass
# 3. Kill backend → tests should skip (health check fails)
```

---

## Files to Modify

| File | Change |
|------|--------|
| `e2e/dashboard.spec.ts` | Add `beforeAll` health + market data guard |
| `e2e/forecasts.spec.ts` | Add `beforeAll` health + bulk predictions guard |
| `e2e/models.spec.ts` | Add `beforeAll` health + models comparison guard |
| `e2e/drift.spec.ts` | Add `beforeAll` health + drift/models guard |

## Files NOT to Modify

- `e2e/fixtures/api.ts` — fixture factories are correct, keep them
- `playwright.config.ts` — no changes needed
- `src/pages/*.tsx` — frontend mock fallbacks are intentional for dev UX
- `e2e/backtest.spec.ts` — not in scope per phase definition

---

## Phase 61 Decisions Relevant to Phase 63

From STATE.md:
- `fixture_` prefix in model_name fields distinguishes E2E fixture data from mock fallback values
- Serial mode required for all spec files
- Playwright LIFO route matching: last registered = first matched
- `page.route()` intercepts XHR/fetch requests from the browser

---

## RESEARCH COMPLETE
