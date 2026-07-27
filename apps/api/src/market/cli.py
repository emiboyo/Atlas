import argparse
import asyncio
import json

from apps.api.src.core.config import get_settings
from apps.api.src.market.fixtures import seed_development_data
from packages.database.atlas_database.session import create_database_engine


async def run(command: str) -> None:
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
            if command == "seed-development-data":
                print(json.dumps(await seed_development_data(session), sort_keys=True))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlas private market-data administration")
    parser.add_argument("command", choices=["seed-development-data"])
    arguments = parser.parse_args()
    asyncio.run(run(arguments.command))


if __name__ == "__main__":
    main()
