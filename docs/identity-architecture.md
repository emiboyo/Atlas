# Identity Architecture

## Responsibility boundary

Clerk authenticates people, manages credentials and sessions, signs short-lived session JWTs, and
delivers identity lifecycle webhooks. Atlas never stores Clerk passwords, session tokens, refresh
tokens, or authentication cookies.

Atlas owns the durable application identity and authorisation model:

- `users` maps an immutable Atlas UUID to one unique Clerk subject.
- `user_profiles` contains minimal application profile data.
- `tenants` represents personal and team workspaces.
- `memberships` connects users to workspaces with a local role and lifecycle.
- `identity_audit_events` records append-only security-sensitive changes.
- `clerk_webhook_events` is the idempotent, payload-minimised webhook inbox.

Email is neither an identity key nor an authorisation input.

## Token verification

FastAPI accepts bearer tokens only on protected endpoints. It resolves the signing key through
Clerk JWKS with a five-second timeout and bounded cache, restricts algorithms to RS256, and
validates issuer, optional audience, expiry, not-before, issued-at, subject, session identifier,
authorised party, and session state. Unknown keys can trigger JWKS refresh. Retrieval failure
returns a stable availability error; it never falls back to decoded or unverified claims.

The browser cannot authoritatively supply an Atlas user ID, organisation ID, role, platform role,
or permission. Organisation path identifiers are resolved against active local membership.

## Provisioning and synchronisation

Clerk `user.created`, `user.updated`, and `user.deleted` events are accepted through the verified
Svix endpoint. Verification uses the exact raw body, timestamp tolerance, constant-time signature
comparison, and a bounded body size.

Provisioning is idempotent by Clerk subject. The first successful creation makes one local user,
one minimal profile, exactly one personal workspace, and one active owner membership.

The inbox stores event identity, type, subject, digest, timestamps, processing status, and a
bounded failure class—not the full webhook payload. Completed deliveries are idempotent. Failed
deliveries can be retried safely. A deletion event deactivates or creates a tombstone; it never
hard-deletes audit or financial references.

## Data classification

Clerk subjects, profiles, tenants, memberships, and identity audit events are Confidential.
Authentication tokens, webhook secrets, signing keys, and cookies are Restricted and must not be
persisted or logged. This milestone does not collect birth dates, tax identifiers, passports,
bank details, or KYC evidence.

## Production restriction

Local fake-key operation may expose public pages, but protected APIs fail closed and protected web
routes show an unavailable state. Real Clerk configuration, independent security review, provider
runbooks, key rotation testing, rate limiting, and deployment approval are required before
production.
