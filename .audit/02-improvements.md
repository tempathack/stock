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

