interface HorizonToggleProps {
  horizons: number[];
  selected: number;
  onChange: (h: number) => void;
  loading?: boolean;
}

export function HorizonToggle({
  horizons,
  selected,
  onChange,
  loading = false,
}: HorizonToggleProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Prediction horizon"
      className={`inline-flex gap-1 rounded-lg bg-bg-card p-1 ${
        loading ? "pointer-events-none opacity-50" : ""
      }`}
    >
      {horizons.map((h) => {
        const isSelected = h === selected;
        return (
          <button
            key={h}
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(h)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isSelected
                ? "bg-accent text-white"
                : "text-text-secondary hover:bg-border hover:text-text-primary"
            }`}
          >
            {h}D
          </button>
        );
      })}
    </div>
  );
}

export default HorizonToggle;
