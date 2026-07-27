from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apps.api.src.core.config import Settings
from apps.api.src.market.providers import (
    ProviderCandleBatch,
    ProviderError,
    ProviderListingContext,
    ProviderQuote,
    ProviderVenue,
)
from packages.database.atlas_database.models.enums import MarketDataStatus


class ProviderDataQualityService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def currency(value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ProviderError(
                "The provider currency is invalid.", code="provider_response_invalid"
            )
        return normalized

    def timestamp(self, value: datetime, *, now: datetime | None = None) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ProviderError(
                "The provider timestamp must include a timezone.",
                code="provider_timestamp_invalid",
            )
        current = now or datetime.now(UTC)
        if value > current + timedelta(
            seconds=self.settings.market_provider_future_timestamp_tolerance_seconds
        ):
            raise ProviderError(
                "The provider timestamp is outside the accepted tolerance.",
                code="provider_timestamp_invalid",
            )
        return value.astimezone(UTC)

    def quote(
        self,
        result: ProviderQuote,
        expected: ProviderListingContext,
        *,
        now: datetime | None = None,
    ) -> ProviderQuote:
        if result.listing_id != expected.listing_id:
            raise ProviderError(
                "The provider returned a different listing.", code="provider_symbol_mismatch"
            )
        if result.provider_symbol != expected.provider_symbol:
            raise ProviderError(
                "The provider symbol does not match the configured mapping.",
                code="provider_symbol_mismatch",
            )
        if result.provider_venue_code != expected.provider_venue_code:
            raise ProviderError(
                "The provider venue does not match the configured mapping.",
                code="provider_symbol_mismatch",
            )
        if self.currency(result.currency) != self.currency(expected.currency):
            raise ProviderError(
                "The provider currency does not match the listing.",
                code="provider_currency_mismatch",
            )
        if not result.source_reference.strip():
            raise ProviderError(
                "The provider result has no source provenance.",
                code="provider_response_invalid",
            )
        provider_timestamp = self.timestamp(result.provider_timestamp, now=now)
        received_at = self.timestamp(result.received_at, now=now)
        stale_at = provider_timestamp + timedelta(
            seconds=self.settings.market_quote_stale_after_seconds
        )
        status = result.status
        if status == MarketDataStatus.LIVE and (now or datetime.now(UTC)) > stale_at:
            status = MarketDataStatus.STALE
        return result.model_copy(
            update={
                "provider_timestamp": provider_timestamp,
                "received_at": received_at,
                "currency": self.currency(result.currency),
                "status": status,
            }
        )

    def candles(
        self,
        result: ProviderCandleBatch,
        expected: ProviderListingContext,
        *,
        now: datetime | None = None,
    ) -> ProviderCandleBatch:
        if (
            result.listing_id != expected.listing_id
            or result.provider_symbol != expected.provider_symbol
            or result.provider_venue_code != expected.provider_venue_code
        ):
            raise ProviderError(
                "The provider candle identity does not match the configured mapping.",
                code="provider_symbol_mismatch",
            )
        if self.currency(result.currency) != self.currency(expected.currency):
            raise ProviderError(
                "The provider currency does not match the listing.",
                code="provider_currency_mismatch",
            )
        if not result.source_reference.strip():
            raise ProviderError(
                "The provider result has no source provenance.",
                code="provider_response_invalid",
            )
        received_at = self.timestamp(result.received_at, now=now)
        for candle in result.candles:
            self.timestamp(candle.period_start, now=now)
            self.timestamp(candle.period_end, now=now)
        return result.model_copy(
            update={"received_at": received_at, "currency": self.currency(result.currency)}
        )

    def venue(self, venue: ProviderVenue) -> ProviderVenue:
        if venue.mic is not None and (
            len(venue.mic) != 4 or not venue.mic.isalnum() or venue.mic != venue.mic.upper()
        ):
            raise ProviderError("The provider MIC is invalid.", code="provider_response_invalid")
        if len(venue.country_code) != 2 or not venue.country_code.isalpha():
            raise ProviderError(
                "The provider country code is invalid.", code="provider_response_invalid"
            )
        self.currency(venue.currency)
        try:
            ZoneInfo(venue.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ProviderError(
                "The provider timezone is invalid.", code="provider_response_invalid"
            ) from exc
        if not venue.provider_venue_code.strip() or not venue.source_reference.strip():
            raise ProviderError(
                "The provider venue identity is incomplete.", code="provider_response_invalid"
            )
        return venue
