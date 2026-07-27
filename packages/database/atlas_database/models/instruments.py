from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.database.atlas_database.base import (
    Base,
    ImmutableTimestampMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from packages.database.atlas_database.models.enums import (
    AssetClass,
    CandleInterval,
    InstrumentStatus,
    ListingStatus,
    MarketDataStatus,
    MarketSession,
    ProviderMappingStatus,
    VenueStatus,
    WatchlistStatus,
    WatchlistVisibility,
)


def enum_values(enum: type[object]) -> list[str]:
    return [str(member.value) for member in enum]  # type: ignore[attr-defined]


class Exchange(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exchanges"
    __table_args__ = (
        UniqueConstraint("mic", name="uq_exchanges_mic"),
        CheckConstraint("length(mic) = 4", name="mic_length"),
        CheckConstraint("length(country_code) = 2", name="country_iso_length"),
        CheckConstraint("length(default_currency) = 3", name="currency_iso_length"),
        Index("ix_exchanges_status_name", "status", "name"),
    )

    mic: Mapped[str] = mapped_column(String(4), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    acronym: Mapped[str | None] = mapped_column(String(32))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    market_type: Mapped[str] = mapped_column(String(32), default="exchange", nullable=False)
    status: Mapped[VenueStatus] = mapped_column(
        Enum(
            VenueStatus,
            name="venue_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=VenueStatus.ACTIVE,
        nullable=False,
    )

    listings: Mapped[list["InstrumentListing"]] = relationship(back_populates="exchange")


class Instrument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instruments"
    __table_args__ = (
        CheckConstraint("length(base_currency) = 3", name="base_currency_iso_length"),
        CheckConstraint(
            "country_code IS NULL OR length(country_code) = 2", name="country_iso_length"
        ),
        Index("ix_instruments_asset_status", "asset_class", "status"),
        Index("ix_instruments_name", "name"),
    )

    # canonical_symbol is retained for backwards compatibility only. Listing symbols are the
    # discovery identity; Atlas UUID remains the immutable instrument identity.
    canonical_symbol: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    asset_class: Mapped[AssetClass] = mapped_column(
        Enum(
            AssetClass,
            name="asset_class",
            native_enum=False,
            length=24,
            create_constraint=True,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    status: Mapped[InstrumentStatus] = mapped_column(
        Enum(
            InstrumentStatus,
            name="instrument_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=InstrumentStatus.ACTIVE,
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    isin: Mapped[str | None] = mapped_column(String(12), unique=True)
    cusip: Mapped[str | None] = mapped_column(String(9), unique=True)
    sedol: Mapped[str | None] = mapped_column(String(7), unique=True)
    figi: Mapped[str | None] = mapped_column(String(12), unique=True)
    metadata_version: Mapped[int] = mapped_column(default=1, nullable=False)

    listings: Mapped[list["InstrumentListing"]] = relationship(back_populates="instrument")


class InstrumentListing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instrument_listings"
    __table_args__ = (
        UniqueConstraint("exchange_id", "ticker", name="uq_listings_exchange_symbol"),
        CheckConstraint("length(venue_mic) = 4", name="venue_mic_iso_length"),
        CheckConstraint("length(quote_currency) = 3", name="quote_currency_iso_length"),
        CheckConstraint("price_increment > 0", name="price_increment_positive"),
        Index("ix_listings_symbol_exchange", "ticker", "exchange_id"),
        Index("ix_listings_instrument_status", "instrument_id", "listing_status"),
    )

    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False
    )
    exchange_id: Mapped[UUID] = mapped_column(
        ForeignKey("exchanges.id", ondelete="RESTRICT"), nullable=False
    )
    venue_mic: Mapped[str] = mapped_column(String(4), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_normalised_symbol: Mapped[str | None] = mapped_column(String(96))
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    listing_status: Mapped[ListingStatus] = mapped_column(
        Enum(
            ListingStatus,
            name="listing_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=ListingStatus.ACTIVE,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_trade_date: Mapped[date | None] = mapped_column(Date)
    last_trade_date: Mapped[date | None] = mapped_column(Date)
    price_increment: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    instrument: Mapped[Instrument] = relationship(back_populates="listings")
    exchange: Mapped[Exchange] = relationship(back_populates="listings")
    provider_mappings: Mapped[list["ProviderSymbolMapping"]] = relationship(
        back_populates="listing"
    )


class ProviderSymbolMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_symbol_mappings"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_symbol",
            "provider_exchange_code",
            name="uq_provider_symbol_namespace",
        ),
        UniqueConstraint("provider", "listing_id", name="uq_provider_listing"),
        Index("ix_provider_mappings_listing", "listing_id", "status"),
    )

    provider: Mapped[str] = mapped_column(String(48), nullable=False)
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="CASCADE"), nullable=False
    )
    provider_symbol: Mapped[str] = mapped_column(String(96), nullable=False)
    provider_exchange_code: Mapped[str] = mapped_column(String(48), default="", nullable=False)
    provider_instrument_type: Mapped[str | None] = mapped_column(String(48))
    status: Mapped[ProviderMappingStatus] = mapped_column(
        Enum(
            ProviderMappingStatus,
            name="provider_mapping_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=ProviderMappingStatus.ACTIVE,
        nullable=False,
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listing: Mapped[InstrumentListing] = relationship(back_populates="provider_mappings")


class QuoteObservation(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "quote_observations"
    __table_args__ = (
        UniqueConstraint(
            "provider", "listing_id", "provider_timestamp", name="uq_quote_observation"
        ),
        CheckConstraint("price IS NULL OR price >= 0", name="price_non_negative"),
        CheckConstraint("bid IS NULL OR bid >= 0", name="bid_non_negative"),
        CheckConstraint("ask IS NULL OR ask >= 0", name="ask_non_negative"),
        CheckConstraint("volume IS NULL OR volume >= 0", name="volume_non_negative"),
        Index(
            "ix_quote_listing_provider_timestamp",
            "listing_id",
            "provider",
            "provider_timestamp",
        ),
    )

    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(48), nullable=False)
    provider_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    market_session: Mapped[MarketSession] = mapped_column(
        Enum(
            MarketSession,
            name="market_session",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=MarketSession.UNKNOWN,
        nullable=False,
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    bid: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    ask: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    bid_size: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    ask_size: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    open: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    high: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    low: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    previous_close: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    data_status: Mapped[MarketDataStatus] = mapped_column(
        Enum(
            MarketDataStatus,
            name="market_data_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    delay_seconds: Mapped[int | None]
    source_reference: Mapped[str] = mapped_column(String(160), nullable=False)


class HistoricalCandle(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "historical_candles"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "listing_id",
            "interval",
            "period_start",
            name="uq_candle_observation",
        ),
        CheckConstraint("period_end > period_start", name="period_order"),
        CheckConstraint(
            "open >= 0 AND high >= 0 AND low >= 0 AND close >= 0", name="prices_non_negative"
        ),
        CheckConstraint("high >= low", name="high_not_below_low"),
        CheckConstraint("open BETWEEN low AND high", name="open_in_range"),
        CheckConstraint("close BETWEEN low AND high", name="close_in_range"),
        CheckConstraint("volume IS NULL OR volume >= 0", name="volume_non_negative"),
        Index(
            "ix_candles_listing_interval_start",
            "listing_id",
            "interval",
            "period_start",
        ),
    )

    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(48), nullable=False)
    interval: Mapped[CandleInterval] = mapped_column(
        Enum(
            CandleInterval,
            name="candle_interval",
            native_enum=False,
            length=4,
            create_constraint=True,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    data_status: Mapped[MarketDataStatus] = mapped_column(
        Enum(
            MarketDataStatus,
            name="candle_data_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Watchlist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_watchlists_tenant_name"),
        Index("ix_watchlists_tenant_status_created", "tenant_id", "status", "created_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    visibility: Mapped[WatchlistVisibility] = mapped_column(
        Enum(
            WatchlistVisibility,
            name="watchlist_visibility",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=WatchlistVisibility.TENANT,
        nullable=False,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[WatchlistStatus] = mapped_column(
        Enum(
            WatchlistStatus,
            name="watchlist_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=WatchlistStatus.ACTIVE,
        nullable=False,
    )

    items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "listing_id", name="uq_watchlist_items_listing"),
        UniqueConstraint("watchlist_id", "position", name="uq_watchlist_items_position"),
        CheckConstraint("position >= 0", name="position_non_negative"),
        Index("ix_watchlist_items_watchlist_position", "watchlist_id", "position"),
    )

    watchlist_id: Mapped[UUID] = mapped_column(
        ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False
    )
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument_listings.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))
    added_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    watchlist: Mapped[Watchlist] = relationship(back_populates="items")
