import { useState, useMemo } from "react";
import type { ModelComparisonEntry } from "@/api";

interface ModelComparisonTableProps {
  models: ModelComparisonEntry[];
  onSelectModel?: (model: ModelComparisonEntry) => void;
}

type SortField =
  | "model_name"
  | "oos_rmse"
  | "oos_mae"
  | "oos_r2"
  | "oos_mape"
  | "directional_accuracy"
  | "fold_stability";

type SortDir = "asc" | "desc";

function num(v: unknown): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : Infinity;
}

function fmt(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(decimals) : "—";
}

function pct(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? `${(n * 100).toFixed(decimals)}%` : "—";
}

const COLUMNS: {
  label: string;
  field: SortField;
  render: (m: ModelComparisonEntry) => string;
  mono?: boolean;
}[] = [
  { label: "Model Name", field: "model_name", render: (m) => m.model_name },
  { label: "Scaler", field: "model_name", render: (m) => m.scaler_variant },
  { label: "OOS RMSE", field: "oos_rmse", render: (m) => fmt(m.oos_metrics.rmse, 6), mono: true },
  { label: "OOS MAE", field: "oos_mae", render: (m) => fmt(m.oos_metrics.mae, 6), mono: true },
  { label: "OOS R²", field: "oos_r2", render: (m) => fmt(m.oos_metrics.r2, 4), mono: true },
  { label: "OOS MAPE", field: "oos_mape", render: (m) => pct(m.oos_metrics.mape, 2), mono: true },
  { label: "Dir. Accuracy", field: "directional_accuracy", render: (m) => pct(m.oos_metrics.directional_accuracy, 2), mono: true },
  { label: "Fold Stability", field: "fold_stability", render: (m) => fmt(m.fold_stability, 4), mono: true },
];

function getSortValue(m: ModelComparisonEntry, field: SortField): number | string {
  switch (field) {
    case "model_name":
      return m.model_name.toLowerCase();
    case "oos_rmse":
      return num(m.oos_metrics.rmse);
    case "oos_mae":
      return num(m.oos_metrics.mae);
    case "oos_r2":
      return num(m.oos_metrics.r2);
    case "oos_mape":
      return num(m.oos_metrics.mape);
    case "directional_accuracy":
      return num(m.oos_metrics.directional_accuracy);
    case "fold_stability":
      return num(m.fold_stability);
  }
}

export default function ModelComparisonTable({ models, onSelectModel }: ModelComparisonTableProps) {
  const [sortField, setSortField] = useState<SortField>("oos_rmse");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filter, setFilter] = useState("");

  const sorted = useMemo(() => {
    const filtered = models.filter((m) =>
      m.model_name.toLowerCase().includes(filter.toLowerCase()),
    );

    return [...filtered].sort((a, b) => {
      const va = getSortValue(a, sortField);
      const vb = getSortValue(b, sortField);
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [models, sortField, sortDir, filter]);

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  }

  function sortIndicator(field: SortField) {
    if (sortField !== field) return <span className="ml-1 text-text-secondary/40">↕</span>;
    return <span className="ml-1 text-accent">{sortDir === "asc" ? "▲" : "▼"}</span>;
  }

  return (
    <div className="space-y-3">
      {/* Filter */}
      <input
        type="text"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter by model name…"
        className="w-full max-w-xs rounded-md border border-border bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-accent focus:outline-none"
      />

      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-lg border border-border sm:block">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="sticky top-0 bg-bg-card text-xs uppercase tracking-wide text-text-secondary">
              {COLUMNS.map((col) => (
                <th
                  key={col.label}
                  className="cursor-pointer whitespace-nowrap px-4 py-3 font-medium hover:text-text-primary"
                  onClick={() => toggleSort(col.field)}
                >
                  {col.label}
                  {sortIndicator(col.field)}
                </th>
              ))}
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="px-4 py-8 text-center text-text-secondary">
                  No models found
                </td>
              </tr>
            )}
            {sorted.map((model) => (
              <tr
                key={`${model.model_name}-${model.scaler_variant}-${model.version}`}
                onClick={() => onSelectModel?.(model)}
                className={`cursor-pointer border-t border-border transition-colors hover:bg-bg-card/30 ${
                  model.is_winner
                    ? "border-l-4 border-l-accent bg-accent/5"
                    : "even:bg-bg-surface odd:bg-bg-primary"
                }`}
              >
                {COLUMNS.map((col, i) => (
                  <td
                    key={col.label}
                    className={`whitespace-nowrap px-4 py-3 ${col.mono ? "font-mono" : ""} ${
                      i === 0 ? "font-medium text-text-primary" : "text-text-secondary"
                    }`}
                  >
                    {i === 0 && model.is_winner && (
                      <span className="mr-2 text-xs text-accent">★</span>
                    )}
                    {col.render(model)}
                  </td>
                ))}
                <td className="px-4 py-3">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      model.is_active ? "bg-profit" : "bg-text-secondary/40"
                    }`}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card layout */}
      <div className="space-y-2 sm:hidden">
        {sorted.length === 0 && (
          <div className="rounded-lg border border-border bg-bg-surface p-8 text-center text-text-secondary">
            No models found
          </div>
        )}
        {sorted.map((model) => (
          <div
            key={`m-${model.model_name}-${model.scaler_variant}-${model.version}`}
            onClick={() => onSelectModel?.(model)}
            className={`cursor-pointer rounded-lg border border-border bg-bg-surface p-3 transition-colors hover:bg-bg-card/30 ${
              model.is_winner
                ? "border-l-4 border-l-accent bg-accent/5"
                : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {model.is_winner && (
                  <span className="text-xs text-accent">★</span>
                )}
                <span className="font-medium text-text-primary">
                  {model.model_name}
                </span>
              </div>
              <span
                className={`inline-block h-2 w-2 rounded-full ${
                  model.is_active ? "bg-profit" : "bg-text-secondary/40"
                }`}
              />
            </div>
            <p className="text-xs text-text-secondary">{model.scaler_variant}</p>
            <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <div>
                <span className="text-text-secondary">RMSE: </span>
                <span className="font-mono">{fmt(model.oos_metrics.rmse, 6)}</span>
              </div>
              <div>
                <span className="text-text-secondary">MAE: </span>
                <span className="font-mono">{fmt(model.oos_metrics.mae, 6)}</span>
              </div>
              <div>
                <span className="text-text-secondary">R²: </span>
                <span className="font-mono">{fmt(model.oos_metrics.r2, 4)}</span>
              </div>
              <div>
                <span className="text-text-secondary">Dir. Acc: </span>
                <span className="font-mono">{pct(model.oos_metrics.directional_accuracy, 2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
