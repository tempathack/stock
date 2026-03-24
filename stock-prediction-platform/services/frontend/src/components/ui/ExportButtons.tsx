interface ExportButtonsProps {
  onExportCsv: () => void;
  onExportPdf: () => void;
  disabled?: boolean;
  className?: string;
}

export default function ExportButtons({
  onExportCsv,
  onExportPdf,
  disabled = false,
  className = "",
}: ExportButtonsProps) {
  const base =
    "rounded-md border border-border bg-bg-card px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:bg-border hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <button className={base} disabled={disabled} onClick={onExportCsv}>
        📄 CSV
      </button>
      <button className={base} disabled={disabled} onClick={onExportPdf}>
        📑 PDF
      </button>
    </div>
  );
}
