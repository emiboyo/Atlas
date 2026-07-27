import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.src.core.security import Principal, get_current_principal
from apps.api.src.main import app
from apps.api.src.market.fixtures import fixture_listing_id, seed_development_data
from packages.database.atlas_database.models.enums import (
    MembershipRole,
    MembershipStatus,
    OnboardingStatus,
    TenantStatus,
    TenantType,
    UserStatus,
)
from packages.database.atlas_database.models.identity import Membership, Tenant, User, UserProfile
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
        added = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=headers,
            json={"listing_id": str(nova_xdev), "notes": "<script>safe text</script>"},
        )
        assert added.status_code == 201
        duplicate = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=headers,
            json={"listing_id": str(nova_xdev)},
        )
        assert duplicate.status_code == 409

        current["subject"] = viewer_subject
        viewer_read = await client.get(f"/api/v1/watchlists/{watchlist_id}", headers=headers)
        assert viewer_read.status_code == 200
        viewer_mutation = await client.patch(
            f"/api/v1/watchlists/{watchlist_id}",
            headers=headers,
            json={"name": "Escalated"},
        )
        assert viewer_mutation.status_code == 404

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
