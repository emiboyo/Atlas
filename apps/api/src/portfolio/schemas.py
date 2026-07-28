from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from packages.database.atlas_database.models.enums import (
    AssetClass,
    MarketDataStatus,
    PortfolioStatus,
    PortfolioTransactionStatus,
    PortfolioTransactionType,
    PositionStatus,
    ValuationCompleteness,
)

Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
IdempotencyKey = Annotated[str, StringConstraints(min_length=8, max_length=128)]
Money = Annotated[Decimal, Field(max_digits=38, decimal_places=18, ge=0)]
PositiveDecimal = Annotated[Decimal, Field(max_digits=38, decimal_places=18, gt=0)]

SIMULATION_NOTICE = "Simulated portfolio — no real money or orders."
INFORMATIONAL_DISCLAIMER = (
    "Simulated and informational only. This is not investment, financial, tax, or other advice."
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PortfolioCreate(StrictModel):
    tenant_id: UUID
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    description: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=1000)
    ] = None
    base_currency: Currency


class PortfolioUpdate(StrictModel):
    name: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
    ] = None
    description: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=1000)
    ] = None
    benchmark_listing_id: UUID | None = None
    version: int = Field(ge=1)


class EffectivePortfolioPermissions(BaseModel):
    can_read: bool
    can_update: bool
    can_archive: bool
    can_create_transaction: bool
    can_read_transactions: bool
    can_read_analytics: bool
    can_read_audit: bool


class PortfolioResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    base_currency: str
    status: PortfolioStatus
    benchmark_listing_id: UUID | None
    version: int
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    is_simulated: bool = True
    simulation_notice: str = SIMULATION_NOTICE


class PortfolioPage(BaseModel):
    items: list[PortfolioResponse]
    offset: int
    limit: int


class TransactionCreate(StrictModel):
    transaction_type: PortfolioTransactionType
    currency: Currency
    listing_id: UUID | None = None
    quantity: PositiveDecimal | None = None
    unit_price: Money | None = None
    amount: PositiveDecimal | None = None
    fee_amount: Money = Decimal("0")
    split_ratio: PositiveDecimal | None = None
    effective_at: datetime
    external_reference: Annotated[str | None, StringConstraints(max_length=128)] = None
    reason: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=500)] = None
    metadata: dict[
        Annotated[str, StringConstraints(max_length=40)],
        Annotated[str, StringConstraints(max_length=160)],
    ] = Field(default_factory=dict, max_length=10)

    @field_validator("effective_at")
    @classmethod
    def timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("effective_at must include a timezone")
        return value

    @model_validator(mode="after")
    def valid_shape(self) -> "TransactionCreate":
        security_forbidden = {PortfolioTransactionType.REVERSAL}
        if self.transaction_type in security_forbidden:
            raise ValueError("reversals use the dedicated reversal endpoint")
        trade_types = {
            PortfolioTransactionType.SIMULATED_BUY,
            PortfolioTransactionType.SIMULATED_SELL,
        }
        listing_types = trade_types | {
            PortfolioTransactionType.SIMULATED_DIVIDEND,
            PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT,
        }
        if self.transaction_type in listing_types and self.listing_id is None:
            raise ValueError("listing_id is required for this simulated transaction")
        if self.transaction_type in trade_types and (
            self.quantity is None or self.unit_price is None
        ):
            raise ValueError("quantity and unit_price are required for a simulated buy or sell")
        if self.transaction_type == PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT:
            if self.split_ratio is None:
                raise ValueError("split_ratio is required for a simulated split adjustment")
        elif (
            self.transaction_type
            in {
                PortfolioTransactionType.VIRTUAL_DEPOSIT,
                PortfolioTransactionType.VIRTUAL_WITHDRAWAL,
                PortfolioTransactionType.SIMULATED_DIVIDEND,
                PortfolioTransactionType.SIMULATED_FEE,
            }
            and self.amount is None
        ):
            raise ValueError("amount is required for this simulated transaction")
        return self


