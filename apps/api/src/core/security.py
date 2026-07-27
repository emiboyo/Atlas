from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, Protocol, cast

import jwt
from fastapi import Depends, Request, status
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientConnectionError, PyJWKClientError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.logging import get_logger

logger = get_logger(__name__)


class OrganizationClaim(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slg: str | None = None
    rol: str
    per: str = ""
    fpm: str = ""


class ClerkSessionClaims(BaseModel):
    model_config = ConfigDict(extra="allow")

    sub: str
    sid: str
    iss: str
    exp: int
    nbf: int
    iat: int
    azp: str | None = None
    sts: Literal["active", "pending"] | None = None
    v: int = 2
    fea: str = ""
    o: OrganizationClaim | None = None


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    session_id: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organization_id: str | None = None
    organization_slug: str | None = None
    organization_role: str | None = None
    organization_permissions: frozenset[str] = Field(default_factory=frozenset)

    @property
    def is_organization_member(self) -> bool:
        return self.organization_id is not None

    def has_permission(self, permission: str) -> bool:
        return permission in self.organization_permissions

    def has_role(self, role: str) -> bool:
        normalized = role if role.startswith("org:") else f"org:{role}"
        return self.organization_role == normalized


class SigningKeyResolver(Protocol):
    def resolve(self, token: str) -> Any: ...


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> Principal: ...


@dataclass
class ClerkJwksResolver:
    client: PyJWKClient

    def resolve(self, token: str) -> Any:
        return self.client.get_signing_key_from_jwt(token).key


def decode_organization_permissions(claims: ClerkSessionClaims) -> frozenset[str]:
    organization = claims.o
    if organization is None:
        return frozenset()

    features = [
        value.removeprefix("o:")
        for value in claims.fea.split(",")
        if value.startswith("o:") and len(value) > 2
    ]
    permission_names = [value for value in organization.per.split(",") if value]
    masks = organization.fpm.split(",") if organization.fpm else []
    permissions: set[str] = set()

    for feature_index, feature in enumerate(features):
        if feature_index >= len(masks):
            break
        try:
            mask = int(masks[feature_index])
        except ValueError:
            logger.warning(
                "invalid_clerk_permission_mask",
                organization_id=organization.id,
                feature=feature,
            )
            continue
        for permission_index, permission in enumerate(permission_names):
            if mask & (1 << permission_index):
                permissions.add(f"org:{feature}:{permission}")

    return frozenset(permissions)


class ClerkTokenVerifier:
    def __init__(self, settings: Settings, resolver: SigningKeyResolver) -> None:
        self._settings = settings
        self._resolver = resolver

    async def verify(self, token: str) -> Principal:
        try:
            signing_key = await run_in_threadpool(self._resolver.resolve, token)
        except PyJWKClientConnectionError as exc:
            logger.error("authentication_key_service_unavailable")
            raise ApplicationError(
                "Authentication is temporarily unavailable.",
                code="authentication_unavailable",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        except PyJWKClientError as exc:
            logger.info("authentication_failed", reason=type(exc).__name__)
            raise AuthenticationRequiredError() from exc

        try:
            decode_options: dict[str, Any] = {"require": ["sub", "sid", "iss", "exp", "nbf", "iat"]}
            decode_arguments: dict[str, Any] = {
                "key": signing_key,
                "algorithms": ["RS256"],
                "issuer": self._settings.clerk_issuer_url,
                "options": decode_options,
            }
            if self._settings.clerk_audience:
                decode_arguments["audience"] = self._settings.clerk_audience
            else:
                decode_options["verify_aud"] = False

            raw_claims = jwt.decode(token, **decode_arguments)
            claims = ClerkSessionClaims.model_validate(raw_claims)
        except (InvalidTokenError, ValidationError, ValueError) as exc:
            logger.info("authentication_failed", reason=type(exc).__name__)
            raise AuthenticationRequiredError() from exc

        if claims.azp and claims.azp not in self._settings.clerk_authorized_parties:
            logger.info("authentication_failed", reason="unauthorized_party")
            raise AuthenticationRequiredError()
        if claims.sts == "pending":
            raise ApplicationError(
                "Complete account setup before continuing.",
                code="session_pending",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        organization = claims.o
        return Principal(
            user_id=claims.sub,
            session_id=claims.sid,
            issued_at=datetime.fromtimestamp(claims.iat, tz=UTC),
            organization_id=organization.id if organization else None,
            organization_slug=organization.slg if organization else None,
            organization_role=f"org:{organization.rol}" if organization else None,
            organization_permissions=decode_organization_permissions(claims),
        )


class AuthenticationRequiredError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "Authentication is required.",
            code="authentication_required",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UnavailableTokenVerifier:
    async def verify(self, token: str) -> Principal:
        del token
        raise ApplicationError(
            "Authentication is not configured.",
            code="authentication_unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def create_token_verifier(settings: Settings) -> TokenVerifier:
    if not settings.clerk_issuer_url or not settings.clerk_jwks_url:
        logger.warning("authentication_not_configured")
        return UnavailableTokenVerifier()
    resolver = ClerkJwksResolver(
        PyJWKClient(
            settings.clerk_jwks_url,
            cache_keys=True,
            lifespan=settings.clerk_jwks_cache_ttl_seconds,
            timeout=settings.clerk_jwks_timeout_seconds,
        )
    )
    return ClerkTokenVerifier(settings, resolver)


def get_token_verifier(request: Request) -> TokenVerifier:
    return cast("TokenVerifier", request.app.state.token_verifier)


async def get_current_principal(
    request: Request,
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> Principal:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationRequiredError()
    return await verifier.verify(token)


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


async def get_optional_principal(
    request: Request,
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> Principal | None:
    authorization = request.headers.get("authorization", "")
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationRequiredError()
    return await verifier.verify(token)


OptionalPrincipal = Annotated[Principal | None, Depends(get_optional_principal)]


def require_organization(principal: CurrentPrincipal) -> Principal:
    if not principal.is_organization_member:
        raise ApplicationError(
            "An active organization is required.",
            code="organization_required",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return principal


def require_permission(permission: str) -> Any:
    def dependency(
        principal: Annotated[Principal, Depends(require_organization)],
    ) -> Principal:
        if not principal.has_permission(permission):
            raise ApplicationError(
                "You do not have permission to perform this action.",
                code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return principal

    return dependency


def require_role(role: str) -> Any:
    def dependency(
        principal: Annotated[Principal, Depends(require_organization)],
    ) -> Principal:
        if not principal.has_role(role):
            raise ApplicationError(
                "You do not have the required role.",
                code="role_required",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return principal

    return dependency
