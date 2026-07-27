from fastapi import APIRouter
from pydantic import BaseModel

from apps.api.src.api.v1.webhooks import router as webhooks_router
from apps.api.src.core.security import CurrentPrincipal
from apps.api.src.identity.routes import router as identity_router
from apps.api.src.market.routes import router as market_router

router = APIRouter()
router.include_router(webhooks_router)
router.include_router(identity_router)
router.include_router(market_router)


@router.get("/", summary="API v1 information")
async def api_information() -> dict[str, str]:
    return {"name": "Atlas AI API", "version": "v1"}


class AuthenticationContext(BaseModel):
    user_id: str
    session_id: str
    organization_id: str | None
    organization_slug: str | None
    organization_role: str | None
    organization_permissions: list[str]


@router.get("/auth/context", response_model=AuthenticationContext, tags=["Authentication"])
async def authentication_context(principal: CurrentPrincipal) -> AuthenticationContext:
    return AuthenticationContext(
        user_id=principal.user_id,
        session_id=principal.session_id,
        organization_id=principal.organization_id,
        organization_slug=principal.organization_slug,
        organization_role=principal.organization_role,
        organization_permissions=sorted(principal.organization_permissions),
    )
