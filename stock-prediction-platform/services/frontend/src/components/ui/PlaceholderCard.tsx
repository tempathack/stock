import { Box, Chip, Typography } from "@mui/material";

interface PlaceholderCardProps {
  title: string;
  phase: number;
}

export default function PlaceholderCard({ title, phase }: PlaceholderCardProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        border: "2px dashed",
        borderColor: "divider",
        borderRadius: 1,
        p: 6,
      }}
    >
      <Typography variant="body1" color="text.secondary" fontWeight={500}>
        {title}
      </Typography>
      <Chip label={`Coming in Phase ${phase}`} size="small" sx={{ mt: 1 }} />
    </Box>
  );
}
