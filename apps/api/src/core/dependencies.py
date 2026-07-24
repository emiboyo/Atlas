from typing import Annotated, Any, cast

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import Settings, get_settings
from packages.database.atlas_database.session import get_session

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


def get_redis(request: Request) -> Redis:  # type: ignore[type-arg]
    return cast("Redis[Any]", request.app.state.redis)


RedisClient = Annotated[Redis, Depends(get_redis)]
