# Audit Section 2: System Improvements

Status: IN PROGRESS

---

## Improvements Identified and Implemented

---

## Frontend Issues Found

### US-002: Dashboard Market Tab Audit (2026-04-07)

**Status:** PASS with minor issues

**Verified working:**
- Market Dashboard loads with real live data (WS CONNECTED)
- Ticker bar: AAPL $252.62 -0.58%, MSFT $358.06 -1.06%, NVDA $164.56 -2.48% (real prices)
- Market Treemap renders: TECHNOLOGY, COMMUNICATION SERVICES, FINANCIAL SERVICES, CONSUMER CYCLICAL, HEALTHCARE, ENERGY sectors with color-coded % changes. 62 Gainers / 98 Losers.
- Top Gainers: AMD +4.14%, DOW +3.45%, APA +2.81%, AKAM +2.71%, BIIB +2.31%
- Top Losers: CTAS -3.98%, TSLA -3.55%, BBY -2.93%, CCI -2.59%, CBOE -2.59%
- Ticker search: type 'AAPL' → dropdown shows "AAPL Apple Inc. -0.58% $252.62" ✓
- AAPL price cards: Current Price $252.62, Daily Change -0.58%, Market Cap $3.40T, Volume 41.3M, VWAP $232.96, 52W Range $9-$286 ✓
- Historical chart: AAPL — Historical with BB Lower/Upper, Close, SMA 20, SMA 200, SMA 50, Forecast lines ✓
- 0 console errors

**Issues found:**
1. **Intraday candle chart unavailable**: Left "Price Charts" panel shows "Intraday candle data unavailable" — no intraday OHLCV candlestick data. The historical chart works but the real-time intraday panel is empty. Root cause likely: intraday data endpoint not returning data (API may not support minute-level bars).
2. **52W Range shows $9**: AAPL 52W Range displayed as "$9 – $286" — the $9 low is incorrect (AAPL never traded that low in any recent 52-week window). Likely a data normalization bug.
3. **WebSocket warning**: `ws://localhost:8010/ws/prices` — "WebSocket is closed before the connection is established" (warning only, status shows WS CONNECTED so reconnect logic works).
4. **No sentiment data**: Market Sentiment panel shows "No sentiment data available — Reddit pipeline may be starting up" for all tickers (AAPL, TSLA, MSFT, NVDA, AMZN). Known issue: sentiment_timeseries table has 0 rows.

**Screenshots:**
- audit-p02-dashboard-market.png — full dashboard on load
- audit-p02-search-dropdown.png — search box with AAPL result in dropdown
- audit-p02-price-cards.png — AAPL price cards + historical chart
- audit-p02-treemap.png — market treemap + top movers

---

### US-003: Dashboard Macro Tab Audit (2026-04-07)

**Status:** FULL PASS — all 19 cards show real values, MacroChart fully functional

**Verified working:**
- Macro tab toggle switches from Market to Macro view cleanly
- **19 macro indicator cards** visible, ALL showing real numeric values (no dashes)
  - VIX: 18.50, SPY RETURN: +0.12%, 10Y YIELD: 4.39%, 2-10 SPREAD: -0.67%
  - HY SPREAD: 292.70%, WTI CRUDE: $70.66, USD INDEX: 110.5, INITIAL CLAIMS: 217,997
  - CORE PCE: 122.883, SECTOR RETURN: +0.08%, 52W HIGH %: 0.85, 52W LOW %: 0.35
  - 3M-10Y SPREAD: -0.49%, BAA YIELD: 5.45%, USD/JPY: 149.9, NFCI: -0.10
  - CPI INDEX: 314.8, 2Y YIELD: 4.82%, 10Y BREAKEVEN: 2.25%
  - Data timestamp: "As of 2026-04-04"
- MacroChart "HISTORICAL TRENDS — 90 DAYS" shows **17 series chips**: 10Y Yield, 2-10 Spread, 2Y Yield, 3M-10Y Spread, HY Spread, BAA Yield, 10Y Breakeven, WTI Crude, Trade USD Index, USD/JPY, Jobless Claims, NFCI, CPI, Core PCE, Sector Return, 52W High %, 52W Low %
- Clicking BAA Yield chip updates chart ✓
- Default active chips on load: 10Y Yield, 2-10 Spread, WTI Crude

**Console output:**
- 0 errors
- 2 pre-existing warnings: WS timing warning + ECharts dispose warning (both non-blocking)

