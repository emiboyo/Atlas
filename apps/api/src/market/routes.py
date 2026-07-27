from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from apps.api.src.core.config import get_settings
from apps.api.src.core.dependencies import DatabaseSession
from apps.api.src.identity.authorization import Permission
from apps.api.src.identity.dependencies import ActiveUser
from apps.api.src.market.cache import MarketCache
from apps.api.src.market.repositories import WatchlistRepository
from apps.api.src.market.schemas import (
    CandleResult,
    EffectiveWatchlistPermissions,
    ExchangeResponse,
    InstrumentDetail,
    ListingSummary,
    MarketPage,
    MarketStatusResponse,
    QuoteResult,
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistReorder,
    WatchlistResponse,
    WatchlistUpdate,
)
from apps.api.src.market.services import MarketService, WatchlistService
from packages.database.atlas_database.models.enums import CandleInterval
from packages.database.atlas_database.models.instruments import Watchlist

router = APIRouter()


def request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def market_service(request: Request) -> MarketService:
    redis = getattr(request.app.state, "redis", None)
    return MarketService(get_settings(), MarketCache(redis) if redis is not None else None)


def watchlist_response(watchlist: Watchlist, *, include_items: bool = True) -> WatchlistResponse:
    return WatchlistResponse(
        id=watchlist.id,
        tenant_id=watchlist.tenant_id,
        name=watchlist.name,
        description=watchlist.description,
        visibility=watchlist.visibility,
        status=watchlist.status,
        created_by_user_id=watchlist.created_by_user_id,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
        items=(
            [
                WatchlistItemResponse.model_validate(item)
                for item in sorted(watchlist.items, key=lambda item: (item.position, item.id))
            ]
            if include_items
            else []
        ),
    )


