from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from fastapi import status
from pydantic import BaseModel, ConfigDict, Field

from apps.api.src.core.errors import ApplicationError
from apps.api.src.market.schemas import CandlePoint
from packages.database.atlas_database.models.enums import (
    AssetClass,
    CandleInterval,
    ListingStatus,
    MarketDataStatus,
    MarketSession,
)

SIMULATED_PROVIDER = "atlas_simulated"
SIMULATED_SOURCE = "Atlas deterministic development fixture"
NON_ADVISORY_DISCLAIMER = (
    "Simulated development data. For software testing only; not real-time market data "
    "and not investment advice."
)


class FrozenProviderModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ProviderListingContext(FrozenProviderModel):
    listing_id: UUID
    provider_symbol: str
    provider_venue_code: str
    currency: str


class ProviderInstrument(FrozenProviderModel):
    provider: str
    provider_instrument_id: str
    provider_symbol: str
    provider_exchange_code: str
    canonical_name: str
    asset_class: AssetClass
    currency: str
    country_code: str | None = None
    isin: str | None = None
    cusip: str | None = None
    sedol: str | None = None
    listing_status: ListingStatus
    source_reference: str
    retrieved_at: datetime


class ProviderVenue(FrozenProviderModel):
    provider: str
    provider_venue_code: str
    name: str
    mic: str | None = None
    country_code: str
    timezone: str
    currency: str
    status: str
    source_reference: str
    retrieved_at: datetime


class ProviderRateLimitStatus(FrozenProviderModel):
    provider: str
    status: str
    limit: int | None = Field(default=None, ge=0)
    remaining: int | None = Field(default=None, ge=0)
    reset_at: datetime | None = None
    retry_after_seconds: int | None = Field(default=None, ge=0)
    observed_at: datetime


class ProviderHealth(FrozenProviderModel):
    provider: str
    available: bool
    observed_at: datetime
    message: str | None = None


class ProviderQuote(FrozenProviderModel):
    listing_id: UUID
    provider: str
    provider_symbol: str
    provider_venue_code: str
    source_reference: str
    provider_timestamp: datetime
    received_at: datetime
    currency: str
    price: Decimal | None = Field(default=None, ge=0)
    bid: Decimal | None = Field(default=None, ge=0)
    ask: Decimal | None = Field(default=None, ge=0)
    open: Decimal | None = Field(default=None, ge=0)
    high: Decimal | None = Field(default=None, ge=0)
    low: Decimal | None = Field(default=None, ge=0)
    previous_close: Decimal | None = Field(default=None, ge=0)
    volume: int | None = Field(default=None, ge=0)
    delay_seconds: int | None = Field(default=None, ge=0)
    status: MarketDataStatus
    session: MarketSession


class ProviderCandleBatch(FrozenProviderModel):
    listing_id: UUID
    provider: str
    provider_symbol: str
    provider_venue_code: str
    source_reference: str
    received_at: datetime
    currency: str
    data_status: MarketDataStatus
    interval: CandleInterval
    candles: tuple[CandlePoint, ...]


