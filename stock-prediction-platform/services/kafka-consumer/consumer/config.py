"""Consumer configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConsumerSettings(BaseSettings):
    """Consumer settings loaded from environment variables.

    Env vars injected by K8s configmap (processing-config) and secret (stock-platform-secrets).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_GROUP_ID: str = "stock-consumer-group"
    INTRADAY_TOPIC: str = "intraday-data"
    HISTORICAL_TOPIC: str = "historical-data"

    # Batching
    BATCH_SIZE: int = 100
    BATCH_TIMEOUT_MS: int = 5000

    # Database — injected by K8s Secret (stock-platform-secrets) in production
    DATABASE_URL: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"


settings = ConsumerSettings()
