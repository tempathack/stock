import type { ModelComparisonEntry } from "@/api";

interface ModelDetailPanelProps {
  model: ModelComparisonEntry;
}

function fmt(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(decimals) : "—";
}

function stabilityColor(val: number | null): string {
  if (val === null) return "text-text-secondary";
  if (val < 0.01) return "text-profit";
  if (val < 0.05) return "text-warning";
  return "text-loss";
}

function metricColor(key: string, value: number): string {
  if (key === "r2" || key === "directional_accuracy") {
    return value > 0.8 ? "text-profit" : value > 0.5 ? "text-warning" : "text-loss";
  }
  // Lower is better for RMSE, MAE, MAPE
  return "text-text-primary";
}

export default function ModelDetailPanel({ model }: ModelDetailPanelProps) {
  const params = model.best_params ?? {};
  const metrics = model.oos_metrics ?? {};

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h3 className="text-lg font-bold text-text-primary">{model.model_name}</h3>
        {model.version != null && (
          <span className="rounded bg-bg-card px-2 py-0.5 text-xs font-medium text-text-secondary">
            v{model.version}
          </span>
        )}
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            model.is_active ? "bg-profit" : "bg-text-secondary/40"
          }`}
        />
        <span className="text-xs text-text-secondary">{model.is_active ? "Active" : "Inactive"}</span>
      </div>

      {/* Metadata grid */}
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <span className="text-xs text-text-secondary">Scaler</span>
          <p className="font-medium capitalize text-text-primary">{model.scaler_variant}</p>
        </div>
        <div>
          <span className="text-xs text-text-secondary">Saved At</span>
          <p className="font-medium text-text-primary">
            {model.saved_at ? new Date(model.saved_at).toLocaleString() : "—"}
          </p>
        </div>
        <div>
          <span className="text-xs text-text-secondary">Fold Stability</span>
          <p className={`font-mono font-medium ${stabilityColor(model.fold_stability)}`}>
            {fmt(model.fold_stability, 4)}
          </p>
        </div>
      </div>

      {/* Hyperparameters */}
      {Object.keys(params).length > 0 && (
        <div className="mt-4">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-secondary">Hyperparameters</h4>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-3 lg:grid-cols-4">
            {Object.entries(params).map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs text-text-secondary">{key}</dt>
                <dd className="font-mono text-sm text-text-primary">
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* OOS Metrics */}
      {Object.keys(metrics).length > 0 && (
        <div className="mt-4">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-secondary">OOS Metrics</h4>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-3 lg:grid-cols-5">
            {Object.entries(metrics).map(([key, value]) => {
              const n = Number(value);
              return (
                <div key={key}>
                  <span className="text-xs text-text-secondary">{key}</span>
                  <p className={`font-mono text-sm font-medium ${Number.isFinite(n) ? metricColor(key, n) : "text-text-secondary"}`}>
                    {fmt(value, 4)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
