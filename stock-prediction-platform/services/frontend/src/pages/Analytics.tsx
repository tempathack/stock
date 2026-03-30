import { Component, type ErrorInfo, type ReactNode } from "react";
import { Container, Alert } from "@mui/material";
import Grid from "@mui/material/Grid";
import PageHeader from "../components/layout/PageHeader";
import {
  FeatureFreshnessPanel,
  OLAPCandleChart,
  StreamHealthPanel,
  StreamLagMonitor,
  SystemHealthSummary,
} from "../components/analytics";

// Local error boundary — react-error-boundary is not in this project's dependencies
interface PanelErrorBoundaryState {
  hasError: boolean;
  message: string;
}

class PanelErrorBoundary extends Component<
  { children: ReactNode },
  PanelErrorBoundaryState
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error): PanelErrorBoundaryState {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[PanelErrorBoundary]", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert severity="error">
          Panel failed to render: {this.state.message}
        </Alert>
      );
    }
    return this.props.children;
  }
}

export default function Analytics() {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <PageHeader
        title="Analytics"
        subtitle="Real-time stream health and feature pipeline status"
      />

      {/* Row 1: System Health Summary — full width */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12 }}>
          <PanelErrorBoundary>
            <SystemHealthSummary />
          </PanelErrorBoundary>
        </Grid>
      </Grid>

      {/* Row 2: Stream Health (left) + Feature Freshness (right) */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <PanelErrorBoundary>
            <StreamHealthPanel />
          </PanelErrorBoundary>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <PanelErrorBoundary>
            <FeatureFreshnessPanel />
          </PanelErrorBoundary>
        </Grid>
      </Grid>

      {/* Row 3: OLAP Candle Chart (wide) + Stream Lag (narrow) */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 8 }}>
          <PanelErrorBoundary>
            <OLAPCandleChart />
          </PanelErrorBoundary>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <PanelErrorBoundary>
            <StreamLagMonitor />
          </PanelErrorBoundary>
        </Grid>
      </Grid>
    </Container>
  );
}
