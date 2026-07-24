from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.database.atlas_database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from packages.database.atlas_database.models.enums import AssetClass, InstrumentStatus


class Instrument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("canonical_symbol", "asset_class", name="uq_instruments_symbol_class"),
        CheckConstraint("length(base_currency) = 3", name="base_currency_iso_length"),
        Index("ix_instruments_asset_status", "asset_class", "status"),
    )

    canonical_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_class: Mapped[AssetClass] = mapped_column(
        Enum(
            AssetClass,
            name="asset_class",
            native_enum=False,
            length=16,
            create_constraint=True,
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
        ),
        default=InstrumentStatus.ACTIVE,
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(12), unique=True)
    figi: Mapped[str | None] = mapped_column(String(12), unique=True)
    metadata_version: Mapped[int] = mapped_column(default=1, nullable=False)

    listings: Mapped[list["InstrumentListing"]] = relationship(back_populates="instrument")


class InstrumentListing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instrument_listings"
    __table_args__ = (
        UniqueConstraint(
            "venue_mic", "ticker", "quote_currency", name="uq_listings_venue_ticker_currency"
        ),
        CheckConstraint("length(venue_mic) = 4", name="venue_mic_iso_length"),
        CheckConstraint("length(quote_currency) = 3", name="quote_currency_iso_length"),
        CheckConstraint("price_increment > 0", name="price_increment_positive"),
    )

    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False
    )
    venue_mic: Mapped[str] = mapped_column(String(4), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    price_increment: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    instrument: Mapped[Instrument] = relationship(back_populates="listings")
