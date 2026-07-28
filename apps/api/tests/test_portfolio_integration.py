import asyncio
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.src.core.errors import ApplicationError
from apps.api.src.market.fixtures import fixture_listing_id, seed_development_data
from apps.api.src.portfolio.schemas import (
    PortfolioCreate,
    PortfolioUpdate,
    ReversalCreate,
    TransactionCreate,
)
from apps.api.src.portfolio.services import (
    PortfolioQueryService,
    PortfolioService,
    TransactionPostingService,
)
from packages.database.atlas_database.models.enums import (
    MembershipRole,
    MembershipStatus,
    PortfolioTransactionStatus,
    PortfolioTransactionType,
    TenantStatus,
    TenantType,
    UserStatus,
    ValuationCompleteness,
)
from packages.database.atlas_database.models.identity import Membership, Tenant, User
from packages.database.atlas_database.models.ledger import LedgerEntry
from packages.database.atlas_database.models.portfolios import (
    PortfolioAuditEvent,
    PortfolioPosition,
    PortfolioTransaction,
    PortfolioValuationSnapshot,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("ATLAS_TEST_DATABASE_URL"),
    reason="ATLAS_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


async def setup_context(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[User, User, User, Tenant, Tenant, object]:
    suffix = uuid4().hex
    async with factory() as session:
        await seed_development_data(session)
        listing_id = await fixture_listing_id(session, "NOVA", "XDEV")
        assert listing_id is not None
        owner = User(clerk_user_id=f"portfolio_owner_{suffix}", status=UserStatus.ACTIVE)
        viewer = User(clerk_user_id=f"portfolio_viewer_{suffix}", status=UserStatus.ACTIVE)
        outsider = User(clerk_user_id=f"portfolio_outsider_{suffix}", status=UserStatus.ACTIVE)
        session.add_all([owner, viewer, outsider])
        await session.flush()
        tenant = Tenant(
            clerk_organization_id=f"portfolio:{suffix}",
            slug=f"portfolio-{suffix}",
            display_name="Portfolio development tenant",
            status=TenantStatus.ACTIVE,
            organisation_type=TenantType.TEAM,
            created_by_user_id=owner.id,
        )
        other = Tenant(
            clerk_organization_id=f"portfolio-other:{suffix}",
            slug=f"portfolio-other-{suffix}",
            display_name="Other development tenant",
            status=TenantStatus.ACTIVE,
            organisation_type=TenantType.TEAM,
            created_by_user_id=outsider.id,
        )
        session.add_all([tenant, other])
        await session.flush()
        session.add_all(
            [
                Membership(
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role=MembershipRole.OWNER,
                    status=MembershipStatus.ACTIVE,
                ),
                Membership(
                    tenant_id=tenant.id,
                    user_id=viewer.id,
                    role=MembershipRole.VIEWER,
                    status=MembershipStatus.ACTIVE,
                ),
                Membership(
                    tenant_id=other.id,
                    user_id=outsider.id,
                    role=MembershipRole.OWNER,
                    status=MembershipStatus.ACTIVE,
                ),
            ]
        )
        await session.commit()
        return owner, viewer, outsider, tenant, other, listing_id


async def create_portfolio(
    factory: async_sessionmaker[AsyncSession], owner: User, tenant: Tenant
) -> object:
    async with factory() as session:
        result = await PortfolioService().create(
            session,
            owner,
            PortfolioCreate(
                tenant_id=tenant.id,
                name=f"Simulated {uuid4().hex[:8]}",
                description="Integration-test paper accounting",
                base_currency="GBP",
            ),
            "request-create",
        )
        return result.id


def transaction(transaction_type: PortfolioTransactionType, **values: object) -> TransactionCreate:
    return TransactionCreate(
        transaction_type=transaction_type,
        currency="GBP",
        effective_at=datetime.now(UTC),
        **values,
    )


async def post(
    factory: async_sessionmaker[AsyncSession],
    owner: User,
    portfolio_id: object,
    data: TransactionCreate,
    key: str,
):
    async with factory() as session:
        return await TransactionPostingService().post(
            session, owner, portfolio_id, data, key, f"request-{key}"
        )


async def test_complete_simulated_accounting_workflow_and_reversal() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, viewer, outsider, tenant, _other, listing_id = await setup_context(factory)
    portfolio_id = await create_portfolio(factory, owner, tenant)

    deposit = await post(
        factory,
        owner,
        portfolio_id,
        transaction(PortfolioTransactionType.VIRTUAL_DEPOSIT, amount=Decimal("1000.00")),
        f"deposit-{uuid4()}",
    )
    buy_data = transaction(
        PortfolioTransactionType.SIMULATED_BUY,
        listing_id=listing_id,
        quantity=Decimal("10"),
        unit_price=Decimal("20"),
        fee_amount=Decimal("2"),
    )
    buy_key = f"buy-{uuid4()}"
    buy = await post(factory, owner, portfolio_id, buy_data, buy_key)
    retry = await post(factory, owner, portfolio_id, buy_data, buy_key)
    assert retry.id == buy.id

    with pytest.raises(ApplicationError, match="different data") as conflict:
        await post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.SIMULATED_BUY,
                listing_id=listing_id,
                quantity=Decimal("1"),
                unit_price=Decimal("20"),
            ),
            buy_key,
        )
    assert conflict.value.code == "idempotency_conflict"

    sell = await post(
        factory,
        owner,
        portfolio_id,
        transaction(
            PortfolioTransactionType.SIMULATED_SELL,
            listing_id=listing_id,
            quantity=Decimal("4"),
            unit_price=Decimal("30"),
            fee_amount=Decimal("1"),
        ),
        f"sell-{uuid4()}",
    )
    await post(
        factory,
        owner,
        portfolio_id,
        transaction(
            PortfolioTransactionType.SIMULATED_DIVIDEND,
            listing_id=listing_id,
            amount=Decimal("5"),
        ),
        f"dividend-{uuid4()}",
    )
    await post(
        factory,
        owner,
        portfolio_id,
        transaction(
            PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT,
            listing_id=listing_id,
            split_ratio=Decimal("2"),
        ),
        f"split-{uuid4()}",
    )
    await post(
        factory,
        owner,
        portfolio_id,
        TransactionCreate(
            transaction_type=PortfolioTransactionType.VIRTUAL_DEPOSIT,
            currency="USD",
            amount=Decimal("50"),
            effective_at=datetime.now(UTC),
        ),
        f"usd-deposit-{uuid4()}",
    )

    async with factory() as session:
        holdings = await PortfolioQueryService().holdings(session, owner, portfolio_id)
        assert len(holdings) == 1
        assert holdings[0].quantity == Decimal("12")
        assert holdings[0].cost_basis == Decimal("120")
        assert holdings[0].average_cost_per_unit == Decimal("10")
        assert holdings[0].realised_simulated_pnl == Decimal("39")
        transactions = await PortfolioQueryService().transactions_list(
            session, owner, portfolio_id, offset=0, limit=100
        )
        assert len(transactions) == 6
        assert len({item.sequence for item in transactions}) == 6
        valuation = await PortfolioQueryService().valuation(session, owner, portfolio_id)
        assert valuation.base_currency_total is None
        assert valuation.is_complete is False
        assert valuation.unconverted_currencies == ["USD"]
        assert {item.currency for item in valuation.virtual_cash_by_currency} == {
            "GBP",
            "USD",
        }
        journal_sums = (
            await session.execute(
                select(LedgerEntry.transaction_id, func.sum(LedgerEntry.amount)).group_by(
                    LedgerEntry.transaction_id
                )
            )
        ).all()
        assert all(total == Decimal("0") for _journal_id, total in journal_sums)

    async with factory() as session:
        reversed_sell = await TransactionPostingService().reverse(
            session,
            owner,
            portfolio_id,
            sell.id,
            ReversalCreate(
                reason="Correct an integration-test simulated sale",
                effective_at=datetime.now(UTC),
            ),
            f"reverse-{uuid4()}",
            "request-reversal",
        )
        assert reversed_sell.transaction_type == PortfolioTransactionType.REVERSAL

    async with factory() as session:
        original = await session.get(PortfolioTransaction, sell.id)
        position = await session.scalar(
            select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio_id)
        )
        assert original is not None
        assert original.status == PortfolioTransactionStatus.REVERSED
        assert position is not None
        assert position.quantity == Decimal("16")
        assert position.cost_basis == Decimal("200")
        assert position.realised_pnl == Decimal("0")
        assert (
            await session.scalar(
                select(func.count())
                .select_from(PortfolioAuditEvent)
                .where(PortfolioAuditEvent.portfolio_id == portfolio_id)
            )
            or 0
        ) >= 8

        with pytest.raises(ApplicationError) as duplicate_reversal:
            await TransactionPostingService().reverse(
                session,
                owner,
                portfolio_id,
                sell.id,
                ReversalCreate(
                    reason="Attempt duplicate reversal",
                    effective_at=datetime.now(UTC),
                ),
                f"second-reverse-{uuid4()}",
                "request-second-reversal",
            )
        assert duplicate_reversal.value.code == "transaction_already_reversed"

    async with factory() as session:
        with pytest.raises(ApplicationError) as viewer_denied:
            await TransactionPostingService().post(
                session,
                viewer,
                portfolio_id,
                transaction(
                    PortfolioTransactionType.VIRTUAL_DEPOSIT,
                    amount=Decimal("10"),
                ),
                f"viewer-{uuid4()}",
                "request-viewer",
            )
        assert viewer_denied.value.status_code == 403
        with pytest.raises(ApplicationError) as concealed:
            await PortfolioService().get(session, outsider, portfolio_id)
        assert concealed.value.code == "portfolio_not_found"

    assert deposit.is_simulated
    await engine.dispose()


