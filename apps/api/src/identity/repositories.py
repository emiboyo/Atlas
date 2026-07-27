from collections.abc import Sequence
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.database.atlas_database.models.enums import MembershipStatus, TenantType
from packages.database.atlas_database.models.identity import (
    ClerkWebhookEvent,
    IdentityAuditEvent,
    Membership,
    Tenant,
    User,
)


class UserRepository:
    async def by_clerk_subject(
        self, session: AsyncSession, clerk_subject: str, *, with_profile: bool = False
    ) -> User | None:
        statement = select(User).where(User.clerk_user_id == clerk_subject)
        if with_profile:
            statement = statement.options(selectinload(User.profile))
        return cast(User | None, await session.scalar(statement))

    async def by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        return await session.get(User, user_id)


class OrganisationRepository:
    async def by_id(self, session: AsyncSession, organisation_id: UUID) -> Tenant | None:
        return await session.get(Tenant, organisation_id)

    async def personal_for_user(self, session: AsyncSession, user_id: UUID) -> Tenant | None:
        return cast(
            Tenant | None,
            await session.scalar(
                select(Tenant)
                .join(Membership)
                .where(
                    Membership.user_id == user_id,
                    Membership.status == MembershipStatus.ACTIVE,
                    Tenant.organisation_type == TenantType.PERSONAL,
                )
            ),
        )

    async def for_user(
        self, session: AsyncSession, user_id: UUID, *, offset: int, limit: int
    ) -> Sequence[tuple[Tenant, Membership]]:
        result = await session.execute(
            select(Tenant, Membership)
            .join(Membership)
            .where(
                Membership.user_id == user_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
            .order_by(Tenant.created_at)
            .offset(offset)
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def count_for_user(self, session: AsyncSession, user_id: UUID) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(Membership)
                .where(
                    Membership.user_id == user_id,
                    Membership.status == MembershipStatus.ACTIVE,
                )
            )
            or 0
        )


class MembershipRepository:
    async def active(
        self, session: AsyncSession, organisation_id: UUID, user_id: UUID
    ) -> Membership | None:
        return cast(
            Membership | None,
            await session.scalar(
                select(Membership).where(
                    Membership.tenant_id == organisation_id,
                    Membership.user_id == user_id,
                    Membership.status == MembershipStatus.ACTIVE,
                )
            ),
        )

    async def by_id(
        self, session: AsyncSession, organisation_id: UUID, membership_id: UUID
    ) -> Membership | None:
        return cast(
            Membership | None,
            await session.scalar(
                select(Membership).where(
                    Membership.id == membership_id,
                    Membership.tenant_id == organisation_id,
                )
            ),
        )

    async def list(
        self, session: AsyncSession, organisation_id: UUID, *, offset: int, limit: int
    ) -> Sequence[Membership]:
        return (
            await session.scalars(
                select(Membership)
                .where(Membership.tenant_id == organisation_id)
                .order_by(Membership.created_at)
                .offset(offset)
                .limit(limit)
            )
        ).all()

    async def count(self, session: AsyncSession, organisation_id: UUID) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(Membership)
                .where(Membership.tenant_id == organisation_id)
            )
            or 0
        )


class AuditRepository:
    def add(self, session: AsyncSession, event: IdentityAuditEvent) -> None:
        session.add(event)

    async def list(
        self, session: AsyncSession, organisation_id: UUID, *, offset: int, limit: int
    ) -> Sequence[IdentityAuditEvent]:
        return (
            await session.scalars(
                select(IdentityAuditEvent)
                .where(IdentityAuditEvent.tenant_id == organisation_id)
                .order_by(IdentityAuditEvent.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).all()


class WebhookRepository:
    async def by_svix_id(self, session: AsyncSession, svix_id: str) -> ClerkWebhookEvent | None:
        return cast(
            ClerkWebhookEvent | None,
            await session.scalar(
                select(ClerkWebhookEvent).where(ClerkWebhookEvent.svix_id == svix_id)
            ),
        )
