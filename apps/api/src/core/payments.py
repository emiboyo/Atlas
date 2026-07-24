from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, cast

import stripe
from fastapi import status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.logging import get_logger
from packages.database.atlas_database.models.billing import StripeWebhookEvent
from packages.database.atlas_database.models.enums import WebhookEventStatus

logger = get_logger(__name__)


class StripeWebhookVerifier:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.stripe_webhook_secret.get_secret_value()
        self.max_payload_bytes = settings.stripe_webhook_max_bytes

    def verify(self, payload: bytes, signature: str) -> dict[str, Any]:
        if not self._secret or "replace_me" in self._secret:
            raise ApplicationError(
                "Payment webhooks are not configured.",
                code="payment_webhook_unavailable",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
                payload, signature, self._secret
            )
        except (ValueError, stripe.SignatureVerificationError) as exc:
            logger.info("stripe_webhook_rejected", reason=type(exc).__name__)
            raise ApplicationError(
                "The webhook signature is invalid.",
                code="invalid_webhook_signature",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc
        return cast(dict[str, Any], event.to_dict())


class StripeWebhookInbox:
    async def accept(
        self, session: AsyncSession, event: dict[str, Any], raw_payload: bytes
    ) -> bool:
        stripe_created_at = datetime.fromtimestamp(int(event["created"]), tz=UTC)
        statement = (
            insert(StripeWebhookEvent)
            .values(
                stripe_event_id=str(event["id"]),
                event_type=str(event["type"]),
                api_version=event.get("api_version"),
                stripe_account_id=event.get("account"),
                livemode=bool(event["livemode"]),
                stripe_created_at=stripe_created_at,
                payload_sha256=sha256(raw_payload).hexdigest(),
                payload=event,
                status=WebhookEventStatus.PENDING,
                processing_attempts=0,
            )
            .on_conflict_do_nothing(index_elements=["stripe_event_id"])
            .returning(StripeWebhookEvent.id)
        )
        result = await session.execute(statement)
        inserted = result.scalar_one_or_none() is not None
        await session.commit()
        logger.info(
            "stripe_webhook_accepted",
            stripe_event_id=event["id"],
            event_type=event["type"],
            duplicate=not inserted,
        )
        return inserted
