import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { Box, Chip, Stack, Typography } from "@mui/material";
import type { TreemapSectorGroup } from "@/api";
import { changePctToColor } from "@/utils/dashboardUtils";
import MobileMarketList from "./MobileMarketList";

interface MarketTreemapProps {
  data: TreemapSectorGroup[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
  height?: number;
}

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
  height = 580,
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
        itemStyle: { color: changePctToColor(stock.dailyChangePct) },
      })),
    }));

    const option = {
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: "rgba(13,10,36,0.97)",
        borderColor: "rgba(124,58,237,0.5)",
        borderWidth: 1,
        padding: 0,
        textStyle: { color: "#F0EEFF", fontFamily: "Inter, sans-serif" },
        formatter: (params: any) => {
          if (params.data?.children) {
            return `<div style="padding:10px 14px">
              <div style="font-weight:800;font-size:13px;color:#F0EEFF;letter-spacing:0.05em">${params.name.toUpperCase()}</div>
              <div style="font-size:11px;color:#6B60A8;margin-top:3px">${params.data.children.length} stocks</div>
            </div>`;
          }
          const pct = params.data.changePct ?? 0;
          const sign = pct >= 0 ? "+" : "";
          const pctColor = pct >= 0 ? "#00E5FF" : "#BF5AF2";
          const borderAccent = pct >= 0 ? "rgba(0,229,255,0.4)" : "rgba(191,90,242,0.4)";
          const cap = params.data.value >= 1e12
            ? `$${(params.data.value / 1e12).toFixed(2)}T`
            : params.data.value >= 1e9
            ? `$${(params.data.value / 1e9).toFixed(1)}B`
            : `$${(params.data.value / 1e6).toFixed(0)}M`;
          return `<div style="padding:12px 14px;min-width:180px;border-left:3px solid ${borderAccent}">
            <div style="font-weight:800;font-size:15px;color:#F0EEFF;letter-spacing:0.06em">${params.name}</div>
            <div style="font-size:11px;color:#6B60A8;margin-bottom:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px">${params.data.fullName ?? ""}</div>
            <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:5px">
              <span style="color:#6B60A8;font-size:11px">Price</span>
              <span style="color:#F0EEFF;font-weight:600;font-size:12px">$${params.data.price?.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:5px">
              <span style="color:#6B60A8;font-size:11px">Change</span>
              <span style="color:${pctColor};font-weight:700;font-size:13px;text-shadow:0 0 8px ${pctColor}55">${sign}${pct.toFixed(2)}%</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:16px">
              <span style="color:#6B60A8;font-size:11px">Mkt Cap</span>
              <span style="color:#F0EEFF;font-size:11px">${cap}</span>
            </div>
          </div>`;
        },
      },
      series: [
        {
          type: "treemap",
          data: treeData,
          left: 0,
          right: 0,
          top: 30,    // leave room for breadcrumb
          bottom: 0,
          roam: "move",
          nodeClick: "zoomToNode",
          breadcrumb: {
            show: true,
            top: 0,
            left: "center",
            height: 26,
            itemStyle: {
              color: "rgba(13,10,36,0.95)",
              borderColor: "rgba(124,58,237,0.35)",
              borderWidth: 1,
            },
            textStyle: {
              color: "#BF5AF2",
              fontSize: 11,
              fontWeight: "bold",
              fontFamily: "Inter, sans-serif",
            },
          },
          // Stock tile labels — rich text works correctly here
          label: {
            show: true,
            position: "insideTopLeft",
            formatter: (params: any) => {
              // Sector nodes: label hidden behind children tiles, only upperLabel matters
              if (params.data?.children) return params.name;
              const sign = params.data.changePct >= 0 ? "+" : "";
              return `{sym|${params.name}}\n{chg|${sign}${params.data.changePct?.toFixed(1)}%}`;
            },
            rich: {
              sym: {
                fontSize: 11,
                fontWeight: "bold",
                color: "rgba(240,238,255,0.95)",
                lineHeight: 16,
                fontFamily: "Inter, sans-serif",
              },
              chg: {
                fontSize: 10,
                color: "rgba(240,238,255,0.72)",
                lineHeight: 14,
                fontFamily: "Inter, sans-serif",
              },
            },
          },
          // Sector group header bar — plain text, no rich text inheritance
          upperLabel: {
            show: true,
            height: 22,
            formatter: (params: any) => params.name.toUpperCase(),
            color: "#BF5AF2",
            fontSize: 10,
            fontWeight: "bold",
            fontFamily: "Inter, sans-serif",
            backgroundColor: "rgba(13,10,36,0.85)",
          },
          itemStyle: {
            borderColor: "rgba(13,10,36,0.9)",
            borderWidth: 1,
            gapWidth: 1,
          },
          levels: [
            {
              // Sector level
              itemStyle: {
                borderColor: "rgba(124,58,237,0.45)",
                borderWidth: 2,
                gapWidth: 2,
              },
              upperLabel: {
                show: true,
                height: 22,
                formatter: (params: any) => params.name.toUpperCase(),
                color: "#BF5AF2",
                fontSize: 10,
                fontWeight: "bold",
                fontFamily: "Inter, sans-serif",
                backgroundColor: "rgba(13,10,36,0.85)",
              },
            },
            {
              // Stock tile level
              itemStyle: {
                borderColor: "rgba(13,10,36,0.8)",
                borderWidth: 1,
                gapWidth: 1,
              },
            },
          ],
          emphasis: {
            itemStyle: {
              borderColor: "#00F5FF",
              borderWidth: 2,
              shadowBlur: 10,
              shadowColor: "rgba(0,245,255,0.35)",
            },
          },
        },
      ],
    } as any;

    chart.setOption(option, true);
    requestAnimationFrame(() => chart.resize());

  }, [data, selectedTicker, isMobile]);

  // Bridge echarts click → onSelectTicker
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

  // ResizeObserver keeps canvas in sync with container
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
        transition: "border-color 0.3s ease, box-shadow 0.3s ease",
        "&:hover": {
          borderColor: "rgba(0,245,255,0.25)",
          boxShadow: "0 0 24px rgba(124,58,237,0.08)",
        },
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
          <Chip
            label={`${gainers} Gainers`}
            size="small"
            sx={{ bgcolor: "rgba(0,194,212,0.10)", color: "#00C2D4", border: "1px solid rgba(0,194,212,0.28)", fontFamily: '"Inter", sans-serif', fontSize: "0.65rem", height: 22 }}
          />
          <Chip
            label={`${losers} Losers`}
            size="small"
            sx={{ bgcolor: "rgba(139,47,201,0.10)", color: "#BF5AF2", border: "1px solid rgba(139,47,201,0.28)", fontFamily: '"Inter", sans-serif', fontSize: "0.65rem", height: 22 }}
          />
        </Stack>
      </Stack>

      {/* Chart canvas */}
      <Box
        ref={chartRef}
        sx={{ width: "100%", height, borderRadius: "10px", overflow: "hidden" }}
      />

      {/* Colour legend */}
      <Box sx={{ mt: 1.5, px: 0.5 }}>
        <Box sx={{
          height: 4,
          borderRadius: "3px",
          background: "linear-gradient(to right, #8B2FC9 0%, #3D1A6B 30%, #110C2E 50%, #0A3040 70%, #00C2D4 100%)",
          opacity: 0.85,
        }} />
        <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
          {["-3%+", "-2%", "-1%", "0%", "+1%", "+2%", "+3%+"].map((label) => (
            <Typography key={label} sx={{ fontFamily: '"Inter", sans-serif', fontSize: "0.52rem", color: "rgba(107,96,168,0.5)" }}>
              {label}
            </Typography>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
