from datetime import UTC, datetime
from hashlib import sha256
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import get_settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.identity.services import OrganisationService
from apps.api.src.market.repositories import MarketRepository
from apps.api.src.research.engine import (
    ENGINE_VERSION,
    DeterministicBacktestEngine,
    canonical_fingerprint,
)
from apps.api.src.research.metrics import BACKTESTS, EXPLANATIONS, RESEARCH_CONFLICTS
from apps.api.src.research.repositories import ResearchRepository
from apps.api.src.research.schemas import (
    AuditEventResponse,
    BacktestCreate,
    ComparisonResponse,
    DataQualityResponse,
    EffectivePermissions,
    EquityResponse,
    EventResponse,
    ExplanationCreate,
    ExplanationResponse,
    ResultResponse,
    RunResponse,
    StrategyCreate,
    StrategyResponse,
    StrategyUpdate,
    VersionCreate,
    VersionResponse,
)
from packages.database.atlas_database.models.enums import (
    BacktestEventType,
    BacktestRunStatus,
    ExplanationStatus,
    MarketDataStatus,
    ResearchCompleteness,
    ResearchStrategyStatus,
)
from packages.database.atlas_database.models.identity import User
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

SOFTWARE_VERSION = "atlas-milestone-5"


def error(code: str, message: str, status_code: int = 422) -> ApplicationError:
    return ApplicationError(message, code=code, status_code=status_code)


def strategy_response(value: ResearchStrategy) -> StrategyResponse:
    return StrategyResponse.model_validate(value, from_attributes=True)


def version_response(value: ResearchStrategyVersion) -> VersionResponse:
    return VersionResponse.model_validate(value, from_attributes=True)


def run_response(value: BacktestRun) -> RunResponse:
    return RunResponse.model_validate(value, from_attributes=True)


class ResearchAuthorisation:
    def __init__(self) -> None:
        self.organisations = OrganisationService()
        self.central = AuthorisationService()
        self.repo = ResearchRepository()

    async def tenant(
        self, session: AsyncSession, actor: User, tenant_id: UUID, permission: Permission
    ) -> object:
        tenant, membership = await self.organisations.require_membership(
            session, tenant_id, actor.id
        )
        self.central.require_permission(membership.role, permission)
        return tenant

    async def strategy(
        self,
        session: AsyncSession,
        actor: User,
        strategy_id: UUID,
        permission: Permission,
        *,
        lock: bool = False,
    ) -> ResearchStrategy:
        strategy = await self.repo.strategy(session, strategy_id, lock=lock)
        if strategy is None:
            raise error("strategy_not_found", "The research strategy was not found.", 404)
        try:
            _tenant, membership = await self.organisations.require_membership(
                session, strategy.tenant_id, actor.id
            )
        except ApplicationError as exc:
            if exc.status_code == 404:
                raise error(
                    "strategy_not_found", "The research strategy was not found.", 404
                ) from exc
            raise
        self.central.require_permission(membership.role, permission)
        return strategy

    async def run(
        self,
        session: AsyncSession,
        actor: User,
        run_id: UUID,
        permission: Permission,
        *,
        lock: bool = False,
    ) -> tuple[BacktestRun, ResearchStrategy]:
        run = await self.repo.run(session, run_id, lock=lock)
        if run is None:
            raise error("run_not_found", "The historical simulation was not found.", 404)
        strategy = await self.strategy(session, actor, run.strategy_id, permission)
        return run, strategy


