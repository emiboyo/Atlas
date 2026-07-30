from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from prometheus_client import Counter, Histogram

from apps.api.src.core.errors import ApplicationError

P = ParamSpec("P")
R = TypeVar("R")

STRATEGY_OPERATIONS = Counter(
    "atlas_research_strategy_operations_total",
    "Bounded research strategy operations.",
    ["operation", "outcome"],
)
BACKTESTS = Counter("atlas_research_backtests_total", "Historical simulation runs.", ["outcome"])
BACKTEST_DURATION = Histogram(
    "atlas_research_backtest_duration_seconds",
    "Historical simulation duration.",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
RESEARCH_CONFLICTS = Counter("atlas_research_conflicts_total", "Research conflicts.", ["operation"])
EXPLANATIONS = Counter(
    "atlas_research_explanations_total", "Local deterministic explanations.", ["outcome"]
)
DATA_QUALITY = Counter(
    "atlas_research_data_quality_total",
    "Bounded historical-data quality outcomes.",
    ["outcome"],
)


def metric_outcome(exc: Exception) -> str:
    if isinstance(exc, ApplicationError):
        if exc.status_code in (401, 403, 404):
            return "denied"
        if exc.status_code == 409:
            return "conflict"
    return "failure"


def track_strategy(
    operation: str,
) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
    def decorator(
        function: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(function)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                value = await function(*args, **kwargs)
            except Exception as exc:
                STRATEGY_OPERATIONS.labels(operation=operation, outcome=metric_outcome(exc)).inc()
                raise
            STRATEGY_OPERATIONS.labels(operation=operation, outcome="success").inc()
            return value

        return wrapped

    return decorator


def track_backtest[**Args, Result](
    function: Callable[Args, Coroutine[Any, Any, Result]],
) -> Callable[Args, Coroutine[Any, Any, Result]]:
    @wraps(function)
    async def wrapped(*args: Args.args, **kwargs: Args.kwargs) -> Result:
        BACKTESTS.labels(outcome="requested").inc()
        try:
            return await function(*args, **kwargs)
        except ApplicationError as exc:
            if exc.code not in {
                "idempotency_conflict",
                "market_data_unavailable",
                "insufficient_historical_data",
            }:
                BACKTESTS.labels(outcome="failed").inc()
            raise
        except Exception:
            BACKTESTS.labels(outcome="failed").inc()
            raise

    return wrapped


def track_explanation[**Args, Result](
    function: Callable[Args, Coroutine[Any, Any, Result]],
) -> Callable[Args, Coroutine[Any, Any, Result]]:
    @wraps(function)
    async def wrapped(*args: Args.args, **kwargs: Args.kwargs) -> Result:
        EXPLANATIONS.labels(outcome="requested").inc()
        try:
            return await function(*args, **kwargs)
        except ApplicationError as exc:
            if exc.status_code in (401, 403, 404):
                EXPLANATIONS.labels(outcome="denied").inc()
            elif exc.code not in {"explanations_disabled", "idempotency_conflict"}:
                EXPLANATIONS.labels(outcome="failed").inc()
            raise
        except Exception:
            EXPLANATIONS.labels(outcome="failed").inc()
            raise

    return wrapped
