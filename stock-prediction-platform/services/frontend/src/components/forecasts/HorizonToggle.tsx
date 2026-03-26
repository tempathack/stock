import { ToggleButtonGroup, ToggleButton } from "@mui/material";

interface HorizonToggleProps {
  horizons: number[];
  selected: number;
  onChange: (h: number) => void;
  loading?: boolean;
}

export function HorizonToggle({
  horizons,
  selected,
  onChange,
  loading = false,
}: HorizonToggleProps) {
  return (
    <ToggleButtonGroup
      exclusive
      value={selected}
      onChange={(_, v: number | null) => {
        if (v !== null) onChange(v);
      }}
      disabled={loading}
      size="small"
      aria-label="Prediction horizon"
    >
      {horizons.map((h) => (
        <ToggleButton key={h} value={h}>
          {h}D
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

export default HorizonToggle;
