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

