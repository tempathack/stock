import { useState, useCallback } from "react";
import {
  Box,
  Chip,
  CircularProgress,
  Container,
  Divider,
  InputAdornment,
  Paper,
  Skeleton,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef } from "@mui/x-data-grid";
import { PageHeader } from "@/components/layout";
import { ErrorFallback } from "@/components/ui";
import {
  useSearchPredictions,
  useSearchModels,
  useSearchDriftEvents,
  useSearchStocks,
} from "@/api";

// Shared DataGrid sx — matches UI spec
const GRID_SX = {
  border: "none",
  "& .MuiDataGrid-columnHeaders": {
    backgroundColor: "rgba(7, 4, 26, 0.9)",
  },
};

// Shared DataGrid props
const GRID_PROPS = {
  density: "compact" as const,
  disableRowSelectionOnClick: true,
  pageSizeOptions: [25, 50, 100],
  initialState: { pagination: { paginationModel: { pageSize: 50 } } },
  sx: GRID_SX,
};

// Severity chip colors from UI spec
function SeverityChip({ value }: { value: string | null }) {
  if (!value) return <span>—</span>;
  const colorMap: Record<string, string> = {
    high: "#FF2D78",
    medium: "#FFD60A",
    low: "#6B60A8",
  };
  return (
    <Chip
      label={value}
      size="small"
      sx={{ backgroundColor: colorMap[value.toLowerCase()] ?? "#6B60A8", color: "#fff", fontSize: "0.7rem" }}
    />
  );
}

// Status chip for models
function StatusChip({ value }: { value: string | null }) {
  if (!value) return <span>—</span>;
  const colorMap: Record<string, string> = {
    winner: "#7C3AED",
    active: "#00F5FF",
    retired: "#6B60A8",
  };
  return (
    <Chip
      label={value}
      size="small"
      sx={{ backgroundColor: colorMap[value.toLowerCase()] ?? "#6B60A8", color: "#fff", fontSize: "0.7rem" }}
    />
  );
}

// Confidence chip
function ConfidenceChip({ value }: { value: string | null }) {
  if (!value) return <span>—</span>;
  const colorMap: Record<string, string> = { high: "#00FF87", medium: "#FFD60A", low: "#FF2D78" };
  return (
    <Chip
      label={value}
      size="small"
      sx={{ backgroundColor: colorMap[value.toLowerCase()] ?? "#6B60A8", color: "#fff", fontSize: "0.7rem" }}
    />
  );
}

// Column definitions per UI spec
const predictionsColumns: GridColDef[] = [
  { field: "ticker", headerName: "Ticker", width: 80, renderCell: (p) => <strong style={{ fontFamily: "JetBrains Mono" }}>{p.value ?? "—"}</strong> },
  { field: "predicted_price", headerName: "Predicted Price", width: 120, type: "number", headerAlign: "right", align: "right", valueFormatter: (v) => v != null ? `$${Number(v).toFixed(2)}` : "—" },
  { field: "current_price", headerName: "Actual Price", width: 120, type: "number", headerAlign: "right", align: "right", valueFormatter: (v) => v != null ? `$${Number(v).toFixed(2)}` : "—" },
  {
    field: "expected_return_pct",
    headerName: "Expected Return",
    width: 110,
    type: "number",
    headerAlign: "right",
    align: "right",
    renderCell: (p) => {
      const v = p.value as number | null;
      if (v == null) return "—";
      const color = v >= 0 ? "#00FF87" : "#FF2D78";
      return <span style={{ color, fontFamily: "JetBrains Mono" }}>{v >= 0 ? "+" : ""}{v.toFixed(2)}%</span>;
    },
  },
  { field: "confidence", headerName: "Confidence", width: 100, renderCell: (p) => <ConfidenceChip value={p.value} /> },
  { field: "model_id", headerName: "Model ID", width: 120, renderCell: (p) => <span style={{ color: "#6B60A8" }}>{p.value ?? "—"}</span> },
  { field: "prediction_date", headerName: "Prediction Date", width: 130, valueFormatter: (v) => v ?? "—" },
];

const modelsColumns: GridColDef[] = [
  { field: "model_name", headerName: "Model Name", width: 180, renderCell: (p) => <strong>{p.value ?? "—"}</strong> },
  { field: "status", headerName: "Status", width: 90, renderCell: (p) => <StatusChip value={p.value} /> },
  { field: "r2_oos", headerName: "R² (OOS)", width: 90, type: "number", valueFormatter: (v) => v != null ? Number(v).toFixed(4) : "—" },
  { field: "rmse_oos", headerName: "RMSE (OOS)", width: 90, type: "number", valueFormatter: (v) => v != null ? Number(v).toFixed(4) : "—" },
  { field: "mae_oos", headerName: "MAE (OOS)", width: 90, type: "number", valueFormatter: (v) => v != null ? Number(v).toFixed(4) : "—" },
  { field: "trained_at", headerName: "Trained Date", width: 130, valueFormatter: (v) => v ?? "—" },
  { field: "version", headerName: "Version", width: 80, renderCell: (p) => <span style={{ fontFamily: "JetBrains Mono" }}>{p.value ?? "—"}</span> },
];

