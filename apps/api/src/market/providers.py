from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import status

from apps.api.src.core.errors import ApplicationError
from apps.api.src.market.schemas import CandlePoint
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MarketDataStatus,
    MarketSession,
)

SIMULATED_PROVIDER = "atlas_simulated"
SIMULATED_SOURCE = "Atlas deterministic development fixture"
NON_ADVISORY_DISCLAIMER = (
    "Simulated development data. For software testing only; not real-time market data "
    "and not investment advice."
)


class ProviderError(ApplicationError):
    def __init__(self, message: str, *, code: str, status_code: int = 503) -> None:
        super().__init__(message, code=code, status_code=status_code)


class ProviderQuote:
    def __init__(self, listing_id: UUID, price_seed: int) -> None:
        if price_seed < 0:
            raise ProviderError(
                "Provider returned an invalid price.", code="malformed_provider_response"
            )
        self.listing_id = listing_id
        self.provider = SIMULATED_PROVIDER
        self.provider_timestamp = datetime(2026, 1, 15, 16, 0, tzinfo=UTC)
        self.received_at = datetime(2026, 1, 15, 16, 0, 5, tzinfo=UTC)
        self.price = Decimal(price_seed) + Decimal("0.125")
        self.open = self.price - Decimal("0.500")
        self.high = self.price + Decimal("1.000")
        self.low = self.price - Decimal("1.000")
        self.previous_close = self.price - Decimal("0.250")
        self.volume = 100_000 + price_seed
        self.status = MarketDataStatus.SIMULATED
        self.session = MarketSession.CLOSED


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    async def get_latest_quote(self, listing_id: UUID) -> ProviderQuote: ...

    @abstractmethod
    async def get_historical_candles(
        self,
        listing_id: UUID,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> list[CandlePoint]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...


class DeterministicFixtureProvider(MarketDataProvider):
    name = SIMULATED_PROVIDER

    async def get_latest_quote(self, listing_id: UUID) -> ProviderQuote:
        return ProviderQuote(listing_id, (listing_id.int % 900) + 100)

    async def get_historical_candles(
        self,
        listing_id: UUID,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> list[CandlePoint]:
        if interval not in {CandleInterval.ONE_DAY, CandleInterval.ONE_WEEK}:
            raise ProviderError(
                "The requested interval is not supported by this provider.",
                code="unsupported_interval",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        step = timedelta(days=1 if interval == CandleInterval.ONE_DAY else 7)
        anchor = datetime(2026, 1, 1, tzinfo=UTC)
        cursor = max(start, anchor)
        fixture_end = min(end, datetime(2026, 1, 15, tzinfo=UTC))
        seed = Decimal((listing_id.int % 900) + 100)
        candles: list[CandlePoint] = []
        index = 0
        while cursor < fixture_end and len(candles) < 500:
            value = seed + Decimal(index)
            candles.append(
                CandlePoint(
                    period_start=cursor,
                    period_end=cursor + step,
                    open=value,
                    high=value + Decimal("2"),
                    low=value - Decimal("1"),
                    close=value + Decimal("1"),
                    adjusted_close=value + Decimal("1"),
                    volume=100_000 + index,
                )
            )
            cursor += step
            index += 1
        return candles

    async def health_check(self) -> bool:
        return True


class DisabledExternalProvider(MarketDataProvider):
    name = "external_disabled"

    async def get_latest_quote(self, listing_id: UUID) -> ProviderQuote:
        del listing_id
        raise ProviderError("External market data is not configured.", code="provider_unavailable")

    async def get_historical_candles(
        self,
        listing_id: UUID,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> list[CandlePoint]:
        del listing_id, interval, start, end
        raise ProviderError("External market data is not configured.", code="provider_unavailable")

    async def health_check(self) -> bool:
        return False
