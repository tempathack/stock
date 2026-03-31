import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import BarChartIcon from "@mui/icons-material/BarChart";
import BubbleChartIcon from "@mui/icons-material/BubbleChart";
import SsidChartIcon from "@mui/icons-material/SsidChart";
import { useK8sHealth, useHealthCheck, useModelDrift } from "@/api";

const navItems = [
  { to: "/dashboard", label: "Dashboard",  Icon: DashboardIcon  },
  { to: "/models",    label: "Models",      Icon: AccountTreeIcon },
  { to: "/forecasts", label: "Forecasts",   Icon: TrendingUpIcon  },
  { to: "/drift",     label: "Drift",       Icon: BubbleChartIcon },
  { to: "/backtest",  label: "Backtest",    Icon: SsidChartIcon   },
  { to: "/analytics", label: "Analytics",   Icon: BarChartIcon    },
];

type DotColor = "success" | "warning" | "error";

const DOT_COLORS: Record<DotColor, string> = {
  success: "#10B981",
  warning: "#F59E0B",
  error:   "#F43F5E",
};

function StatusDot({ label, color }: { label: string; color: DotColor }) {
  const c = DOT_COLORS[color];
  return (
    <Stack direction="row" spacing={0.6} alignItems="center">
      <Box
        sx={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          bgcolor: c,
          boxShadow: `0 0 ${color === "success" ? 4 : 8}px ${c}`,
          animation: color !== "success"
            ? "pulse-dot 2s ease-in-out infinite"
            : "none",
          "@keyframes pulse-dot": {
            "0%, 100%": { opacity: 1 },
            "50%":       { opacity: 0.4 },
          },
          flexShrink: 0,
        }}
      />
      <Typography
        variant="caption"
        sx={{
          fontFamily: '"IBM Plex Sans", sans-serif',
          fontWeight: 600,
          fontSize: "0.62rem",
          letterSpacing: "0.06em",
          color: color === "success" ? "rgba(226,232,240,0.5)" : c,
        }}
      >
        {label}
      </Typography>
    </Stack>
  );
}

function TopNav() {
  const location = useLocation();
  const { data: k8s } = useK8sHealth();
  const healthQuery = useHealthCheck();
  const driftQuery  = useModelDrift();
  const [clock, setClock] = useState<string>("");

  useEffect(() => {
    const tick = () =>
      setClock(
        new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      );
    tick();
    const id = setInterval(tick, 1_000);
    return () => clearInterval(id);
  }, []);

  const apiColor: DotColor   = !healthQuery.isError && healthQuery.data != null ? "success" : "error";
  const dbColor: DotColor    = healthQuery.data?.status === "ok" ? "success" : "error";
  const kafkaColor: DotColor = (() => {
    if (driftQuery.isError) return "error";
    const latest = driftQuery.data?.latest_event;
    if (!latest?.timestamp) return "warning";
    const ageMs = Date.now() - new Date(latest.timestamp).getTime();
    return ageMs > 3_600_000 ? "warning" : "success";
  })();

  return (
    <Box
      component="header"
      sx={{
        height: 56,
        flexShrink: 0,
        bgcolor: "#060C1A",
        borderBottom: "1px solid rgba(14, 165, 233, 0.15)",
        display: "flex",
        alignItems: "center",
        px: 2.5,
        gap: 3,
        zIndex: (t) => t.zIndex.appBar,
      }}
    >
      {/* Logo */}
      <Stack direction="row" spacing={1.25} alignItems="center" sx={{ flexShrink: 0 }}>
        <Box
          sx={{
            width: 28,
            height: 28,
            borderRadius: "6px",
            background: "linear-gradient(135deg, #0EA5E9 0%, #8B5CF6 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.58rem",
            fontWeight: 700,
            color: "#050A14",
            fontFamily: '"IBM Plex Sans", sans-serif',
            letterSpacing: "-0.01em",
            flexShrink: 0,
            boxShadow: "0 2px 12px rgba(14, 165, 233, 0.35)",
          }}
        >
          SP
        </Box>
        <Typography
          sx={{
            fontFamily: '"IBM Plex Sans", sans-serif',
            fontWeight: 700,
            fontSize: "0.82rem",
            letterSpacing: "0.02em",
            color: "#E2E8F0",
            lineHeight: 1.2,
            whiteSpace: "nowrap",
          }}
        >
          S&amp;P 500 AI
        </Typography>
      </Stack>

      {/* Nav links */}
      <Stack
        component="nav"
        direction="row"
        spacing={0}
        alignItems="stretch"
        sx={{ flex: 1, height: "100%" }}
      >
        {navItems.map(({ to, label, Icon }) => {
          const isActive =
            location.pathname === to ||
            location.pathname.startsWith(to + "/");

          return (
            <Box
              key={to}
              component={NavLink}
              to={to}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.75,
                px: 1.5,
                height: "100%",
                textDecoration: "none",
                color: isActive ? "#E2E8F0" : "#64748B",
                borderBottom: isActive
                  ? "2px solid #0EA5E9"
                  : "2px solid transparent",
                transition: "color 0.15s ease, border-color 0.15s ease",
                "&:hover": {
                  color: isActive ? "#E2E8F0" : "#94A3B8",
                },
              }}
            >
              <Icon sx={{ fontSize: "0.9rem", opacity: isActive ? 1 : 0.7 }} />
              <Typography
                sx={{
                  fontFamily: '"IBM Plex Sans", sans-serif',
                  fontWeight: isActive ? 600 : 400,
                  fontSize: "0.78rem",
                  letterSpacing: "0.01em",
                  whiteSpace: "nowrap",
                }}
              >
                {label}
              </Typography>
            </Box>
          );
        })}
      </Stack>

      {/* Right: K8s status + service dots + clock */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ flexShrink: 0 }}>
        {/* K8s cluster pod count */}
        {k8s?.available && k8s.running_pods != null && (
          <Stack direction="row" spacing={0.6} alignItems="center">
            <Box
              sx={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                bgcolor: "#10B981",
                boxShadow: "0 0 4px #10B981",
                flexShrink: 0,
              }}
            />
            <Typography
              sx={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: "0.65rem",
                color: "rgba(100,116,139,0.8)",
                whiteSpace: "nowrap",
              }}
            >
              {k8s.running_pods} pods
            </Typography>
          </Stack>
        )}

        {/* Service status dots */}
        <StatusDot label="API"   color={apiColor}   />
        <StatusDot label="KAFKA" color={kafkaColor} />
        <StatusDot label="DB"    color={dbColor}    />

        {/* Live clock */}
        {clock && (
          <Typography
            variant="caption"
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              color: "rgba(100,116,139,0.7)",
              fontSize: "0.65rem",
              borderLeft: "1px solid rgba(14,165,233,0.15)",
              pl: 2,
              whiteSpace: "nowrap",
            }}
          >
            {clock}
          </Typography>
        )}
      </Stack>
    </Box>
  );
}

export default TopNav;
