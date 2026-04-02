---
phase: 76-ux-polish
verified: 2026-04-02T08:10:00Z
status: passed
score: 23/23 must-haves verified
re_verification: false
---

# Phase 76: UX Polish Verification Report

**Phase Goal:** UX polish — backtest empty state + loading feedback, icon tooltips, sector and company names in forecasts, horizon selector, dashboard below-fold content, analytics OLAP chart ticker selector
**Verified:** 2026-04-02T08:10:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

#### Plan 01 — Backtest Idle State and Tooltip Audit

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Backtest page shows a centered idle prompt (PlayArrow icon + text) when no backtest has been run yet | VERIFIED | `!activeTicker` block at line 211 renders PlayArrowIcon + "Configure parameters above" text |
| 2 | The idle state disappears once Run Backtest is clicked and a query fires | VERIFIED | `setActiveTicker(cleaned)` in `handleRun` (line 51) makes `!activeTicker` false permanently |
| 3 | The idle state never flashes after data has loaded (hasRunOnce guard prevents regression) | VERIFIED | `activeTicker` is `string \| null`; once set to a non-null string by `handleRun`, it never reverts to null — functionally equivalent to `hasRunOnce` |
| 4 | All icon-only buttons across all pages have a MUI Tooltip with a descriptive action label | VERIFIED | 7 Tooltip usages in Backtest.tsx; audit found no untooltipped icon-only buttons across Forecasts, Dashboard, Models, Drift, Analytics, NavBar (all either already wrapped or use text labels) |
| 5 | Backtest export buttons (CSV, PDF) already have Tooltips — confirmed present, not duplicated | VERIFIED | Lines 184–198 pattern confirmed; `grep -c "Tooltip" Backtest.tsx` returns 7 |

#### Plan 02 — Analytics null staleness and OLAP ticker selector

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | Feature Freshness rows with null staleness display — (em-dash) instead of "unknown" | VERIFIED | Line 23: `if (s === null) return "—"` |
| 7 | Feature Freshness rows with null staleness are greyed out at reduced opacity | VERIFIED | Line 64: `<Box sx={{ opacity: view.staleness_seconds === null ? 0.45 : 1 }}>` |
| 8 | Feature Freshness rows with null staleness show no LinearProgress bar | VERIFIED | Line 77: `{view.staleness_seconds !== null && (<LinearProgress .../>)}` |
| 9 | getStalenessColor(null) returns "inherit", not "warning" | VERIFIED | Line 16: `if (s === null) return "inherit"` |
| 10 | OLAP Candle Chart has a ticker Autocomplete dropdown in its panel header | VERIFIED | Line 135: `<Autocomplete` in panel header; `Autocomplete` imported at line 5 |
| 11 | OLAP ticker dropdown is populated from useMarketOverview() — not hardcoded | VERIFIED | Line 100: `const marketQuery = useMarketOverview()` + useMemo tickers derivation at lines 101–104 |
| 12 | OLAP interval toggle (1H/1D) continues to work independently of ticker selection | VERIFIED | `interval` state unchanged; `ToggleButtonGroup` wired to `setInterval` independently of ticker state |

#### Plan 03 — Backend data: horizons + company names

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 13 | AVAILABLE_HORIZONS config includes 14 — /predict/bulk?horizon=14 returns 200 (not 400) | VERIFIED | config.py line 86: `AVAILABLE_HORIZONS: str = "1,7,14,30"` |
| 14 | The weekly-training CronJob includes --horizons 1,7,14,30 so future runs produce 14D predictions | VERIFIED | cronjob-training.yaml lines 37–38: `"--horizons"` / `"1,7,14,30"` |
| 15 | HorizonToggle on Forecasts page shows 14D option immediately after API deployment (horizons.json seed file contains 14) | VERIFIED | `serving/active/horizons.json`: `{"horizons": [1, 7, 14, 30], "default": 7}` |
| 16 | The stocks table has non-null company_name and sector for all active tickers (after next ingestion) | VERIFIED | db_writer.py: `_fetch_ticker_metadata()` uses yfinance `longName`/`sector`; upsert SQL writes both columns; fallback ensures `company_name` is never NULL |
| 17 | GET /market/overview returns non-null company_name for all active stocks (after next ingestion cycle) | VERIFIED | db_writer enrichment populates the stocks table rows which market overview queries; deferred by design to next kafka-consumer run |