async def test_insufficient_cash_quantity_archival_and_atomic_rollback() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _viewer, _outsider, tenant, _other, listing_id = await setup_context(factory)
    portfolio_id = await create_portfolio(factory, owner, tenant)

    with pytest.raises(ApplicationError) as insufficient_cash:
        await post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.SIMULATED_BUY,
                listing_id=listing_id,
                quantity=Decimal("1"),
                unit_price=Decimal("10"),
            ),
            f"no-cash-{uuid4()}",
        )
    assert insufficient_cash.value.code == "insufficient_virtual_cash"

    async with factory() as session:
        assert (
            await session.scalar(
                select(func.count())
                .select_from(PortfolioTransaction)
                .where(PortfolioTransaction.portfolio_id == portfolio_id)
            )
            == 0
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(PortfolioAuditEvent)
                .where(
                    PortfolioAuditEvent.portfolio_id == portfolio_id,
                    PortfolioAuditEvent.event_type == "portfolio.transaction.posted",
                )
            )
            == 0
        )

    await post(
        factory,
        owner,
        portfolio_id,
        transaction(PortfolioTransactionType.VIRTUAL_DEPOSIT, amount=Decimal("100")),
        f"cash-{uuid4()}",
    )
    with pytest.raises(ApplicationError) as insufficient_quantity:
        await post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.SIMULATED_SELL,
                listing_id=listing_id,
                quantity=Decimal("1"),
                unit_price=Decimal("10"),
            ),
            f"oversell-{uuid4()}",
        )
    assert insufficient_quantity.value.code == "insufficient_simulated_quantity"

    async with factory() as session:
        await PortfolioService().archive(session, owner, portfolio_id, "request-archive")
    with pytest.raises(ApplicationError) as archived:
        await post(
            factory,
            owner,
            portfolio_id,
            transaction(PortfolioTransactionType.VIRTUAL_DEPOSIT, amount=Decimal("1")),
            f"archived-{uuid4()}",
        )
    assert archived.value.code == "portfolio_archived"
    await engine.dispose()