const driftColumns: GridColDef[] = [
  { field: "timestamp", headerName: "Timestamp", width: 160, renderCell: (p) => <span style={{ fontFamily: "JetBrains Mono" }}>{p.value ?? "—"}</span> },
  { field: "drift_type", headerName: "Drift Type", width: 120, renderCell: (p) => <span style={{ fontFamily: "JetBrains Mono" }}>{p.value ?? "—"}</span> },
  { field: "severity", headerName: "Severity", width: 90, renderCell: (p) => <SeverityChip value={p.value} /> },
  { field: "ticker", headerName: "Ticker", width: 80, valueFormatter: (v) => v ?? "—" },
  {
    field: "details",
    headerName: "Details",
    flex: 1,
    renderCell: (p) => (
      <Tooltip title={p.value ?? ""} placement="top">
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.value ?? "—"}</span>
      </Tooltip>
    ),
  },
  { field: "retrain_triggered", headerName: "Retrain", width: 80, valueFormatter: (v) => v === true ? "Yes" : v === false ? "No" : "—" },
];

const stocksColumns: GridColDef[] = [
  { field: "ticker", headerName: "Ticker", width: 80, renderCell: (p) => <strong style={{ fontFamily: "JetBrains Mono" }}>{p.value ?? "—"}</strong> },
  { field: "company_name", headerName: "Company Name", width: 200 },
  { field: "sector", headerName: "Sector", width: 140, renderCell: (p) => <span style={{ color: "#6B60A8" }}>{p.value ?? "—"}</span> },
  { field: "industry", headerName: "Industry", width: 160, renderCell: (p) => <span style={{ color: "#6B60A8" }}>{p.value ?? "—"}</span> },
  {
    field: "market_cap",
    headerName: "Market Cap",
    width: 100,
    type: "number",
    valueFormatter: (v) => {
      if (v == null) return "—";
      const n = Number(v);
      if (n >= 1e12) return `${(n / 1e12).toFixed(1)}T`;
      if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
      if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
      return String(n);
    },
  },
  { field: "exchange", headerName: "Exchange", width: 80, renderCell: (p) => p.value ? <Chip label={p.value.toUpperCase()} size="small" variant="outlined" /> : <span>—</span> },
];

// Empty state component
function EmptyState({ hasQuery, query, entity }: { hasQuery: boolean; query: string; entity: string }) {
  if (!hasQuery) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", py: 8, gap: 1 }}>
        <SearchIcon sx={{ fontSize: 120, color: "#6B60A8", opacity: 0.4 }} />
        <Typography variant="h6" sx={{ color: "#6B60A8" }}>Start searching</Typography>
        <Typography variant="body2" sx={{ color: "#6B60A8" }}>Enter a ticker, model name, or keyword above to search across all entities.</Typography>
      </Box>
    );
  }
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", py: 8, gap: 1 }}>
      <Typography variant="h6" sx={{ color: "#6B60A8" }}>No results found</Typography>
      <Typography variant="body2" sx={{ color: "#6B60A8" }}>No {entity} matched &quot;{query}&quot;. Try a different search term or broaden your filters.</Typography>
    </Box>
  );
}

// Loading skeleton
function LoadingSkeleton() {
  return (
    <Box sx={{ p: 2 }}>
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={48} sx={{ mb: 0.5, borderRadius: 1 }} />
      ))}
    </Box>
  );
}

// Tab panel: only render when active (keepMounted=false via conditional)
interface TabPanelProps {
  active: boolean;
  children: React.ReactNode;
}
function TabPanel({ active, children }: TabPanelProps) {
  if (!active) return null;
  return <Box>{children}</Box>;
}

const TABS = ["Predictions", "Models", "Drift Events", "Stocks"] as const;
type TabName = (typeof TABS)[number];

