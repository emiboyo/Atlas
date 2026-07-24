import hashlib
import hmac
import json
import time

import pytest

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.payments import StripeWebhookVerifier

WEBHOOK_SECRET = "whsec_test_secret"  # noqa: S105


def event_payload() -> bytes:
    return json.dumps(
        {
            "id": "evt_123",
            "object": "event",
            "api_version": "2025-06-30.basil",
            "created": int(time.time()),
            "data": {"object": {"id": "sub_123", "object": "subscription"}},
            "livemode": False,
            "pending_webhooks": 1,
            "request": {"id": None, "idempotency_key": None},
            "type": "customer.subscription.updated",
        },
        separators=(",", ":"),
    ).encode()


def sign(payload: bytes, secret: str = WEBHOOK_SECRET) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode() + payload
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_verifies_raw_stripe_webhook_signature() -> None:
    payload = event_payload()
    verifier = StripeWebhookVerifier(Settings(stripe_webhook_secret=WEBHOOK_SECRET))

    event = verifier.verify(payload, sign(payload))

    assert event["id"] == "evt_123"
    assert event["type"] == "customer.subscription.updated"


def test_rejects_invalid_signature() -> None:
    verifier = StripeWebhookVerifier(Settings(stripe_webhook_secret=WEBHOOK_SECRET))

    with pytest.raises(ApplicationError) as error:
        verifier.verify(event_payload(), "t=1,v1=invalid")

    assert error.value.code == "invalid_webhook_signature"


def test_rejects_unconfigured_webhook() -> None:
    verifier = StripeWebhookVerifier(Settings(stripe_webhook_secret=""))

    with pytest.raises(ApplicationError) as error:
        verifier.verify(event_payload(), "signature")

    assert error.value.status_code == 503
