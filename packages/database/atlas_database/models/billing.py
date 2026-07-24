from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.atlas_database.base import (
    Base,
    ImmutableTimestampMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from packages.database.atlas_database.models.enums import SubscriptionStatus, WebhookEventStatus


class BillingCustomer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "billing_customers"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_billing_customers_tenant"),
        Index("ix_billing_customers_tenant", "tenant_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    livemode: Mapped[bool] = mapped_column(Boolean, nullable=False)


class BillingSubscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "billing_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "billing_customer_id", "stripe_subscription_id", name="uq_billing_subscription_customer"
        ),
        Index("ix_billing_subscriptions_customer_status", "billing_customer_id", "status"),
    )

    billing_customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("billing_customers.id", ondelete="RESTRICT"), nullable=False
    )
    stripe_subscription_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    stripe_product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="subscription_status",
            native_enum=False,
            length=24,
            create_constraint=True,
        ),
        nullable=False,
    )
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StripeWebhookEvent(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "stripe_webhook_events"
    __table_args__ = (
        Index("ix_stripe_webhook_events_status_created", "status", "stripe_created_at"),
    )

    stripe_event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    api_version: Mapped[str | None] = mapped_column(String(32))
    stripe_account_id: Mapped[str | None] = mapped_column(String(64))
    livemode: Mapped[bool] = mapped_column(Boolean, nullable=False)
    stripe_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(
            WebhookEventStatus,
            name="webhook_event_status",
            native_enum=False,
            length=16,
            create_constraint=True,
        ),
        default=WebhookEventStatus.PENDING,
        nullable=False,
    )
    processing_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(128))


class PaymentLedgerLink(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "payment_ledger_links"
    __table_args__ = (
        UniqueConstraint(
            "stripe_object_type", "stripe_object_id", name="uq_payment_ledger_stripe_object"
        ),
        UniqueConstraint("ledger_transaction_id", name="uq_payment_ledger_transaction"),
        ForeignKeyConstraint(
            ["ledger_transaction_id", "tenant_id"],
            ["ledger_transactions.id", "ledger_transactions.tenant_id"],
            name="fk_payment_ledger_links_transaction_tenant",
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    stripe_object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    stripe_object_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ledger_transaction_id: Mapped[UUID] = mapped_column(nullable=False)
