import { useMemo } from "react";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef, GridRowParams } from "@mui/x-data-grid";
import { Chip, Box } from "@mui/material";
import type { ForecastRow } from "@/api";

interface ForecastTableProps {
  rows: ForecastRow[];
  selectedTicker: string | null;
  comparisonTickers: string[];
  onSelectTicker: (ticker: string) => void;
  onToggleCompare: (ticker: string) => void;
}

const fmt = (n: number | null, decimals = 2, prefix = "") =>
  n != null ? `${prefix}${n.toFixed(decimals)}` : "—";

const trendColorMap: Record<string, "success" | "error" | "default"> = {
  bullish: "success",
  bearish: "error",
  neutral: "default",
};

export default function ForecastTable({
  rows,
  selectedTicker,
  onSelectTicker,
}: ForecastTableProps) {
  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: "ticker",
        headerName: "Ticker",
        width: 90,
        renderCell: (params) => (
          <Box
            component="span"
            sx={{ color: "primary.main", fontWeight: 600, fontFamily: "monospace" }}
          >
            {params.value}
          </Box>
        ),
      },
      { field: "company_name", headerName: "Company", flex: 1, minWidth: 150 },
      { field: "sector", headerName: "Sector", width: 130 },
      {
        field: "current_price",
        headerName: "Price",
        width: 100,
        renderCell: (params) => (
          <Box sx={{ fontFamily: "monospace" }}>
            {fmt(params.value as number | null, 2, "$")}
          </Box>
        ),
      },
      {
        field: "predicted_price",
        headerName: "Predicted",
        width: 110,
        renderCell: (params) => (
          <Box sx={{ fontFamily: "monospace" }}>
            {fmt(params.value as number | null, 2, "$")}
          </Box>
        ),
      },
      {
        field: "expected_return_pct",
        headerName: "Return %",
        width: 100,
        renderCell: (params) => {
          const v = params.value as number;
          return (
            <Box
              sx={{
                fontFamily: "monospace",
                fontWeight: 600,
                color: v >= 0 ? "success.main" : "error.main",
              }}
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(2)}%
            </Box>
          );
        },
      },
      {
        field: "confidence",
        headerName: "Conf.",
        width: 80,
        renderCell: (params) => (
          <Box sx={{ fontFamily: "monospace" }}>
            {fmt(params.value as number | null, 2)}
          </Box>
        ),
      },
      {
        field: "daily_change_pct",
        headerName: "Daily Δ",
        width: 90,
        renderCell: (params) => {
          const v = params.value as number | null;
          if (v == null) return "—";
          return (
            <Box
              sx={{
                fontFamily: "monospace",
                fontSize: "0.75rem",
                color: v >= 0 ? "success.main" : "error.main",
              }}
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(2)}%
            </Box>
          );
        },
      },
      {
        field: "trend",
        headerName: "Trend",
        width: 110,
        renderCell: (params) => {
          const trend = params.value as ForecastRow["trend"];
          return (
            <Chip
              label={trend}
              color={trendColorMap[trend]}
              size="small"
              sx={{ fontSize: "0.7rem" }}
            />
          );
        },
      },
    ],
    [],
  );

  const getRowId = (row: ForecastRow) => row.ticker;

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      getRowId={getRowId}
      onRowClick={(params: GridRowParams) => onSelectTicker(params.row.ticker)}
      initialState={{
        pagination: { paginationModel: { pageSize: 25 } },
      }}
      pageSizeOptions={[25, 50, 100]}
      getRowClassName={(params) =>
        params.row.ticker === selectedTicker ? "Mui-selected" : ""
      }
      sx={{
        "& .MuiDataGrid-row": { cursor: "pointer" },
        "& .MuiDataGrid-columnHeader": {
          backgroundColor: "background.paper",
          color: "text.secondary",
          fontWeight: 700,
          textTransform: "uppercase",
          fontSize: "0.7rem",
          letterSpacing: "0.05em",
        },
      }}
      autoHeight
      disableColumnMenu
    />
  );
}
