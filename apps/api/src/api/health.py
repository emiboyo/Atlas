from typing import Literal, cast

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    status: Literal["healthy", "unhealthy"]
    service: str
    version: str


class ReadinessStatus(HealthStatus):
    dependencies: dict[str, str]


@router.get("/live", response_model=HealthStatus, summary="Liveness probe")
async def liveness() -> HealthStatus:
    return HealthStatus(status="healthy", service="atlas-api", version="0.1.0")


@router.get("/ready", response_model=ReadinessStatus, summary="Readiness probe")
async def readiness(request: Request, response: Response) -> ReadinessStatus:
    dependencies: dict[str, str] = {}
    engine: AsyncEngine = request.app.state.database_engine
    redis = cast(Redis, request.app.state.redis)

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        dependencies["postgres"] = "healthy"
    except Exception:  # noqa: BLE001
        dependencies["postgres"] = "unhealthy"

    try:
        await redis.ping()
        dependencies["redis"] = "healthy"
    except Exception:  # noqa: BLE001
        dependencies["redis"] = "unhealthy"

    healthy = all(value == "healthy" for value in dependencies.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessStatus(
        status="healthy" if healthy else "unhealthy",
        service="atlas-api",
        version="0.1.0",
        dependencies=dependencies,
    )