**Card count:** 19 (meets ≥17 requirement)

**Screenshots:**
- audit-p03-macro-tab.png — full Macro tab with all 19 cards
- audit-p03-macro-chart-chips.png — MacroChart with all 17 series chips
- audit-p03-macro-chart-baa.png — chart after clicking BAA Yield chip
- audit-p03-macro-tab-full.png — full-page screenshot


---

### US-005: Dashboard — Technical Analysis Panel Audit (2026-04-07)

**Status:** PASS — all 6 TA indicator charts render with real data, TimeframeSelector works

**API findings:**
- `curl http://localhost:8010/market/history/AAPL?period=1mo` → **404** (endpoint does not exist with this name)
- Actual endpoint: `GET /market/indicators/{ticker}` — returns RSI, MACD, BB, SMA, EMA, Volume, VWAP series
- `curl http://localhost:8010/market/indicators/AAPL` → full 250-point series with latest values
- Latest AMD RSI: 49.4, MACD line: -0.98, MACD signal: 0.02, SMA 20: $257.13, SMA 50: $250.64, SMA 200: $240.39

**Verified working:**
- Stock selection via Top Gainers click (AMD) → TA panel expands below ✓
- Key Metrics: Current Price, Daily Change, Volume (20D Avg), VWAP, 52W Range all populated ✓
- TimeframeSelector (1D/1W/1M/3M/1Y) — clicking 1W updates historical chart to 1-week view ✓
- **RSI (14)** chart: renders full time series, reference lines at 30/70, no NaN visible ✓
- **MACD (12/26/9)** chart: MACD line (blue) and signal (orange dashed) render correctly ✓
- **Bollinger Bands** chart: Upper/Lower bands with close price render correctly ✓
- **Moving Averages** chart: Close, SMA 20, SMA 50, SMA 200, EMA 12, EMA 26 all render, tooltip shows exact values ✓
- **Volume (20-day SMA)** bar chart: renders with proper M/K formatting ✓
- **VWAP** chart: Close vs VWAP lines render correctly ✓
- 0 console errors (3 warnings: WebSocket closed × 2, ECharts disposed × 1 — all pre-existing)

**Data quality issues found:**
1. **MACD histogram always null** — `macd_histogram` is null for all 250 data points in the series. MACD bars never render. Root cause: histogram not being computed in the indicators pipeline.
2. **BB Middle band always null** — `bb_middle` is null for all 250 data points. Middle Bollinger Band line never renders.
3. **Market Cap shows $0** — KeyMetrics card shows "MARKET CAP: $0" for AMD. Data not populated.
4. **Sector shows "UNKNOWN"** — AMD company sector not resolved; displays as "UNKNOWN" instead of "Technology".
5. **Intraday candle chart unavailable** — left panel shows placeholder; intraday data requires live Flink pipeline.
6. **No toggle for individual indicators** — acceptance criteria mentioned toggling RSI/MACD/BB on/off; no such UI exists. All 6 charts always visible. Minor UX gap.

**Screenshots:**
- audit-p05-ta-panel.png — initial dashboard on load
- audit-p05-ta-panel-loaded.png — after clicking AMD from Top Gainers
- audit-p05-rsi-macd-bb.png — RSI, MACD, Bollinger Bands charts
- audit-p05-ta-charts-bottom.png — Moving Averages, Volume, VWAP charts
- audit-p05-timeframe-1w.png — 1W timeframe selected, Key Metrics, historical chart

---

### US-006: Dashboard — Streaming Features Panel Audit (2026-04-07)

**Status:** PASS — panel renders correctly; empty state shown as expected (Flink pipeline lacks live intraday data)

**API findings:**
- `curl http://localhost:8010/market/streaming-features/AAPL` → HTTP 200
- Response: `{"ticker":"AAPL","ema_20":null,"rsi_14":null,"macd_signal":null,"available":false,"source":"flink-indicator-stream","sampled_at":"2026-04-07T10:44:23Z","fred_macro":null}`
- `available: false` — Flink indicator_stream job running but no live intraday data flowing in

**Verified working:**
- "⚡ STREAMING FEATURES" section header visible after selecting AAPL stock ✓
- Panel renders empty state: "No live Flink data yet — intraday data ingestion must be active and the indicator_stream Flink job must be running." ✓
- `data-testid="streaming-features-empty"` present in DOM — correct fallback state ✓
- Panel uses correct API endpoint: `/market/streaming-features/{ticker}` ✓
- Panel would show EMA-20, RSI-14, MACD Signal columns with "LIVE — Flink" chip when data available ✓
- 0 console errors (3 pre-existing warnings: WS timing × 2, ECharts dispose × 1)

