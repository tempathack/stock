import { useState, useMemo } from "react";
import { PageHeader } from "@/components/layout";
import { LoadingSpinner, ErrorFallback, ExportButtons } from "@/components/ui";
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

  return (
    <>
      <PageHeader
        title="Backtest"
        subtitle="Compare historical predictions against actual prices"
      />

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-end gap-4">
        {/* Ticker */}
        <div className="w-full sm:w-auto">
          <label className="mb-1 block text-xs text-text-secondary">
            Ticker
          </label>
          <select
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-text-primary"
          >
            {tickers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* Start */}
        <div className="w-full sm:w-auto">
          <label className="mb-1 block text-xs text-text-secondary">
            Start Date
          </label>
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-text-primary"
          />
        </div>

        {/* End */}
        <div className="w-full sm:w-auto">
          <label className="mb-1 block text-xs text-text-secondary">
            End Date
          </label>
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-text-primary"
          />
        </div>

        {/* Horizon */}
        <div className="w-full sm:w-auto">
          <label className="mb-1 block text-xs text-text-secondary">
            Horizon (days)
          </label>
          <select
            value={horizon ?? ""}
            onChange={(e) =>
              setHorizon(e.target.value ? Number(e.target.value) : undefined)
            }
            className="rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-text-primary"
          >
            <option value="">All</option>
            <option value="1">1d</option>
            <option value="7">7d</option>
            <option value="30">30d</option>
          </select>
        </div>

        {/* Run button */}
        <button
          onClick={handleRun}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent/80"
        >
          Run Backtest
        </button>

        <ExportButtons
          disabled={!backtestQuery.data}
          onExportCsv={() => {
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
          }}
          onExportPdf={() => {
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
              `Backtest Report \u2014 ${activeTicker}`,
              headers,
              rows,
              [
                `Model: ${d.model_name}`,
                `Horizon: ${d.horizon}d`,
                `Period: ${d.start_date} \u2192 ${d.end_date}`,
                `RMSE: ${d.metrics.rmse.toFixed(4)}`,
                `MAE: ${d.metrics.mae.toFixed(4)}`,
                `Dir. Accuracy: ${d.metrics.directional_accuracy.toFixed(1)}%`,
              ],
            );
          }}
        />
      </div>

      {/* Results */}
      {backtestQuery.isLoading && <LoadingSpinner />}
      {backtestQuery.isError && (
        <ErrorFallback
          message={`No backtest data available for ${activeTicker} in the selected range.`}
        />
      )}
      {backtestQuery.data && (
        <div className="space-y-6">
          {/* Model info banner */}
          <div className="rounded-lg border border-border bg-bg-card px-4 py-3 text-sm text-text-secondary">
            Model: <span className="font-medium text-text-primary">{backtestQuery.data.model_name}</span>
            {" · "}Horizon: <span className="font-medium text-text-primary">{backtestQuery.data.horizon}d</span>
            {" · "}Period: <span className="font-medium text-text-primary">{backtestQuery.data.start_date}</span>
            {" → "}
            <span className="font-medium text-text-primary">{backtestQuery.data.end_date}</span>
          </div>

          {/* Chart */}
          <BacktestChart
            series={backtestQuery.data.series}
            ticker={activeTicker}
          />

          {/* Metrics summary */}
          <BacktestMetricsSummary metrics={backtestQuery.data.metrics} />
        </div>
      )}
    </>
  );
}
