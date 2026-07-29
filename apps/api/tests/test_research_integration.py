import asyncio
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.src.core.errors import ApplicationError
from apps.api.src.research.engine import (
    DeterministicBacktestEngine,
    canonical_fingerprint,
)
from apps.api.src.research.schemas import (
    BacktestCreate,
    ExplanationCreate,
    ResearchRule,
    StrategyCreate,
    VersionCreate,
)
from apps.api.src.research.services import ResearchService
from apps.api.tests.test_portfolio_integration import setup_context
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MarketDataStatus,
)
from packages.database.atlas_database.models.instruments import HistoricalCandle
from packages.database.atlas_database.models.research import (
    BacktestEvent,
    BacktestExplanation,
    BacktestResult,
    BacktestRun,
    ResearchAuditEvent,
    ResearchStrategy,
    ResearchStrategyVersion,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("ATLAS_TEST_DATABASE_URL"),
    reason="ATLAS_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


async def seed_research_candles(session: AsyncSession, listing_id: object) -> None:
    existing = await session.scalar(
        select(func.count())
        .select_from(HistoricalCandle)
        .where(
            HistoricalCandle.listing_id == listing_id,
            HistoricalCandle.provider == "atlas_simulated",
            HistoricalCandle.period_start >= datetime(2026, 2, 1, tzinfo=UTC),
            HistoricalCandle.period_start < datetime(2026, 2, 10, tzinfo=UTC),
        )
    )
    if existing:
        return
    values = ("10", "9", "8", "9", "10", "8", "7", "9", "11")
    for index, value in enumerate(values):
        start = datetime(2026, 2, 1, tzinfo=UTC) + timedelta(days=index)
        session.add(
            HistoricalCandle(
                id=uuid4(),
                listing_id=listing_id,
                provider="atlas_simulated",
                interval=CandleInterval.ONE_DAY,
                period_start=start,
                period_end=start + timedelta(days=1),
                open=Decimal(value),
                high=Decimal(value) + 1,
                low=Decimal(value) - 1,
                close=Decimal(value),
                adjusted_close=Decimal(value),
                volume=100,
                currency="GBP",
                data_status=MarketDataStatus.SIMULATED,
                received_at=datetime(2026, 3, 1, tzinfo=UTC),
            )
        )
    await session.commit()


async def test_complete_research_workflow_is_reproducible_and_isolated() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, viewer, outsider, tenant, _other, listing_id = await setup_context(factory)
    async with factory() as session:
        await seed_research_candles(session, listing_id)
    async with factory() as session:
        strategy = await ResearchService().create_strategy(
            session,
            owner,
            StrategyCreate(
                tenant_id=tenant.id,
                name=f"Historical research {uuid4().hex[:8]}",
                research_purpose="Evaluate a deterministic historical hypothesis",
            ),
            "research-create",
        )
    version_data = VersionCreate(
        version_label="SMA 2/3",
        base_currency="GBP",
        listing_id=listing_id,
        benchmark_listing_id=listing_id,
        rules=[
            ResearchRule(
                id="sma-cross",
                rule_type="sma_crossover",
                short_window=2,
                long_window=3,
            )
        ],
    )
    async with factory() as session:
        version = await ResearchService().create_version(
            session, owner, strategy.id, version_data, f"version-{uuid4()}", "version"
        )
    run_data = BacktestCreate(
        strategy_id=strategy.id,
        strategy_version_id=version.id,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 10),
        starting_capital=Decimal("1000"),
        fee_model="fixed_amount_per_event",
        fee_value=Decimal("1"),
        slippage_model="fixed_basis_points",
        slippage_bps=Decimal("10"),
        execution_policy="next_open",
        sizing_policy="fixed_percentage_of_available_simulated_cash",
        sizing_value=Decimal("50"),
        missing_data_policy="fail_run",
    )
    run_key = f"run-{uuid4()}"
    async with factory() as session:
        run = await ResearchService().create_run(session, owner, run_data, run_key, "run")
    async with factory() as session:
        replay = await ResearchService().create_run(session, owner, run_data, run_key, "run-replay")
        assert replay.id == run.id
        events = await ResearchService().events(session, owner, run.id)
        result = await ResearchService().result(session, owner, run.id)
        assert events
        assert all(item.simulated_at >= item.decision_at for item in events)
        assert result.result_checksum
        assert result.starting_value == Decimal("1000")
        explanation = await ResearchService().explain(
            session,
            owner,
            run.id,
            ExplanationCreate(explanation_type="run_summary"),
            f"explain-{uuid4()}",
            "explain",
        )
        assert "do not predict future performance" in explanation.explanation_text
        assert explanation.engine_identifier == "atlas-local-deterministic-explainer"
    async with factory() as session:
        with pytest.raises(ApplicationError) as viewer_denied:
            await ResearchService().create_run(
                session, viewer, run_data, f"viewer-{uuid4()}", "viewer"
            )
        assert viewer_denied.value.status_code == 403
        with pytest.raises(ApplicationError) as concealed:
            await ResearchService().get_strategy(session, outsider, strategy.id)
        assert concealed.value.code == "strategy_not_found"
    async with factory() as session:
        counts = {
            "runs": await session.scalar(
                select(func.count()).select_from(BacktestRun).where(BacktestRun.id == run.id)
            ),
            "results": await session.scalar(
                select(func.count())
                .select_from(BacktestResult)
                .where(BacktestResult.run_id == run.id)
            ),
            "events": await session.scalar(
                select(func.count())
                .select_from(BacktestEvent)
                .where(BacktestEvent.run_id == run.id)
            ),
            "audits": await session.scalar(
                select(func.count())
                .select_from(ResearchAuditEvent)
                .where(ResearchAuditEvent.strategy_id == strategy.id)
            ),
        }
        assert counts["runs"] == 1
        assert counts["results"] == 1
        assert counts["events"] == len(events)
        assert counts["audits"] >= 4
        with pytest.raises(DBAPIError):
            await session.execute(
                text(
                    "UPDATE backtest_results SET event_count = event_count + 1 "
                    "WHERE run_id = :run_id"
                ),
                {"run_id": run.id},
            )
            await session.commit()
        await session.rollback()
    await engine.dispose()


