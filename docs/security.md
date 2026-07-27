# Security baseline

- Identity is delegated to Clerk; API authorization must validate issuer, audience, signature,
  expiry, and subject for every protected route.
- Stripe webhook signatures must be verified before event processing.
- Secrets belong in Vercel environment variables or AWS Secrets Manager, never Git.
- Production data services remain private and encrypted in transit and at rest.
- Least-privilege IAM roles are assigned per workload.
- Dependency, container, SAST, and IaC scanning should be enforced before release.
- Audit-relevant events require immutable retention and explicit data classification.
- Financial features require threat modelling, regulatory review, and abuse controls before launch.

## API perimeter controls

Trusted hosts and exact CORS origins are environment-specific. Production configuration rejects
wildcards and local values, disables interactive API documentation, and refuses debug mode.
Request IDs are returned and bound to structured logs without recording authorization headers,
request bodies, payment data, or personal information.

Only the Stripe webhook currently accepts a request body. It enforces a configurable byte limit
before signature verification and persists events through an idempotent unique identifier.
File-upload routes are not implemented.

Rate limiting belongs at two layers: AWS WAF/ALB provides coarse IP and abuse protection, while a
future API policy adapter may use Redis for authenticated principal-, tenant-, and operation-level
budgets. Limits must fail safely, return a stable error schema, emit bounded metrics, and avoid
using client-supplied forwarding headers as identity. No application rate limiter is enabled yet;
that is a documented release warning, not an implicit unlimited-production decision.

## Identity controls

Milestone 2 adds local active-user and membership enforcement, central permission evaluation,
tenant-object concealment, transactional final-owner protection, Svix-verified Clerk webhooks,
idempotent personal-workspace provisioning, recent-authentication account deactivation, and
append-only identity audit events. See `docs/identity-threat-model.md`.

Protected access fails closed when Clerk is absent or unavailable. Browser-supplied roles,
platform roles, subjects, and tenant identifiers are never authorisation inputs. Tokens, cookies,
authorisation headers, webhook secrets, and full webhook bodies are excluded from persistence and
logs.
