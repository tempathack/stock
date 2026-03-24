import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export function exportTableToPdf(
  filename: string,
  title: string,
  headers: string[],
  rows: string[][],
  metadata?: string[],
): void {
  const doc = new jsPDF({ orientation: "landscape" });

  // Title
  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(224, 224, 224);
  doc.setFillColor(15, 52, 96);
  doc.rect(0, 0, doc.internal.pageSize.getWidth(), 35, "F");
  doc.text(title, 14, 18);

  // Metadata
  let startY = 28;
  if (metadata?.length) {
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(180, 180, 180);
    metadata.forEach((line) => {
      doc.text(line, 14, startY);
      startY += 4;
    });
  }

  // Table
  autoTable(doc, {
    head: [headers],
    body: rows,
    startY: startY + 6,
    theme: "grid",
    styles: {
      fillColor: [26, 26, 46],
      textColor: [224, 224, 224],
      lineColor: [42, 42, 74],
      lineWidth: 0.3,
      fontSize: 8,
      cellPadding: 3,
    },
    headStyles: {
      fillColor: [15, 52, 96],
      textColor: [255, 255, 255],
      fontStyle: "bold",
      fontSize: 9,
    },
    alternateRowStyles: {
      fillColor: [22, 33, 62],
    },
  });

  doc.save(filename);
}
