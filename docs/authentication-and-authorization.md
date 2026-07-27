# Authentication and authorization

## Trust boundary

Clerk authenticates human users and issues short-lived RS256 session JWTs. The API remains
the authorization authority for Atlas resources: it validates every protected request and
never trusts identity fields sent in request bodies, query parameters, or client state.

Protected cross-origin requests use:

```http
Authorization: Bearer <clerk-session-token>
```

The verifier enforces:

- RS256 signatures using the configured Clerk JWKS endpoint
- issuer, expiry, not-before, and issued-at claims
- optional audience when `ATLAS_CLERK_AUDIENCE` is configured
- the `azp` authorized-party allowlist when the claim is present
- rejection of pending sessions
- Clerk session-token claim version 2

Signing keys are cached by `PyJWKClient`; unknown key IDs trigger a JWKS refresh. Secrets and
tokens are never logged.

## Tenancy

Clerk Organizations represent the external identity boundary for a tenant. The active
organization in the verified token becomes the request's tenant context. Future persisted
resources must also carry an internal tenant identifier and queries must enforce it at the
repository boundary. A client-supplied organization ID must never override the verified context.

Personal sessions may authenticate successfully but cannot access organization-scoped
dependencies. `require_organization` returns a stable `organization_required` error.

## Authorization model

Atlas uses permission-first authorization:

| Permission pattern      | Intended boundary                         |
| ----------------------- | ----------------------------------------- |
| `org:portfolios:read`   | View organization portfolios              |
| `org:portfolios:manage` | Create or change organization portfolios  |
| `org:members:read`      | View organization membership              |
| `org:members:manage`    | Invite or change members                  |
| `org:billing:manage`    | Change billing configuration              |
| `org:audit:read`        | Read security and compliance audit events |

These keys document the intended Clerk configuration; no corresponding business capabilities
exist yet. Permission dependencies are created with `require_permission("org:feature:action")`.

Role checks are reserved for Clerk system permissions that Clerk does not place in session
claims. Supported initial role semantics:

- `org:admin`: organization administration
- `org:member`: standard organization participation

The backend decodes Clerk's compact v2 feature-permission map into full permission keys. Denials
return `403` without revealing protected resource existence.

## API integration

- `CurrentPrincipal` requires and verifies a session.
- `require_organization` requires an active organization.
- `require_permission(...)` enforces a custom organization permission.
- `require_role(...)` enforces a normalized organization role.
- `GET /api/v1/auth/context` returns the server-verified request context for integration testing.

Authentication errors use the standard Atlas error envelope and request correlation ID.

Milestone 2 persists the verified Clerk subject as a unique mapping to an immutable Atlas user
UUID. Protected resource access uses the active local user and local membership; Clerk
organisation claims are context only and never override local tenancy. The current role and
permission matrix is documented in `docs/authorisation-model.md`.

Clerk lifecycle synchronisation uses the raw-body `/api/v1/webhooks/clerk` endpoint with Svix
signature verification, payload limits, timestamp tolerance, an idempotent inbox, safe retry, and
deactivation rather than hard deletion.

## Clerk dashboard checklist

1. Enable Organizations and decide whether personal accounts are allowed.
2. Create features and custom permissions matching the approved Atlas permission catalogue.
3. Assign permissions to reviewed custom roles.
4. Configure production domains and authorized parties.
5. Use session-token version 2; do not add large metadata objects to tokens.
6. Configure distinct Clerk instances and credentials for development, staging, and production.
7. Rotate keys through Clerk and verify JWKS refresh behavior before production.

## Security operations

Changes to roles or permissions require security review and audit events. High-risk actions
should later add recent-authentication or multi-factor requirements, idempotency, and explicit
approval policy. Authentication proves identity; it does not by itself establish suitability,
financial authority, or regulatory eligibility.
