import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { Box, Chip, Stack, Typography } from "@mui/material";
import type { TreemapSectorGroup } from "@/api";
import MobileMarketList from "./MobileMarketList";

interface MarketTreemapProps {
  data: TreemapSectorGroup[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
  height?: number;
}

const getColorByChange = (pct: number): string => {
  if (pct >= 5)   return "#00C853";
  if (pct >= 3)   return "#00E676";
  if (pct >= 2)   return "#69F0AE";
  if (pct >= 1)   return "#A5D6A7";
  if (pct >= 0.5) return "#C8E6C9";
  if (pct >= 0)   return "#2E7D32";
  if (pct >= -0.5) return "#C62828";
  if (pct >= -1)  return "#E57373";
  if (pct >= -2)  return "#EF5350";
  if (pct >= -3)  return "#F44336";
  return "#D32F2F";
};

function useIsMobile(breakpoint = 640) {
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth < breakpoint : false,
  );
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    setIsMobile(mql.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);
  return isMobile;
}

export default function MarketTreemap({
  data,
  selectedTicker,
  onSelectTicker,
  height = 560,
}: MarketTreemapProps) {
  const isMobile = useIsMobile();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  const gainers = data.flatMap((g) => g.children).filter((s) => s.dailyChangePct > 0).length;
  const losers  = data.flatMap((g) => g.children).filter((s) => s.dailyChangePct < 0).length;

  useEffect(() => {
    if (isMobile || !chartRef.current || data.length === 0) return;

    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current, "dark");
    }

    const chart = chartInstanceRef.current;

    const treeData = data.map((group) => ({
      name: group.name,
      children: group.children.map((stock) => ({
        name: stock.ticker,
        value: Math.max(stock.marketCap ?? 1_000_000_000, 1_000_000_000),
        fullName: stock.name,
        price: stock.lastClose,
        changePct: stock.dailyChangePct,
        itemStyle: { color: getColorByChange(stock.dailyChangePct) },
      })),
    }));

    const option = {
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: "rgba(13,10,36,0.96)",
        borderColor: "rgba(124,58,237,0.4)",
        borderWidth: 1,
        textStyle: { color: "#fff", fontSize: 13 },
        formatter: (params: any) => {
          if (params.data?.children) {
            return `<div style="padding:8px"><div style="font-weight:bold;font-size:15px;margin-bottom:4px;">${params.name}</div><div style="color:#aaa;">${params.data.children.length} stocks</div></div>`;
          }
          const sign = params.data.changePct >= 0 ? "+" : "";
          const color = params.data.changePct >= 0 ? "#00E676" : "#FF5252";
          const cap = params.data.value >= 1e12
            ? `$${(params.data.value / 1e12).toFixed(2)}T`
            : params.data.value >= 1e9
            ? `$${(params.data.value / 1e9).toFixed(1)}B`
            : `$${(params.data.value / 1e6).toFixed(0)}M`;
          return `<div style="padding:10px;min-width:180px">
            <div style="font-weight:bold;font-size:16px;margin-bottom:2px;">${params.name}</div>
            <div style="color:#aaa;font-size:12px;margin-bottom:8px;">${params.data.fullName ?? ""}</div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="color:#888">Price:</span><span style="font-weight:bold">$${params.data.price?.toFixed(2)}</span></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="color:#888">Change:</span><span style="color:${color};font-weight:bold">${sign}${params.data.changePct?.toFixed(2)}%</span></div>
            <div style="display:flex;justify-content:space-between"><span style="color:#888">Mkt Cap:</span><span>${cap}</span></div>
          </div>`;
        },
      },
      series: [
        {
          type: "treemap",
          data: treeData,
          width: "100%",
          height: "100%",
          roam: "move",
          nodeClick: "zoomToNode",
          breadcrumb: {
            show: true,
            top: 5,
            left: "center",
            itemStyle: { color: "#1a1a2e", borderColor: "#444" },
            textStyle: { color: "#fff", fontSize: 12 },
          },
          label: {
            show: true,
            position: "insideTopLeft",
            formatter: (params: any) => {
              if (params.data?.children) return `{sector|${params.name}}`;
              const sign = params.data.changePct >= 0 ? "+" : "";
              return `{symbol|${params.name}}\n{change|${sign}${params.data.changePct?.toFixed(1)}%}`;
            },
            rich: {
              sector: { fontSize: 13, fontWeight: "bold", color: "#fff", padding: [4, 0, 0, 4] },
              symbol: { fontSize: 11, fontWeight: "bold", color: "#fff", lineHeight: 16 },
              change:  { fontSize: 10, color: "rgba(255,255,255,0.85)", lineHeight: 14 },
            },
          },
          upperLabel: {
            show: true,
            height: 28,
            color: "#fff",
            backgroundColor: "rgba(0,0,0,0.5)",
          },
          itemStyle: {
            borderColor: "#0d0a24",
            borderWidth: 1,
            gapWidth: 1,
          },
          levels: [
            {
              itemStyle: { borderColor: "#333", borderWidth: 2, gapWidth: 2 },
              upperLabel: { show: true },
            },
            {
              itemStyle: { borderColor: "#222", borderWidth: 1, gapWidth: 1 },
              colorSaturation: [0.6, 0.9],
            },
          ],
          emphasis: {
            itemStyle: {
              borderColor: selectedTicker ? "#00F5FF" : "#fff",
              borderWidth: 2,
            },
          },
        },
      ],
    } as any;

    chart.setOption(option, true);

    // Force resize so the chart fills the container after setOption
    requestAnimationFrame(() => chart.resize());

  }, [data, selectedTicker, isMobile]);

  // Click handler — bridge echarts click to onSelectTicker
  useEffect(() => {
    const chart = chartInstanceRef.current;
    if (!chart) return;
    const handler = (params: any) => {
      if (params.data && !params.data.children && params.name) {
        onSelectTicker(params.name);
      }
    };
    chart.on("click", handler);
    return () => { chart.off("click", handler); };
  }, [onSelectTicker]);

  // Resize observer
  useEffect(() => {
    if (!chartRef.current) return;
    const ro = new ResizeObserver(() => chartInstanceRef.current?.resize());
    ro.observe(chartRef.current);
    return () => ro.disconnect();
  }, []);

  // Dispose on unmount
  useEffect(() => {
    return () => {
      chartInstanceRef.current?.dispose();
      chartInstanceRef.current = null;
    };
  }, []);

  if (isMobile) {
    return (
      <MobileMarketList data={data} selectedTicker={selectedTicker} onSelectTicker={onSelectTicker} />
    );
  }

  if (data.length === 0) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", border: "1px dashed rgba(124,58,237,0.2)", borderRadius: "12px", p: 6 }}>
        <Typography sx={{ color: "rgba(107,96,168,0.5)", fontFamily: '"Inter", sans-serif', fontSize: "0.8rem" }}>
          No market data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        background: "rgba(13,10,36,0.55)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(124,58,237,0.22)",
        borderRadius: "18px",
        p: 2,
        transition: "border-color 0.3s ease",
        "&:hover": { borderColor: "rgba(0,245,255,0.25)" },
      }}
    >
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5, px: 0.5 }}>
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box sx={{ width: 3, height: 18, borderRadius: "2px", background: "linear-gradient(180deg, #7C3AED, #00F5FF)", boxShadow: "0 0 8px rgba(124,58,237,0.7)", flexShrink: 0 }} />
            <Typography sx={{ fontFamily: '"Inter", sans-serif', fontWeight: 800, fontSize: "0.85rem", letterSpacing: "-0.01em", background: "linear-gradient(90deg, #F0EEFF, #BF5AF2)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
              S&amp;P 500 Market Treemap
            </Typography>
          </Box>
          <Typography sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.62rem", color: "rgba(107,96,168,0.65)", mt: 0.3, pl: "19px" }}>
            Click any cell to inspect · Click sector to zoom in
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip label={`${gainers} Gainers`} size="small" sx={{ bgcolor: "rgba(0,200,83,0.12)", color: "#00E676", border: "1px solid rgba(0,200,83,0.25)", fontFamily: '"Inter", sans-serif', fontSize: "0.65rem", height: 22 }} />
          <Chip label={`${losers} Losers`} size="small" sx={{ bgcolor: "rgba(244,67,54,0.12)", color: "#FF5252", border: "1px solid rgba(244,67,54,0.25)", fontFamily: '"Inter", sans-serif', fontSize: "0.65rem", height: 22 }} />
        </Stack>
      </Stack>

      {/* Chart */}
      <Box ref={chartRef} sx={{ width: "100%", height, borderRadius: "12px", overflow: "hidden" }} />

      {/* Colour scale bar */}
      <Box sx={{ mt: 1.5, px: 0.5 }}>
        <Box sx={{ height: 5, borderRadius: "3px", background: "linear-gradient(to right, #D32F2F 0%, #F44336 25%, #2E7D32 50%, #69F0AE 75%, #00C853 100%)", boxShadow: "0 0 12px rgba(0,0,0,0.4)" }} />
        <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
          {["-3%+", "-2%", "-1%", "0%", "+1%", "+2%", "+3%+"].map((label) => (
            <Typography key={label} sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.55rem", color: "rgba(107,96,168,0.55)" }}>
              {label}
            </Typography>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
