import { ShapBarChart } from "@/components/charts";
import { generateMockShapImportance } from "@/utils/mockModelData";

interface StockShapPanelProps {
  ticker: string;
  modelName: string;
}

export default function StockShapPanel({
  ticker,
  modelName,
}: StockShapPanelProps) {
  const importance = generateMockShapImportance(ticker);

  if (importance.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-bg-surface p-4 text-center text-sm text-text-secondary">
        SHAP analysis not available for this stock.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-4">
      <div className="mb-3">
        <h3 className="text-sm font-medium text-text-primary">
          Feature Contribution — {ticker}
        </h3>
        <p className="text-xs text-text-secondary">Model: {modelName}</p>
      </div>

      <ShapBarChart
        data={importance}
        title={`SHAP Feature Importance for ${ticker}`}
      />

      <p className="mt-3 text-xs text-text-secondary">
        Features driving the 7-day prediction. Higher bars indicate stronger
        influence on the forecast.
      </p>
    </div>
  );
}
