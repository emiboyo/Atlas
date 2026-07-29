from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, status

from apps.api.src.core.dependencies import DatabaseSession
from apps.api.src.identity.authorization import Permission
from apps.api.src.identity.dependencies import ActiveUser
from apps.api.src.research.schemas import (
    AuditEventResponse,
    BacktestCreate,
    ComparisonCreate,
    ComparisonResponse,
    DataQualityResponse,
    EffectivePermissions,
    EquityResponse,
    EventResponse,
    ExplanationCreate,
    ExplanationResponse,
    IdempotencyKey,
    ResultResponse,
    RunResponse,
    StrategyCreate,
    StrategyPage,
    StrategyResponse,
    StrategyUpdate,
    VersionCreate,
    VersionResponse,
)
from apps.api.src.research.services import ResearchService

router = APIRouter(prefix="/research", tags=["Historical strategy research"])
Idempotency = Annotated[IdempotencyKey, Header(alias="Idempotency-Key")]


def request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.get("/strategies", response_model=StrategyPage)
async def list_strategies(
    session: DatabaseSession,
    actor: ActiveUser,
    tenant_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> StrategyPage:
    items = await ResearchService().list_strategies(session, actor, tenant_id, offset, limit)
    return StrategyPage(items=items, offset=offset, limit=limit)


@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    data: StrategyCreate, request: Request, session: DatabaseSession, actor: ActiveUser
) -> StrategyResponse:
    return await ResearchService().create_strategy(session, actor, data, request_id(request))


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> StrategyResponse:
    return await ResearchService().get_strategy(session, actor, strategy_id)


@router.patch("/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    data: StrategyUpdate,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> StrategyResponse:
    return await ResearchService().update_strategy(
        session, actor, strategy_id, data, request_id(request)
    )


@router.post("/strategies/{strategy_id}/archive", response_model=StrategyResponse)
async def archive_strategy(
    strategy_id: UUID, request: Request, session: DatabaseSession, actor: ActiveUser
) -> StrategyResponse:
    return await ResearchService().archive_strategy(
        session, actor, strategy_id, request_id(request)
    )


@router.get(
    "/strategies/{strategy_id}/effective-permissions",
    response_model=EffectivePermissions,
)
async def effective_permissions(
    strategy_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> EffectivePermissions:
    return await ResearchService().permissions(session, actor, strategy_id)


@router.get("/strategies/{strategy_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    strategy_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> list[VersionResponse]:
    return await ResearchService().versions(session, actor, strategy_id)


@router.post(
    "/strategies/{strategy_id}/versions",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    strategy_id: UUID,
    data: VersionCreate,
    idempotency_key: Idempotency,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> VersionResponse:
    return await ResearchService().create_version(
        session, actor, strategy_id, data, idempotency_key, request_id(request)
    )


@router.get(
    "/strategies/{strategy_id}/versions/{version_id}",
    response_model=VersionResponse,
)
async def get_version(
    strategy_id: UUID,
    version_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
) -> VersionResponse:
    await ResearchService().auth.strategy(session, actor, strategy_id, Permission.STRATEGY_READ)
    value = await ResearchService().repo.version(session, strategy_id, version_id)
    if value is None:
        from apps.api.src.research.services import error

        raise error("strategy_version_not_found", "The strategy version was not found.", 404)
    from apps.api.src.research.services import version_response

    return version_response(value)


@router.get("/backtests", response_model=list[RunResponse])
async def list_backtests(
    session: DatabaseSession,
    actor: ActiveUser,
    tenant_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[RunResponse]:
    return await ResearchService().list_runs(session, actor, tenant_id, offset, limit)


@router.post("/backtests", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    data: BacktestCreate,
    idempotency_key: Idempotency,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> RunResponse:
    return await ResearchService().create_run(
        session, actor, data, idempotency_key, request_id(request)
    )


@router.post("/backtests/compare", response_model=ComparisonResponse)
async def compare_backtests(
    data: ComparisonCreate,
    session: DatabaseSession,
    actor: ActiveUser,
) -> ComparisonResponse:
    return await ResearchService().compare(session, actor, data.run_ids)


@router.get("/backtests/{run_id}", response_model=RunResponse)
async def get_backtest(run_id: UUID, session: DatabaseSession, actor: ActiveUser) -> RunResponse:
    return await ResearchService().get_run(session, actor, run_id)


@router.get("/backtests/{run_id}/events", response_model=list[EventResponse])
async def events(run_id: UUID, session: DatabaseSession, actor: ActiveUser) -> list[EventResponse]:
    return await ResearchService().events(session, actor, run_id)


@router.get("/backtests/{run_id}/equity", response_model=list[EquityResponse])
async def equity(run_id: UUID, session: DatabaseSession, actor: ActiveUser) -> list[EquityResponse]:
    return await ResearchService().equity(session, actor, run_id)


@router.get("/backtests/{run_id}/result", response_model=ResultResponse)
async def result(run_id: UUID, session: DatabaseSession, actor: ActiveUser) -> ResultResponse:
    return await ResearchService().result(session, actor, run_id)


@router.get("/backtests/{run_id}/data-quality", response_model=DataQualityResponse)
async def data_quality(
    run_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> DataQualityResponse:
    return await ResearchService().data_quality(session, actor, run_id)


@router.get("/strategies/{strategy_id}/audit-events", response_model=list[AuditEventResponse])
async def audit_events(
    strategy_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
    run_id: UUID | None = None,
) -> list[AuditEventResponse]:
    return await ResearchService().audits(session, actor, strategy_id, run_id)


@router.get("/backtests/{run_id}/audit-events", response_model=list[AuditEventResponse])
async def backtest_audit_events(
    run_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> list[AuditEventResponse]:
    run, _strategy = await ResearchService().auth.run(
        session, actor, run_id, Permission.BACKTEST_AUDIT_READ
    )
    return await ResearchService().audits(session, actor, run.strategy_id, run.id)


@router.post(
    "/backtests/{run_id}/explanations",
    response_model=ExplanationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def explain(
    run_id: UUID,
    data: ExplanationCreate,
    idempotency_key: Idempotency,
    request: Request,
    session: DatabaseSession,
    actor: ActiveUser,
) -> ExplanationResponse:
    return await ResearchService().explain(
        session, actor, run_id, data, idempotency_key, request_id(request)
    )


@router.get("/backtests/{run_id}/explanations", response_model=list[ExplanationResponse])
async def explanations(
    run_id: UUID, session: DatabaseSession, actor: ActiveUser
) -> list[ExplanationResponse]:
    return await ResearchService().explanations(session, actor, run_id)


@router.get(
    "/backtests/{run_id}/explanations/{explanation_id}",
    response_model=ExplanationResponse,
)
async def explanation(
    run_id: UUID,
    explanation_id: UUID,
    session: DatabaseSession,
    actor: ActiveUser,
) -> ExplanationResponse:
    return await ResearchService().explanation(session, actor, run_id, explanation_id)
