import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import TypeVar

from apps.api.src.market.metrics import PROVIDER_ERRORS, PROVIDER_LATENCY
from apps.api.src.market.providers import ProviderError

T = TypeVar("T")


class ProviderExecutor:
    def __init__(
        self,
        *,
        timeout_seconds: float,
        retry_count: int,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.sleep = sleep

    async def execute(
        self,
        provider: str,
        operation: str,
        call: Callable[[], Awaitable[T]],
    ) -> T:
        for attempt in range(self.retry_count + 1):
            started = perf_counter()
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    return await call()
            except TimeoutError as exc:
                error = ProviderError(
                    "The market-data provider timed out.", code="provider_timeout"
                )
                if attempt >= self.retry_count:
                    PROVIDER_ERRORS.labels(provider=provider, code=error.code).inc()
                    raise error from exc
            except ProviderError as exc:
                PROVIDER_ERRORS.labels(provider=provider, code=exc.code).inc()
                raise
            except (ConnectionError, OSError) as exc:
                error = ProviderError(
                    "The market-data provider is unavailable.", code="provider_unavailable"
                )
                if attempt >= self.retry_count:
                    PROVIDER_ERRORS.labels(provider=provider, code=error.code).inc()
                    raise error from exc
            finally:
                PROVIDER_LATENCY.labels(provider=provider, operation=operation).observe(
                    perf_counter() - started
                )
            await self.sleep(0.05 * (attempt + 1))
        raise AssertionError("Provider execution loop exhausted unexpectedly")
