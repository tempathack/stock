import type { ModelComparisonEntry } from "@/api";

interface WinnerCardProps {
  winner: ModelComparisonEntry | null;
}

function fmt(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(decimals) : "—";
}

export default function WinnerCard({ winner }: WinnerCardProps) {
  if (!winner) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-bg-surface p-6 text-center text-text-secondary">
        No winner model selected
      </div>
    );
  }

  return (
    <div className="rounded-lg border-l-4 border-accent bg-bg-card p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        {/* Left — title */}
        <div>
          <span className="inline-block rounded bg-accent/20 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-accent">
            🏆 Winner
          </span>
          <h3 className="mt-1 text-xl font-bold text-accent">{winner.model_name}</h3>
        </div>

        {/* Right — key metrics */}
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <div>
            <span className="text-text-secondary">OOS RMSE</span>
            <p className="font-mono font-medium text-text-primary">{fmt(winner.oos_metrics.rmse, 6)}</p>
          </div>
          <div>
            <span className="text-text-secondary">OOS R²</span>
            <p className="font-mono font-medium text-text-primary">{fmt(winner.oos_metrics.r2, 4)}</p>
          </div>
          <div>
            <span className="text-text-secondary">Fold Stability</span>
            <p className="font-mono font-medium text-text-primary">{fmt(winner.fold_stability, 4)}</p>
          </div>
          <div>
            <span className="text-text-secondary">Scaler</span>
            <p className="font-medium capitalize text-text-primary">{winner.scaler_variant}</p>
          </div>
        </div>
      </div>

      <p className="mt-4 text-xs text-text-secondary">
        Selected based on lowest OOS RMSE with stable cross-validation performance
      </p>
    </div>
  );
}
