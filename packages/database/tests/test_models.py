from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from packages.database.atlas_database.base import Base
from packages.database.atlas_database.models import (
    BillingCustomer,
    BillingSubscription,
    Exchange,
    HistoricalCandle,
    IdentityAuditEvent,
    Instrument,
    InvestmentAccount,
    LedgerEntry,
    LedgerTransaction,
    Portfolio,
    PositionSnapshot,
    ProviderSymbolMapping,
    QuoteObservation,
    StripeWebhookEvent,
    Tenant,
    User,
    UserProfile,
    Watchlist,
    WatchlistItem,
)


def constraint_names(table_name: str, constraint_type: type[object]) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, constraint_type) and constraint.name is not None
    }


def test_all_foundation_models_are_registered() -> None:
    assert {
        "tenants",
        "users",
        "memberships",
        "instruments",
        "instrument_listings",
        "investment_accounts",
        "portfolios",
        "position_snapshots",
        "ledger_accounts",
        "ledger_transactions",
        "ledger_entries",
        "billing_customers",
        "billing_subscriptions",
        "stripe_webhook_events",
        "payment_ledger_links",
        "user_profiles",
        "identity_audit_events",
        "clerk_webhook_events",
        "exchanges",
        "provider_symbol_mappings",
        "quote_observations",
        "historical_candles",
        "watchlists",
        "watchlist_items",
    }.issubset(Base.metadata.tables)


def test_financial_values_use_fixed_precision() -> None:
    for model, column_name in [
        (PositionSnapshot, "quantity"),
        (PositionSnapshot, "cost_basis"),
        (LedgerEntry, "amount"),
        (QuoteObservation, "price"),
        (HistoricalCandle, "open"),
        (HistoricalCandle, "close"),
    ]:
        column_type = model.__table__.c[column_name].type
        assert column_type.precision == 38
        assert column_type.scale == 18


def test_tenant_owned_relationships_have_composite_foreign_keys() -> None:
    assert "fk_portfolios_account_tenant" in constraint_names(
        Portfolio.__tablename__, ForeignKeyConstraint
    )
    assert "fk_position_snapshots_portfolio_tenant" in constraint_names(
        PositionSnapshot.__tablename__, ForeignKeyConstraint
    )
    assert "fk_ledger_entries_transaction_tenant" in constraint_names(
        LedgerEntry.__tablename__, ForeignKeyConstraint
    )
    assert "fk_ledger_entries_account_tenant" in constraint_names(
        LedgerEntry.__tablename__, ForeignKeyConstraint
    )


def test_ledger_has_integrity_constraints() -> None:
    assert "ck_ledger_entries_amount_non_zero" in constraint_names(
        LedgerEntry.__tablename__, CheckConstraint
    )
    assert "uq_ledger_transactions_idempotency" in constraint_names(
        LedgerTransaction.__tablename__, UniqueConstraint
    )


def test_identity_and_account_external_ids_are_unique() -> None:
    assert Tenant.__table__.c.clerk_organization_id.unique
    assert User.__table__.c.clerk_user_id.unique
    assert UserProfile.__table__.c.user_id.unique
    assert "uq_accounts_provider_id" in constraint_names(
        InvestmentAccount.__tablename__, UniqueConstraint
    )


def test_instrument_identifiers_are_globally_unique() -> None:
    assert Instrument.__table__.c.isin.unique
    assert Instrument.__table__.c.figi.unique


def test_billing_projections_use_unique_stripe_identifiers() -> None:
    assert BillingCustomer.__table__.c.stripe_customer_id.unique
    assert BillingSubscription.__table__.c.stripe_subscription_id.unique
    assert StripeWebhookEvent.__table__.c.stripe_event_id.unique


def test_identity_audit_events_have_no_update_timestamp() -> None:
    assert "created_at" in IdentityAuditEvent.__table__.c
    assert "updated_at" not in IdentityAuditEvent.__table__.c


def test_market_identity_and_observation_constraints() -> None:
    assert "uq_exchanges_mic" in constraint_names(Exchange.__tablename__, UniqueConstraint)
    assert "uq_provider_symbol_namespace" in constraint_names(
        ProviderSymbolMapping.__tablename__, UniqueConstraint
    )
    assert "uq_candle_observation" in constraint_names(
        HistoricalCandle.__tablename__, UniqueConstraint
    )
    assert "ck_historical_candles_high_not_below_low" in constraint_names(
        HistoricalCandle.__tablename__, CheckConstraint
    )
    assert "uq_watchlist_items_listing" in constraint_names(
        WatchlistItem.__tablename__, UniqueConstraint
    )
    assert "uq_watchlists_tenant_name" in constraint_names(
        Watchlist.__tablename__, UniqueConstraint
    )
