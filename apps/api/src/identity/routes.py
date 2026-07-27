from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from apps.api.src.core.dependencies import DatabaseSession
from apps.api.src.core.security import CurrentPrincipal
from apps.api.src.identity.authorization import Permission
from apps.api.src.identity.dependencies import ActiveUser
from apps.api.src.identity.schemas import (
    AuditEventResponse,
    DeactivationRequest,
    MembershipCreate,
    MembershipResponse,
    MembershipUpdate,
    OnboardingResponse,
    OrganisationCreate,
    OrganisationResponse,
    OrganisationUpdate,
    Page,
    ProfileResponse,
    ProfileUpdate,
    TransferOwnershipRequest,
    UserResponse,
)
from apps.api.src.identity.services import IdentityService, OrganisationService
from packages.database.atlas_database.models.enums import MembershipRole
from packages.database.atlas_database.models.identity import Tenant

router = APIRouter()


def request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def organisation_response(
    organisation: Tenant, *, role: MembershipRole | None = None
) -> OrganisationResponse:
    return OrganisationResponse(
        id=organisation.id,
        name=organisation.display_name,
        slug=organisation.slug,
        organisation_type=organisation.organisation_type,
        status=organisation.status,
        role=role,
        created_at=organisation.created_at,
        updated_at=organisation.updated_at,
    )


@router.get("/me", response_model=UserResponse, tags=["Identity"])
async def get_me(user: ActiveUser) -> UserResponse:
    return UserResponse(
        id=user.id,
        status=user.status,
        platform_role=user.platform_role,
        profile=ProfileResponse.model_validate(user.profile),
    )


