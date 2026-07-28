# Security baseline

Milestone 3 provider selection is server-controlled. Browser input cannot select a provider,
mapping, role or permission. Provider results are immutable, validated centrally, executed under
bounded timeouts/retries, and never logged as raw payloads. Development administration uses
non-public CLI commands and bounded audit metadata.

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

## Market-data security

Market routes require a verified active Atlas user. Watchlists additionally require a
server-resolved membership and central permission. Browser symbols, tenant IDs, provider names,
and roles are never authorities. Search is bounded and parameterised; candle ranges and
watchlist sizes are capped. Provider credentials remain server-side. Simulated/stale status and
provenance cannot be promoted to live by browser input or caching. See
`docs/market-data-threat-model.md`.

## Milestone 4 simulated-portfolio boundary

Milestone 4 is authorised for private simulated development only under
[`milestone-4-governance.md`](milestone-4-governance.md) and
[ADR 0009](adr/0009-milestone-4-private-development-authorisation.md). Portfolio permissions must
be evaluated centrally and server-side; browser-supplied tenant, role, permission, ownership,
provider, transaction-status, or simulation values are not authorities.

Financial values require fixed-precision persistence, explicit currencies, idempotent and
deterministically ordered transactions, append-only history, safe reversals, provenance,
freshness, database constraints, and tenant isolation. Simulation must remain unmistakable.
Production, public access, live providers, real money, payments, brokerage, execution, custody,
advice, customer funds, and Milestone 5 remain prohibited.

Milestone 4 uses the existing active-user and membership chain. Same-tenant permission failures
return `403`; foreign portfolio, transaction, and snapshot identifiers are concealed. Financial
mutations require idempotency, execute under PostgreSQL row locks, and atomically commit
transaction, journal, position, and audit changes. Append-only triggers and reversal uniqueness
backstop service logic. See `portfolio-threat-model.md`.

CI runs a fail-closed governed pnpm audit verifier. It permits only
GHSA-mh99-v99m-4gvg/CVE-2026-14257 at the recorded workspace ESLint/minimatch paths before 2026-10-28 and
fails for a new path, advisory, severity change, or expiry. Python audit remains unexcepted.