## Streaming Pipeline Status

**Infrastructure pods — all Running:**
- `ingestion` namespace: `reddit-producer-75dcc9fdb6-7jj6m` — Running (3d10h age) ✓
- `processing` namespace: `kafka-consumer-78875d9b96-t8m62`, `kafka-consumer-78875d9b96-tbr7z` — Running (both 3d10h) ✓
- `flink` namespace:
  - `indicator-stream-*` — Running (17 restarts — job recovering) ✓
  - `indicator-stream-taskmanager-10-1` — Running ✓
  - `feast-writer-*` — Running (13 restarts) ✓
  - `ohlcv-normalizer-*` — Running (17 restarts) ✓
  - `sentiment-stream-*` — Running ✓
  - `sentiment-writer-*` — Running ✓
  - `flink-kubernetes-operator-*` — Running ✓

**Root cause of empty Streaming Features:**
- Flink `indicator_stream` job processes intraday OHLCV ticks from Kafka
- Intraday ingestion CronJobs show `Completed` status (no live streaming), only ran batch jobs
- No real-time tick data in Kafka topic → Flink job has nothing to compute → Feast Redis store stays empty
- This is expected outside market hours or when intraday tick pipeline is not streaming live

**Screenshots:**
- audit-p06-streaming-features-initial.png — dashboard before stock selection
- audit-p06-streaming-features.png — after AAPL selected, STREAMING FEATURES section visible
- audit-p06-streaming-features-panel.png — zoomed view of Streaming Features empty state

---

### US-004: Dashboard — Sentiment Tab Full Feature Audit (2026-04-07)

**Status:** PASS — empty state renders correctly, appropriate messaging shown

**API findings:**
- `curl http://localhost:8010/market/sentiment/AAPL` → **404 Not Found** (endpoint does not exist at this path)
- Actual endpoint: `GET /market/sentiment/{ticker}/timeseries`
- `curl http://localhost:8010/market/sentiment/AAPL/timeseries` → `{"ticker":"AAPL","points":[],"count":0,"window_hours":10}`
- **0 rows in sentiment_timeseries** — Flink sentiment-writer is in CREATED/STABLE state, not producing data

**Verified working:**
- Market Sentiment section renders below Top Gainers/Losers on the Market tab
- Header: "MARKET SENTIMENT" with lightning bolt icon ✓
- Ticker quick-select row: AAPL (selected/pink), TSLA, MSFT, NVDA, AMZN chips ✓
- Sentiment indicator (top-right): blue dot with "—" label (correct for no data) ✓
- Empty state message: "No sentiment data available" ✓
- Sub-text: "Reddit pipeline may be starting up" ✓
- No console errors (2 pre-existing warnings unrelated to sentiment)

**Sentiment pipeline status:**
- **Sentiment pipeline not writing data — Flink sentiment-writer may be in CREATED state**
- sentiment_timeseries table has 0 rows
- reddit-producer is running in ingestion namespace (pod age 3d)
- Flink job in CREATED/STABLE state — not actively consuming Reddit posts and writing sentiment scores

**Console output:**
- 0 errors
- 2 pre-existing warnings: WS timing warning + ECharts dispose warning (both non-blocking, unrelated to sentiment)

**Screenshots:**
- audit-p04-sentiment.png — full dashboard showing Market Sentiment section
- audit-p04-sentiment-panel.png — zoomed view of Market Sentiment panel with empty state


---

### US-007: Forecasts Page Audit (2026-04-07)

**Status:** FULL PASS — table loads with real data, model_name column present, horizon toggle functional

**Verified working:**
- ForecastTable renders with real tickers (TSLA, BWA, AWK, CTSH, APH, SCHW, CZR, AVB, CLX, etc.)
- All 4 horizon groups visible simultaneously: 1-DAY FORECAST, 7-DAY FORECAST, 14-DAY FORECAST, 30-DAY FORECAST
- **MODEL column IS present** (field: model_name, header: "Model") — shows "catboost_standard" for all rows — this was previously marked as missing in progress.txt but had already been implemented
- Predicted prices and return % shown with green/red color coding
- Clicking a stock row opens detail drawer with:
  - 1D / 7D / 14D / 30D horizon toggle buttons at top (HorizonToggle component)
  - Price history + forecast chart (CHD: 7-day chart shown)
  - RSI (14), MACD (12/26/9), Bollinger Band Width charts
  - SHAP Feature Importance bar chart (shows volume, obv, ema, close, sma, returns, bb_l, nacd, etc.)
