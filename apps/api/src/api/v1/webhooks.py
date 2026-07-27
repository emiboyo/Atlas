from typing import Annotated

from fastapi import APIRouter, Header, Request, status
from pydantic import BaseModel

from apps.api.src.core.clerk_webhooks import ClerkWebhookService, ClerkWebhookVerifier
from apps.api.src.core.config import get_settings
from apps.api.src.core.dependencies import DatabaseSession
from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.payments import StripeWebhookInbox, StripeWebhookVerifier

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookAccepted(BaseModel):
    received: bool
    duplicate: bool


def validate_content_length(request: Request, max_payload_bytes: int) -> None:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise ApplicationError(
                "The Content-Length header is invalid.",
                code="invalid_content_length",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc
        if declared_length < 0:
            raise ApplicationError(
                "The Content-Length header is invalid.",
                code="invalid_content_length",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if declared_length > max_payload_bytes:
            raise ApplicationError(
                "The webhook payload is too large.",
                code="webhook_payload_too_large",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )


@router.post(
    "/stripe",
    response_model=WebhookAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive a Stripe event",
)
async def receive_stripe_webhook(
    request: Request,
    session: DatabaseSession,
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> WebhookAccepted:
    settings = get_settings()
    verifier = StripeWebhookVerifier(settings)
    if not stripe_signature:
        raise ApplicationError(
            "The Stripe-Signature header is required.",
            code="missing_webhook_signature",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    validate_content_length(request, verifier.max_payload_bytes)
    payload = await request.body()
    if len(payload) > verifier.max_payload_bytes:
        raise ApplicationError(
            "The webhook payload is too large.",
            code="webhook_payload_too_large",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    event = verifier.verify(payload, stripe_signature)
    inserted = await StripeWebhookInbox().accept(session, event, payload)
    return WebhookAccepted(received=True, duplicate=not inserted)


@router.post(
    "/clerk",
    response_model=WebhookAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive a verified Clerk identity event",
)
async def receive_clerk_webhook(
    request: Request,
    session: DatabaseSession,
    svix_id: Annotated[str | None, Header(alias="svix-id")] = None,
    svix_timestamp: Annotated[str | None, Header(alias="svix-timestamp")] = None,
    svix_signature: Annotated[str | None, Header(alias="svix-signature")] = None,
) -> WebhookAccepted:
    if not svix_id or not svix_timestamp or not svix_signature:
        raise ApplicationError(
            "The required Svix signature headers are missing.",
            code="missing_webhook_signature",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    verifier = ClerkWebhookVerifier(get_settings())
    validate_content_length(request, verifier.max_payload_bytes)
    payload = await request.body()
    if len(payload) > verifier.max_payload_bytes:
        raise ApplicationError(
            "The webhook payload is too large.",
            code="webhook_payload_too_large",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    event = verifier.verify(
        payload,
        svix_id=svix_id,
        svix_timestamp=svix_timestamp,
        svix_signature=svix_signature,
    )
    inserted = await ClerkWebhookService().process(
        session,
        svix_id=svix_id,
        event=event,
        payload=payload,
        request_id=getattr(request.state, "request_id", None),
    )
    return WebhookAccepted(received=True, duplicate=not inserted)
