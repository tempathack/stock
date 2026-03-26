import type { TreemapSectorGroup } from "@/api";
import { changePctToColor } from "@/utils/dashboardUtils";
import { Box, ButtonBase, Divider, Paper, Stack, Typography } from "@mui/material";

interface MobileMarketListProps {
  data: TreemapSectorGroup[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
}

export default function MobileMarketList({
  data,
  selectedTicker,
  onSelectTicker,
}: MobileMarketListProps) {
  if (data.length === 0) {
    return (
      <Box
        sx={{
          border: "2px dashed",
          borderColor: "divider",
          borderRadius: 1,
          p: 4,
          textAlign: "center",
        }}
      >
        <Typography color="text.secondary">No market data available</Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={1}>
      {data.map((sector) => (
        <Paper key={sector.name} variant="outlined">
          <Box sx={{ borderBottom: "1px solid", borderColor: "divider", px: 1.5, py: 1 }}>
            <Typography
              variant="caption"
              fontWeight={700}
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: "0.08em" }}
            >
              {sector.name}
            </Typography>
          </Box>
          <Stack divider={<Divider />}>
            {sector.children.map((stock) => {
              const isSelected = stock.ticker === selectedTicker;
              const pct = stock.dailyChangePct ?? 0;
              return (
                <ButtonBase
                  key={stock.ticker}
                  onClick={() => onSelectTicker(stock.ticker)}
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    px: 1.5,
                    py: 1,
                    textAlign: "left",
                    width: "100%",
                    borderLeft: isSelected ? "2px solid" : "2px solid transparent",
                    borderLeftColor: isSelected ? "primary.main" : "transparent",
                    bgcolor: isSelected ? "primary.main" : "transparent",
                    "&:hover": { bgcolor: "action.hover" },
                  }}
                >
                  <Box sx={{ minWidth: 0, flex: 1 }}>
                    <Typography
                      component="span"
                      variant="body2"
                      fontWeight={700}
                      color="primary.main"
                    >
                      {stock.ticker}
                    </Typography>
                    <Typography
                      component="span"
                      variant="caption"
                      color="text.secondary"
                      sx={{ ml: 1 }}
                      noWrap
                    >
                      {stock.name}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Typography variant="body2" fontFamily="monospace">
                      ${stock.lastClose.toFixed(2)}
                    </Typography>
                    <Typography
                      variant="caption"
                      fontFamily="monospace"
                      fontWeight={600}
                      sx={{ minWidth: 60, textAlign: "right", color: changePctToColor(pct) }}
                    >
                      {pct >= 0 ? "+" : ""}{pct.toFixed(2)}%
                    </Typography>
                  </Stack>
                </ButtonBase>
              );
            })}
          </Stack>
        </Paper>
      ))}
    </Stack>
  );
}