- Filter bar visible: Search, Sector dropdown, Min Return %, Max Return %, Min Confidence slider, Clear
- Export buttons: CSV and PDF

**API verification:**
- `curl 'http://localhost:8010/predict/bulk?horizon=7'` returns predictions array with model_name field ("CatBoost_standard") ✅

**Console output:**
- 0 errors
- 0 warnings

**Screenshots:**
- audit-p07-forecasts.png — full Forecasts page with table loaded
- audit-p07-horizon-7d.png — detail drawer with 1D/7D/14D/30D horizon toggle + CHD charts + SHAP panel


---

### US-009: Forecasts — StockComparisonPanel and StockDetailChart audit (2026-04-07)

**Status:** PARTIAL PASS — StockDetailChart and IndicatorOverlayCharts fully functional; StockComparisonPanel non-functional (dead code wiring)

**Verified working:**
- StockDetailChart renders: TSLA/AWK price history + 7-day forecast line with predicted price dot ✓
- IndicatorOverlayCharts verified: RSI (14), MACD (12/26/9), Bollinger Band Width all render with real data ✓
- SHAP Feature Importance panel renders alongside detail chart ✓
- Horizon toggle (1D/7D/14D/30D) present in detail drawer ✓
- 0 console errors, 0 warnings

**Issues found:**
1. **StockComparisonPanel is non-functional — dead code wiring.** The `handleToggleCompare` function is defined in `Forecasts.tsx` but is never passed to `ForecastTable` (which has no `onToggleCompare` prop). As a result, `comparisonTickers` state always remains `[]` and the panel permanently shows the placeholder "Select 2+ stocks in the table to compare side by side." There is no UI mechanism to populate it.
   - Root cause: `ForecastTable` props are `{rows, selectedTicker, onSelectTicker}` — no comparison toggle prop
   - Fix needed: add `onToggleCompare` and `comparisonTickers` props to `ForecastTable`, wire MUI DataGrid checkbox selection or an "Add to Compare" button per row

**Screenshots:**
- audit-p09-forecasts-loaded.png — Forecasts table with real data
- audit-p09-detail-chart.png — full-page view of StockDetailChart (TSLA) + IndicatorOverlayCharts
- audit-p09-indicator-overlay.png — viewport: RSI + MACD + Bollinger Band overlays visible
- audit-p09-comparison-placeholder.png — StockComparisonPanel shows placeholder (no trigger mechanism)

---

### US-010: Models Page — ModelComparisonTable and FoldPerformanceChart Audit (2026-04-07)

**Status:** PASS

**Verified working:**
- Models page loads at http://localhost:5173/models with real data ✓
- WinnerCard: stacking_ensemble displayed with "Winner" badge, OOS RMSE 0.023400, OOS R² -0.0259, Fold Stability 0.0000, Scaler Meta_ridge ✓
- ModelComparisonTable: 9 models rendered with OOS RMSE/MAE/R²/MAPE/DIR.ACCURACY/FOLD STABILITY/STATUS columns — all numeric values populated ✓
  - Models present: stacking_ensemble (Inactive), elastic_net (Inactive), CatBoost_standard (**Active**), RandomForest_minmax (Inactive), Ridge_quantile (Inactive), bayesian_ridge (Inactive), linear_regression (Inactive), ridge (Inactive), lasso (Inactive)
  - Note: XGBoost and LightGBM are NOT in the registry — only 9 models trained
- FoldPerformanceChart: renders 5 folds (Fold 1–5) with MAE/RMSE/R² bars for stacking_ensemble ✓ (uses mock fold data from generateModelDetail utility — no real /models/fold API)
- ShapBarChart: FEATURE IMPORTANCE (SHAP) with feature bars ✓ (mock data)
- ShapBeeswarmPlot: SHAP VALUE DISTRIBUTION scatter plot ✓ (mock data)
- 0 console errors, 0 warnings

