import argparse
import asyncio
import json
from datetime import datetime
from uuid import UUID, uuid4

from apps.api.src.core.config import get_settings
from apps.api.src.market.administration import MarketAdministrationService
from apps.api.src.market.ingestion import MarketIngestionService
from apps.api.src.market.providers import SIMULATED_PROVIDER, DeterministicFixtureProvider
from packages.database.atlas_database.models.enums import CandleInterval
from packages.database.atlas_database.session import create_database_engine


async def run(
    command: str,
    operation_id: UUID,
    *,
    listing_id: UUID | None,
    provider_symbol: str | None,
    provider_venue_code: str | None,
    start: datetime | None,
    end: datetime | None,
) -> None:
    settings = get_settings()
    if settings.environment == "production":
        raise RuntimeError("Development market-data commands are disabled in production")
    engine = create_database_engine(settings)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda _connection: None)
        from sqlalchemy.ext.asyncio import async_sessionmaker

        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            ingestion = MarketIngestionService(settings, DeterministicFixtureProvider())
            if command == "seed-development-data":
                print(
                    json.dumps(
                        await MarketAdministrationService().seed(
                            session,
                            operation_id=operation_id,
                            provider=SIMULATED_PROVIDER,
                        ),
                        sort_keys=True,
                    )
                )
            elif command == "sync-reference-data":
                print(
                    json.dumps(
                        {
                            "venues_validated": await ingestion.synchronise_reference_data(
                                session, operation_id=operation_id
                            )
                        }
                    )
                )
            elif command == "reconcile-listings":
                print(
                    json.dumps(
                        {
                            "listings_validated": await ingestion.reconcile_listings(
                                session, query=provider_symbol or "NOVA", operation_id=operation_id
                            )
                        }
                    )
                )
            elif command == "refresh-quote" and listing_id is not None:
                _observation, quote_inserted = await ingestion.refresh_quote(
                    session, listing_id=listing_id, operation_id=operation_id
                )
                print(json.dumps({"inserted": quote_inserted}))
            elif (
                command == "refresh-candles"
                and listing_id is not None
                and start is not None
                and end is not None
            ):
                candle_inserted, duplicates = await ingestion.refresh_candles(
                    session,
                    listing_id=listing_id,
                    interval=CandleInterval.ONE_DAY,
                    start=start,
                    end=end,
                    operation_id=operation_id,
                )
                print(json.dumps({"inserted": candle_inserted, "duplicates": duplicates}))
            elif (
                command == "upsert-provider-mapping"
                and listing_id is not None
                and provider_symbol is not None
                and provider_venue_code is not None
            ):
                mapping = await ingestion.upsert_mapping(
                    session,
                    listing_id=listing_id,
                    provider_symbol=provider_symbol,
                    provider_venue_code=provider_venue_code,
                    operation_id=operation_id,
                )
                print(json.dumps({"mapping_id": str(mapping.id)}))
            else:
                raise ValueError("The selected command requires additional arguments")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlas private market-data administration")
    parser.add_argument(
        "command",
        choices=[
            "seed-development-data",
            "sync-reference-data",
            "reconcile-listings",
            "refresh-quote",
            "refresh-candles",
            "upsert-provider-mapping",
        ],
    )
    parser.add_argument("--operation-id", type=UUID, default=uuid4())
    parser.add_argument("--listing-id", type=UUID)
    parser.add_argument("--provider-symbol")
    parser.add_argument("--provider-venue-code")
    parser.add_argument("--start", type=datetime.fromisoformat)
    parser.add_argument("--end", type=datetime.fromisoformat)
    arguments = parser.parse_args()
    asyncio.run(
        run(
            arguments.command,
            arguments.operation_id,
            listing_id=arguments.listing_id,
            provider_symbol=arguments.provider_symbol,
            provider_venue_code=arguments.provider_venue_code,
            start=arguments.start,
            end=arguments.end,
        )
    )


if __name__ == "__main__":
    main()
