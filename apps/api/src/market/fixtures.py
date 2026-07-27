from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.market.metrics import INGESTION_RESULTS
from apps.api.src.market.providers import SIMULATED_PROVIDER
from packages.database.atlas_database.models.enums import (
    AssetClass,
    CandleInterval,
    InstrumentStatus,
    ListingStatus,
    MarketDataStatus,
    MarketSession,
    ProviderMappingStatus,
    VenueStatus,
)
from packages.database.atlas_database.models.instruments import (
    Exchange,
    HistoricalCandle,
    Instrument,
    InstrumentListing,
    ProviderSymbolMapping,
    QuoteObservation,
)


def fixture_id(kind: str, value: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://development.atlas.invalid/{kind}/{value}")


EXCHANGES = (
    ("XDEV", "Atlas Development Exchange", "ADX", "GB", "Europe/London", "GBP"),
    ("XDEM", "Atlas Demonstration Market", "ADM", "US", "America/New_York", "USD"),
    ("XCRY", "Atlas Simulated Digital Venue", "ASDV", "ZZ", "UTC", "USD"),
)

INSTRUMENTS = (
    ("NOVA", "Nova Systems Development Equity", AssetClass.EQUITY, "GBP", "XDEV"),
    ("ORBT", "Orbit Works Development Equity", AssetClass.EQUITY, "USD", "XDEM"),
    ("NOVA", "Nova Research Development Equity", AssetClass.EQUITY, "USD", "XDEM"),
    ("WIDE", "Atlas Broad Development ETF", AssetClass.EXCHANGE_TRADED_FUND, "GBP", "XDEV"),
    ("BOND", "Atlas Bond Development ETF", AssetClass.EXCHANGE_TRADED_FUND, "USD", "XDEM"),
    ("AIDX", "Atlas Development Index", AssetClass.INDEX, "GBP", "XDEV"),
    ("GBXU", "Simulated GBP USD Pair", AssetClass.FOREIGN_EXCHANGE, "USD", "XDEM"),
    ("ATCX", "Simulated Atlas Crypto Pair", AssetClass.CRYPTOCURRENCY, "USD", "XCRY"),
)


async def seed_development_data(session: AsyncSession) -> dict[str, int]:
    exchange_count = instrument_count = listing_count = 0
    exchanges: dict[str, Exchange] = {}
    for mic, name, acronym, country, timezone, currency in EXCHANGES:
        exchange_id = fixture_id("exchange", mic)
        exchange = await session.get(Exchange, exchange_id)
        if exchange is None:
            exchange = Exchange(
                id=exchange_id,
                mic=mic,
                name=name,
                acronym=acronym,
                country_code=country,
                timezone=timezone,
                default_currency=currency,
                market_type="simulated",
                status=VenueStatus.ACTIVE,
            )
            session.add(exchange)
            exchange_count += 1
        exchanges[mic] = exchange
    await session.flush()

    for sequence, (symbol, name, asset_class, currency, mic) in enumerate(INSTRUMENTS):
        stable_key = f"{mic}-{symbol}-{sequence}"
        instrument_id = fixture_id("instrument", stable_key)
        listing_id = fixture_id("listing", stable_key)
        instrument = await session.get(Instrument, instrument_id)
        if instrument is None:
            instrument = Instrument(
                id=instrument_id,
                canonical_symbol=None,
                name=name,
                short_name=name.replace(" Development", ""),
                description="Fictional catalogue record for deterministic private development.",
                asset_class=asset_class,
                status=InstrumentStatus.ACTIVE,
                base_currency=currency,
                country_code=None,
                metadata_version=1,
            )
            session.add(instrument)
            instrument_count += 1
        listing = await session.get(InstrumentListing, listing_id)
        if listing is None:
            listing = InstrumentListing(
                id=listing_id,
                instrument_id=instrument_id,
                exchange_id=exchanges[mic].id,
                venue_mic=mic,
                ticker=symbol,
                provider_normalised_symbol=f"{symbol}.{mic}",
                quote_currency=currency,
                listing_status=ListingStatus.ACTIVE,
                is_primary=True,
                price_increment=Decimal("0.0001"),
                active=True,
            )
            session.add(listing)
            await session.flush()
            session.add(
                ProviderSymbolMapping(
                    id=fixture_id("mapping", stable_key),
                    provider=SIMULATED_PROVIDER,
                    listing_id=listing_id,
                    provider_symbol=f"{symbol}.{mic}",
                    provider_exchange_code=mic,
                    provider_instrument_type=asset_class.value,
                    status=ProviderMappingStatus.ACTIVE,
                    last_verified_at=datetime(2026, 1, 15, tzinfo=UTC),
                )
            )
            price = Decimal((listing_id.int % 900) + 100) + Decimal("0.125")
            session.add(
                QuoteObservation(
                    id=fixture_id("quote", stable_key),
                    listing_id=listing_id,
                    provider=SIMULATED_PROVIDER,
                    provider_timestamp=datetime(2026, 1, 15, 16, tzinfo=UTC),
                    received_at=datetime(2026, 1, 15, 16, 0, 5, tzinfo=UTC),
                    market_session=MarketSession.CLOSED,
                    price=price,
                    open=price - Decimal("0.5"),
                    high=price + Decimal("1"),
                    low=price - Decimal("1"),
                    previous_close=price - Decimal("0.25"),
                    volume=100_000 + sequence,
                    currency=currency,
                    data_status=MarketDataStatus.SIMULATED,
                    source_reference=f"fixture:{stable_key}",
                )
            )
            for day in range(5):
                period_start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day)
                value = price + Decimal(day)
                session.add(
                    HistoricalCandle(
                        id=fixture_id("candle", f"{stable_key}-{day}"),
                        listing_id=listing_id,
                        provider=SIMULATED_PROVIDER,
                        interval=CandleInterval.ONE_DAY,
                        period_start=period_start,
                        period_end=period_start + timedelta(days=1),
                        open=value,
                        high=value + Decimal("2"),
                        low=value - Decimal("1"),
                        close=value + Decimal("1"),
                        adjusted_close=value + Decimal("1"),
                        volume=100_000 + day,
                        currency=currency,
                        data_status=MarketDataStatus.SIMULATED,
                        received_at=datetime(2026, 1, 15, tzinfo=UTC),
                    )
                )
            listing_count += 1
    await session.commit()
    INGESTION_RESULTS.labels(operation="seed", outcome="success").inc()
    return {
        "exchanges_created": exchange_count,
        "instruments_created": instrument_count,
        "listings_created": listing_count,
    }


async def fixture_listing_id(session: AsyncSession, symbol: str, mic: str) -> UUID | None:
    return cast(
        UUID | None,
        await session.scalar(
            select(InstrumentListing.id)
            .join(Exchange)
            .where(InstrumentListing.ticker == symbol, Exchange.mic == mic)
        ),
    )
