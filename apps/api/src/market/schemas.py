from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packages.database.atlas_database.models.enums import (
    AssetClass,
    CandleInterval,
    InstrumentStatus,
    ListingStatus,
    MarketDataStatus,
    WatchlistStatus,
    WatchlistVisibility,
)


class ExchangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mic: str
    name: str
    acronym: str | None
    country_code: str
    timezone: str
    default_currency: str
    market_type: str
    status: str


class ListingSummary(BaseModel):
    id: UUID
    instrument_id: UUID
    symbol: str
    exchange: ExchangeResponse
    currency: str
    status: ListingStatus
    is_primary: bool
    data_availability: MarketDataStatus = MarketDataStatus.SIMULATED


class InstrumentSearchResult(BaseModel):
    instrument_id: UUID
    canonical_name: str
    short_name: str | None
    asset_class: AssetClass
    status: InstrumentStatus
    listing: ListingSummary


class InstrumentDetail(BaseModel):
    id: UUID
    canonical_name: str
    short_name: str | None
    description: str | None
    asset_class: AssetClass
    primary_currency: str
    country_code: str | None
    isin: str | None
    cusip: str | None
    sedol: str | None
    status: InstrumentStatus
    listings: list[ListingSummary]


class QuoteResult(BaseModel):
    listing_id: UUID
    instrument_id: UUID
    symbol: str
    exchange: str
    currency: str
    price: Decimal | None
    bid: Decimal | None = None
    ask: Decimal | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    previous_close: Decimal | None = None
    volume: int | None = None
    provider: str
    provider_timestamp: datetime
    received_at: datetime
    delay_seconds: int | None = None
    data_status: MarketDataStatus
    is_stale: bool
    stale_after: datetime
    source_label: str
    market_session: str
    disclaimer: str


class CandlePoint(BaseModel):
    period_start: datetime
    period_end: datetime
    open: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    low: Decimal = Field(ge=0)
    close: Decimal = Field(ge=0)
    adjusted_close: Decimal | None = Field(default=None, ge=0)
    volume: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_shape(self) -> "CandlePoint":
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start")
        if self.high < self.low:
            raise ValueError("high cannot be below low")
        if not self.low <= self.open <= self.high:
            raise ValueError("open must be within low and high")
        if not self.low <= self.close <= self.high:
            raise ValueError("close must be within low and high")
        return self


class CandleResult(BaseModel):
    listing_id: UUID
    interval: CandleInterval
    requested_start: datetime
    requested_end: datetime
    returned_start: datetime | None
    returned_end: datetime | None
    provider: str
    currency: str
    data_status: MarketDataStatus
    candles: list[CandlePoint]
    next_cursor: str | None = None
    disclaimer: str


class MarketStatusResponse(BaseModel):
    provider: str
    status: str
    data_status: MarketDataStatus
    source_label: str
    disclaimer: str


class WatchlistCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    visibility: WatchlistVisibility = WatchlistVisibility.TENANT


class WatchlistUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    visibility: WatchlistVisibility | None = None


class WatchlistItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_id: UUID
    notes: str | None = Field(default=None, max_length=500)


class WatchlistReorder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_ids: list[UUID] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def unique_items(self) -> "WatchlistReorder":
        if len(self.item_ids) != len(set(self.item_ids)):
            raise ValueError("item_ids must be unique")
        return self


class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_id: UUID
    position: int
    notes: str | None
    added_by_user_id: UUID
    created_at: datetime


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    visibility: WatchlistVisibility
    status: WatchlistStatus
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    items: list[WatchlistItemResponse] = Field(default_factory=list)


class MarketPage(BaseModel):
    items: list[InstrumentSearchResult]
    page: int
    page_size: int
    total: int