async def test_concurrent_version_and_run_idempotency_create_one_effect() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _viewer, _outsider, tenant, _other, listing_id = await setup_context(factory)
    async with factory() as session:
        await seed_research_candles(session, listing_id)
        strategy = await ResearchService().create_strategy(
            session,
            owner,
            StrategyCreate(
                tenant_id=tenant.id,
                name=f"Concurrent research {uuid4().hex[:8]}",
                research_purpose="Concurrency evidence",
            ),
            "concurrent-create",
        )
    version_data = VersionCreate(
        version_label="Concurrent",
        base_currency="GBP",
        listing_id=listing_id,
        rules=[ResearchRule(id="cross", rule_type="sma_crossover", short_window=2, long_window=3)],
    )
    key = f"version-{uuid4()}"

    async def version_call():
        async with factory() as session:
            return await ResearchService().create_version(
                session, owner, strategy.id, version_data, key, "concurrent-version"
            )

    versions = await asyncio.gather(version_call(), version_call())
    assert versions[0].id == versions[1].id
    async with factory() as session:
        assert (
            await session.scalar(
                select(func.count())
                .select_from(ResearchStrategyVersion)
                .where(ResearchStrategyVersion.strategy_id == strategy.id)
            )
            == 1
        )
    await engine.dispose()


async def create_concurrency_subject(factory, *, label: str):
    owner, _viewer, _outsider, tenant, _other, listing_id = await setup_context(factory)
    async with factory() as session:
        await seed_research_candles(session, listing_id)
        strategy = await ResearchService().create_strategy(
            session,
            owner,
            StrategyCreate(
                tenant_id=tenant.id,
                name=f"{label} {uuid4().hex[:8]}",
                research_purpose="Real PostgreSQL concurrency evidence",
            ),
            f"{label}-strategy",
        )
        version = await ResearchService().create_version(
            session,
            owner,
            strategy.id,
            VersionCreate(
                version_label="SMA 2/3",
                base_currency="GBP",
                listing_id=listing_id,
                rules=[
                    ResearchRule(
                        id="cross",
                        rule_type="sma_crossover",
                        short_window=2,
                        long_window=3,
                    )
                ],
            ),
            f"version-{uuid4()}",
            f"{label}-version",
        )
    run_data = BacktestCreate(
        strategy_id=strategy.id,
        strategy_version_id=version.id,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 10),
        starting_capital=Decimal("1000"),
        fee_model="fixed_amount_per_event",
        fee_value=Decimal("1"),
        slippage_model="fixed_basis_points",
        slippage_bps=Decimal("10"),
        execution_policy="next_open",
        sizing_policy="fixed_percentage_of_available_simulated_cash",
        sizing_value=Decimal("50"),
        missing_data_policy="fail_run",
    )
    return owner, strategy, version, run_data


