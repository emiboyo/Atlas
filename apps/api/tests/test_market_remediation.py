import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.api.src.core.config import Settings
from apps.api.src.market.cache import MarketCache
from apps.api.src.market.execution import ProviderExecutor
from apps.api.src.market.providers import (
    DeterministicFixtureProvider,
    ProviderCandleBatch,
    ProviderError,
    ProviderListingContext,
    ProviderQuote,
)
from apps.api.src.market.quality import ProviderDataQualityService
from apps.api.src.market.schemas import CandlePoint, QuoteResult
from apps.api.src.market.services import MarketService
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MarketDataStatus,
    MarketSession,
)


def context() -> ProviderListingContext:
    return ProviderListingContext(
        listing_id=uuid4(),
        provider_symbol="SAFE.XDEV",
        provider_venue_code="XDEV",
        currency="GBP",
    )


def quote(
    listing: ProviderListingContext,
    *,
    now: datetime,
    symbol: str | None = None,
    venue: str | None = None,
    currency: str | None = None,
    status: MarketDataStatus = MarketDataStatus.LIVE,
    source_reference: str = "fixture:safe",
) -> ProviderQuote:
    return ProviderQuote(
        listing_id=listing.listing_id,
        provider="fake",
        provider_symbol=symbol or listing.provider_symbol,
        provider_venue_code=venue or listing.provider_venue_code,
        source_reference=source_reference,
        provider_timestamp=now,
        received_at=now,
        currency=currency or listing.currency,
        price=Decimal("1.123456789012345678"),
        status=status,
        session=MarketSession.REGULAR,
    )


async def test_provider_executor_success_timeout_connection_and_no_unsafe_retries() -> None:
    sleeps: list[float] = []

    async def sleep(delay: float) -> None:
        sleeps.append(delay)

    executor = ProviderExecutor(timeout_seconds=0.01, retry_count=1, sleep=sleep)
    assert await executor.execute("fake", "success", lambda: asyncio.sleep(0, result="ok")) == "ok"

    async def timeout() -> None:
        await asyncio.sleep(0.1)

    with pytest.raises(ProviderError) as error:
        await executor.execute("fake", "timeout", timeout)
    assert error.value.code == "provider_timeout"
    assert sleeps == [0.05]

    attempts = 0

    async def connection_failure() -> None:
        nonlocal attempts
        attempts += 1
        raise ConnectionError

    with pytest.raises(ProviderError) as error:
        await executor.execute("fake", "connection", connection_failure)
    assert error.value.code == "provider_unavailable"
    assert attempts == 2

    for code in (
        "provider_authentication_failed",
        "provider_rate_limited",
        "provider_response_invalid",
        "unsupported_capability",
    ):
        attempts = 0

        async def domain_failure(error_code: str = code) -> None:
            nonlocal attempts
            attempts += 1
            raise ProviderError("Safe provider failure.", code=error_code)

        with pytest.raises(ProviderError) as error:
            await executor.execute("fake", "domain", domain_failure)
        assert error.value.code == code
        assert attempts == 1


def test_provider_data_quality_timestamp_currency_symbol_and_staleness() -> None:
    settings = Settings(
        market_provider_future_timestamp_tolerance_seconds=60,
        market_quote_stale_after_seconds=30,
        _env_file=None,
    )
    quality = ProviderDataQualityService(settings)
    listing = context()
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)

    accepted = quality.quote(quote(listing, now=now + timedelta(seconds=60)), listing, now=now)
    assert accepted.status == MarketDataStatus.LIVE

    with pytest.raises(ProviderError, match="tolerance") as error:
        quality.quote(quote(listing, now=now + timedelta(seconds=61)), listing, now=now)
    assert error.value.code == "provider_timestamp_invalid"

    naive = quote(listing, now=now).model_copy(
        update={"provider_timestamp": datetime(2026, 1, 1, 12)}
    )
    with pytest.raises(ProviderError) as error:
        quality.quote(naive, listing, now=now)
    assert error.value.code == "provider_timestamp_invalid"

    for changed, code in (
        ({"currency": "USD"}, "provider_currency_mismatch"),
        ({"provider_symbol": "OTHER.XDEV"}, "provider_symbol_mismatch"),
        ({"provider_venue_code": "XDEM"}, "provider_symbol_mismatch"),
        ({"source_reference": ""}, "provider_response_invalid"),
    ):
        with pytest.raises(ProviderError) as error:
            quality.quote(quote(listing, now=now).model_copy(update=changed), listing, now=now)
        assert error.value.code == code

    stale = quality.quote(quote(listing, now=now - timedelta(seconds=31)), listing, now=now)
    assert stale.status == MarketDataStatus.STALE
    assert (
        quality.quote(
            quote(listing, now=now, status=MarketDataStatus.SIMULATED),
            listing,
            now=now,
        ).status
        == MarketDataStatus.SIMULATED
    )


def test_candle_quality_rejects_identity_currency_and_missing_provenance() -> None:
    listing = context()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    candle = CandlePoint(
        period_start=now - timedelta(days=1),
        period_end=now,
        open=Decimal("1"),
        high=Decimal("2"),
        low=Decimal("1"),
        close=Decimal("2"),
    )
    batch = ProviderCandleBatch(
        listing_id=listing.listing_id,
        provider="fake",
        provider_symbol=listing.provider_symbol,
        provider_venue_code=listing.provider_venue_code,
        source_reference="fixture:candles",
        received_at=now,
        currency=listing.currency,
        data_status=MarketDataStatus.DELAYED,
        interval=CandleInterval.ONE_DAY,
        candles=(candle,),
    )
    quality = ProviderDataQualityService(Settings(_env_file=None))
    assert quality.candles(batch, listing, now=now).data_status == MarketDataStatus.DELAYED
    for changed, code in (
        ({"provider_symbol": "OTHER"}, "provider_symbol_mismatch"),
        ({"currency": "USD"}, "provider_currency_mismatch"),
        ({"source_reference": ""}, "provider_response_invalid"),
    ):
        with pytest.raises(ProviderError) as error:
            quality.candles(batch.model_copy(update=changed), listing, now=now)
        assert error.value.code == code


