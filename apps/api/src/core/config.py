from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )

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
    clerk_jwks_timeout_seconds: int = Field(default=5, ge=1, le=30)
    clerk_webhook_secret: SecretStr = SecretStr("")
    clerk_webhook_max_bytes: int = Field(default=262_144, ge=1024, le=1_048_576)
    clerk_webhook_tolerance_seconds: int = Field(default=300, ge=60, le=900)
    stripe_secret_key: SecretStr = SecretStr("")
    stripe_webhook_secret: SecretStr = SecretStr("")
    stripe_webhook_max_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)
    otel_exporter_otlp_endpoint: str = ""
    market_data_provider: Literal["simulated", "disabled"] = "simulated"
    market_search_cache_ttl_seconds: int = Field(default=900, ge=10, le=86400)
    market_detail_cache_ttl_seconds: int = Field(default=1800, ge=10, le=86400)
    market_quote_cache_ttl_seconds: int = Field(default=30, ge=1, le=3600)
    market_quote_stale_fallback_ttl_seconds: int = Field(default=300, ge=1, le=86400)
    market_candle_cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    market_provider_timeout_seconds: int = Field(default=5, ge=1, le=30)
    market_provider_retry_count: int = Field(default=1, ge=0, le=3)
    market_provider_future_timestamp_tolerance_seconds: int = Field(default=300, ge=0, le=3600)
    market_quote_stale_after_seconds: int = Field(default=30, ge=1, le=3600)
    market_candle_stale_after_seconds: int = Field(default=86400, ge=60, le=604800)
    market_health_cache_ttl_seconds: int = Field(default=15, ge=1, le=300)
    market_max_search_results: int = Field(default=50, ge=1, le=100)
    market_max_candle_days: int = Field(default=366, ge=1, le=3660)
    watchlist_max_per_tenant: int = Field(default=25, ge=1, le=500)
    watchlist_max_items: int = Field(default=100, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.environment != "production":
            return self

        unsafe_configuration: list[str] = []
        database_url = self.database_url.get_secret_value()
        redis_url = self.redis_url.get_secret_value()

        if self.debug:
            unsafe_configuration.append("ATLAS_DEBUG must be false")
        if "localhost" in database_url or "atlas-local-only" in database_url:
            unsafe_configuration.append("ATLAS_DATABASE_URL must use production credentials")
        if "localhost" in redis_url:
            unsafe_configuration.append("ATLAS_REDIS_URL must use the production service")
        if not self.cors_origins or any(
            origin == "*" or "localhost" in origin for origin in self.cors_origins
        ):
            unsafe_configuration.append("ATLAS_CORS_ORIGINS must contain production origins")
        if not self.trusted_hosts or any(
            host == "*" or host in {"localhost", "127.0.0.1", "testserver"}
            for host in self.trusted_hosts
        ):
            unsafe_configuration.append("ATLAS_TRUSTED_HOSTS must contain production hosts")
        if not self.clerk_issuer_url or not self.clerk_jwks_url:
            unsafe_configuration.append("Clerk issuer and JWKS URLs are required")
        if not self.clerk_webhook_secret.get_secret_value():
            unsafe_configuration.append("ATLAS_CLERK_WEBHOOK_SECRET is required")

        if unsafe_configuration:
            raise ValueError("Unsafe production configuration: " + "; ".join(unsafe_configuration))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
