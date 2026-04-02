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

const getColorByChange = (pct: number): string => {
  // Purple (loss) → dark navy (neutral) → cyan (gain)
  if (pct >= 3)  return "#00C2D4";
  if (pct >= 2)  return "#0097A7";
  if (pct >= 1)  return "#00838F";
  if (pct >= 0)  return "#1A3A4A";
  if (pct >= -1) return "#2A1A4A";
  if (pct >= -2) return "#5B2490";
  return "#8B2FC9";
};

export default function MarketTreemap({
  data,
  selectedTicker,
  onSelectTicker,
  height = 560,
}: MarketTreemapProps) {
  const isMobile = useIsMobile();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current, "dark");
    }
    const chart = chartInstanceRef.current;

    const treeData = data.map((group) => ({
      name: group.name,
      children: group.children.map((stock) => ({
        name: stock.ticker,
        value: Math.max(stock.marketCap, 1_000_000_000),
        fullName: stock.name,
        price: stock.lastClose,
        changePct: stock.dailyChangePct,
        itemStyle: { color: getColorByChange(stock.dailyChangePct) },
      })),
    }));

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const option: any = {
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: "rgba(13,10,36,0.96)",
        borderColor: "rgba(124,58,237,0.4)",
        borderWidth: 1,
        textStyle: { color: "#F0EEFF", fontSize: 13, fontFamily: "Inter, sans-serif" },
        formatter: (params: any) => {
          if (params.data.children) {
            return `<div style="padding:8px 10px">
              <div style="font-weight:700;font-size:14px;color:#F0EEFF">${params.name}</div>
              <div style="color:#9B8FC0;font-size:11px;margin-top:2px">${params.data.children.length} stocks</div>
            </div>`;
          }
          const sign = params.data.changePct >= 0 ? "+" : "";
          const color = params.data.changePct >= 0 ? "#00E5FF" : "#BF5AF2";
          const cap = params.data.value >= 1e12
            ? `$${(params.data.value / 1e12).toFixed(2)}T`
            : params.data.value >= 1e9
            ? `$${(params.data.value / 1e9).toFixed(1)}B`
            : `$${(params.data.value / 1e6).toFixed(0)}M`;
          return `<div style="padding:10px 12px;min-width:180px;font-family:Inter,sans-serif">
            <div style="font-weight:700;font-size:16px;color:#F0EEFF;margin-bottom:2px">${params.name}</div>
            <div style="color:#9B8FC0;font-size:11px;margin-bottom:10px">${params.data.fullName || ""}</div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
              <span style="color:#6B60A8">Price</span>
              <span style="font-weight:600;color:#F0EEFF">$${params.data.price?.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
              <span style="color:#6B60A8">Change</span>
              <span style="font-weight:700;color:${color}">${sign}${params.data.changePct?.toFixed(2)}%</span>
            </div>
            <div style="display:flex;justify-content:space-between">
              <span style="color:#6B60A8">Market Cap</span>
              <span style="color:#F0EEFF">${cap}</span>
            </div>
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
            itemStyle: { color: "rgba(13,10,36,0.85)", borderColor: "rgba(124,58,237,0.4)" },
            textStyle: { color: "#BF5AF2", fontSize: 12, fontFamily: "Inter, sans-serif" },
          },
          label: {
            show: true,
            position: "insideTopLeft",
            formatter: (params: any) => {
              if (params.data.children) {
                return `{sector|${params.name}}`;
              }
              const sign = params.data.changePct >= 0 ? "+" : "";
              return `{symbol|${params.name}}\n{change|${sign}${params.data.changePct?.toFixed(1)}%}`;
            },
            rich: {
              sector: {
                fontSize: 13,
                fontWeight: "bold",
                color: "#F0EEFF",
                fontFamily: "Inter, sans-serif",
                padding: [4, 0, 0, 6],
              },
              symbol: {
                fontSize: 12,
                fontWeight: "700",
                color: "#FFFFFF",
                fontFamily: "Inter, sans-serif",
                lineHeight: 18,
              },
              change: {
                fontSize: 10,
                color: "rgba(255,255,255,0.75)",
                fontFamily: "Inter, sans-serif",
                lineHeight: 14,
              },
            },
          },
          upperLabel: {
            show: true,
            height: 28,
            color: "#F0EEFF",
            backgroundColor: "rgba(13,10,36,0.6)",
            fontFamily: "Inter, sans-serif",
            fontWeight: "bold",
          },
          itemStyle: {
            borderColor: "rgba(13,10,36,0.9)",
            borderWidth: 1,
            gapWidth: 1,
          },
          levels: [
            {
              itemStyle: {
                borderColor: "rgba(124,58,237,0.35)",
                borderWidth: 2,
                gapWidth: 2,
              },
              upperLabel: { show: true },
            },
            {
              itemStyle: {
                borderColor: "rgba(13,10,36,0.7)",
                borderWidth: 1,
                gapWidth: 1,
              },
              colorSaturation: [0.6, 0.9],
            },
          ],
          emphasis: {
            itemStyle: {
              borderColor: "#00F5FF",
              borderWidth: 2,
            },
          },
        },
      ],
    };

    chart.setOption(option);
    // Force resize after option set so echarts picks up container dimensions
    requestAnimationFrame(() => chart.resize());

    // Click to select ticker
    chart.off("click");
    chart.on("click", (params: any) => {
      if (params.data && !params.data.children && params.name) {
        onSelectTicker(params.name);
      }
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);

    // ResizeObserver so echarts tracks container size changes
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(chartRef.current!);

    return () => {
      window.removeEventListener("resize", handleResize);
      ro.disconnect();
    };
  }, [data, onSelectTicker]);

  // Highlight selected ticker by re-dispatching highlight action
  useEffect(() => {
    if (!chartInstanceRef.current || !selectedTicker) return;
    chartInstanceRef.current.dispatchAction({
      type: "highlight",
      name: selectedTicker,
    });
  }, [selectedTicker]);

  useEffect(() => {
    return () => {
      chartInstanceRef.current?.dispose();
    };
  }, []);

  if (isMobile) {
    return (
      <MobileMarketList
        data={data}
        selectedTicker={selectedTicker}
        onSelectTicker={onSelectTicker}
      />
    );
  }

  const gainers = data.flatMap((g) => g.children).filter((s) => s.dailyChangePct > 0).length;
  const losers  = data.flatMap((g) => g.children).filter((s) => s.dailyChangePct < 0).length;

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
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5, px: 0.5 }}>
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 3,
                height: 18,
                borderRadius: "2px",
                background: "linear-gradient(180deg, #7C3AED, #00F5FF)",
                boxShadow: "0 0 8px rgba(124,58,237,0.7)",
                flexShrink: 0,
              }}
            />
            <Typography
              sx={{
                fontFamily: '"Inter", sans-serif',
                fontWeight: 800,
                fontSize: "0.85rem",
                letterSpacing: "-0.01em",
                background: "linear-gradient(90deg, #F0EEFF, #BF5AF2)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              S&amp;P 500 Market Treemap
            </Typography>
          </Box>
          <Typography
            sx={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.62rem",
              color: "rgba(107,96,168,0.65)",
              mt: 0.3,
              pl: "19px",
            }}
          >
            Click to zoom · drag to pan · click stock to inspect
          </Typography>
        </Box>

        <Stack direction="row" spacing={1}>
          {data.length > 0 && (
            <>
              <Chip
                label={`${gainers} Gainers`}
                size="small"
                sx={{
                  bgcolor: "rgba(0,194,212,0.12)",
                  color: "#00C2D4",
                  border: "1px solid rgba(0,194,212,0.25)",
                  fontFamily: '"Inter", sans-serif',
                  fontSize: "0.65rem",
                  height: 22,
                }}
              />
              <Chip
                label={`${losers} Losers`}
                size="small"
                sx={{
                  bgcolor: "rgba(139,47,201,0.12)",
                  color: "#BF5AF2",
                  border: "1px solid rgba(139,47,201,0.25)",
                  fontFamily: '"Inter", sans-serif',
                  fontSize: "0.65rem",
                  height: 22,
                }}
              />
            </>
          )}
        </Stack>
      </Box>

      {data.length === 0 ? (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height,
            border: "1px dashed rgba(124,58,237,0.2)",
            borderRadius: "12px",
          }}
        >
          <Typography sx={{ color: "rgba(107,96,168,0.5)", fontFamily: '"Inter", sans-serif', fontSize: "0.8rem" }}>
            No market data available
          </Typography>
        </Box>
      ) : (
        <Box
          ref={chartRef}
          sx={{ width: "100%", height, borderRadius: "12px", overflow: "hidden" }}
        />
      )}
    </Box>
  );
}