async def test_postgresql_concurrent_idempotency_overspend_and_oversell() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _viewer, _outsider, tenant, _other, listing_id = await setup_context(factory)
    portfolio_id = await create_portfolio(factory, owner, tenant)
    await post(
        factory,
        owner,
        portfolio_id,
        transaction(PortfolioTransactionType.VIRTUAL_DEPOSIT, amount=Decimal("100")),
        f"initial-{uuid4()}",
    )

    duplicate_key = f"duplicate-{uuid4()}"
    duplicate_data = transaction(PortfolioTransactionType.VIRTUAL_WITHDRAWAL, amount=Decimal("10"))
    duplicate_results = await asyncio.gather(
        post(factory, owner, portfolio_id, duplicate_data, duplicate_key),
        post(factory, owner, portfolio_id, duplicate_data, duplicate_key),
    )
    assert duplicate_results[0].id == duplicate_results[1].id

    withdrawal_results = await asyncio.gather(
        post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.VIRTUAL_WITHDRAWAL,
                amount=Decimal("70"),
            ),
            f"withdraw-a-{uuid4()}",
        ),
        post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.VIRTUAL_WITHDRAWAL,
                amount=Decimal("70"),
            ),
            f"withdraw-b-{uuid4()}",
        ),
        return_exceptions=True,
    )
    assert sum(not isinstance(result, Exception) for result in withdrawal_results) == 1
    assert any(
        isinstance(result, ApplicationError) and result.code == "insufficient_virtual_cash"
        for result in withdrawal_results
    )

    await post(
        factory,
        owner,
        portfolio_id,
        transaction(PortfolioTransactionType.VIRTUAL_DEPOSIT, amount=Decimal("200")),
        f"replenish-{uuid4()}",
    )
    await post(
        factory,
        owner,
        portfolio_id,
        transaction(
            PortfolioTransactionType.SIMULATED_BUY,
            listing_id=listing_id,
            quantity=Decimal("5"),
            unit_price=Decimal("10"),
        ),
        f"position-{uuid4()}",
    )
    sell_results = await asyncio.gather(
        post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.SIMULATED_SELL,
                listing_id=listing_id,
                quantity=Decimal("4"),
                unit_price=Decimal("11"),
            ),
            f"sell-a-{uuid4()}",
        ),
        post(
            factory,
            owner,
            portfolio_id,
            transaction(
                PortfolioTransactionType.SIMULATED_SELL,
                listing_id=listing_id,
                quantity=Decimal("4"),
                unit_price=Decimal("11"),
            ),
            f"sell-b-{uuid4()}",
        ),
        return_exceptions=True,
    )
    assert sum(not isinstance(result, Exception) for result in sell_results) == 1
    assert any(
        isinstance(result, ApplicationError) and result.code == "insufficient_simulated_quantity"
        for result in sell_results
    )
    await engine.dispose()


