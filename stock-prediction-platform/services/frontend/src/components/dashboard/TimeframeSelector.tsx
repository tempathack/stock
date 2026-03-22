import type { Timeframe } from "@/api";

interface TimeframeSelectorProps {
  value: Timeframe;
  onChange: (tf: Timeframe) => void;
}

const OPTIONS: Timeframe[] = ["1D", "1W", "1M", "3M", "1Y"];

export default function TimeframeSelector({
  value,
  onChange,
}: TimeframeSelectorProps) {
  return (
    <div className="flex gap-1 rounded-lg bg-bg-card p-1 w-fit">
      {OPTIONS.map((tf) => (
        <button
          key={tf}
          onClick={() => onChange(tf)}
          className={`rounded px-3 py-1 text-sm transition-colors ${
            tf === value
              ? "bg-accent font-medium text-white"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}