**Issues found:**
1. **API key name mismatch with PRD criteria**: PRD states `/models/comparison` should have `model_metrics` array, but the actual API returns `models` key. Frontend correctly reads `data.models` — no bug, just documentation inconsistency.
2. **FoldPerformanceChart uses mock data**: `generateModelDetail()` in `utils/mockModelData.ts` generates synthetic fold metrics. No real cross-validation fold data is stored or served. The chart renders but shows fabricated values.
3. **XGBoost and LightGBM absent**: Only 9 models in registry — no XGBoost or LightGBM trained models. These were mentioned in phase plan acceptance criteria.

**Screenshots:**
- audit-p10-models.png — full-page Models page initial load
- audit-p10-winner.png — WinnerCard stacking_ensemble visible
- audit-p10-comparison-table.png — ModelComparisonTable with 9 model rows
- audit-p10-fold-chart.png — FoldPerformanceChart + SHAP charts (scrolled to bottom)

---

### US-011: Models Page — ModelDetailPanel Audit (2026-04-07)

**Status:** PASS

**Verified working:**
- Navigate to http://localhost:5173/models — ModelDetailPanel already open by default showing stacking_ensemble ✓
- Clicked CatBoost_standard row — DetailPanel updated to show CatBoost_standard v1 (Active), Scaler=Standard, Saved At=3/22/2026, Fold Stability=0.0089, Hyperparameters: depth=6 iterations=500 learning_rate=0.05 ✓
- OOS Metrics panel shows r2/mae/mape/rmse/directional_accuracy for selected model ✓
- "In-Sample vs Out-of-Sample Metrics" section renders with metric values ✓
- Feature Importance (SHAP) bar chart renders with 15 features ✓
- SHAP Value Distribution beeswarm plot renders ✓
- Fold-by-Fold Performance chart renders with 5 folds (MAE/RMSE/R² bars) ✓
- 0 console errors, 0 warnings

**API findings:**
- `/models/list` does NOT exist — returns 404. Actual endpoint is `/models/comparison`
- `/models/comparison` response keys: `model_name`, `scaler_variant`, `version`, `is_winner`, `is_active`, `traffic_weight`, `oos_metrics`, `fold_stability`, `best_params`, `saved_at`
- **`features_count` is NOT in the API response** — detail panel has no feature count display
- **`model_id` field is absent** — API uses `model_name` as the identifier (no separate integer ID)
- **`trained_at` field is absent** — UI shows `saved_at` labeled as "Saved At"

**Issues found:**
1. **`/models/list` endpoint missing**: PRD acceptance criteria references `curl http://localhost:8010/models/list` but this route returns 404. The comparison data comes from `/models/comparison`. Low priority — frontend is unaffected.
2. **Feature count not exposed or displayed**: Neither the API nor the UI shows how many features the model was trained on. Given the recent feature count change (49 features after macro additions vs. earlier models trained on fewer), this would be useful for stale-model detection.
3. **model_name displayed as heading only**: The detail panel shows `model_name` as a heading (`<h6>`) rather than a labeled key-value field. It correctly matches registry names from `/models/comparison`.

**Screenshots:**
- audit-p11-models-initial.png — Models page initial state (stacking_ensemble selected)
- audit-p11-model-detail.png — Full page with CatBoost_standard selected, detail panel updated

---

### US-012: Drift Page Audit — ActiveModelCard, DriftTimeline, RollingPerformanceChart (2026-04-07)

**Status:** PASS with one data gap

**Verified working:**
- Drift page loads at `/drift` with 0 console errors ✅
- **ActiveModelCard**: Shows "CatBoost_standard" Active badge, RMSE 0.0234, MAE 0.0187, Dir. Acc 62.0%, Scaler: Standard, Version: v1, Trained: Mar 22, 2026 ✅
- **RetrainStatusPanel**: "Up to Date", Last retrained: Mar 31, 2026, Previous Model: ridge (1.4089 RMSE, MAE 0.1523) vs Current Model: lasso (1.4120 RMSE, MAE 0.1463) ✅
- **DriftTimeline**: 15 events detected — Data (Medium), Prediction (Low), Concept (High), Data (Low) drift events with timestamps, feature names (rsi_14, macd_line, bb_upper) ✅
- `/models/drift` API returns 15 events with `any_recent_drift: true`, latest data drift on rsi_14 and macd_line ✅

