import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.src.core.config import Settings, get_settings
from apps.api.src.core.security import Principal, get_current_principal
from apps.api.src.main import app
from apps.api.src.market.administration import MarketAdministrationService
from apps.api.src.market.cli import run as run_market_command
from apps.api.src.market.fixtures import fixture_listing_id, seed_development_data
from apps.api.src.market.ingestion import MarketIngestionService
from apps.api.src.market.providers import (
    DeterministicFixtureProvider,
    ProviderCandleBatch,
    ProviderError,
    ProviderListingContext,
    ProviderQuote,
)
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MembershipRole,
    MembershipStatus,
    OnboardingStatus,
    TenantStatus,
    TenantType,
    UserStatus,
)
from packages.database.atlas_database.models.identity import (
    IdentityAuditEvent,
    Membership,
    Tenant,
    User,
    UserProfile,
)
from packages.database.atlas_database.models.instruments import (
    HistoricalCandle,
    QuoteObservation,
)
from packages.database.atlas_database.session import set_session_factory

pytestmark = pytest.mark.skipif(
    not os.environ.get("ATLAS_TEST_DATABASE_URL"),
    reason="ATLAS_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


class IntegrationRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int) -> None:
        del ex
        self.values[key] = value


async def test_market_and_tenant_watchlist_flows() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    set_session_factory(engine)
    suffix = uuid4().hex
    owner_subject = f"market_owner_{suffix}"
    viewer_subject = f"market_viewer_{suffix}"
    outsider_subject = f"market_outsider_{suffix}"
    async with factory() as session:
        await seed_development_data(session)
        operation_id = uuid4()
        administration = MarketAdministrationService()
        first_seed = await administration.seed(
            session, operation_id=operation_id, provider="atlas_simulated"
        )
        second_seed = await administration.seed(
            session, operation_id=operation_id, provider="atlas_simulated"
        )
        assert first_seed == second_seed
        assert (
            await session.scalar(
                select(func.count())
                .select_from(IdentityAuditEvent)
                .where(IdentityAuditEvent.id == operation_id)
            )
        ) == 1
        nova_xdev = await fixture_listing_id(session, "NOVA", "XDEV")
        owner = User(clerk_user_id=owner_subject, status=UserStatus.ACTIVE)
        viewer = User(clerk_user_id=viewer_subject, status=UserStatus.ACTIVE)
        outsider = User(clerk_user_id=outsider_subject, status=UserStatus.ACTIVE)
        session.add_all([owner, viewer, outsider])
        await session.flush()
        for user, name in (
            (owner, "Market Owner"),
            (viewer, "Market Viewer"),
            (outsider, "Market Outsider"),
        ):
            user.profile = UserProfile(
                display_name=name, onboarding_status=OnboardingStatus.COMPLETED
            )
        tenant = Tenant(
            clerk_organization_id=f"market:{suffix}",
            slug=f"market-{suffix}",
            display_name="Market Tenant",
            status=TenantStatus.ACTIVE,
            organisation_type=TenantType.TEAM,
            created_by_user_id=owner.id,
        )
        unrelated = Tenant(
            clerk_organization_id=f"market-unrelated:{suffix}",
            slug=f"market-unrelated-{suffix}",
            display_name="Unrelated Market Tenant",
            status=TenantStatus.ACTIVE,
            organisation_type=TenantType.TEAM,
            created_by_user_id=outsider.id,
        )
        session.add_all([tenant, unrelated])
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
                    tenant_id=unrelated.id,
                    user_id=outsider.id,
                    role=MembershipRole.OWNER,
                    status=MembershipStatus.ACTIVE,
                ),
            ]
        )
        await session.commit()
        tenant_id = tenant.id
        unrelated_id = unrelated.id
    assert nova_xdev is not None

    current = {"subject": owner_subject}

    async def principal_override() -> Principal:
        return Principal(
            user_id=current["subject"],
            session_id=f"market_session_{suffix}",
            issued_at=datetime.now(UTC),
        )

    app.dependency_overrides[get_current_principal] = principal_override
    app.state.redis = IntegrationRedis()
    headers = {"Authorization": "Bearer local-test"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        search = await client.get("/api/v1/market/instruments/search?q=NOVA", headers=headers)
        assert search.status_code == 200
        assert search.json()["total"] == 2
        assert {item["listing"]["exchange"]["mic"] for item in search.json()["items"]} == {
            "XDEV",
            "XDEM",
        }
        for query in ("NOVA' OR 1=1 --", "%_", "nOvA", "NOVA   ", "æx"):
            safe_search = await client.get(
                "/api/v1/market/instruments/search",
                headers=headers,
                params={"q": query},
            )
            assert safe_search.status_code == 200
        exact_name = await client.get(
            "/api/v1/market/instruments/search",
            headers=headers,
            params={"q": "Nova Systems Development Equity"},
        )
        assert exact_name.status_code == 200
        assert exact_name.json()["total"] >= 1
        maximum_page = await client.get(
            "/api/v1/market/instruments/search",
            headers=headers,
            params={"q": "NOVA", "page": 10000, "page_size": 100},
        )
        assert maximum_page.status_code == 200
        assert maximum_page.json()["page"] == 10000
        assert (
            await client.get(
                "/api/v1/market/instruments/search",
                headers=headers,
                params={"q": "", "page": 10001},
            )
        ).status_code == 422
        assert (
            await client.get(
                "/api/v1/market/instruments/search",
                headers=headers,
                params={"q": "NOVA", "page_size": 101},
            )
        ).status_code == 422
        assert (
            await client.get(
                "/api/v1/market/instruments/search",
                headers=headers,
                params={"q": "N" * 101},
            )
        ).status_code == 422
        manipulated_provider = await client.get(
            "/api/v1/market/status",
            headers=headers,
            params={"provider": "attacker-controlled"},
        )
        assert manipulated_provider.status_code == 200
        assert manipulated_provider.json()["provider"] == "atlas_simulated"
        cached_search = await client.get(
            "/api/v1/market/instruments/search?q=NOVA", headers=headers
        )
        assert cached_search.json() == search.json()
        instrument_id = search.json()["items"][0]["instrument_id"]
        detail = await client.get(f"/api/v1/market/instruments/{instrument_id}", headers=headers)
        cached_detail = await client.get(
            f"/api/v1/market/instruments/{instrument_id}", headers=headers
        )
        assert detail.status_code == 200
        assert cached_detail.json() == detail.json()

        quote = await client.get(f"/api/v1/market/listings/{nova_xdev}/quote", headers=headers)
        assert quote.status_code == 200
        assert quote.json()["data_status"] == "simulated"
        assert quote.json()["is_stale"] is False
        assert "not investment advice" in quote.json()["disclaimer"]
        cached_quote = await client.get(
            f"/api/v1/market/listings/{nova_xdev}/quote", headers=headers
        )
        assert cached_quote.json() == quote.json()

        candles = await client.get(
            f"/api/v1/market/listings/{nova_xdev}/candles",
            headers=headers,
            params={
                "interval": "1d",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-06T00:00:00Z",
            },
        )
        assert candles.status_code == 200
        assert candles.json()["data_status"] == "simulated"
        assert len(candles.json()["candles"]) == 5
        cached_candles = await client.get(
            f"/api/v1/market/listings/{nova_xdev}/candles",
            headers=headers,
            params={
                "interval": "1d",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-06T00:00:00Z",
            },
        )
        assert cached_candles.json() == candles.json()

        created = await client.post(
            "/api/v1/watchlists",
            headers=headers,
            json={"tenant_id": str(tenant_id), "name": "<b>Research</b>"},
        )
        assert created.status_code == 201
        assert created.json()["name"] == "<b>Research</b>"
        watchlist_id = created.json()["id"]
        owner_permissions = await client.get(
            "/api/v1/watchlists/effective-permissions",
            headers=headers,
            params={"tenant_id": str(tenant_id)},
        )
        assert owner_permissions.status_code == 200
        assert owner_permissions.json()["can_delete_watchlists"] is True
        added = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=headers,
            json={"listing_id": str(nova_xdev), "notes": "<script>safe text</script>"},
        )
        assert added.status_code == 201
        item_id = added.json()["id"]
        duplicate = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=headers,
            json={"listing_id": str(nova_xdev)},
        )
        assert duplicate.status_code == 409

        current["subject"] = viewer_subject
        viewer_permissions = await client.get(
            "/api/v1/watchlists/effective-permissions",
            headers=headers,
            params={"tenant_id": str(tenant_id)},
        )
        assert viewer_permissions.json()["can_read_watchlists"] is True
        assert viewer_permissions.json()["can_add_watchlist_items"] is False
        viewer_read = await client.get(f"/api/v1/watchlists/{watchlist_id}", headers=headers)
        assert viewer_read.status_code == 200
        viewer_mutation = await client.patch(
            f"/api/v1/watchlists/{watchlist_id}",
            headers=headers,
            json={"name": "Escalated"},
        )
        assert viewer_mutation.status_code == 404
        guessed_item = await client.delete(
            f"/api/v1/watchlists/{watchlist_id}/items/{uuid4()}", headers=headers
        )
        assert guessed_item.status_code == 404

        current["subject"] = outsider_subject
        cross_tenant = await client.get(f"/api/v1/watchlists/{watchlist_id}", headers=headers)
        assert cross_tenant.status_code == 404
        manipulated_tenant = await client.get(
            "/api/v1/watchlists",
            headers=headers,
            params={"tenant_id": str(tenant_id)},
        )
        assert manipulated_tenant.status_code == 404

        current["subject"] = owner_subject
        foreign_reorder = await client.patch(
            f"/api/v1/watchlists/{watchlist_id}/items/reorder",
            headers=headers,
            json={"item_ids": [str(item_id), str(uuid4())]},
        )
        assert foreign_reorder.status_code == 422
        archived = await client.delete(f"/api/v1/watchlists/{watchlist_id}", headers=headers)
        assert archived.status_code == 204
        archived_mutation = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=headers,
            json={"listing_id": str(nova_xdev)},
        )
        assert archived_mutation.status_code == 409

        unrelated_access = await client.get(
            "/api/v1/watchlists",
            headers=headers,
            params={"tenant_id": str(unrelated_id)},
        )
        assert unrelated_access.status_code == 404

    app.dependency_overrides.clear()
    del app.state.redis
    await engine.dispose()