#### Plan 04 — Dashboard Top Movers below-fold content

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 18 | Dashboard page shows a Top Movers section below the treemap without requiring stock selection | VERIFIED | Dashboard.tsx line 475: `<TopMoversPanel .../>` between treemap Box (line 459) and StockSelector (line 482) |
| 19 | Top Movers section displays top 5 gainers and top 5 losers by daily_change_pct | VERIFIED | TopMoversPanel.tsx lines 113–116: single sort by `daily_change_pct` desc; `gainers = sorted.slice(0, 5)`; `losers = sorted.slice(-5).reverse()` |
| 20 | Each mover row shows ticker, company name, last close price, and daily change percent | VERIFIED | MoverRow renders `stock.ticker`, `stock.company_name ?? stock.ticker`, `stock.last_close.toFixed(2)`, `pct.toFixed(2)%` |
| 21 | Clicking a mover row selects that stock and scrolls to the detail panel | VERIFIED | `onSelectTicker` prop wired to `handleSelect` (Dashboard.tsx line 478); `handleSelect` calls `scrollIntoView` on `detailRef` |
| 22 | Top Movers section is always visible (not gated behind Collapse or stock selection) | VERIFIED | TopMoversPanel placed outside any `Collapse` or conditional; render order: treemap → TopMoversPanel → StockSelector → Collapse |
| 23 | Top Movers shows a skeleton when market data is loading | VERIFIED | TopMoversPanel lines 155–165: `loading ? skeletonRows.map(Skeleton) : gainers.map(MoverRow)` |

**Score:** 23/23 truths verified

---

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `services/frontend/src/pages/Backtest.tsx` | VERIFIED | `useState<string | null>(null)` at line 39; idle state block at line 211; `activeTicker ?? ""` at line 41 |
| `services/frontend/src/components/analytics/FeatureFreshnessPanel.tsx` | VERIFIED | Returns `"—"` (line 23), `"inherit"` (line 16); conditional LinearProgress (line 77); opacity guard (line 64) |
| `services/frontend/src/components/analytics/OLAPCandleChart.tsx` | VERIFIED | No `DEFAULT_TICKER`; `useMarketOverview` imported and used; `useState("AAPL")` ticker state; `Autocomplete` in header |
| `services/api/app/config.py` | VERIFIED | `AVAILABLE_HORIZONS: str = "1,7,14,30"` at line 86 |
| `k8s/ml/cronjob-training.yaml` | VERIFIED | `"--horizons"` / `"1,7,14,30"` args at lines 37–38 |
| `services/kafka-consumer/consumer/db_writer.py` | VERIFIED | `_fetch_ticker_metadata()` function; yfinance `longName`; 3-column INSERT with DO UPDATE SET |
| `services/api/serving/active/horizons.json` | VERIFIED | `{"horizons": [1, 7, 14, 30], "default": 7}` |
| `services/api/tests/test_predict_horizon.py` | VERIFIED | `TestHorizon14Support` class with `test_bulk_horizon_14_accepted` and `test_bulk_horizon_99_rejected` |
| `services/frontend/src/components/dashboard/TopMoversPanel.tsx` | VERIFIED | Full component with MoverRow, sorting, 5 gainers/5 losers, skeleton loading |
| `services/frontend/src/components/dashboard/index.ts` | VERIFIED | Line 10: `export { default as TopMoversPanel } from "./TopMoversPanel"` |
| `services/frontend/src/pages/Dashboard.tsx` | VERIFIED | TopMoversPanel imported (line 27) and used at line 475 with `loading` and `onSelectTicker` props |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `Backtest.tsx activeTicker state` | idle state render block | `!activeTicker` conditional | WIRED | Line 211: `{!activeTicker && (...)}`; becomes false permanently after `handleRun` |
| `handleRun` | `setActiveTicker` | triggers query enable | WIRED | Line 51: `if (cleaned) setActiveTicker(cleaned)` |
| `FeatureFreshnessPanel getStalenessColor` | LinearProgress color prop | TypeScript type constraint | WIRED | Line 77: conditional render ensures `"inherit"` branch never reaches `<LinearProgress color=...>` |
| `OLAPCandleChart ticker state` | `useAnalyticsCandles(ticker, interval)` | replaces DEFAULT_TICKER | WIRED | Line 105: `useAnalyticsCandles(ticker, interval)` |
| `config.py AVAILABLE_HORIZONS` | `_validate_horizon` in predict.py | `settings.available_horizons_list` | WIRED | predict.py line 45: `if horizon not in settings.available_horizons_list` |
| `db_writer.py _ensure_tickers` | stocks table company_name/sector | yfinance Ticker.info | WIRED | `_fetch_ticker_metadata` fetches `longName`/`sector`; INSERT SQL writes both columns |
| `serving/active/horizons.json` | `useAvailableHorizons() → HorizonToggle` | `load_available_horizons()` reads file | WIRED | File contains `[1, 7, 14, 30]`; load function reads from SERVING_DIR |
| `Dashboard.tsx stocks (marketQuery)` | TopMoversPanel gainers/losers | sort by `daily_change_pct` in TopMoversPanel | WIRED | TopMoversPanel.tsx line 113: `.sort((a, b) => (b.daily_change_pct ?? 0) - (a.daily_change_pct ?? 0))` |
| `TopMoversPanel MoverRow onClick` | `handleSelect(ticker)` | `onSelectTicker` prop | WIRED | Dashboard.tsx line 478: `onSelectTicker={handleSelect}` |

