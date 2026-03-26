import { Outlet } from "react-router-dom";
import Box from "@mui/material/Box";
import Sidebar from "./Sidebar";

const DRAWER_WIDTH = 220;

export default function Layout() {
  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
      <Sidebar />
      <Box
        component="main"
        sx={{
          ml: `${DRAWER_WIDTH}px`,
          flex: 1,
          overflow: 'auto',
          p: { xs: 2, sm: 3 },
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
