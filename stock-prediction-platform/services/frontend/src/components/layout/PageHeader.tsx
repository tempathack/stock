import type { ReactNode } from "react";
import { Box, Typography } from "@mui/material";

interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
}

export default function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 0.75 }}>
        {/* Neon gradient accent bar */}
        <Box
          sx={{
            width: 4,
            height: 28,
            borderRadius: "3px",
            background: "linear-gradient(180deg, #7C3AED 0%, #00F5FF 100%)",
            boxShadow: "0 0 12px rgba(124,58,237,0.7), 0 0 24px rgba(0,245,255,0.3)",
            flexShrink: 0,
          }}
        />
        <Typography
          variant="h4"
          sx={{
            fontFamily: '"Inter", sans-serif',
            fontWeight: 800,
            fontSize: { xs: "1.4rem", sm: "1.75rem" },
            letterSpacing: "-0.03em",
            background: "linear-gradient(90deg, #F0EEFF 0%, #BF5AF2 50%, #00F5FF 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          {title}
        </Typography>
      </Box>

      {subtitle && (
        <Box sx={{ pl: "21px" }}>
          <Typography
            variant="body2"
            sx={{
              color: "rgba(107,96,168,0.8)",
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: "0.72rem",
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            {subtitle}
          </Typography>
        </Box>
      )}

      {/* Gradient ruled line */}
      <Box
        sx={{
          mt: 2,
          height: "1px",
          background:
            "linear-gradient(to right, rgba(124,58,237,0.6) 0%, rgba(0,245,255,0.3) 30%, rgba(236,72,153,0.1) 60%, transparent 100%)",
        }}
      />
    </Box>
  );
}
