from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.api.src.identity.authorization import AuthorisationService, Permission
from apps.api.src.main import app
from apps.api.src.portfolio.schemas import PortfolioCreate, TransactionCreate
from apps.api.src.portfolio.services import quantize
from packages.database.atlas_database.models.enums import (
    MembershipRole,
    PortfolioTransactionType,
)


def test_portfolio_permission_matrix_is_central_and_least_privilege() -> None:
    authorisation = AuthorisationService()
    assert authorisation.can(MembershipRole.OWNER, Permission.PORTFOLIO_AUDIT_READ)
    assert authorisation.can(MembershipRole.ADMIN, Permission.PORTFOLIO_ARCHIVE)
    assert authorisation.can(MembershipRole.MEMBER, Permission.PORTFOLIO_TRANSACTION_CREATE)
    assert not authorisation.can(MembershipRole.MEMBER, Permission.PORTFOLIO_ARCHIVE)
    assert authorisation.can(MembershipRole.VIEWER, Permission.PORTFOLIO_ANALYTICS_READ)
    assert not authorisation.can(MembershipRole.VIEWER, Permission.PORTFOLIO_TRANSACTION_CREATE)
    assert not authorisation.can(MembershipRole.VIEWER, Permission.PORTFOLIO_AUDIT_READ)


def test_portfolio_and_transaction_schemas_forbid_mass_assignment() -> None:
    with pytest.raises(ValidationError):
        PortfolioCreate.model_validate(
            {
                "tenant_id": str(uuid4()),
                "name": "Safe simulation",
                "base_currency": "GBP",
                "status": "posted",
            }
        )
    with pytest.raises(ValidationError):
        TransactionCreate.model_validate(
            {
                "transaction_type": "simulated_buy",
                "currency": "GBP",
                "listing_id": str(uuid4()),
                "quantity": "1",
                "unit_price": "10",
                "effective_at": datetime.now(UTC).isoformat(),
                "realised_pnl": "1000",
            }
        )
    with pytest.raises(ValidationError):
        TransactionCreate.model_validate(
            {
                "transaction_type": "reversal",
                "currency": "GBP",
                "effective_at": datetime.now(UTC).isoformat(),
            }
        )


@pytest.mark.parametrize(
    ("transaction_type", "payload"),
    [
        (PortfolioTransactionType.VIRTUAL_DEPOSIT, {"amount": "10"}),
        (
            PortfolioTransactionType.SIMULATED_BUY,
            {"listing_id": str(uuid4()), "quantity": "2", "unit_price": "3.25"},
        ),
        (
            PortfolioTransactionType.SIMULATED_SPLIT_ADJUSTMENT,
            {"listing_id": str(uuid4()), "split_ratio": "2"},
        ),
    ],
)
def test_supported_simulated_transaction_shapes(
    transaction_type: PortfolioTransactionType, payload: dict[str, str]
) -> None:
    data = TransactionCreate.model_validate(
        {
            "transaction_type": transaction_type,
            "currency": "GBP",
            "effective_at": datetime.now(UTC).isoformat(),
            **payload,
        }
    )
    assert data.transaction_type == transaction_type
    assert data.model_dump().get("status") is None


def test_decimal_quantisation_is_fixed_precision_and_bounded() -> None:
    assert quantize(Decimal("1.2345678901234567894")) == Decimal("1.234567890123456789")
    assert quantize(Decimal("1.2345678901234567896")) == Decimal("1.234567890123456790")


def test_openapi_exposes_only_typed_simulated_portfolio_operations() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/v1/portfolios",
        "/api/v1/portfolios/{portfolio_id}",
        "/api/v1/portfolios/{portfolio_id}/transactions",
        "/api/v1/portfolios/{portfolio_id}/transactions/{transaction_id}/reverse",
        "/api/v1/portfolios/{portfolio_id}/holdings",
        "/api/v1/portfolios/{portfolio_id}/valuation",
        "/api/v1/portfolios/{portfolio_id}/analytics",
        "/api/v1/portfolios/{portfolio_id}/analytics/benchmark",
        "/api/v1/portfolios/{portfolio_id}/audit-events",
    }
    assert required <= set(paths)
    assert not any(
        forbidden in path
        for path in paths
        for forbidden in ("/orders", "/brokers", "/ledger-entries")
    )
