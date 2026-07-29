from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from packages.database.atlas_database.models.enums import (
    BacktestEventType,
    BacktestRunStatus,
    ExplanationStatus,
    ResearchCompleteness,
    ResearchStrategyStatus,
)

NOTICE = (
    "Historical simulation only — not investment advice and not a prediction of future performance."
)
IdempotencyKey = Annotated[str, StringConstraints(min_length=8, max_length=128)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Money = Annotated[Decimal, Field(max_digits=38, decimal_places=18, ge=0)]
Positive = Annotated[Decimal, Field(max_digits=38, decimal_places=18, gt=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrategyCreate(StrictModel):
    tenant_id: UUID
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    description: Annotated[str | None, StringConstraints(max_length=1000)] = None
    research_purpose: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)
    ]


class StrategyUpdate(StrictModel):
    name: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
    ] = None
    description: Annotated[str | None, StringConstraints(max_length=1000)] = None
    research_purpose: Annotated[str | None, StringConstraints(max_length=500)] = None
    version: int = Field(ge=1)


class StrategyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    research_purpose: str
    status: ResearchStrategyStatus
    current_version_id: UUID | None
    created_by_user_id: UUID
    version: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    notice: str = NOTICE


class StrategyPage(BaseModel):
    items: list[StrategyResponse]
    offset: int
    limit: int


class ResearchRule(StrictModel):
    id: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,39}$")]
    rule_type: Literal["sma_crossover"]
    schema_version: Literal[1] = 1
    short_window: int = Field(ge=2, le=100)
    long_window: int = Field(ge=3, le=250)

    @model_validator(mode="after")
    def ordered_windows(self) -> "ResearchRule":
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be less than long_window")
        return self


class VersionCreate(StrictModel):
    version_label: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    base_currency: Currency
    listing_id: UUID
    benchmark_listing_id: UUID | None = None
    rules: list[ResearchRule] = Field(min_length=1, max_length=10)


class VersionResponse(BaseModel):
    id: UUID
    strategy_id: UUID
    tenant_id: UUID
    version_number: int
    version_label: str
    configuration: dict[str, object]
    configuration_fingerprint: str
    base_currency: str
    benchmark_listing_id: UUID | None
    created_by_user_id: UUID
    created_at: datetime
    superseded_at: datetime | None
    notice: str = NOTICE


class BacktestCreate(StrictModel):
    strategy_id: UUID
    strategy_version_id: UUID
    start_date: date
    end_date: date
    starting_capital: Positive
    fee_model: Literal["zero_fee", "fixed_amount_per_event", "percentage_of_gross_value"]
    fee_value: Money = Decimal("0")
    slippage_model: Literal["zero_slippage", "fixed_basis_points"]
    slippage_bps: Money = Decimal("0")
    execution_policy: Literal["next_open", "same_close", "next_close"]
    sizing_policy: Literal[
        "fixed_simulated_cash_amount",
        "fixed_percentage_of_available_simulated_cash",
        "fixed_quantity",
    ]
    sizing_value: Positive
    missing_data_policy: Literal["fail_run", "skip_event", "skip_observation"]

    @model_validator(mode="after")
    def bounded(self) -> "BacktestCreate":
        if self.start_date >= self.end_date or (self.end_date - self.start_date).days > 3650:
            raise ValueError("date range must be positive and no longer than ten years")
        if self.slippage_bps > Decimal("1000"):
            raise ValueError("slippage_bps cannot exceed 1000")
        if self.fee_model == "percentage_of_gross_value" and self.fee_value > Decimal("10"):
            raise ValueError("percentage fee cannot exceed 10")
        if self.sizing_policy == "fixed_percentage_of_available_simulated_cash" and (
            self.sizing_value > Decimal("100")
        ):
            raise ValueError("cash percentage cannot exceed 100")
        return self


class RunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    strategy_id: UUID
    strategy_version_id: UUID
    listing_id: UUID
    status: BacktestRunStatus
    configuration_fingerprint: str
    data_fingerprint: str | None
    start_date: date
    end_date: date
    starting_capital: Decimal
    base_currency: str
    fee_model: str
    fee_value: Decimal
    slippage_model: str
    slippage_bps: Decimal
    execution_policy: str
    sizing_policy: str
    sizing_value: Decimal
    missing_data_policy: str
    engine_version: str
    software_version: str
    requested_at: datetime
    completed_at: datetime | None
    failure_code: str | None
    is_historical_simulation: bool
    notice: str = NOTICE


class EventResponse(BaseModel):
    id: UUID
    sequence: int
    listing_id: UUID
    event_type: BacktestEventType
    decision_at: datetime
    simulated_at: datetime
    price: Decimal
    quantity: Decimal
    gross_value: Decimal
    fee: Decimal
    slippage: Decimal
    cash_before: Decimal
    cash_after: Decimal
    position_before: Decimal
    position_after: Decimal
    triggered_rule_ids: list[str]
    source_observation_ids: list[str]


class EquityResponse(BaseModel):
    sequence: int
    observed_at: datetime
    cash: Decimal
    position_value: Decimal
    total_equity: Decimal
    running_peak: Decimal
    drawdown_amount: Decimal
    drawdown_percentage: Decimal


class ResultResponse(BaseModel):
    run_id: UUID
    starting_value: Decimal
    ending_value: Decimal
    simulated_pnl: Decimal
    historical_return: Decimal
    event_count: int
    completed_trade_count: int
    maximum_drawdown: Decimal
    volatility: Decimal | None
    turnover: Decimal
    benchmark_return: Decimal | None
    missing_count: int
    stale_count: int
    unavailable_count: int
    excluded_count: int
    completeness: ResearchCompleteness
    result_checksum: str
    notice: str = NOTICE


class DataQualityResponse(BaseModel):
    run_id: UUID
    completeness: ResearchCompleteness
    missing_count: int
    stale_count: int
    unavailable_count: int
    excluded_count: int
    data_fingerprint: str | None
    notice: str = NOTICE


class ComparisonResponse(BaseModel):
    runs: list[ResultResponse]
    comparable: bool
    comparison_basis: str
    notice: str = NOTICE


class ComparisonCreate(StrictModel):
    run_ids: list[UUID] = Field(min_length=2, max_length=10)


class ExplanationCreate(StrictModel):
    explanation_type: Literal[
        "strategy_summary",
        "run_summary",
        "rule_trigger_explanation",
        "data_quality_explanation",
        "limitation_summary",
        "overfitting_warning",
    ]


class ExplanationResponse(BaseModel):
    id: UUID
    run_id: UUID
    explanation_type: str
    engine_identifier: str
    engine_version: str
    template_version: str
    explanation_text: str
    limitations: str
    status: ExplanationStatus
    generated_at: datetime
    notice: str = NOTICE


class AuditEventResponse(BaseModel):
    id: UUID
    strategy_id: UUID
    strategy_version_id: UUID | None
    run_id: UUID | None
    event_type: str
    request_id: str | None
    operation_id: str | None
    actor_user_id: UUID
    target_id: UUID | None
    event_metadata: dict[str, str]
    created_at: datetime


class EffectivePermissions(BaseModel):
    can_read: bool
    can_update: bool
    can_archive: bool
    can_create_version: bool
    can_create_backtest: bool
    can_compare: bool
    can_explain: bool
    can_read_audit: bool
