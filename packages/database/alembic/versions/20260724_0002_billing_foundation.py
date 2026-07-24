"""Create Stripe billing projections and webhook inbox.

Revision ID: 20260724_0002
Revises: 20260724_0001
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0002"
down_revision: str | None = "20260724_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = sa.Uuid()


def audit_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    ]


def immutable_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "billing_customers",
        *audit_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("stripe_customer_id", sa.String(64), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_billing_customers_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_billing_customers"),
        sa.UniqueConstraint("stripe_customer_id", name="uq_billing_customers_stripe_customer_id"),
        sa.UniqueConstraint("tenant_id", name="uq_billing_customers_tenant"),
    )
    op.create_index(
        "ix_billing_customers_tenant", "billing_customers", ["tenant_id"], unique=False
    )
    op.create_table(
        "billing_subscriptions",
        *audit_columns(),
        sa.Column("billing_customer_id", UUID, nullable=False),
        sa.Column("stripe_subscription_id", sa.String(64), nullable=False),
        sa.Column("stripe_product_id", sa.String(64), nullable=False),
        sa.Column("stripe_price_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('incomplete','incomplete_expired','trialing','active','past_due',"
            "'canceled','unpaid','paused')",
            name="ck_billing_subscriptions_subscription_status",
        ),
        sa.ForeignKeyConstraint(
            ["billing_customer_id"],
            ["billing_customers.id"],
            name="fk_billing_subscriptions_billing_customer_id_billing_customers",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_billing_subscriptions"),
        sa.UniqueConstraint(
            "billing_customer_id",
            "stripe_subscription_id",
            name="uq_billing_subscription_customer",
        ),
        sa.UniqueConstraint(
            "stripe_subscription_id", name="uq_billing_subscriptions_stripe_subscription_id"
        ),
    )
    op.create_index(
        "ix_billing_subscriptions_customer_status",
        "billing_subscriptions",
        ["billing_customer_id", "status"],
        unique=False,
    )
    op.create_table(
        "stripe_webhook_events",
        *immutable_columns(),
        sa.Column("stripe_event_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("api_version", sa.String(32), nullable=True),
        sa.Column("stripe_account_id", sa.String(64), nullable=True),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("stripe_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("processing_attempts", sa.Integer(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(128), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','processing','processed','failed','ignored')",
            name="ck_stripe_webhook_events_webhook_event_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stripe_webhook_events"),
        sa.UniqueConstraint(
            "stripe_event_id", name="uq_stripe_webhook_events_stripe_event_id"
        ),
    )
    op.create_index(
        "ix_stripe_webhook_events_status_created",
        "stripe_webhook_events",
        ["status", "stripe_created_at"],
        unique=False,
    )
    op.create_table(
        "payment_ledger_links",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("stripe_object_type", sa.String(32), nullable=False),
        sa.Column("stripe_object_id", sa.String(64), nullable=False),
        sa.Column("ledger_transaction_id", UUID, nullable=False),
        sa.ForeignKeyConstraint(
            ["ledger_transaction_id", "tenant_id"],
            ["ledger_transactions.id", "ledger_transactions.tenant_id"],
            name="fk_payment_ledger_links_transaction_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_payment_ledger_links_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payment_ledger_links"),
        sa.UniqueConstraint(
            "ledger_transaction_id", name="uq_payment_ledger_transaction"
        ),
        sa.UniqueConstraint(
            "stripe_object_type",
            "stripe_object_id",
            name="uq_payment_ledger_stripe_object",
        ),
    )


def downgrade() -> None:
    op.drop_table("payment_ledger_links")
    op.drop_table("stripe_webhook_events")
    op.drop_table("billing_subscriptions")
    op.drop_table("billing_customers")
