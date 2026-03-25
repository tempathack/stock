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

    # Group 7 — WebSocket (Phase 45+)
    WS_PRICE_INTERVAL: float = 5.0
    WS_MARKET_RECHECK_INTERVAL: float = 60.0

    # Group 8 — Redis (Phase 47+)
    REDIS_URL: Optional[str] = None

    # Group 9 — Rate Limiting (Phase 48+)
    RATE_LIMIT_GLOBAL: str = "100/minute"
    RATE_LIMIT_PREDICT: str = "30/minute"
    RATE_LIMIT_INGEST: str = "10/minute"

    # Group 10 — Health Checks (Phase 48+)
    MODEL_FRESHNESS_THRESHOLD_DAYS: int = 7
    PREDICTION_STALENESS_HOURS: int = 24

    # Group 11 — A/B Testing (Phase 49+)
    AB_TESTING_ENABLED: bool = False
    AB_LOG_ASSIGNMENTS: bool = True

    # Group 12 — KServe Inference (Phase 56+)
    KSERVE_INFERENCE_URL: Optional[str] = None
    KSERVE_MODEL_NAME: str = "stock-model-serving"
    KSERVE_TIMEOUT_SECONDS: float = 30.0
    KSERVE_ENABLED: bool = False
    KSERVE_CANARY_URL: Optional[str] = None

    # Group 13 — MinIO / Model Metadata (Phase 60+)
    MINIO_SERVING_PREFIX: str = "serving/active"

    # Group 6 — ML / Model Serving (Phase 23+)
    MODEL_REGISTRY_DIR: str = "model_registry"
    DRIFT_LOG_DIR: str = "drift_logs"
    SERVING_DIR: str = "/models/active"
    DEFAULT_HORIZON: int = 7
    AVAILABLE_HORIZONS: str = "1,7,30"

    @property
    def available_horizons_list(self) -> list[int]:
        """Parse AVAILABLE_HORIZONS into a list of ints."""
        return [int(h.strip()) for h in self.AVAILABLE_HORIZONS.split(",") if h.strip()]


settings = Settings()
