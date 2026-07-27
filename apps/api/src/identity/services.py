from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.errors import ApplicationError
from apps.api.src.core.security import Principal
from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.identity.repositories import (
    AuditRepository,
    MembershipRepository,
    OrganisationRepository,
    UserRepository,
)
from apps.api.src.identity.schemas import (
    MembershipCreate,
    MembershipUpdate,
    OrganisationCreate,
    OrganisationUpdate,
    ProfileUpdate,
)
from packages.database.atlas_database.models.enums import (
    MembershipRole,
    MembershipStatus,
    OnboardingStatus,
    PlatformRole,
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


def not_found() -> ApplicationError:
    return ApplicationError(
        "The requested resource was not found.",
        code="not_found",
        status_code=status.HTTP_404_NOT_FOUND,
    )


async def commit_or_conflict(session: AsyncSession, *, code: str, message: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ApplicationError(
            message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
        ) from exc


class IdentityService:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.organisations = OrganisationRepository()
        self.audit = AuditRepository()

    async def require_active_user(self, session: AsyncSession, principal: Principal) -> User:
        user = await self.users.by_clerk_subject(session, principal.user_id, with_profile=True)
        if user is None:
            raise ApplicationError(
                "Your Atlas identity has not been provisioned.",
                code="identity_not_provisioned",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if user.status != UserStatus.ACTIVE:
            raise ApplicationError(
                "This account is not active.",
                code="account_inactive",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if user.profile is None:
            raise ApplicationError(
                "Your Atlas profile is unavailable.",
                code="profile_unavailable",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return user

    async def provision(
        self,
        session: AsyncSession,
        *,
        clerk_subject: str,
        display_name: str,
        first_name: str | None,
        last_name: str | None,
        request_id: str | None,
        commit: bool = True,
    ) -> User:
        user = await self.users.by_clerk_subject(session, clerk_subject, with_profile=True)
        profile: UserProfile | None
        if user is None:
            user = User(
                clerk_user_id=clerk_subject,
                status=UserStatus.ACTIVE,
                platform_role=PlatformRole.USER,
            )
            session.add(user)
            await session.flush()
            profile = None
        elif user.status == UserStatus.PENDING:
            user.status = UserStatus.ACTIVE
            profile = user.profile
        elif user.status == UserStatus.DEACTIVATED:
            if commit:
                await session.commit()
            return user
        else:
            profile = user.profile

        if profile is None:
            profile = UserProfile(
                display_name=(display_name.strip() or "Atlas member")[:120],
                first_name=first_name[:80] if first_name else None,
                last_name=last_name[:80] if last_name else None,
                onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
            )
            user.profile = profile

        workspace = await self.organisations.personal_for_user(session, user.id)
        if workspace is None:
            digest = sha256(clerk_subject.encode()).hexdigest()[:20]
            workspace = Tenant(
                clerk_organization_id=f"personal:{digest}",
                slug=f"personal-{digest}",
                display_name=f"{profile.display_name}'s workspace"[:160],
                status=TenantStatus.ACTIVE,
                organisation_type=TenantType.PERSONAL,
                created_by_user_id=user.id,
            )
            session.add(workspace)
            await session.flush()
            session.add(
                Membership(
                    tenant_id=workspace.id,
                    user_id=user.id,
                    role=MembershipRole.OWNER,
                    status=MembershipStatus.ACTIVE,
                )
            )
            self._audit(
                session,
                event_type="organisation.created",
                actor_user_id=user.id,
                tenant_id=workspace.id,
                target_type="organisation",
                target_id=workspace.id,
                request_id=request_id,
                metadata={"organisation_type": "personal"},
            )
        self._audit(
            session,
            event_type="user.provisioned",
            actor_user_id=user.id,
            tenant_id=workspace.id,
            target_type="user",
            target_id=user.id,
            request_id=request_id,
        )
        if commit:
            await session.commit()
        return user

    async def update_profile(
        self,
        session: AsyncSession,
        user: User,
        update: ProfileUpdate,
        request_id: str | None,
    ) -> UserProfile:
        profile = user.profile
        if profile is None:
            raise not_found()
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        if profile.onboarding_status == OnboardingStatus.NOT_STARTED:
            profile.onboarding_status = OnboardingStatus.PROFILE_REQUIRED
        self._audit(
            session,
            event_type="profile.updated",
            actor_user_id=user.id,
            tenant_id=None,
            target_type="profile",
            target_id=profile.id,
            request_id=request_id,
            metadata={"fields": sorted(update.model_fields_set)},
        )
        await session.commit()
        await session.refresh(profile)
        return profile

    async def complete_onboarding(
        self, session: AsyncSession, user: User, request_id: str | None
    ) -> UserProfile:
        profile = user.profile
        if profile is None:
            raise not_found()
        workspace = await self.organisations.personal_for_user(session, user.id)
        if workspace is None:
            raise ApplicationError(
                "A personal workspace is required.",
                code="workspace_required",
                status_code=status.HTTP_409_CONFLICT,
            )
        if not profile.display_name.strip():
            raise ApplicationError(
                "Profile information is required.",
                code="profile_required",
                status_code=status.HTTP_409_CONFLICT,
            )
        if profile.onboarding_status != OnboardingStatus.COMPLETED:
            profile.onboarding_status = OnboardingStatus.COMPLETED
            self._audit(
                session,
                event_type="onboarding.completed",
                actor_user_id=user.id,
                tenant_id=workspace.id,
                target_type="user",
                target_id=user.id,
                request_id=request_id,
            )
            await session.commit()
            await session.refresh(profile)
        return profile

    async def deactivate(
        self,
        session: AsyncSession,
        user: User,
        principal: Principal,
        confirmation: str,
        request_id: str | None,
    ) -> None:
        if confirmation != "DEACTIVATE":
            raise ApplicationError(
                "Explicit confirmation is required.",
                code="deactivation_confirmation_required",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if datetime.now(UTC) - principal.issued_at > timedelta(minutes=10):
            raise ApplicationError(
                "Recent authentication is required.",
                code="recent_authentication_required",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        user.status = UserStatus.DEACTIVATED
        user.deactivated_at = datetime.now(UTC)
        self._audit(
            session,
            event_type="account.deactivated",
            actor_user_id=user.id,
            tenant_id=None,
            target_type="user",
            target_id=user.id,
            request_id=request_id,
        )
        await session.commit()

    def _audit(
        self,
        session: AsyncSession,
        *,
        event_type: str,
        actor_user_id: UUID | None,
        tenant_id: UUID | None,
        target_type: str,
        target_id: UUID | None,
        request_id: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.audit.add(
            session,
            IdentityAuditEvent(
                event_type=event_type,
                actor_user_id=actor_user_id,
                tenant_id=tenant_id,
                target_type=target_type,
                target_id=target_id,
                request_id=request_id,
                event_metadata=metadata or {},
            ),
        )


class OrganisationService:
    def __init__(self) -> None:
        self.organisations = OrganisationRepository()
        self.memberships = MembershipRepository()
        self.users = UserRepository()
        self.authorisation = AuthorisationService()
        self.identity = IdentityService()

    async def require_membership(
        self, session: AsyncSession, organisation_id: UUID, user_id: UUID
    ) -> tuple[Tenant, Membership]:
        membership = await self.memberships.active(session, organisation_id, user_id)
        if membership is None:
            raise not_found()
        organisation = await self.organisations.by_id(session, organisation_id)
        if organisation is None:
            raise not_found()
        if organisation.status != TenantStatus.ACTIVE:
            raise ApplicationError(
                "The organisation is not active.",
                code="organisation_inactive",
                status_code=status.HTTP_409_CONFLICT,
            )
        return organisation, membership

    async def create(
        self,
        session: AsyncSession,
        actor: User,
        data: OrganisationCreate,
        request_id: str | None,
    ) -> tuple[Tenant, Membership]:
        organisation = Tenant(
            clerk_organization_id=f"atlas:{sha256(data.slug.encode()).hexdigest()[:24]}",
            slug=data.slug,
            display_name=data.name,
            organisation_type=TenantType.TEAM,
            status=TenantStatus.ACTIVE,
            created_by_user_id=actor.id,
        )
        session.add(organisation)
        await session.flush()
        membership = Membership(
            tenant_id=organisation.id,
            user_id=actor.id,
            role=MembershipRole.OWNER,
            status=MembershipStatus.ACTIVE,
        )
        session.add(membership)
        self.identity._audit(
            session,
            event_type="organisation.created",
            actor_user_id=actor.id,
            tenant_id=organisation.id,
            target_type="organisation",
            target_id=organisation.id,
            request_id=request_id,
            metadata={"organisation_type": "team"},
        )
        await commit_or_conflict(
            session,
            code="organisation_slug_conflict",
            message="The organisation slug is already in use.",
        )
        return organisation, membership

    async def update(
        self,
        session: AsyncSession,
        actor: User,
        organisation_id: UUID,
        data: OrganisationUpdate,
        request_id: str | None,
    ) -> Tenant:
        organisation, membership = await self.require_membership(session, organisation_id, actor.id)
        self.authorisation.require_permission(membership.role, Permission.ORGANISATION_UPDATE)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(organisation, "display_name" if field == "name" else field, value)
        self.identity._audit(
            session,
            event_type="organisation.updated",
            actor_user_id=actor.id,
            tenant_id=organisation.id,
            target_type="organisation",
            target_id=organisation.id,
            request_id=request_id,
            metadata={"fields": sorted(data.model_fields_set)},
        )
        await commit_or_conflict(
            session,
            code="organisation_slug_conflict",
            message="The organisation slug is already in use.",
        )
        await session.refresh(organisation)
        return organisation

    async def add_member(
        self,
        session: AsyncSession,
        actor: User,
        organisation_id: UUID,
        data: MembershipCreate,
        request_id: str | None,
    ) -> Membership:
        _, actor_membership = await self.require_membership(session, organisation_id, actor.id)
        self.authorisation.require_permission(actor_membership.role, Permission.MEMBERSHIP_INVITE)
        if data.role == MembershipRole.OWNER:
            self.authorisation.require_role(actor_membership.role, {MembershipRole.OWNER})
        target = await self.users.by_id(session, data.user_id)
        if target is None or target.status != UserStatus.ACTIVE:
            raise not_found()
        existing = await self.memberships.active(session, organisation_id, target.id)
        if existing:
            raise ApplicationError(
                "The user is already an active member.",
                code="membership_exists",
                status_code=status.HTTP_409_CONFLICT,
            )
        membership = Membership(
            tenant_id=organisation_id,
            user_id=target.id,
            role=data.role,
            status=MembershipStatus.ACTIVE,
        )
        session.add(membership)
        await session.flush()
        self.identity._audit(
            session,
            event_type="membership.created",
            actor_user_id=actor.id,
            tenant_id=organisation_id,
            target_type="membership",
            target_id=membership.id,
            request_id=request_id,
            metadata={"role": data.role.value},
        )
        await commit_or_conflict(
            session,
            code="membership_conflict",
            message="The membership could not be created.",
        )
        return membership

    async def update_member(
        self,
        session: AsyncSession,
        actor: User,
        organisation_id: UUID,
        membership_id: UUID,
        data: MembershipUpdate,
        request_id: str | None,
    ) -> Membership:
        _, actor_membership = await self.require_membership(session, organisation_id, actor.id)
        self.authorisation.require_permission(actor_membership.role, Permission.MEMBERSHIP_UPDATE)
        target = await self.memberships.by_id(session, organisation_id, membership_id)
        if target is None:
            raise not_found()
        if target.role == MembershipRole.OWNER or data.role == MembershipRole.OWNER:
            self.authorisation.require_role(actor_membership.role, {MembershipRole.OWNER})
        previous_role = target.role
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(target, field, value)
        self.identity._audit(
            session,
            event_type="membership.role_changed",
            actor_user_id=actor.id,
            tenant_id=organisation_id,
            target_type="membership",
            target_id=target.id,
            request_id=request_id,
            metadata={"previous_role": previous_role.value, "role": target.role.value},
        )
        await commit_or_conflict(
            session,
            code="final_owner_required",
            message="An organisation must retain an active owner.",
        )
        await session.refresh(target)
        return target

    async def remove_member(
        self,
        session: AsyncSession,
        actor: User,
        organisation_id: UUID,
        membership_id: UUID,
        request_id: str | None,
    ) -> None:
        _, actor_membership = await self.require_membership(session, organisation_id, actor.id)
        self.authorisation.require_permission(actor_membership.role, Permission.MEMBERSHIP_REMOVE)
        target = await self.memberships.by_id(session, organisation_id, membership_id)
        if target is None:
            raise not_found()
        if target.role == MembershipRole.OWNER:
            self.authorisation.require_role(actor_membership.role, {MembershipRole.OWNER})
        target.status = MembershipStatus.REMOVED
        self.identity._audit(
            session,
            event_type="membership.removed",
            actor_user_id=actor.id,
            tenant_id=organisation_id,
            target_type="membership",
            target_id=target.id,
            request_id=request_id,
        )
        await commit_or_conflict(
            session,
            code="final_owner_required",
            message="An organisation must retain an active owner.",
        )

    async def transfer_ownership(
        self,
        session: AsyncSession,
        actor: User,
        organisation_id: UUID,
        target_membership_id: UUID,
        request_id: str | None,
    ) -> None:
        _, actor_membership = await self.require_membership(session, organisation_id, actor.id)
        self.authorisation.require_permission(actor_membership.role, Permission.OWNERSHIP_TRANSFER)
        target = await self.memberships.by_id(session, organisation_id, target_membership_id)
        if target is None or target.status != MembershipStatus.ACTIVE:
            raise not_found()
        if target.id == actor_membership.id:
            return
        target.role = MembershipRole.OWNER
        await session.flush()
        actor_membership.role = MembershipRole.ADMIN
        self.identity._audit(
            session,
            event_type="ownership.transferred",
            actor_user_id=actor.id,
            tenant_id=organisation_id,
            target_type="membership",
            target_id=target.id,
            request_id=request_id,
        )
        await commit_or_conflict(
            session,
            code="ownership_transfer_conflict",
            message="Ownership could not be transferred.",
        )
