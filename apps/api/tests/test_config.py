import pytest
from pydantic import ValidationError

from apps.api.src.core.config import Settings


def test_local_configuration_uses_safe_disabled_integrations() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "local"
    assert settings.clerk_issuer_url == ""
    assert settings.stripe_webhook_secret.get_secret_value() == ""


def test_production_rejects_local_defaults() -> None:
    with pytest.raises(ValidationError, match="Unsafe production configuration"):
        Settings(environment="production", _env_file=None)


def test_production_accepts_explicit_non_local_dependencies() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://atlas:secret@database.internal/atlas",
        redis_url="rediss://cache.internal:6379/0",
        cors_origins=["https://atlas.example"],
        trusted_hosts=["api.atlas.example"],
        clerk_issuer_url="https://clerk.atlas.example",
        clerk_jwks_url="https://clerk.atlas.example/.well-known/jwks.json",
        clerk_webhook_secret="whsec_dGVzdC1vbmx5LXNlY3JldA==",  # noqa: S106
        _env_file=None,
    )

    assert settings.environment == "production"
