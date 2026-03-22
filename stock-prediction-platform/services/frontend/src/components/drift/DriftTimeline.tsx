import type { DriftEventEntry } from "@/api";

interface DriftTimelineProps {
  events: DriftEventEntry[];
}

const DRIFT_TYPE_STYLES: Record<string, { label: string; bg: string; text: string }> = {
  data_drift: { label: "Data", bg: "bg-blue-500/20", text: "text-blue-400" },
  prediction_drift: { label: "Prediction", bg: "bg-purple-500/20", text: "text-purple-400" },
  concept_drift: { label: "Concept", bg: "bg-orange-500/20", text: "text-orange-400" },
};

const SEVERITY_STYLES: Record<string, { label: string; dot: string }> = {
  none: { label: "None", dot: "bg-gray-500" },
  low: { label: "Low", dot: "bg-green-500" },
  medium: { label: "Medium", dot: "bg-warning" },
  high: { label: "High", dot: "bg-accent" },
};

function fmtTimestamp(iso: string | null): string {
  if (!iso) return "Unknown";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function DriftTimeline({ events }: DriftTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-bg-surface p-6 text-center text-text-secondary">
        No drift events recorded
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-bg-surface p-5">
      <h3 className="text-sm font-semibold text-text-primary">Drift Event Timeline</h3>
      <p className="mt-0.5 text-xs text-text-secondary">{events.length} events detected</p>

      <div className="mt-4 space-y-3">
        {events.map((evt, idx) => {
          const typeStyle = DRIFT_TYPE_STYLES[evt.drift_type] ?? DRIFT_TYPE_STYLES.data_drift!;
          const sevStyle = SEVERITY_STYLES[evt.severity] ?? SEVERITY_STYLES.none!;

          return (
            <div
              key={`${evt.drift_type}-${evt.timestamp}-${idx}`}
              className="flex items-start gap-3 rounded-lg border border-border bg-bg-card p-3"
            >
              {/* Severity dot */}
              <div className="mt-1 flex-shrink-0">
                <div className={`h-2.5 w-2.5 rounded-full ${sevStyle.dot}`} />
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  {/* Type badge */}
                  <span
                    className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold uppercase ${typeStyle.bg} ${typeStyle.text}`}
                  >
                    {typeStyle.label}
                  </span>

                  {/* Severity badge */}
                  <span className="text-xs text-text-secondary">{sevStyle.label}</span>

                  {/* Drifted indicator */}
                  {evt.is_drifted && (
                    <span className="rounded bg-accent/15 px-1.5 py-0.5 text-xs font-medium text-accent">
                      Drifted
                    </span>
                  )}
                </div>

                {/* Timestamp */}
                <p className="mt-1 text-xs text-text-secondary">
                  {fmtTimestamp(evt.timestamp)}
                </p>

                {/* Features affected */}
                {evt.features_affected.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {evt.features_affected.map((f) => (
                      <span
                        key={f}
                        className="rounded bg-bg-primary px-1.5 py-0.5 text-xs font-mono text-text-secondary"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
