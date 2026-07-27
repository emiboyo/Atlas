import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.src.core.clerk_webhooks import ClerkWebhook, ClerkWebhookData, ClerkWebhookService
from apps.api.src.core.security import Principal, get_current_principal
from apps.api.src.main import app
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


async def test_verified_user_and_cross_tenant_isolation() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    set_session_factory(engine)
    suffix = uuid4().hex
    async with factory() as session:
        user = User(clerk_user_id=f"user_{suffix}", status=UserStatus.ACTIVE)
        outsider = User(clerk_user_id=f"outsider_{suffix}", status=UserStatus.ACTIVE)
        session.add_all([user, outsider])
        await session.flush()
        user.profile = UserProfile(
            display_name="Integration User",
            onboarding_status=OnboardingStatus.COMPLETED,
        )
        tenant = Tenant(
            clerk_organization_id=f"org_{suffix}",
            slug=f"org-{suffix}",
            display_name="Integration Organisation",
            status=TenantStatus.ACTIVE,
            organisation_type=TenantType.TEAM,
            created_by_user_id=user.id,
        )
        unrelated = Tenant(
            clerk_organization_id=f"unrelated_{suffix}",
            slug=f"unrelated-{suffix}",
            display_name="Unrelated Organisation",
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
                    user_id=user.id,
                    role=MembershipRole.OWNER,
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

    async def principal_override() -> Principal:
        return Principal(user_id=f"user_{suffix}", session_id=f"session_{suffix}")

    app.dependency_overrides[get_current_principal] = principal_override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        me = await client.get("/api/v1/me", headers={"Authorization": "Bearer local-test"})
        denied = await client.get(
            f"/api/v1/organisations/{unrelated.id}",
            headers={"Authorization": "Bearer local-test"},
        )

    app.dependency_overrides.clear()
    await engine.dispose()
    assert me.status_code == 200
    assert me.json()["profile"]["display_name"] == "Integration User"
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "not_found"


async def test_webhook_provisioning_is_idempotent() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    set_session_factory(engine)
    suffix = uuid4().hex
    event = ClerkWebhook(
        type="user.created",
        timestamp=int(datetime.now(UTC).timestamp() * 1000),
        data=ClerkWebhookData(id=f"webhook_{suffix}", first_name="Webhook"),
    )
    service = ClerkWebhookService()
    async with factory() as session:
        first = await service.process(
            session,
            svix_id=f"msg_{suffix}",
            event=event,
            payload=b"synthetic-payload",
            request_id="integration-request",
        )
        second = await service.process(
            session,
            svix_id=f"msg_{suffix}",
            event=event,
            payload=b"synthetic-payload",
            request_id="integration-request",
        )
        user = await session.scalar(select(User).where(User.clerk_user_id == f"webhook_{suffix}"))
        assert user is not None
        workspace_count = await session.scalar(
            select(func.count())
            .select_from(Membership)
            .join(Tenant)
            .where(
                Membership.user_id == user.id,
                Tenant.organisation_type == TenantType.PERSONAL,
            )
        )

    async def principal_override() -> Principal:
        return Principal(
            user_id=f"webhook_{suffix}",
            session_id=f"session_{suffix}",
            issued_at=datetime.now(UTC),
        )

    app.dependency_overrides[get_current_principal] = principal_override
    headers = {"Authorization": "Bearer local-test"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        onboarding = await client.get("/api/v1/onboarding", headers=headers)
        assert onboarding.status_code == 200
        assert onboarding.json()["personal_workspace"]["organisation_type"] == "personal"
        profile = await client.patch(
            "/api/v1/onboarding/profile",
            headers=headers,
            json={
                "display_name": "Webhook User",
                "timezone": "Europe/London",
                "base_currency": "GBP",
            },
        )
        assert profile.status_code == 200
        completed = await client.post("/api/v1/onboarding/complete", headers=headers)
        assert completed.status_code == 200
        assert completed.json()["onboarding_status"] == "completed"

    app.dependency_overrides.clear()
    await engine.dispose()

    assert first is True
    assert second is False
    assert workspace_count == 1


async def test_role_enforcement_owner_transfer_and_deactivation() -> None:
    engine = create_async_engine(os.environ["ATLAS_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    set_session_factory(engine)
    suffix = uuid4().hex
    owner_subject = f"owner_{suffix}"
    viewer_subject = f"viewer_{suffix}"
    async with factory() as session:
        owner = User(clerk_user_id=owner_subject, status=UserStatus.ACTIVE)
        viewer = User(clerk_user_id=viewer_subject, status=UserStatus.ACTIVE)
        session.add_all([owner, viewer])
        await session.flush()
        owner.profile = UserProfile(
            display_name="Owner",
            onboarding_status=OnboardingStatus.COMPLETED,
        )
        viewer.profile = UserProfile(
            display_name="Viewer",
            onboarding_status=OnboardingStatus.COMPLETED,
        )
        await session.commit()
        viewer_id = viewer.id

    current_subject = {"value": owner_subject}

    async def principal_override() -> Principal:
        return Principal(
            user_id=current_subject["value"],
            session_id=f"session_{suffix}",
            issued_at=datetime.now(UTC),
        )

    app.dependency_overrides[get_current_principal] = principal_override
    headers = {"Authorization": "Bearer local-test"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        created = await client.post(
            "/api/v1/organisations",
            headers=headers,
            json={"name": "Role Test", "slug": f"role-{suffix}"},
        )
        assert created.status_code == 201
        organisation_id = created.json()["id"]

        member = await client.post(
            f"/api/v1/organisations/{organisation_id}/members",
            headers=headers,
            json={"user_id": str(viewer_id), "role": "viewer"},
        )
        assert member.status_code == 201
        viewer_membership_id = member.json()["id"]

        organisations = await client.get("/api/v1/organisations", headers=headers)
        assert organisations.status_code == 200
        assert organisations.json()["total"] >= 1

        owner_members = await client.get(
            f"/api/v1/organisations/{organisation_id}/members",
            headers=headers,
        )
        owner_membership_id = next(
            item["id"] for item in owner_members.json()["items"] if item["role"] == "owner"
        )
        final_owner = await client.patch(
            f"/api/v1/organisations/{organisation_id}/members/{owner_membership_id}",
            headers=headers,
            json={"role": "admin"},
        )
        assert final_owner.status_code == 409
        assert final_owner.json()["error"]["code"] == "final_owner_required"

        current_subject["value"] = viewer_subject
        forbidden = await client.patch(
            f"/api/v1/organisations/{organisation_id}",
            headers=headers,
            json={"name": "Escalated"},
        )
        assert forbidden.status_code == 403

        current_subject["value"] = owner_subject
        transfer = await client.post(
            f"/api/v1/organisations/{organisation_id}/transfer-ownership",
            headers=headers,
            json={"membership_id": viewer_membership_id},
        )
        assert transfer.status_code == 204
        audit = await client.get(
            f"/api/v1/organisations/{organisation_id}/audit-events",
            headers=headers,
        )
        assert audit.status_code == 200
        assert any(event["event_type"] == "ownership.transferred" for event in audit.json())

        deactivated = await client.post(
            "/api/v1/me/deactivate",
            headers=headers,
            json={"confirmation": "DEACTIVATE"},
        )
        assert deactivated.status_code == 204
        denied = await client.get("/api/v1/me", headers=headers)
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "account_inactive"

    app.dependency_overrides.clear()
    await engine.dispose()
