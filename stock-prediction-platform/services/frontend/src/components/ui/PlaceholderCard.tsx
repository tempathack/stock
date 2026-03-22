interface PlaceholderCardProps {
  title: string;
  phase: number;
}

export default function PlaceholderCard({ title, phase }: PlaceholderCardProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-bg-surface p-12">
      <p className="text-lg font-medium text-text-secondary">{title}</p>
      <span className="mt-2 rounded-full bg-bg-card px-3 py-1 text-xs text-text-secondary">
        Coming in Phase {phase}
      </span>
    </div>
  );
}
