import { useState, useMemo, useEffect } from "react";
import { PageHeader } from "@/components/layout";
import { LoadingSpinner, ErrorFallback, ExportButtons } from "@/components/ui";
import { ModelComparisonTable, WinnerCard, ModelDetailPanel } from "@/components/tables";
import { ShapBarChart, ShapBeeswarmPlot, FoldPerformanceChart } from "@/components/charts";
import { useModelComparison } from "@/api";
import type { ModelComparisonEntry } from "@/api";
import { generateModelDetail } from "@/utils/mockModelData";
import { exportToCsv } from "@/utils/exportCsv";
import { exportTableToPdf } from "@/utils/exportPdf";

export default function Models() {
  const { data, isLoading, isError, refetch } = useModelComparison();
  const [selectedModel, setSelectedModel] = useState<ModelComparisonEntry | null>(null);

  // Default to winner on first load
  useEffect(() => {
    if (data?.winner && !selectedModel) {
      setSelectedModel(data.winner);
    }
  }, [data, selectedModel]);

  const detail = useMemo(
    () => (selectedModel ? generateModelDetail(selectedModel.model_name) : null),
    [selectedModel],
  );

  if (isLoading) return <LoadingSpinner />;
  if (isError) return <ErrorFallback message="Failed to load model data" onRetry={refetch} />;

  if (!data?.models.length) {
    return (
      <>
        <PageHeader
          title="Model Comparison"
          subtitle="Compare ML model performance across evaluation metrics"
        />
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-bg-surface p-16">
          <p className="text-lg text-text-secondary">No models trained yet</p>
          <p className="mt-2 text-sm text-text-secondary">
            Run the training pipeline to see model comparison data.
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Model Comparison"
        subtitle="Compare ML model performance across evaluation metrics"
      />

      <div className="mb-4 flex justify-end">
        <ExportButtons
          disabled={!data?.models.length}
          onExportCsv={() => {
            const today = new Date().toISOString().slice(0, 10);
            const headers = ["Model Name", "Scaler", "OOS RMSE", "OOS MAE", "OOS R²", "OOS MAPE", "Dir. Accuracy", "Fold Stability", "Winner", "Active"];
            const rows = data.models.map((m) => [
              m.model_name,
              m.scaler_variant,
              String(m.oos_metrics.rmse ?? ""),
              String(m.oos_metrics.mae ?? ""),
              String(m.oos_metrics.r2 ?? ""),
              String(m.oos_metrics.mape ?? ""),
              String(m.oos_metrics.directional_accuracy ?? ""),
              String(m.fold_stability ?? ""),
              m.is_winner ? "Yes" : "No",
              m.is_active ? "Yes" : "No",
            ]);
            exportToCsv(`models_comparison_${today}.csv`, headers, rows);
          }}
          onExportPdf={() => {
            const today = new Date().toISOString().slice(0, 10);
            const headers = ["Model Name", "Scaler", "OOS RMSE", "OOS MAE", "OOS R²", "OOS MAPE", "Dir. Accuracy", "Fold Stability", "Winner", "Active"];
            const rows = data.models.map((m) => [
              m.model_name,
              m.scaler_variant,
              String(m.oos_metrics.rmse ?? ""),
              String(m.oos_metrics.mae ?? ""),
              String(m.oos_metrics.r2 ?? ""),
              String(m.oos_metrics.mape ?? ""),
              String(m.oos_metrics.directional_accuracy ?? ""),
              String(m.fold_stability ?? ""),
              m.is_winner ? "Yes" : "No",
              m.is_active ? "Yes" : "No",
            ]);
            exportTableToPdf(
              `models_comparison_${today}.pdf`,
              "Model Comparison Report",
              headers,
              rows,
              [
                `Winner: ${data.winner?.model_name ?? "N/A"}`,
                `Total Models: ${data.models.length}`,
                `Generated: ${today}`,
              ],
            );
          }}
        />
      </div>

      {/* Winner Card */}
      <WinnerCard winner={data.winner ?? null} />

      {/* Model Comparison Table */}
      <div className="mt-6">
        <ModelComparisonTable models={data.models} onSelectModel={setSelectedModel} />
      </div>

      {/* Model Detail Panel */}
      {selectedModel && (
        <div className="mt-6">
          <ModelDetailPanel model={selectedModel} />
        </div>
      )}

      {/* Charts Section */}
      {selectedModel && detail ? (
        <section className="mt-8 space-y-6">
          <h2 className="text-lg font-semibold text-text-primary">
            Detailed Analysis — {selectedModel.model_name}
          </h2>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <ShapBarChart data={detail.shap_importance} />
            <ShapBeeswarmPlot data={detail.shap_beeswarm} />
          </div>
          <FoldPerformanceChart data={detail.fold_metrics} modelName={selectedModel.model_name} />
        </section>
      ) : (
        <div className="mt-8 rounded-lg border border-dashed border-border bg-bg-surface p-8 text-center text-text-secondary">
          Click a model row to see detailed analysis
        </div>
      )}
    </>
  );
}
