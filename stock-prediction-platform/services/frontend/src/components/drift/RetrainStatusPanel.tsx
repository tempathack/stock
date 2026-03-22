import type { RetrainStatus } from "@/api";

interface RetrainStatusPanelProps {
  status: RetrainStatus;
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZoneName: "short",
  });
}

export default function RetrainStatusPanel({ status }: RetrainStatusPanelProps) {
  const hasComparison = status.oldModel && status.newModel;

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-5">
      {/* Header with status badge */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Retraining Status</h3>
        {status.isRetraining ? (
          <span className="animate-pulse rounded-full bg-warning/20 px-2.5 py-0.5 text-xs font-semibold text-warning">
            Retraining…
          </span>
        ) : status.lastRetrainDate ? (
          <span className="rounded-full bg-profit/20 px-2.5 py-0.5 text-xs font-semibold text-profit">
            Up to Date
          </span>
        ) : (
          <span className="rounded-full bg-gray-500/20 px-2.5 py-0.5 text-xs font-semibold text-gray-400">
            Never Retrained
          </span>
        )}
      </div>

      {/* Last retrain date */}
      <p className="mt-3 text-xs text-text-secondary">
        {status.lastRetrainDate
          ? `Last retrained: ${fmtDate(status.lastRetrainDate)}`
          : "Never retrained"}
      </p>

      {/* Retraining in progress message */}
      {status.isRetraining && (
        <p className="mt-2 text-xs text-warning/80">Model retraining in progress…</p>
      )}

      {/* Model comparison */}
      {hasComparison ? (
        <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          {/* Old model */}
          <div className="rounded-lg bg-bg-card p-3">
            <p className="text-xs text-text-secondary">Previous Model</p>
            <p className="mt-1 text-sm font-medium text-text-primary">
              {status.oldModel!.name}
            </p>
            <p className="mt-1 font-mono text-lg text-loss">
              {status.oldModel!.rmse.toFixed(4)}
            </p>
            <p className="font-mono text-xs text-text-secondary">
              MAE {status.oldModel!.mae.toFixed(4)}
            </p>
          </div>

          {/* Arrow separator */}
          <span className="text-lg text-text-secondary">→</span>

          {/* New model */}
          <div className="rounded-lg bg-bg-card p-3">
            <p className="text-xs text-text-secondary">Current Model</p>
            <p className="mt-1 text-sm font-medium text-text-primary">
              {status.newModel!.name}
            </p>
            <p className="mt-1 font-mono text-lg text-profit">
              {status.newModel!.rmse.toFixed(4)}
            </p>
            <p className="font-mono text-xs text-text-secondary">
              MAE {status.newModel!.mae.toFixed(4)}
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-lg border border-dashed border-border bg-bg-card p-4 text-center text-sm text-text-secondary">
          No retraining history available
        </div>
      )}

      {/* Improvement metric */}
      {status.improvementPct != null && (
        <div className="mt-4 text-center">
          <p
            className={`text-2xl font-bold ${
              status.improvementPct > 0 ? "text-profit" : "text-loss"
            }`}
          >
            {status.improvementPct > 0 ? "+" : ""}
            {status.improvementPct.toFixed(1)}%
          </p>
          <p className="text-xs text-text-secondary">RMSE Improvement</p>
        </div>
      )}
    </div>
  );
}
