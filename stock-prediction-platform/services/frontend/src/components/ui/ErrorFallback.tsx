import { Box, Button, Typography } from "@mui/material";

interface ErrorFallbackProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorFallback({
  message = "Something went wrong",
  onRetry,
}: ErrorFallbackProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        p: 4,
      }}
    >
      <Typography color="error.main" variant="body1" fontWeight={500}>
        {message}
      </Typography>
      {onRetry && (
        <Button variant="contained" onClick={onRetry} sx={{ mt: 2 }}>
          Retry
        </Button>
      )}
    </Box>
  );
}
