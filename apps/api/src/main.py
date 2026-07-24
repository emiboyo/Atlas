from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from apps.api.src.api.health import router as health_router
from apps.api.src.api.metrics import router as metrics_router
from apps.api.src.api.router import api_router
from apps.api.src.core.config import get_settings
from apps.api.src.core.errors import register_exception_handlers
from apps.api.src.core.logging import configure_logging, get_logger
from apps.api.src.core.middleware import ObservabilityMiddleware
from apps.api.src.core.security import create_token_verifier
from packages.database.atlas_database.session import (
    create_database_engine,
    set_session_factory,
)

settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_database_engine(settings)
    set_session_factory(engine)
    redis = Redis.from_url(
        settings.redis_url.get_secret_value(), encoding="utf-8", decode_responses=True
    )
    app.state.database_engine = engine
    app.state.redis = redis
    app.state.token_verifier = create_token_verifier(settings)
    logger.info("application_started", environment=settings.environment)
    yield
    await redis.close()
    await engine.dispose()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="The API foundation for the Atlas AI investment operating system.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(ObservabilityMiddleware)
register_exception_handlers(app)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
