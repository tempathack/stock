import { useMemo } from "react";
import { PageHeader } from "@/components/layout";
import { LoadingSpinner, ErrorFallback } from "@/components/ui";
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
  if (isAllLoading) return <LoadingSpinner />;
  if (driftQuery.isError && !driftQuery.data) {
    return (
      <ErrorFallback
        message="Failed to load drift data"
        onRetry={() => driftQuery.refetch()}
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Drift Monitoring"
        subtitle="Data and model drift detection status"
      />

      {/* Row 1: Active Model + Retrain Status */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ActiveModelCard model={activeModel} />
        <RetrainStatusPanel status={retrainStatus} />
      </div>

      {/* Row 2: Rolling Performance Chart */}
      <div className="mt-6">
        <RollingPerformanceChart data={rollingPerformance} />
      </div>

      {/* Row 3: Drift Timeline */}
      <div className="mt-6">
        <DriftTimeline events={events} />
      </div>

      {/* Row 4: Feature Distributions */}
      <div className="mt-6">
        <FeatureDistributionChart distributions={featureDistributions} />
      </div>
    </>
  );
}
