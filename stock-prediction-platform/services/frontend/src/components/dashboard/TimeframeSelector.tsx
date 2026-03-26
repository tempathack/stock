import type { Timeframe } from "@/api";
import { ToggleButton, ToggleButtonGroup } from "@mui/material";

interface TimeframeSelectorProps {
  value: Timeframe;
  onChange: (tf: Timeframe) => void;
}

const OPTIONS: Timeframe[] = ["1D", "1W", "1M", "3M", "1Y"];

export default function TimeframeSelector({
  value,
  onChange,
}: TimeframeSelectorProps) {
  return (
    <ToggleButtonGroup
      value={value}
      exclusive
      onChange={(_, v: Timeframe | null) => { if (v) onChange(v); }}
      size="small"
    >
      {OPTIONS.map((tf) => (
        <ToggleButton key={tf} value={tf} sx={{ px: 1.5, py: 0.5, fontSize: "0.75rem" }}>
          {tf}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}