class HealthRedis:
    def __init__(self, *, fail: bool = False, now: float = 0) -> None:
        self.values: dict[str, str] = {}
        self.expires_at: dict[str, float] = {}
        self.fail = fail
        self.now = now

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError
        if self.expires_at.get(key, float("inf")) <= self.now:
            self.values.pop(key, None)
            self.expires_at.pop(key, None)
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int) -> None:
        assert 1 <= ex <= 86400
        if self.fail:
            raise ConnectionError
        self.values[key] = value
        self.expires_at[key] = self.now + ex


async def test_provider_health_cache_hit_miss_malformed_and_redis_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = HealthRedis()
    service = MarketService(
        Settings(market_health_cache_ttl_seconds=5, _env_file=None),
        MarketCache(redis),  # type: ignore[arg-type]
    )
    calls = 0
    original = service.provider.get_health

    async def counted_health():
        nonlocal calls
        calls += 1
        return await original()

    monkeypatch.setattr(service.provider, "get_health", counted_health)
    assert (await service.status()).status == "available"
    assert (await service.status()).status == "available"
    assert calls == 1
    redis.now = 6
    assert (await service.status()).status == "available"
    assert calls == 2

    key = MarketCache.key("health", service.provider.name)
    redis.values[key] = '{"invalid":true}'
    assert (await service.status()).status == "available"
    assert calls == 3

    degraded = MarketService(
        Settings(_env_file=None),
        MarketCache(HealthRedis(fail=True)),  # type: ignore[arg-type]
    )
    assert (await degraded.status()).status == "available"
    assert MarketCache.key("health", "provider-a") != MarketCache.key("health", "provider-b")


async def test_quote_provider_failure_returns_only_explicit_stale_shadow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = HealthRedis()
    settings = Settings(
        market_quote_cache_ttl_seconds=5,
        market_quote_stale_fallback_ttl_seconds=30,
        _env_file=None,
    )
    service = MarketService(settings, MarketCache(redis))  # type: ignore[arg-type]
    listing_id = uuid4()
    instrument_id = uuid4()
    listing = SimpleNamespace(
        id=listing_id,
        instrument_id=instrument_id,
        ticker="SAFE",
        quote_currency="GBP",
        provider_normalised_symbol="SAFE.XDEV",
        exchange=SimpleNamespace(mic="XDEV"),
        provider_mappings=(
            SimpleNamespace(
                provider=service.provider.name,
                provider_symbol="SAFE.XDEV",
                provider_exchange_code="XDEV",
            ),
        ),
    )

    async def find_listing(_session: object, _listing_id: object) -> object:
        return listing

    monkeypatch.setattr(service.repository, "listing", find_listing)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    cached = QuoteResult(
        listing_id=listing_id,
        instrument_id=instrument_id,
        symbol="SAFE",
        exchange="XDEV",
        currency="GBP",
        price=Decimal("10.25"),
        provider=service.provider.name,
        provider_timestamp=now,
        received_at=now,
        data_status=MarketDataStatus.LIVE,
        is_stale=False,
        stale_after=now + timedelta(seconds=30),
        source_label="Verified fixture",
        market_session="regular",
        disclaimer="Read-only market data.",
    )
    key = MarketCache.key("quote", service.provider.name, listing_id)
    await service.cache.set_model_with_stale_fallback(  # type: ignore[union-attr]
        key, cached, fresh_ttl_seconds=5, stale_ttl_seconds=30
    )
    redis.now = 6

    async def unavailable(_context: ProviderListingContext) -> ProviderQuote:
        raise ProviderError("Provider unavailable.", code="provider_unavailable")

    monkeypatch.setattr(service.provider, "get_latest_quote", unavailable)
    result = await service.quote(object(), listing_id)  # type: ignore[arg-type]
    assert result.data_status == MarketDataStatus.STALE
    assert result.is_stale is True
    assert result.price == Decimal("10.25")

    redis.now = 31
    with pytest.raises(ProviderError, match="unavailable"):
        await service.quote(object(), listing_id)  # type: ignore[arg-type]


async def test_fixture_provider_rejects_unknown_instrument_without_external_io() -> None:
    with pytest.raises(ProviderError) as error:
        await DeterministicFixtureProvider().get_instrument("missing")
    assert error.value.code == "provider_symbol_not_found"


@pytest.mark.parametrize(
    "code",
    sorted(ProviderError.allowed_codes),
)
def test_every_provider_error_code_is_stable_and_safe(code: str) -> None:
    error = ProviderError("Safe provider failure.", code=code, retry_after_seconds=30)
    assert error.code == code
    assert error.retry_after_seconds == 30
    assert "key" not in error.message.casefold()


async def test_provider_models_reject_unexpected_fields() -> None:
    result = await DeterministicFixtureProvider().get_latest_quote(context())
    with pytest.raises(ValidationError):
        ProviderQuote.model_validate({**result.model_dump(), "raw_provider_payload": "secret"})