class ProviderError(ApplicationError):
    allowed_codes: ClassVar[set[str]] = {
        "provider_unavailable",
        "provider_timeout",
        "provider_rate_limited",
        "provider_authentication_failed",
        "provider_response_invalid",
        "provider_symbol_not_found",
        "unsupported_interval",
        "unsupported_capability",
        "provider_currency_mismatch",
        "provider_symbol_mismatch",
        "provider_timestamp_invalid",
    }

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        retry_after_seconds: int | None = None,
    ) -> None:
        if code not in self.allowed_codes:
            raise ValueError("Unsupported provider error code")
        super().__init__(message, code=code, status_code=status_code)
        self.retry_after_seconds = retry_after_seconds


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    async def search_instruments(
        self, query: str, limit: int
    ) -> tuple[ProviderInstrument, ...]: ...

    @abstractmethod
    async def get_instrument(self, provider_instrument_id: str) -> ProviderInstrument: ...

    @abstractmethod
    async def get_exchange_reference_data(self) -> tuple[ProviderVenue, ...]: ...

    @abstractmethod
    async def get_latest_quote(self, listing: ProviderListingContext) -> ProviderQuote: ...

    @abstractmethod
    async def get_historical_candles(
        self,
        listing: ProviderListingContext,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> ProviderCandleBatch: ...

    @abstractmethod
    async def get_health(self) -> ProviderHealth: ...

    @abstractmethod
    async def get_rate_limit_status(self) -> ProviderRateLimitStatus: ...


class DeterministicFixtureProvider(MarketDataProvider):
    name = SIMULATED_PROVIDER
    observed_at = datetime(2026, 1, 15, 16, tzinfo=UTC)

    def _instruments(self) -> tuple[ProviderInstrument, ...]:
        return (
            ProviderInstrument(
                provider=self.name,
                provider_instrument_id="fixture-nova-xdev",
                provider_symbol="NOVA.XDEV",
                provider_exchange_code="XDEV",
                canonical_name="Nova Systems Development Equity",
                asset_class=AssetClass.EQUITY,
                currency="GBP",
                country_code="GB",
                listing_status=ListingStatus.ACTIVE,
                source_reference="fixture:instrument:nova-xdev",
                retrieved_at=self.observed_at,
            ),
        )

    async def search_instruments(self, query: str, limit: int) -> tuple[ProviderInstrument, ...]:
        normalized = query.strip().casefold()
        return tuple(
            item
            for item in self._instruments()
            if normalized in item.provider_symbol.casefold()
            or normalized in item.canonical_name.casefold()
        )[:limit]

    async def get_instrument(self, provider_instrument_id: str) -> ProviderInstrument:
        for item in self._instruments():
            if item.provider_instrument_id == provider_instrument_id:
                return item
        raise ProviderError(
            "The provider instrument was not found.",
            code="provider_symbol_not_found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    async def get_exchange_reference_data(self) -> tuple[ProviderVenue, ...]:
        return (
            ProviderVenue(
                provider=self.name,
                provider_venue_code="XDEV",
                name="Atlas Development Exchange",
                mic="XDEV",
                country_code="GB",
                timezone="Europe/London",
                currency="GBP",
                status="active",
                source_reference="fixture:venue:xdev",
                retrieved_at=self.observed_at,
            ),
        )

    async def get_latest_quote(self, listing: ProviderListingContext) -> ProviderQuote:
        price_seed = (listing.listing_id.int % 900) + 100
        price = Decimal(price_seed) + Decimal("0.125")
        return ProviderQuote(
            listing_id=listing.listing_id,
            provider=self.name,
            provider_symbol=listing.provider_symbol,
            provider_venue_code=listing.provider_venue_code,
            source_reference=f"fixture:quote:{listing.listing_id}",
            provider_timestamp=self.observed_at,
            received_at=self.observed_at + timedelta(seconds=5),
            currency=listing.currency,
            price=price,
            open=price - Decimal("0.500"),
            high=price + Decimal("1.000"),
            low=price - Decimal("1.000"),
            previous_close=price - Decimal("0.250"),
            volume=100_000 + price_seed,
            status=MarketDataStatus.SIMULATED,
            session=MarketSession.CLOSED,
        )

    async def get_historical_candles(
        self,
        listing: ProviderListingContext,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> ProviderCandleBatch:
        if interval not in {CandleInterval.ONE_DAY, CandleInterval.ONE_WEEK}:
            raise ProviderError(
                "The requested interval is not supported by this provider.",
                code="unsupported_interval",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        step = timedelta(days=1 if interval == CandleInterval.ONE_DAY else 7)
        cursor = max(start, datetime(2026, 1, 1, tzinfo=UTC))
        fixture_end = min(end, datetime(2026, 1, 15, tzinfo=UTC))
        seed = Decimal((listing.listing_id.int % 900) + 100)
        candles: list[CandlePoint] = []
        while cursor < fixture_end and len(candles) < 500:
            value = seed + Decimal(len(candles))
            candles.append(
                CandlePoint(
                    period_start=cursor,
                    period_end=cursor + step,
                    open=value,
                    high=value + Decimal("2"),
                    low=value - Decimal("1"),
                    close=value + Decimal("1"),
                    adjusted_close=value + Decimal("1"),
                    volume=100_000 + len(candles),
                )
            )
            cursor += step
        return ProviderCandleBatch(
            listing_id=listing.listing_id,
            provider=self.name,
            provider_symbol=listing.provider_symbol,
            provider_venue_code=listing.provider_venue_code,
            source_reference=f"fixture:candles:{listing.listing_id}:{interval.value}",
            received_at=self.observed_at,
            currency=listing.currency,
            data_status=MarketDataStatus.SIMULATED,
            interval=interval,
            candles=tuple(candles),
        )

    async def get_health(self) -> ProviderHealth:
        return ProviderHealth(provider=self.name, available=True, observed_at=self.observed_at)

    async def get_rate_limit_status(self) -> ProviderRateLimitStatus:
        return ProviderRateLimitStatus(
            provider=self.name,
            status="not_applicable",
            observed_at=self.observed_at,
        )


class DisabledExternalProvider(MarketDataProvider):
    name = "external_disabled"

    @staticmethod
    def _unavailable() -> ProviderError:
        return ProviderError("External market data is not configured.", code="provider_unavailable")

    async def search_instruments(self, query: str, limit: int) -> tuple[ProviderInstrument, ...]:
        del query, limit
        raise self._unavailable()

    async def get_instrument(self, provider_instrument_id: str) -> ProviderInstrument:
        del provider_instrument_id
        raise self._unavailable()

    async def get_exchange_reference_data(self) -> tuple[ProviderVenue, ...]:
        raise self._unavailable()

    async def get_latest_quote(self, listing: ProviderListingContext) -> ProviderQuote:
        del listing
        raise self._unavailable()

    async def get_historical_candles(
        self,
        listing: ProviderListingContext,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> ProviderCandleBatch:
        del listing, interval, start, end
        raise self._unavailable()

    async def get_health(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=False,
            observed_at=datetime.now(UTC),
            message="External provider disabled",
        )

    async def get_rate_limit_status(self) -> ProviderRateLimitStatus:
        return ProviderRateLimitStatus(
            provider=self.name,
            status="unavailable",
            observed_at=datetime.now(UTC),
        )
