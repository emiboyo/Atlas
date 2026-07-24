from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.security import (
    AuthenticationRequiredError,
    ClerkSessionClaims,
    ClerkTokenVerifier,
    Principal,
    UnavailableTokenVerifier,
    decode_organization_permissions,
)


class StaticKeyResolver:
    def __init__(self, key: Any) -> None:
        self.key = key

    def resolve(self, token: str) -> Any:
        del token
        return self.key


class FailingKeyResolver:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def resolve(self, token: str) -> Any:
        del token
        raise self.error


def build_token(
    private_key: Any,
    *,
    authorized_party: str = "http://localhost:3000",
    status: str = "active",
) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": "user_123",
        "sid": "sess_123",
        "iss": "https://atlas.clerk.accounts.dev",
        "iat": now,
        "nbf": now - timedelta(seconds=1),
        "exp": now + timedelta(minutes=5),
        "azp": authorized_party,
        "sts": status,
        "v": 2,
        "fea": "o:portfolios,o:members",
        "o": {
            "id": "org_123",
            "slg": "atlas-capital",
            "rol": "admin",
            "per": "manage,read",
            "fpm": "3,2",
        },
    }
    return jwt.encode(claims, private_key, algorithm="RS256")


@pytest.fixture
def key_pair() -> tuple[Any, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def test_decodes_clerk_v2_permission_bitmasks() -> None:
    claims = ClerkSessionClaims.model_validate(
        {
            "sub": "user_123",
            "sid": "sess_123",
            "iss": "https://atlas.clerk.accounts.dev",
            "iat": 1,
            "nbf": 1,
            "exp": 2,
            "fea": "o:portfolios,o:members",
            "o": {
                "id": "org_123",
                "rol": "admin",
                "per": "manage,read",
                "fpm": "3,2",
            },
        }
    )

    assert decode_organization_permissions(claims) == {
        "org:portfolios:manage",
        "org:portfolios:read",
        "org:members:read",
    }


async def test_verifies_valid_session_and_builds_principal(key_pair: tuple[Any, Any]) -> None:
    private_key, public_key = key_pair
    settings = Settings(
        clerk_issuer_url="https://atlas.clerk.accounts.dev",
        clerk_authorized_parties=["http://localhost:3000"],
    )
    verifier = ClerkTokenVerifier(settings, StaticKeyResolver(public_key))

    principal = await verifier.verify(build_token(private_key))

    assert principal.user_id == "user_123"
    assert principal.organization_id == "org_123"
    assert principal.has_role("admin")
    assert principal.has_permission("org:portfolios:manage")


async def test_rejects_unknown_authorized_party(key_pair: tuple[Any, Any]) -> None:
    private_key, public_key = key_pair
    settings = Settings(
        clerk_issuer_url="https://atlas.clerk.accounts.dev",
        clerk_authorized_parties=["https://atlas.example"],
    )
    verifier = ClerkTokenVerifier(settings, StaticKeyResolver(public_key))

    with pytest.raises(AuthenticationRequiredError):
        await verifier.verify(build_token(private_key))


async def test_rejects_pending_session(key_pair: tuple[Any, Any]) -> None:
    private_key, public_key = key_pair
    settings = Settings(
        clerk_issuer_url="https://atlas.clerk.accounts.dev",
        clerk_authorized_parties=["http://localhost:3000"],
    )
    verifier = ClerkTokenVerifier(settings, StaticKeyResolver(public_key))

    with pytest.raises(ApplicationError) as error:
        await verifier.verify(build_token(private_key, status="pending"))

    assert error.value.code == "session_pending"


def test_principal_role_normalization() -> None:
    principal = Principal(
        user_id="user_123",
        session_id="sess_123",
        organization_id="org_123",
        organization_role="org:admin",
    )

    assert principal.has_role("admin")
    assert principal.has_role("org:admin")


async def test_rejects_invalid_token(key_pair: tuple[Any, Any]) -> None:
    _, public_key = key_pair
    settings = Settings(clerk_issuer_url="https://atlas.clerk.accounts.dev")
    verifier = ClerkTokenVerifier(settings, StaticKeyResolver(public_key))

    with pytest.raises(AuthenticationRequiredError):
        await verifier.verify("not-a-jwt")


async def test_unconfigured_authentication_is_unavailable() -> None:
    with pytest.raises(ApplicationError) as error:
        await UnavailableTokenVerifier().verify("token")

    assert error.value.status_code == 503


@pytest.mark.parametrize(
    ("resolver_error", "expected_code"),
    [
        (PyJWKClientConnectionError("unavailable"), "authentication_unavailable"),
        (PyJWKClientError("unknown key"), "authentication_required"),
    ],
)
async def test_maps_jwks_failures_to_safe_errors(
    resolver_error: Exception, expected_code: str
) -> None:
    settings = Settings(clerk_issuer_url="https://atlas.clerk.accounts.dev")
    verifier = ClerkTokenVerifier(settings, FailingKeyResolver(resolver_error))

    with pytest.raises(ApplicationError) as error:
        await verifier.verify("token")

    assert error.value.code == expected_code
