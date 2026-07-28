from collections.abc import Sequence
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.database.atlas_database.models.enums import CandleInterval
from packages.database.atlas_database.models.instruments import (
    Exchange,
    HistoricalCandle,
    Instrument,
    InstrumentListing,
    QuoteObservation,
)
from packages.database.atlas_database.models.ledger import LedgerEntry
from packages.database.atlas_database.models.portfolios import (
    Portfolio,
    PortfolioAccount,
    PortfolioAuditEvent,
    PortfolioPosition,
    PortfolioTransaction,
    PortfolioValuationLine,
    PortfolioValuationSnapshot,
)


class PortfolioRepository:
    async def list(
        self, session: AsyncSession, tenant_id: UUID, *, offset: int, limit: int
    ) -> Sequence[Portfolio]:
        return (
            await session.scalars(
                select(Portfolio)
                .where(Portfolio.tenant_id == tenant_id)
                .order_by(Portfolio.created_at, Portfolio.id)
                .offset(offset)
                .limit(limit)
            )
        ).all()

    async def by_id(
        self,
        session: AsyncSession,
        portfolio_id: UUID,
        *,
        for_update: bool = False,
    ) -> Portfolio | None:
        statement = select(Portfolio).where(Portfolio.id == portfolio_id)
        if for_update:
            statement = statement.with_for_update()
        return cast(Portfolio | None, await session.scalar(statement))


class PortfolioAccountRepository:
    async def list(self, session: AsyncSession, portfolio_id: UUID) -> Sequence[PortfolioAccount]:
        return (
            await session.scalars(
                select(PortfolioAccount)
                .where(PortfolioAccount.portfolio_id == portfolio_id)
                .order_by(PortfolioAccount.account_role)
            )
        ).all()

    async def cash_balance(
        self, session: AsyncSession, portfolio_id: UUID, currency: str
    ) -> object:
        return (
            await session.scalar(
                select(func.coalesce(func.sum(LedgerEntry.amount), 0))
                .join(
                    PortfolioAccount,
                    PortfolioAccount.ledger_account_id == LedgerEntry.ledger_account_id,
                )
                .where(
                    PortfolioAccount.portfolio_id == portfolio_id,
                    PortfolioAccount.account_role == "virtual_cash",
                    PortfolioAccount.currency == currency,
                )
            )
            or 0
        )

    async def cash_balances(
        self, session: AsyncSession, portfolio_id: UUID
    ) -> Sequence[tuple[str, object]]:
        rows = await session.execute(
            select(
                PortfolioAccount.currency,
                func.coalesce(func.sum(LedgerEntry.amount), 0),
            )
            .join(
                LedgerEntry,
                LedgerEntry.ledger_account_id == PortfolioAccount.ledger_account_id,
                isouter=True,
            )
            .where(
                PortfolioAccount.portfolio_id == portfolio_id,
                PortfolioAccount.account_role == "virtual_cash",
            )
            .group_by(PortfolioAccount.currency)
            .order_by(PortfolioAccount.currency)
        )
        return [(row[0], row[1]) for row in rows.all()]


