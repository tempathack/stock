import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import PsychologyIcon from "@mui/icons-material/Psychology";
import WaterDropIcon  from "@mui/icons-material/WaterDrop";
import HistoryIcon    from "@mui/icons-material/History";
import InsightsIcon   from "@mui/icons-material/Insights";
import { useK8sHealth, useHealthCheck, useModelDrift } from "@/api";

const navItems = [
  { to: "/dashboard", label: "Dashboard",  Icon: DashboardIcon   },
  { to: "/models",    label: "Models",      Icon: PsychologyIcon  },
  { to: "/forecasts", label: "Forecasts",   Icon: TrendingUpIcon  },
  { to: "/drift",     label: "Drift",       Icon: WaterDropIcon   },
  { to: "/backtest",  label: "Backtest",    Icon: HistoryIcon     },
  { to: "/analytics", label: "Analytics",   Icon: InsightsIcon    },
];

type DotColor = "success" | "warning" | "error";

const DOT_COLORS: Record<DotColor, { color: string; glow: string }> = {
  success: { color: "#00FF87", glow: "rgba(0, 255, 135, 0.6)" },
  warning: { color: "#FFD60A", glow: "rgba(255, 214, 10, 0.6)" },
  error:   { color: "#FF2D78", glow: "rgba(255, 45, 120, 0.6)" },
};

function StatusDot({ label, color }: { label: string; color: DotColor }) {
  const { color: c, glow } = DOT_COLORS[color];
  return (
    <Stack direction="row" spacing={0.75} alignItems="center">
      <Box
        sx={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          bgcolor: c,
          boxShadow: `0 0 6px ${glow}, 0 0 12px ${glow}`,
          animation: color !== "success" ? "pulse-dot 2s ease-in-out infinite" : "none",
          "@keyframes pulse-dot": {
            "0%, 100%": { opacity: 1, boxShadow: `0 0 6px ${glow}` },
            "50%":       { opacity: 0.4, boxShadow: `0 0 2px ${glow}` },
          },
          flexShrink: 0,
        }}
      />
      <Typography
        variant="caption"
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontWeight: 600,
          fontSize: "0.6rem",
          letterSpacing: "0.08em",
          color: color === "success" ? "rgba(240,238,255,0.45)" : c,
          textShadow: color !== "success" ? `0 0 8px ${glow}` : "none",
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
        height: 60,
        flexShrink: 0,
        background: "rgba(7, 4, 26, 0.85)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderBottom: "1px solid rgba(124, 58, 237, 0.2)",
        boxShadow: "0 1px 0 rgba(124, 58, 237, 0.1), 0 4px 32px rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        px: 2.5,
        gap: 3,
        zIndex: (t) => t.zIndex.appBar,
        position: "relative",
      }}
    >
      {/* Logo */}
      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ flexShrink: 0 }}>
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: "10px",
            background: "linear-gradient(135deg, #7C3AED 0%, #EC4899 50%, #00F5FF 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.62rem",
            fontWeight: 800,
            color: "#fff",
            fontFamily: '"Inter", sans-serif',
            letterSpacing: "-0.02em",
            flexShrink: 0,
            boxShadow: "0 0 20px rgba(124, 58, 237, 0.6), 0 0 40px rgba(124, 58, 237, 0.2)",
            animation: "neon-flicker 8s ease-in-out infinite",
            "@keyframes neon-flicker": {
              "0%, 100%": { opacity: 1 },
              "92%": { opacity: 1 },
              "93%": { opacity: 0.85 },
              "94%": { opacity: 1 },
            },
          }}
        >
          SP
        </Box>
        <Box>
          <Typography
            sx={{
              fontFamily: '"Inter", sans-serif',
              fontWeight: 800,
              fontSize: "0.88rem",
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              background: "linear-gradient(90deg, #BF5AF2, #00F5FF)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              whiteSpace: "nowrap",
            }}
          >
            S&P 500 AI
          </Typography>
          <Typography
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.52rem",
              letterSpacing: "0.12em",
              color: "rgba(107, 96, 168, 0.8)",
              textTransform: "uppercase",
              lineHeight: 1,
            }}
          >
            Platform
          </Typography>
        </Box>
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
                color: isActive ? "#F0EEFF" : "#4A4270",
                position: "relative",
                transition: "color 0.2s ease",
                "&::after": isActive ? {
                  content: '""',
                  position: "absolute",
                  bottom: 0,
                  left: "50%",
                  transform: "translateX(-50%)",
                  width: "60%",
                  height: "2px",
                  background: "linear-gradient(90deg, #7C3AED, #00F5FF)",
                  borderRadius: "2px 2px 0 0",
                  boxShadow: "0 0 8px rgba(0, 245, 255, 0.6)",
                } : {},
                "&::before": isActive ? {
                  content: '""',
                  position: "absolute",
                  inset: "8px 4px",
                  background: "linear-gradient(135deg, rgba(124,58,237,0.12), rgba(0,245,255,0.06))",
                  borderRadius: "8px",
                  border: "1px solid rgba(124,58,237,0.2)",
                } : {},
                "&:hover": {
                  color: isActive ? "#F0EEFF" : "#9D8FD8",
                },
              }}
            >
              <Icon
                sx={{
                  fontSize: "0.95rem",
                  opacity: isActive ? 1 : 0.5,
                  color: isActive ? "#BF5AF2" : "inherit",
                  filter: isActive ? "drop-shadow(0 0 4px rgba(191,90,242,0.7))" : "none",
                  zIndex: 1,
                }}
              />
              <Typography
                sx={{
                  fontFamily: '"Inter", sans-serif',
                  fontWeight: isActive ? 700 : 400,
                  fontSize: "0.78rem",
                  letterSpacing: "0.01em",
                  whiteSpace: "nowrap",
                  zIndex: 1,
                  textShadow: isActive ? "0 0 12px rgba(191,90,242,0.4)" : "none",
                }}
              >
                {label}
              </Typography>
            </Box>
          );
        })}
      </Stack>

      {/* Right: K8s + status dots + clock */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ flexShrink: 0 }}>
        {k8s?.available && k8s.running_pods != null && (
          <Stack direction="row" spacing={0.6} alignItems="center"
            sx={{
              px: 1.25,
              py: 0.4,
              borderRadius: "6px",
              background: "rgba(0,255,135,0.06)",
              border: "1px solid rgba(0,255,135,0.15)",
            }}
          >
            <Box
              sx={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                bgcolor: "#00FF87",
                boxShadow: "0 0 6px rgba(0,255,135,0.8)",
                flexShrink: 0,
              }}
            />
            <Typography
              sx={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: "0.62rem",
                color: "rgba(0,255,135,0.7)",
                whiteSpace: "nowrap",
              }}
            >
              {k8s.running_pods} pods
            </Typography>
          </Stack>
        )}

        <Stack direction="row" spacing={1.5} alignItems="center"
          sx={{
            px: 1.5,
            py: 0.5,
            borderRadius: "8px",
            background: "rgba(13,10,36,0.6)",
            border: "1px solid rgba(124,58,237,0.15)",
          }}
        >
          <StatusDot label="API"   color={apiColor}   />
          <StatusDot label="KAFKA" color={kafkaColor} />
          <StatusDot label="DB"    color={dbColor}    />
        </Stack>

        {clock && (
          <Typography
            variant="caption"
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.68rem",
              fontWeight: 600,
              background: "linear-gradient(90deg, #7C3AED, #00F5FF)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              whiteSpace: "nowrap",
              letterSpacing: "0.05em",
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