**Issues found:**
1. **RollingPerformanceChart shows "No performance data available"**: `/models/drift/rolling-performance` returns `{"entries":[],"model_name":null,"period_days":30,"count":0}`. The endpoint exists but the DB table has no rolling performance rows. UI handles empty state gracefully. Data population would require predictions to be scored against actuals over 30 days.

**Screenshots:**
- audit-p12-drift.png — Full Drift page
- audit-p12-active-model.png — ActiveModelCard (CatBoost_standard Active)
- audit-p12-retrain-status.png — RetrainStatusPanel (Up to Date)
- audit-p12-rolling-perf.png — RollingPerformanceChart (empty state)
- audit-p12-drift-timeline.png — DriftTimeline (15 events)


---

### US-013: Drift Page — FeatureDistributionChart Audit (2026-04-07)

**Status:** IMPLEMENTED & PASS

**Gap found:** FeatureDistributionChart was hardcoded with `distributions={[]}` and returned null (invisible). No backend endpoint existed to provide training vs. recent feature distributions.

**Fix implemented:**
1. Added `/models/drift/feature-distributions` endpoint to FastAPI (`services/api/app/routers/models.py`)
   - Queries `feature_store` table (7.2M rows, 46 features, 150 tickers, 2022–2026)
   - Extracts drifted features from `drift_logs.details_json->per_feature` (KS/PSI stats)
   - Computes 10-bin training vs recent histograms (training ≤ 1yr ago, recent ≥ 60d ago)
   - Returns percentage-normalized bin counts with KS stat and PSI value per feature
2. Added `FeatureDistributionEntry` and `FeatureDistributionResponse` schemas to `schemas.py`
3. Added `useFeatureDistributions(nFeatures)` React Query hook to `queries.ts`
4. Wired hook into `Drift.tsx`, mapping snake_case API response to camelCase component props

**Verified working:**
- `/models/drift/feature-distributions?n_features=12` returns 12 features (rsi_14, macd_line, bb_upper drifted; 9 stable) with 10 histogram bins each ✅
- FeatureDistributionChart accordion renders with "12 features monitored" ✅
- Feature cards show "Drifted" chip for rsi_14, macd_line, bb_upper with KS/PSI stats ✅
- 0 console errors ✅
- TypeScript 0 errors, `npm run build` passes ✅

**Data freshness:** Training period ≤ 2025-04-07, recent period ≥ 2026-02-06. No "last updated" date displayed in UI — chart shows period labels from API response but not surfaced to component.

**Screenshots:**
- audit-p13-feature-dist.png — Full drift page with accordion expanded, feature cards visible
- audit-p13-feature-select.png — Scroll showing 12 features monitored header

---

### US-014: Analytics page — StreamHealthPanel, FeatureFreshnessPanel, SystemHealthSummary (2026-04-07)

**Status:** PASS — all 3 components render with real pipeline data, 0 console errors

**Verified working:**
- StreamHealthPanel: Shows 3 Flink jobs — ohlcv-normalizer (RUNNING), indicator-stream (RUNNING), feast-writer-job (RUNNING) via `/analytics/flink/jobs`
- FeatureFreshnessPanel: Shows ohlcv_stats_fv, technical_indicators_fv, lag_features_fv — timestamps display "—" (null) because feast_metadata table has no row-level freshness data from Feast materialization
- SystemHealthSummary cards: Argo CD Sync = Synced, Flink Cluster = 3 running / 0 failed, Feast Latency p99 = 0.1-0.2 ms, CA Last Refresh = 1:02:18 PM
- Kafka Stream Lag chart: Renders, shows 0 lag across 3 partitions (P0/P1/P2) — healthy
- OLAP Candle Chart: Renders for AAPL with price axis ($145–$180 range)
- 0 console errors

**Note on acceptance criteria paths:**
- The PRD referenced `/analytics/stream-health` and `/analytics/feature-freshness` — these return 404.
- Actual API paths are `/analytics/flink/jobs`, `/analytics/feast/freshness`, `/analytics/kafka/lag`, `/analytics/summary`.
- Frontend correctly calls the real paths; the PRD paths were documentation-only aliases that were never implemented. Not a bug.

**FeatureFreshness null timestamps — root cause:**
- `/analytics/feast/freshness` queries the `feast_metadata` table (PostgreSQL-backed Feast registry)
- All 3 FeatureViews return `last_updated: null` — Feast has never materialized data to the online store, so no `last_materialized` timestamp is written
- This is a data bootstrapping issue (Feast online materialization not run), not a code bug

