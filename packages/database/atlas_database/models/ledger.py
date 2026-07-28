from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.database.atlas_database.base import (
    Base,
    ImmutableTimestampMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from packages.database.atlas_database.models.enums import (
    LedgerAccountType,
    LedgerTransactionStatus,
)


class LedgerAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", "currency", name="uq_ledger_accounts_code_currency"),
        UniqueConstraint("id", "tenant_id", name="uq_ledger_accounts_id_tenant"),
        CheckConstraint("length(currency) = 3", name="currency_iso_length"),
        Index("ix_ledger_accounts_tenant_type", "tenant_id", "account_type"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    account_type: Mapped[LedgerAccountType] = mapped_column(
        Enum(
            LedgerAccountType,
            name="ledger_account_type",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    entries: Mapped[list["LedgerEntry"]] = relationship(
        back_populates="account", overlaps="entries,transaction"
    )


class LedgerTransaction(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_ledger_transactions_idempotency"),
        UniqueConstraint("id", "tenant_id", name="uq_ledger_transactions_id_tenant"),
        Index("ix_ledger_transactions_tenant_effective", "tenant_id", "effective_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[LedgerTransactionStatus] = mapped_column(
        Enum(
            LedgerTransactionStatus,
            name="ledger_transaction_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=LedgerTransactionStatus.DRAFT,
        nullable=False,
    )
    reversal_of_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), unique=True
    )

    entries: Mapped[list["LedgerEntry"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan", overlaps="account,entries"
    )


class LedgerEntry(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("amount <> 0", name="amount_non_zero"),
        ForeignKeyConstraint(
            ["transaction_id", "tenant_id"],
            ["ledger_transactions.id", "ledger_transactions.tenant_id"],
            name="fk_ledger_entries_transaction_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["ledger_account_id", "tenant_id"],
            ["ledger_accounts.id", "ledger_accounts.tenant_id"],
            name="fk_ledger_entries_account_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_ledger_entries_tenant_transaction", "tenant_id", "transaction_id"),
        Index("ix_ledger_entries_account_created", "ledger_account_id", "created_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    transaction_id: Mapped[UUID] = mapped_column(nullable=False)
    ledger_account_id: Mapped[UUID] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    memo: Mapped[str | None] = mapped_column(String(500))

    transaction: Mapped[LedgerTransaction] = relationship(
        back_populates="entries", overlaps="account,entries"
    )
    account: Mapped[LedgerAccount] = relationship(
        back_populates="entries", overlaps="entries,transaction"
    )
