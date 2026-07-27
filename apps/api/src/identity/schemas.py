import re
from datetime import datetime
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.database.atlas_database.models.enums import (
    MembershipRole,
    MembershipStatus,
    OnboardingStatus,
    PlatformRole,
    TenantStatus,
    TenantType,
    UserStatus,
)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    first_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    preferred_locale: str | None = Field(default=None, pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z]{2})?$")
    timezone: str | None = Field(default=None, max_length=64)
    country_of_residence: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    base_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(r"(?:UTC|[A-Za-z_]+(?:/[A-Za-z0-9_+\-]+)+)", value):
                raise ValueError("timezone must be a recognised IANA timezone")
            known_timezones = available_timezones()
            if known_timezones and value not in known_timezones:
                raise ValueError("timezone must be a recognised IANA timezone")
        return value


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str
    first_name: str | None
    last_name: str | None
    preferred_locale: str
    timezone: str
    country_of_residence: str | None
    base_currency: str
    onboarding_status: OnboardingStatus
    updated_at: datetime


class UserResponse(BaseModel):
    id: UUID
    status: UserStatus
    platform_role: PlatformRole
    profile: ProfileResponse


class OrganisationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    slug: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganisationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(
        default=None, min_length=3, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )


class OrganisationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    organisation_type: TenantType
    status: TenantStatus
    role: MembershipRole | None = None
    created_at: datetime
    updated_at: datetime


class MembershipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    role: MembershipRole = MembershipRole.MEMBER


class MembershipUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: MembershipRole | None = None
    status: MembershipStatus | None = None


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    role: MembershipRole
    status: MembershipStatus
    created_at: datetime
    updated_at: datetime


class TransferOwnershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    membership_id: UUID


class DeactivationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation: str


class OnboardingResponse(BaseModel):
    status: OnboardingStatus
    profile: ProfileResponse
    personal_workspace: OrganisationResponse


class Page(BaseModel):
    items: list[dict[str, object]]
    page: int
    page_size: int
    total: int


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    actor_user_id: UUID | None
    target_type: str
    target_id: UUID | None
    request_id: str | None
    event_metadata: dict[str, object]
    created_at: datetime