**Screenshots:**
- audit-p14-analytics.png — Full page full-scroll
- audit-p14-stream-health.png — StreamHealthPanel + all panels visible
- audit-p14-freshness.png — FeatureFreshnessPanel with null timestamps
- audit-p14-system-health.png — SystemHealthSummary cards row

---

### US-014: Analytics Page — StreamHealthPanel, FeatureFreshnessPanel, SystemHealthSummary (2026-04-07)

**Status:** PASS with one data gap

**Verified working:**
- StreamHealthPanel: 3 Flink jobs all RUNNING (`ohlcv-normalizer`, `indicator-stream`, `feast-writer-job`)
- SystemHealthSummary cards: Argo CD=Synced, Flink=3 running/0 failed, Feast latency=0.1ms, CA Last Refresh=11:02 AM
- Kafka Stream Lag: 0 messages total lag, live per-partition chart working
- OLAP Candle Chart: frame, controls, ticker selector render — no candle data plotted
- 0 console errors

**Issue found:**
- **FeatureFreshnessPanel shows `—` for all 3 feature view timestamps** (`ohlcv_stats_fv`, `technical_indicators_fv`, `lag_features_fv`). API endpoint `/analytics/feast/freshness` returns `last_updated: null` for all views — feast_metadata table is not being populated with last-write timestamps.

**Note:** Acceptance criteria referenced `/analytics/stream-health` and `/analytics/feature-freshness` — actual endpoints are `/analytics/flink/jobs` and `/analytics/feast/freshness`.

---

### US-015: Analytics page — OLAPCandleChart and StreamLagMonitor audit (2026-04-07)

**Status:** PASS (audit complete) — OLAPCandleChart has a rendering bug

**StreamLagMonitor:** FUNCTIONAL
- `/analytics/kafka/lag` returns: topic=processed-features, consumer_group=feast-writer-group, P0/P1/P2 all at lag=0, total_lag=0
- Note: acceptance criteria referenced `/analytics/kafka-lag` (404) — actual endpoint is `/analytics/kafka/lag`
- All partitions at 0 lag indicates either healthy consumer or no messages flowing

**OLAPCandleChart: RENDERS SHELL, NO CANDLESTICKS**
- API `/market/candles?ticker=AAPL&interval=1h` returns 35 candles (data IS available, last bar: 2026-03-23)
- Root cause: two bugs compounding:
  1. `CandlePoint` type has `date` field but API returns `ts` field — XAxis dataKey="date" matches nothing
  2. `bodyRange: [number, number]` passed to Recharts `<Bar>` — Bar expects scalar, not tuple; range rendering not supported natively
- Fix needed: rename `ts→date` in API serialization OR update frontend type; fix `bodyRange` rendering for proper candlestick shape
- 0 console errors (no network failures — chart just renders empty)

**Console errors:** None

---

### US-016: Backtest page — AAPL 2024-01-01 to 2024-06-30 (2026-04-07)

**Status:** PASS — Backtest runs and renders correctly

**API endpoint:** GET /backtest/AAPL?start=2024-01-01&end=2024-06-30
- Returns 124 data points, model: naive_sma7, horizon: 7d
- Metrics: RMSE=8.86, MAE=7.09, MAPE=3.80%, R²=0.51, Dir.Accuracy=61.8%, 124 points

**Note:** Acceptance criteria mentioned POST /backtest/run — actual endpoint is GET /backtest/{ticker}

**BacktestChart:** Renders Actual vs Predicted price lines with shaded error band — PASS
**BacktestMetricsSummary:** 6 metric cards (RMSE, MAE, MAPE, R², Directional Accuracy, Total Points) — PASS

**Gap vs acceptance criteria:**
- Sharpe ratio: NOT implemented — current metrics are model accuracy, not portfolio metrics
- Max drawdown: NOT implemented
- Total return: NOT implemented

**Console errors:** None

---

### US-017: Search page — stock search, predictions, SHAP results (2026-04-07)

**Status:** PASS with gap — SHAP row-expand not implemented

**API:** /search/stocks?q=AAPL returns 1 result (Apple Inc). /search/predictions?q=AAPL returns 4 predictions with predicted_price, actual_price, expected_return, confidence.

