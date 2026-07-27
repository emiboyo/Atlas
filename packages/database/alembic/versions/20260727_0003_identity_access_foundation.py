"""Create the identity, profile, tenancy, membership, and audit foundation.

Revision ID: 20260727_0003
Revises: 20260724_0002
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_0003"
down_revision: str | None = "20260724_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = sa.Uuid()


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


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("platform_role", sa.String(24), server_default="user", nullable=False),
    )
    op.add_column("users", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column(
        "memberships",
        "role",
        existing_type=sa.String(64),
        type_=sa.String(16),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_users_user_status",
        "users",
        "status IN ('pending','active','suspended','deactivated')",
    )
    op.create_check_constraint(
        "ck_users_platform_role",
        "users",
        "platform_role IN ('user','support','compliance','platform_admin')",
    )

    op.drop_constraint("ck_tenants_tenant_status", "tenants", type_="check")
    op.create_check_constraint(
        "ck_tenants_tenant_status",
        "tenants",
        "status IN ('active','suspended','archived','closed')",
    )
    op.add_column(
        "tenants",
        sa.Column("organisation_type", sa.String(16), server_default="team", nullable=False),
    )
    op.add_column("tenants", sa.Column("created_by_user_id", UUID, nullable=True))
    op.create_check_constraint(
        "ck_tenants_tenant_type",
        "tenants",
        "organisation_type IN ('personal','team')",
    )
    op.create_foreign_key(
        "fk_tenants_created_by_user_id_users",
        "tenants",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_tenants_type_status", "tenants", ["organisation_type", "status"], unique=False
    )

    op.create_check_constraint(
        "ck_memberships_membership_role",
        "memberships",
        "role IN ('owner','admin','member','viewer')",
    )
    op.create_index(
        "ix_memberships_tenant_status_role",
        "memberships",
        ["tenant_id", "status", "role"],
        unique=False,
    )

    op.create_table(
        "user_profiles",
        *audit_columns(),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=True),
        sa.Column("last_name", sa.String(80), nullable=True),
        sa.Column("preferred_locale", sa.String(16), server_default="en-GB", nullable=False),
        sa.Column("timezone", sa.String(64), server_default="Europe/London", nullable=False),
        sa.Column("country_of_residence", sa.String(2), nullable=True),
        sa.Column("base_currency", sa.String(3), server_default="GBP", nullable=False),
        sa.Column(
            "onboarding_status",
            sa.String(24),
            server_default="profile_required",
            nullable=False,
        ),
        sa.CheckConstraint("length(base_currency) = 3", name="ck_user_profiles_base_currency_iso"),
        sa.CheckConstraint(
            "country_of_residence IS NULL OR length(country_of_residence) = 2",
            name="ck_user_profiles_country_iso",
        ),
        sa.CheckConstraint(
            "onboarding_status IN "
            "('not_started','profile_required','workspace_required','completed')",
            name="ck_user_profiles_onboarding_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_profiles_user_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_profiles"),
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
    )

    op.create_table(
        "identity_audit_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("tenant_id", UUID, nullable=True),
        sa.Column("actor_user_id", UUID, nullable=True),
        sa.Column("target_type", sa.String(48), nullable=False),
        sa.Column("target_id", UUID, nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("event_metadata", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_identity_audit_events_actor_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_identity_audit_events_tenant_id_tenants",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_identity_audit_events"),
    )
    op.create_index(
        "ix_identity_audit_tenant_created",
        "identity_audit_events",
        ["tenant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_identity_audit_actor_created",
        "identity_audit_events",
        ["actor_user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "clerk_webhook_events",
        *audit_columns(),
        sa.Column("svix_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("clerk_subject_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','processed','failed','ignored')",
            name="ck_clerk_webhook_events_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clerk_webhook_events"),
        sa.UniqueConstraint("svix_id", name="uq_clerk_webhook_events_svix_id"),
    )
    op.create_index(
        "ix_clerk_webhook_status_created",
        "clerk_webhook_events",
        ["status", "created_at"],
        unique=False,
    )

    op.execute(
        """
        CREATE FUNCTION atlas_reject_identity_audit_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'identity audit events are append-only'
            USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_identity_audit_events_append_only
        BEFORE UPDATE OR DELETE ON identity_audit_events
        FOR EACH ROW EXECUTE FUNCTION atlas_reject_identity_audit_mutation();
        """
    )
    op.execute(
        """
        CREATE FUNCTION atlas_protect_final_owner()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
          active_owner_count integer;
        BEGIN
          IF OLD.role = 'owner' AND OLD.status = 'active'
             AND (TG_OP = 'DELETE' OR NEW.role <> 'owner' OR NEW.status <> 'active') THEN
            PERFORM pg_advisory_xact_lock(hashtextextended(OLD.tenant_id::text, 0));
            SELECT count(*) INTO active_owner_count
            FROM memberships
            WHERE tenant_id = OLD.tenant_id
              AND role = 'owner'
              AND status = 'active'
              AND id <> OLD.id;
            IF active_owner_count = 0 THEN
              RAISE EXCEPTION 'an organisation must retain an active owner'
                USING ERRCODE = 'integrity_constraint_violation';
            END IF;
          END IF;
          IF TG_OP = 'DELETE' THEN
            RETURN OLD;
          END IF;
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_memberships_protect_final_owner
        BEFORE UPDATE OR DELETE ON memberships
        FOR EACH ROW EXECUTE FUNCTION atlas_protect_final_owner();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_memberships_protect_final_owner ON memberships")
    op.execute("DROP FUNCTION IF EXISTS atlas_protect_final_owner")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_identity_audit_events_append_only ON identity_audit_events"
    )
    op.execute("DROP FUNCTION IF EXISTS atlas_reject_identity_audit_mutation")
    op.drop_index("ix_clerk_webhook_status_created", table_name="clerk_webhook_events")
    op.drop_table("clerk_webhook_events")
    op.drop_index("ix_identity_audit_actor_created", table_name="identity_audit_events")
    op.drop_index("ix_identity_audit_tenant_created", table_name="identity_audit_events")
    op.drop_table("identity_audit_events")
    op.drop_table("user_profiles")
    op.drop_index("ix_memberships_tenant_status_role", table_name="memberships")
    op.drop_constraint("ck_memberships_membership_role", "memberships", type_="check")
    op.alter_column(
        "memberships",
        "role",
        existing_type=sa.String(16),
        type_=sa.String(64),
        existing_nullable=False,
    )
    op.drop_index("ix_tenants_type_status", table_name="tenants")
    op.drop_constraint("fk_tenants_created_by_user_id_users", "tenants", type_="foreignkey")
    op.drop_constraint("ck_tenants_tenant_type", "tenants", type_="check")
    op.drop_column("tenants", "created_by_user_id")
    op.drop_column("tenants", "organisation_type")
    op.drop_constraint("ck_tenants_tenant_status", "tenants", type_="check")
    op.create_check_constraint(
        "ck_tenants_tenant_status",
        "tenants",
        "status IN ('active','suspended','closed')",
    )
    op.drop_constraint("ck_users_platform_role", "users", type_="check")
    op.drop_constraint("ck_users_user_status", "users", type_="check")
    op.drop_column("users", "deactivated_at")
    op.drop_column("users", "platform_role")