async def test_concurrent_identical_run_and_execution_requests_create_one_effect() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, strategy, _version, run_data = await create_concurrency_subject(
        factory, label="Identical run"
    )
    key = f"run-{uuid4()}"

    async def execute():
        async with factory() as session:
            return await ResearchService().create_run(
                session, owner, run_data, key, "concurrent-identical-run"
            )

    runs = await asyncio.gather(execute(), execute())
    assert runs[0].id == runs[1].id
    async with factory() as session:
        run_count = await session.scalar(
            select(func.count())
            .select_from(BacktestRun)
            .where(
                BacktestRun.strategy_id == strategy.id,
                BacktestRun.idempotency_key == key,
            )
        )
        result_count = await session.scalar(
            select(func.count())
            .select_from(BacktestResult)
            .where(BacktestResult.run_id == runs[0].id)
        )
        event_count = await session.scalar(
            select(func.count())
            .select_from(BacktestEvent)
            .where(BacktestEvent.run_id == runs[0].id)
        )
        duplicate_sequences = (
            await session.execute(
                select(BacktestEvent.sequence, func.count())
                .where(BacktestEvent.run_id == runs[0].id)
                .group_by(BacktestEvent.sequence)
                .having(func.count() > 1)
            )
        ).all()
        lifecycle_audits = await session.scalar(
            select(func.count())
            .select_from(ResearchAuditEvent)
            .where(
                ResearchAuditEvent.run_id == runs[0].id,
                ResearchAuditEvent.event_type.in_(
                    (
                        "research.backtest.requested",
                        "research.backtest.started",
                        "research.backtest.completed",
                    )
                ),
            )
        )
        assert run_count == 1
        assert result_count == 1
        assert event_count and event_count > 0
        assert duplicate_sequences == []
        assert lifecycle_audits == 3
    await engine.dispose()


async def test_concurrent_conflicting_run_idempotency_key_fails_closed() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, strategy, _version, run_data = await create_concurrency_subject(
        factory, label="Conflicting run"
    )
    conflicting = run_data.model_copy(update={"starting_capital": Decimal("2000")})
    key = f"conflict-{uuid4()}"

    async def execute(payload: BacktestCreate):
        async with factory() as session:
            return await ResearchService().create_run(
                session, owner, payload, key, "concurrent-conflicting-run"
            )

    outcomes = await asyncio.gather(
        execute(run_data),
        execute(conflicting),
        return_exceptions=True,
    )
    successes = [item for item in outcomes if not isinstance(item, BaseException)]
    failures = [item for item in outcomes if isinstance(item, ApplicationError)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].code == "idempotency_conflict"
    assert failures[0].status_code == 409
    async with factory() as session:
        assert (
            await session.scalar(
                select(func.count())
                .select_from(BacktestRun)
                .where(
                    BacktestRun.strategy_id == strategy.id,
                    BacktestRun.idempotency_key == key,
                )
            )
            == 1
        )
    await engine.dispose()


async def test_concurrent_explanation_generation_creates_one_explanation_and_audit() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _strategy, _version, run_data = await create_concurrency_subject(
        factory, label="Concurrent explanation"
    )
    async with factory() as session:
        run = await ResearchService().create_run(
            session, owner, run_data, f"run-{uuid4()}", "explanation-run"
        )
    key = f"explanation-{uuid4()}"

    async def explain():
        async with factory() as session:
            return await ResearchService().explain(
                session,
                owner,
                run.id,
                ExplanationCreate(explanation_type="run_summary"),
                key,
                "concurrent-explanation",
            )

    explanations = await asyncio.gather(explain(), explain())
    assert explanations[0].id == explanations[1].id
    async with factory() as session:
        assert (
            await session.scalar(
                select(func.count())
                .select_from(BacktestExplanation)
                .where(BacktestExplanation.run_id == run.id)
            )
            == 1
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(ResearchAuditEvent)
                .where(
                    ResearchAuditEvent.run_id == run.id,
                    ResearchAuditEvent.event_type == "research.explanation.generated",
                )
            )
            == 1
        )
    await engine.dispose()