class ReversalCreate(StrictModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
    effective_at: datetime

    @field_validator("effective_at")
    @classmethod
    def timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("effective_at must include a timezone")
        return value


class TransactionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    tenant_id: UUID
    sequence: int
    transaction_type: PortfolioTransactionType
    status: PortfolioTransactionStatus
    idempotency_key: str
    external_reference: str | None
    listing_id: UUID | None
    currency: str
    quantity: Decimal | None
    unit_price: Decimal | None
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    effective_at: datetime
    recorded_at: datetime
    created_by_user_id: UUID
    reversal_of_transaction_id: UUID | None
    reason: str | None
    is_simulated: bool
    simulation_notice: str = SIMULATION_NOTICE


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    offset: int
    limit: int


class HoldingResponse(BaseModel):
    listing_id: UUID
    instrument_id: UUID
    symbol: str
    exchange: str
    asset_class: AssetClass
    currency: str
    quantity: Decimal
    average_cost_per_unit: Decimal
    cost_basis: Decimal
    realised_simulated_pnl: Decimal
    position_status: PositionStatus
    is_simulated: bool = True


class ValuedHolding(HoldingResponse):
    latest_price: Decimal | None
    market_value: Decimal | None
    unrealised_simulated_pnl: Decimal | None
    provider: str | None
    provider_timestamp: datetime | None
    received_at: datetime | None
    data_status: MarketDataStatus
    is_stale: bool
    valuation_status: str


class CashBalance(BaseModel):
    currency: str
    amount: Decimal
    is_simulated: bool = True


class ValuationResponse(BaseModel):
    portfolio_id: UUID
    as_of: datetime
    base_currency: str
    virtual_cash_by_currency: list[CashBalance]
    positions: list[ValuedHolding]
    subtotal_by_currency: dict[str, Decimal]
    base_currency_total: Decimal | None
    completeness: ValuationCompleteness
    is_complete: bool
    missing_listing_ids: list[UUID]
    stale_listing_ids: list[UUID]
    unavailable_listing_ids: list[UUID]
    unconverted_currencies: list[str]
    data_status_summary: dict[str, int]
    source_summary: list[str]
    is_simulated: bool = True
    simulation_notice: str = SIMULATION_NOTICE
    disclaimer: str = INFORMATIONAL_DISCLAIMER


class ValuationSnapshotResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    as_of: datetime
    base_currency: str
    base_currency_total: Decimal | None
    completeness: ValuationCompleteness
    created_at: datetime
    is_simulated: bool


class AllocationItem(BaseModel):
    label: str
    currency: str
    value: Decimal
    percentage: Decimal | None


class AnalyticsResponse(BaseModel):
    portfolio_id: UUID
    as_of: datetime
    total_value_by_currency: dict[str, Decimal]
    virtual_cash_by_currency: dict[str, Decimal]
    allocation: list[AllocationItem]
    asset_class_allocation: list[AllocationItem]
    largest_positions: list[ValuedHolding]
    realised_simulated_pnl: Decimal
    unrealised_simulated_pnl: Decimal | None
    currency_exposure: dict[str, Decimal]
    data_complete: bool
    is_simulated: bool = True
    disclaimer: str = INFORMATIONAL_DISCLAIMER


class HistoryPoint(BaseModel):
    as_of: datetime
    value: Decimal
    percentage_change: Decimal | None


class HistoryResponse(BaseModel):
    portfolio_id: UUID
    currency: str
    points: list[HistoryPoint]
    is_simulated: bool = True
    disclaimer: str = INFORMATIONAL_DISCLAIMER


class StatisticalAnalytics(BaseModel):
    portfolio_id: UUID
    metric: str
    value: Decimal | None
    time_range_start: datetime | None
    time_range_end: datetime | None
    frequency: str = "valuation_snapshot"
    observations: int
    missing_data_policy: str = "Incomplete or non-base-currency snapshots are excluded."
    is_simulated: bool = True
    disclaimer: str = INFORMATIONAL_DISCLAIMER


class BenchmarkAnalytics(BaseModel):
    portfolio_id: UUID
    benchmark_listing_id: UUID | None
    aligned_observations: int
    portfolio_percentage_change: Decimal | None
    benchmark_percentage_change: Decimal | None
    status: str
    missing_dates: list[date] = Field(default_factory=list)
    data_status_summary: dict[str, int] = Field(default_factory=dict)
    is_simulated: bool = True
    disclaimer: str = INFORMATIONAL_DISCLAIMER


class AuditEventResponse(BaseModel):
    id: UUID
    event_type: str
    request_id: str | None
    operation_id: str | None
    actor_user_id: UUID
    tenant_id: UUID
    portfolio_id: UUID
    target_id: UUID | None
    created_at: datetime
    event_metadata: dict[str, str]
