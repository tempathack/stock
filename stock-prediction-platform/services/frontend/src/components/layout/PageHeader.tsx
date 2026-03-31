import type { ReactNode } from "react";
import { Box, Typography } from "@mui/material";

interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
}

export default function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5, mb: 0.75 }}>
        {/* Sky blue accent mark */}
        <Box
          sx={{
            width: 3,
            height: 24,
            borderRadius: "2px",
            bgcolor: "#0EA5E9",
            boxShadow: "0 0 10px rgba(14, 165, 233, 0.5)",
            flexShrink: 0,
            alignSelf: "center",
          }}
        />
        <Typography
          variant="h4"
          sx={{
            fontFamily: '"IBM Plex Sans", sans-serif',
            fontWeight: 700,
            fontSize: { xs: "1.4rem", sm: "1.75rem" },
            letterSpacing: "-0.02em",
            color: "#E2E8F0",
          }}
        >
          {title}
        </Typography>
      </Box>

      {subtitle && (
        <Box sx={{ pl: "19px" }}>
          <Typography
            variant="body2"
            sx={{
              color: "rgba(100,116,139,0.8)",
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

      {/* Subtle ruled line */}
      <Box
        sx={{
          mt: 2,
          height: "1px",
          background:
            "linear-gradient(to right, rgba(14,165,233,0.35) 0%, rgba(14,165,233,0.08) 40%, transparent 100%)",
        }}
      />
    </Box>
  );
}
