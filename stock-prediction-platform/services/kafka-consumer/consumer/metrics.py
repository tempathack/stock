"""Prometheus metrics for the Kafka consumer service."""

from prometheus_client import Counter, Gauge, Histogram, start_http_server

messages_consumed_total = Counter(
    "messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic"],
)

batch_write_duration_seconds = Histogram(
    "batch_write_duration_seconds",
    "Duration of batch write to PostgreSQL in seconds",
    ["table"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

consumer_lag = Gauge(
    "consumer_lag",
    "Kafka consumer lag (messages behind high watermark)",
    ["topic", "partition"],
)


def start_metrics_server(port: int = 9090) -> None:
    """Start a Prometheus metrics HTTP server on a daemon thread."""
    start_http_server(port)
