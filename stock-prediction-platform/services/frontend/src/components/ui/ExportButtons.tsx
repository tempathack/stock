import { ButtonGroup, Button } from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";

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
  return (
    <ButtonGroup variant="outlined" size="small" className={className}>
      <Button
        disabled={disabled}
        onClick={onExportCsv}
        startIcon={<FileDownloadIcon />}
      >
        CSV
      </Button>
      <Button
        disabled={disabled}
        onClick={onExportPdf}
        startIcon={<PictureAsPdfIcon />}
      >
        PDF
      </Button>
    </ButtonGroup>
  );
}
