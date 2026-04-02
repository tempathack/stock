import { useMemo } from "react";
import {
  Alert,
  Box,
  Container,
  LinearProgress,
  Paper,
  Skeleton,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid";
import { ErrorFallback } from "@/components/ui";
import { PageHeader } from "@/components/layout";
import {
  ActiveModelCard,
  DriftTimeline,
  RollingPerformanceChart,
  RetrainStatusPanel,
  FeatureDistributionChart,
} from "@/components/drift";
import { useModelDrift, useModelComparison, useRollingPerformance, useRetrainStatus } from "@/api";
import type { ActiveModelInfo, RetrainStatus } from "@/api";

export default function Drift() {
  const driftQuery = useModelDrift();
  const modelsQuery = useModelComparison();
  const rollingPerfQuery = useRollingPerformance();
  const retrainQuery = useRetrainStatus();

  const activeModel: ActiveModelInfo | null = useMemo(() => {
    const active = modelsQuery.data?.models.find((m) => m.is_active);
    if (!active) return null;
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
  }, [modelsQuery.data]);

  const events = driftQuery.data?.events ?? [];

  const rollingPerformance = useMemo(() => {
    if (rollingPerfQuery.data?.entries?.length) {
      return rollingPerfQuery.data.entries.map((e) => ({
        date: e.date,
        rmse: e.rmse,
        mae: e.mae,
        directionalAccuracy: e.directional_accuracy,
      }));
    }
    return [];
  }, [rollingPerfQuery.data]);

  const retrainStatus = useMemo<RetrainStatus>(() => {
    if (retrainQuery.data?.model_name) {
      const d = retrainQuery.data;
      return {
        lastRetrainDate: d.trained_at,
        isRetraining: false,
        oldModel: d.previous_model
          ? {
              name: d.previous_model,
              rmse: (d.previous_oos_metrics?.oos_rmse as number) ?? null,
              mae: (d.previous_oos_metrics?.oos_mae as number) ?? null,
            }
          : null,
        newModel: d.model_name
          ? {
              name: d.model_name,
              rmse: (d.oos_metrics?.oos_rmse as number) ?? null,
              mae: (d.oos_metrics?.oos_mae as number) ?? null,
            }
          : null,
        improvementPct: null,
      };
    }
    return { lastRetrainDate: null, isRetraining: false, oldModel: null, newModel: null, improvementPct: null };
  }, [retrainQuery.data]);

  const isAllLoading = driftQuery.isLoading && modelsQuery.isLoading
    && rollingPerfQuery.isLoading && retrainQuery.isLoading;

  if (isAllLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <PageHeader
          title="Drift Monitoring"
          subtitle="Model drift detection and auto-retrain status"
        />
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, lg: 6 }}>
            <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
          </Grid>
        </Grid>
        <Skeleton variant="rectangular" height={220} sx={{ borderRadius: 1, mb: 3 }} />
        <Skeleton variant="rectangular" height={180} sx={{ borderRadius: 1, mb: 3 }} />
      </Container>
    );
  }

  if (driftQuery.isError && !driftQuery.data) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <PageHeader
          title="Drift Monitoring"
          subtitle="Model drift detection and auto-retrain status"
        />
        <Box sx={{ display: "flex", justifyContent: "center", mt: 6 }}>
          <ErrorFallback
            message="Failed to load drift data"
            onRetry={() => driftQuery.refetch()}
          />
        </Box>
      </Container>
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

      <PageHeader
        title="Drift Monitoring"
        subtitle="Model drift detection and auto-retrain status"
      />

      {hasHighSeverity && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          High severity drift events detected in the last 7 days. Consider retraining the model.
        </Alert>
      )}

      {/* Row 1: Active Model + Retrain Status */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, lg: 6 }}>
          {modelsQuery.isError && !modelsQuery.data ? (
            <ErrorFallback message="Failed to load active model" onRetry={() => modelsQuery.refetch()} />
          ) : (
            <ActiveModelCard model={activeModel} />
          )}
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          {retrainQuery.isError && !retrainQuery.data ? (
            <ErrorFallback message="Failed to load retrain status" onRetry={() => retrainQuery.refetch()} />
          ) : (
            <RetrainStatusPanel status={retrainStatus} />
          )}
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
        {rollingPerfQuery.isError && !rollingPerfQuery.data ? (
          <ErrorFallback message="Failed to load performance data" onRetry={() => rollingPerfQuery.refetch()} />
        ) : (
          <RollingPerformanceChart data={rollingPerformance} />
        )}
      </Paper>

      {/* Row 3: Drift Timeline */}
      <Box sx={{ mb: 3 }}>
        <DriftTimeline events={events} />
      </Box>

      {/* Row 4: Feature Distributions (collapsible accordion) */}
      <FeatureDistributionChart distributions={[]} />
    </Container>
  );
}
