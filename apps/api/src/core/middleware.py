import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

REQUEST_COUNT = Counter(
    "atlas_http_requests_total",
    "Total HTTP requests.",
    ["method", "route", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "atlas_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "route"],
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        started_at = time.perf_counter()

        response = await call_next(request)
        duration = time.perf_counter() - started_at
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")

        REQUEST_COUNT.labels(request.method, route_path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, route_path).observe(duration)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            route=route_path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        return response
