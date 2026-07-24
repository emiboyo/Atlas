from httpx import AsyncClient

from apps.api.src.main import app


class FakeConnection:
    async def __aenter__(self) -> "FakeConnection":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def execute(self, _: object) -> None:
        return None


class FakeEngine:
    def connect(self) -> FakeConnection:
        return FakeConnection()


class FakeRedis:
    async def ping(self) -> bool:
        return True


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "atlas-api",
        "version": "0.1.0",
    }
    assert response.headers["x-request-id"]


async def test_api_v1_root(client: AsyncClient) -> None:
    response = await client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["version"] == "v1"


async def test_readiness_checks_dependencies(client: AsyncClient) -> None:
    app.state.database_engine = FakeEngine()
    app.state.redis = FakeRedis()

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"] == {
        "postgres": "healthy",
        "redis": "healthy",
    }


async def test_metrics_are_prometheus_formatted(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "atlas_http_requests_total" in response.text
