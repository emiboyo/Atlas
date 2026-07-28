from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from hashlib import sha256
from itertools import pairwise
from typing import cast
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.errors import ApplicationError
from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.identity.services import OrganisationService
from apps.api.src.market.services import MarketService
from apps.api.src.portfolio.metrics import (
    ANALYTICS_REQUESTS,
    IDEMPOTENT_REPLAYS,
    INVARIANT_FAILURES,
    PORTFOLIO_CREATIONS,
    REVERSALS,
    SIMULATED_TRANSACTIONS,
    STALE_VALUATIONS,
    TRANSACTION_CONFLICTS,
    VALUATIONS,
)
from apps.api.src.portfolio.repositories import (
    PortfolioAccountRepository,
    PortfolioAuditRepository,
    PortfolioPositionRepository,
    PortfolioRepository,
    PortfolioTransactionRepository,
    PortfolioValuationRepository,
)
from apps.api.src.portfolio.schemas import (
    AllocationItem,
    AnalyticsResponse,
    AuditEventResponse,
    BenchmarkAnalytics,
    CashBalance,
    EffectivePortfolioPermissions,
    HistoryPoint,
    HistoryResponse,
    HoldingResponse,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
    ReversalCreate,
    StatisticalAnalytics,
    TransactionCreate,
    TransactionResponse,
    ValuationResponse,
    ValuationSnapshotResponse,
    ValuedHolding,
)
from packages.database.atlas_database.models.enums import (
    AccountStatus,
    AccountType,
    LedgerAccountType,
    LedgerTransactionStatus,
    ListingStatus,
    MarketDataStatus,
    PortfolioAccountRole,
    PortfolioStatus,
    PortfolioTransactionStatus,
    PortfolioTransactionType,
    PositionStatus,
    ValuationCompleteness,
)
from packages.database.atlas_database.models.identity import User
from packages.database.atlas_database.models.instruments import HistoricalCandle
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
)

ZERO = Decimal("0")
DECIMAL_QUANTUM = Decimal("0.000000000000000001")
MAX_ABSOLUTE_VALUE = Decimal("99999999999999999999")
MAX_EFFECTIVE_FUTURE = timedelta(minutes=5)
SUPPORTED_CURRENCIES = frozenset(
    {
        "AUD",
        "CAD",
        "CHF",
        "CNY",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "INR",
        "JPY",
        "NOK",
        "NZD",
        "PLN",
        "SEK",
        "SGD",
        "USD",
        "ZAR",
    }
)


def financial_error(
    code: str,
    message: str,
    *,
    status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT,
) -> ApplicationError:
    INVARIANT_FAILURES.labels(code=code).inc()
    return ApplicationError(message, code=code, status_code=status_code)


def portfolio_not_found() -> ApplicationError:
    return ApplicationError(
        "The simulated portfolio was not found.",
        code="portfolio_not_found",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value))


def quantize(value: Decimal) -> Decimal:
    if abs(value) > MAX_ABSOLUTE_VALUE:
        raise financial_error("invalid_transaction_amount", "The amount exceeds the safe limit.")
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def portfolio_response(portfolio: Portfolio) -> PortfolioResponse:
    return PortfolioResponse.model_validate(portfolio, from_attributes=True)


def transaction_response(transaction: PortfolioTransaction) -> TransactionResponse:
    return TransactionResponse.model_validate(transaction, from_attributes=True)


def snapshot_response(snapshot: PortfolioValuationSnapshot) -> ValuationSnapshotResponse:
    return ValuationSnapshotResponse.model_validate(snapshot, from_attributes=True)


class PortfolioAuthorisation:
    def __init__(self) -> None:
        self.organisations = OrganisationService()
        self.authorisation = AuthorisationService()
        self.portfolios = PortfolioRepository()

    async def tenant(
        self,
        session: AsyncSession,
        actor: User,
        tenant_id: UUID,
        permission: Permission,
    ) -> object:
        tenant, membership = await self.organisations.require_membership(
            session, tenant_id, actor.id
        )
        self.authorisation.require_permission(membership.role, permission)
        return tenant

    async def portfolio(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        permission: Permission,
        *,
        for_update: bool = False,
    ) -> Portfolio:
        portfolio = await self.portfolios.by_id(session, portfolio_id, for_update=for_update)
        if portfolio is None:
            raise portfolio_not_found()
        try:
            _tenant, membership = await self.organisations.require_membership(
                session, portfolio.tenant_id, actor.id
            )
        except ApplicationError as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                raise portfolio_not_found() from exc
            raise
        self.authorisation.require_permission(membership.role, permission)
        return portfolio

    async def effective_permissions(
        self, session: AsyncSession, actor: User, portfolio: Portfolio
    ) -> EffectivePortfolioPermissions:
        _tenant, membership = await self.organisations.require_membership(
            session, portfolio.tenant_id, actor.id
        )

        def can(permission: Permission) -> bool:
            return self.authorisation.can(membership.role, permission)

        return EffectivePortfolioPermissions(
            can_read=can(Permission.PORTFOLIO_READ),
            can_update=can(Permission.PORTFOLIO_UPDATE),
            can_archive=can(Permission.PORTFOLIO_ARCHIVE),
            can_create_transaction=can(Permission.PORTFOLIO_TRANSACTION_CREATE),
            can_read_transactions=can(Permission.PORTFOLIO_TRANSACTION_READ),
            can_read_analytics=can(Permission.PORTFOLIO_ANALYTICS_READ),
            can_read_audit=can(Permission.PORTFOLIO_AUDIT_READ),
        )


