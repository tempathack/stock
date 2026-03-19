"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables.

    Groups are organized by feature domain. Groups 2-3 carry safe defaults
    so the app can start at Phase 3 without requiring all env vars.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Group 1 — Service identity
    SERVICE_NAME: str = "stock-api"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # Group 2 — Database (Phase 4+)
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Group 3 — Kafka (Phase 5+)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
    INTRADAY_TOPIC: str = "intraday-data"
    HISTORICAL_TOPIC: str = "historical-data"

    # Group 4 — Feature flags
    DEBUG: bool = False
    ENVIRONMENT: str = "dev"

    # Group 5 — Ingestion (Phase 6+)
    TICKER_SYMBOLS: str = "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,BRK-B,JPM,JNJ,V,PG,UNH,HD,MA,BAC,XOM,PFE,ABBV,CVX"


settings = Settings()
