from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.api.src.core.config import Settings
from apps.api.src.core.errors import ApplicationError
from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.market.cache import MarketCache
from apps.api.src.market.providers import (
    DeterministicFixtureProvider,
    DisabledExternalProvider,
    ProviderError,
    ProviderQuote,
)
from apps.api.src.market.schemas import (
    CandlePoint,
    WatchlistCreate,
    WatchlistReorder,
)
from apps.api.src.market.services import MarketService
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MarketDataStatus,
    MembershipRole,
)


async def test_deterministic_provider_is_simulated_and_repeatable() -> None:
    provider = DeterministicFixtureProvider()
    listing_id = uuid4()

    first = await provider.get_latest_quote(listing_id)
    second = await provider.get_latest_quote(listing_id)

    assert first.price == second.price
    assert first.provider_timestamp == datetime(2026, 1, 15, 16, tzinfo=UTC)
    assert first.status == MarketDataStatus.SIMULATED
    assert "simulated" in provider.name


async def test_provider_rejects_unsupported_interval_and_disabled_boundary() -> None:
    provider = DeterministicFixtureProvider()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ProviderError) as error:
        await provider.get_historical_candles(
            uuid4(), CandleInterval.ONE_MINUTE, start, start + timedelta(days=1)
        )
    assert error.value.code == "unsupported_interval"

    with pytest.raises(ProviderError) as error:
        await DisabledExternalProvider().get_latest_quote(uuid4())
    assert error.value.code == "provider_unavailable"

    with pytest.raises(ProviderError) as error:
        await DisabledExternalProvider().get_historical_candles(
            uuid4(), CandleInterval.ONE_DAY, start, start + timedelta(days=1)
        )
    assert error.value.code == "provider_unavailable"
    assert await provider.health_check() is True
    assert await DisabledExternalProvider().health_check() is False


def test_provider_rejects_negative_price_seed() -> None:
    with pytest.raises(ProviderError) as error:
        ProviderQuote(uuid4(), -1)
    assert error.value.code == "malformed_provider_response"


def test_candle_shape_and_watchlist_mass_assignment_validation() -> None:
    with pytest.raises(ValidationError):
        CandlePoint(
            period_start=datetime(2026, 1, 1, tzinfo=UTC),
            period_end=datetime(2026, 1, 2, tzinfo=UTC),
            open=Decimal("10"),
            high=Decimal("9"),
            low=Decimal("8"),
            close=Decimal("9"),
        )
    with pytest.raises(ValidationError):
        WatchlistCreate.model_validate(
            {
                "tenant_id": str(uuid4()),
                "name": "Safe",
                "created_by_user_id": str(uuid4()),
            }
        )
    duplicate_id = uuid4()
    with pytest.raises(ValidationError):
        WatchlistReorder(item_ids=[duplicate_id, duplicate_id])

    with pytest.raises(ValidationError):
        CandlePoint(
            period_start=datetime(2026, 1, 2, tzinfo=UTC),
            period_end=datetime(2026, 1, 1, tzinfo=UTC),
            open=Decimal("8"),
            high=Decimal("9"),
            low=Decimal("8"),
            close=Decimal("9"),
        )
    with pytest.raises(ValidationError):
        CandlePoint(
            period_start=datetime(2026, 1, 1, tzinfo=UTC),
            period_end=datetime(2026, 1, 2, tzinfo=UTC),
            open=Decimal("7"),
            high=Decimal("9"),
            low=Decimal("8"),
            close=Decimal("9"),
        )
    with pytest.raises(ValidationError):
        CandlePoint(
            period_start=datetime(2026, 1, 1, tzinfo=UTC),
            period_end=datetime(2026, 1, 2, tzinfo=UTC),
            open=Decimal("8"),
            high=Decimal("9"),
            low=Decimal("8"),
            close=Decimal("10"),
        )


def test_watchlist_permissions_are_centralised() -> None:
    service = AuthorisationService()
    assert service.can(MembershipRole.OWNER, Permission.WATCHLIST_DELETE)
    assert service.can(MembershipRole.ADMIN, Permission.WATCHLIST_ITEM_ADD)
    assert service.can(MembershipRole.MEMBER, Permission.WATCHLIST_CREATE)
    assert service.can(MembershipRole.VIEWER, Permission.WATCHLIST_READ)
    assert not service.can(MembershipRole.VIEWER, Permission.WATCHLIST_UPDATE)


class FakeRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.values: dict[str, str] = {}
        self.fail = fail

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int) -> None:
        del ex
        if self.fail:
            raise ConnectionError
        self.values[key] = value


async def test_cache_hit_miss_collision_resistance_and_safe_degradation() -> None:
    redis = FakeRedis()
    cache = MarketCache(redis)  # type: ignore[arg-type]
    first_key = cache.key("quote", "provider-a", uuid4())
    second_key = cache.key("quote", "provider-b", uuid4())
    assert first_key != second_key

    calls = 0

    async def loader() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"status": "simulated"}

    first, first_hit = await cache.remember(first_key, 30, loader)
    second, second_hit = await cache.remember(first_key, 30, loader)
    assert first == second
    assert first_hit is False
    assert second_hit is True
    assert calls == 1

    failing = MarketCache(FakeRedis(fail=True))  # type: ignore[arg-type]
    result, hit = await failing.remember(first_key, 30, loader)
    assert result == {"status": "simulated"}
    assert hit is False


async def test_market_service_status_and_search_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    simulated = MarketService(Settings(_env_file=None))
    simulated_status = await simulated.status()
    assert simulated_status.status == "available"
    assert simulated_status.data_status == MarketDataStatus.SIMULATED

    disabled = MarketService(Settings(market_data_provider="disabled", _env_file=None))
    disabled_status = await disabled.status()
    assert disabled_status.status == "unavailable"
    assert disabled_status.data_status == MarketDataStatus.UNAVAILABLE

    listing = SimpleNamespace(
        id=uuid4(),
        instrument_id=uuid4(),
        ticker="SAFE",
        exchange=SimpleNamespace(
            id=uuid4(),
            mic="XDEV",
            name="Development Exchange",
            acronym="XDEV",
            country_code="GB",
            timezone="Europe/London",
            default_currency="GBP",
            market_type="simulated",
            status="active",
        ),
        quote_currency="GBP",
        listing_status="active",
        is_primary=True,
    )
    assert simulated.listing_summary(listing).symbol == "SAFE"  # type: ignore[arg-type]

    with pytest.raises(ApplicationError) as error:
        await simulated.search(None, "x", page=1, page_size=10)  # type: ignore[arg-type]
    assert error.value.code == "invalid_search_query"

    async def missing_instrument(*_args: object) -> None:
        return None

    monkeypatch.setattr(simulated.repository, "instrument", missing_instrument)
    with pytest.raises(ApplicationError) as error:
        await simulated.instrument_detail(None, uuid4())  # type: ignore[arg-type]
    assert error.value.code == "market_resource_not_found"

    async def existing_listing(*_args: object) -> SimpleNamespace:
        return listing

    monkeypatch.setattr(simulated.repository, "listing", existing_listing)
    with pytest.raises(ApplicationError) as error:
        await simulated.candles(
            None,  # type: ignore[arg-type]
            listing.id,
            CandleInterval.ONE_DAY,
            datetime(2026, 1, 1),
            datetime(2026, 1, 2),
        )
    assert error.value.code == "invalid_candle_range"
