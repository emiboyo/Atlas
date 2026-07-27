from typing import Annotated

from fastapi import Depends

from apps.api.src.core.dependencies import DatabaseSession
from apps.api.src.core.security import CurrentPrincipal
from apps.api.src.identity.services import IdentityService
from packages.database.atlas_database.models.identity import User


async def get_active_user(principal: CurrentPrincipal, session: DatabaseSession) -> User:
    return await IdentityService().require_active_user(session, principal)


ActiveUser = Annotated[User, Depends(get_active_user)]
