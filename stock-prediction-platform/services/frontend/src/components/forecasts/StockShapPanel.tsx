import { ShapBarChart } from "@/components/charts";
import { generateMockShapImportance } from "@/utils/mockModelData";
import { Box, Paper, Typography } from "@mui/material";

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
      <Paper sx={{ p: 2, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          SHAP analysis not available for this stock.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="subtitle2">Feature Contribution — {ticker}</Typography>
        <Typography variant="caption" color="text.secondary">
          Model: {modelName}
        </Typography>
      </Box>

      <ShapBarChart
        data={importance}
        title={`SHAP Feature Importance for ${ticker}`}
      />

      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1.5 }}>
        Features driving the 7-day prediction. Higher bars indicate stronger influence on the
        forecast.
      </Typography>
    </Paper>
  );
}
