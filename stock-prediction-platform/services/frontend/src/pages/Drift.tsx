import { useMemo } from "react";
import {
  Alert,
  Box,
  CircularProgress,
  Container,
  LinearProgress,
  Paper,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid";
import { ErrorFallback } from "@/components/ui";
import {
  ActiveModelCard,
  DriftTimeline,
  RollingPerformanceChart,
  RetrainStatusPanel,
  FeatureDistributionChart,
} from "@/components/drift";
import { useModelDrift, useModelComparison, useRollingPerformance, useRetrainStatus } from "@/api";
import type { ActiveModelInfo, RetrainStatus } from "@/api";
import { generateMockDriftData } from "@/utils/mockDriftData";

export default function Drift() {
  const driftQuery = useModelDrift();
  const modelsQuery = useModelComparison();
  const rollingPerfQuery = useRollingPerformance();
  const retrainQuery = useRetrainStatus();

  const mockData = useMemo(() => generateMockDriftData(), []);

  const activeModel: ActiveModelInfo | null = useMemo(() => {
    const active = modelsQuery.data?.models.find((m) => m.is_active);
    if (!active) return modelsQuery.isError ? mockData.activeModel : null;
    return {
      modelName: active.model_name,
      scalerVariant: active.scaler_variant,
      version: active.version ?? 1,
      trainedDate: active.saved_at ?? "",
      isActive: true,
      oosRmse: (active.oos_metrics?.rmse as number) ?? null,
      oosMae: (active.oos_metrics?.mae as number) ?? null,
      oosDirectionalAccuracy: (active.oos_metrics?.directional_accuracy as number) ?? null,
    };
  }, [modelsQuery.data, modelsQuery.isError, mockData]);

  const events = driftQuery.data?.events
    ?? (driftQuery.isError ? mockData.events : []);

  const rollingPerformance = useMemo(() => {
    if (rollingPerfQuery.data?.entries?.length) {
      return rollingPerfQuery.data.entries.map((e) => ({
        date: e.date,
        rmse: e.rmse,
        mae: e.mae,
        directionalAccuracy: e.directional_accuracy,
      }));
    }
    if (rollingPerfQuery.isError) return mockData.rollingPerformance;
    return [];
  }, [rollingPerfQuery.data, rollingPerfQuery.isError, mockData]);

  const retrainStatus = useMemo<RetrainStatus>(() => {
    if (retrainQuery.data?.model_name) {
      const d = retrainQuery.data;
      return {
        lastRetrainDate: d.trained_at,
        isRetraining: false,
        oldModel: d.previous_model
          ? { name: d.previous_model, rmse: 0, mae: 0 }
          : null,
        newModel: d.model_name
          ? {
              name: d.model_name,
              rmse: (d.oos_metrics?.oos_rmse as number) ?? 0,
              mae: (d.oos_metrics?.oos_mae as number) ?? 0,
            }
          : null,
        improvementPct: null,
      };
    }
    if (retrainQuery.isError) return mockData.retrainStatus;
    return mockData.retrainStatus;
  }, [retrainQuery.data, retrainQuery.isError, mockData]);

  const featureDistributions = mockData.featureDistributions;

  const isAllLoading = driftQuery.isLoading && modelsQuery.isLoading
    && rollingPerfQuery.isLoading && retrainQuery.isLoading;

  if (isAllLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (driftQuery.isError && !driftQuery.data) {
    return (
      <ErrorFallback
        message="Failed to load drift data"
        onRetry={() => driftQuery.refetch()}
      />
    );
  }

  // Check for high-severity events in the last 7 days
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const hasHighSeverity = events.some(
    (e) =>
      e.severity === "high" &&
      e.timestamp &&
      new Date(e.timestamp) >= sevenDaysAgo,
  );

  const isAnyLoading = driftQuery.isLoading || modelsQuery.isLoading
    || rollingPerfQuery.isLoading || retrainQuery.isLoading;

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {isAnyLoading && (
        <LinearProgress sx={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 9999 }} />
      )}

      <Typography variant="h4" sx={{ mb: 3 }}>
        Drift Monitoring
      </Typography>

      {hasHighSeverity && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          High severity drift events detected in the last 7 days. Consider retraining the model.
        </Alert>
      )}

      {/* Row 1: Active Model + Retrain Status */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, lg: 6 }}>
          <ActiveModelCard model={activeModel} />
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          <RetrainStatusPanel status={retrainStatus} />
        </Grid>
      </Grid>

      {/* Row 2: Rolling Performance Chart */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Rolling Model Performance
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          30-day rolling RMSE, MAE, and Directional Accuracy
        </Typography>
        <RollingPerformanceChart data={rollingPerformance} />
      </Paper>

      {/* Row 3: Drift Timeline */}
      <Box sx={{ mb: 3 }}>
        <DriftTimeline events={events} />
      </Box>

      {/* Row 4: Feature Distributions (collapsible accordion) */}
      <FeatureDistributionChart distributions={featureDistributions} />
    </Container>
  );
}
