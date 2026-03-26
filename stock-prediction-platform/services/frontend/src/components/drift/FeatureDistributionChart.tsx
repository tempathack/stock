import { useMemo } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  Tooltip,
} from "recharts";
import type { FeatureDistribution } from "@/api";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, Chip, Grid, Typography } from "@mui/material";

interface FeatureDistributionChartProps {
  distributions: FeatureDistribution[];
}

const tooltipStyle = {
  backgroundColor: "#0f3460",
  border: "1px solid #2a2a4a",
  borderRadius: 6,
  color: "#e0e0e0",
  fontSize: 11,
};

function FeatureCard({ dist }: { dist: FeatureDistribution }) {
  const mergedData = useMemo(
    () =>
      dist.trainingBins.map((tb, i) => ({
        bin: tb.bin,
        training: tb.count,
        recent: dist.recentBins[i]?.count ?? 0,
      })),
    [dist],
  );

  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: dist.isDrifted ? "primary.main" : "divider",
        borderRadius: 1,
        p: 1.5,
        bgcolor: "background.default",
      }}
    >
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
        <Typography variant="caption" fontFamily="monospace" color="text.primary">
          {dist.feature}
        </Typography>
        {dist.isDrifted ? (
          <Chip label="Drifted" color="primary" size="small" />
        ) : (
          <Chip label="OK" color="success" size="small" />
        )}
      </Box>
      <Box sx={{ display: "flex", gap: 2, mb: 1 }}>
        <Typography variant="caption" fontFamily="monospace" color="text.secondary">
          KS: {dist.ksStat?.toFixed(3) ?? "—"}
        </Typography>
        <Typography variant="caption" fontFamily="monospace" color="text.secondary">
          PSI: {dist.psiValue?.toFixed(3) ?? "—"}
        </Typography>
      </Box>
      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={mergedData} barCategoryGap="15%">
          <XAxis
            dataKey="bin"
            tick={{ fontSize: 9, fill: "#a0a0a0" }}
            axisLine={{ stroke: "#2a2a4a" }}
            angle={-45}
            textAnchor="end"
            height={30}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value, name) => [
              Number(value),
              name === "training" ? "Training" : "Recent",
            ]}
          />
          <Bar dataKey="training" fill="#3b82f6" opacity={0.7} isAnimationActive={false} />
          <Bar dataKey="recent" fill="#e94560" opacity={0.7} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}

export default function FeatureDistributionChart({ distributions }: FeatureDistributionChartProps) {
  if (distributions.length === 0) {
    return null;
  }

  return (
    <Accordion defaultExpanded={false}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box>
          <Typography variant="subtitle2">
            Feature Distributions — Training vs. Recent
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {distributions.length} features monitored
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          {distributions.map((dist) => (
            <Grid size={{ xs: 12, md: 6, xl: 4 }} key={dist.feature}>
              <FeatureCard dist={dist} />
            </Grid>
          ))}
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}
