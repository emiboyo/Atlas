from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.database.atlas_database.base import (
    Base,
    ImmutableTimestampMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from packages.database.atlas_database.models.enums import (
    IdentityWebhookStatus,
    MembershipRole,
    MembershipStatus,
    OnboardingStatus,
    PlatformRole,
    TenantStatus,
    TenantType,
    UserStatus,
)


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (Index("ix_tenants_type_status", "organisation_type", "status"),)

    clerk_organization_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(
            TenantStatus,
            name="tenant_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )
    residency_country_code: Mapped[str | None] = mapped_column(String(2))
    organisation_type: Mapped[TenantType] = mapped_column(
        Enum(
            TenantType,
            name="tenant_type",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=TenantType.TEAM,
        nullable=False,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )

    memberships: Mapped[list["Membership"]] = relationship(back_populates="tenant")
    audit_events: Mapped[list["IdentityAuditEvent"]] = relationship(back_populates="tenant")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    clerk_user_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            name="user_status",
            native_enum=False,
            length=24,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=UserStatus.PENDING,
        nullable=False,
    )
    platform_role: Mapped[PlatformRole] = mapped_column(
        Enum(
            PlatformRole,
            name="platform_role",
            native_enum=False,
            length=24,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=PlatformRole.USER,
        nullable=False,
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")
    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("length(base_currency) = 3", name="base_currency_iso_length"),
        CheckConstraint(
            "country_of_residence IS NULL OR length(country_of_residence) = 2",
            name="country_iso_length",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str | None] = mapped_column(String(80))
    preferred_locale: Mapped[str] = mapped_column(String(16), default="en-GB", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/London", nullable=False)
    country_of_residence: Mapped[str | None] = mapped_column(String(2))
    base_currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)
    onboarding_status: Mapped[OnboardingStatus] = mapped_column(
        Enum(
            OnboardingStatus,
            name="onboarding_status",
            native_enum=False,
            length=24,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=OnboardingStatus.PROFILE_REQUIRED,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="profile")


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),
        Index("ix_memberships_user_status", "user_id", "status"),
        Index("ix_memberships_tenant_status_role", "tenant_id", "status", "role"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    clerk_membership_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            MembershipRole,
            name="membership_role",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(
            MembershipStatus,
            name="membership_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=MembershipStatus.ACTIVE,
        nullable=False,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class IdentityAuditEvent(UUIDPrimaryKeyMixin, ImmutableTimestampMixin, Base):
    __tablename__ = "identity_audit_events"
    __table_args__ = (
        Index("ix_identity_audit_tenant_created", "tenant_id", "created_at"),
        Index("ix_identity_audit_actor_created", "actor_user_id", "created_at"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    target_type: Mapped[str] = mapped_column(String(48), nullable=False)
    target_id: Mapped[UUID | None]
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="audit_events")


class ClerkWebhookEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clerk_webhook_events"
    __table_args__ = (Index("ix_clerk_webhook_status_created", "status", "created_at"),)

    svix_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    clerk_subject_id: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[IdentityWebhookStatus] = mapped_column(
        Enum(
            IdentityWebhookStatus,
            name="identity_webhook_status",
            native_enum=False,
            length=16,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=IdentityWebhookStatus.PENDING,
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