export default function Search() {
  const [inputValue, setInputValue] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [activeTab, setActiveTab] = useState<number>(0);
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const hasQuery = debouncedQuery.trim().length > 0;
  const searchParams = { q: debouncedQuery || undefined };

  const predictions = useSearchPredictions(searchParams, hasQuery);
  const models = useSearchModels(searchParams, hasQuery);
  const driftEvents = useSearchDriftEvents(searchParams, hasQuery);
  const stocks = useSearchStocks(searchParams, hasQuery);

  const isFetching = predictions.isFetching || models.isFetching || driftEvents.isFetching || stocks.isFetching;

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);
    if (debounceTimer) clearTimeout(debounceTimer);
    const timer = setTimeout(() => setDebouncedQuery(value), 300);
    setDebounceTimer(timer);
  }, [debounceTimer]);

  const getTabLabel = (tab: TabName, idx: number): string => {
    if (!hasQuery) return tab;
    const counts = [
      predictions.data?.total,
      models.data?.total,
      driftEvents.data?.total,
      stocks.data?.total,
    ];
    const count = counts[idx];
    if (predictions.isLoading || models.isLoading) return `${tab} (Searching...)`;
    return count != null ? `${tab} (${count})` : tab;
  };

  // Build rows with id field for DataGrid
  const makeRows = <T extends object>(items: T[] | undefined): (T & { id: number })[] =>
    (items ?? []).map((item, i) => ({ ...item, id: i }));

  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Search"
        subtitle="Search predictions, models, drift events, and stocks"
      />

      {/* Search input card */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: "rgba(13, 10, 36, 0.7)", border: "1px solid rgba(124, 58, 237, 0.22)" }}>
        <TextField
          fullWidth
          variant="outlined"
          size="medium"
          autoFocus
          placeholder="Search predictions, models, drift events, and stocks..."
          value={inputValue}
          onChange={handleInputChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: "#6B60A8" }} />
              </InputAdornment>
            ),
            endAdornment: isFetching ? (
              <InputAdornment position="end">
                <CircularProgress size={16} />
              </InputAdornment>
            ) : null,
          }}
        />
      </Paper>

      {/* Tabs + results card */}
      <Paper sx={{ p: 0, backgroundColor: "rgba(13, 10, 36, 0.7)", border: "1px solid rgba(124, 58, 237, 0.22)" }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="scrollable"
          scrollButtons="auto"
          indicatorColor="primary"
          sx={{
            "& .MuiTabs-indicator": {
              background: "linear-gradient(90deg, #7C3AED, #00F5FF)",
            },
          }}
        >
          {TABS.map((tab, idx) => (
            <Tab key={tab} label={getTabLabel(tab, idx)} />
          ))}
        </Tabs>
        <Divider sx={{ borderColor: "rgba(124, 58, 237, 0.22)" }} />

        {/* Predictions tab */}
        <TabPanel active={activeTab === 0}>
          {predictions.isError ? (
            <Box sx={{ p: 3 }}><ErrorFallback message="Search unavailable — the search service could not be reached. Check that Elasticsearch is running and retry." onRetry={predictions.refetch} /></Box>
          ) : predictions.isLoading ? (
            <LoadingSkeleton />
          ) : !hasQuery || !predictions.data?.items.length ? (
            <EmptyState hasQuery={hasQuery} query={debouncedQuery} entity="predictions" />
          ) : (
            <DataGrid
              {...GRID_PROPS}
              rows={makeRows(predictions.data.items)}
              columns={predictionsColumns}
            />
          )}
        </TabPanel>

        {/* Models tab */}
        <TabPanel active={activeTab === 1}>
          {models.isError ? (
            <Box sx={{ p: 3 }}><ErrorFallback message="Search unavailable — the search service could not be reached. Check that Elasticsearch is running and retry." onRetry={models.refetch} /></Box>
          ) : models.isLoading ? (
            <LoadingSkeleton />
          ) : !hasQuery || !models.data?.items.length ? (
            <EmptyState hasQuery={hasQuery} query={debouncedQuery} entity="models" />
          ) : (
            <DataGrid
              {...GRID_PROPS}
              rows={makeRows(models.data.items)}
              columns={modelsColumns}
            />
          )}
        </TabPanel>

        {/* Drift Events tab */}
        <TabPanel active={activeTab === 2}>
          {driftEvents.isError ? (
            <Box sx={{ p: 3 }}><ErrorFallback message="Search unavailable — the search service could not be reached. Check that Elasticsearch is running and retry." onRetry={driftEvents.refetch} /></Box>
          ) : driftEvents.isLoading ? (
            <LoadingSkeleton />
          ) : !hasQuery || !driftEvents.data?.items.length ? (
            <EmptyState hasQuery={hasQuery} query={debouncedQuery} entity="drift events" />
          ) : (
            <DataGrid
              {...GRID_PROPS}
              rows={makeRows(driftEvents.data.items)}
              columns={driftColumns}
            />
          )}
        </TabPanel>

        {/* Stocks tab */}
        <TabPanel active={activeTab === 3}>
          {stocks.isError ? (
            <Box sx={{ p: 3 }}><ErrorFallback message="Search unavailable — the search service could not be reached. Check that Elasticsearch is running and retry." onRetry={stocks.refetch} /></Box>
          ) : stocks.isLoading ? (
            <LoadingSkeleton />
          ) : !hasQuery || !stocks.data?.items.length ? (
            <EmptyState hasQuery={hasQuery} query={debouncedQuery} entity="stocks" />
          ) : (
            <DataGrid
              {...GRID_PROPS}
              rows={makeRows(stocks.data.items)}
              columns={stocksColumns}
            />
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
}
