import { useState, useMemo, useEffect } from "react";
import {
  Box,
  Container,
  Divider,
  Grid,
  Paper,
  Typography,
} from "@mui/material";
import { PageHeader } from "@/components/layout";
import { ErrorFallback, ExportButtons } from "@/components/ui";
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

  if (isLoading) return null;
  if (isError) return <ErrorFallback message="Failed to load model data" onRetry={refetch} />;

  if (!data?.models.length) {
    return (
      <Container maxWidth="xl">
        <PageHeader
          title="Model Comparison"
          subtitle="Compare ML model performance across evaluation metrics"
        />
        <Paper
          sx={{
            p: 8,
            textAlign: "center",
            border: "2px dashed",
            borderColor: "divider",
          }}
        >
          <Typography variant="h6" color="text.secondary">
            No models trained yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Run the training pipeline to see model comparison data.
          </Typography>
        </Paper>
      </Container>
    );
  }

  const today = new Date().toISOString().slice(0, 10);

  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Model Comparison"
        subtitle="Compare ML model performance across evaluation metrics"
      />

      <Box sx={{ mb: 2, display: "flex", justifyContent: "flex-end" }}>
        <ExportButtons
          disabled={!data?.models.length}
          onExportCsv={() => {
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
      </Box>

      {/* Winner Card */}
      <WinnerCard winner={data.winner ?? null} />

      {/* Model Comparison Table */}
      <Box sx={{ mt: 3 }}>
        <ModelComparisonTable models={data.models} onSelectModel={setSelectedModel} />
      </Box>

      {/* Model Detail Panel — two-column in-sample vs out-of-sample */}
      {selectedModel && (
        <Box sx={{ mt: 3 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <ModelDetailPanel model={selectedModel} />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper sx={{ p: 2, height: "100%" }}>
                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                  In-Sample vs Out-of-Sample Metrics
                </Typography>
                <Divider sx={{ mb: 1 }} />
                <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {/* OOS metrics highlighted */}
                  {Object.entries(selectedModel.oos_metrics ?? {}).map(([key, value]) => {
                    const n = Number(value);
                    return (
                      <Box key={key}>
                        <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase" }}>
                          {key}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: "monospace",
                            fontWeight: 600,
                            color:
                              (key === "r2" || key === "directional_accuracy") && Number.isFinite(n)
                                ? n > 0.8 ? "success.main" : n > 0.5 ? "warning.main" : "error.main"
                                : "text.primary",
                          }}
                        >
                          {Number.isFinite(n) ? n.toFixed(4) : "—"}
                        </Typography>
                      </Box>
                    );
                  })}
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Charts Section */}
      {selectedModel && detail ? (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            Detailed Analysis — {selectedModel.model_name}
          </Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, xl: 6 }}>
              <ShapBarChart data={detail.shap_importance} />
            </Grid>
            <Grid size={{ xs: 12, xl: 6 }}>
              <ShapBeeswarmPlot data={detail.shap_beeswarm} />
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <FoldPerformanceChart data={detail.fold_metrics} modelName={selectedModel.model_name} />
          </Box>
        </Box>
      ) : (
        <Paper
          sx={{
            mt: 4,
            p: 4,
            textAlign: "center",
            border: "1px dashed",
            borderColor: "divider",
          }}
        >
          <Typography color="text.secondary">
            Click a model row to see detailed analysis
          </Typography>
        </Paper>
      )}
    </Container>
  );
}
