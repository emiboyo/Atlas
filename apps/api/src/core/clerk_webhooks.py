import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime

from fastapi import status
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.identity.repositories import UserRepository, WebhookRepository
from apps.api.src.identity.services import IdentityService
from packages.database.atlas_database.models.enums import IdentityWebhookStatus, UserStatus
from packages.database.atlas_database.models.identity import ClerkWebhookEvent, User


class ClerkWebhookData(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    first_name: str | None = None
    last_name: str | None = None


class ClerkWebhook(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    data: ClerkWebhookData
    timestamp: int | None = None


class ClerkWebhookVerifier:
    def __init__(self, settings: Settings) -> None:
        self.max_payload_bytes = settings.clerk_webhook_max_bytes
        self.tolerance_seconds = settings.clerk_webhook_tolerance_seconds
        encoded = settings.clerk_webhook_secret.get_secret_value().removeprefix("whsec_")
        if not encoded:
            raise self._unavailable()
        try:
            self._secret = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise self._unavailable() from exc

    def verify(
        self, payload: bytes, *, svix_id: str, svix_timestamp: str, svix_signature: str
    ) -> ClerkWebhook:
        try:
            timestamp = int(svix_timestamp)
        except ValueError as exc:
            raise self._invalid() from exc
        if abs(int(time.time()) - timestamp) > self.tolerance_seconds:
            raise self._invalid()
        signed = f"{svix_id}.{svix_timestamp}.".encode() + payload
        expected = base64.b64encode(
            hmac.new(self._secret, signed, hashlib.sha256).digest()
        ).decode()
        candidates = [
            item.split(",", 1)[1]
            for item in svix_signature.split()
            if item.startswith("v1,") and "," in item
        ]
        if not candidates or not any(hmac.compare_digest(expected, value) for value in candidates):
            raise self._invalid()
        try:
            return ClerkWebhook.model_validate(json.loads(payload))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ApplicationError(
                "The Clerk webhook payload is invalid.",
                code="invalid_webhook_payload",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

    @staticmethod
    def _invalid() -> ApplicationError:
        return ApplicationError(
            "The Clerk webhook signature is invalid.",
            code="invalid_webhook_signature",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def _unavailable() -> ApplicationError:
        return ApplicationError(
            "Clerk webhook processing is not configured.",
            code="webhook_unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ClerkWebhookService:
    supported_events = frozenset({"user.created", "user.updated", "user.deleted"})

    def __init__(self) -> None:
        self.events = WebhookRepository()
        self.users = UserRepository()
        self.identity = IdentityService()

    async def process(
        self,
        session: AsyncSession,
        *,
        svix_id: str,
        event: ClerkWebhook,
        payload: bytes,
        request_id: str | None,
    ) -> bool:
        existing = await self.events.by_svix_id(session, svix_id)
        if existing is not None and existing.status in {
            IdentityWebhookStatus.PROCESSED,
            IdentityWebhookStatus.IGNORED,
        }:
            return False
        occurred_at = (
            datetime.fromtimestamp(event.timestamp / 1000, tz=UTC)
            if event.timestamp is not None
            else datetime.now(UTC)
        )
        inbox = existing or ClerkWebhookEvent(
            svix_id=svix_id,
            event_type=event.type,
            clerk_subject_id=event.data.id,
            status=IdentityWebhookStatus.PENDING,
            occurred_at=occurred_at,
            payload_digest=hashlib.sha256(payload).hexdigest(),
        )
        inbox.status = IdentityWebhookStatus.PENDING
        inbox.failure_reason = None
        if existing is None:
            session.add(inbox)
            try:
                await session.flush()
            except IntegrityError:
                await session.rollback()
                if await self.events.by_svix_id(session, svix_id):
                    return False
                raise
        try:
            if event.type not in self.supported_events:
                inbox.status = IdentityWebhookStatus.IGNORED
            elif event.type == "user.deleted":
                await self._deactivate_tombstone(session, event.data.id, request_id)
                inbox.status = IdentityWebhookStatus.PROCESSED
            else:
                display_name = " ".join(
                    value for value in (event.data.first_name, event.data.last_name) if value
                )
                await self.identity.provision(
                    session,
                    clerk_subject=event.data.id,
                    display_name=display_name or "Atlas member",
                    first_name=event.data.first_name,
                    last_name=event.data.last_name,
                    request_id=request_id,
                    commit=False,
                )
                inbox.status = IdentityWebhookStatus.PROCESSED
            inbox.processed_at = datetime.now(UTC)
            await session.commit()
            return True
        except Exception as exc:
            await session.rollback()
            failed = await self.events.by_svix_id(session, svix_id)
            if failed is None:
                failed = ClerkWebhookEvent(
                    svix_id=svix_id,
                    event_type=event.type,
                    clerk_subject_id=event.data.id,
                    occurred_at=occurred_at,
                    payload_digest=hashlib.sha256(payload).hexdigest(),
                )
                session.add(failed)
            failed.status = IdentityWebhookStatus.FAILED
            failed.failure_reason = type(exc).__name__[:120]
            failed.processed_at = datetime.now(UTC)
            await session.commit()
            raise

    async def _deactivate_tombstone(
        self, session: AsyncSession, clerk_subject: str, request_id: str | None
    ) -> None:
        user = await self.users.by_clerk_subject(session, clerk_subject)
        if user is None:
            user = User(clerk_user_id=clerk_subject, status=UserStatus.DEACTIVATED)
            session.add(user)
            await session.flush()
        else:
            user.status = UserStatus.DEACTIVATED
        user.deactivated_at = datetime.now(UTC)
        self.identity._audit(
            session,
            event_type="account.deactivated",
            actor_user_id=None,
            tenant_id=None,
            target_type="user",
            target_id=user.id,
            request_id=request_id,
            metadata={"source": "clerk_webhook"},
        )