class PortfolioTransactionRepository:
    async def by_id(
        self, session: AsyncSession, portfolio_id: UUID, transaction_id: UUID
    ) -> PortfolioTransaction | None:
        return cast(
            PortfolioTransaction | None,
            await session.scalar(
                select(PortfolioTransaction).where(
                    PortfolioTransaction.id == transaction_id,
                    PortfolioTransaction.portfolio_id == portfolio_id,
                )
            ),
        )

    async def by_idempotency_key(
        self, session: AsyncSession, portfolio_id: UUID, key: str
    ) -> PortfolioTransaction | None:
        return cast(
            PortfolioTransaction | None,
            await session.scalar(
                select(PortfolioTransaction).where(
                    PortfolioTransaction.portfolio_id == portfolio_id,
                    PortfolioTransaction.idempotency_key == key,
                )
            ),
        )

    async def list(
        self,
        session: AsyncSession,
        portfolio_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> Sequence[PortfolioTransaction]:
        return (
            await session.scalars(
                select(PortfolioTransaction)
                .where(PortfolioTransaction.portfolio_id == portfolio_id)
                .order_by(
                    PortfolioTransaction.sequence.desc(),
                    PortfolioTransaction.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
        ).all()

    async def next_sequence(self, session: AsyncSession, portfolio_id: UUID) -> int:
        return (
            await session.scalar(
                select(func.coalesce(func.max(PortfolioTransaction.sequence), 0) + 1).where(
                    PortfolioTransaction.portfolio_id == portfolio_id
                )
            )
            or 1
        )


class PortfolioPositionRepository:
    async def by_listing(
        self,
        session: AsyncSession,
        portfolio_id: UUID,
        listing_id: UUID,
        *,
        for_update: bool = False,
    ) -> PortfolioPosition | None:
        statement = select(PortfolioPosition).where(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.listing_id == listing_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return cast(PortfolioPosition | None, await session.scalar(statement))

    async def list(
        self, session: AsyncSession, portfolio_id: UUID
    ) -> Sequence[tuple[PortfolioPosition, InstrumentListing, Instrument, Exchange]]:
        rows = await session.execute(
            select(PortfolioPosition, InstrumentListing, Instrument, Exchange)
            .join(
                InstrumentListing,
                InstrumentListing.id == PortfolioPosition.listing_id,
            )
            .join(Instrument, Instrument.id == InstrumentListing.instrument_id)
            .join(Exchange, Exchange.id == InstrumentListing.exchange_id)
            .where(PortfolioPosition.portfolio_id == portfolio_id)
            .order_by(InstrumentListing.ticker, PortfolioPosition.id)
        )
        return [(row[0], row[1], row[2], row[3]) for row in rows.all()]

    async def latest_quote(
        self, session: AsyncSession, listing_id: UUID
    ) -> QuoteObservation | None:
        return cast(
            QuoteObservation | None,
            await session.scalar(
                select(QuoteObservation)
                .where(QuoteObservation.listing_id == listing_id)
                .order_by(
                    QuoteObservation.provider_timestamp.desc(),
                    QuoteObservation.received_at.desc(),
                    QuoteObservation.id.desc(),
                )
                .limit(1)
            ),
        )


class PortfolioValuationRepository:
    async def by_idempotency_key(
        self, session: AsyncSession, portfolio_id: UUID, key: str
    ) -> PortfolioValuationSnapshot | None:
        return cast(
            PortfolioValuationSnapshot | None,
            await session.scalar(
                select(PortfolioValuationSnapshot).where(
                    PortfolioValuationSnapshot.portfolio_id == portfolio_id,
                    PortfolioValuationSnapshot.idempotency_key == key,
                )
            ),
        )

    async def by_id(
        self, session: AsyncSession, portfolio_id: UUID, snapshot_id: UUID
    ) -> PortfolioValuationSnapshot | None:
        return cast(
            PortfolioValuationSnapshot | None,
            await session.scalar(
                select(PortfolioValuationSnapshot).where(
                    PortfolioValuationSnapshot.id == snapshot_id,
                    PortfolioValuationSnapshot.portfolio_id == portfolio_id,
                )
            ),
        )

    async def list(
        self,
        session: AsyncSession,
        portfolio_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> Sequence[PortfolioValuationSnapshot]:
        return (
            await session.scalars(
                select(PortfolioValuationSnapshot)
                .where(PortfolioValuationSnapshot.portfolio_id == portfolio_id)
                .order_by(
                    PortfolioValuationSnapshot.as_of.desc(),
                    PortfolioValuationSnapshot.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
        ).all()

    async def history(
        self,
        session: AsyncSession,
        portfolio_id: UUID,
        *,
        start: object | None = None,
        end: object | None = None,
        limit: int = 366,
    ) -> Sequence[PortfolioValuationSnapshot]:
        statement = select(PortfolioValuationSnapshot).where(
            PortfolioValuationSnapshot.portfolio_id == portfolio_id,
            PortfolioValuationSnapshot.base_currency_total.is_not(None),
        )
        if start is not None:
            statement = statement.where(PortfolioValuationSnapshot.as_of >= start)
        if end is not None:
            statement = statement.where(PortfolioValuationSnapshot.as_of <= end)
        return (
            await session.scalars(
                statement.order_by(
                    PortfolioValuationSnapshot.as_of,
                    PortfolioValuationSnapshot.id,
                ).limit(limit)
            )
        ).all()

    async def lines(
        self, session: AsyncSession, snapshot_id: UUID
    ) -> Sequence[PortfolioValuationLine]:
        return (
            await session.scalars(
                select(PortfolioValuationLine)
                .where(PortfolioValuationLine.snapshot_id == snapshot_id)
                .order_by(PortfolioValuationLine.listing_id)
            )
        ).all()

    async def benchmark_candles(
        self,
        session: AsyncSession,
        listing_id: UUID,
        start: datetime,
        end: datetime,
    ) -> Sequence[HistoricalCandle]:
        return (
            await session.scalars(
                select(HistoricalCandle)
                .where(
                    HistoricalCandle.listing_id == listing_id,
                    HistoricalCandle.interval == CandleInterval.ONE_DAY,
                    HistoricalCandle.period_start >= start,
                    HistoricalCandle.period_start <= end,
                )
                .order_by(
                    HistoricalCandle.period_start,
                    HistoricalCandle.provider,
                    HistoricalCandle.id,
                )
            )
        ).all()


class PortfolioAuditRepository:
    async def list(
        self,
        session: AsyncSession,
        portfolio_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> Sequence[PortfolioAuditEvent]:
        return (
            await session.scalars(
                select(PortfolioAuditEvent)
                .where(PortfolioAuditEvent.portfolio_id == portfolio_id)
                .order_by(
                    PortfolioAuditEvent.created_at.desc(),
                    PortfolioAuditEvent.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
        ).all()
