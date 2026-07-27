from enum import StrEnum


class TenantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    CLOSED = "closed"


class TenantType(StrEnum):
    PERSONAL = "personal"
    TEAM = "team"


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class PlatformRole(StrEnum):
    USER = "user"
    SUPPORT = "support"
    COMPLIANCE = "compliance"
    PLATFORM_ADMIN = "platform_admin"


class OnboardingStatus(StrEnum):
    NOT_STARTED = "not_started"
    PROFILE_REQUIRED = "profile_required"
    WORKSPACE_REQUIRED = "workspace_required"
    COMPLETED = "completed"


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    REMOVED = "removed"


class IdentityWebhookStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class AccountType(StrEnum):
    CASH = "cash"
    CUSTODY = "custody"
    BROKERAGE = "brokerage"
    RETIREMENT = "retirement"
    TAX_ADVANTAGED = "tax_advantaged"


class AccountStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    CLOSED = "closed"


class AssetClass(StrEnum):
    EQUITY = "equity"
    EXCHANGE_TRADED_FUND = "exchange_traded_fund"
    FOREIGN_EXCHANGE = "foreign_exchange"
    CRYPTOCURRENCY = "cryptocurrency"
    BOND = "bond"
    FUND = "fund"
    OTHER = "other"
    STOCK = "stock"
    ETF = "etf"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    INDEX = "index"
    CASH = "cash"


class InstrumentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELISTED = "delisted"


class VenueStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ListingStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELISTED = "delisted"
    INACTIVE = "inactive"


class ProviderMappingStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MarketDataStatus(StrEnum):
    LIVE = "live"
    DELAYED = "delayed"
    END_OF_DAY = "end_of_day"
    CACHED = "cached"
    STALE = "stale"
    SIMULATED = "simulated"
    UNAVAILABLE = "unavailable"


class MarketSession(StrEnum):
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class CandleInterval(StrEnum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1mo"


class WatchlistVisibility(StrEnum):
    PRIVATE = "private"
    TENANT = "tenant"


class WatchlistStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class LedgerAccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class LedgerTransactionStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"


class SubscriptionStatus(StrEnum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class WebhookEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"
