import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import CircleIcon from "@mui/icons-material/Circle";
import Sidebar from "./Sidebar";
import { useHealthCheck, useModelDrift } from "@/api";

const DRAWER_WIDTH = 220;

function ConnectionStatusBar() {
  const healthQuery = useHealthCheck();
  const driftQuery = useModelDrift();
  const [lastUpdate, setLastUpdate] = useState<string>("");

  useEffect(() => {
    const update = () =>
      setLastUpdate(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    update();
    const id = setInterval(update, 1_000);
    return () => clearInterval(id);
  }, []);

  // API: up if health query succeeds
  const apiUp = !healthQuery.isError && healthQuery.data != null;

  // DB: ok if health status === "ok"
  const dbUp = healthQuery.data?.status === "ok";

  // Kafka: inferred from drift data freshness — warn if latest event > 1h old or no data
  const kafkaColor = (() => {
    if (driftQuery.isError) return "error" as const;
    const latest = driftQuery.data?.latest_event;
    if (!latest?.timestamp) return "warning" as const;
    const ageMs = Date.now() - new Date(latest.timestamp).getTime();
    if (ageMs > 3_600_000) return "warning" as const;
    return "success" as const;
  })();

  const dotSx = { fontSize: "8px !important" };

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: "background.paper",
        borderBottom: "1px solid rgba(0,188,212,0.12)",
        zIndex: (t) => t.zIndex.drawer - 1,
      }}
    >
      <Toolbar variant="dense" sx={{ justifyContent: "space-between", minHeight: 40 }}>
        <Typography
          variant="subtitle2"
          sx={{ color: "primary.main", fontWeight: 700, letterSpacing: "0.05em", fontSize: "0.75rem" }}
        >
          S&amp;P 500 AI Platform
        </Typography>

        <Stack direction="row" spacing={1} alignItems="center">
          <Chip
            size="small"
            icon={<CircleIcon sx={dotSx} />}
            label="API"
            color={apiUp ? "success" : "error"}
            variant="outlined"
            sx={{ fontSize: "0.65rem", height: 20 }}
          />
          <Chip
            size="small"
            icon={<CircleIcon sx={dotSx} />}
            label="Kafka"
            color={kafkaColor}
            variant="outlined"
            sx={{ fontSize: "0.65rem", height: 20 }}
          />
          <Chip
            size="small"
            icon={<CircleIcon sx={dotSx} />}
            label="DB"
            color={dbUp ? "success" : "error"}
            variant="outlined"
            sx={{ fontSize: "0.65rem", height: 20 }}
          />
          {lastUpdate && (
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>
              {lastUpdate}
            </Typography>
          )}
        </Stack>
      </Toolbar>
    </AppBar>
  );
}

export default function Layout() {
  return (
    <Box sx={{ display: "flex", height: "100vh", overflow: "hidden", bgcolor: "background.default" }}>
      <Sidebar />
      <Box
        sx={{
          ml: `${DRAWER_WIDTH}px`,
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <ConnectionStatusBar />
        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: "auto",
            p: { xs: 2, sm: 3 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
