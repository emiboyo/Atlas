"""Add simulated portfolio accounting and read-only valuation foundations.

Revision ID: 20260728_0006
Revises: 20260727_0005
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_0006"
down_revision: str | None = "20260727_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = sa.Uuid()
DECIMAL = sa.Numeric(38, 18)


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


def timestamp_columns() -> list[sa.Column[object]]:
    return [
        *immutable_columns(),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.add_column("portfolios", sa.Column("base_currency", sa.String(3), nullable=True))
    op.add_column(
        "portfolios",
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
    )
    op.add_column("portfolios", sa.Column("created_by_user_id", UUID, nullable=True))
    op.add_column(
        "portfolios", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("portfolios", sa.Column("benchmark_listing_id", UUID, nullable=True))
    op.execute(
        """
        UPDATE portfolios AS p
        SET base_currency = a.base_currency,
            created_by_user_id = COALESCE(a.owner_user_id, t.created_by_user_id)
        FROM investment_accounts AS a, tenants AS t
        WHERE p.investment_account_id = a.id
          AND p.tenant_id = t.id
        """
    )
    op.alter_column("portfolios", "base_currency", nullable=False)
    op.alter_column("portfolios", "created_by_user_id", nullable=False)
    op.create_check_constraint(
        "ck_portfolios_base_currency_iso_length",
        "portfolios",
        "length(base_currency) = 3",
    )
    op.create_check_constraint(
        "ck_portfolios_portfolio_status",
        "portfolios",
        "status IN ('active','archived')",
    )
    op.create_foreign_key(
        "fk_portfolios_created_by_user_id_users",
        "portfolios",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_portfolios_benchmark_listing_id_instrument_listings",
        "portfolios",
        "instrument_listings",
        ["benchmark_listing_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_portfolios_tenant_status",
        "portfolios",
        ["tenant_id", "status"],
        unique=False,
    )

    op.create_table(
        "portfolio_accounts",
        *timestamp_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("portfolio_id", UUID, nullable=False),
        sa.Column("ledger_account_id", UUID, nullable=False),
        sa.Column("account_role", sa.String(40), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint(
            "account_role IN ('virtual_cash','simulated_investment_cost','simulated_capital',"
            "'simulated_dividend_income','simulated_fee_expense','simulated_realised_gain',"
            "'simulated_realised_loss')",
            name="ck_portfolio_accounts_portfolio_account_role",
        ),
        sa.CheckConstraint(
            "length(currency) = 3", name="ck_portfolio_accounts_currency_iso_length"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_portfolio_accounts_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_accounts_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ledger_account_id", "tenant_id"],
            ["ledger_accounts.id", "ledger_accounts.tenant_id"],
            name="fk_portfolio_accounts_ledger_tenant",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_accounts"),
        sa.UniqueConstraint(
            "ledger_account_id", name="uq_portfolio_accounts_ledger_account_id"
        ),
        sa.UniqueConstraint(
            "portfolio_id",
            "account_role",
            "currency",
            name="uq_portfolio_account_role_currency",
        ),
    )
    op.create_index(
        "ix_portfolio_accounts_tenant_portfolio",
        "portfolio_accounts",
        ["tenant_id", "portfolio_id"],
        unique=False,
    )

    op.create_table(
        "portfolio_transactions",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("portfolio_id", UUID, nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("transaction_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("external_reference", sa.String(128), nullable=True),
        sa.Column("listing_id", UUID, nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("quantity", DECIMAL, nullable=True),
        sa.Column("unit_price", DECIMAL, nullable=True),
        sa.Column("gross_amount", DECIMAL, nullable=False),
        sa.Column("fee_amount", DECIMAL, nullable=False),
        sa.Column("net_amount", DECIMAL, nullable=False),
        sa.Column("position_quantity_delta", DECIMAL, nullable=False),
        sa.Column("position_cost_delta", DECIMAL, nullable=False),
        sa.Column("realised_pnl_delta", DECIMAL, nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", UUID, nullable=False),
        sa.Column("reversal_of_transaction_id", UUID, nullable=True),
        sa.Column("ledger_transaction_id", UUID, nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("transaction_metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint(
            "transaction_type IN ('virtual_deposit','virtual_withdrawal','simulated_buy',"
            "'simulated_sell','simulated_dividend','simulated_fee',"
            "'simulated_split_adjustment','reversal')",
            name="ck_portfolio_transactions_portfolio_transaction_type",
        ),
        sa.CheckConstraint(
            "status IN ('posted','reversed')",
            name="ck_portfolio_transactions_portfolio_transaction_status",
        ),
        sa.CheckConstraint(
            "length(currency) = 3", name="ck_portfolio_transactions_currency_iso_length"
        ),
        sa.CheckConstraint(
            "gross_amount >= 0", name="ck_portfolio_transactions_gross_amount_non_negative"
        ),
        sa.CheckConstraint(
            "fee_amount >= 0", name="ck_portfolio_transactions_fee_amount_non_negative"
        ),
        sa.CheckConstraint(
            "net_amount >= 0", name="ck_portfolio_transactions_net_amount_non_negative"
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_portfolio_transactions_quantity_positive",
        ),
        sa.CheckConstraint(
            "unit_price IS NULL OR unit_price >= 0",
            name="ck_portfolio_transactions_unit_price_non_negative",
        ),
        sa.CheckConstraint(
            "is_simulated = true", name="ck_portfolio_transactions_simulated_only"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_portfolio_transactions_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_transactions_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_portfolio_transactions_listing_id_instrument_listings",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_portfolio_transactions_created_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reversal_of_transaction_id"],
            ["portfolio_transactions.id"],
            name="fk_portfolio_transactions_reversal_of",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ledger_transaction_id"],
            ["ledger_transactions.id"],
            name="fk_portfolio_transactions_ledger_transaction",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_transactions"),
        sa.UniqueConstraint(
            "tenant_id",
            "portfolio_id",
            "idempotency_key",
            name="uq_portfolio_transactions_idempotency",
        ),
        sa.UniqueConstraint(
            "portfolio_id", "sequence", name="uq_portfolio_transactions_sequence"
        ),
        sa.UniqueConstraint(
            "reversal_of_transaction_id",
            name="uq_portfolio_transactions_reversal_of_transaction_id",
        ),
        sa.UniqueConstraint(
            "ledger_transaction_id", name="uq_portfolio_transactions_ledger"
        ),
    )
    op.create_index(
        "ix_portfolio_transactions_tenant_portfolio_effective",
        "portfolio_transactions",
        ["tenant_id", "portfolio_id", "effective_at"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_transactions_listing",
        "portfolio_transactions",
        ["listing_id"],
        unique=False,
    )

    op.create_table(
        "portfolio_positions",
        *timestamp_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("portfolio_id", UUID, nullable=False),
        sa.Column("listing_id", UUID, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("quantity", DECIMAL, nullable=False),
        sa.Column("average_cost_per_unit", DECIMAL, nullable=False),
        sa.Column("cost_basis", DECIMAL, nullable=False),
        sa.Column("realised_pnl", DECIMAL, nullable=False),
        sa.Column("position_status", sa.String(16), nullable=False),
        sa.Column("last_transaction_sequence", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "length(currency) = 3", name="ck_portfolio_positions_currency_iso_length"
        ),
        sa.CheckConstraint(
            "quantity >= 0", name="ck_portfolio_positions_quantity_non_negative"
        ),
        sa.CheckConstraint(
            "average_cost_per_unit >= 0",
            name="ck_portfolio_positions_average_cost_non_negative",
        ),
        sa.CheckConstraint(
            "cost_basis >= 0", name="ck_portfolio_positions_cost_basis_non_negative"
        ),
        sa.CheckConstraint(
            "position_status IN ('open','closed')",
            name="ck_portfolio_positions_portfolio_position_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_portfolio_positions_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_positions_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_portfolio_positions_listing_id_instrument_listings",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_positions"),
        sa.UniqueConstraint(
            "portfolio_id", "listing_id", name="uq_portfolio_positions_listing"
        ),
    )
    op.create_index(
        "ix_portfolio_positions_tenant_portfolio",
        "portfolio_positions",
        ["tenant_id", "portfolio_id"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_positions_listing",
        "portfolio_positions",
        ["listing_id"],
        unique=False,
    )

    op.create_table(
        "portfolio_valuation_snapshots",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("portfolio_id", UUID, nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("base_currency_total", DECIMAL, nullable=True),
        sa.Column("completeness", sa.String(16), nullable=False),
        sa.Column("created_by_user_id", UUID, nullable=False),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint(
            "length(base_currency) = 3",
            name="ck_portfolio_valuation_snapshots_base_currency_iso_length",
        ),
        sa.CheckConstraint(
            "completeness IN ('complete','incomplete')",
            name="ck_portfolio_valuation_snapshots_valuation_completeness",
        ),
        sa.CheckConstraint(
            "is_simulated = true",
            name="ck_portfolio_valuation_snapshots_simulated_only",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_portfolio_valuation_snapshots_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_valuation_snapshots_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_portfolio_valuation_snapshots_created_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_valuation_snapshots"),
        sa.UniqueConstraint(
            "portfolio_id",
            "idempotency_key",
            name="uq_portfolio_valuation_snapshot_idempotency",
        ),
    )
    op.create_index(
        "ix_portfolio_valuation_snapshots_portfolio_as_of",
        "portfolio_valuation_snapshots",
        ["portfolio_id", "as_of"],
        unique=False,
    )

    op.create_table(
        "portfolio_valuation_lines",
        *immutable_columns(),
        sa.Column("snapshot_id", UUID, nullable=False),
        sa.Column("listing_id", UUID, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("quantity", DECIMAL, nullable=False),
        sa.Column("cost_basis", DECIMAL, nullable=False),
        sa.Column("latest_price", DECIMAL, nullable=True),
        sa.Column("market_value", DECIMAL, nullable=True),
        sa.Column("unrealised_pnl", DECIMAL, nullable=True),
        sa.Column("provider", sa.String(48), nullable=True),
        sa.Column("provider_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_status", sa.String(16), nullable=False),
        sa.Column("source_reference", sa.String(160), nullable=True),
        sa.CheckConstraint(
            "length(currency) = 3",
            name="ck_portfolio_valuation_lines_currency_iso_length",
        ),
        sa.CheckConstraint(
            "quantity >= 0", name="ck_portfolio_valuation_lines_quantity_non_negative"
        ),
        sa.CheckConstraint(
            "cost_basis >= 0",
            name="ck_portfolio_valuation_lines_cost_basis_non_negative",
        ),
        sa.CheckConstraint(
            "data_status IN ('live','delayed','end_of_day','cached','stale','simulated',"
            "'unavailable')",
            name="ck_portfolio_valuation_lines_valuation_market_data_status",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["portfolio_valuation_snapshots.id"],
            name="fk_portfolio_valuation_lines_snapshot",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["instrument_listings.id"],
            name="fk_portfolio_valuation_lines_listing_id_instrument_listings",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_valuation_lines"),
        sa.UniqueConstraint(
            "snapshot_id", "listing_id", name="uq_portfolio_valuation_line_listing"
        ),
    )
    op.create_index(
        "ix_portfolio_valuation_lines_listing",
        "portfolio_valuation_lines",
        ["listing_id"],
        unique=False,
    )

    op.create_table(
        "portfolio_audit_events",
        *immutable_columns(),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("portfolio_id", UUID, nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("operation_id", sa.String(128), nullable=True),
        sa.Column("actor_user_id", UUID, nullable=False),
        sa.Column("target_id", UUID, nullable=True),
        sa.Column("event_metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_portfolio_audit_events_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "tenant_id"],
            ["portfolios.id", "portfolios.tenant_id"],
            name="fk_portfolio_audit_events_portfolio_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_portfolio_audit_events_actor_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_audit_events"),
    )
    op.create_index(
        "ix_portfolio_audit_events_portfolio_created",
        "portfolio_audit_events",
        ["portfolio_id", "created_at"],
        unique=False,
    )

    op.execute(
        """
        CREATE FUNCTION atlas_reject_portfolio_history_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'portfolio financial history is append-only'
            USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$
        """
    )
    for table in (
        "portfolio_valuation_lines",
        "portfolio_valuation_snapshots",
        "portfolio_audit_events",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_append_only
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION atlas_reject_portfolio_history_mutation()
            """
        )
    op.execute(
        """
        CREATE FUNCTION atlas_restrict_portfolio_transaction_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'portfolio transactions are append-only'
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          IF NEW.status <> OLD.status
             AND OLD.status = 'posted'
             AND NEW.status = 'reversed'
             AND (to_jsonb(NEW) - 'status') = (to_jsonb(OLD) - 'status')
             AND EXISTS (
               SELECT 1 FROM portfolio_transactions reversal
               WHERE reversal.reversal_of_transaction_id = OLD.id
                 AND reversal.transaction_type = 'reversal'
             )
          THEN
            RETURN NEW;
          END IF;
          IF NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'posted portfolio transactions are immutable'
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_portfolio_transactions_append_only
        BEFORE UPDATE OR DELETE ON portfolio_transactions
        FOR EACH ROW EXECUTE FUNCTION atlas_restrict_portfolio_transaction_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_portfolio_transactions_append_only "
        "ON portfolio_transactions"
    )
    for table in (
        "portfolio_audit_events",
        "portfolio_valuation_snapshots",
        "portfolio_valuation_lines",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_append_only ON {table}")
    op.execute("DROP FUNCTION IF EXISTS atlas_restrict_portfolio_transaction_mutation()")
    op.execute("DROP FUNCTION IF EXISTS atlas_reject_portfolio_history_mutation()")
    op.drop_table("portfolio_audit_events")
    op.drop_table("portfolio_valuation_lines")
    op.drop_table("portfolio_valuation_snapshots")
    op.drop_table("portfolio_positions")
    op.drop_table("portfolio_transactions")
    op.drop_table("portfolio_accounts")
    op.drop_index("ix_portfolios_tenant_status", table_name="portfolios")
    op.drop_constraint(
        "fk_portfolios_benchmark_listing_id_instrument_listings",
        "portfolios",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_portfolios_created_by_user_id_users", "portfolios", type_="foreignkey"
    )
    op.drop_constraint(
        "ck_portfolios_portfolio_status", "portfolios", type_="check"
    )
    op.drop_constraint(
        "ck_portfolios_base_currency_iso_length", "portfolios", type_="check"
    )
    op.drop_column("portfolios", "benchmark_listing_id")
    op.drop_column("portfolios", "archived_at")
    op.drop_column("portfolios", "created_by_user_id")
    op.drop_column("portfolios", "status")
    op.drop_column("portfolios", "base_currency")
