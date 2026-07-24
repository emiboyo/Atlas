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
from packages.database.atlas_database.models.enums import AccountStatus, AccountType


class InvestmentAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investment_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "external_provider", "external_account_id", name="uq_accounts_provider_id"
        ),
        UniqueConstraint("id", "tenant_id", name="uq_investment_accounts_id_tenant"),
        CheckConstraint("length(base_currency) = 3", name="base_currency_iso_length"),
        Index("ix_investment_accounts_tenant_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(
            AccountType,
            name="account_type",
            native_enum=False,
            length=24,
            create_constraint=True,
        ),
        nullable=False,
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(
            AccountStatus,
            name="account_status",
            native_enum=False,
            length=16,
            create_constraint=True,
        ),
        default=AccountStatus.PENDING,
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    external_provider: Mapped[str | None] = mapped_column(String(64))
    external_account_id: Mapped[str | None] = mapped_column(String(128))

    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="account")


class Portfolio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_portfolios_tenant_name"),
        UniqueConstraint("id", "tenant_id", name="uq_portfolios_id_tenant"),
        ForeignKeyConstraint(
            ["investment_account_id", "tenant_id"],
            ["investment_accounts.id", "investment_accounts.tenant_id"],
            name="fk_portfolios_account_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_portfolios_tenant_account", "tenant_id", "investment_account_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    investment_account_id: Mapped[UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    account: Mapped[InvestmentAccount] = relationship(back_populates="portfolios")
    position_snapshots: Mapped[list["PositionSnapshot"]] = relationship(back_populates="portfolio")


class PositionSnapshot(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "position_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "instrument_id", "as_of", name="uq_position_snapshot_point"
        ),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("cost_basis >= 0", name="cost_basis_non_negative"),
        CheckConstraint("length(cost_basis_currency) = 3", name="cost_basis_currency_iso_length"),
        ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_position_snapshots_portfolio_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_position_snapshots_tenant_as_of", "tenant_id", "as_of"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    portfolio_id: Mapped[UUID] = mapped_column(nullable=False)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False
    )
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    cost_basis_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(128), nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="position_snapshots")
