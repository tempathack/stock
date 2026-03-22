# Phase 27 — Frontend /forecasts Page

## What This Phase Delivers

A fully functional `/forecasts` page replacing the placeholder card with:

1. **Forecast table for all S&P 500 stocks** — current price, predicted price, expected return %, confidence, trend indicator
2. **Multi-dimensional filters** — by sector, expected return range, confidence level
3. **Multi-stock comparison view** — select multiple stocks and view them side-by-side
4. **Per-stock detail view** — historical + 7-day forecast time series chart
5. **Technical indicators overlay** — RSI, MACD, Bollinger Bands on the detail chart
6. **SHAP explanation panel** — per-stock feature importance from the winning model

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| FFOR-01 | Forecast table for all S&P 500 stocks (current price, predicted price, expected return %, confidence, trend indicator) | `ForecastTable` component with sortable columns |
| FFOR-02 | Filter by sector, expected return range, confidence level | `ForecastFilters` component with dropdowns + range sliders |
| FFOR-03 | Multi-stock comparison view (select multiple side by side) | `StockComparisonPanel` with multi-select + side-by-side cards |
| FFOR-04 | Per-stock detail view with historical + forecast time series chart | `StockDetailChart` component (line chart with forecast overlay) |
| FFOR-05 | Technical indicators overlay (RSI, MACD, Bollinger Bands) on stock detail chart | `IndicatorOverlayCharts` — sub-charts below the main price chart |
| FFOR-06 | SHAP explanation panel per stock | `StockShapPanel` — horizontal bar chart of feature contributions |

## Data Sources

### GET /predict/bulk → `BulkPredictionResponse`

```typescript
interface PredictionResponse {
  ticker: string;
  prediction_date: string;
  predicted_date: string;
  predicted_price: number;
  model_name: string;
  confidence: number | null;
}

interface BulkPredictionResponse {
  predictions: PredictionResponse[];
  model_name: string | null;
  generated_at: string | null;
  count: number;
}
```

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
  // ... plus return fields
}

interface TickerIndicatorsResponse {
  ticker: string;
  latest: IndicatorValues | null;
  series: IndicatorValues[];
  count: number;
}
```

### Data Joining Strategy

The forecasts page requires joining two API responses:

1. **`/predict/bulk`** — provides predictions (ticker, predicted_price, confidence, model_name)
2. **`/market/overview`** — provides current market data (ticker, company_name, sector, last_close, daily_change_pct, market_cap)

These are joined client-side by `ticker` to produce the enriched forecast row:

```typescript
interface ForecastRow {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  current_price: number | null;       // from market/overview.last_close
  predicted_price: number;             // from predict/bulk
  expected_return_pct: number;         // computed: (predicted - current) / current * 100
  confidence: number | null;           // from predict/bulk
  daily_change_pct: number | null;     // from market/overview
  trend: "bullish" | "bearish" | "neutral"; // derived from expected_return_pct
  model_name: string;
  prediction_date: string;
  predicted_date: string;
}
```

### Per-Stock Detail Data

When a user selects a stock for detail view, the page fetches:
- **`/market/indicators/{ticker}`** — full time series of OHLCV + technical indicators
- **`/predict/{ticker}`** — individual prediction (for the forecast point overlay on the chart)

### SHAP Data

Similar to Phase 26, per-stock SHAP data is not yet exposed via a dedicated endpoint. For Phase 27, the `StockShapPanel` uses mock data shaped per the SHAP analysis module output. The mock generator from Phase 26 (`generateMockShapImportance`) is reused with ticker-based seeding.

## Existing Infrastructure (from Phases 25–26)

| Asset | Path | Status |
|-------|------|--------|
| Forecasts page skeleton | `src/pages/Forecasts.tsx` | Exists — placeholder, will be replaced |
| Bulk predictions hook | `src/api/queries.ts` → `useBulkPredictions()` | Ready to use |
| Single prediction hook | `src/api/queries.ts` → `usePrediction(ticker)` | Ready to use |
| Market overview hook | `src/api/queries.ts` → `useMarketOverview()` | Ready to use |
| Indicator series hook | `src/api/queries.ts` → `useTickerIndicators(ticker)` | Ready to use |
| API types | `src/api/types.ts` → all relevant interfaces | Ready to use |
| UI components | `src/components/ui/` → LoadingSpinner, ErrorFallback, PlaceholderCard | Reusable |
| Layout | `src/components/layout/` → PageHeader | Reusable |
| Charts dir | `src/components/charts/` → ShapBarChart, ShapBeeswarmPlot, FoldPerformanceChart | Reusable ShapBarChart for SHAP panel |
| Mock data | `src/utils/mockModelData.ts` → generateMockShapImportance | Reusable for per-stock SHAP |
| Recharts | Installed in Phase 26 | Available |
| Tailwind dark theme | `src/styles/globals.css` | Available |

## Component Architecture

```
Forecasts.tsx (page)
├── ForecastFilters          (sector dropdown, return range, confidence slider)
├── ForecastTable            (sortable rows, row click → detail, checkbox select → compare)
├── StockComparisonPanel     (side-by-side cards for selected stocks)
└── StockDetailModal/Panel
    ├── StockDetailChart      (historical + forecast line chart)
    ├── IndicatorOverlayCharts (RSI sub-chart, MACD sub-chart, Bollinger bands on main chart)
    └── StockShapPanel        (horizontal bar chart of SHAP feature importance)
```

## Mock Data Strategy

For development, a `mockForecastData.ts` utility generates realistic forecast rows for ~20 dev tickers, matching the actual data shape. This allows full UI development and testing without a live API. The mock includes:
- Sector distribution (Technology, Healthcare, Finance, Energy, etc.)
- Realistic price ranges and expected returns (-5% to +8%)
- Varied confidence levels (0.5–0.95)
- Trend derivation (bullish > +1%, bearish < -1%, neutral otherwise)

When the API is live, the mock is replaced by the joined `useBulkPredictions()` + `useMarketOverview()` data.

## Plan Breakdown

| Plan | Scope | Requirements |
|------|-------|--------------|
| 27-01 | Forecast types, mock data, ForecastTable + ForecastFilters, basic page wiring | FFOR-01, FFOR-02 |
| 27-02 | StockComparisonPanel + StockDetailChart + IndicatorOverlayCharts | FFOR-03, FFOR-04, FFOR-05 |
| 27-03 | StockShapPanel, responsive polish, edge cases, build verification | FFOR-06 + polish |
