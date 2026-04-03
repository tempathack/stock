import { useMemo } from "react";
import { DataGrid } from "@mui/x-data-grid";
import type {
  GridColDef,
  GridColumnGroupingModel,
  GridRowParams,
} from "@mui/x-data-grid";
import { Box, Tooltip } from "@mui/material";
import type { MultiHorizonForecastRow } from "@/api";

interface ForecastTableProps {
  rows: MultiHorizonForecastRow[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
}

const fmt = (n: number | null, decimals = 2, prefix = "") =>
  n != null ? `${prefix}${n.toFixed(decimals)}` : "—";

export default function ForecastTable({
  rows,
  selectedTicker,
  onSelectTicker,
}: ForecastTableProps) {
  // Flatten MultiHorizonForecastRow.horizons into DataGrid-compatible flat fields
  const flatRows = useMemo(
    () =>
      rows.map((row) => ({
        ticker: row.ticker,
        company_name: row.company_name,
        sector: row.sector,
        current_price: row.current_price,
        daily_change_pct: row.daily_change_pct,
        // 1-day
        price_1d: row.horizons[1]?.predicted_price ?? null,
        return_1d: row.horizons[1]?.expected_return_pct ?? null,
        date_1d: row.horizons[1]?.predicted_date ?? null,
        // 7-day
        price_7d: row.horizons[7]?.predicted_price ?? null,
        return_7d: row.horizons[7]?.expected_return_pct ?? null,
        date_7d: row.horizons[7]?.predicted_date ?? null,
        // 14-day
        price_14d: row.horizons[14]?.predicted_price ?? null,
        return_14d: row.horizons[14]?.expected_return_pct ?? null,
        date_14d: row.horizons[14]?.predicted_date ?? null,
        // 30-day
        price_30d: row.horizons[30]?.predicted_price ?? null,
        return_30d: row.horizons[30]?.expected_return_pct ?? null,
        date_30d: row.horizons[30]?.predicted_date ?? null,
      })),
    [rows],
  );

  type FlatRow = (typeof flatRows)[0];

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
      { field: "company_name", headerName: "Company", flex: 1, minWidth: 140 },
      { field: "sector", headerName: "Sector", width: 120 },
      {
        field: "current_price",
        headerName: "Price",
        width: 95,
        renderCell: (params) => (
          <Box sx={{ fontFamily: "monospace" }}>
            {fmt(params.value as number | null, 2, "$")}
          </Box>
        ),
      },
      {
        field: "daily_change_pct",
        headerName: "Daily \u0394",
        width: 85,
        renderCell: (params) => {
          const v = params.value as number | null;
          if (v == null) return <span>—</span>;
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
      // ── 1-day columns ──────────────────────────────
      {
        field: "price_1d",
        headerName: "Pred. Price",
        width: 105,
        renderCell: (params) => {
          const v = params.value as number | null;
          const date = (params.row as FlatRow).date_1d;
          return (
            <Tooltip title={date ? `Predicted date: ${date}` : ""} placement="top">
              <Box sx={{ fontFamily: "monospace" }}>{fmt(v, 2, "$")}</Box>
            </Tooltip>
          );
        },
      },
      {
        field: "return_1d",
        headerName: "Return %",
        width: 95,
        renderCell: (params) => {
          const v = params.value as number | null;
          if (v == null) return <Box sx={{ color: "text.secondary" }}>—</Box>;
          return (
            <Box
              sx={{ fontFamily: "monospace", fontWeight: 600, color: v >= 0 ? "success.main" : "error.main" }}
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(2)}%
            </Box>
          );
        },
      },
      // ── 7-day columns ──────────────────────────────
      {
        field: "price_7d",
        headerName: "Pred. Price",
        width: 105,
        renderCell: (params) => {
          const v = params.value as number | null;
          const date = (params.row as FlatRow).date_7d;
          return (
            <Tooltip title={date ? `Predicted date: ${date}` : ""} placement="top">
              <Box sx={{ fontFamily: "monospace" }}>{fmt(v, 2, "$")}</Box>
            </Tooltip>
          );
        },
      },
      {
        field: "return_7d",
        headerName: "Return %",
        width: 95,
        renderCell: (params) => {
          const v = params.value as number | null;
          if (v == null) return <Box sx={{ color: "text.secondary" }}>—</Box>;
          return (
            <Box
              sx={{ fontFamily: "monospace", fontWeight: 600, color: v >= 0 ? "success.main" : "error.main" }}
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(2)}%
            </Box>
          );
        },
      },
      // ── 14-day columns ─────────────────────────────
      {
        field: "price_14d",
        headerName: "Pred. Price",
        width: 105,
        renderCell: (params) => {
          const v = params.value as number | null;
          const date = (params.row as FlatRow).date_14d;
          return (
            <Tooltip title={date ? `Predicted date: ${date}` : ""} placement="top">
              <Box sx={{ fontFamily: "monospace" }}>{fmt(v, 2, "$")}</Box>
            </Tooltip>
          );
        },
      },
      {
        field: "return_14d",
        headerName: "Return %",
        width: 95,
        renderCell: (params) => {
          const v = params.value as number | null;
          if (v == null) return <Box sx={{ color: "text.secondary" }}>—</Box>;
          return (
            <Box
              sx={{ fontFamily: "monospace", fontWeight: 600, color: v >= 0 ? "success.main" : "error.main" }}
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(2)}%
            </Box>
          );
        },
      },
      // ── 30-day columns ─────────────────────────────
      {
        field: "price_30d",
        headerName: "Pred. Price",
        width: 105,
        renderCell: (params) => {
          const v = params.value as number | null;
          const date = (params.row as FlatRow).date_30d;
          return (
            <Tooltip title={date ? `Predicted date: ${date}` : ""} placement="top">
              <Box sx={{ fontFamily: "monospace" }}>{fmt(v, 2, "$")}</Box>
            </Tooltip>
          );
        },
      },
      {
        field: "return_30d",
        headerName: "Return %",
        width: 95,
        renderCell: (params) => {
          const v = params.value as number | null;
          if (v == null) return <Box sx={{ color: "text.secondary" }}>—</Box>;
          return (
            <Box
              sx={{ fontFamily: "monospace", fontWeight: 600, color: v >= 0 ? "success.main" : "error.main" }}
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(2)}%
            </Box>
          );
        },
      },
    ],
    [],
  );

  const columnGroupingModel: GridColumnGroupingModel = [
    {
      groupId: "1d",
      headerName: "1-Day Forecast",
      children: [{ field: "price_1d" }, { field: "return_1d" }],
      headerAlign: "center",
    },
    {
      groupId: "7d",
      headerName: "7-Day Forecast",
      children: [{ field: "price_7d" }, { field: "return_7d" }],
      headerAlign: "center",
    },
    {
      groupId: "14d",
      headerName: "14-Day Forecast",
      children: [{ field: "price_14d" }, { field: "return_14d" }],
      headerAlign: "center",
    },
    {
      groupId: "30d",
      headerName: "30-Day Forecast",
      children: [{ field: "price_30d" }, { field: "return_30d" }],
      headerAlign: "center",
    },
  ];

  return (
    <DataGrid
      rows={flatRows}
      columns={columns}
      columnGroupingModel={columnGroupingModel}
      getRowId={(row) => row.ticker}
      onRowClick={(params: GridRowParams) => onSelectTicker(params.row.ticker)}
      initialState={{
        pagination: { paginationModel: { pageSize: 25 } },
        sorting: {
          sortModel: [{ field: "return_7d", sort: "desc" }],
        },
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
        "& .MuiDataGrid-columnHeaderGroup": {
          backgroundColor: "background.paper",
          color: "primary.main",
          fontWeight: 700,
          fontSize: "0.75rem",
          borderBottom: "2px solid",
          borderBottomColor: "rgba(124, 58, 237, 0.4)",
        },
      }}
      autoHeight
      disableColumnMenu
    />
  );
}
