from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.src.main import app


@asynccontextmanager
async def no_lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = no_lifespan
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.router.lifespan_context = original_lifespan
