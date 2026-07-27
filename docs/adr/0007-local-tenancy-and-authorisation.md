# ADR 0007: Atlas-local tenancy and central authorisation

- Status: Accepted
- Date: 2026-07-27
- Supersedes: The Clerk-organisation authority portion of ADR 0002

## Context

ADR 0002 established Clerk as the human identity provider and proposed Clerk Organisations as
the external tenant context. Atlas now needs personal workspaces, durable internal membership
records, append-only access audit events, and transactionally enforced ownership invariants.
Those controls must remain available independently of browser claims and identity-provider
organisation configuration.

## Decision

Clerk remains authoritative for authentication and its immutable subject identifies an external
human identity. Atlas PostgreSQL records are authoritative for users' lifecycle state,
workspaces, memberships, organisation roles, platform roles, onboarding state, and
authorisation decisions.

Every protected request starts with server-side Clerk token verification, resolves the subject
to an active Atlas user, and then evaluates the requested permission against the Atlas
membership for the target organisation. Request-provided organisation identifiers select an
object; they never establish authority. Cross-tenant misses are returned as `404` where
existence should be concealed.

Organisation roles map to a central permission matrix. Database constraints and transactions
enforce uniqueness and final-owner protection in addition to application checks. Clerk public
metadata, email addresses, browser storage, and client-supplied role values are not privileged
authorities.

## Consequences

- Atlas can create exactly one durable personal workspace during idempotent provisioning.
- Membership and ownership changes can be audited and protected transactionally.
- Access revocation requires changing the local user or membership state; a still-valid Clerk
  session cannot bypass that state.
- Future Clerk Organisation synchronisation, if adopted, must be an explicitly designed
  integration and must not silently overwrite Atlas authority.
- ADR 0002 continues to govern Clerk token verification and the requirement for internal tenant
  keys, but not Clerk Organisations as the authorisation source.
