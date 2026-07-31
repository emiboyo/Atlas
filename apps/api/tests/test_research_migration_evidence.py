import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.src.research.schemas import ResearchRule, StrategyCreate, VersionCreate
from apps.api.src.research.services import ResearchService
from apps.api.tests.test_research_integration import create_concurrency_subject
from packages.database.atlas_database.models.research import ResearchAuditEvent

pytestmark = pytest.mark.skipif(
    not os.environ.get("ATLAS_TEST_DATABASE_URL"),
    reason="ATLAS_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def rejection_details(error: DBAPIError) -> tuple[str | None, str | None]:
    driver_error = error.orig.__cause__ or error.orig
    return (
        getattr(driver_error, "sqlstate", None),
        getattr(driver_error, "constraint_name", None),
    )


def database_url(database: str) -> str:
    return os.environ["ATLAS_TEST_DATABASE_URL"].rsplit("/", 1)[0] + f"/{database}"


def run_alembic(url: str, revision: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["ATLAS_DATABASE_URL"] = url
    return subprocess.run(  # noqa: S603 - fixed interpreter and static Alembic arguments
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "packages/database/alembic.ini",
            "upgrade",
            revision,
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


async def create_database(name: str) -> None:
    admin = create_async_engine(database_url("postgres"), isolation_level="AUTOCOMMIT")
    async with admin.connect() as connection:
        await connection.execute(text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()


async def drop_database(name: str) -> None:
    admin = create_async_engine(database_url("postgres"), isolation_level="AUTOCOMMIT")
    async with admin.connect() as connection:
        await connection.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": name},
        )
        await connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
    await admin.dispose()


async def create_other_version(factory, owner, strategy, version):
    async with factory() as session:
        other_strategy = await ResearchService().create_strategy(
            session,
            owner,
            StrategyCreate(
                tenant_id=strategy.tenant_id,
                name=f"Migration evidence {uuid4().hex[:8]}",
                research_purpose="Controlled malformed revision 0007 evidence",
            ),
            "migration-evidence-strategy",
        )
        other_version = await ResearchService().create_version(
            session,
            owner,
            other_strategy.id,
            VersionCreate(
                version_label="Other parent",
                base_currency="GBP",
                listing_id=UUID(str(version.configuration["listing_id"])),
                rules=[
                    ResearchRule(
                        id="cross",
                        rule_type="sma_crossover",
                        short_window=2,
                        long_window=3,
                    )
                ],
            ),
            f"migration-evidence-version-{uuid4()}",
            "migration-evidence-version",
        )
    return other_strategy, other_version


@pytest.mark.parametrize(
    ("case", "expected_message"),
    [
        ("run_parent", "malformed backtest run"),
        ("cross_tenant_run_parent", "malformed backtest run"),
        ("current_version", "malformed current version"),
        ("cross_tenant_current_version", "malformed current version"),
        ("audit_version", "malformed audit parent"),
        ("audit_run", "malformed audit parent"),
        ("audit_run_without_version", "malformed audit parent"),
        ("missing_policy", "unsupported historical missing-data policy"),
    ],
)
async def test_malformed_revision_0007_data_blocks_0008_without_mutation(
    case: str, expected_message: str
) -> None:
    name = f"atlas_m5_migration_{case}_{uuid4().hex[:8]}"
    await create_database(name)
    url = database_url(name)
    engine = None
    try:
        upgrade_0007 = run_alembic(url, "20260728_0007")
        assert upgrade_0007.returncode == 0, upgrade_0007.stderr

        engine = create_async_engine(url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        owner, strategy, version, run_data = await create_concurrency_subject(
            factory, label=f"Migration {case}"
        )
        async with factory() as session:
            source_run = await ResearchService().create_run(
                session,
                owner,
                run_data,
                f"migration-source-{uuid4()}",
                "migration-source",
            )
        other_strategy, other_version = await create_other_version(
            factory, owner, strategy, version
        )
        cross_version = None
        if case in {"cross_tenant_run_parent", "cross_tenant_current_version"}:
            (
                _cross_owner,
                _cross_strategy,
                cross_version,
                _cross_data,
            ) = await create_concurrency_subject(factory, label=f"Migration cross-tenant {case}")

        async with factory() as session:
            if case in {"run_parent", "cross_tenant_run_parent", "missing_policy"}:
                if case == "cross_tenant_run_parent":
                    assert cross_version is not None
                    await session.execute(
                        text(
                            "ALTER TABLE backtest_runs "
                            "DROP CONSTRAINT fk_backtest_runs_version_tenant"
                        )
                    )
                await session.execute(
                    text(
                        """
                        INSERT INTO backtest_runs (
                          tenant_id, strategy_id, strategy_version_id, listing_id, status,
                          idempotency_key, request_fingerprint, configuration_fingerprint,
                          data_fingerprint, start_date, end_date, starting_capital,
                          base_currency, fee_model, fee_value, slippage_model,
                          slippage_bps, execution_policy, sizing_policy, sizing_value,
                          missing_data_policy, engine_version, software_version,
                          requested_by_user_id, requested_at, started_at, completed_at,
                          failure_code, is_historical_simulation, id, created_at
                        )
                        SELECT tenant_id, strategy_id, :version_id, listing_id, status,
                          :key, request_fingerprint, configuration_fingerprint,
                          data_fingerprint, start_date, end_date, starting_capital,
                          base_currency, fee_model, fee_value, slippage_model,
                          slippage_bps, execution_policy, sizing_policy, sizing_value,
                          :policy, engine_version, software_version, requested_by_user_id,
                          requested_at, started_at, completed_at, failure_code,
                          is_historical_simulation, :id, now()
                        FROM backtest_runs WHERE id = :source_id
                        """
                    ),
                    {
                        "version_id": (
                            other_version.id
                            if case == "run_parent"
                            else (
                                cross_version.id
                                if case == "cross_tenant_run_parent"
                                else version.id
                            )
                        ),
                        "key": f"malformed-{uuid4()}",
                        "policy": "skip_event" if case == "missing_policy" else "fail_run",
                        "id": uuid4(),
                        "source_id": source_run.id,
                    },
                )
            elif case in {"current_version", "cross_tenant_current_version"}:
                target_version = (
                    cross_version if case == "cross_tenant_current_version" else other_version
                )
                assert target_version is not None
                await session.execute(
                    text(
                        "UPDATE research_strategies SET current_version_id = :version "
                        "WHERE id = :strategy"
                    ),
                    {"version": target_version.id, "strategy": strategy.id},
                )
            else:
                source_audit = await session.scalar(
                    select(ResearchAuditEvent)
                    .where(ResearchAuditEvent.strategy_id == strategy.id)
                    .order_by(ResearchAuditEvent.created_at.desc())
                )
                assert source_audit is not None
                session.add(
                    ResearchAuditEvent(
                        tenant_id=strategy.tenant_id,
                        strategy_id=strategy.id,
                        strategy_version_id=(
                            version.id
                            if case == "audit_run"
                            else (None if case == "audit_run_without_version" else other_version.id)
                        ),
                        run_id=(
                            uuid4()
                            if case == "audit_run"
                            else (source_run.id if case == "audit_run_without_version" else None)
                        ),
                        event_type="research.evidence.malformed",
                        request_id="migration-evidence",
                        operation_id=f"malformed-{uuid4()}",
                        actor_user_id=owner.id,
                        target_id=other_strategy.id,
                        event_metadata={},
                    )
                )
            await session.commit()

        async with factory() as session:
            before = {
                "runs": (
                    await session.execute(
                        text(
                            "SELECT id::text, strategy_id::text, "
                            "strategy_version_id::text, missing_data_policy "
                            "FROM backtest_runs ORDER BY id"
                        )
                    )
                ).all(),
                "audits": (
                    await session.execute(
                        text(
                            "SELECT id::text, strategy_id::text, "
                            "strategy_version_id::text, run_id::text "
                            "FROM research_audit_events ORDER BY id"
                        )
                    )
                ).all(),
            }

        failed_upgrade = run_alembic(url, "head")
        assert failed_upgrade.returncode != 0
        assert expected_message in (failed_upgrade.stdout + failed_upgrade.stderr)

        async with factory() as session:
            after = {
                "runs": (
                    await session.execute(
                        text(
                            "SELECT id::text, strategy_id::text, "
                            "strategy_version_id::text, missing_data_policy "
                            "FROM backtest_runs ORDER BY id"
                        )
                    )
                ).all(),
                "audits": (
                    await session.execute(
                        text(
                            "SELECT id::text, strategy_id::text, "
                            "strategy_version_id::text, run_id::text "
                            "FROM research_audit_events ORDER BY id"
                        )
                    )
                ).all(),
            }
            revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
            new_constraint = await session.scalar(
                text(
                    "SELECT count(*) FROM pg_constraint "
                    "WHERE conname = 'fk_backtest_runs_version_parent'"
                )
            )
        assert after == before
        assert revision == "20260728_0007"
        assert new_constraint == 0
    finally:
        if engine is not None:
            await engine.dispose()
        await drop_database(name)


async def test_revision_0008_reports_exact_parent_constraint_rejections() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, strategy, version, run_data = await create_concurrency_subject(
        factory, label="Constraint evidence"
    )
    async with factory() as session:
        source_run = await ResearchService().create_run(
            session,
            owner,
            run_data,
            f"constraint-source-{uuid4()}",
            "constraint-evidence",
        )
    _other_strategy, other_version = await create_other_version(factory, owner, strategy, version)
    _cross_owner, _cross_strategy, cross_version, _cross_data = await create_concurrency_subject(
        factory, label="Cross tenant constraint"
    )

    clone_run = text(
        """
        INSERT INTO backtest_runs (
          tenant_id, strategy_id, strategy_version_id, listing_id, status,
          idempotency_key, request_fingerprint, configuration_fingerprint,
          data_fingerprint, start_date, end_date, starting_capital, base_currency,
          fee_model, fee_value, slippage_model, slippage_bps, execution_policy,
          sizing_policy, sizing_value, missing_data_policy, engine_version,
          software_version, requested_by_user_id, requested_at, started_at,
          completed_at, failure_code, is_historical_simulation, id, created_at
        )
        SELECT tenant_id, strategy_id, :version_id, listing_id, status, :key,
          request_fingerprint, configuration_fingerprint, data_fingerprint,
          start_date, end_date, starting_capital, base_currency, fee_model,
          fee_value, slippage_model, slippage_bps, execution_policy, sizing_policy,
          sizing_value, missing_data_policy, engine_version, software_version,
          requested_by_user_id, requested_at, started_at, completed_at,
          failure_code, is_historical_simulation, :id, now()
        FROM backtest_runs WHERE id = :source_id
        """
    )
    for label, rejected_version in (
        ("same-tenant", other_version.id),
        ("cross-tenant", cross_version.id),
    ):
        async with factory() as session:
            with pytest.raises(DBAPIError) as rejected:
                await session.execute(
                    clone_run,
                    {
                        "version_id": rejected_version,
                        "key": f"{label}-{uuid4()}",
                        "id": uuid4(),
                        "source_id": source_run.id,
                    },
                )
                await session.commit()
            assert rejection_details(rejected.value) == (
                "23503",
                "fk_backtest_runs_version_parent",
            )
            await session.rollback()
            assert await session.scalar(text("SELECT 1")) == 1

    audit_insert = text(
        """
        INSERT INTO research_audit_events (
          tenant_id, strategy_id, strategy_version_id, run_id, event_type,
          request_id, operation_id, actor_user_id, target_id, event_metadata, id
        ) VALUES (
          :tenant_id, :strategy_id, :version_id, :run_id, 'research.invalid',
          'constraint-evidence', :operation_id, :actor_id, :target_id, '{}', :id
        )
        """
    )
    audit_cases = (
        (other_version.id, None, "23503", "fk_research_audit_version_parent"),
        (version.id, uuid4(), "23503", "fk_research_audit_run_parent"),
        (
            None,
            source_run.id,
            "23514",
            "ck_research_audit_events_ck_research_audit_events_resea_6150",
        ),
    )
    for rejected_version, rejected_run, sqlstate, constraint in audit_cases:
        async with factory() as session:
            with pytest.raises(DBAPIError) as rejected:
                await session.execute(
                    audit_insert,
                    {
                        "tenant_id": strategy.tenant_id,
                        "strategy_id": strategy.id,
                        "version_id": rejected_version,
                        "run_id": rejected_run,
                        "operation_id": f"audit-invalid-{uuid4()}",
                        "actor_id": owner.id,
                        "target_id": strategy.id,
                        "id": uuid4(),
                    },
                )
                await session.commit()
            assert rejection_details(rejected.value) == (sqlstate, constraint)
            await session.rollback()

    for label, rejected_version in (
        ("same-tenant", other_version.id),
        ("cross-tenant", cross_version.id),
    ):
        async with factory() as session:
            await session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            await session.execute(
                text(
                    "UPDATE research_strategies SET current_version_id = :version "
                    "WHERE id = :strategy"
                ),
                {"version": rejected_version, "strategy": strategy.id},
            )
            with pytest.raises(DBAPIError) as deferred:
                await session.commit()
            assert rejection_details(deferred.value) == (
                "23503",
                "fk_research_strategy_current_version_parent",
            ), label
            await session.rollback()
            assert await session.scalar(text("SELECT 1")) == 1

    for table, identifier, message in (
        ("research_strategy_versions", version.id, "research history is append-only"),
        ("backtest_runs", source_run.id, "completed backtest runs are immutable"),
    ):
        async with factory() as session:
            with pytest.raises(DBAPIError) as restricted:
                await session.execute(
                    text(f"DELETE FROM {table} WHERE id = :id"),  # noqa: S608
                    {"id": identifier},
                )
                await session.commit()
            sqlstate, constraint = rejection_details(restricted.value)
            assert sqlstate == "23000"
            assert constraint is None
            assert message in str(restricted.value.orig)
            await session.rollback()

    async with factory() as session:
        restrict_constraints = (
            await session.execute(
                text(
                    "SELECT conname, confdeltype FROM pg_constraint "
                    "WHERE conname = ANY(:names) ORDER BY conname"
                ),
                {
                    "names": [
                        "fk_backtest_runs_version_parent",
                        "fk_research_audit_run_parent",
                        "fk_research_audit_version_parent",
                        "fk_research_strategy_current_version_parent",
                    ]
                },
            )
        ).all()
    assert restrict_constraints == [
        ("fk_backtest_runs_version_parent", b"r"),
        ("fk_research_audit_run_parent", b"r"),
        ("fk_research_audit_version_parent", b"r"),
        ("fk_research_strategy_current_version_parent", b"r"),
    ]
    async with factory() as session:
        valid_current_version = await session.scalar(
            text("SELECT current_version_id FROM research_strategies WHERE id = :strategy"),
            {"strategy": _other_strategy.id},
        )
        assert valid_current_version == other_version.id
        assert await session.scalar(text("SELECT 1")) == 1
    await engine.dispose()
