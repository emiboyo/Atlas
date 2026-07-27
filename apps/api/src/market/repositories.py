from collections.abc import Sequence
from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.database.atlas_database.models.enums import WatchlistStatus
from packages.database.atlas_database.models.instruments import (
    Exchange,
    Instrument,
    InstrumentListing,
    Watchlist,
    WatchlistItem,
)


class MarketRepository:
    async def exchanges(
        self, session: AsyncSession, *, offset: int, limit: int
    ) -> Sequence[Exchange]:
        return (
            await session.scalars(
                select(Exchange).order_by(Exchange.mic).offset(offset).limit(limit)
            )
        ).all()

    async def search(
        self, session: AsyncSession, query: str, *, offset: int, limit: int
    ) -> Sequence[tuple[Instrument, InstrumentListing, Exchange]]:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        exact = query.upper()
        result = await session.execute(
            select(Instrument, InstrumentListing, Exchange)
            .join(InstrumentListing, InstrumentListing.instrument_id == Instrument.id)
            .join(Exchange, Exchange.id == InstrumentListing.exchange_id)
            .where(
                or_(
                    func.upper(InstrumentListing.ticker) == exact,
                    InstrumentListing.ticker.ilike(pattern, escape="\\"),
                    Instrument.name.ilike(pattern, escape="\\"),
                    Instrument.short_name.ilike(pattern, escape="\\"),
                    Exchange.name.ilike(pattern, escape="\\"),
                    func.upper(Exchange.mic) == exact,
                    func.upper(Instrument.isin) == exact,
                )
            )
            .order_by(
                (func.upper(InstrumentListing.ticker) == exact).desc(),
                InstrumentListing.ticker,
                Exchange.mic,
            )
            .offset(offset)
            .limit(limit)
        )
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def search_count(self, session: AsyncSession, query: str) -> int:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        exact = query.upper()
        return (
            await session.scalar(
                select(func.count())
                .select_from(InstrumentListing)
                .join(Instrument)
                .join(Exchange)
                .where(
                    or_(
                        func.upper(InstrumentListing.ticker) == exact,
                        InstrumentListing.ticker.ilike(pattern, escape="\\"),
                        Instrument.name.ilike(pattern, escape="\\"),
                        Instrument.short_name.ilike(pattern, escape="\\"),
                        Exchange.name.ilike(pattern, escape="\\"),
                        func.upper(Exchange.mic) == exact,
                        func.upper(Instrument.isin) == exact,
                    )
                )
            )
            or 0
        )

    async def instrument(self, session: AsyncSession, instrument_id: UUID) -> Instrument | None:
        return cast(
            Instrument | None,
            await session.scalar(
                select(Instrument)
                .where(Instrument.id == instrument_id)
                .options(selectinload(Instrument.listings).selectinload(InstrumentListing.exchange))
            ),
        )

    async def listing(self, session: AsyncSession, listing_id: UUID) -> InstrumentListing | None:
        return cast(
            InstrumentListing | None,
            await session.scalar(
                select(InstrumentListing)
                .where(InstrumentListing.id == listing_id)
                .options(
                    selectinload(InstrumentListing.instrument),
                    selectinload(InstrumentListing.exchange),
                )
            ),
        )


class WatchlistRepository:
    async def list(
        self, session: AsyncSession, tenant_id: UUID, *, offset: int, limit: int
    ) -> Sequence[Watchlist]:
        return (
            await session.scalars(
                select(Watchlist)
                .where(Watchlist.tenant_id == tenant_id)
                .options(selectinload(Watchlist.items))
                .order_by(Watchlist.created_at, Watchlist.id)
                .offset(offset)
                .limit(limit)
            )
        ).all()

    async def count(self, session: AsyncSession, tenant_id: UUID) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(Watchlist)
                .where(
                    Watchlist.tenant_id == tenant_id,
                    Watchlist.status == WatchlistStatus.ACTIVE,
                )
            )
            or 0
        )

    async def by_id(
        self, session: AsyncSession, watchlist_id: UUID, *, with_items: bool = True
    ) -> Watchlist | None:
        statement = select(Watchlist).where(Watchlist.id == watchlist_id)
        if with_items:
            statement = statement.options(selectinload(Watchlist.items))
        return cast(Watchlist | None, await session.scalar(statement))

    async def item(
        self, session: AsyncSession, watchlist_id: UUID, item_id: UUID
    ) -> WatchlistItem | None:
        return cast(
            WatchlistItem | None,
            await session.scalar(
                select(WatchlistItem).where(
                    WatchlistItem.id == item_id,
                    WatchlistItem.watchlist_id == watchlist_id,
                )
            ),
        )

    async def item_count(self, session: AsyncSession, watchlist_id: UUID) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(WatchlistItem)
                .where(WatchlistItem.watchlist_id == watchlist_id)
            )
            or 0
        )
