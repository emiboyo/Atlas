from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
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
    AccountStatus,
    AccountType,
    MarketDataStatus,
    PortfolioAccountRole,
    PortfolioStatus,
    PortfolioTransactionStatus,
    PortfolioTransactionType,
    PositionStatus,
    ValuationCompleteness,
)


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
            values_callable=lambda enum: [member.value for member in enum],
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
            values_callable=lambda enum: [member.value for member in enum],
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
        Index("ix_portfolios_tenant_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    investment_account_id: Mapped[UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PortfolioStatus] = mapped_column(
        Enum(
            PortfolioStatus,
            name="portfolio_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=PortfolioStatus.ACTIVE,
        nullable=False,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    benchmark_listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT")
    )

    account: Mapped[InvestmentAccount] = relationship(back_populates="portfolios")
    position_snapshots: Mapped[list["PositionSnapshot"]] = relationship(back_populates="portfolio")


class PortfolioAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolio_accounts"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "account_role", "currency", name="uq_portfolio_account_role_currency"
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_accounts_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["ledger_account_id", "tenant_id"],
            ["ledger_accounts.id", "ledger_accounts.tenant_id"],
            name="fk_portfolio_accounts_ledger_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("length(currency) = 3", name="currency_iso_length"),
        Index("ix_portfolio_accounts_tenant_portfolio", "tenant_id", "portfolio_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    portfolio_id: Mapped[UUID] = mapped_column(nullable=False)
    ledger_account_id: Mapped[UUID] = mapped_column(nullable=False, unique=True)
    account_role: Mapped[PortfolioAccountRole] = mapped_column(
        Enum(
            PortfolioAccountRole,
            name="portfolio_account_role",
            native_enum=False,
            length=40,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PortfolioTransaction(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "portfolio_transactions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "portfolio_id",
            "idempotency_key",
            name="uq_portfolio_transactions_idempotency",
        ),
        UniqueConstraint("portfolio_id", "sequence", name="uq_portfolio_transactions_sequence"),
        UniqueConstraint(
            "reversal_of_transaction_id",
            name="uq_portfolio_transactions_reversal_of_transaction_id",
        ),
        UniqueConstraint("ledger_transaction_id", name="uq_portfolio_transactions_ledger"),
        ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_transactions_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("length(currency) = 3", name="currency_iso_length"),
        CheckConstraint("gross_amount >= 0", name="gross_amount_non_negative"),
        CheckConstraint("fee_amount >= 0", name="fee_amount_non_negative"),
        CheckConstraint("net_amount >= 0", name="net_amount_non_negative"),
        CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="quantity_positive",
        ),
        CheckConstraint(
            "unit_price IS NULL OR unit_price >= 0",
            name="unit_price_non_negative",
        ),
        CheckConstraint("position_cost_delta IS NOT NULL", name="position_cost_delta_present"),
        Index(
            "ix_portfolio_transactions_tenant_portfolio_effective",
            "tenant_id",
            "portfolio_id",
            "effective_at",
        ),
        Index("ix_portfolio_transactions_listing", "listing_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    portfolio_id: Mapped[UUID] = mapped_column(nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    transaction_type: Mapped[PortfolioTransactionType] = mapped_column(
        Enum(
            PortfolioTransactionType,
            name="portfolio_transaction_type",
            native_enum=False,
            length=40,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    status: Mapped[PortfolioTransactionStatus] = mapped_column(
        Enum(
            PortfolioTransactionStatus,
            name="portfolio_transaction_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=PortfolioTransactionStatus.POSTED,
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(128))
    listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    position_quantity_delta: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    position_cost_delta: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    realised_pnl_delta: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reversal_of_transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("portfolio_transactions.id", ondelete="RESTRICT")
    )
    ledger_transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(500))
    transaction_metadata: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PortfolioPosition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolio_positions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "listing_id", name="uq_portfolio_positions_listing"),
        ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_positions_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("average_cost_per_unit >= 0", name="average_cost_non_negative"),
        CheckConstraint("cost_basis >= 0", name="cost_basis_non_negative"),
        CheckConstraint("length(currency) = 3", name="currency_iso_length"),
        Index("ix_portfolio_positions_tenant_portfolio", "tenant_id", "portfolio_id"),
        Index("ix_portfolio_positions_listing", "listing_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    portfolio_id: Mapped[UUID] = mapped_column(nullable=False)
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    average_cost_per_unit: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    realised_pnl: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    position_status: Mapped[PositionStatus] = mapped_column(
        Enum(
            PositionStatus,
            name="portfolio_position_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    last_transaction_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)


class PortfolioValuationSnapshot(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "portfolio_valuation_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "idempotency_key", name="uq_portfolio_valuation_snapshot_idempotency"
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_valuation_snapshots_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("length(base_currency) = 3", name="base_currency_iso_length"),
        Index(
            "ix_portfolio_valuation_snapshots_portfolio_as_of",
            "portfolio_id",
            "as_of",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    portfolio_id: Mapped[UUID] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_currency_total: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    completeness: Mapped[ValuationCompleteness] = mapped_column(
        Enum(
            ValuationCompleteness,
            name="valuation_completeness",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PortfolioValuationLine(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "portfolio_valuation_lines"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "listing_id", name="uq_portfolio_valuation_line_listing"),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("cost_basis >= 0", name="cost_basis_non_negative"),
        CheckConstraint("length(currency) = 3", name="currency_iso_length"),
        Index("ix_portfolio_valuation_lines_listing", "listing_id"),
    )

    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("portfolio_valuation_snapshots.id", ondelete="RESTRICT"), nullable=False
    )
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    latest_price: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    unrealised_pnl: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    provider: Mapped[str | None] = mapped_column(String(48))
    provider_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_status: Mapped[MarketDataStatus] = mapped_column(
        Enum(
            MarketDataStatus,
            name="valuation_market_data_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    source_reference: Mapped[str | None] = mapped_column(String(160))


class PortfolioAuditEvent(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "portfolio_audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_audit_events_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_portfolio_audit_events_portfolio_created", "portfolio_id", "created_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    portfolio_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))
    operation_id: Mapped[str | None] = mapped_column(String(128))
    actor_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    target_id: Mapped[UUID | None]
    event_metadata: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)


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