class ResearchService:
    def __init__(self) -> None:
        self.repo = ResearchRepository()
        self.auth = ResearchAuthorisation()

    async def create_strategy(
        self, session: AsyncSession, actor: User, data: StrategyCreate, request_id: str | None
    ) -> StrategyResponse:
        await self.auth.tenant(session, actor, data.tenant_id, Permission.STRATEGY_CREATE)
        value = ResearchStrategy(
            tenant_id=data.tenant_id,
            name=data.name,
            description=data.description,
            research_purpose=data.research_purpose,
            status=ResearchStrategyStatus.ACTIVE,
            created_by_user_id=actor.id,
            version=1,
        )
        session.add(value)
        await session.flush()
        self._audit(session, value, actor, "research.strategy.created", request_id, value.id)
        await self._commit(session)
        await session.refresh(value)
        return strategy_response(value)

    async def list_strategies(
        self, session: AsyncSession, actor: User, tenant_id: UUID, offset: int, limit: int
    ) -> list[StrategyResponse]:
        await self.auth.tenant(session, actor, tenant_id, Permission.STRATEGY_READ)
        return [
            strategy_response(item)
            for item in await self.repo.strategies(session, tenant_id, offset, limit)
        ]

    async def get_strategy(
        self, session: AsyncSession, actor: User, strategy_id: UUID
    ) -> StrategyResponse:
        return strategy_response(
            await self.auth.strategy(session, actor, strategy_id, Permission.STRATEGY_READ)
        )

    async def update_strategy(
        self,
        session: AsyncSession,
        actor: User,
        strategy_id: UUID,
        data: StrategyUpdate,
        request_id: str | None,
    ) -> StrategyResponse:
        value = await self.auth.strategy(
            session, actor, strategy_id, Permission.STRATEGY_UPDATE, lock=True
        )
        if value.status == ResearchStrategyStatus.ARCHIVED:
            raise error("strategy_archived", "Archived strategies cannot be changed.", 409)
        if value.version != data.version:
            raise error("concurrency_conflict", "The strategy changed concurrently.", 409)
        for field in ("name", "description", "research_purpose"):
            changed = getattr(data, field)
            if changed is not None:
                setattr(value, field, changed)
        value.version += 1
        self._audit(session, value, actor, "research.strategy.updated", request_id, value.id)
        await self._commit(session)
        await session.refresh(value)
        return strategy_response(value)

    async def archive_strategy(
        self, session: AsyncSession, actor: User, strategy_id: UUID, request_id: str | None
    ) -> StrategyResponse:
        value = await self.auth.strategy(
            session, actor, strategy_id, Permission.STRATEGY_ARCHIVE, lock=True
        )
        value.status = ResearchStrategyStatus.ARCHIVED
        value.archived_at = datetime.now(UTC)
        value.version += 1
        self._audit(session, value, actor, "research.strategy.archived", request_id, value.id)
        await self._commit(session)
        await session.refresh(value)
        return strategy_response(value)

    async def permissions(
        self, session: AsyncSession, actor: User, strategy_id: UUID
    ) -> EffectivePermissions:
        value = await self.auth.strategy(session, actor, strategy_id, Permission.STRATEGY_READ)
        _tenant, membership = await self.auth.organisations.require_membership(
            session, value.tenant_id, actor.id
        )

        def can(permission: Permission) -> bool:
            return self.auth.central.can(membership.role, permission)

        return EffectivePermissions(
            can_read=True,
            can_update=can(Permission.STRATEGY_UPDATE),
            can_archive=can(Permission.STRATEGY_ARCHIVE),
            can_create_version=can(Permission.STRATEGY_VERSION_CREATE),
            can_create_backtest=can(Permission.BACKTEST_CREATE),
            can_compare=can(Permission.BACKTEST_COMPARE),
            can_explain=can(Permission.BACKTEST_EXPLAIN),
            can_read_audit=can(Permission.BACKTEST_AUDIT_READ),
        )

    async def create_version(
        self,
        session: AsyncSession,
        actor: User,
        strategy_id: UUID,
        data: VersionCreate,
        key: str,
        request_id: str | None,
    ) -> VersionResponse:
        strategy = await self.auth.strategy(
            session, actor, strategy_id, Permission.STRATEGY_VERSION_CREATE, lock=True
        )
        if strategy.status == ResearchStrategyStatus.ARCHIVED:
            raise error("strategy_archived", "Archived strategies cannot create versions.", 409)
        listing = await MarketRepository().listing(session, data.listing_id)
        if listing is None or listing.quote_currency != data.base_currency:
            raise error("currency_mismatch", "Listing and strategy currency differ.")
        if data.benchmark_listing_id is not None:
            benchmark = await MarketRepository().listing(session, data.benchmark_listing_id)
            if benchmark is None or benchmark.quote_currency != data.base_currency:
                raise error("currency_mismatch", "Benchmark and strategy currency differ.")
        request_fp = sha256(data.model_dump_json().encode()).hexdigest()
        existing = await session.scalar(
            select(ResearchStrategyVersion).where(
                ResearchStrategyVersion.strategy_id == strategy.id,
                ResearchStrategyVersion.idempotency_key == key,
            )
        )
        if existing:
            if existing.request_fingerprint != request_fp:
                raise error("idempotency_conflict", "The idempotency key was reused.", 409)
            return version_response(existing)
        configuration = data.model_dump(mode="json")
        number = (
            await session.scalar(
                select(
                    func.coalesce(func.max(ResearchStrategyVersion.version_number), 0) + 1
                ).where(ResearchStrategyVersion.strategy_id == strategy.id)
            )
            or 1
        )
        value = ResearchStrategyVersion(
            tenant_id=strategy.tenant_id,
            strategy_id=strategy.id,
            version_number=number,
            version_label=data.version_label,
            configuration=configuration,
            configuration_fingerprint=canonical_fingerprint(configuration),
            request_fingerprint=request_fp,
            idempotency_key=key,
            base_currency=data.base_currency,
            benchmark_listing_id=data.benchmark_listing_id,
            created_by_user_id=actor.id,
        )
        session.add(value)
        await session.flush()
        strategy.current_version_id = value.id
        self._audit(
            session,
            strategy,
            actor,
            "research.strategy_version.created",
            request_id,
            value.id,
            strategy_version_id=value.id,
            operation_id=key,
        )
        await self._commit(session)
        await session.refresh(value)
        return version_response(value)

    async def versions(
        self, session: AsyncSession, actor: User, strategy_id: UUID
    ) -> list[VersionResponse]:
        await self.auth.strategy(session, actor, strategy_id, Permission.STRATEGY_READ)
        return [version_response(item) for item in await self.repo.versions(session, strategy_id)]

    async def create_run(
        self,
        session: AsyncSession,
        actor: User,
        data: BacktestCreate,
        key: str,
        request_id: str | None,
    ) -> RunResponse:
        strategy = await self.auth.strategy(
            session, actor, data.strategy_id, Permission.BACKTEST_CREATE, lock=True
        )
        if strategy.status == ResearchStrategyStatus.ARCHIVED:
            raise error("strategy_archived", "Archived strategies cannot create runs.", 409)
        version = await self.repo.version(session, strategy.id, data.strategy_version_id)
        if version is None:
            raise error("strategy_version_not_found", "The strategy version was not found.", 404)
        request_fp = sha256(data.model_dump_json().encode()).hexdigest()
        existing = await session.scalar(
            select(BacktestRun).where(
                BacktestRun.strategy_id == strategy.id, BacktestRun.idempotency_key == key
            )
        )
        if existing:
            if existing.request_fingerprint != request_fp:
                raise error("idempotency_conflict", "The idempotency key was reused.", 409)
            return run_response(existing)
        configuration = {**data.model_dump(mode="json"), "strategy": version.configuration}
        listing_id = UUID(cast(str, version.configuration["listing_id"]))
        run = BacktestRun(
            tenant_id=strategy.tenant_id,
            strategy_id=strategy.id,
            strategy_version_id=version.id,
            listing_id=listing_id,
            status=BacktestRunStatus.RUNNING,
            idempotency_key=key,
            request_fingerprint=request_fp,
            configuration_fingerprint=canonical_fingerprint(configuration),
            start_date=data.start_date,
            end_date=data.end_date,
            starting_capital=data.starting_capital,
            base_currency=version.base_currency,
            fee_model=data.fee_model,
            fee_value=data.fee_value,
            slippage_model=data.slippage_model,
            slippage_bps=data.slippage_bps,
            execution_policy=data.execution_policy,
            sizing_policy=data.sizing_policy,
            sizing_value=data.sizing_value,
            missing_data_policy=data.missing_data_policy,
            engine_version=ENGINE_VERSION,
            software_version=SOFTWARE_VERSION,
            requested_by_user_id=actor.id,
            requested_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
            is_historical_simulation=True,
        )
        session.add(run)
        await session.flush()
        self._audit(
            session,
            strategy,
            actor,
            "research.backtest.requested",
            request_id,
            run.id,
            strategy_version_id=version.id,
            run_id=run.id,
            operation_id=key,
        )
        self._audit(
            session,
            strategy,
            actor,
            "research.backtest.started",
            request_id,
            run.id,
            strategy_version_id=version.id,
            run_id=run.id,
            operation_id=key,
        )
        candles = await self.repo.candles(session, listing_id, data.start_date, data.end_date)
        unavailable = sum(item.data_status == MarketDataStatus.UNAVAILABLE for item in candles)
        if unavailable:
            await session.rollback()
            raise error(
                "market_data_unavailable",
                "Unavailable historical observations cannot be simulated.",
                422,
            )
        rule = cast(list[dict[str, object]], version.configuration["rules"])[0]
        try:
            simulation = DeterministicBacktestEngine().run(
                candles,
                starting_capital=data.starting_capital,
                rule_id=cast(str, rule["id"]),
                short_window=cast(int, rule["short_window"]),
                long_window=cast(int, rule["long_window"]),
                execution_policy=data.execution_policy,
                fee_model=data.fee_model,
                fee_value=data.fee_value,
                slippage_bps=data.slippage_bps,
                sizing_policy=data.sizing_policy,
                sizing_value=data.sizing_value,
            )
        except ValueError as exc:
            await session.rollback()
            raise error("insufficient_historical_data", str(exc), 422) from exc
        run.data_fingerprint = simulation.data_fingerprint
        for sequence, item in enumerate(simulation.events, 1):
            decision = candles[item.decision_index]
            executed = candles[item.execution_index]
            simulated_at = (
                executed.period_start
                if data.execution_policy == "next_open"
                and item.execution_index > item.decision_index
                else executed.period_end
            )
            session.add(
                BacktestEvent(
                    tenant_id=run.tenant_id,
                    run_id=run.id,
                    sequence=sequence,
                    listing_id=listing_id,
                    event_type=BacktestEventType(item.event_type),
                    decision_at=decision.period_end,
                    simulated_at=simulated_at,
                    price=item.price,
                    quantity=item.quantity,
                    gross_value=item.gross,
                    fee=item.fee,
                    slippage=item.slippage,
                    cash_before=item.cash_before,
                    cash_after=item.cash_after,
                    position_before=item.position_before,
                    position_after=item.position_after,
                    triggered_rule_ids=item.rule_ids,
                    source_observation_ids=[str(decision.id), str(executed.id)],
                )
            )
        for sequence, equity_item in enumerate(simulation.equity, 1):
            session.add(
                BacktestEquityPoint(
                    tenant_id=run.tenant_id,
                    run_id=run.id,
                    sequence=sequence,
                    observed_at=candles[equity_item.index].period_end,
                    cash=equity_item.cash,
                    position_value=equity_item.position_value,
                    total_equity=equity_item.total,
                    running_peak=equity_item.peak,
                    drawdown_amount=equity_item.drawdown_amount,
                    drawdown_percentage=equity_item.drawdown_percentage,
                )
            )
        stale = sum(item.data_status == MarketDataStatus.STALE for item in candles)
        benchmark_return = None
        if version.benchmark_listing_id is not None:
            benchmark_candles = await self.repo.candles(
                session, version.benchmark_listing_id, data.start_date, data.end_date
            )
            if len(benchmark_candles) >= 2:
                first = benchmark_candles[0].adjusted_close or benchmark_candles[0].close
                last = benchmark_candles[-1].adjusted_close or benchmark_candles[-1].close
                if first > 0:
                    benchmark_return = ((last - first) / first) * 100
        result_checksum = canonical_fingerprint(
            {
                "engine_result_checksum": simulation.result_checksum,
                "benchmark_return": benchmark_return,
                "missing_count": 0,
                "stale_count": stale,
                "unavailable_count": 0,
                "excluded_count": 0,
            }
        )
        result = BacktestResult(
            tenant_id=run.tenant_id,
            run_id=run.id,
            starting_value=data.starting_capital,
            ending_value=simulation.ending_value,
            simulated_pnl=simulation.pnl,
            historical_return=simulation.historical_return,
            event_count=len(simulation.events),
            completed_trade_count=len(simulation.events) // 2,
            maximum_drawdown=simulation.maximum_drawdown,
            volatility=simulation.volatility,
            turnover=simulation.turnover,
            benchmark_return=benchmark_return,
            missing_count=0,
            stale_count=stale,
            unavailable_count=0,
            excluded_count=0,
            completeness=(
                ResearchCompleteness.COMPLETE if not stale else ResearchCompleteness.INCOMPLETE
            ),
            result_checksum=result_checksum,
        )
        session.add(result)
        run.status = BacktestRunStatus.COMPLETED
        run.completed_at = datetime.now(UTC)
        self._audit(
            session,
            strategy,
            actor,
            "research.backtest.completed",
            request_id,
            run.id,
            strategy_version_id=version.id,
            run_id=run.id,
            operation_id=key,
        )
        await self._commit(session)
        await session.refresh(run)
        BACKTESTS.labels(outcome="completed").inc()
        return run_response(run)

    async def list_runs(
        self, session: AsyncSession, actor: User, tenant_id: UUID, offset: int, limit: int
    ) -> list[RunResponse]:
        await self.auth.tenant(session, actor, tenant_id, Permission.BACKTEST_READ)
        return [
            run_response(item) for item in await self.repo.runs(session, tenant_id, offset, limit)
        ]

    async def get_run(self, session: AsyncSession, actor: User, run_id: UUID) -> RunResponse:
        run, _strategy = await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        return run_response(run)

    async def events(self, session: AsyncSession, actor: User, run_id: UUID) -> list[EventResponse]:
        await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        return [
            EventResponse.model_validate(x, from_attributes=True)
            for x in await self.repo.events(session, run_id)
        ]

    async def equity(
        self, session: AsyncSession, actor: User, run_id: UUID
    ) -> list[EquityResponse]:
        await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        return [
            EquityResponse.model_validate(x, from_attributes=True)
            for x in await self.repo.equity(session, run_id)
        ]

    async def result(self, session: AsyncSession, actor: User, run_id: UUID) -> ResultResponse:
        await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        value = await self.repo.result(session, run_id)
        if value is None:
            raise error("result_unavailable", "The historical result is unavailable.", 404)
        return ResultResponse.model_validate(value, from_attributes=True)

    async def data_quality(
        self, session: AsyncSession, actor: User, run_id: UUID
    ) -> DataQualityResponse:
        run, _strategy = await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        value = await self.repo.result(session, run_id)
        if value is None:
            raise error("result_unavailable", "The historical result is unavailable.", 404)
        return DataQualityResponse(
            run_id=run.id,
            completeness=value.completeness,
            missing_count=value.missing_count,
            stale_count=value.stale_count,
            unavailable_count=value.unavailable_count,
            excluded_count=value.excluded_count,
            data_fingerprint=run.data_fingerprint,
        )

    async def compare(
        self, session: AsyncSession, actor: User, run_ids: list[UUID]
    ) -> ComparisonResponse:
        if len(run_ids) < 2 or len(run_ids) > 10 or len(set(run_ids)) != len(run_ids):
            raise error("invalid_comparison", "Select between two and ten distinct runs.")
        results: list[ResultResponse] = []
        runs: list[BacktestRun] = []
        for run_id in run_ids:
            run, _strategy = await self.auth.run(
                session, actor, run_id, Permission.BACKTEST_COMPARE
            )
            value = await self.repo.result(session, run_id)
            if value is None:
                raise error("result_unavailable", "Every compared run must be complete.", 409)
            runs.append(run)
            results.append(ResultResponse.model_validate(value, from_attributes=True))
        comparable = len({(x.base_currency, x.start_date, x.end_date) for x in runs}) == 1
        return ComparisonResponse(
            runs=results,
            comparable=comparable,
            comparison_basis=(
                "Same base currency and historical period."
                if comparable
                else "Runs differ in base currency or historical period; values are not normalized."
            ),
        )

    async def explain(
        self,
        session: AsyncSession,
        actor: User,
        run_id: UUID,
        data: ExplanationCreate,
        key: str,
        request_id: str | None,
    ) -> ExplanationResponse:
        run, strategy = await self.auth.run(
            session, actor, run_id, Permission.BACKTEST_EXPLAIN, lock=True
        )
        if not get_settings().research_explanations_enabled:
            EXPLANATIONS.labels(outcome="disabled").inc()
            raise error(
                "explanations_disabled",
                "Historical-result explanations are disabled by configuration.",
                503,
            )
        request_fp = sha256(data.model_dump_json().encode()).hexdigest()
        existing = await session.scalar(
            select(BacktestExplanation).where(
                BacktestExplanation.run_id == run.id,
                BacktestExplanation.idempotency_key == key,
            )
        )
        if existing:
            if existing.request_fingerprint != request_fp:
                raise error("idempotency_conflict", "The idempotency key was reused.", 409)
            return ExplanationResponse.model_validate(existing, from_attributes=True)
        result = await self.repo.result(session, run.id)
        if result is None:
            raise error("result_unavailable", "A completed historical result is required.", 409)
        text = (
            f"This historical simulation ended at {result.ending_value} {run.base_currency} "
            f"with a simulated historical change of {result.historical_return}%. "
            f"It generated {result.event_count} deterministic simulated events. "
            "These historical results do not predict future performance."
        )
        input_fp = canonical_fingerprint(
            {"run": str(run.id), "result": result.result_checksum, "type": data.explanation_type}
        )
        value = BacktestExplanation(
            tenant_id=run.tenant_id,
            run_id=run.id,
            idempotency_key=key,
            request_fingerprint=request_fp,
            explanation_type=data.explanation_type,
            engine_identifier="atlas-local-deterministic-explainer",
            engine_version="1",
            template_version="research-summary/1",
            input_fingerprint=input_fp,
            output_fingerprint=sha256(text.encode()).hexdigest(),
            explanation_text=text,
            limitations=(
                "Historical simulation only; no prediction, recommendation, suitability, "
                "causal claim, live signal, or execution capability."
            ),
            status=ExplanationStatus.COMPLETED,
            generated_by_user_id=actor.id,
            generated_at=datetime.now(UTC),
        )
        session.add(value)
        await session.flush()
        self._audit(
            session,
            strategy,
            actor,
            "research.explanation.generated",
            request_id,
            value.id,
            strategy_version_id=run.strategy_version_id,
            run_id=run.id,
            operation_id=key,
        )
        await self._commit(session)
        await session.refresh(value)
        EXPLANATIONS.labels(outcome="completed").inc()
        return ExplanationResponse.model_validate(value, from_attributes=True)

    async def explanations(
        self, session: AsyncSession, actor: User, run_id: UUID
    ) -> list[ExplanationResponse]:
        await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        return [
            ExplanationResponse.model_validate(item, from_attributes=True)
            for item in await self.repo.explanations(session, run_id)
        ]

    async def explanation(
        self, session: AsyncSession, actor: User, run_id: UUID, explanation_id: UUID
    ) -> ExplanationResponse:
        await self.auth.run(session, actor, run_id, Permission.BACKTEST_READ)
        value = await self.repo.explanation(session, run_id, explanation_id)
        if value is None:
            raise error("explanation_not_found", "The explanation was not found.", 404)
        return ExplanationResponse.model_validate(value, from_attributes=True)

    async def audits(
        self,
        session: AsyncSession,
        actor: User,
        strategy_id: UUID,
        run_id: UUID | None,
    ) -> list[AuditEventResponse]:
        await self.auth.strategy(session, actor, strategy_id, Permission.BACKTEST_AUDIT_READ)
        return [
            AuditEventResponse.model_validate(item, from_attributes=True)
            for item in await self.repo.audits(session, strategy_id, run_id)
        ]

    @staticmethod
    def _audit(
        session: AsyncSession,
        strategy: ResearchStrategy,
        actor: User,
        event_type: str,
        request_id: str | None,
        target_id: UUID,
        *,
        strategy_version_id: UUID | None = None,
        run_id: UUID | None = None,
        operation_id: str | None = None,
    ) -> None:
        session.add(
            ResearchAuditEvent(
                tenant_id=strategy.tenant_id,
                strategy_id=strategy.id,
                strategy_version_id=strategy_version_id,
                run_id=run_id,
                event_type=event_type,
                request_id=request_id,
                operation_id=operation_id,
                actor_user_id=actor.id,
                target_id=target_id,
                event_metadata={},
            )
        )

    @staticmethod
    async def _commit(session: AsyncSession) -> None:
        try:
            await session.commit()
        except (IntegrityError, DBAPIError) as exc:
            await session.rollback()
            RESEARCH_CONFLICTS.labels(code="concurrency_conflict").inc()
            raise error("concurrency_conflict", "The research operation conflicted.", 409) from exc
