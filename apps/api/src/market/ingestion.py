from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import Settings
from apps.api.src.market.administration import MarketAdministrationService
from apps.api.src.market.execution import ProviderExecutor
from apps.api.src.market.providers import (
    MarketDataProvider,
    ProviderError,
    ProviderListingContext,
)
from apps.api.src.market.quality import ProviderDataQualityService
from packages.database.atlas_database.models.enums import CandleInterval
from packages.database.atlas_database.models.instruments import (
    HistoricalCandle,
    InstrumentListing,
    ProviderSymbolMapping,
    QuoteObservation,
)


class MarketIngestionService:
    def __init__(self, settings: Settings, provider: MarketDataProvider) -> None:
        self.provider = provider
        self.quality = ProviderDataQualityService(settings)
        self.executor = ProviderExecutor(
            timeout_seconds=settings.market_provider_timeout_seconds,
            retry_count=settings.market_provider_retry_count,
        )
        self.administration = MarketAdministrationService()

    async def synchronise_reference_data(self, session: AsyncSession, *, operation_id: UUID) -> int:
        venues = await self.executor.execute(
            self.provider.name,
            "reference_data",
            self.provider.get_exchange_reference_data,
        )
        for venue in venues:
            self.quality.venue(venue)
        await self.administration.record(
            session,
            operation_id=operation_id,
            event_type="market_data.reference_data_synced",
            provider=self.provider.name,
            command="sync-reference-data",
            metadata={"validated_venues": len(venues)},
        )
        await session.commit()
        return len(venues)

    async def reconcile_listings(
        self, session: AsyncSession, *, query: str, operation_id: UUID
    ) -> int:
        instruments = await self.executor.execute(
            self.provider.name,
            "listing_reconciliation",
            lambda: self.provider.search_instruments(query, 100),
        )
        for instrument in instruments:
            if (
                not instrument.provider_symbol.strip()
                or not instrument.provider_exchange_code.strip()
                or not instrument.source_reference.strip()
            ):
                raise ProviderError(
                    "The provider listing identity is incomplete.",
                    code="provider_response_invalid",
                )
            self.quality.currency(instrument.currency)
        await self.administration.record(
            session,
            operation_id=operation_id,
            event_type="market_data.reference_data_synced",
            provider=self.provider.name,
            command="reconcile-listings",
            metadata={"validated_listings": len(instruments), "query_length": len(query)},
        )
        await session.commit()
        return len(instruments)

    async def upsert_mapping(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        provider_symbol: str,
        provider_venue_code: str,
        operation_id: UUID,
    ) -> ProviderSymbolMapping:
        try:
            return await self._upsert_mapping(
                session,
                listing_id=listing_id,
                provider_symbol=provider_symbol,
                provider_venue_code=provider_venue_code,
                operation_id=operation_id,
            )
        except Exception:
            await session.rollback()
            raise

    async def _upsert_mapping(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        provider_symbol: str,
        provider_venue_code: str,
        operation_id: UUID,
    ) -> ProviderSymbolMapping:
        if not provider_symbol.strip() or not provider_venue_code.strip():
            raise ProviderError(
                "Provider mapping identity is required.", code="provider_response_invalid"
            )
        mapping = await session.scalar(
            select(ProviderSymbolMapping).where(
                ProviderSymbolMapping.provider == self.provider.name,
                ProviderSymbolMapping.listing_id == listing_id,
            )
        )
        created = mapping is None
        if mapping is None:
            if await session.get(InstrumentListing, listing_id) is None:
                raise ProviderError(
                    "The Atlas listing was not found.", code="provider_symbol_not_found"
                )
            mapping = ProviderSymbolMapping(
                provider=self.provider.name,
                listing_id=listing_id,
                provider_symbol=provider_symbol.strip(),
                provider_exchange_code=provider_venue_code.strip(),
            )
            session.add(mapping)
        else:
            mapping.provider_symbol = provider_symbol.strip()
            mapping.provider_exchange_code = provider_venue_code.strip()
        await self.administration.record(
            session,
            operation_id=operation_id,
            event_type=(
                "market_data.provider_mapping_created"
                if created
                else "market_data.provider_mapping_updated"
            ),
            provider=self.provider.name,
            command="upsert-provider-mapping",
            metadata={"listing_ids": [str(listing_id)]},
        )
        await session.commit()
        return mapping

    @staticmethod
    async def context(
        session: AsyncSession, listing_id: UUID, provider: str
    ) -> ProviderListingContext:
        listing = await session.get(InstrumentListing, listing_id)
        if listing is None:
            raise ProviderError(
                "The Atlas listing was not found.", code="provider_symbol_not_found"
            )
        mapping = await session.scalar(
            select(ProviderSymbolMapping).where(
                ProviderSymbolMapping.provider == provider,
                ProviderSymbolMapping.listing_id == listing_id,
            )
        )
        if mapping is None:
            raise ProviderError(
                "The provider mapping was not found.", code="provider_symbol_mismatch"
            )
        return ProviderListingContext(
            listing_id=listing.id,
            provider_symbol=mapping.provider_symbol,
            provider_venue_code=mapping.provider_exchange_code,
            currency=listing.quote_currency,
        )

    async def refresh_quote(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        operation_id: UUID,
    ) -> tuple[QuoteObservation, bool]:
        try:
            return await self._refresh_quote(
                session, listing_id=listing_id, operation_id=operation_id
            )
        except Exception:
            await session.rollback()
            raise

    async def _refresh_quote(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        operation_id: UUID,
    ) -> tuple[QuoteObservation, bool]:
        context = await self.context(session, listing_id, self.provider.name)
        result = self.quality.quote(
            await self.executor.execute(
                self.provider.name,
                "refresh_quote",
                lambda: self.provider.get_latest_quote(context),
            ),
            context,
        )
        existing = await session.scalar(
            select(QuoteObservation).where(
                QuoteObservation.provider == result.provider,
                QuoteObservation.listing_id == result.listing_id,
                QuoteObservation.provider_timestamp == result.provider_timestamp,
            )
        )
        if existing is not None:
            if (
                existing.price != result.price
                or existing.currency != result.currency
                or existing.source_reference != result.source_reference
            ):
                raise ProviderError(
                    "A conflicting quote observation already exists.",
                    code="provider_response_invalid",
                )
            return existing, False
        observation = QuoteObservation(
            listing_id=result.listing_id,
            provider=result.provider,
            provider_timestamp=result.provider_timestamp,
            received_at=result.received_at,
            market_session=result.session,
            price=result.price,
            bid=result.bid,
            ask=result.ask,
            open=result.open,
            high=result.high,
            low=result.low,
            previous_close=result.previous_close,
            volume=result.volume,
            currency=result.currency,
            data_status=result.status,
            delay_seconds=result.delay_seconds,
            source_reference=result.source_reference,
        )
        session.add(observation)
        await self.administration.record(
            session,
            operation_id=operation_id,
            event_type="market_data.quote_refreshed",
            provider=self.provider.name,
            command="refresh-quote",
            metadata={"listing_ids": [str(listing_id)], "inserted": 1},
        )
        await session.commit()
        return observation, True

    async def refresh_candles(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
        operation_id: UUID,
    ) -> tuple[int, int]:
        try:
            return await self._refresh_candles(
                session,
                listing_id=listing_id,
                interval=interval,
                start=start,
                end=end,
                operation_id=operation_id,
            )
        except Exception:
            await session.rollback()
            raise

    async def _refresh_candles(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
        operation_id: UUID,
    ) -> tuple[int, int]:
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ProviderError(
                "A valid timezone-aware candle range is required.",
                code="provider_timestamp_invalid",
            )
        context = await self.context(session, listing_id, self.provider.name)
        batch = self.quality.candles(
            await self.executor.execute(
                self.provider.name,
                "refresh_candles",
                lambda: self.provider.get_historical_candles(context, interval, start, end),
            ),
            context,
        )
        inserted = duplicates = 0
        for candle in batch.candles:
            existing = await session.scalar(
                select(HistoricalCandle).where(
                    HistoricalCandle.provider == batch.provider,
                    HistoricalCandle.listing_id == listing_id,
                    HistoricalCandle.interval == interval,
                    HistoricalCandle.period_start == candle.period_start,
                )
            )
            if existing is not None:
                if (
                    existing.open,
                    existing.high,
                    existing.low,
                    existing.close,
                    existing.currency,
                ) != (
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    batch.currency,
                ):
                    raise ProviderError(
                        "A conflicting candle observation already exists.",
                        code="provider_response_invalid",
                    )
                duplicates += 1
                continue
            session.add(
                HistoricalCandle(
                    listing_id=listing_id,
                    provider=batch.provider,
                    interval=interval,
                    period_start=candle.period_start,
                    period_end=candle.period_end,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    adjusted_close=candle.adjusted_close,
                    volume=candle.volume,
                    currency=batch.currency,
                    data_status=batch.data_status,
                    received_at=batch.received_at,
                )
            )
            inserted += 1
        await self.administration.record(
            session,
            operation_id=operation_id,
            event_type="market_data.candles_refreshed",
            provider=self.provider.name,
            command="refresh-candles",
            metadata={
                "listing_ids": [str(listing_id)],
                "inserted": inserted,
                "duplicates": duplicates,
            },
        )
        await session.commit()
        return inserted, duplicates
