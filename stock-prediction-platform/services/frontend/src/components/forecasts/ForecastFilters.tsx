import type { ForecastFiltersState } from "@/api";

interface ForecastFiltersProps {
  filters: ForecastFiltersState;
  onFilterChange: (filters: ForecastFiltersState) => void;
  sectors: string[];
}

export default function ForecastFilters({
  filters,
  onFilterChange,
  sectors,
}: ForecastFiltersProps) {
  const update = (patch: Partial<ForecastFiltersState>) =>
    onFilterChange({ ...filters, ...patch });

  const clearAll = () =>
    onFilterChange({
      sector: null,
      minReturn: null,
      maxReturn: null,
      minConfidence: null,
      search: "",
    });

  const hasActive =
    filters.sector !== null ||
    filters.minReturn !== null ||
    filters.maxReturn !== null ||
    filters.minConfidence !== null ||
    filters.search !== "";

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-6">
        {/* Search */}
        <div className="lg:col-span-1">
          <label className="mb-1 block text-xs text-text-secondary">
            Search
          </label>
          <input
            type="text"
            placeholder="Ticker or company…"
            value={filters.search}
            onChange={(e) => update({ search: e.target.value })}
            className="w-full rounded border border-border bg-bg-card px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-accent focus:outline-none"
          />
        </div>

        {/* Sector */}
        <div>
          <label className="mb-1 block text-xs text-text-secondary">
            Sector
          </label>
          <select
            value={filters.sector ?? ""}
            onChange={(e) =>
              update({ sector: e.target.value || null })
            }
            className="w-full rounded border border-border bg-bg-card px-3 py-1.5 text-sm text-text-primary focus:border-accent focus:outline-none"
          >
            <option value="">All Sectors</option>
            {sectors.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Min Return */}
        <div>
          <label className="mb-1 block text-xs text-text-secondary">
            Min Return %
          </label>
          <input
            type="number"
            step="0.5"
            placeholder="—"
            value={filters.minReturn ?? ""}
            onChange={(e) =>
              update({
                minReturn: e.target.value ? Number(e.target.value) : null,
              })
            }
            className="w-full rounded border border-border bg-bg-card px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-accent focus:outline-none"
          />
        </div>

        {/* Max Return */}
        <div>
          <label className="mb-1 block text-xs text-text-secondary">
            Max Return %
          </label>
          <input
            type="number"
            step="0.5"
            placeholder="—"
            value={filters.maxReturn ?? ""}
            onChange={(e) =>
              update({
                maxReturn: e.target.value ? Number(e.target.value) : null,
              })
            }
            className="w-full rounded border border-border bg-bg-card px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-accent focus:outline-none"
          />
        </div>

        {/* Confidence slider */}
        <div>
          <label className="mb-1 block text-xs text-text-secondary">
            Min Confidence:{" "}
            <span className="text-text-primary">
              {filters.minConfidence != null
                ? filters.minConfidence.toFixed(2)
                : "Any"}
            </span>
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={filters.minConfidence ?? 0}
            onChange={(e) => {
              const v = Number(e.target.value);
              update({ minConfidence: v > 0 ? v : null });
            }}
            className="mt-1 w-full accent-accent"
          />
        </div>

        {/* Clear */}
        <div className="flex items-end">
          <button
            onClick={clearAll}
            disabled={!hasActive}
            className="w-full rounded bg-bg-card px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-border hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
}
