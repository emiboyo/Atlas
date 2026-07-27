import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from apps.api.src.api.v1.webhooks import validate_content_length
from apps.api.src.core.clerk_webhooks import ClerkWebhookVerifier
from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.security import Principal
from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.identity.schemas import DeactivationRequest, MembershipUpdate, ProfileUpdate
from apps.api.src.identity.services import IdentityService
from packages.database.atlas_database.models.enums import (
    MembershipRole,
    UserStatus,
)
from packages.database.atlas_database.models.identity import User


def signed_webhook(
    payload: bytes, secret: bytes, *, timestamp: int | None = None
) -> tuple[str, str, str]:
    svix_id = "msg_test"
    timestamp_text = str(timestamp or int(time.time()))
    signature = base64.b64encode(
        hmac.new(
            secret,
            f"{svix_id}.{timestamp_text}.".encode() + payload,
            hashlib.sha256,
        ).digest()
    ).decode()
    return svix_id, timestamp_text, f"v1,{signature}"


def test_clerk_webhook_signature_verification() -> None:
    secret = b"test-only-webhook-secret"
    payload = json.dumps(
        {
            "type": "user.created",
            "timestamp": int(time.time() * 1000),
            "data": {"id": "user_123", "first_name": "Atlas"},
        }
    ).encode()
    verifier = ClerkWebhookVerifier(
        Settings(clerk_webhook_secret=f"whsec_{base64.b64encode(secret).decode()}")
    )
    svix_id, timestamp, signature = signed_webhook(payload, secret)

    event = verifier.verify(
        payload,
        svix_id=svix_id,
        svix_timestamp=timestamp,
        svix_signature=signature,
    )

    assert event.type == "user.created"
    assert event.data.id == "user_123"


@pytest.mark.parametrize(
    ("timestamp_offset", "signature"),
    [(0, "v1,invalid"), (-1000, None)],
)
def test_clerk_webhook_rejects_invalid_or_stale_signature(
    timestamp_offset: int, signature: str | None
) -> None:
    secret = b"test-only-webhook-secret"
    payload = b'{"type":"user.created","data":{"id":"user_123"}}'
    verifier = ClerkWebhookVerifier(
        Settings(clerk_webhook_secret=f"whsec_{base64.b64encode(secret).decode()}")
    )
    svix_id, timestamp, valid_signature = signed_webhook(
        payload, secret, timestamp=int(time.time()) + timestamp_offset
    )

    with pytest.raises(ApplicationError) as error:
        verifier.verify(
            payload,
            svix_id=svix_id,
            svix_timestamp=timestamp,
            svix_signature=signature or valid_signature,
        )

    assert error.value.code == "invalid_webhook_signature"


def test_permission_matrix_prevents_role_escalation() -> None:
    authorisation = AuthorisationService()

    assert authorisation.can(MembershipRole.OWNER, Permission.OWNERSHIP_TRANSFER)
    assert authorisation.can(MembershipRole.ADMIN, Permission.MEMBERSHIP_UPDATE)
    assert not authorisation.can(MembershipRole.ADMIN, Permission.OWNERSHIP_TRANSFER)
    assert not authorisation.can(MembershipRole.VIEWER, Permission.MEMBERSHIP_UPDATE)

    with pytest.raises(ApplicationError):
        authorisation.require_permission(MembershipRole.VIEWER, Permission.MEMBERSHIP_UPDATE)


def test_profile_and_membership_requests_reject_mass_assignment() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdate.model_validate({"platform_role": "platform_admin"})
    with pytest.raises(ValidationError):
        MembershipUpdate.model_validate({"user_id": "00000000-0000-0000-0000-000000000000"})


def test_profile_validates_timezone_and_iso_codes() -> None:
    profile = ProfileUpdate(
        timezone="Europe/London",
        country_of_residence="GB",
        base_currency="GBP",
    )
    assert profile.timezone == "Europe/London"

    with pytest.raises(ValidationError):
        ProfileUpdate(timezone="Not/A_Timezone")
    with pytest.raises(ValidationError):
        ProfileUpdate(base_currency="pounds")


def test_oversized_and_invalid_webhook_content_length_are_rejected() -> None:
    oversized = Request(
        {"type": "http", "method": "POST", "path": "/", "headers": [(b"content-length", b"2048")]}
    )
    invalid = Request(
        {"type": "http", "method": "POST", "path": "/", "headers": [(b"content-length", b"-1")]}
    )

    with pytest.raises(ApplicationError) as error:
        validate_content_length(oversized, 1024)
    assert error.value.code == "webhook_payload_too_large"

    with pytest.raises(ApplicationError) as error:
        validate_content_length(invalid, 1024)
    assert error.value.code == "invalid_content_length"


async def test_inactive_users_are_rejected() -> None:
    service = IdentityService()
    service.users.by_clerk_subject = _returning(  # type: ignore[method-assign]
        User(clerk_user_id="user_123", status=UserStatus.SUSPENDED)
    )

    with pytest.raises(ApplicationError) as error:
        await service.require_active_user(
            object(),  # type: ignore[arg-type]
            Principal(user_id="user_123", session_id="session_123"),
        )

    assert error.value.code == "account_inactive"


async def test_deactivation_requires_recent_authentication() -> None:
    user = User(clerk_user_id="user_123", status=UserStatus.ACTIVE)
    principal = Principal(
        user_id="user_123",
        session_id="session_123",
        issued_at=datetime.now(UTC) - timedelta(hours=1),
    )

    with pytest.raises(ApplicationError) as error:
        await IdentityService().deactivate(
            object(),  # type: ignore[arg-type]
            user,
            principal,
            DeactivationRequest(confirmation="DEACTIVATE").confirmation,
            None,
        )

    assert error.value.code == "recent_authentication_required"


def _returning(value: object):
    async def function(*_: object, **__: object):
        return value

    return function