@router.get("/market/exchanges", response_model=list[ExchangeResponse], tags=["Market reference"])
async def list_exchanges(
    request: Request,
    session: DatabaseSession,
    _user: ActiveUser,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[ExchangeResponse]:
    rows = await market_service(request).repository.exchanges(
        session, offset=(page - 1) * page_size, limit=page_size
    )
    return [ExchangeResponse.model_validate(exchange) for exchange in rows]


@router.get("/market/instruments/search", response_model=MarketPage, tags=["Market reference"])
async def search_instruments(
    request: Request,
    session: DatabaseSession,
    _user: ActiveUser,
    q: Annotated[str, Query(min_length=2, max_length=100)],
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> MarketPage:
    return await market_service(request).search(session, q, page=page, page_size=page_size)


@router.get(
    "/market/instruments/{instrument_id}",
    response_model=InstrumentDetail,
    tags=["Market reference"],
)
async def get_instrument(
    instrument_id: UUID, request: Request, session: DatabaseSession, _user: ActiveUser
) -> InstrumentDetail:
    return await market_service(request).instrument_detail(session, instrument_id)


@router.get(
    "/market/listings/{listing_id}",
    response_model=ListingSummary,
    tags=["Market reference"],
)
async def get_listing(
    listing_id: UUID, request: Request, session: DatabaseSession, _user: ActiveUser
) -> ListingSummary:
    service = market_service(request)
    listing = await service.repository.listing(session, listing_id)
    if listing is None:
        from apps.api.src.market.services import market_not_found

        raise market_not_found()
    return service.listing_summary(listing)


@router.get(
    "/market/listings/{listing_id}/quote",
    response_model=QuoteResult,
    tags=["Market data"],
)
async def get_quote(
    listing_id: UUID, request: Request, session: DatabaseSession, _user: ActiveUser
) -> QuoteResult:
    return await market_service(request).quote(session, listing_id)


@router.get(
    "/market/listings/{listing_id}/candles",
    response_model=CandleResult,
    tags=["Market data"],
)
async def get_candles(
    listing_id: UUID,
    request: Request,
    session: DatabaseSession,
    _user: ActiveUser,
    interval: CandleInterval,
    start: datetime,
    end: datetime,
) -> CandleResult:
    return await market_service(request).candles(session, listing_id, interval, start, end)


@router.get("/market/status", response_model=MarketStatusResponse, tags=["Market data"])
async def get_market_status(request: Request, _user: ActiveUser) -> MarketStatusResponse:
    return await market_service(request).status()


@router.get("/watchlists", response_model=list[WatchlistResponse], tags=["Watchlists"])
async def list_watchlists(
    tenant_id: UUID,
    session: DatabaseSession,
    user: ActiveUser,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[WatchlistResponse]:
    service = WatchlistService(get_settings())
    await service._authorise(session, user, tenant_id, Permission.WATCHLIST_READ)
    rows = await WatchlistRepository().list(
        session, tenant_id, offset=(page - 1) * page_size, limit=page_size
    )
    return [watchlist_response(item) for item in rows]


@router.get(
    "/watchlists/effective-permissions",
    response_model=EffectiveWatchlistPermissions,
    tags=["Watchlists"],
)
async def get_effective_watchlist_permissions(
    tenant_id: UUID,
    session: DatabaseSession,
    user: ActiveUser,
) -> EffectiveWatchlistPermissions:
    return await WatchlistService(get_settings()).effective_permissions(session, user, tenant_id)


@router.post(
    "/watchlists",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Watchlists"],
)
async def create_watchlist(
    data: WatchlistCreate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> WatchlistResponse:
    watchlist = await WatchlistService(get_settings()).create(
        session, user, data, request_id(request)
    )
    return watchlist_response(watchlist, include_items=False)


@router.get(
    "/watchlists/{watchlist_id}",
    response_model=WatchlistResponse,
    tags=["Watchlists"],
)
async def get_watchlist(
    watchlist_id: UUID, session: DatabaseSession, user: ActiveUser
) -> WatchlistResponse:
    watchlist = await WatchlistService(get_settings()).require(
        session, user, watchlist_id, Permission.WATCHLIST_READ
    )
    return watchlist_response(watchlist)


@router.patch(
    "/watchlists/{watchlist_id}",
    response_model=WatchlistResponse,
    tags=["Watchlists"],
)
async def update_watchlist(
    watchlist_id: UUID,
    data: WatchlistUpdate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> WatchlistResponse:
    watchlist = await WatchlistService(get_settings()).update(
        session, user, watchlist_id, data, request_id(request)
    )
    return WatchlistResponse.model_validate(watchlist)


@router.delete(
    "/watchlists/{watchlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Watchlists"],
)
async def archive_watchlist(
    watchlist_id: UUID,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> Response:
    await WatchlistService(get_settings()).archive(session, user, watchlist_id, request_id(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/watchlists/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Watchlists"],
)
async def add_watchlist_item(
    watchlist_id: UUID,
    data: WatchlistItemCreate,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> WatchlistItemResponse:
    item = await WatchlistService(get_settings()).add_item(
        session, user, watchlist_id, data, request_id(request)
    )
    return WatchlistItemResponse.model_validate(item)


@router.delete(
    "/watchlists/{watchlist_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Watchlists"],
)
async def remove_watchlist_item(
    watchlist_id: UUID,
    item_id: UUID,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> Response:
    await WatchlistService(get_settings()).remove_item(
        session, user, watchlist_id, item_id, request_id(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/watchlists/{watchlist_id}/items/reorder",
    response_model=WatchlistResponse,
    tags=["Watchlists"],
)
async def reorder_watchlist_items(
    watchlist_id: UUID,
    data: WatchlistReorder,
    request: Request,
    session: DatabaseSession,
    user: ActiveUser,
) -> WatchlistResponse:
    watchlist = await WatchlistService(get_settings()).reorder(
        session, user, watchlist_id, data, request_id(request)
    )
    return watchlist_response(watchlist)
