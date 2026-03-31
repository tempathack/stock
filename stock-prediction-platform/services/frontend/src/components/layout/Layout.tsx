import { Outlet } from "react-router-dom";
import Box from "@mui/material/Box";
import TopNav from "./Sidebar";

export default function Layout() {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
        bgcolor: "background.default",
      }}
    >
      <TopNav />
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
  );
}
