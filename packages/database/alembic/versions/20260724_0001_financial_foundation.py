"""Create identity, portfolio, instrument, and ledger foundations.

Revision ID: 20260724_0001
Revises:
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = sa.Uuid()
MONEY = sa.Numeric(38, 18)


def audit_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def immutable_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "tenants",
        *audit_columns(),
        sa.Column("clerk_organization_id", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("residency_country_code", sa.String(2), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'closed')", name="ck_tenants_tenant_status"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.UniqueConstraint("clerk_organization_id", name="uq_tenants_clerk_organization_id"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_table(
        "users",
        *audit_columns(),
        sa.Column("clerk_user_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("clerk_user_id", name="uq_users_clerk_user_id"),
    )
    op.create_table(
        "instruments",
        *audit_columns(),
        sa.Column("canonical_symbol", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_class", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("isin", sa.String(12), nullable=True),
        sa.Column("figi", sa.String(12), nullable=True),
        sa.Column("metadata_version", sa.Integer(), nullable=False),
        sa.CheckConstraint("length(base_currency) = 3", name="ck_instruments_base_currency_iso_length"),
        sa.CheckConstraint(
            "asset_class IN ('stock','etf','forex','crypto','commodity','index','cash')",
            name="ck_instruments_asset_class",
        ),
        sa.CheckConstraint(
            "status IN ('active','inactive','delisted')",
            name="ck_instruments_instrument_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_instruments"),
        sa.UniqueConstraint(
            "canonical_symbol", "asset_class", name="uq_instruments_symbol_class"
        ),
        sa.UniqueConstraint("figi", name="uq_instruments_figi"),
        sa.UniqueConstraint("isin", name="uq_instruments_isin"),
    )
    op.create_index(
        "ix_instruments_asset_status", "instruments", ["asset_class", "status"], unique=False
    )
    op.create_table(
        "memberships",
        *audit_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("clerk_membership_id", sa.String(64), nullable=True),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.CheckConstraint(
            "status IN ('active','invited','suspended','removed')",
            name="ck_memberships_membership_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_memberships_tenant_id_tenants", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_memberships_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_memberships"),
        sa.UniqueConstraint("clerk_membership_id", name="uq_memberships_clerk_membership_id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),
    )
    op.create_index(
        "ix_memberships_user_status", "memberships", ["user_id", "status"], unique=False
    )
    op.create_table(
        "instrument_listings",
        *audit_columns(),
        sa.Column("instrument_id", UUID, nullable=False),
        sa.Column("venue_mic", sa.String(4), nullable=False),
        sa.Column("ticker", sa.String(32), nullable=False),
        sa.Column("quote_currency", sa.String(3), nullable=False),
        sa.Column("price_increment", MONEY, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "length(quote_currency) = 3", name="ck_instrument_listings_quote_currency_iso_length"
        ),
        sa.CheckConstraint(
            "length(venue_mic) = 4", name="ck_instrument_listings_venue_mic_iso_length"
        ),
        sa.CheckConstraint(
            "price_increment > 0", name="ck_instrument_listings_price_increment_positive"
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name="fk_instrument_listings_instrument_id_instruments",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_instrument_listings"),
        sa.UniqueConstraint(
            "venue_mic", "ticker", "quote_currency", name="uq_listings_venue_ticker_currency"
        ),
    )
    op.create_table(
        "investment_accounts",
        *audit_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("owner_user_id", UUID, nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("account_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("external_provider", sa.String(64), nullable=True),
        sa.Column("external_account_id", sa.String(128), nullable=True),
        sa.CheckConstraint(
            "account_type IN ('cash','custody','brokerage','retirement','tax_advantaged')",
            name="ck_investment_accounts_account_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','active','restricted','closed')",
            name="ck_investment_accounts_account_status",
        ),
        sa.CheckConstraint(
            "length(base_currency) = 3",
            name="ck_investment_accounts_base_currency_iso_length",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name="fk_investment_accounts_owner_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_investment_accounts_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investment_accounts"),
        sa.UniqueConstraint("id", "tenant_id", name="uq_investment_accounts_id_tenant"),
        sa.UniqueConstraint(
            "tenant_id",
            "external_provider",
            "external_account_id",
            name="uq_accounts_provider_id",
        ),
    )
    op.create_index(
        "ix_investment_accounts_tenant_status",
        "investment_accounts",
        ["tenant_id", "status"],
        unique=False,
    )
    op.create_table(
        "portfolios",
        *audit_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("investment_account_id", UUID, nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["investment_account_id", "tenant_id"],
            ["investment_accounts.id", "investment_accounts.tenant_id"],
            name="fk_portfolios_account_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_portfolios_tenant_id_tenants", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolios"),
        sa.UniqueConstraint("id", "tenant_id", name="uq_portfolios_id_tenant"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_portfolios_tenant_name"),
    )
    op.create_index(
        "ix_portfolios_tenant_account",
        "portfolios",
        ["tenant_id", "investment_account_id"],
        unique=False,
    )
    op.create_table(
        "ledger_accounts",
        *audit_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("account_type", sa.String(16), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.CheckConstraint(
            "account_type IN ('asset','liability','equity','revenue','expense')",
            name="ck_ledger_accounts_ledger_account_type",
        ),
        sa.CheckConstraint(
            "length(currency) = 3", name="ck_ledger_accounts_currency_iso_length"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_ledger_accounts_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_accounts"),
        sa.UniqueConstraint("id", "tenant_id", name="uq_ledger_accounts_id_tenant"),
        sa.UniqueConstraint(
            "tenant_id", "code", "currency", name="uq_ledger_accounts_code_currency"
        ),
    )
    op.create_index(
        "ix_ledger_accounts_tenant_type",
        "ledger_accounts",
        ["tenant_id", "account_type"],
        unique=False,
    )
    op.create_table(
        "ledger_transactions",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("external_reference", sa.String(128), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reversal_of_id", UUID, nullable=True),
        sa.CheckConstraint(
            "status IN ('draft','posted','reversed')",
            name="ck_ledger_transactions_ledger_transaction_status",
        ),
        sa.ForeignKeyConstraint(
            ["reversal_of_id"],
            ["ledger_transactions.id"],
            name="fk_ledger_transactions_reversal_of_id_ledger_transactions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_ledger_transactions_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_transactions"),
        sa.UniqueConstraint("id", "tenant_id", name="uq_ledger_transactions_id_tenant"),
        sa.UniqueConstraint("reversal_of_id", name="uq_ledger_transactions_reversal_of_id"),
        sa.UniqueConstraint(
            "tenant_id", "idempotency_key", name="uq_ledger_transactions_idempotency"
        ),
    )
    op.create_index(
        "ix_ledger_transactions_tenant_effective",
        "ledger_transactions",
        ["tenant_id", "effective_at"],
        unique=False,
    )
    op.create_table(
        "position_snapshots",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("portfolio_id", UUID, nullable=False),
        sa.Column("instrument_id", UUID, nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", MONEY, nullable=False),
        sa.Column("cost_basis", MONEY, nullable=False),
        sa.Column("cost_basis_currency", sa.String(3), nullable=False),
        sa.Column("source_event_id", sa.String(128), nullable=False),
        sa.CheckConstraint(
            "length(cost_basis_currency) = 3",
            name="ck_position_snapshots_cost_basis_currency_iso_length",
        ),
        sa.CheckConstraint(
            "cost_basis >= 0", name="ck_position_snapshots_cost_basis_non_negative"
        ),
        sa.CheckConstraint(
            "quantity >= 0", name="ck_position_snapshots_quantity_non_negative"
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name="fk_position_snapshots_instrument_id_instruments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_position_snapshots_portfolio_tenant",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_position_snapshots_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_position_snapshots"),
        sa.UniqueConstraint(
            "portfolio_id", "instrument_id", "as_of", name="uq_position_snapshot_point"
        ),
    )
    op.create_index(
        "ix_position_snapshots_tenant_as_of",
        "position_snapshots",
        ["tenant_id", "as_of"],
        unique=False,
    )
    op.create_table(
        "ledger_entries",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("transaction_id", UUID, nullable=False),
        sa.Column("ledger_account_id", UUID, nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("memo", sa.String(500), nullable=True),
        sa.CheckConstraint("amount <> 0", name="ck_ledger_entries_amount_non_zero"),
        sa.ForeignKeyConstraint(
            ["ledger_account_id", "tenant_id"],
            ["ledger_accounts.id", "ledger_accounts.tenant_id"],
            name="fk_ledger_entries_account_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_ledger_entries_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id", "tenant_id"],
            ["ledger_transactions.id", "ledger_transactions.tenant_id"],
            name="fk_ledger_entries_transaction_tenant",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_entries"),
    )
    op.create_index(
        "ix_ledger_entries_account_created",
        "ledger_entries",
        ["ledger_account_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ledger_entries_tenant_transaction",
        "ledger_entries",
        ["tenant_id", "transaction_id"],
        unique=False,
    )

    op.execute(
        """
        CREATE FUNCTION atlas_reject_ledger_entry_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'ledger entries are append-only'
            USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ledger_entries_append_only
        BEFORE UPDATE OR DELETE ON ledger_entries
        FOR EACH ROW EXECUTE FUNCTION atlas_reject_ledger_entry_mutation();
        """
    )
    op.execute(
        """
        CREATE FUNCTION atlas_validate_ledger_balance()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
          target_transaction_id uuid;
          target_status varchar;
          entry_count integer;
          unbalanced_currency_count integer;
        BEGIN
          IF TG_TABLE_NAME = 'ledger_transactions' THEN
            target_transaction_id := NEW.id;
          ELSE
            target_transaction_id := NEW.transaction_id;
          END IF;

          SELECT status INTO target_status
          FROM ledger_transactions
          WHERE id = target_transaction_id;

          IF target_status <> 'posted' THEN
            RETURN NULL;
          END IF;

          SELECT count(*) INTO entry_count
          FROM ledger_entries
          WHERE transaction_id = target_transaction_id;

          SELECT count(*) INTO unbalanced_currency_count
          FROM (
            SELECT account.currency
            FROM ledger_entries entry
            JOIN ledger_accounts account ON account.id = entry.ledger_account_id
            WHERE entry.transaction_id = target_transaction_id
            GROUP BY account.currency
            HAVING sum(entry.amount) <> 0
          ) unbalanced;

          IF entry_count < 2 OR unbalanced_currency_count > 0 THEN
            RAISE EXCEPTION 'posted ledger transaction % is not balanced', target_transaction_id
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          RETURN NULL;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_ledger_entries_balance
        AFTER INSERT ON ledger_entries
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION atlas_validate_ledger_balance();
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_ledger_transaction_balance
        AFTER INSERT OR UPDATE OF status ON ledger_transactions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION atlas_validate_ledger_balance();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_transaction_balance ON ledger_transactions")
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_entries_balance ON ledger_entries")
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_entries_append_only ON ledger_entries")
    op.execute("DROP FUNCTION IF EXISTS atlas_validate_ledger_balance()")
    op.execute("DROP FUNCTION IF EXISTS atlas_reject_ledger_entry_mutation()")
    op.drop_table("ledger_entries")
    op.drop_table("position_snapshots")
    op.drop_table("ledger_transactions")
    op.drop_table("ledger_accounts")
    op.drop_table("portfolios")
    op.drop_table("investment_accounts")
    op.drop_table("instrument_listings")
    op.drop_table("memberships")
    op.drop_table("instruments")
    op.drop_table("users")
    op.drop_table("tenants")
