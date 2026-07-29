from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.atlas_database.base import (
    Base,
    ImmutableTimestampMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from packages.database.atlas_database.models.enums import (
    BacktestEventType,
    BacktestRunStatus,
    ExplanationStatus,
    ResearchCompleteness,
    ResearchStrategyStatus,
)

DECIMAL = Numeric(38, 18)


class ResearchStrategy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_strategies"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_research_strategies_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="uq_research_strategies_tenant_name"),
        Index("ix_research_strategies_tenant_status", "tenant_id", "status"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(String(1000))
    research_purpose: Mapped[str] = mapped_column(String(500))
    status: Mapped[ResearchStrategyStatus] = mapped_column(
        Enum(
            ResearchStrategyStatus,
            native_enum=False,
            length=16,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=ResearchStrategyStatus.ACTIVE,
    )
    current_version_id: Mapped[UUID | None]
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(default=1)


class ResearchStrategyVersion(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "research_strategy_versions"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_research_versions_id_tenant"),
        UniqueConstraint("strategy_id", "version_number", name="uq_research_version_number"),
        UniqueConstraint("strategy_id", "idempotency_key", name="uq_research_version_idempotency"),
        ForeignKeyConstraint(
            ["strategy_id", "tenant_id"],
            ["research_strategies.id", "research_strategies.tenant_id"],
            name="fk_research_versions_strategy_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("version_number > 0", name="research_version_positive"),
        CheckConstraint("length(base_currency) = 3", name="research_version_currency"),
        Index("ix_research_versions_strategy_created", "strategy_id", "created_at"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    strategy_id: Mapped[UUID]
    version_number: Mapped[int]
    version_label: Mapped[str] = mapped_column(String(80))
    configuration: Mapped[dict[str, object]] = mapped_column(JSON)
    configuration_fingerprint: Mapped[str] = mapped_column(String(64))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    base_currency: Mapped[str] = mapped_column(String(3))
    benchmark_listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT")
    )
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BacktestRun(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_backtest_runs_id_tenant"),
        UniqueConstraint("strategy_id", "idempotency_key", name="uq_backtest_run_idempotency"),
        ForeignKeyConstraint(
            ["strategy_id", "tenant_id"],
            ["research_strategies.id", "research_strategies.tenant_id"],
            name="fk_backtest_runs_strategy_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["strategy_version_id", "tenant_id"],
            ["research_strategy_versions.id", "research_strategy_versions.tenant_id"],
            name="fk_backtest_runs_version_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("start_date < end_date", name="backtest_run_date_range"),
        CheckConstraint("starting_capital > 0", name="backtest_run_capital_positive"),
        CheckConstraint("fee_value >= 0", name="backtest_run_fee_nonnegative"),
        CheckConstraint(
            "slippage_bps >= 0 AND slippage_bps <= 1000", name="backtest_run_slippage_bounded"
        ),
        Index("ix_backtest_runs_tenant_status", "tenant_id", "status"),
        Index("ix_backtest_runs_strategy_requested", "strategy_id", "requested_at"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    strategy_id: Mapped[UUID]
    strategy_version_id: Mapped[UUID]
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT")
    )
    status: Mapped[BacktestRunStatus] = mapped_column(
        Enum(
            BacktestRunStatus,
            native_enum=False,
            length=16,
            values_callable=lambda e: [x.value for x in e],
        )
    )
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    configuration_fingerprint: Mapped[str] = mapped_column(String(64))
    data_fingerprint: Mapped[str | None] = mapped_column(String(64))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    starting_capital: Mapped[Decimal] = mapped_column(DECIMAL)
    base_currency: Mapped[str] = mapped_column(String(3))
    fee_model: Mapped[str] = mapped_column(String(32))
    fee_value: Mapped[Decimal] = mapped_column(DECIMAL)
    slippage_model: Mapped[str] = mapped_column(String(32))
    slippage_bps: Mapped[Decimal] = mapped_column(DECIMAL)
    execution_policy: Mapped[str] = mapped_column(String(24))
    sizing_policy: Mapped[str] = mapped_column(String(48))
    sizing_value: Mapped[Decimal] = mapped_column(DECIMAL)
    missing_data_policy: Mapped[str] = mapped_column(String(24))
    engine_version: Mapped[str] = mapped_column(String(32))
    software_version: Mapped[str] = mapped_column(String(64))
    requested_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(64))
    is_historical_simulation: Mapped[bool] = mapped_column(Boolean, default=True)


class BacktestEvent(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "backtest_events"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence", name="uq_backtest_event_sequence"),
        ForeignKeyConstraint(
            ["run_id", "tenant_id"],
            ["backtest_runs.id", "backtest_runs.tenant_id"],
            name="fk_backtest_events_run_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_backtest_events_run_sequence", "run_id", "sequence"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    run_id: Mapped[UUID]
    sequence: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT")
    )
    event_type: Mapped[BacktestEventType] = mapped_column(
        Enum(
            BacktestEventType,
            native_enum=False,
            length=32,
            values_callable=lambda e: [x.value for x in e],
        )
    )
    decision_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    simulated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    price: Mapped[Decimal] = mapped_column(DECIMAL)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL)
    gross_value: Mapped[Decimal] = mapped_column(DECIMAL)
    fee: Mapped[Decimal] = mapped_column(DECIMAL)
    slippage: Mapped[Decimal] = mapped_column(DECIMAL)
    cash_before: Mapped[Decimal] = mapped_column(DECIMAL)
    cash_after: Mapped[Decimal] = mapped_column(DECIMAL)
    position_before: Mapped[Decimal] = mapped_column(DECIMAL)
    position_after: Mapped[Decimal] = mapped_column(DECIMAL)
    triggered_rule_ids: Mapped[list[str]] = mapped_column(JSON)
    source_observation_ids: Mapped[list[str]] = mapped_column(JSON)


class BacktestEquityPoint(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "backtest_equity_points"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence", name="uq_backtest_equity_sequence"),
        ForeignKeyConstraint(
            ["run_id", "tenant_id"],
            ["backtest_runs.id", "backtest_runs.tenant_id"],
            name="fk_backtest_equity_run_tenant",
            ondelete="RESTRICT",
        ),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    run_id: Mapped[UUID]
    sequence: Mapped[int]
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cash: Mapped[Decimal] = mapped_column(DECIMAL)
    position_value: Mapped[Decimal] = mapped_column(DECIMAL)
    total_equity: Mapped[Decimal] = mapped_column(DECIMAL)
    running_peak: Mapped[Decimal] = mapped_column(DECIMAL)
    drawdown_amount: Mapped[Decimal] = mapped_column(DECIMAL)
    drawdown_percentage: Mapped[Decimal] = mapped_column(DECIMAL)


class BacktestResult(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "backtest_results"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_backtest_result_run"),
        ForeignKeyConstraint(
            ["run_id", "tenant_id"],
            ["backtest_runs.id", "backtest_runs.tenant_id"],
            name="fk_backtest_results_run_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_backtest_results_run", "run_id"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    run_id: Mapped[UUID]
    starting_value: Mapped[Decimal] = mapped_column(DECIMAL)
    ending_value: Mapped[Decimal] = mapped_column(DECIMAL)
    simulated_pnl: Mapped[Decimal] = mapped_column(DECIMAL)
    historical_return: Mapped[Decimal] = mapped_column(DECIMAL)
    event_count: Mapped[int]
    completed_trade_count: Mapped[int]
    maximum_drawdown: Mapped[Decimal] = mapped_column(DECIMAL)
    volatility: Mapped[Decimal | None] = mapped_column(DECIMAL)
    turnover: Mapped[Decimal] = mapped_column(DECIMAL)
    benchmark_return: Mapped[Decimal | None] = mapped_column(DECIMAL)
    missing_count: Mapped[int]
    stale_count: Mapped[int]
    unavailable_count: Mapped[int]
    excluded_count: Mapped[int]
    completeness: Mapped[ResearchCompleteness] = mapped_column(
        Enum(
            ResearchCompleteness,
            native_enum=False,
            length=16,
            values_callable=lambda e: [x.value for x in e],
        )
    )
    result_checksum: Mapped[str] = mapped_column(String(64))


class BacktestExplanation(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "backtest_explanations"
    __table_args__ = (
        UniqueConstraint("run_id", "idempotency_key", name="uq_backtest_explanation_idempotency"),
        ForeignKeyConstraint(
            ["run_id", "tenant_id"],
            ["backtest_runs.id", "backtest_runs.tenant_id"],
            name="fk_backtest_explanations_run_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_backtest_explanations_run_created", "run_id", "created_at"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    run_id: Mapped[UUID]
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    explanation_type: Mapped[str] = mapped_column(String(40))
    engine_identifier: Mapped[str] = mapped_column(String(64))
    engine_version: Mapped[str] = mapped_column(String(32))
    template_version: Mapped[str] = mapped_column(String(32))
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    output_fingerprint: Mapped[str] = mapped_column(String(64))
    explanation_text: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str] = mapped_column(String(1000))
    status: Mapped[ExplanationStatus] = mapped_column(
        Enum(
            ExplanationStatus,
            native_enum=False,
            length=16,
            values_callable=lambda e: [x.value for x in e],
        )
    )
    generated_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ResearchAuditEvent(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "research_audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["strategy_id", "tenant_id"],
            ["research_strategies.id", "research_strategies.tenant_id"],
            name="fk_research_audit_strategy_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_research_audit_strategy_created", "strategy_id", "created_at"),
        Index("ix_research_audit_run_created", "run_id", "created_at"),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    strategy_id: Mapped[UUID]
    strategy_version_id: Mapped[UUID | None]
    run_id: Mapped[UUID | None]
    event_type: Mapped[str] = mapped_column(String(80))
    request_id: Mapped[str | None] = mapped_column(String(64))
    operation_id: Mapped[str | None] = mapped_column(String(128))
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    target_id: Mapped[UUID | None]
    event_metadata: Mapped[dict[str, str]] = mapped_column(JSON)
