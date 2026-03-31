import { useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef, GridRowParams } from "@mui/x-data-grid";
import { Box, Chip, TextField } from "@mui/material";
import type { ModelComparisonEntry } from "@/api";

interface ModelComparisonTableProps {
  models: ModelComparisonEntry[];
  onSelectModel?: (model: ModelComparisonEntry) => void;
}

function fmt(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(decimals) : "—";
}

function pct(value: unknown, decimals: number): string {
  const n = Number(value);
  return Number.isFinite(n) ? `${(n * 100).toFixed(decimals)}%` : "—";
}

export default function ModelComparisonTable({
  models,
  onSelectModel,
}: ModelComparisonTableProps) {
  const [filter, setFilter] = useState("");

  const filtered = models.filter((m) =>
    m.model_name.toLowerCase().includes(filter.toLowerCase()),
  );

  const columns: GridColDef[] = [
    {
      field: "model_name",
      headerName: "Model Name",
      flex: 1,
      minWidth: 180,
      renderCell: (params) => {
        const row = params.row as ModelComparisonEntry;
        return (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {row.is_winner && (
              <Box component="span" sx={{ color: "primary.main", fontSize: "0.75rem" }}>
                ★
              </Box>
            )}
            <Box component="span" sx={{ fontWeight: row.is_winner ? 700 : 400 }}>
              {params.value}
            </Box>
          </Box>
        );
      },
    },
    { field: "scaler_variant", headerName: "Scaler", width: 110 },
    {
      field: "oos_rmse",
      headerName: "OOS RMSE",
      width: 110,
      valueGetter: (_value, row: ModelComparisonEntry) => row.oos_metrics?.rmse,
      renderCell: (params) => (
        <Box sx={{ fontFamily: "monospace" }}>{fmt(params.value, 6)}</Box>
      ),
    },
    {
      field: "oos_mae",
      headerName: "OOS MAE",
      width: 110,
      valueGetter: (_value, row: ModelComparisonEntry) => row.oos_metrics?.mae,
      renderCell: (params) => (
        <Box sx={{ fontFamily: "monospace" }}>{fmt(params.value, 6)}</Box>
      ),
    },
    {
      field: "oos_r2",
      headerName: "OOS R²",
      width: 90,
      valueGetter: (_value, row: ModelComparisonEntry) => row.oos_metrics?.r2,
      renderCell: (params) => (
        <Box sx={{ fontFamily: "monospace" }}>{fmt(params.value, 4)}</Box>
      ),
    },
    {
      field: "oos_mape",
      headerName: "OOS MAPE",
      width: 100,
      valueGetter: (_value, row: ModelComparisonEntry) => row.oos_metrics?.mape,
      renderCell: (params) => (
        <Box sx={{ fontFamily: "monospace" }}>{pct(params.value, 2)}</Box>
      ),
    },
    {
      field: "directional_accuracy",
      headerName: "Dir. Accuracy",
      width: 120,
      valueGetter: (_value, row: ModelComparisonEntry) =>
        row.oos_metrics?.directional_accuracy,
      renderCell: (params) => (
        <Box sx={{ fontFamily: "monospace" }}>{pct(params.value, 2)}</Box>
      ),
    },
    {
      field: "fold_stability",
      headerName: "Fold Stability",
      width: 120,
      renderCell: (params) => (
        <Box sx={{ fontFamily: "monospace" }}>{fmt(params.value, 4)}</Box>
      ),
    },
    {
      field: "status",
      headerName: "Status",
      width: 90,
      sortable: false,
      renderCell: (params) => {
        const row = params.row as ModelComparisonEntry;
        return row.is_active ? (
          <Chip label="Active" color="success" size="small" />
        ) : (
          <Chip label="Inactive" size="small" />
        );
      },
    },
  ];

  const getRowId = (row: ModelComparisonEntry) =>
    `${row.model_name}__${row.scaler_variant}__${row.version ?? row.saved_at ?? "nv"}`;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <TextField
        size="small"
        sx={{ maxWidth: 320 }}
        placeholder="Filter by model name…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        label="Search models"
      />
      <DataGrid
        rows={filtered}
        columns={columns}
        getRowId={getRowId}
        onRowClick={(params: GridRowParams) =>
          onSelectModel?.(params.row as ModelComparisonEntry)
        }
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
          sorting: { sortModel: [{ field: "oos_rmse", sort: "asc" }] },
        }}
        pageSizeOptions={[25, 50]}
        getRowClassName={(params) => {
          const row = params.row as ModelComparisonEntry;
          return row.is_winner ? "winner-row" : "";
        }}
        sx={{
          "& .MuiDataGrid-row": { cursor: "pointer" },
          "& .winner-row": {
            borderLeft: "4px solid",
            borderLeftColor: "primary.main",
            backgroundColor: "rgba(0, 188, 212, 0.05)",
          },
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
    </Box>
  );
}