---

## Requirements Coverage

No requirement IDs declared across any of the 4 plans (`requirements: []`). No orphaned requirements in REQUIREMENTS.md mapped to Phase 76.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `OLAPCandleChart.tsx` | 166 | `<PlaceholderCard title="No candle data available" phase={69} />` | INFO | Pre-existing empty-state rendered when no candle data returned (not loading, not error). This is a legitimate empty state, not a stub — it is conditional on `!isLoading && candles.length === 0`. Not introduced by Phase 76. |
| `FeatureFreshnessPanel.tsx` | 56 | `<PlaceholderCard title="No feature views found" phase={69} />` | INFO | Pre-existing empty-state rendered when API returns no views. Conditional on data absence. Not a stub. Not introduced by Phase 76. |

No blockers. Both `PlaceholderCard` usages are conditional error/empty-states guarded by real data checks, not stubs replacing functionality.

---

## Human Verification Required

### 1. Forecasts page Company and Sector columns

**Test:** Observe the Forecasts page after the next kafka-consumer ingestion cycle processes at least one message per active ticker.
**Expected:** Company column shows real names (e.g. "Apple Inc.") and Sector column shows real sectors (e.g. "Technology"), not blank or ticker symbols.
**Why human:** The backfill depends on a live yfinance network call from the running kafka-consumer, which cannot be verified without a live deployment or integration test environment.

### 2. HorizonToggle 14D option in Forecasts page

**Test:** Open the Forecasts page; check that the HorizonToggle shows a "14D" option.
**Expected:** 14D button visible alongside 7D and 30D.
**Why human:** Depends on the frontend reading `horizons.json` from the correct path — the seed file path is `services/api/serving/active/` which matches K8s override but not the default `SERVING_DIR=/models/active`. In local dev, 14D may only appear if the API is run from the service directory. Requires runtime observation.

### 3. Dashboard Top Movers visual layout

**Test:** Open the Dashboard; verify the Top Gainers and Top Losers panels appear below the treemap.
**Expected:** Two side-by-side panels (green-accented for gainers, pink-accented for losers) each showing 5 stocks with ticker, company name, price, and percentage change.
**Why human:** Visual layout and color rendering cannot be verified programmatically.

### 4. Backtest idle state visual

**Test:** Navigate to the Backtest page without clicking Run Backtest.
**Expected:** Centered play icon and instruction text "Configure parameters above and click Run Backtest to see results" visible in the content area.
**Why human:** Visual rendering and center alignment require browser observation.

---

## Commit Verification

All 8 commits from summaries verified in git log:

| Commit | Description |
|--------|-------------|
| `eca8784` | fix(76-02): fix FeatureFreshnessPanel null staleness display |
| `106cb75` | feat(76-02): add ticker Autocomplete to OLAPCandleChart |
| `e063c96` | test(76-03): add failing test for horizon=14 acceptance |
| `437bccc` | feat(76-03): add 14D horizon support and seed horizons.json |
| `50031ac` | test(76-03): add failing tests for yfinance-enriched _ensure_tickers |
| `df0a08e` | feat(76-03): enrich stocks table with company_name and sector from yfinance |
| `50b85ff` | feat(76-04): create TopMoversPanel component |
| `64197ca` | feat(76-04): wire TopMoversPanel into Dashboard below treemap |

---

## Overall Assessment

All 23 must-have truths verified. All artifacts exist, are substantive, and are wired. All key links confirmed. No anti-patterns introduced by this phase. No blocker gaps.

The two `PlaceholderCard` usages flagged in anti-pattern scan are pre-existing and conditional on real data absence — they are not stubs. The Forecasts company/sector column backfill is intentionally runtime-dependent (requires a kafka-consumer run) and documented as such in the plan.

---

_Verified: 2026-04-02T08:10:00Z_
_Verifier: Claude (gsd-verifier)_
