"""Create provider-neutral instruments, market data, and tenant watchlists.

Revision ID: 20260727_0004
Revises: 20260727_0003
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_0004"
down_revision: str | None = "20260727_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = sa.Uuid()
PRICE = sa.Numeric(38, 18)


def timestamps(*, mutable: bool = True) -> list[sa.Column[object]]:
    columns: list[sa.Column[object]] = [
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    ]
    if mutable:
        columns.append(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
    return columns


def upgrade() -> None:
    op.drop_constraint("ck_instruments_asset_class", "instruments", type_="check")
    op.drop_constraint("ck_instruments_instrument_status", "instruments", type_="check")
    op.drop_constraint("uq_instruments_symbol_class", "instruments", type_="unique")
    op.alter_column(
        "instruments",
        "canonical_symbol",
        existing_type=sa.String(64),
        nullable=True,
    )
    op.alter_column(
        "instruments",
        "asset_class",
        existing_type=sa.String(16),
        type_=sa.String(24),
        existing_nullable=False,
    )
    op.add_column("instruments", sa.Column("short_name", sa.String(120), nullable=True))
    op.add_column("instruments", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("instruments", sa.Column("country_code", sa.String(2), nullable=True))
    op.add_column("instruments", sa.Column("cusip", sa.String(9), nullable=True))
    op.add_column("instruments", sa.Column("sedol", sa.String(7), nullable=True))
    op.create_unique_constraint("uq_instruments_cusip", "instruments", ["cusip"])
    op.create_unique_constraint("uq_instruments_sedol", "instruments", ["sedol"])
    op.create_check_constraint(
        "ck_instruments_country_iso_length",
        "instruments",
        "country_code IS NULL OR length(country_code) = 2",
    )
    op.create_check_constraint(
        "ck_instruments_asset_class",
        "instruments",
        "asset_class IN ('equity','exchange_traded_fund','index','foreign_exchange',"
        "'cryptocurrency','commodity','bond','fund','other','stock','etf','forex','crypto','cash')",
    )
    op.create_check_constraint(
        "ck_instruments_instrument_status",
        "instruments",
        "status IN ('active','inactive','suspended','delisted')",
    )
    op.create_index("ix_instruments_name", "instruments", ["name"], unique=False)

    op.create_table(
        "exchanges",
        *timestamps(),
        sa.Column("mic", sa.String(4), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("acronym", sa.String(32), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("market_type", sa.String(32), server_default="exchange", nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.CheckConstraint("length(mic) = 4", name="ck_exchanges_mic_length"),
        sa.CheckConstraint("length(country_code) = 2", name="ck_exchanges_country_iso_length"),
        sa.CheckConstraint(
            "length(default_currency) = 3", name="ck_exchanges_currency_iso_length"
        ),
        sa.CheckConstraint("status IN ('active','inactive')", name="ck_exchanges_venue_status"),
        sa.PrimaryKeyConstraint("id", name="pk_exchanges"),
        sa.UniqueConstraint("mic", name="uq_exchanges_mic"),
    )
    op.create_index("ix_exchanges_status_name", "exchanges", ["status", "name"], unique=False)
    op.execute(
        """
        INSERT INTO exchanges
            (id, mic, name, country_code, timezone, default_currency, market_type, status)
        SELECT gen_random_uuid(), venue_mic, 'Legacy venue ' || venue_mic, 'ZZ', 'UTC',
               min(quote_currency), 'exchange', 'active'
        FROM instrument_listings
        GROUP BY venue_mic
        """
    )

    op.add_column("instrument_listings", sa.Column("exchange_id", UUID, nullable=True))
    op.add_column(
        "instrument_listings",
        sa.Column("provider_normalised_symbol", sa.String(96), nullable=True),
    )
    op.add_column(
        "instrument_listings",
        sa.Column("listing_status", sa.String(16), server_default="active", nullable=False),
    )
    op.add_column(
        "instrument_listings",
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("instrument_listings", sa.Column("first_trade_date", sa.Date(), nullable=True))
    op.add_column("instrument_listings", sa.Column("last_trade_date", sa.Date(), nullable=True))
    op.execute(
        """
        UPDATE instrument_listings AS listing
        SET exchange_id = exchange.id
        FROM exchanges AS exchange
        WHERE exchange.mic = listing.venue_mic
        """
    )
    op.alter_column("instrument_listings", "exchange_id", nullable=False)
    op.create_foreign_key(
        "fk_instrument_listings_exchange_id_exchanges",
        "instrument_listings",
        "exchanges",
        ["exchange_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_listings_venue_ticker_currency", "instrument_listings", type_="unique"
    )
    op.create_unique_constraint(
        "uq_listings_exchange_symbol", "instrument_listings", ["exchange_id", "ticker"]
    )
    op.create_check_constraint(
        "ck_instrument_listings_listing_status",
        "instrument_listings",
        "listing_status IN ('active','suspended','delisted','inactive')",
    )
    op.create_index(
        "ix_listings_symbol_exchange",
        "instrument_listings",
        ["ticker", "exchange_id"],
        unique=False,
    )
    op.create_index(
        "ix_listings_instrument_status",
        "instrument_listings",
        ["instrument_id", "listing_status"],
        unique=False,
    )

    op.create_table(
        "provider_symbol_mappings",
        *timestamps(),
        sa.Column("provider", sa.String(48), nullable=False),
        sa.Column("listing_id", UUID, nullable=False),
        sa.Column("provider_symbol", sa.String(96), nullable=False),
        sa.Column(
            "provider_exchange_code", sa.String(48), server_default="", nullable=False
        ),
        sa.Column("provider_instrument_type", sa.String(48), nullable=True),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active','inactive')", name="ck_provider_symbol_mappings_status"
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_provider_symbol_mappings_listing_id_instrument_listings",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_provider_symbol_mappings"),
        sa.UniqueConstraint(
            "provider",
            "provider_symbol",
            "provider_exchange_code",
            name="uq_provider_symbol_namespace",
        ),
        sa.UniqueConstraint("provider", "listing_id", name="uq_provider_listing"),
    )
    op.create_index(
        "ix_provider_mappings_listing",
        "provider_symbol_mappings",
        ["listing_id", "status"],
        unique=False,
    )

    op.create_table(
        "quote_observations",
        *timestamps(mutable=False),
        sa.Column("listing_id", UUID, nullable=False),
        sa.Column("provider", sa.String(48), nullable=False),
        sa.Column("provider_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market_session", sa.String(16), server_default="unknown", nullable=False),
        sa.Column("price", PRICE, nullable=True),
        sa.Column("bid", PRICE, nullable=True),
        sa.Column("ask", PRICE, nullable=True),
        sa.Column("bid_size", PRICE, nullable=True),
        sa.Column("ask_size", PRICE, nullable=True),
        sa.Column("open", PRICE, nullable=True),
        sa.Column("high", PRICE, nullable=True),
        sa.Column("low", PRICE, nullable=True),
        sa.Column("previous_close", PRICE, nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("data_status", sa.String(16), nullable=False),
        sa.Column("delay_seconds", sa.Integer(), nullable=True),
        sa.Column("source_reference", sa.String(160), nullable=False),
        sa.CheckConstraint("price IS NULL OR price >= 0", name="ck_quote_price_non_negative"),
        sa.CheckConstraint("bid IS NULL OR bid >= 0", name="ck_quote_bid_non_negative"),
        sa.CheckConstraint("ask IS NULL OR ask >= 0", name="ck_quote_ask_non_negative"),
        sa.CheckConstraint("volume IS NULL OR volume >= 0", name="ck_quote_volume_non_negative"),
        sa.CheckConstraint(
            "data_status IN ('live','delayed','end_of_day','cached','stale','simulated','unavailable')",
            name="ck_quote_data_status",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_quote_observations_listing_id_instrument_listings",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quote_observations"),
        sa.UniqueConstraint(
            "provider", "listing_id", "provider_timestamp", name="uq_quote_observation"
        ),
    )
    op.create_index(
        "ix_quote_listing_provider_timestamp",
        "quote_observations",
        ["listing_id", "provider", "provider_timestamp"],
        unique=False,
    )

    op.create_table(
        "historical_candles",
        *timestamps(mutable=False),
        sa.Column("listing_id", UUID, nullable=False),
        sa.Column("provider", sa.String(48), nullable=False),
        sa.Column("interval", sa.String(4), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", PRICE, nullable=False),
        sa.Column("high", PRICE, nullable=False),
        sa.Column("low", PRICE, nullable=False),
        sa.Column("close", PRICE, nullable=False),
        sa.Column("adjusted_close", PRICE, nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("data_status", sa.String(16), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("period_end > period_start", name="ck_candles_period_order"),
        sa.CheckConstraint(
            "open >= 0 AND high >= 0 AND low >= 0 AND close >= 0",
            name="ck_candles_prices_non_negative",
        ),
        sa.CheckConstraint("high >= low", name="ck_candles_high_not_below_low"),
        sa.CheckConstraint("open BETWEEN low AND high", name="ck_candles_open_in_range"),
        sa.CheckConstraint("close BETWEEN low AND high", name="ck_candles_close_in_range"),
        sa.CheckConstraint(
            "volume IS NULL OR volume >= 0", name="ck_candles_volume_non_negative"
        ),
        sa.CheckConstraint(
            "interval IN ('1m','5m','15m','1h','1d','1w','1mo')",
            name="ck_candles_interval",
        ),
        sa.CheckConstraint(
            "data_status IN ('live','delayed','end_of_day','cached','stale','simulated','unavailable')",
            name="ck_candles_data_status",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_historical_candles_listing_id_instrument_listings",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_historical_candles"),
        sa.UniqueConstraint(
            "provider",
            "listing_id",
            "interval",
            "period_start",
            name="uq_candle_observation",
        ),
    )
    op.create_index(
        "ix_candles_listing_interval_start",
        "historical_candles",
        ["listing_id", "interval", "period_start"],
        unique=False,
    )

    op.create_table(
        "watchlists",
        *timestamps(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("visibility", sa.String(16), server_default="tenant", nullable=False),
        sa.Column("created_by_user_id", UUID, nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.CheckConstraint(
            "visibility IN ('private','tenant')", name="ck_watchlists_visibility"
        ),
        sa.CheckConstraint(
            "status IN ('active','archived')", name="ck_watchlists_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_watchlists_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_watchlists_created_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_watchlists"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_watchlists_tenant_name"),
    )
    op.create_index(
        "ix_watchlists_tenant_status_created",
        "watchlists",
        ["tenant_id", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "watchlist_items",
        *timestamps(),
        sa.Column("watchlist_id", UUID, nullable=False),
        sa.Column("listing_id", UUID, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("added_by_user_id", UUID, nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_watchlist_items_position_non_negative"),
        sa.ForeignKeyConstraint(
            ["watchlist_id"],
            ["watchlists.id"],
            name="fk_watchlist_items_watchlist_id_watchlists",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_watchlist_items_listing_id_instrument_listings",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["added_by_user_id"],
            ["users.id"],
            name="fk_watchlist_items_added_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_watchlist_items"),
        sa.UniqueConstraint(
            "watchlist_id", "listing_id", name="uq_watchlist_items_listing"
        ),
        sa.UniqueConstraint(
            "watchlist_id", "position", name="uq_watchlist_items_position"
        ),
    )
    op.create_index(
        "ix_watchlist_items_watchlist_position",
        "watchlist_items",
        ["watchlist_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_table("historical_candles")
    op.drop_table("quote_observations")
    op.execute(
        """
        DELETE FROM instrument_listings AS listing
        USING provider_symbol_mappings AS mapping
        WHERE mapping.listing_id = listing.id
          AND mapping.provider = 'atlas_simulated'
        """
    )
    op.execute(
        """
        DELETE FROM instruments
        WHERE description = 'Fictional catalogue record for deterministic private development.'
          AND NOT EXISTS (
              SELECT 1 FROM instrument_listings
              WHERE instrument_listings.instrument_id = instruments.id
          )
        """
    )
    op.drop_table("provider_symbol_mappings")
    op.drop_index("ix_listings_instrument_status", table_name="instrument_listings")
    op.drop_index("ix_listings_symbol_exchange", table_name="instrument_listings")
    op.drop_constraint(
        "ck_instrument_listings_listing_status", "instrument_listings", type_="check"
    )
    op.drop_constraint(
        "uq_listings_exchange_symbol", "instrument_listings", type_="unique"
    )
    op.drop_constraint(
        "fk_instrument_listings_exchange_id_exchanges",
        "instrument_listings",
        type_="foreignkey",
    )
    op.drop_column("instrument_listings", "last_trade_date")
    op.drop_column("instrument_listings", "first_trade_date")
    op.drop_column("instrument_listings", "is_primary")
    op.drop_column("instrument_listings", "listing_status")
    op.drop_column("instrument_listings", "provider_normalised_symbol")
    op.drop_column("instrument_listings", "exchange_id")
    op.create_unique_constraint(
        "uq_listings_venue_ticker_currency",
        "instrument_listings",
        ["venue_mic", "ticker", "quote_currency"],
    )
    op.execute(
        "DELETE FROM exchanges WHERE market_type = 'simulated' "
        "AND NOT EXISTS (SELECT 1 FROM instrument_listings "
        "WHERE instrument_listings.venue_mic = exchanges.mic)"
    )
    op.drop_table("exchanges")

    op.drop_index("ix_instruments_name", table_name="instruments")
    op.drop_constraint("ck_instruments_instrument_status", "instruments", type_="check")
    op.drop_constraint("ck_instruments_asset_class", "instruments", type_="check")
    op.drop_constraint("ck_instruments_country_iso_length", "instruments", type_="check")
    op.drop_constraint("uq_instruments_sedol", "instruments", type_="unique")
    op.drop_constraint("uq_instruments_cusip", "instruments", type_="unique")
    op.drop_column("instruments", "sedol")
    op.drop_column("instruments", "cusip")
    op.drop_column("instruments", "country_code")
    op.drop_column("instruments", "description")
    op.drop_column("instruments", "short_name")
    op.execute(
        "UPDATE instruments SET canonical_symbol = 'ATLAS-' || substring(id::text, 1, 8) "
        "WHERE canonical_symbol IS NULL"
    )
    op.alter_column(
        "instruments",
        "asset_class",
        existing_type=sa.String(24),
        type_=sa.String(16),
        existing_nullable=False,
    )
    op.alter_column(
        "instruments",
        "canonical_symbol",
        existing_type=sa.String(64),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_instruments_asset_class",
        "instruments",
        "asset_class IN ('stock','etf','forex','crypto','commodity','index','cash')",
    )
    op.create_check_constraint(
        "ck_instruments_instrument_status",
        "instruments",
        "status IN ('active','inactive','delisted')",
    )
    op.create_unique_constraint(
        "uq_instruments_symbol_class",
        "instruments",
        ["canonical_symbol", "asset_class"],
    )