class PortfolioService:
    def __init__(self) -> None:
        self.repository = PortfolioRepository()
        self.authorisation = PortfolioAuthorisation()

    async def list(
        self,
        session: AsyncSession,
        actor: User,
        tenant_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[PortfolioResponse]:
        await self.authorisation.tenant(session, actor, tenant_id, Permission.PORTFOLIO_READ)
        return [
            portfolio_response(item)
            for item in await self.repository.list(session, tenant_id, offset=offset, limit=limit)
        ]

    async def get(
        self, session: AsyncSession, actor: User, portfolio_id: UUID
    ) -> PortfolioResponse:
        portfolio = await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_READ
        )
        return portfolio_response(portfolio)

    async def create(
        self,
        session: AsyncSession,
        actor: User,
        data: PortfolioCreate,
        request_id: str | None,
    ) -> PortfolioResponse:
        self._require_supported_currency(data.base_currency)
        await self.authorisation.tenant(session, actor, data.tenant_id, Permission.PORTFOLIO_CREATE)
        account = InvestmentAccount(
            tenant_id=data.tenant_id,
            owner_user_id=actor.id,
            name=f"{data.name} simulated account",
            account_type=AccountType.CASH,
            status=AccountStatus.ACTIVE,
            base_currency=data.base_currency,
            external_provider=None,
            external_account_id=None,
        )
        session.add(account)
        await session.flush()
        portfolio = Portfolio(
            tenant_id=data.tenant_id,
            investment_account_id=account.id,
            name=data.name,
            description=data.description,
            base_currency=data.base_currency,
            status=PortfolioStatus.ACTIVE,
            created_by_user_id=actor.id,
            version=1,
        )
        session.add(portfolio)
        await session.flush()
        self._create_accounts(session, portfolio, portfolio.base_currency)
        self._audit(
            session,
            portfolio,
            actor,
            "portfolio.created",
            request_id,
            portfolio.id,
        )
        await self._commit(session, "portfolio_conflict")
        await session.refresh(portfolio)
        PORTFOLIO_CREATIONS.inc()
        return portfolio_response(portfolio)

    async def update(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        data: PortfolioUpdate,
        request_id: str | None,
    ) -> PortfolioResponse:
        portfolio = await self.authorisation.portfolio(
            session,
            actor,
            portfolio_id,
            Permission.PORTFOLIO_UPDATE,
            for_update=True,
        )
        self.require_active(portfolio)
        if portfolio.version != data.version:
            raise financial_error(
                "concurrency_conflict",
                "The simulated portfolio changed; reload before trying again.",
                status_code=status.HTTP_409_CONFLICT,
            )
        changes = data.model_dump(exclude_unset=True, exclude={"version"})
        benchmark_id = changes.get("benchmark_listing_id")
        if benchmark_id is not None:
            from apps.api.src.market.repositories import MarketRepository

            benchmark = await MarketRepository().listing(session, benchmark_id)
            if benchmark is None or benchmark.listing_status != ListingStatus.ACTIVE:
                raise ApplicationError(
                    "The benchmark listing was not found.",
                    code="listing_not_found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        for field, value in changes.items():
            setattr(portfolio, field, value)
        portfolio.version += 1
        self._audit(
            session,
            portfolio,
            actor,
            "portfolio.benchmark.changed"
            if set(changes) == {"benchmark_listing_id"}
            else "portfolio.updated",
            request_id,
            portfolio.id,
        )
        await self._commit(session, "portfolio_conflict")
        await session.refresh(portfolio)
        return portfolio_response(portfolio)

    async def archive(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        request_id: str | None,
    ) -> PortfolioResponse:
        portfolio = await self.authorisation.portfolio(
            session,
            actor,
            portfolio_id,
            Permission.PORTFOLIO_ARCHIVE,
            for_update=True,
        )
        self.require_active(portfolio)
        portfolio.status = PortfolioStatus.ARCHIVED
        portfolio.archived_at = datetime.now(UTC)
        portfolio.version += 1
        self._audit(session, portfolio, actor, "portfolio.archived", request_id, portfolio.id)
        await session.commit()
        await session.refresh(portfolio)
        return portfolio_response(portfolio)

    @staticmethod
    def require_active(portfolio: Portfolio) -> None:
        if portfolio.status != PortfolioStatus.ACTIVE:
            raise ApplicationError(
                "Archived simulated portfolios cannot receive financial mutations.",
                code="portfolio_archived",
                status_code=status.HTTP_409_CONFLICT,
            )

    @staticmethod
    def _create_accounts(session: AsyncSession, portfolio: Portfolio, currency: str) -> None:
        account_types = {
            PortfolioAccountRole.VIRTUAL_CASH: LedgerAccountType.ASSET,
            PortfolioAccountRole.SIMULATED_INVESTMENT_COST: LedgerAccountType.ASSET,
            PortfolioAccountRole.SIMULATED_CAPITAL: LedgerAccountType.EQUITY,
            PortfolioAccountRole.SIMULATED_DIVIDEND_INCOME: LedgerAccountType.REVENUE,
            PortfolioAccountRole.SIMULATED_FEE_EXPENSE: LedgerAccountType.EXPENSE,
            PortfolioAccountRole.SIMULATED_REALISED_GAIN: LedgerAccountType.REVENUE,
            PortfolioAccountRole.SIMULATED_REALISED_LOSS: LedgerAccountType.EXPENSE,
        }
        role_codes = {
            PortfolioAccountRole.VIRTUAL_CASH: "cash",
            PortfolioAccountRole.SIMULATED_INVESTMENT_COST: "cost",
            PortfolioAccountRole.SIMULATED_CAPITAL: "capital",
            PortfolioAccountRole.SIMULATED_DIVIDEND_INCOME: "dividend",
            PortfolioAccountRole.SIMULATED_FEE_EXPENSE: "fee",
            PortfolioAccountRole.SIMULATED_REALISED_GAIN: "gain",
            PortfolioAccountRole.SIMULATED_REALISED_LOSS: "loss",
        }
        for role, account_type in account_types.items():
            ledger = LedgerAccount(
                id=uuid4(),
                tenant_id=portfolio.tenant_id,
                code=f"sim:{portfolio.id}:{currency}:{role_codes[role]}",
                name=role.value.replace("_", " ").title(),
                account_type=account_type,
                currency=currency,
            )
            session.add(ledger)
            session.add(
                PortfolioAccount(
                    tenant_id=portfolio.tenant_id,
                    portfolio_id=portfolio.id,
                    ledger_account_id=ledger.id,
                    account_role=role,
                    currency=currency,
                    is_active=True,
                )
            )

    @staticmethod
    def _require_supported_currency(currency: str) -> None:
        if currency not in SUPPORTED_CURRENCIES:
            raise financial_error(
                "unsupported_currency",
                "The currency is not supported by the simulated accounting scope.",
            )

    @staticmethod
    def _audit(
        session: AsyncSession,
        portfolio: Portfolio,
        actor: User,
        event_type: str,
        request_id: str | None,
        target_id: UUID | None,
        *,
        operation_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        session.add(
            PortfolioAuditEvent(
                tenant_id=portfolio.tenant_id,
                portfolio_id=portfolio.id,
                event_type=event_type,
                request_id=request_id,
                operation_id=operation_id,
                actor_user_id=actor.id,
                target_id=target_id,
                event_metadata=metadata or {},
            )
        )

    @staticmethod
    async def _commit(session: AsyncSession, code: str) -> None:
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise ApplicationError(
                "The requested simulated portfolio change conflicts with existing data.",
                code=code,
                status_code=status.HTTP_409_CONFLICT,
            ) from exc


class TransactionPostingService:
    def __init__(self) -> None:
        self.authorisation = PortfolioAuthorisation()
        self.accounts = PortfolioAccountRepository()
        self.transactions = PortfolioTransactionRepository()
        self.positions = PortfolioPositionRepository()

    async def post(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        data: TransactionCreate,
        idempotency_key: str,
        request_id: str | None,
    ) -> TransactionResponse:
        portfolio = await self.authorisation.portfolio(
            session,
            actor,
            portfolio_id,
            Permission.PORTFOLIO_TRANSACTION_CREATE,
            for_update=True,
        )
        PortfolioService.require_active(portfolio)
        fingerprint = self._fingerprint(data)
        existing = await self.transactions.by_idempotency_key(
            session, portfolio.id, idempotency_key
        )
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                TRANSACTION_CONFLICTS.labels(code="idempotency_conflict").inc()
                raise ApplicationError(
                    "The idempotency key was already used with different data.",
                    code="idempotency_conflict",
                    status_code=status.HTTP_409_CONFLICT,
                )
            IDEMPOTENT_REPLAYS.labels(operation="transaction").inc()
            return transaction_response(existing)
        self._validate_common(portfolio, data)
        account_rows = await self.accounts.list(session, portfolio.id)
        accounts = {
            account.account_role: account
            for account in account_rows
            if account.currency == data.currency
        }
        if not accounts:
            PortfolioService._create_accounts(session, portfolio, data.currency)
            await session.flush()
            accounts = {
                account.account_role: account
                for account in await self.accounts.list(session, portfolio.id)
                if account.currency == data.currency
            }
        if len(accounts) != len(PortfolioAccountRole):
            raise financial_error(
                "accounting_configuration_invalid",
                "The simulated accounting configuration is incomplete.",
                status_code=status.HTTP_409_CONFLICT,
            )
        listing = None
        position = None
        if data.listing_id is not None:
            from apps.api.src.market.repositories import MarketRepository

            listing = await MarketRepository().listing(session, data.listing_id)
            if (
                listing is None
                or listing.listing_status != ListingStatus.ACTIVE
                or not listing.active
            ):
                raise ApplicationError(
                    "The listing was not found.",
                    code="listing_not_found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            if listing.quote_currency != data.currency:
                raise financial_error(
                    "currency_mismatch",
                    "Listing and transaction currencies differ; Atlas does not convert silently.",
                )
            position = await self.positions.by_listing(
                session, portfolio.id, listing.id, for_update=True
            )
        effects = await self._calculate_effects(session, portfolio, position, data)
        sequence = await self.transactions.next_sequence(session, portfolio.id)
        now = datetime.now(UTC)
        ledger = LedgerTransaction(
            tenant_id=portfolio.tenant_id,
            idempotency_key=f"portfolio:{portfolio.id}:{idempotency_key}",
            external_reference=data.external_reference,
            description=f"Simulated {data.transaction_type.value}",
            effective_at=data.effective_at,
            status=LedgerTransactionStatus.POSTED,
        )
        session.add(ledger)
        await session.flush()
        transaction = PortfolioTransaction(
            tenant_id=portfolio.tenant_id,
            portfolio_id=portfolio.id,
            sequence=sequence,
            transaction_type=data.transaction_type,
            status=PortfolioTransactionStatus.POSTED,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            external_reference=data.external_reference,
            listing_id=data.listing_id,
            currency=data.currency,
            quantity=effects["stored_quantity"],
            unit_price=data.unit_price,
            gross_amount=effects["gross"],
            fee_amount=data.fee_amount,
            net_amount=effects["net"],
            position_quantity_delta=effects["quantity_delta"],
            position_cost_delta=effects["cost_delta"],
            realised_pnl_delta=effects["realised_delta"],
            effective_at=data.effective_at,
            recorded_at=now,
            created_by_user_id=actor.id,
            ledger_transaction_id=ledger.id,
            reason=data.reason,
            transaction_metadata=data.metadata,
            is_simulated=True,
        )
        session.add(transaction)
        self._post_entries(session, portfolio, ledger, accounts, data, effects)
        position_affecting = data.transaction_type in {
            PortfolioTransactionType.SIMULATED_BUY,
            PortfolioTransactionType.SIMULATED_SELL,
            PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT,
        }
        if listing is not None and position_affecting:
            self._apply_position(
                session,
                portfolio,
                listing.id,
                data.currency,
                position,
                sequence,
                cast(Decimal, effects["quantity_delta"]),
                cast(Decimal, effects["cost_delta"]),
                cast(Decimal, effects["realised_delta"]),
            )
        PortfolioService._audit(
            session,
            portfolio,
            actor,
            "portfolio.transaction.posted",
            request_id,
            transaction.id,
            operation_id=idempotency_key,
            metadata={"transaction_type": data.transaction_type.value},
        )
        if data.transaction_type in {
            PortfolioTransactionType.VIRTUAL_DEPOSIT,
            PortfolioTransactionType.VIRTUAL_WITHDRAWAL,
            PortfolioTransactionType.SIMULATED_DIVIDEND,
            PortfolioTransactionType.SIMULATED_FEE,
            PortfolioTransactionType.SIMULATED_BUY,
            PortfolioTransactionType.SIMULATED_SELL,
        }:
            PortfolioService._audit(
                session,
                portfolio,
                actor,
                "portfolio.virtual_cash.changed",
                request_id,
                transaction.id,
                operation_id=idempotency_key,
            )
        if listing is not None and position_affecting:
            PortfolioService._audit(
                session,
                portfolio,
                actor,
                "portfolio.position.changed",
                request_id,
                transaction.id,
                operation_id=idempotency_key,
            )
        await self._commit(session)
        await session.refresh(transaction)
        SIMULATED_TRANSACTIONS.labels(transaction_type=data.transaction_type.value).inc()
        return transaction_response(transaction)

    async def reverse(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        transaction_id: UUID,
        data: ReversalCreate,
        idempotency_key: str,
        request_id: str | None,
    ) -> TransactionResponse:
        portfolio = await self.authorisation.portfolio(
            session,
            actor,
            portfolio_id,
            Permission.PORTFOLIO_TRANSACTION_CREATE,
            for_update=True,
        )
        PortfolioService.require_active(portfolio)
        fingerprint = sha256(f"{transaction_id}|{data.model_dump_json()}".encode()).hexdigest()
        replay = await self.transactions.by_idempotency_key(session, portfolio.id, idempotency_key)
        if replay is not None:
            if replay.request_fingerprint != fingerprint:
                raise ApplicationError(
                    "The idempotency key was already used with different data.",
                    code="idempotency_conflict",
                    status_code=status.HTTP_409_CONFLICT,
                )
            IDEMPOTENT_REPLAYS.labels(operation="reversal").inc()
            return transaction_response(replay)
        original = await self.transactions.by_id(session, portfolio.id, transaction_id)
        if original is None:
            raise portfolio_not_found()
        if original.status == PortfolioTransactionStatus.REVERSED:
            raise ApplicationError(
                "The simulated transaction has already been reversed.",
                code="transaction_already_reversed",
                status_code=status.HTTP_409_CONFLICT,
            )
        if original.transaction_type == PortfolioTransactionType.REVERSAL:
            raise ApplicationError(
                "A compensating reversal cannot itself be reversed.",
                code="reversal_failed",
                status_code=status.HTTP_409_CONFLICT,
            )
        position = None
        if original.listing_id is not None:
            position = await self.positions.by_listing(
                session, portfolio.id, original.listing_id, for_update=True
            )
            new_quantity = (
                position.quantity if position else ZERO
            ) - original.position_quantity_delta
            new_cost = (position.cost_basis if position else ZERO) - original.position_cost_delta
            if new_quantity < ZERO or new_cost < ZERO:
                raise financial_error(
                    "reversal_failed",
                    "Later simulated activity prevents a safe compensating reversal.",
                    status_code=status.HTTP_409_CONFLICT,
                )
        ledger_original = await session.get(LedgerTransaction, original.ledger_transaction_id)
        if ledger_original is None:
            raise financial_error(
                "reversal_failed",
                "The original accounting journal is unavailable.",
                status_code=status.HTTP_409_CONFLICT,
            )
        await session.refresh(ledger_original, attribute_names=["entries"])
        sequence = await self.transactions.next_sequence(session, portfolio.id)
        ledger = LedgerTransaction(
            tenant_id=portfolio.tenant_id,
            idempotency_key=f"portfolio:{portfolio.id}:{idempotency_key}",
            description=f"Compensating reversal of simulated transaction {original.id}",
            effective_at=data.effective_at,
            status=LedgerTransactionStatus.POSTED,
            reversal_of_id=ledger_original.id,
        )
        session.add(ledger)
        await session.flush()
        for entry in ledger_original.entries:
            session.add(
                LedgerEntry(
                    tenant_id=portfolio.tenant_id,
                    transaction_id=ledger.id,
                    ledger_account_id=entry.ledger_account_id,
                    amount=-entry.amount,
                    memo="Compensating simulated reversal",
                )
            )
        if not ledger_original.entries:
            ledger.status = LedgerTransactionStatus.DRAFT
        reversal = PortfolioTransaction(
            tenant_id=portfolio.tenant_id,
            portfolio_id=portfolio.id,
            sequence=sequence,
            transaction_type=PortfolioTransactionType.REVERSAL,
            status=PortfolioTransactionStatus.POSTED,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            listing_id=original.listing_id,
            currency=original.currency,
            quantity=original.quantity,
            unit_price=original.unit_price,
            gross_amount=original.gross_amount,
            fee_amount=original.fee_amount,
            net_amount=original.net_amount,
            position_quantity_delta=-original.position_quantity_delta,
            position_cost_delta=-original.position_cost_delta,
            realised_pnl_delta=-original.realised_pnl_delta,
            effective_at=data.effective_at,
            recorded_at=datetime.now(UTC),
            created_by_user_id=actor.id,
            reversal_of_transaction_id=original.id,
            ledger_transaction_id=ledger.id,
            reason=data.reason,
            transaction_metadata={"original_transaction_type": original.transaction_type.value},
            is_simulated=True,
        )
        session.add(reversal)
        await session.flush()
        original.status = PortfolioTransactionStatus.REVERSED
        ledger_original.status = LedgerTransactionStatus.REVERSED
        if original.listing_id is not None:
            self._apply_position(
                session,
                portfolio,
                original.listing_id,
                original.currency,
                position,
                sequence,
                -original.position_quantity_delta,
                -original.position_cost_delta,
                -original.realised_pnl_delta,
            )
        PortfolioService._audit(
            session,
            portfolio,
            actor,
            "portfolio.transaction.reversed",
            request_id,
            reversal.id,
            operation_id=idempotency_key,
            metadata={"original_transaction_id": str(original.id)},
        )
        await self._commit(session)
        await session.refresh(reversal)
        REVERSALS.inc()
        return transaction_response(reversal)

    @staticmethod
    def _fingerprint(data: TransactionCreate) -> str:
        return sha256(data.model_dump_json().encode()).hexdigest()

    @staticmethod
    def _validate_common(portfolio: Portfolio, data: TransactionCreate) -> None:
        del portfolio
        PortfolioService._require_supported_currency(data.currency)
        if data.effective_at > datetime.now(UTC) + MAX_EFFECTIVE_FUTURE:
            raise financial_error(
                "invalid_transaction_timestamp",
                "The simulated transaction time is too far in the future.",
            )
        if data.fee_amount > ZERO and data.transaction_type not in {
            PortfolioTransactionType.SIMULATED_BUY,
            PortfolioTransactionType.SIMULATED_SELL,
        }:
            raise financial_error(
                "invalid_transaction_amount",
                "Fees on this transaction must be recorded as a separate simulated fee.",
            )

    async def _calculate_effects(
        self,
        session: AsyncSession,
        portfolio: Portfolio,
        position: PortfolioPosition | None,
        data: TransactionCreate,
    ) -> dict[str, Decimal | None]:
        transaction_type = data.transaction_type
        amount = quantize(data.amount or ZERO)
        fee = quantize(data.fee_amount)
        quantity = quantize(data.quantity or ZERO)
        unit_price = quantize(data.unit_price or ZERO)
        cash = decimal_value(await self.accounts.cash_balance(session, portfolio.id, data.currency))
        gross = amount
        net = amount
        quantity_delta = ZERO
        cost_delta = ZERO
        realised_delta = ZERO
        stored_quantity: Decimal | None = data.quantity

        if transaction_type in {
            PortfolioTransactionType.SIMULATED_BUY,
            PortfolioTransactionType.SIMULATED_SELL,
        }:
            gross = quantize(quantity * unit_price)
        if transaction_type == PortfolioTransactionType.VIRTUAL_DEPOSIT:
            pass
        elif transaction_type == PortfolioTransactionType.VIRTUAL_WITHDRAWAL:
            if cash < amount:
                raise financial_error(
                    "insufficient_virtual_cash",
                    "The simulated portfolio has insufficient virtual cash.",
                    status_code=status.HTTP_409_CONFLICT,
                )
        elif transaction_type == PortfolioTransactionType.SIMULATED_BUY:
            net = quantize(gross + fee)
            if cash < net:
                raise financial_error(
                    "insufficient_virtual_cash",
                    "The simulated portfolio has insufficient virtual cash.",
                    status_code=status.HTTP_409_CONFLICT,
                )
            quantity_delta = quantity
            # Milestone 4 expenses simulated fees separately; weighted-average cost
            # therefore includes gross simulated acquisition value, not the fee.
            cost_delta = gross
        elif transaction_type == PortfolioTransactionType.SIMULATED_SELL:
            if fee > gross:
                raise financial_error(
                    "invalid_transaction_amount",
                    "A simulated fee cannot exceed gross simulated proceeds.",
                )
            available = position.quantity if position else ZERO
            if available < quantity:
                raise financial_error(
                    "insufficient_simulated_quantity",
                    "The simulated portfolio has insufficient quantity.",
                    status_code=status.HTTP_409_CONFLICT,
                )
            average = position.average_cost_per_unit if position else ZERO
            removed_cost = quantize(average * quantity)
            net = quantize(gross - fee)
            quantity_delta = -quantity
            cost_delta = -removed_cost
            realised_delta = quantize(net - removed_cost)
        elif transaction_type == PortfolioTransactionType.SIMULATED_DIVIDEND:
            net = amount
        elif transaction_type == PortfolioTransactionType.SIMULATED_FEE:
            if cash < amount:
                raise financial_error(
                    "insufficient_virtual_cash",
                    "The simulated portfolio has insufficient virtual cash.",
                    status_code=status.HTTP_409_CONFLICT,
                )
        elif transaction_type == PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT:
            if position is None or position.quantity <= ZERO:
                raise financial_error(
                    "insufficient_simulated_quantity",
                    "A split adjustment requires an open simulated holding.",
                    status_code=status.HTTP_409_CONFLICT,
                )
            ratio = quantize(data.split_ratio or ZERO)
            new_quantity = quantize(position.quantity * ratio)
            quantity_delta = quantize(new_quantity - position.quantity)
            gross = ZERO
            net = ZERO
            stored_quantity = ratio
        return {
            "gross": gross,
            "net": net,
            "quantity_delta": quantity_delta,
            "cost_delta": cost_delta,
            "realised_delta": realised_delta,
            "stored_quantity": stored_quantity,
        }

    @staticmethod
    def _entry(
        session: AsyncSession,
        portfolio: Portfolio,
        ledger: LedgerTransaction,
        account: PortfolioAccount,
        amount: Decimal,
        memo: str,
    ) -> None:
        if amount == ZERO:
            return
        session.add(
            LedgerEntry(
                tenant_id=portfolio.tenant_id,
                transaction_id=ledger.id,
                ledger_account_id=account.ledger_account_id,
                amount=amount,
                memo=memo,
            )
        )

    def _post_entries(
        self,
        session: AsyncSession,
        portfolio: Portfolio,
        ledger: LedgerTransaction,
        accounts: dict[PortfolioAccountRole, PortfolioAccount],
        data: TransactionCreate,
        effects: dict[str, Decimal | None],
    ) -> None:
        gross = cast(Decimal, effects["gross"])
        net = cast(Decimal, effects["net"])
        cost_delta = cast(Decimal, effects["cost_delta"])
        realised = cast(Decimal, effects["realised_delta"])
        fee = data.fee_amount
        cash = accounts[PortfolioAccountRole.VIRTUAL_CASH]
        cost = accounts[PortfolioAccountRole.SIMULATED_INVESTMENT_COST]
        capital = accounts[PortfolioAccountRole.SIMULATED_CAPITAL]
        dividend = accounts[PortfolioAccountRole.SIMULATED_DIVIDEND_INCOME]
        expense = accounts[PortfolioAccountRole.SIMULATED_FEE_EXPENSE]
        gain = accounts[PortfolioAccountRole.SIMULATED_REALISED_GAIN]
        loss = accounts[PortfolioAccountRole.SIMULATED_REALISED_LOSS]
        memo = f"Simulated {data.transaction_type.value}"
        if data.transaction_type == PortfolioTransactionType.VIRTUAL_DEPOSIT:
            self._entry(session, portfolio, ledger, cash, gross, memo)
            self._entry(session, portfolio, ledger, capital, -gross, memo)
        elif data.transaction_type == PortfolioTransactionType.VIRTUAL_WITHDRAWAL:
            self._entry(session, portfolio, ledger, cash, -gross, memo)
            self._entry(session, portfolio, ledger, capital, gross, memo)
        elif data.transaction_type == PortfolioTransactionType.SIMULATED_BUY:
            self._entry(session, portfolio, ledger, cost, gross, memo)
            self._entry(session, portfolio, ledger, expense, fee, memo)
            self._entry(session, portfolio, ledger, cash, -net, memo)
        elif data.transaction_type == PortfolioTransactionType.SIMULATED_SELL:
            self._entry(session, portfolio, ledger, cash, net, memo)
            self._entry(session, portfolio, ledger, cost, cost_delta, memo)
            self._entry(session, portfolio, ledger, expense, fee, memo)
            ledger_realised = realised + fee
            if ledger_realised > ZERO:
                self._entry(session, portfolio, ledger, gain, -ledger_realised, memo)
            elif ledger_realised < ZERO:
                self._entry(session, portfolio, ledger, loss, -ledger_realised, memo)
        elif data.transaction_type == PortfolioTransactionType.SIMULATED_DIVIDEND:
            self._entry(session, portfolio, ledger, cash, gross, memo)
            self._entry(session, portfolio, ledger, dividend, -gross, memo)
        elif data.transaction_type == PortfolioTransactionType.SIMULATED_FEE:
            self._entry(session, portfolio, ledger, cash, -gross, memo)
            self._entry(session, portfolio, ledger, expense, gross, memo)
        elif data.transaction_type == PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT:
            # A split changes units, not monetary balances. A zero-value journal is invalid,
            # so no ledger journal group is persisted for this non-monetary event.
            ledger.status = LedgerTransactionStatus.DRAFT

    @staticmethod
    def _apply_position(
        session: AsyncSession,
        portfolio: Portfolio,
        listing_id: UUID,
        currency: str,
        position: PortfolioPosition | None,
        sequence: int,
        quantity_delta: Decimal,
        cost_delta: Decimal,
        realised_delta: Decimal,
    ) -> None:
        if position is None:
            position = PortfolioPosition(
                tenant_id=portfolio.tenant_id,
                portfolio_id=portfolio.id,
                listing_id=listing_id,
                currency=currency,
                quantity=ZERO,
                average_cost_per_unit=ZERO,
                cost_basis=ZERO,
                realised_pnl=ZERO,
                position_status=PositionStatus.CLOSED,
                last_transaction_sequence=sequence,
            )
            session.add(position)
        new_quantity = quantize(position.quantity + quantity_delta)
        new_cost = quantize(position.cost_basis + cost_delta)
        if new_quantity < ZERO or new_cost < ZERO:
            raise financial_error(
                "accounting_invariant_failed",
                "The simulated position would violate long-only accounting.",
                status_code=status.HTTP_409_CONFLICT,
            )
        position.quantity = new_quantity
        position.cost_basis = new_cost
        position.average_cost_per_unit = (
            quantize(new_cost / new_quantity) if new_quantity > ZERO else ZERO
        )
        position.realised_pnl = quantize(position.realised_pnl + realised_delta)
        position.position_status = (
            PositionStatus.OPEN if new_quantity > ZERO else PositionStatus.CLOSED
        )
        position.last_transaction_sequence = sequence

    @staticmethod
    async def _commit(session: AsyncSession) -> None:
        try:
            await session.commit()
        except (IntegrityError, DBAPIError) as exc:
            await session.rollback()
            TRANSACTION_CONFLICTS.labels(code="concurrency_conflict").inc()
            raise ApplicationError(
                "The simulated transaction conflicted with another request.",
                code="concurrency_conflict",
                status_code=status.HTTP_409_CONFLICT,
            ) from exc


class PortfolioQueryService:
    def __init__(self, market: MarketService | None = None) -> None:
        self.authorisation = PortfolioAuthorisation()
        self.accounts = PortfolioAccountRepository()
        self.transactions = PortfolioTransactionRepository()
        self.positions = PortfolioPositionRepository()
        self.valuations = PortfolioValuationRepository()
        self.audits = PortfolioAuditRepository()
        self.market = market

    async def transactions_list(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[TransactionResponse]:
        await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_TRANSACTION_READ
        )
        return [
            transaction_response(item)
            for item in await self.transactions.list(
                session, portfolio_id, offset=offset, limit=limit
            )
        ]

    async def transaction(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        transaction_id: UUID,
    ) -> TransactionResponse:
        await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_TRANSACTION_READ
        )
        item = await self.transactions.by_id(session, portfolio_id, transaction_id)
        if item is None:
            raise portfolio_not_found()
        return transaction_response(item)

    async def holdings(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
    ) -> list[HoldingResponse]:
        await self.authorisation.portfolio(session, actor, portfolio_id, Permission.PORTFOLIO_READ)
        rows = await self.positions.list(session, portfolio_id)
        return [
            HoldingResponse(
                listing_id=position.listing_id,
                instrument_id=listing.instrument_id,
                symbol=listing.ticker,
                exchange=exchange.mic,
                asset_class=instrument.asset_class,
                currency=position.currency,
                quantity=position.quantity,
                average_cost_per_unit=position.average_cost_per_unit,
                cost_basis=position.cost_basis,
                realised_simulated_pnl=position.realised_pnl,
                position_status=position.position_status,
            )
            for position, listing, instrument, exchange in rows
        ]

    async def valuation(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
    ) -> ValuationResponse:
        portfolio = await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_ANALYTICS_READ
        )
        rows = await self.positions.list(session, portfolio_id)
        cash_rows = await self.accounts.cash_balances(session, portfolio.id)
        cash_by_currency = {currency: decimal_value(amount) for currency, amount in cash_rows}
        positions: list[ValuedHolding] = []
        subtotals: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
        for currency, amount in cash_by_currency.items():
            subtotals[currency] += amount
        missing: list[UUID] = []
        stale: list[UUID] = []
        unavailable: list[UUID] = []
        statuses: defaultdict[str, int] = defaultdict(int)
        sources: set[str] = set()
        realised_total = ZERO
        for position, listing, instrument, exchange in rows:
            quote = None
            if self.market is not None:
                try:
                    quote = await self.market.quote(session, listing.id)
                except ApplicationError:
                    quote = None
            price = quote.price if quote else None
            market_value = (
                quantize(position.quantity * price)
                if price is not None and position.quantity > ZERO
                else None
            )
            unrealised = (
                quantize(market_value - position.cost_basis) if market_value is not None else None
            )
            data_status = quote.data_status if quote else MarketDataStatus.UNAVAILABLE
            is_stale = bool(quote and quote.is_stale)
            if price is None:
                missing.append(listing.id)
                unavailable.append(listing.id)
            elif is_stale or data_status == MarketDataStatus.STALE:
                stale.append(listing.id)
            if market_value is not None:
                subtotals[position.currency] += market_value
            statuses[data_status.value] += 1
            if quote:
                sources.add(f"{quote.provider}:{quote.data_status.value}")
            realised_total += position.realised_pnl
            positions.append(
                ValuedHolding(
                    listing_id=listing.id,
                    instrument_id=instrument.id,
                    symbol=listing.ticker,
                    exchange=exchange.mic,
                    asset_class=instrument.asset_class,
                    currency=position.currency,
                    quantity=position.quantity,
                    average_cost_per_unit=position.average_cost_per_unit,
                    cost_basis=position.cost_basis,
                    realised_simulated_pnl=position.realised_pnl,
                    position_status=position.position_status,
                    latest_price=price,
                    market_value=market_value,
                    unrealised_simulated_pnl=unrealised,
                    provider=quote.provider if quote else None,
                    provider_timestamp=quote.provider_timestamp if quote else None,
                    received_at=quote.received_at if quote else None,
                    data_status=data_status,
                    is_stale=is_stale,
                    valuation_status=(
                        "missing" if price is None else "stale" if is_stale else data_status.value
                    ),
                )
            )
        unconverted = sorted(
            currency for currency in subtotals if currency != portfolio.base_currency
        )
        complete = not missing and not unconverted
        total = subtotals[portfolio.base_currency] if complete else None
        result = ValuationResponse(
            portfolio_id=portfolio.id,
            as_of=datetime.now(UTC),
            base_currency=portfolio.base_currency,
            virtual_cash_by_currency=[
                CashBalance(currency=currency, amount=amount)
                for currency, amount in sorted(cash_by_currency.items())
            ],
            positions=positions,
            subtotal_by_currency=dict(sorted(subtotals.items())),
            base_currency_total=total,
            completeness=(
                ValuationCompleteness.COMPLETE if complete else ValuationCompleteness.INCOMPLETE
            ),
            is_complete=complete,
            missing_listing_ids=missing,
            stale_listing_ids=stale,
            unavailable_listing_ids=unavailable,
            unconverted_currencies=unconverted,
            data_status_summary=dict(sorted(statuses.items())),
            source_summary=sorted(sources),
        )
        VALUATIONS.labels(completeness=result.completeness.value).inc()
        if stale:
            STALE_VALUATIONS.inc()
        return result

    async def create_snapshot(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        idempotency_key: str,
        request_id: str | None,
    ) -> ValuationSnapshotResponse:
        portfolio = await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_ANALYTICS_READ
        )
        existing = await self.valuations.by_idempotency_key(session, portfolio.id, idempotency_key)
        if existing is not None:
            IDEMPOTENT_REPLAYS.labels(operation="valuation_snapshot").inc()
            return snapshot_response(existing)
        valuation = await self.valuation(session, actor, portfolio_id)
        snapshot = PortfolioValuationSnapshot(
            tenant_id=portfolio.tenant_id,
            portfolio_id=portfolio.id,
            idempotency_key=idempotency_key,
            as_of=valuation.as_of,
            base_currency=portfolio.base_currency,
            base_currency_total=valuation.base_currency_total,
            completeness=valuation.completeness,
            created_by_user_id=actor.id,
            is_simulated=True,
        )
        session.add(snapshot)
        await session.flush()
        for line in valuation.positions:
            session.add(
                PortfolioValuationLine(
                    snapshot_id=snapshot.id,
                    listing_id=line.listing_id,
                    currency=line.currency,
                    quantity=line.quantity,
                    cost_basis=line.cost_basis,
                    latest_price=line.latest_price,
                    market_value=line.market_value,
                    unrealised_pnl=line.unrealised_simulated_pnl,
                    provider=line.provider,
                    provider_timestamp=line.provider_timestamp,
                    received_at=line.received_at,
                    data_status=line.data_status,
                    source_reference=(
                        f"{line.provider}:{line.provider_timestamp.isoformat()}"
                        if line.provider and line.provider_timestamp
                        else None
                    ),
                )
            )
        PortfolioService._audit(
            session,
            portfolio,
            actor,
            "portfolio.valuation.created",
            request_id,
            snapshot.id,
            operation_id=idempotency_key,
            metadata={"completeness": valuation.completeness.value},
        )
        await session.commit()
        await session.refresh(snapshot)
        return snapshot_response(snapshot)

    async def snapshot_list(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[ValuationSnapshotResponse]:
        await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_ANALYTICS_READ
        )
        return [
            snapshot_response(item)
            for item in await self.valuations.list(
                session, portfolio_id, offset=offset, limit=limit
            )
        ]

    async def snapshot(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        snapshot_id: UUID,
    ) -> ValuationSnapshotResponse:
        await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_ANALYTICS_READ
        )
        item = await self.valuations.by_id(session, portfolio_id, snapshot_id)
        if item is None:
            raise portfolio_not_found()
        return snapshot_response(item)

    async def analytics(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
    ) -> AnalyticsResponse:
        valuation = await self.valuation(session, actor, portfolio_id)
        total_by_currency = dict(valuation.subtotal_by_currency)
        allocation: list[AllocationItem] = []
        by_asset: defaultdict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
        for item in valuation.positions:
            if item.market_value is None:
                continue
            currency_total = total_by_currency.get(item.currency, ZERO)
            percentage = (
                quantize(item.market_value / currency_total * Decimal("100"))
                if currency_total > ZERO
                else None
            )
            allocation.append(
                AllocationItem(
                    label=f"{item.symbol} · {item.exchange}",
                    currency=item.currency,
                    value=item.market_value,
                    percentage=percentage,
                )
            )
            by_asset[(item.asset_class.value, item.currency)] += item.market_value
        asset_allocation = [
            AllocationItem(
                label=asset_class,
                currency=currency,
                value=value,
                percentage=(
                    quantize(value / total_by_currency[currency] * Decimal("100"))
                    if total_by_currency[currency] > ZERO
                    else None
                ),
            )
            for (asset_class, currency), value in sorted(by_asset.items())
        ]
        unrealised_values = [
            item.unrealised_simulated_pnl
            for item in valuation.positions
            if item.unrealised_simulated_pnl is not None
        ]
        ANALYTICS_REQUESTS.labels(metric="summary").inc()
        return AnalyticsResponse(
            portfolio_id=portfolio_id,
            as_of=valuation.as_of,
            total_value_by_currency=total_by_currency,
            virtual_cash_by_currency={
                item.currency: item.amount for item in valuation.virtual_cash_by_currency
            },
            allocation=sorted(allocation, key=lambda item: item.value, reverse=True),
            asset_class_allocation=asset_allocation,
            largest_positions=sorted(
                valuation.positions,
                key=lambda item: item.market_value or ZERO,
                reverse=True,
            )[:10],
            realised_simulated_pnl=sum(
                (item.realised_simulated_pnl for item in valuation.positions), ZERO
            ),
            unrealised_simulated_pnl=(
                sum(unrealised_values, ZERO)
                if len(unrealised_values) == len(valuation.positions)
                else None
            ),
            currency_exposure=total_by_currency,
            data_complete=valuation.is_complete,
        )

    async def history(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        start: datetime | None,
        end: datetime | None,
    ) -> HistoryResponse:
        portfolio = await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_ANALYTICS_READ
        )
        snapshots = await self.valuations.history(session, portfolio_id, start=start, end=end)
        first = (
            decimal_value(snapshots[0].base_currency_total)
            if snapshots and snapshots[0].base_currency_total is not None
            else None
        )
        points = [
            HistoryPoint(
                as_of=item.as_of,
                value=decimal_value(item.base_currency_total),
                percentage_change=(
                    quantize(
                        (decimal_value(item.base_currency_total) - first) / first * Decimal("100")
                    )
                    if first and first != ZERO
                    else None
                ),
            )
            for item in snapshots
            if item.base_currency_total is not None
        ]
        ANALYTICS_REQUESTS.labels(metric="history").inc()
        return HistoryResponse(
            portfolio_id=portfolio.id,
            currency=portfolio.base_currency,
            points=points,
        )

    async def statistic(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        metric: str,
        start: datetime | None,
        end: datetime | None,
    ) -> StatisticalAnalytics:
        history = await self.history(session, actor, portfolio_id, start, end)
        values = [point.value for point in history.points]
        result: Decimal | None = None
        if metric == "maximum_drawdown" and len(values) >= 2:
            peak = values[0]
            worst = ZERO
            for value in values:
                peak = max(peak, value)
                if peak > ZERO:
                    worst = min(worst, (value - peak) / peak)
            result = quantize(worst * Decimal("100"))
        elif metric == "volatility" and len(values) >= 3:
            returns = [
                (current / previous) - Decimal("1")
                for previous, current in pairwise(values)
                if previous != ZERO
            ]
            if len(returns) >= 2:
                mean = sum(returns, ZERO) / Decimal(len(returns))
                variance = sum(((item - mean) ** 2 for item in returns), ZERO) / Decimal(
                    len(returns) - 1
                )
                with localcontext() as context:
                    context.prec = 38
                    result = quantize(variance.sqrt() * Decimal("100"))
        ANALYTICS_REQUESTS.labels(metric=metric).inc()
        return StatisticalAnalytics(
            portfolio_id=portfolio_id,
            metric=metric,
            value=result,
            time_range_start=history.points[0].as_of if history.points else None,
            time_range_end=history.points[-1].as_of if history.points else None,
            observations=len(history.points),
        )

    async def benchmark(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        start: datetime | None,
        end: datetime | None,
    ) -> BenchmarkAnalytics:
        portfolio = await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_ANALYTICS_READ
        )
        history = await self.history(session, actor, portfolio_id, start, end)
        if portfolio.benchmark_listing_id is None:
            ANALYTICS_REQUESTS.labels(metric="benchmark").inc()
            return BenchmarkAnalytics(
                portfolio_id=portfolio.id,
                benchmark_listing_id=None,
                aligned_observations=0,
                portfolio_percentage_change=(
                    history.points[-1].percentage_change if history.points else None
                ),
                benchmark_percentage_change=None,
                status="benchmark_not_selected",
            )
        from apps.api.src.market.repositories import MarketRepository

        listing = await MarketRepository().listing(session, portfolio.benchmark_listing_id)
        if listing is None:
            raise ApplicationError(
                "The benchmark listing was not found.",
                code="listing_not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        candles = (
            await self.valuations.benchmark_candles(
                session,
                listing.id,
                history.points[0].as_of,
                history.points[-1].as_of,
            )
            if history.points
            else []
        )
        # Multiple providers may exist for a date. Provider choice remains server-side and
        # deterministic; the first ordered persisted observation wins.
        candle_by_date: dict[date, HistoricalCandle] = {}
        for candle in candles:
            candle_by_date.setdefault(candle.period_start.date(), candle)
        aligned = [
            (point, candle_by_date[point.as_of.date()])
            for point in history.points
            if point.as_of.date() in candle_by_date
        ]
        missing_dates = [
            point.as_of.date()
            for point in history.points
            if point.as_of.date() not in candle_by_date
        ]
        status_counts: defaultdict[str, int] = defaultdict(int)
        for _point, candle in aligned:
            status_counts[candle.data_status.value] += 1
        benchmark_change = None
        if len(aligned) >= 2:
            first_close = aligned[0][1].close
            last_close = aligned[-1][1].close
            if first_close != ZERO:
                benchmark_change = quantize(
                    (last_close - first_close) / first_close * Decimal("100")
                )
        ANALYTICS_REQUESTS.labels(metric="benchmark").inc()
        return BenchmarkAnalytics(
            portfolio_id=portfolio.id,
            benchmark_listing_id=listing.id,
            aligned_observations=len(aligned),
            portfolio_percentage_change=(
                history.points[-1].percentage_change if history.points else None
            ),
            benchmark_percentage_change=benchmark_change,
            status=(
                "complete"
                if len(aligned) >= 2 and not missing_dates
                else "incomplete"
                if aligned
                else "benchmark_data_unavailable"
            ),
            missing_dates=missing_dates,
            data_status_summary=dict(sorted(status_counts.items())),
        )

    async def audit_events(
        self,
        session: AsyncSession,
        actor: User,
        portfolio_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[AuditEventResponse]:
        await self.authorisation.portfolio(
            session, actor, portfolio_id, Permission.PORTFOLIO_AUDIT_READ
        )
        return [
            AuditEventResponse.model_validate(item, from_attributes=True)
            for item in await self.audits.list(session, portfolio_id, offset=offset, limit=limit)
        ]
