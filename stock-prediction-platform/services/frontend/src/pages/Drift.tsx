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
import { useModelDrift, useModelComparison } from "@/api";
import type { ActiveModelInfo } from "@/api";
import { generateMockDriftData } from "@/utils/mockDriftData";

export default function Drift() {
  const driftQuery = useModelDrift();
  const modelsQuery = useModelComparison();

  const mockData = useMemo(() => generateMockDriftData(), []);

  const activeModel: ActiveModelInfo | null = useMemo(() => {
    const active = modelsQuery.data?.models.find((m) => m.is_active);
    if (!active) return mockData.activeModel;
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
  }, [modelsQuery.data, mockData]);

  const events = driftQuery.data?.events ?? mockData.events;
  const rollingPerformance = mockData.rollingPerformance;
  const retrainStatus = mockData.retrainStatus;
  const featureDistributions = mockData.featureDistributions;

  if (driftQuery.isLoading && modelsQuery.isLoading) return <LoadingSpinner />;
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
