import { NavLink, useLocation } from "react-router-dom";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import BubbleChartIcon from "@mui/icons-material/BubbleChart";
import SsidChartIcon from "@mui/icons-material/SsidChart";
import { useK8sHealth } from "@/api";

const DRAWER_WIDTH = 220;

const navItems = [
  { to: "/dashboard", label: "Dashboard", Icon: DashboardIcon },
  { to: "/models", label: "Models", Icon: AccountTreeIcon },
  { to: "/forecasts", label: "Forecasts", Icon: TrendingUpIcon },
  { to: "/drift", label: "Drift", Icon: BubbleChartIcon },
  { to: "/backtest", label: "Backtest", Icon: SsidChartIcon },
];

export default function Sidebar() {
  const location = useLocation();
  const { data: k8s } = useK8sHealth();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          bgcolor: 'background.paper',
          borderRight: '1px solid rgba(0,188,212,0.12)',
        },
      }}
    >
      <Toolbar sx={{ minHeight: 56, px: 2 }}>
        <Typography
          variant="h6"
          sx={{ color: 'primary.main', fontWeight: 700, letterSpacing: '0.05em' }}
        >
          S&P 500 AI
        </Typography>
      </Toolbar>
      <Divider sx={{ borderColor: 'rgba(0,188,212,0.12)' }} />

      <List sx={{ flex: 1, py: 1 }}>
        {navItems.map(({ to, label, Icon }) => {
          const isActive = location.pathname === to || location.pathname.startsWith(to + '/');
          return (
            <ListItemButton
              key={to}
              component={NavLink}
              to={to}
              sx={{
                mx: 1,
                borderRadius: 1,
                mb: 0.5,
                borderLeft: isActive ? '2px solid' : '2px solid transparent',
                borderColor: isActive ? 'primary.main' : 'transparent',
                bgcolor: isActive ? 'rgba(0,188,212,0.08)' : 'transparent',
                '&:hover': { bgcolor: 'rgba(0,188,212,0.05)' },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: isActive ? 'primary.main' : 'text.secondary' }}>
                <Icon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={label}
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'primary.main' : 'text.secondary',
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      <Divider sx={{ borderColor: 'rgba(0,188,212,0.12)' }} />

      {/* K8s health mini-panel — only shown when kubectl is reachable */}
      {k8s?.available && k8s.running_pods != null && (
        <Box sx={{ px: 2, py: 1, borderBottom: '1px solid rgba(0,188,212,0.12)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
            <Box
              sx={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                bgcolor: 'success.main',
                flexShrink: 0,
              }}
            />
            <Typography variant="caption" color="text.secondary" noWrap>
              {k8s.running_pods} pods running
            </Typography>
          </Box>
          {k8s.namespaces && k8s.namespaces.length > 0 && (
            <Typography
              variant="caption"
              color="text.disabled"
              sx={{ fontSize: '0.6rem', display: 'block', mt: 0.25 }}
              noWrap
            >
              {k8s.namespaces.slice(0, 4).join(', ')}
              {k8s.namespaces.length > 4 ? '…' : ''}
            </Typography>
          )}
        </Box>
      )}
    </Drawer>
  );
}
