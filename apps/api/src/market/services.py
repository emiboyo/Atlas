from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.identity.services import OrganisationService
from apps.api.src.market.cache import MarketCache
from apps.api.src.market.metrics import (
    CACHE_OPERATIONS,
    MARKET_REQUESTS,
    PROVIDER_ERRORS,
    PROVIDER_LATENCY,
    STALE_RESPONSES,
)
from apps.api.src.market.providers import (
    NON_ADVISORY_DISCLAIMER,
    SIMULATED_SOURCE,
    DeterministicFixtureProvider,
    DisabledExternalProvider,
    MarketDataProvider,
)
from apps.api.src.market.repositories import MarketRepository, WatchlistRepository
from apps.api.src.market.schemas import (
    CandleResult,
    InstrumentDetail,
    InstrumentSearchResult,
    ListingSummary,
    MarketPage,
    MarketStatusResponse,
    QuoteResult,
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistReorder,
    WatchlistUpdate,
)
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MarketDataStatus,
    WatchlistStatus,
)
from packages.database.atlas_database.models.identity import User
from packages.database.atlas_database.models.instruments import (
    InstrumentListing,
    Watchlist,
    WatchlistItem,
)


def market_not_found() -> ApplicationError:
    return ApplicationError(
        "The requested market resource was not found.",
        code="market_resource_not_found",
        status_code=status.HTTP_404_NOT_FOUND,
    )


