"""harden research parent integrity

Revision ID: 20260730_0008
Revises: 20260728_0007
Create Date: 2026-07-30 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260730_0008"
down_revision: str | None = "20260728_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM backtest_runs r
            LEFT JOIN research_strategy_versions v
              ON v.tenant_id = r.tenant_id
             AND v.strategy_id = r.strategy_id
             AND v.id = r.strategy_version_id
            WHERE v.id IS NULL
          ) THEN
            RAISE EXCEPTION 'research parent-integrity migration blocked: malformed backtest run';
          END IF;
          IF EXISTS (
            SELECT 1 FROM research_strategies s
            LEFT JOIN research_strategy_versions v
              ON v.tenant_id = s.tenant_id
             AND v.strategy_id = s.id
             AND v.id = s.current_version_id
            WHERE s.current_version_id IS NOT NULL AND v.id IS NULL
          ) THEN
            RAISE EXCEPTION 'research parent-integrity migration blocked: malformed current version';
          END IF;
          IF EXISTS (
            SELECT 1 FROM research_audit_events a
            LEFT JOIN research_strategy_versions v
              ON v.tenant_id = a.tenant_id
             AND v.strategy_id = a.strategy_id
             AND v.id = a.strategy_version_id
            LEFT JOIN backtest_runs r
              ON r.tenant_id = a.tenant_id
             AND r.strategy_id = a.strategy_id
             AND r.strategy_version_id = a.strategy_version_id
             AND r.id = a.run_id
            WHERE (a.strategy_version_id IS NOT NULL AND v.id IS NULL)
               OR (a.run_id IS NOT NULL AND r.id IS NULL)
          ) THEN
            RAISE EXCEPTION 'research parent-integrity migration blocked: malformed audit parent';
          END IF;
          IF EXISTS (
            SELECT 1 FROM backtest_runs WHERE missing_data_policy <> 'fail_run'
          ) THEN
            RAISE EXCEPTION 'research policy migration blocked: unsupported historical missing-data policy';
          END IF;
        END $$;
        """
    )

    op.create_unique_constraint(
        "uq_research_versions_parent_identity",
        "research_strategy_versions",
        ["tenant_id", "strategy_id", "id"],
    )
    op.create_unique_constraint(
        "uq_backtest_runs_parent_identity",
        "backtest_runs",
        ["tenant_id", "strategy_id", "strategy_version_id", "id"],
    )
    op.drop_constraint(
        "fk_backtest_runs_version_tenant", "backtest_runs", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_backtest_runs_version_parent",
        "backtest_runs",
        "research_strategy_versions",
        ["tenant_id", "strategy_id", "strategy_version_id"],
        ["tenant_id", "strategy_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_research_strategy_current_version_parent",
        "research_strategies",
        "research_strategy_versions",
        ["tenant_id", "id", "current_version_id"],
        ["tenant_id", "strategy_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_research_audit_version_parent",
        "research_audit_events",
        "research_strategy_versions",
        ["tenant_id", "strategy_id", "strategy_version_id"],
        ["tenant_id", "strategy_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_research_audit_run_parent",
        "research_audit_events",
        "backtest_runs",
        ["tenant_id", "strategy_id", "strategy_version_id", "run_id"],
        ["tenant_id", "strategy_id", "strategy_version_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_research_audit_events_research_audit_run_requires_version",
        "research_audit_events",
        "run_id IS NULL OR strategy_version_id IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_backtest_runs_backtest_run_supported_missing_policy",
        "backtest_runs",
        "missing_data_policy = 'fail_run'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_backtest_runs_backtest_run_supported_missing_policy",
        "backtest_runs",
        type_="check",
    )
    op.drop_constraint(
        "ck_research_audit_events_research_audit_run_requires_version",
        "research_audit_events",
        type_="check",
    )
    op.drop_constraint(
        "fk_research_audit_run_parent", "research_audit_events", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_research_audit_version_parent", "research_audit_events", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_research_strategy_current_version_parent",
        "research_strategies",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_backtest_runs_version_parent", "backtest_runs", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_backtest_runs_version_tenant",
        "backtest_runs",
        "research_strategy_versions",
        ["strategy_version_id", "tenant_id"],
        ["id", "tenant_id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_backtest_runs_parent_identity", "backtest_runs", type_="unique"
    )
    op.drop_constraint(
        "uq_research_versions_parent_identity",
        "research_strategy_versions",
        type_="unique",
    )
