"""Custom Prometheus metrics for prediction endpoints."""

from prometheus_client import Counter, Gauge, Histogram

prediction_requests_total = Counter(
    "prediction_requests_total",
    "Total prediction requests",
    ["ticker", "model", "status"],
)

prediction_latency_seconds = Histogram(
    "prediction_latency_seconds",
    "Prediction inference latency in seconds",
    ["ticker", "model"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

model_inference_errors_total = Counter(
    "model_inference_errors_total",
    "Total model inference errors",
    ["ticker", "error_type"],
)

feast_stale_features_total = Counter(
    "feast_stale_features_total",
    "Total Feast feature fallbacks due to staleness or unavailability",
    ["ticker", "reason"],  # reason: "feast_unavailable" | "feast_stale"
)

drift_score_current = Gauge(
    "drift_score_current",
    "Current drift score (KS statistic) per feature",
    ["feature", "model_id"],
)
