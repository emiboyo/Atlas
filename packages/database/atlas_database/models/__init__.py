"""Atlas persistence models.

Importing this module registers every model with the shared SQLAlchemy metadata.
"""

from packages.database.atlas_database.models.billing import (
    BillingCustomer,
    BillingSubscription,
    PaymentLedgerLink,
    StripeWebhookEvent,
)
from packages.database.atlas_database.models.identity import (
    ClerkWebhookEvent,
    IdentityAuditEvent,
    Membership,
    Tenant,
    User,
    UserProfile,
)
from packages.database.atlas_database.models.instruments import (
    Exchange,
    HistoricalCandle,
    Instrument,
    InstrumentListing,
    ProviderSymbolMapping,
    QuoteObservation,
    Watchlist,
    WatchlistItem,
)
from packages.database.atlas_database.models.ledger import (
    LedgerAccount,
    LedgerEntry,
    LedgerTransaction,
)
from packages.database.atlas_database.models.portfolios import (
    InvestmentAccount,
    Portfolio,
    PortfolioAccount,
    PortfolioAuditEvent,
    PortfolioPosition,
    PortfolioTransaction,
    PortfolioValuationLine,
    PortfolioValuationSnapshot,
    PositionSnapshot,
)

__all__ = [
    "BillingCustomer",
    "BillingSubscription",
    "ClerkWebhookEvent",
    "Exchange",
    "HistoricalCandle",
    "IdentityAuditEvent",
    "Instrument",
    "InstrumentListing",
    "InvestmentAccount",
    "LedgerAccount",
    "LedgerEntry",
    "LedgerTransaction",
    "Membership",
    "PaymentLedgerLink",
    "Portfolio",
    "PortfolioAccount",
    "PortfolioAuditEvent",
    "PortfolioPosition",
    "PortfolioTransaction",
    "PortfolioValuationLine",
    "PortfolioValuationSnapshot",
    "PositionSnapshot",
    "ProviderSymbolMapping",
    "QuoteObservation",
    "StripeWebhookEvent",
    "Tenant",
    "User",
    "UserProfile",
    "Watchlist",
    "WatchlistItem",
]