@router.patch("/me/profile", response_model=ProfileResponse, tags=["Identity"])
async def update_me_profile(
    payload: ProfileUpdate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> ProfileResponse:
    profile = await IdentityService().update_profile(session, user, payload, request_id(request))
    return ProfileResponse.model_validate(profile)


@router.post(
    "/me/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Identity"],
)
async def deactivate_me(
    payload: DeactivationRequest,
    request: Request,
    session: DatabaseSession,
    principal: CurrentPrincipal,
    user: ActiveUser,
) -> Response:
    await IdentityService().deactivate(
        session, user, principal, payload.confirmation, request_id(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/onboarding", response_model=OnboardingResponse, tags=["Onboarding"])
async def get_onboarding(session: DatabaseSession, user: ActiveUser) -> OnboardingResponse:
    service = IdentityService()
    workspace = await service.organisations.personal_for_user(session, user.id)
    if workspace is None:
        from apps.api.src.identity.services import not_found

        raise not_found()
    profile = ProfileResponse.model_validate(user.profile)
    return OnboardingResponse(
        status=profile.onboarding_status,
        profile=profile,
        personal_workspace=organisation_response(workspace),
    )


@router.patch("/onboarding/profile", response_model=ProfileResponse, tags=["Onboarding"])
async def update_onboarding_profile(
    payload: ProfileUpdate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> ProfileResponse:
    profile = await IdentityService().update_profile(session, user, payload, request_id(request))
    return ProfileResponse.model_validate(profile)


@router.post("/onboarding/complete", response_model=ProfileResponse, tags=["Onboarding"])
async def complete_onboarding(
    request: Request, session: DatabaseSession, user: ActiveUser
) -> ProfileResponse:
    profile = await IdentityService().complete_onboarding(session, user, request_id(request))
    return ProfileResponse.model_validate(profile)


@router.get("/organisations", response_model=Page, tags=["Organisations"])
async def list_organisations(
    session: DatabaseSession,
    user: ActiveUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page:
    repository = OrganisationService().organisations
    rows = await repository.for_user(
        session, user.id, offset=(page - 1) * page_size, limit=page_size
    )
    items = [
        organisation_response(organisation, role=membership.role).model_dump()
        for organisation, membership in rows
    ]
    return Page(
        items=items,
        page=page,
        page_size=page_size,
        total=await repository.count_for_user(session, user.id),
    )


@router.post(
    "/organisations",
    response_model=OrganisationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Organisations"],
)
async def create_organisation(
    payload: OrganisationCreate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> OrganisationResponse:
    organisation, membership = await OrganisationService().create(
        session, user, payload, request_id(request)
    )
    return organisation_response(organisation, role=membership.role)


@router.get(
    "/organisations/{organisation_id}",
    response_model=OrganisationResponse,
    tags=["Organisations"],
)
async def get_organisation(
    organisation_id: UUID, session: DatabaseSession, user: ActiveUser
) -> OrganisationResponse:
    organisation, membership = await OrganisationService().require_membership(
        session, organisation_id, user.id
    )
    return organisation_response(organisation, role=membership.role)


@router.patch(
    "/organisations/{organisation_id}",
    response_model=OrganisationResponse,
    tags=["Organisations"],
)
async def update_organisation(
    organisation_id: UUID,
    payload: OrganisationUpdate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> OrganisationResponse:
    organisation = await OrganisationService().update(
        session, user, organisation_id, payload, request_id(request)
    )
    membership = await OrganisationService().memberships.active(session, organisation_id, user.id)
    return organisation_response(
        organisation, role=membership.role if membership is not None else None
    )


@router.get(
    "/organisations/{organisation_id}/members",
    response_model=Page,
    tags=["Memberships"],
)
async def list_members(
    organisation_id: UUID,
    session: DatabaseSession,
    user: ActiveUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page:
    service = OrganisationService()
    _, actor_membership = await service.require_membership(session, organisation_id, user.id)
    service.authorisation.require_permission(actor_membership.role, Permission.MEMBERSHIP_READ)
    rows = await service.memberships.list(
        session, organisation_id, offset=(page - 1) * page_size, limit=page_size
    )
    return Page(
        items=[MembershipResponse.model_validate(item).model_dump() for item in rows],
        page=page,
        page_size=page_size,
        total=await service.memberships.count(session, organisation_id),
    )


@router.post(
    "/organisations/{organisation_id}/members",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Memberships"],
)
async def add_member(
    organisation_id: UUID,
    payload: MembershipCreate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> MembershipResponse:
    membership = await OrganisationService().add_member(
        session, user, organisation_id, payload, request_id(request)
    )
    return MembershipResponse.model_validate(membership)


@router.patch(
    "/organisations/{organisation_id}/members/{membership_id}",
    response_model=MembershipResponse,
    tags=["Memberships"],
)
async def update_member(
    organisation_id: UUID,
    membership_id: UUID,
    payload: MembershipUpdate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> MembershipResponse:
    membership = await OrganisationService().update_member(
        session, user, organisation_id, membership_id, payload, request_id(request)
    )
    return MembershipResponse.model_validate(membership)


@router.delete(
    "/organisations/{organisation_id}/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Memberships"],
)
async def remove_member(
    organisation_id: UUID,
    membership_id: UUID,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> Response:
    await OrganisationService().remove_member(
        session, user, organisation_id, membership_id, request_id(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/organisations/{organisation_id}/transfer-ownership",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Memberships"],
)
async def transfer_ownership(
    organisation_id: UUID,
    payload: TransferOwnershipRequest,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> Response:
    await OrganisationService().transfer_ownership(
        session, user, organisation_id, payload.membership_id, request_id(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/organisations/{organisation_id}/audit-events",
    response_model=list[AuditEventResponse],
    tags=["Audit"],
)
async def list_audit_events(
    organisation_id: UUID,
    session: DatabaseSession,
    user: ActiveUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[AuditEventResponse]:
    service = OrganisationService()
    _, membership = await service.require_membership(session, organisation_id, user.id)
    service.authorisation.require_permission(membership.role, Permission.AUDIT_READ)
    events = await service.identity.audit.list(
        session, organisation_id, offset=(page - 1) * page_size, limit=page_size
    )
    return [AuditEventResponse.model_validate(event) for event in events]
