import {
  Box,
  Button,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  TextField,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import type { ForecastFiltersState } from "@/api";

interface ForecastFiltersProps {
  filters: ForecastFiltersState;
  onFilterChange: (filters: ForecastFiltersState) => void;
  sectors: string[];
}

export default function ForecastFilters({
  filters,
  onFilterChange,
  sectors,
}: ForecastFiltersProps) {
  const update = (patch: Partial<ForecastFiltersState>) =>
    onFilterChange({ ...filters, ...patch });

  const clearAll = () =>
    onFilterChange({
      sector: null,
      minReturn: null,
      maxReturn: null,
      minConfidence: null,
      search: "",
    });

  const hasActive =
    filters.sector !== null ||
    filters.minReturn !== null ||
    filters.maxReturn !== null ||
    filters.minConfidence !== null ||
    filters.search !== "";

  return (
    <Paper sx={{ p: 2 }}>
      <Grid container spacing={2} alignItems="flex-end">
        {/* Search */}
        <Grid size={{ xs: 12, sm: 6, lg: 2 }}>
          <TextField
            size="small"
            fullWidth
            label="Search"
            placeholder="Ticker or company…"
            value={filters.search}
            onChange={(e) => update({ search: e.target.value })}
            slotProps={{
              input: {
                startAdornment: (
                  <SearchIcon sx={{ mr: 0.5, color: "text.secondary", fontSize: 18 }} />
                ),
              },
            }}
          />
        </Grid>

        {/* Sector */}
        <Grid size={{ xs: 12, sm: 6, lg: 2 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>Sector</InputLabel>
            <Select
              label="Sector"
              value={filters.sector ?? ""}
              onChange={(e) => update({ sector: e.target.value || null })}
            >
              <MenuItem value="">All Sectors</MenuItem>
              {sectors.map((s) => (
                <MenuItem key={s} value={s}>
                  {s}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Min Return */}
        <Grid size={{ xs: 6, sm: 4, lg: 2 }}>
          <TextField
            size="small"
            fullWidth
            label="Min Return %"
            type="number"
            inputProps={{ step: 0.5 }}
            value={filters.minReturn ?? ""}
            onChange={(e) =>
              update({ minReturn: e.target.value ? Number(e.target.value) : null })
            }
          />
        </Grid>

        {/* Max Return */}
        <Grid size={{ xs: 6, sm: 4, lg: 2 }}>
          <TextField
            size="small"
            fullWidth
            label="Max Return %"
            type="number"
            inputProps={{ step: 0.5 }}
            value={filters.maxReturn ?? ""}
            onChange={(e) =>
              update({ maxReturn: e.target.value ? Number(e.target.value) : null })
            }
          />
        </Grid>

        {/* Min Confidence slider */}
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Min Confidence:{" "}
              <span style={{ color: "inherit" }}>
                {filters.minConfidence != null
                  ? filters.minConfidence.toFixed(2)
                  : "Any"}
              </span>
            </Typography>
            <Slider
              size="small"
              min={0}
              max={1}
              step={0.05}
              value={filters.minConfidence ?? 0}
              onChange={(_, v) => {
                const val = v as number;
                update({ minConfidence: val > 0 ? val : null });
              }}
              sx={{ mt: 1 }}
            />
          </Box>
        </Grid>

        {/* Clear */}
        <Grid size={{ xs: 12, sm: 2, lg: 1 }}>
          <Button
            variant="outlined"
            size="small"
            fullWidth
            disabled={!hasActive}
            onClick={clearAll}
          >
            Clear
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
}
