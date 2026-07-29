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
from packages.database.atlas_database.models.research import (
    BacktestEquityPoint,
    BacktestEvent,
    BacktestExplanation,
    BacktestResult,
    BacktestRun,
    ResearchAuditEvent,
    ResearchStrategy,
    ResearchStrategyVersion,
)

__all__ = [
    "BacktestEquityPoint",
    "BacktestEvent",
    "BacktestExplanation",
    "BacktestResult",
    "BacktestRun",
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
    "ResearchAuditEvent",
    "ResearchStrategy",
    "ResearchStrategyVersion",
    "StripeWebhookEvent",
    "Tenant",
    "User",
    "UserProfile",
    "Watchlist",
    "WatchlistItem",
]