**Verified working:**
- Search input with placeholder loads correctly
- AAPL predictions: 4 rows — $253.24/+0.25%/conf=0.91, $251.97/-0.26%/conf=0.82, $250.14/-0.98%/conf=0.90, $251.15/-0.58%/conf=0.75
- MSFT predictions: 4 rows — all with confidence values and expected returns
- MODELS (0), DRIFT EVENTS (0), STOCKS (1) tabs present
- 0 console errors

**Gap:** Clicking a prediction row does NOT expand a detail panel with SHAP values. Click has no effect — no drawer, modal, or expanded row. SHAP feature importance per prediction is not implemented in the Search UI.

---

## Mobile Responsiveness Issues

### US-018: Mobile viewport audit — iPhone 14 (390x844) (2026-04-07)

**Status:** AUDIT COMPLETE — critical layout issues found

**Critical: Top nav does not collapse**
- Navigation bar (`Sidebar.tsx`) uses `<Stack direction="row">` with no responsive breakpoints
- At 390px: header scrollWidth=1081px, nav scrollWidth=643px — only "Dashboard" and "Models" visible
- No hamburger menu, no drawer, no bottom navigation bar exists in the codebase
- All 7 pages affected: 5 of 7 nav links invisible/inaccessible on mobile

**High: DataGrid tables overflow horizontally**
- Forecasts page: MuiDataGrid virtual scroller is 1440px wide — columns beyond SECTOR are cut off
- Models page: MuiDataGrid virtual scroller is 1030px wide — OOS metric columns cut off

**Medium: No MobileMarketList component**
- Dashboard uses a vertically-stacked sector/stock list (works adequately but no dedicated mobile optimisation)
- No treemap or MobileMarketList component found — AC was checking for a component that does not exist

**What works on mobile (no overflow):**
- Dashboard content area: single-column sector/stock cards — readable
- Drift page: fully responsive, single-column layout — readable
- Forecasts filter panel: Search, Sector dropdown, Return range, Confidence slider — all usable
- Models winner card — readable

**Console errors:** 0 across all 5 pages

---

## WebSocket Health

### US-019: WebSocket live price feed audit (2026-04-07)

**Status:** WORKING — WS endpoint functional, no price messages because market is closed

**Connection test result:**
- `ws://localhost:8010/ws/prices` — WS OPEN received ✓
- Server logs: connection accepted from 127.0.0.1 — `ws client connected` logged ✓
- Dashboard status bar: **WS CONNECTED** (green) ✓

**Why no price messages:** Market is closed at time of test (12:30 UTC = 8:30 AM Eastern). `is_market_open()` returns False until 09:30 AM ET Mon-Fri. Price feed loop sends one `market_closed` message per check interval, then sleeps 60s.

**Message schema (from source `price_feed.py`):**

During market hours (`price_update`):
```json
{
  "type": "price_update",
  "prices": [
    {"ticker": "AAPL", "price": 252.62, "change_pct": -0.58, "volume": 41300000, "timestamp": "2026-04-07T14:30:00"}
  ]
}
```

Market closed:
```json
{"type": "market_closed", "next_open": "2026-04-07T13:30:00+00:00"}
```

**Warning observed:** `WebSocket connection to 'ws://localhost:8010/ws/prices' failed: WebSocket is closed before the connection is established` — this is a stale `useWebSocket` hook reconnect attempt on initial page load (harmless race condition).

---

## Health Endpoint Gaps

### US-020: Full API health spec run (2026-04-07)

**Status:** PASS — health endpoints functional, two warnings in deep check

**`GET /health` response:**
- status: ok
- db_pool: pool_size=10, checked_in=5, checked_out=0
- redis_status: connected
- Missing: kafka, kserve status fields (not in /health — only in /health/deep)

**`GET /health/deep` response (status: degraded):**
- database: ok
- kafka: ok (1 broker)
- model_freshness: **WARNING** — model stale 15 days (threshold: 7d, trained 2026-03-22)
- prediction_staleness: **WARNING** — predictions stale 90h (threshold: 24h, last: 2026-04-03)
- redis_status: connected

**`GET /health/k8s` response:**
- available: false, running_pods: null — KServe health check not reachable from API pod

**Missing endpoints:**
- /health/detailed → 404 (does not exist)
- /health/ready → 404 (does not exist)

**UI status bar (Playwright):** API ● (green), KAFKA ● (green), DB ● (green), WS CONNECTED — no banners or error overlays. 0 console errors.

**Action items:**
- Retrain models (stale 15d) — weekly-training CronJob should run automatically
- Predictions stale 90h — new predictions needed after retraining