@pytest.mark.parametrize("operation", ["run", "version"])
async def test_concurrent_archive_races_fail_closed_without_duplicate_evidence(
    operation: str,
) -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, strategy, _version, run_data = await create_concurrency_subject(
        factory, label=f"Archive race {operation}"
    )

    async def archive():
        async with factory() as session:
            return await ResearchService().archive_strategy(
                session, owner, strategy.id, f"archive-{operation}"
            )

    if operation == "run":

        async def create_child():
            async with factory() as session:
                return await ResearchService().create_run(
                    session,
                    owner,
                    run_data,
                    f"archive-race-run-{uuid4()}",
                    "archive-run-race",
                )

    else:
        configuration = await _version_configuration(factory, strategy.id)

        async def create_child():
            async with factory() as session:
                return await ResearchService().create_version(
                    session,
                    owner,
                    strategy.id,
                    VersionCreate.model_validate(configuration),
                    f"archive-race-version-{uuid4()}",
                    "archive-version-race",
                )

    outcomes = await asyncio.gather(archive(), create_child(), return_exceptions=True)
    assert not isinstance(outcomes[0], BaseException)
    child_failures = [item for item in outcomes[1:] if isinstance(item, ApplicationError)]
    assert not child_failures or child_failures[0].code == "strategy_archived"
    async with factory() as session:
        archived = await session.get(ResearchStrategy, strategy.id)
        assert archived is not None and archived.status.value == "archived"
        if operation == "run":
            run_ids = list(
                (
                    await session.scalars(
                        select(BacktestRun.id).where(BacktestRun.strategy_id == strategy.id)
                    )
                ).all()
            )
            assert len(run_ids) <= 1
            if run_ids:
                assert (
                    await session.scalar(
                        select(func.count())
                        .select_from(BacktestResult)
                        .where(BacktestResult.run_id == run_ids[0])
                    )
                    == 1
                )
        else:
            version_count = await session.scalar(
                select(func.count())
                .select_from(ResearchStrategyVersion)
                .where(ResearchStrategyVersion.strategy_id == strategy.id)
            )
            assert version_count in {1, 2}
    await engine.dispose()


async def _version_configuration(factory, strategy_id):
    async with factory() as session:
        version = await session.scalar(
            select(ResearchStrategyVersion)
            .where(ResearchStrategyVersion.strategy_id == strategy_id)
            .order_by(ResearchStrategyVersion.version_number)
        )
        assert version is not None
        return version.configuration


@pytest.mark.parametrize("execution_policy", ["same_close", "next_close"])
async def test_close_execution_timestamps_match_the_consumed_close(
    execution_policy: str,
) -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _strategy, _version, run_data = await create_concurrency_subject(
        factory, label=f"Timestamp {execution_policy}"
    )
    run_data = run_data.model_copy(update={"execution_policy": execution_policy})
    async with factory() as session:
        run = await ResearchService().create_run(
            session,
            owner,
            run_data,
            f"timestamp-{execution_policy}-{uuid4()}",
            "timestamp-audit",
        )
        events = await ResearchService().events(session, owner, run.id)
        assert events
        assert all(item.simulated_at >= item.decision_at for item in events)
        source_ids = {source_id for item in events for source_id in item.source_observation_ids}
        observations = (
            await session.scalars(
                select(HistoricalCandle).where(HistoricalCandle.id.in_(source_ids))
            )
        ).all()
        by_id = {str(item.id): item for item in observations}
        for item in events:
            executed = by_id[item.source_observation_ids[-1]]
            assert item.simulated_at == executed.period_end
    await engine.dispose()


