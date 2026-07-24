from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ATLAS_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Atlas AI API"
    app_version: str = "0.1.0"
    environment: Literal["local", "development", "staging", "production", "test"] = "local"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_host: str = "0.0.0.0"  # noqa: S104
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://atlas:change-me-in-production@localhost:5432/atlas"
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")

    clerk_issuer_url: str = ""
    clerk_jwks_url: str = ""
    clerk_audience: str | None = None
    clerk_authorized_parties: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    clerk_jwks_cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    stripe_secret_key: SecretStr = SecretStr("")
    stripe_webhook_secret: SecretStr = SecretStr("")
    stripe_webhook_max_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)
    otel_exporter_otlp_endpoint: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
