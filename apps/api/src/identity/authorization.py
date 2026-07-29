from enum import StrEnum

from fastapi import status

from apps.api.src.core.errors import ApplicationError
from packages.database.atlas_database.models.enums import MembershipRole


class Permission(StrEnum):
    ORGANISATION_READ = "organisation:read"
    ORGANISATION_UPDATE = "organisation:update"
    MEMBERSHIP_READ = "membership:read"
    MEMBERSHIP_INVITE = "membership:invite"
    MEMBERSHIP_UPDATE = "membership:update"
    MEMBERSHIP_REMOVE = "membership:remove"
    PROFILE_READ_SELF = "profile:read:self"
    PROFILE_UPDATE_SELF = "profile:update:self"
    AUDIT_READ = "audit:read"
    OWNERSHIP_TRANSFER = "ownership:transfer"
    ORGANISATION_ARCHIVE = "organisation:archive"
    WATCHLIST_READ = "watchlist:read"
    WATCHLIST_CREATE = "watchlist:create"
    WATCHLIST_UPDATE = "watchlist:update"
    WATCHLIST_DELETE = "watchlist:delete"
    WATCHLIST_ITEM_ADD = "watchlist:item:add"
    WATCHLIST_ITEM_REMOVE = "watchlist:item:remove"
    PORTFOLIO_READ = "portfolio:read"
    PORTFOLIO_CREATE = "portfolio:create"
    PORTFOLIO_UPDATE = "portfolio:update"
    PORTFOLIO_ARCHIVE = "portfolio:archive"
    PORTFOLIO_TRANSACTION_CREATE = "portfolio:transaction:create"
    PORTFOLIO_TRANSACTION_READ = "portfolio:transaction:read"
    PORTFOLIO_ANALYTICS_READ = "portfolio:analytics:read"
    PORTFOLIO_AUDIT_READ = "portfolio:audit:read"
    STRATEGY_READ = "strategy:read"
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_UPDATE = "strategy:update"
    STRATEGY_ARCHIVE = "strategy:archive"
    STRATEGY_VERSION_CREATE = "strategy:version:create"
    BACKTEST_CREATE = "backtest:create"
    BACKTEST_READ = "backtest:read"
    BACKTEST_COMPARE = "backtest:compare"
    BACKTEST_EXPLAIN = "backtest:explain"
    BACKTEST_AUDIT_READ = "backtest:audit:read"


ROLE_PERMISSIONS: dict[MembershipRole, frozenset[Permission]] = {
    MembershipRole.OWNER: frozenset(Permission),
    MembershipRole.ADMIN: frozenset(
        {
            Permission.ORGANISATION_READ,
            Permission.ORGANISATION_UPDATE,
            Permission.MEMBERSHIP_READ,
            Permission.MEMBERSHIP_INVITE,
            Permission.MEMBERSHIP_UPDATE,
            Permission.MEMBERSHIP_REMOVE,
            Permission.PROFILE_READ_SELF,
            Permission.PROFILE_UPDATE_SELF,
            Permission.AUDIT_READ,
            Permission.WATCHLIST_READ,
            Permission.WATCHLIST_CREATE,
            Permission.WATCHLIST_UPDATE,
            Permission.WATCHLIST_DELETE,
            Permission.WATCHLIST_ITEM_ADD,
            Permission.WATCHLIST_ITEM_REMOVE,
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_CREATE,
            Permission.PORTFOLIO_UPDATE,
            Permission.PORTFOLIO_ARCHIVE,
            Permission.PORTFOLIO_TRANSACTION_CREATE,
            Permission.PORTFOLIO_TRANSACTION_READ,
            Permission.PORTFOLIO_ANALYTICS_READ,
            Permission.PORTFOLIO_AUDIT_READ,
            Permission.STRATEGY_READ,
            Permission.STRATEGY_CREATE,
            Permission.STRATEGY_UPDATE,
            Permission.STRATEGY_ARCHIVE,
            Permission.STRATEGY_VERSION_CREATE,
            Permission.BACKTEST_CREATE,
            Permission.BACKTEST_READ,
            Permission.BACKTEST_COMPARE,
            Permission.BACKTEST_EXPLAIN,
            Permission.BACKTEST_AUDIT_READ,
        }
    ),
    MembershipRole.MEMBER: frozenset(
        {
            Permission.ORGANISATION_READ,
            Permission.MEMBERSHIP_READ,
            Permission.PROFILE_READ_SELF,
            Permission.PROFILE_UPDATE_SELF,
            Permission.WATCHLIST_READ,
            Permission.WATCHLIST_CREATE,
            Permission.WATCHLIST_UPDATE,
            Permission.WATCHLIST_ITEM_ADD,
            Permission.WATCHLIST_ITEM_REMOVE,
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_CREATE,
            Permission.PORTFOLIO_UPDATE,
            Permission.PORTFOLIO_TRANSACTION_CREATE,
            Permission.PORTFOLIO_TRANSACTION_READ,
            Permission.PORTFOLIO_ANALYTICS_READ,
            Permission.STRATEGY_READ,
            Permission.STRATEGY_CREATE,
            Permission.STRATEGY_UPDATE,
            Permission.STRATEGY_VERSION_CREATE,
            Permission.BACKTEST_CREATE,
            Permission.BACKTEST_READ,
            Permission.BACKTEST_COMPARE,
            Permission.BACKTEST_EXPLAIN,
        }
    ),
    MembershipRole.VIEWER: frozenset(
        {
            Permission.ORGANISATION_READ,
            Permission.PROFILE_READ_SELF,
            Permission.PROFILE_UPDATE_SELF,
            Permission.WATCHLIST_READ,
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_TRANSACTION_READ,
            Permission.PORTFOLIO_ANALYTICS_READ,
            Permission.STRATEGY_READ,
            Permission.BACKTEST_READ,
            Permission.BACKTEST_COMPARE,
        }
    ),
}


class AuthorisationService:
    def can(self, role: MembershipRole, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS[role]

    def require_permission(self, role: MembershipRole, permission: Permission) -> None:
        if not self.can(role, permission):
            raise ApplicationError(
                "You do not have permission to perform this action.",
                code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    def require_role(self, role: MembershipRole, allowed: set[MembershipRole]) -> None:
        if role not in allowed:
            raise ApplicationError(
                "You do not have the required organisation role.",
                code="role_required",
                status_code=status.HTTP_403_FORBIDDEN,
            )
