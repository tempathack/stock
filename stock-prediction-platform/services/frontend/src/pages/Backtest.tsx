import { useState, useMemo } from "react";
import {
  Autocomplete,
  Box,
  ButtonGroup,
  Button,
  Container,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid";
import LoadingButton from "@mui/lab/LoadingButton";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import { ErrorFallback } from "@/components/ui";
import { BacktestChart, BacktestMetricsSummary } from "@/components/backtest";
import { useBacktest, useMarketOverview } from "@/api";
import { exportToCsv } from "@/utils/exportCsv";
import { exportTableToPdf } from "@/utils/exportPdf";

export default function Backtest() {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const oneYearAgo = useMemo(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 1);
    return d.toISOString().slice(0, 10);
  }, []);

  const [ticker, setTicker] = useState("AAPL");
  const [start, setStart] = useState(oneYearAgo);
  const [end, setEnd] = useState(today);
  const [horizon, setHorizon] = useState<number | undefined>(undefined);
  const [activeTicker, setActiveTicker] = useState("AAPL");

  const backtestQuery = useBacktest(activeTicker, start, end, horizon);
  const marketQuery = useMarketOverview();

  const tickers = useMemo(() => {
    if (!marketQuery.data?.stocks?.length) return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"];
    return marketQuery.data.stocks.map((t) => t.ticker).sort();
  }, [marketQuery.data]);

  const handleRun = () => {
    const cleaned = ticker.trim().toUpperCase();
    if (cleaned) setActiveTicker(cleaned);
  };

  const handleExportCsv = () => {
    if (!backtestQuery.data) return;
    const d = backtestQuery.data;
    const headers = ["Date", "Actual Price", "Predicted Price", "Error"];
    const rows = d.series.map((p) => [
      p.date,
      p.actual_price.toFixed(2),
      p.predicted_price.toFixed(2),
      Math.abs(p.actual_price - p.predicted_price).toFixed(2),
    ]);
    exportToCsv(`backtest_${activeTicker}_${start}_${end}.csv`, headers, rows);
  };

  const handleExportPdf = () => {
    if (!backtestQuery.data) return;
    const d = backtestQuery.data;
    const headers = ["Date", "Actual Price", "Predicted Price", "Error"];
    const rows = d.series.map((p) => [
      p.date,
      p.actual_price.toFixed(2),
      p.predicted_price.toFixed(2),
      Math.abs(p.actual_price - p.predicted_price).toFixed(2),
    ]);
    exportTableToPdf(
      `backtest_${activeTicker}_${start}_${end}.pdf`,
      `Backtest Report — ${activeTicker}`,
      headers,
      rows,
      [
        `Model: ${d.model_name}`,
        `Horizon: ${d.horizon}d`,
        `Period: ${d.start_date} → ${d.end_date}`,
        `RMSE: ${d.metrics.rmse.toFixed(4)}`,
        `MAE: ${d.metrics.mae.toFixed(4)}`,
        `Dir. Accuracy: ${d.metrics.directional_accuracy.toFixed(1)}%`,
      ],
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {backtestQuery.isLoading && (
        <LinearProgress sx={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 9999 }} />
      )}

      <Typography variant="h4" sx={{ mb: 3 }}>
        Backtest
      </Typography>

      {/* Control Panel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="flex-end">
          {/* Ticker */}
          <Grid size={{ xs: 12, sm: 4, md: 3 }}>
            <Autocomplete
              options={tickers}
              value={ticker}
              onChange={(_, v) => setTicker(v ?? "AAPL")}
              renderInput={(params) => (
                <TextField {...params} label="Ticker" size="small" fullWidth />
              )}
              freeSolo
            />
          </Grid>

          {/* Start Date */}
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <TextField
              type="date"
              label="Start Date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              size="small"
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          {/* End Date */}
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <TextField
              type="date"
              label="End Date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              size="small"
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          {/* Horizon */}
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <Select
              value={horizon != null ? String(horizon) : ""}
              onChange={(e) => {
                const v = e.target.value as string;
                setHorizon(v !== "" ? Number(v) : undefined);
              }}
              size="small"
              fullWidth
              displayEmpty
            >
              <MenuItem value="">All Horizons</MenuItem>
              <MenuItem value="1">1d</MenuItem>
              <MenuItem value="7">7d</MenuItem>
              <MenuItem value="30">30d</MenuItem>
            </Select>
          </Grid>

          {/* Run Button */}
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <Tooltip title="Run backtest with selected parameters">
              <span style={{ display: "block" }}>
                <LoadingButton
                  loading={backtestQuery.isLoading}
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleRun}
                  fullWidth
                >
                  Run Backtest
                </LoadingButton>
              </span>
            </Tooltip>
          </Grid>

          {/* Export Buttons */}
          <Grid size={{ xs: 12, sm: 4, md: 1 }}>
            <ButtonGroup variant="outlined" size="small" disabled={!backtestQuery.data}>
              <Tooltip title="Export as CSV">
                <span>
                  <Button onClick={handleExportCsv} disabled={!backtestQuery.data}>
                    <FileDownloadIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title="Export as PDF">
                <span>
                  <Button onClick={handleExportPdf} disabled={!backtestQuery.data}>
                    <PictureAsPdfIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
            </ButtonGroup>
          </Grid>
        </Grid>
      </Paper>

      {/* Error State */}
      {backtestQuery.isError && (
        <ErrorFallback
          message={`No backtest data available for ${activeTicker} in the selected range.`}
        />
      )}

      {/* Results */}
      {backtestQuery.data && (
        <Box>
          {/* Model info banner */}
          <Paper sx={{ px: 3, py: 1.5, mb: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Model:{" "}
              <Box component="span" sx={{ color: "text.primary", fontWeight: 600 }}>
                {backtestQuery.data.model_name}
              </Box>
              {" · "}Horizon:{" "}
              <Box component="span" sx={{ color: "text.primary", fontWeight: 600 }}>
                {backtestQuery.data.horizon}d
              </Box>
              {" · "}Period:{" "}
              <Box component="span" sx={{ color: "text.primary", fontWeight: 600 }}>
                {backtestQuery.data.start_date}
              </Box>
              {" → "}
              <Box component="span" sx={{ color: "text.primary", fontWeight: 600 }}>
                {backtestQuery.data.end_date}
              </Box>
            </Typography>
          </Paper>

          {/* Chart */}
          <Paper sx={{ p: 2, mb: 3, height: 450 }} data-testid="backtest-chart">
            <BacktestChart
              series={backtestQuery.data.series}
              ticker={activeTicker}
            />
          </Paper>

          {/* Metrics summary */}
          <BacktestMetricsSummary metrics={backtestQuery.data.metrics} />
        </Box>
      )}
    </Container>
  );
}