async def test_snapshot_statistics_and_aligned_descriptive_benchmark() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, _viewer, _outsider, tenant, _other, listing_id = await setup_context(factory)
    portfolio_id = await create_portfolio(factory, owner, tenant)
    async with factory() as session:
        updated = await PortfolioService().update(
            session,
            owner,
            portfolio_id,
            PortfolioUpdate(benchmark_listing_id=listing_id, version=1),
            "request-benchmark",
        )
        assert updated.benchmark_listing_id == listing_id
    start = datetime(2026, 1, 1, tzinfo=UTC)
    async with factory() as session:
        for index, value in enumerate(("100", "110", "90")):
            session.add(
                PortfolioValuationSnapshot(
                    tenant_id=tenant.id,
                    portfolio_id=portfolio_id,
                    idempotency_key=f"history-{uuid4()}",
                    as_of=start + timedelta(days=index),
                    base_currency="GBP",
                    base_currency_total=Decimal(value),
                    completeness=ValuationCompleteness.COMPLETE,
                    created_by_user_id=owner.id,
                    is_simulated=True,
                )
            )
        await session.commit()
    async with factory() as session:
        query = PortfolioQueryService()
        history = await query.history(
            session, owner, portfolio_id, start, start + timedelta(days=3)
        )
        assert len(history.points) == 3
        assert history.points[-1].percentage_change == Decimal("-10")
        drawdown = await query.statistic(
            session,
            owner,
            portfolio_id,
            "maximum_drawdown",
            start,
            start + timedelta(days=3),
        )
        assert drawdown.value == Decimal("-18.181818181818181818")
        volatility = await query.statistic(
            session,
            owner,
            portfolio_id,
            "volatility",
            start,
            start + timedelta(days=3),
        )
        assert volatility.value is not None
        benchmark = await query.benchmark(
            session, owner, portfolio_id, start, start + timedelta(days=3)
        )
        assert benchmark.aligned_observations == 3
        assert benchmark.status == "complete"
        assert benchmark.benchmark_percentage_change is not None
        assert benchmark.missing_dates == []
        assert benchmark.data_status_summary == {"simulated": 3}
    await engine.dispose()
