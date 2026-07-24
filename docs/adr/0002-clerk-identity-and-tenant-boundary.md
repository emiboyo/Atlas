# ADR 0002: Clerk identity with API-enforced tenant authorization

- Status: Accepted
- Date: 2026-07-24

## Context

Atlas needs centralized human identity while preserving application control over tenant data and
authorization. Browser state and unsigned identity headers cannot form a trusted boundary.

## Decision

Use Clerk session-token version 2 for authentication and Clerk Organizations as the external
tenant context. FastAPI validates tokens locally against cached JWKS keys, including issuer,
time constraints, and authorized party. Atlas dependencies enforce organization membership and
custom permissions. Persisted resources will use an internal tenant key mapped to the verified
Clerk organization, rather than using a request-provided tenant identifier.

Permission checks are preferred over roles. Roles are used only where Clerk system permissions
are unavailable in session claims.

## Consequences

Requests remain available without a synchronous Clerk Backend API call in the normal path.
Role and permission configuration becomes security-sensitive infrastructure. Permission changes
may remain effective until short-lived existing session tokens expire, so critical revocation
workflows may require an additional server-side control in a later phase.
