# System Audit — Improvement Findings

## US-008: SHAP Panel Audit (Forecasts Page)

**Audit Date:** 2026-04-07
**Page:** http://localhost:5173/forecasts

### Findings

#### ✅ ShapBarChart renders (mock data)
- `StockShapPanel.tsx` renders `ShapBarChart` with horizontal bars for top features
- Data source: `generateMockShapImportance(ticker)` — **mock data, not live API data**
- Heading shown: "SHAP Feature Importance for TSLA"
- No console errors or warnings

#### ❌ ShapBeeswarmPlot NOT rendered in StockShapPanel
- `ShapBeeswarmPlot.tsx` exists as a component but is NOT imported or used in `StockShapPanel.tsx`
- The panel only renders `ShapBarChart`
- **Improvement needed:** Add `ShapBeeswarmPlot` to `StockShapPanel` using beeswarm data from API or mock

#### ❌ API does not return `shap_values` or `feature_importance`
- `curl http://localhost:8010/predict/AAPL?horizon=7` returns:
  ```json
  {"ticker":"AAPL","prediction_date":"2026-04-03","predicted_date":"2026-04-10",
   "predicted_price":251.9657,"model_name":"CatBoost_standard","confidence":0.8228,
   "horizon_days":7,"assigned_model_id":7,"feature_freshness_seconds":null}
  ```
- No `shap_values` or `feature_importance` field in prediction response
- **Improvement needed:** Backend should compute and return SHAP values per prediction, or expose a separate `/predict/{ticker}/shap` endpoint

#### ✅ No console errors
- 0 errors, 0 warnings during forecasts page load and TSLA row click
