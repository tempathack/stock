import { Box, Typography } from "@mui/material";

interface PlaceholderCardProps {
  title: string;
}

export default function PlaceholderCard({ title }: PlaceholderCardProps) {
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
    </Box>
  );
}
