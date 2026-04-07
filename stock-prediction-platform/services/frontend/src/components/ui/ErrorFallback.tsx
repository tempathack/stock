import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { Box, Button, Typography } from "@mui/material";
import type { FallbackProps } from "react-error-boundary";

// Extends FallbackProps so it works both as react-error-boundary FallbackComponent
// and as an inline component with legacy {message, onRetry} props.
interface ErrorFallbackProps extends Partial<FallbackProps> {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorFallback({
  error,
  resetErrorBoundary,
  message,
  onRetry,
}: ErrorFallbackProps) {
  const displayMessage =
    message ??
    (error instanceof Error ? error.message : "Something went wrong");
  const handleRetry = onRetry ?? resetErrorBoundary;

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
        gap: 1,
      }}
    >
      <ErrorOutlineIcon sx={{ color: "error.main", fontSize: 40 }} />
      <Typography color="error.main" variant="body1" fontWeight={500}>
        {displayMessage}
      </Typography>
      {handleRetry && (
        <Button variant="contained" onClick={handleRetry} sx={{ mt: 1 }}>
          Retry
        </Button>
      )}
    </Box>
  );
}
