import type { ActiveModelInfo } from "@/api";

interface ActiveModelCardProps {
  model: ActiveModelInfo | null;
}

function fmt(value: number | null, decimals: number): string {
  return value != null && Number.isFinite(value) ? value.toFixed(decimals) : "—";
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function ActiveModelCard({ model }: ActiveModelCardProps) {
  if (!model) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-bg-surface p-6 text-center text-text-secondary">
        No active model detected
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        {/* Left — title + meta */}
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-text-primary">{model.modelName}</h3>
            {model.isActive && (
              <span className="inline-block rounded-full bg-profit/20 px-2 py-0.5 text-xs font-semibold uppercase text-profit">
                Active
              </span>
            )}
          </div>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-secondary">
            <span>Scaler: <span className="capitalize text-text-primary">{model.scalerVariant}</span></span>
            <span>Version: <span className="text-text-primary">v{model.version}</span></span>
            <span>Trained: <span className="text-text-primary">{fmtDate(model.trainedDate)}</span></span>
          </div>
        </div>

        {/* Right — metric pills */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="rounded-lg bg-bg-card px-3 py-2">
            <p className="text-xs text-text-secondary">RMSE</p>
            <p className="font-mono text-sm font-medium text-text-primary">{fmt(model.oosRmse, 4)}</p>
          </div>
          <div className="rounded-lg bg-bg-card px-3 py-2">
            <p className="text-xs text-text-secondary">MAE</p>
            <p className="font-mono text-sm font-medium text-text-primary">{fmt(model.oosMae, 4)}</p>
          </div>
          <div className="rounded-lg bg-bg-card px-3 py-2">
            <p className="text-xs text-text-secondary">Dir. Acc</p>
            <p className="font-mono text-sm font-medium text-text-primary">
              {model.oosDirectionalAccuracy != null
                ? `${(model.oosDirectionalAccuracy * 100).toFixed(1)}%`
                : "—"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
