from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, status

from apps.api.src.core.config import get_settings
from apps.api.src.core.dependencies import DatabaseSession
from apps.api.src.identity.authorization import Permission
from apps.api.src.identity.dependencies import ActiveUser
from apps.api.src.market.cache import MarketCache
from apps.api.src.market.services import MarketService
from apps.api.src.portfolio.metrics import PORTFOLIO_REQUESTS
from apps.api.src.portfolio.schemas import (
    AnalyticsResponse,
    AuditEventResponse,
    BenchmarkAnalytics,
    EffectivePortfolioPermissions,
    HistoryResponse,
    HoldingResponse,
    IdempotencyKey,
    PortfolioCreate,
    PortfolioPage,
    PortfolioResponse,
    PortfolioUpdate,
    ReversalCreate,
    StatisticalAnalytics,
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
    ValuationResponse,
    ValuationSnapshotResponse,
)
from apps.api.src.portfolio.services import (
    PortfolioAuthorisation,
    PortfolioQueryService,
    PortfolioService,
    TransactionPostingService,
)

router = APIRouter(prefix="/portfolios", tags=["Simulated portfolios"])
IdempotencyHeader = Annotated[IdempotencyKey, Header(alias="Idempotency-Key")]


def request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def query_service(request: Request) -> PortfolioQueryService:
    redis = getattr(request.app.state, "redis", None)
    market = MarketService(
        get_settings(),
        MarketCache(redis) if redis is not None else None,
    )
    return PortfolioQueryService(market)


