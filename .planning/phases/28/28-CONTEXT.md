# Phase 28 — Frontend /dashboard Page

## What This Phase Delivers

A fully functional `/dashboard` page replacing the four placeholder cards with:

1. **S&P 500 interactive treemap** — market-cap-sized cells with daily performance colour gradient (green/red)
2. **Treemap cell click → stock detail** — selecting a tile opens the detail panel for that ticker
3. **Intraday candlestick chart** — minute-level OHLC for the selected stock
4. **Historical OHLCV chart** — adjustable timeframe selector (1D / 1W / 1M / 3M / 1Y)
5. **Technical analysis panel** — RSI, MACD, Bollinger Bands, MAs, Volume, VWAP sub-charts
6. **Key metric cards** — current price, market cap, volume, daily change, sector, 52-week range
7. **Responsive layout** — mobile-first grid that stacks on small viewports
8. **Near-real-time updates** — polling-based refresh of market overview data

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| FDASH-01 | S&P 500 treemap renders with market cap sizing and daily performance colour gradient | `MarketTreemap` component |
| FDASH-02 | Clicking a treemap cell opens stock detail view | Treemap `onCellClick` → `selectedTicker` state |
| FDASH-03 | Intraday minute-level candlestick chart renders for selected stock | `CandlestickChart` component |
| FDASH-04 | Historical OHLCV chart renders with adjustable timeframe selector | `HistoricalChart` + `TimeframeSelector` |
| FDASH-05 | TA panel (RSI, MACD, Bollinger Bands, MAs, Volume, VWAP) renders correctly | `DashboardTAPanel` (reuses indicator logic from Phase 27) |
| FDASH-06 | Key metric cards display on dashboard | `MetricCards` grid |
| FDASH-07 | Dashboard layout responsive and optimised | Tailwind responsive grid |
| FDASH-08 | Market state updates in real-time or near-real-time | `useMarketOverview` with 30 s `refetchInterval` |

## Data Sources

### GET /market/overview → `MarketOverviewResponse`

```typescript
interface MarketOverviewEntry {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  market_cap: number | null;
  last_close: number | null;
  daily_change_pct: number | null;
}

interface MarketOverviewResponse {
  stocks: MarketOverviewEntry[];
  count: number;
}
```

Provides treemap cell data: size by `market_cap`, colour by `daily_change_pct`.

### GET /market/indicators/{ticker} → `TickerIndicatorsResponse`

```typescript
interface IndicatorValues {
  date: string | null;
  close: number | null;
  rsi_14: number | null;
  macd_line: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  ema_12: number | null;
  ema_26: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
  atr: number | null;
  rolling_volatility_21: number | null;
  obv: number | null;
  vwap: number | null;
  volume_sma_20: number | null;
  // + return fields
}

interface TickerIndicatorsResponse {
  ticker: string;
  latest: IndicatorValues | null;
  series: IndicatorValues[];
  count: number;
}
```

Provides historical indicators (90 days) for the selected ticker's detail view.

### GET /predict/{ticker} → `PredictionResponse`

```typescript
interface PredictionResponse {
  ticker: string;
  prediction_date: string;
  predicted_date: string;
  predicted_price: number;
  model_name: string;
  confidence: number | null;
}
```

Provides 7-day prediction overlay for the selected stock's historical chart.

## Existing Reusable Assets

| Asset | Location | Reuse |
|-------|----------|-------|
| `useMarketOverview()` | `src/api/queries.ts` | Treemap data, metric cards |
| `useTickerIndicators(ticker)` | `src/api/queries.ts` | TA panel, historical chart |
| `usePrediction(ticker)` | `src/api/queries.ts` | Forecast overlay |
| `IndicatorOverlayCharts` | `src/components/forecasts/` | Reference for RSI / MACD / BB sub-charts |
| `StockDetailChart` | `src/components/forecasts/` | Reference for composed price chart |
| `generateMockIndicatorSeries()` | `src/utils/mockIndicatorData.ts` | Mock fallback for indicator data |
| `generateMockForecasts()` | `src/utils/mockForecastData.ts` | Mock fallback for treemap data |
| Dark theme tokens | Tailwind CSS | `bg-primary`, `bg-surface`, `bg-card`, `text-primary`, `accent`, `profit`, `loss` |
| `PageHeader`, `LoadingSpinner`, `ErrorFallback` | `src/components/ui/`, `src/components/layout/` | Page furniture |

## Plan Split

| Plan | Scope | Requirements |
|------|-------|-------------|
| **28-01** | Treemap types, mock data, `MarketTreemap` component, `MetricCards`, initial dashboard wiring | FDASH-01, FDASH-02, FDASH-06, FDASH-08 |
| **28-02** | `CandlestickChart`, `HistoricalChart` + `TimeframeSelector`, mock OHLCV data | FDASH-03, FDASH-04 |
| **28-03** | `DashboardTAPanel`, responsive polish, real-time polling, final build verification | FDASH-05, FDASH-07, FDASH-08 |
