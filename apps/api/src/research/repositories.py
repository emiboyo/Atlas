from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.market.providers import SIMULATED_PROVIDER
from packages.database.atlas_database.models.enums import CandleInterval
from packages.database.atlas_database.models.instruments import HistoricalCandle
from packages.database.atlas_database.models.research import (
    BacktestEquityPoint,
    BacktestEvent,
    BacktestExplanation,
    BacktestResult,
    BacktestRun,
    ResearchAuditEvent,
    ResearchStrategy,
    ResearchStrategyVersion,
)


class ResearchRepository:
    async def strategy(
        self, session: AsyncSession, strategy_id: UUID, *, lock: bool = False
    ) -> ResearchStrategy | None:
        query = select(ResearchStrategy).where(ResearchStrategy.id == strategy_id)
        if lock:
            query = query.with_for_update()
        return cast(ResearchStrategy | None, await session.scalar(query))

    async def strategies(
        self, session: AsyncSession, tenant_id: UUID, offset: int, limit: int
    ) -> list[ResearchStrategy]:
        return list(
            (
                await session.scalars(
                    select(ResearchStrategy)
                    .where(ResearchStrategy.tenant_id == tenant_id)
                    .order_by(ResearchStrategy.created_at, ResearchStrategy.id)
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )

    async def version(
        self, session: AsyncSession, strategy_id: UUID, version_id: UUID
    ) -> ResearchStrategyVersion | None:
        return cast(
            ResearchStrategyVersion | None,
            await session.scalar(
                select(ResearchStrategyVersion).where(
                    ResearchStrategyVersion.id == version_id,
                    ResearchStrategyVersion.strategy_id == strategy_id,
                )
            ),
        )

    async def versions(
        self, session: AsyncSession, strategy_id: UUID
    ) -> list[ResearchStrategyVersion]:
        return list(
            (
                await session.scalars(
                    select(ResearchStrategyVersion)
                    .where(ResearchStrategyVersion.strategy_id == strategy_id)
                    .order_by(ResearchStrategyVersion.version_number)
                )
            ).all()
        )

    async def run(
        self, session: AsyncSession, run_id: UUID, *, lock: bool = False
    ) -> BacktestRun | None:
        query = select(BacktestRun).where(BacktestRun.id == run_id)
        if lock:
            query = query.with_for_update()
        return cast(BacktestRun | None, await session.scalar(query))

    async def runs(
        self, session: AsyncSession, tenant_id: UUID, offset: int, limit: int
    ) -> list[BacktestRun]:
        return list(
            (
                await session.scalars(
                    select(BacktestRun)
                    .where(BacktestRun.tenant_id == tenant_id)
                    .order_by(BacktestRun.requested_at.desc(), BacktestRun.id)
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )

    async def candles(
        self, session: AsyncSession, listing_id: UUID, start: object, end: object
    ) -> list[HistoricalCandle]:
        start_at = datetime.combine(start, datetime.min.time(), tzinfo=UTC)  # type: ignore[arg-type]
        end_at = datetime.combine(end, datetime.max.time(), tzinfo=UTC)  # type: ignore[arg-type]
        return list(
            (
                await session.scalars(
                    select(HistoricalCandle)
                    .where(
                        HistoricalCandle.listing_id == listing_id,
                        HistoricalCandle.provider == SIMULATED_PROVIDER,
                        HistoricalCandle.interval == CandleInterval.ONE_DAY,
                        HistoricalCandle.period_start >= start_at,
                        HistoricalCandle.period_start <= end_at,
                    )
                    .order_by(HistoricalCandle.period_start, HistoricalCandle.id)
                )
            ).all()
        )

    async def events(self, session: AsyncSession, run_id: UUID) -> list[BacktestEvent]:
        return list(
            (
                await session.scalars(
                    select(BacktestEvent)
                    .where(BacktestEvent.run_id == run_id)
                    .order_by(BacktestEvent.sequence)
                )
            ).all()
        )

    async def equity(self, session: AsyncSession, run_id: UUID) -> list[BacktestEquityPoint]:
        return list(
            (
                await session.scalars(
                    select(BacktestEquityPoint)
                    .where(BacktestEquityPoint.run_id == run_id)
                    .order_by(BacktestEquityPoint.sequence)
                )
            ).all()
        )

    async def result(self, session: AsyncSession, run_id: UUID) -> BacktestResult | None:
        return cast(
            BacktestResult | None,
            await session.scalar(select(BacktestResult).where(BacktestResult.run_id == run_id)),
        )

    async def explanations(self, session: AsyncSession, run_id: UUID) -> list[BacktestExplanation]:
        return list(
            (
                await session.scalars(
                    select(BacktestExplanation)
                    .where(BacktestExplanation.run_id == run_id)
                    .order_by(BacktestExplanation.created_at)
                )
            ).all()
        )

    async def explanation(
        self, session: AsyncSession, run_id: UUID, explanation_id: UUID
    ) -> BacktestExplanation | None:
        return cast(
            BacktestExplanation | None,
            await session.scalar(
                select(BacktestExplanation).where(
                    BacktestExplanation.id == explanation_id,
                    BacktestExplanation.run_id == run_id,
                )
            ),
        )

    async def audits(
        self,
        session: AsyncSession,
        strategy_id: UUID,
        run_id: UUID | None = None,
    ) -> list[ResearchAuditEvent]:
        query = select(ResearchAuditEvent).where(ResearchAuditEvent.strategy_id == strategy_id)
        if run_id is not None:
            query = query.where(ResearchAuditEvent.run_id == run_id)
        return list(
            (
                await session.scalars(
                    query.order_by(ResearchAuditEvent.created_at, ResearchAuditEvent.id)
                )
            ).all()
        )