async def test_unavailable_observation_fails_atomically_without_false_run() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _viewer, _outsider, tenant, _other, listing_id = await setup_context(factory)
    async with factory() as session:
        fixture_start = datetime(2026, 4, 1, tzinfo=UTC)
        await session.execute(
            delete(HistoricalCandle).where(
                HistoricalCandle.listing_id == listing_id,
                HistoricalCandle.provider == "atlas_simulated",
                HistoricalCandle.interval == CandleInterval.ONE_DAY,
                HistoricalCandle.period_start >= fixture_start,
                HistoricalCandle.period_start < fixture_start + timedelta(days=5),
            )
        )
        for index, value in enumerate(("10", "9", "8", "9", "10")):
            start = fixture_start + timedelta(days=index)
            session.add(
                HistoricalCandle(
                    id=uuid4(),
                    listing_id=listing_id,
                    provider="atlas_simulated",
                    interval=CandleInterval.ONE_DAY,
                    period_start=start,
                    period_end=start + timedelta(days=1),
                    open=Decimal(value),
                    high=Decimal(value) + 1,
                    low=Decimal(value) - 1,
                    close=Decimal(value),
                    adjusted_close=Decimal(value),
                    volume=100,
                    currency="GBP",
                    data_status=(
                        MarketDataStatus.UNAVAILABLE if index == 3 else MarketDataStatus.SIMULATED
                    ),
                    received_at=datetime(2026, 5, 1, tzinfo=UTC),
                )
            )
        await session.commit()
        strategy = await ResearchService().create_strategy(
            session,
            owner,
            StrategyCreate(
                tenant_id=tenant.id,
                name=f"Unavailable data {uuid4().hex[:8]}",
                research_purpose="Fail-closed unavailable-data evidence",
            ),
            "unavailable-strategy",
        )
        version = await ResearchService().create_version(
            session,
            owner,
            strategy.id,
            VersionCreate(
                version_label="Unavailable test",
                base_currency="GBP",
                listing_id=listing_id,
                rules=[
                    ResearchRule(
                        id="cross",
                        rule_type="sma_crossover",
                        short_window=2,
                        long_window=3,
                    )
                ],
            ),
            f"unavailable-version-{uuid4()}",
            "unavailable-version",
        )
    run_data = BacktestCreate(
        strategy_id=strategy.id,
        strategy_version_id=version.id,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 6),
        starting_capital=Decimal("1000"),
        fee_model="zero_fee",
        slippage_model="zero_slippage",
        execution_policy="next_open",
        sizing_policy="fixed_quantity",
        sizing_value=Decimal("1"),
        missing_data_policy="fail_run",
    )
    key = f"unavailable-run-{uuid4()}"
    async with factory() as session:
        with pytest.raises(ApplicationError) as unavailable:
            await ResearchService().create_run(session, owner, run_data, key, "unavailable-run")
        assert unavailable.value.code == "market_data_unavailable"
        assert (
            await session.scalar(
                select(func.count())
                .select_from(BacktestRun)
                .where(
                    BacktestRun.strategy_id == strategy.id,
                    BacktestRun.idempotency_key == key,
                )
            )
            == 0
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(ResearchAuditEvent)
                .where(ResearchAuditEvent.operation_id == key)
            )
            == 0
        )
    await engine.dispose()


async def test_completed_run_reconstructs_from_immutable_inputs() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _strategy, version, run_data = await create_concurrency_subject(
        factory, label="Independent reconstruction"
    )
    async with factory() as session:
        run = await ResearchService().create_run(
            session,
            owner,
            run_data,
            f"reconstruction-{uuid4()}",
            "reconstruction-audit",
        )
        stored_events = await ResearchService().events(session, owner, run.id)
        stored_equity = await ResearchService().equity(session, owner, run.id)
        stored_result = await ResearchService().result(session, owner, run.id)
        observations = await ResearchService().repo.candles(
            session, run.listing_id, run.start_date, run.end_date
        )
    rule = cast(list[dict[str, object]], version.configuration["rules"])[0]
    replay = DeterministicBacktestEngine().run(
        observations,
        starting_capital=run.starting_capital,
        rule_id=cast(str, rule["id"]),
        short_window=cast(int, rule["short_window"]),
        long_window=cast(int, rule["long_window"]),
        execution_policy=run.execution_policy,
        fee_model=run.fee_model,
        fee_value=run.fee_value,
        slippage_bps=run.slippage_bps,
        sizing_policy=run.sizing_policy,
        sizing_value=run.sizing_value,
    )
    assert [item.event_type.value for item in stored_events] == [
        item.event_type for item in replay.events
    ]
    assert [item.sequence for item in stored_events] == list(range(1, len(replay.events) + 1))
    assert [item.total_equity for item in stored_equity] == [item.total for item in replay.equity]
    assert stored_result.ending_value == replay.ending_value
    assert stored_result.simulated_pnl == replay.pnl
    assert stored_result.historical_return == replay.historical_return
    assert stored_result.maximum_drawdown == replay.maximum_drawdown
    assert stored_result.volatility == replay.volatility
    assert stored_result.turnover == replay.turnover
    assert stored_result.result_checksum == canonical_fingerprint(
        {
            "engine_result_checksum": replay.result_checksum,
            "benchmark_return": None,
            "missing_count": 0,
            "stale_count": 0,
            "unavailable_count": 0,
            "excluded_count": 0,
        }
    )
    await engine.dispose()