@router.get("", response_model=PortfolioPage)
async def list_portfolios(
    tenant_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PortfolioPage:
    items = await PortfolioService().list(session, actor, tenant_id, offset=offset, limit=limit)
    PORTFOLIO_REQUESTS.labels(operation="list", outcome="success").inc()
    return PortfolioPage(items=items, offset=offset, limit=limit)


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    data: PortfolioCreate,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> PortfolioResponse:
    result = await PortfolioService().create(session, actor, data, request_id(request))
    PORTFOLIO_REQUESTS.labels(operation="create", outcome="success").inc()
    return result


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> PortfolioResponse:
    return await PortfolioService().get(session, actor, portfolio_id)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    data: PortfolioUpdate,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> PortfolioResponse:
    return await PortfolioService().update(session, actor, portfolio_id, data, request_id(request))


@router.post("/{portfolio_id}/archive", response_model=PortfolioResponse)
async def archive_portfolio(
    portfolio_id: UUID,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> PortfolioResponse:
    return await PortfolioService().archive(session, actor, portfolio_id, request_id(request))


@router.get(
    "/{portfolio_id}/effective-permissions",
    response_model=EffectivePortfolioPermissions,
)
async def effective_permissions(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
) -> EffectivePortfolioPermissions:
    authorisation = PortfolioAuthorisation()
    portfolio = await authorisation.portfolio(
        session,
        actor,
        portfolio_id,
        permission=Permission.PORTFOLIO_READ,
    )
    return await authorisation.effective_permissions(session, actor, portfolio)


@router.get("/{portfolio_id}/transactions", response_model=TransactionPage)
async def list_transactions(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TransactionPage:
    items = await PortfolioQueryService().transactions_list(
        session, actor, portfolio_id, offset=offset, limit=limit
    )
    return TransactionPage(items=items, offset=offset, limit=limit)


@router.post(
    "/{portfolio_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_transaction(
    portfolio_id: UUID,
    data: TransactionCreate,
    idempotency_key: IdempotencyHeader,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> TransactionResponse:
    return await TransactionPostingService().post(
        session,
        actor,
        portfolio_id,
        data,
        idempotency_key,
        request_id(request),
    )


@router.get(
    "/{portfolio_id}/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction(
    portfolio_id: UUID,
    transaction_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
) -> TransactionResponse:
    return await PortfolioQueryService().transaction(session, actor, portfolio_id, transaction_id)


@router.post(
    "/{portfolio_id}/transactions/{transaction_id}/reverse",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reverse_transaction(
    portfolio_id: UUID,
    transaction_id: UUID,
    data: ReversalCreate,
    idempotency_key: IdempotencyHeader,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> TransactionResponse:
    return await TransactionPostingService().reverse(
        session,
        actor,
        portfolio_id,
        transaction_id,
        data,
        idempotency_key,
        request_id(request),
    )


@router.get("/{portfolio_id}/holdings", response_model=list[HoldingResponse])
async def get_holdings(
    portfolio_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> list[HoldingResponse]:
    return await PortfolioQueryService().holdings(session, actor, portfolio_id)


@router.get("/{portfolio_id}/valuation", response_model=ValuationResponse)
async def get_valuation(
    portfolio_id: UUID,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> ValuationResponse:
    return await query_service(request).valuation(session, actor, portfolio_id)


@router.post(
    "/{portfolio_id}/valuation-snapshots",
    response_model=ValuationSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_valuation_snapshot(
    portfolio_id: UUID,
    idempotency_key: IdempotencyHeader,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> ValuationSnapshotResponse:
    return await query_service(request).create_snapshot(
        session,
        actor,
        portfolio_id,
        idempotency_key,
        request_id(request),
    )


@router.get(
    "/{portfolio_id}/valuation-snapshots",
    response_model=list[ValuationSnapshotResponse],
)
async def list_valuation_snapshots(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ValuationSnapshotResponse]:
    return await PortfolioQueryService().snapshot_list(
        session, actor, portfolio_id, offset=offset, limit=limit
    )


@router.get(
    "/{portfolio_id}/valuation-snapshots/{snapshot_id}",
    response_model=ValuationSnapshotResponse,
)
async def get_valuation_snapshot(
    portfolio_id: UUID,
    snapshot_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
) -> ValuationSnapshotResponse:
    return await PortfolioQueryService().snapshot(session, actor, portfolio_id, snapshot_id)


@router.get("/{portfolio_id}/analytics", response_model=AnalyticsResponse)
@router.get("/{portfolio_id}/analytics/allocation", response_model=AnalyticsResponse)
async def get_analytics(
    portfolio_id: UUID,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> AnalyticsResponse:
    return await query_service(request).analytics(session, actor, portfolio_id)


@router.get("/{portfolio_id}/analytics/history", response_model=HistoryResponse)
async def get_history(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    start: datetime | None = None,
    end: datetime | None = None,
) -> HistoryResponse:
    return await PortfolioQueryService().history(session, actor, portfolio_id, start, end)


@router.get(
    "/{portfolio_id}/analytics/drawdown",
    response_model=StatisticalAnalytics,
)
async def get_drawdown(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    start: datetime | None = None,
    end: datetime | None = None,
) -> StatisticalAnalytics:
    return await PortfolioQueryService().statistic(
        session, actor, portfolio_id, "maximum_drawdown", start, end
    )


@router.get(
    "/{portfolio_id}/analytics/volatility",
    response_model=StatisticalAnalytics,
)
async def get_volatility(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    start: datetime | None = None,
    end: datetime | None = None,
) -> StatisticalAnalytics:
    return await PortfolioQueryService().statistic(
        session, actor, portfolio_id, "volatility", start, end
    )


@router.get(
    "/{portfolio_id}/analytics/benchmark",
    response_model=BenchmarkAnalytics,
)
async def get_benchmark(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    start: datetime | None = None,
    end: datetime | None = None,
) -> BenchmarkAnalytics:
    return await PortfolioQueryService().benchmark(session, actor, portfolio_id, start, end)


@router.get(
    "/{portfolio_id}/audit-events",
    response_model=list[AuditEventResponse],
)
async def get_audit_events(
    portfolio_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AuditEventResponse]:
    return await PortfolioQueryService().audit_events(
        session, actor, portfolio_id, offset=offset, limit=limit
    )