class MarketService:
    def __init__(self, settings: Settings, cache: MarketCache | None = None) -> None:
        self.settings = settings
        self.cache = cache
        self.repository = MarketRepository()
        self.provider: MarketDataProvider = (
            DeterministicFixtureProvider()
            if settings.market_data_provider == "simulated"
            else DisabledExternalProvider()
        )

    def listing_summary(self, listing: InstrumentListing) -> ListingSummary:
        return ListingSummary(
            id=listing.id,
            instrument_id=listing.instrument_id,
            symbol=listing.ticker,
            exchange=listing.exchange,
            currency=listing.quote_currency,
            status=listing.listing_status,
            is_primary=listing.is_primary,
            data_availability=(
                MarketDataStatus.SIMULATED
                if self.settings.market_data_provider == "simulated"
                else MarketDataStatus.UNAVAILABLE
            ),
        )

    async def search(
        self, session: AsyncSession, query: str, *, page: int, page_size: int
    ) -> MarketPage:
        normalized = " ".join(query.split())
        if len(normalized) < 2 or len(normalized) > 100:
            raise ApplicationError(
                "Search queries must contain between 2 and 100 characters.",
                code="invalid_search_query",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        limit = min(page_size, self.settings.market_max_search_results)
        cache_key = MarketCache.key("search", normalized.lower(), page, limit)
        if self.cache:
            cached = await self.cache.get_model(cache_key, MarketPage)
            if cached is not None:
                CACHE_OPERATIONS.labels(operation="search", result="hit").inc()
                return cached
            CACHE_OPERATIONS.labels(operation="search", result="miss").inc()
        rows = await self.repository.search(
            session, normalized, offset=(page - 1) * limit, limit=limit
        )
        items = [
            InstrumentSearchResult(
                instrument_id=instrument.id,
                canonical_name=instrument.name,
                short_name=instrument.short_name,
                asset_class=instrument.asset_class,
                status=instrument.status,
                listing=self.listing_summary(listing),
            )
            for instrument, listing, _exchange in rows
        ]
        result = MarketPage(
            items=items,
            page=page,
            page_size=limit,
            total=await self.repository.search_count(session, normalized),
        )
        if self.cache:
            await self.cache.set_json(
                cache_key,
                result.model_dump(mode="json"),
                self.settings.market_search_cache_ttl_seconds,
            )
        MARKET_REQUESTS.labels(operation="search", outcome="success").inc()
        return result

    async def instrument_detail(
        self, session: AsyncSession, instrument_id: UUID
    ) -> InstrumentDetail:
        cache_key = MarketCache.key("instrument", instrument_id)
        if self.cache:
            cached = await self.cache.get_model(cache_key, InstrumentDetail)
            if cached is not None:
                CACHE_OPERATIONS.labels(operation="instrument", result="hit").inc()
                return cached
            CACHE_OPERATIONS.labels(operation="instrument", result="miss").inc()
        instrument = await self.repository.instrument(session, instrument_id)
        if instrument is None:
            raise market_not_found()
        result = InstrumentDetail(
            id=instrument.id,
            canonical_name=instrument.name,
            short_name=instrument.short_name,
            description=instrument.description,
            asset_class=instrument.asset_class,
            primary_currency=instrument.base_currency,
            country_code=instrument.country_code,
            isin=instrument.isin,
            cusip=instrument.cusip,
            sedol=instrument.sedol,
            status=instrument.status,
            listings=[self.listing_summary(listing) for listing in instrument.listings],
        )
        if self.cache:
            await self.cache.set_json(
                cache_key,
                result.model_dump(mode="json"),
                self.settings.market_detail_cache_ttl_seconds,
            )
        return result

    async def quote(self, session: AsyncSession, listing_id: UUID) -> QuoteResult:
        listing = await self.repository.listing(session, listing_id)
        if listing is None:
            raise market_not_found()
        cache_key = MarketCache.key("quote", self.provider.name, listing_id)
        if self.cache:
            cached = await self.cache.get_model(cache_key, QuoteResult)
            if cached is not None:
                CACHE_OPERATIONS.labels(operation="quote", result="hit").inc()
                return cached
            CACHE_OPERATIONS.labels(operation="quote", result="miss").inc()
        started = perf_counter()
        try:
            quote = await self.provider.get_latest_quote(listing_id)
        except ApplicationError as exc:
            PROVIDER_ERRORS.labels(provider=self.provider.name, code=exc.code).inc()
            raise
        finally:
            PROVIDER_LATENCY.labels(provider=self.provider.name, operation="quote").observe(
                perf_counter() - started
            )
        if quote.price is not None and quote.price < 0:
            raise ApplicationError(
                "The provider response failed validation.",
                code="malformed_provider_response",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )
        stale_after = quote.provider_timestamp + timedelta(
            seconds=self.settings.market_quote_cache_ttl_seconds
        )
        is_stale = quote.status != MarketDataStatus.SIMULATED and datetime.now(UTC) > stale_after
        data_status = MarketDataStatus.STALE if is_stale else quote.status
        if is_stale:
            STALE_RESPONSES.labels(provider=self.provider.name).inc()
        result = QuoteResult(
            listing_id=listing.id,
            instrument_id=listing.instrument_id,
            symbol=listing.ticker,
            exchange=listing.exchange.mic,
            currency=listing.quote_currency,
            price=quote.price,
            open=quote.open,
            high=quote.high,
            low=quote.low,
            previous_close=quote.previous_close,
            volume=quote.volume,
            provider=quote.provider,
            provider_timestamp=quote.provider_timestamp,
            received_at=quote.received_at,
            data_status=data_status,
            is_stale=is_stale,
            stale_after=stale_after,
            source_label=SIMULATED_SOURCE,
            market_session=quote.session.value,
            disclaimer=NON_ADVISORY_DISCLAIMER,
        )
        if self.cache:
            await self.cache.set_json(
                cache_key,
                result.model_dump(mode="json"),
                self.settings.market_quote_cache_ttl_seconds,
            )
        return result

    async def candles(
        self,
        session: AsyncSession,
        listing_id: UUID,
        interval: CandleInterval,
        start: datetime,
        end: datetime,
    ) -> CandleResult:
        listing = await self.repository.listing(session, listing_id)
        if listing is None:
            raise market_not_found()
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ApplicationError(
                "A valid timezone-aware candle range is required.",
                code="invalid_candle_range",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if end - start > timedelta(days=self.settings.market_max_candle_days):
            raise ApplicationError(
                "The requested candle range is too large.",
                code="candle_range_too_large",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        cache_key = MarketCache.key(
            "candles",
            self.provider.name,
            listing_id,
            interval.value,
            start.isoformat(),
            end.isoformat(),
        )
        if self.cache:
            cached = await self.cache.get_model(cache_key, CandleResult)
            if cached is not None:
                CACHE_OPERATIONS.labels(operation="candles", result="hit").inc()
                return cached
            CACHE_OPERATIONS.labels(operation="candles", result="miss").inc()
        started = perf_counter()
        try:
            candles = await self.provider.get_historical_candles(
                listing_id, interval, start.astimezone(UTC), end.astimezone(UTC)
            )
        except ApplicationError as exc:
            PROVIDER_ERRORS.labels(provider=self.provider.name, code=exc.code).inc()
            raise
        finally:
            PROVIDER_LATENCY.labels(provider=self.provider.name, operation="candles").observe(
                perf_counter() - started
            )
        result = CandleResult(
            listing_id=listing_id,
            interval=interval,
            requested_start=start,
            requested_end=end,
            returned_start=candles[0].period_start if candles else None,
            returned_end=candles[-1].period_end if candles else None,
            provider=self.provider.name,
            currency=listing.quote_currency,
            data_status=MarketDataStatus.SIMULATED,
            candles=candles,
            disclaimer=NON_ADVISORY_DISCLAIMER,
        )
        if self.cache:
            await self.cache.set_json(
                cache_key,
                result.model_dump(mode="json"),
                self.settings.market_candle_cache_ttl_seconds,
            )
        return result

    async def status(self) -> MarketStatusResponse:
        healthy = await self.provider.health_check()
        return MarketStatusResponse(
            provider=self.provider.name,
            status="available" if healthy else "unavailable",
            data_status=(MarketDataStatus.SIMULATED if healthy else MarketDataStatus.UNAVAILABLE),
            source_label=SIMULATED_SOURCE if healthy else "External provider disabled",
            disclaimer=NON_ADVISORY_DISCLAIMER,
        )


class WatchlistService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = WatchlistRepository()
        self.organisations = OrganisationService()
        self.authorisation = AuthorisationService()

    async def _authorise(
        self,
        session: AsyncSession,
        actor: User,
        tenant_id: UUID,
        permission: Permission,
    ) -> None:
        _organisation, membership = await self.organisations.require_membership(
            session, tenant_id, actor.id
        )
        self.authorisation.require_permission(membership.role, permission)

    async def require(
        self,
        session: AsyncSession,
        actor: User,
        watchlist_id: UUID,
        permission: Permission,
    ) -> Watchlist:
        watchlist = await self.repository.by_id(session, watchlist_id)
        if watchlist is None:
            raise market_not_found()
        try:
            await self._authorise(session, actor, watchlist.tenant_id, permission)
        except ApplicationError as exc:
            if exc.status_code in {403, 404}:
                raise market_not_found() from exc
            raise
        return watchlist

    async def create(
        self,
        session: AsyncSession,
        actor: User,
        data: WatchlistCreate,
        request_id: str | None,
    ) -> Watchlist:
        await self._authorise(session, actor, data.tenant_id, Permission.WATCHLIST_CREATE)
        if (
            await self.repository.count(session, data.tenant_id)
            >= self.settings.watchlist_max_per_tenant
        ):
            raise ApplicationError(
                "The development watchlist limit has been reached.",
                code="watchlist_limit_reached",
                status_code=status.HTTP_409_CONFLICT,
            )
        watchlist = Watchlist(
            tenant_id=data.tenant_id,
            name=data.name.strip(),
            description=data.description,
            visibility=data.visibility,
            created_by_user_id=actor.id,
        )
        session.add(watchlist)
        await session.flush()
        self.organisations.identity._audit(
            session,
            event_type="watchlist.created",
            actor_user_id=actor.id,
            tenant_id=data.tenant_id,
            target_type="watchlist",
            target_id=watchlist.id,
            request_id=request_id,
        )
        await self._commit(session, "watchlist_conflict")
        await session.refresh(watchlist)
        return watchlist

    async def update(
        self,
        session: AsyncSession,
        actor: User,
        watchlist_id: UUID,
        data: WatchlistUpdate,
        request_id: str | None,
    ) -> Watchlist:
        watchlist = await self.require(session, actor, watchlist_id, Permission.WATCHLIST_UPDATE)
        self._require_active(watchlist)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(watchlist, field, value.strip() if isinstance(value, str) else value)
        self._audit(session, actor, watchlist, "watchlist.updated", request_id)
        await self._commit(session, "watchlist_conflict")
        await session.refresh(watchlist)
        return watchlist

    async def archive(
        self,
        session: AsyncSession,
        actor: User,
        watchlist_id: UUID,
        request_id: str | None,
    ) -> None:
        watchlist = await self.require(session, actor, watchlist_id, Permission.WATCHLIST_DELETE)
        watchlist.status = WatchlistStatus.ARCHIVED
        self._audit(session, actor, watchlist, "watchlist.archived", request_id)
        await session.commit()

    async def add_item(
        self,
        session: AsyncSession,
        actor: User,
        watchlist_id: UUID,
        data: WatchlistItemCreate,
        request_id: str | None,
    ) -> WatchlistItem:
        watchlist = await self.require(session, actor, watchlist_id, Permission.WATCHLIST_ITEM_ADD)
        self._require_active(watchlist)
        if await MarketRepository().listing(session, data.listing_id) is None:
            raise market_not_found()
        position = await self.repository.item_count(session, watchlist.id)
        if position >= self.settings.watchlist_max_items:
            raise ApplicationError(
                "The development watchlist item limit has been reached.",
                code="watchlist_item_limit_reached",
                status_code=status.HTTP_409_CONFLICT,
            )
        item = WatchlistItem(
            id=uuid4(),
            watchlist_id=watchlist.id,
            listing_id=data.listing_id,
            position=position,
            notes=data.notes,
            added_by_user_id=actor.id,
        )
        session.add(item)
        self._audit(session, actor, watchlist, "watchlist.item_added", request_id, item.id)
        await self._commit(session, "watchlist_item_conflict")
        return item

    async def remove_item(
        self,
        session: AsyncSession,
        actor: User,
        watchlist_id: UUID,
        item_id: UUID,
        request_id: str | None,
    ) -> None:
        watchlist = await self.require(
            session, actor, watchlist_id, Permission.WATCHLIST_ITEM_REMOVE
        )
        self._require_active(watchlist)
        item = await self.repository.item(session, watchlist.id, item_id)
        if item is None:
            raise market_not_found()
        await session.delete(item)
        self._audit(session, actor, watchlist, "watchlist.item_removed", request_id, item.id)
        await session.commit()

    async def reorder(
        self,
        session: AsyncSession,
        actor: User,
        watchlist_id: UUID,
        data: WatchlistReorder,
        request_id: str | None,
    ) -> Watchlist:
        watchlist = await self.require(session, actor, watchlist_id, Permission.WATCHLIST_UPDATE)
        self._require_active(watchlist)
        existing = {item.id: item for item in watchlist.items}
        if set(data.item_ids) != set(existing):
            raise ApplicationError(
                "The reorder request must contain every current item exactly once.",
                code="invalid_watchlist_order",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        # Use temporary negative positions to avoid violating the unique constraint mid-flush.
        for offset, item_id in enumerate(data.item_ids, start=1):
            existing[item_id].position = -offset
        await session.flush()
        for position, item_id in enumerate(data.item_ids):
            existing[item_id].position = position
        self._audit(session, actor, watchlist, "watchlist.reordered", request_id)
        await session.commit()
        await session.refresh(watchlist, attribute_names=["items"])
        return watchlist

    @staticmethod
    def _require_active(watchlist: Watchlist) -> None:
        if watchlist.status != WatchlistStatus.ACTIVE:
            raise ApplicationError(
                "Archived watchlists cannot be modified.",
                code="watchlist_archived",
                status_code=status.HTTP_409_CONFLICT,
            )

    def _audit(
        self,
        session: AsyncSession,
        actor: User,
        watchlist: Watchlist,
        event_type: str,
        request_id: str | None,
        target_id: UUID | None = None,
    ) -> None:
        self.organisations.identity._audit(
            session,
            event_type=event_type,
            actor_user_id=actor.id,
            tenant_id=watchlist.tenant_id,
            target_type="watchlist_item" if target_id else "watchlist",
            target_id=target_id or watchlist.id,
            request_id=request_id,
        )

    @staticmethod
    async def _commit(session: AsyncSession, code: str) -> None:
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise ApplicationError(
                "The requested watchlist change conflicts with existing data.",
                code=code,
                status_code=status.HTTP_409_CONFLICT,
            ) from exc