async def test_controlled_quote_and_candle_ingestion_is_idempotent() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)

    class NewTimestampProvider(DeterministicFixtureProvider):
        async def get_latest_quote(self, listing: ProviderListingContext) -> ProviderQuote:
            result = await super().get_latest_quote(listing)
            return result.model_copy(
                update={
                    "provider_timestamp": datetime(2026, 1, 16, tzinfo=UTC),
                    "received_at": datetime(2026, 1, 16, 0, 0, 5, tzinfo=UTC),
                    "source_reference": f"fixture:refresh:{listing.listing_id}",
                }
            )

    async with factory() as session:
        await seed_development_data(session)
        listing_id = await fixture_listing_id(session, "NOVA", "XDEV")
        assert listing_id is not None
        await session.execute(
            delete(QuoteObservation).where(
                QuoteObservation.listing_id == listing_id,
                QuoteObservation.provider_timestamp == datetime(2026, 1, 16, tzinfo=UTC),
            )
        )
        await session.execute(
            delete(HistoricalCandle).where(
                HistoricalCandle.listing_id == listing_id,
                HistoricalCandle.interval == CandleInterval.ONE_WEEK,
            )
        )
        await session.commit()
        ingestion = MarketIngestionService(Settings(_env_file=None), NewTimestampProvider())
        mapping_operation_id = uuid4()
        await ingestion.upsert_mapping(
            session,
            listing_id=listing_id,
            provider_symbol="NOVA.XDEV",
            provider_venue_code="XDEV",
            operation_id=mapping_operation_id,
        )
        mapping_event = await session.get(IdentityAuditEvent, mapping_operation_id)
        assert mapping_event is not None
        assert mapping_event.event_type == "market_data.provider_mapping_updated"

        _quote, inserted = await ingestion.refresh_quote(
            session, listing_id=listing_id, operation_id=uuid4()
        )
        assert inserted is True
        _quote, inserted = await ingestion.refresh_quote(
            session, listing_id=listing_id, operation_id=uuid4()
        )
        assert inserted is False

        inserted_candles, duplicates = await ingestion.refresh_candles(
            session,
            listing_id=listing_id,
            interval=CandleInterval.ONE_WEEK,
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 15, tzinfo=UTC),
            operation_id=uuid4(),
        )
        assert (inserted_candles, duplicates) == (2, 0)
        inserted_candles, duplicates = await ingestion.refresh_candles(
            session,
            listing_id=listing_id,
            interval=CandleInterval.ONE_WEEK,
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 15, tzinfo=UTC),
            operation_id=uuid4(),
        )
        assert (inserted_candles, duplicates) == (0, 2)

        class ConflictingQuoteProvider(NewTimestampProvider):
            async def get_latest_quote(self, listing: ProviderListingContext) -> ProviderQuote:
                result = await super().get_latest_quote(listing)
                return result.model_copy(update={"price": result.price + Decimal("1")})

        conflict_operation_id = uuid4()
        with pytest.raises(ProviderError, match="conflicting quote"):
            await MarketIngestionService(
                Settings(_env_file=None), ConflictingQuoteProvider()
            ).refresh_quote(
                session,
                listing_id=listing_id,
                operation_id=conflict_operation_id,
            )
        assert await session.get(IdentityAuditEvent, conflict_operation_id) is None

        class PartiallyConflictingCandleProvider(DeterministicFixtureProvider):
            async def get_historical_candles(
                self,
                listing: ProviderListingContext,
                interval: CandleInterval,
                start: datetime,
                end: datetime,
            ) -> ProviderCandleBatch:
                batch = await super().get_historical_candles(listing, interval, start, end)
                new_first = batch.candles[0].model_copy(
                    update={
                        "period_start": batch.candles[0].period_start - timedelta(days=30),
                        "period_end": batch.candles[0].period_end - timedelta(days=30),
                    }
                )
                conflicting_second = batch.candles[1].model_copy(
                    update={
                        "open": Decimal("100"),
                        "high": Decimal("110"),
                        "low": Decimal("90"),
                        "close": Decimal("105"),
                    }
                )
                return batch.model_copy(update={"candles": (new_first, conflicting_second)})

        partial_operation_id = uuid4()
        new_period = datetime(2025, 12, 2, tzinfo=UTC)
        with pytest.raises(ProviderError, match="conflicting candle"):
            await MarketIngestionService(
                Settings(_env_file=None), PartiallyConflictingCandleProvider()
            ).refresh_candles(
                session,
                listing_id=listing_id,
                interval=CandleInterval.ONE_WEEK,
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 1, 15, tzinfo=UTC),
                operation_id=partial_operation_id,
            )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(HistoricalCandle)
                .where(
                    HistoricalCandle.listing_id == listing_id,
                    HistoricalCandle.interval == CandleInterval.ONE_WEEK,
                    HistoricalCandle.period_start == new_period,
                )
            )
            == 0
        )
        assert await session.get(IdentityAuditEvent, partial_operation_id) is None
    await engine.dispose()


async def test_development_reference_commands_are_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ATLAS_DATABASE_URL", os.environ["ATLAS_TEST_DATABASE_URL"])
    monkeypatch.setenv("ATLAS_ENVIRONMENT", "test")
    get_settings.cache_clear()
    await run_market_command(
        "sync-reference-data",
        uuid4(),
        listing_id=None,
        provider_symbol=None,
        provider_venue_code=None,
        start=None,
        end=None,
    )
    await run_market_command(
        "reconcile-listings",
        uuid4(),
        listing_id=None,
        provider_symbol="NOVA",
        provider_venue_code=None,
        start=None,
        end=None,
    )
    get_settings.cache_clear()
