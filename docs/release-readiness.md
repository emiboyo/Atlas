# Release readiness

## Milestone 2 production blockers

- [ ] Independent identity security review completed.
- [ ] Temporary security exceptions reviewed and replaced or explicitly renewed.
- [ ] Real Clerk production issuer, audience, authorised parties, JWKS, and Svix configuration
      reviewed outside source control.
- [ ] Clerk key rotation and JWKS outage runbooks exercised.
- [ ] Application and perimeter rate limits implemented and tested.
- [ ] Production tenant-isolation and final-owner concurrency tests passed.
- [ ] Privacy, retention, consent, and account-erasure workflows approved.
- [ ] No production deployment, public access, live trading, real-money investing, or custody is
      enabled by this milestone.

This checklist is a gate, not a deployment command.

## Required evidence

- [ ] `pnpm install --frozen-lockfile` succeeds on Node.js 22.14.0 with pnpm 10.12.1.
- [ ] Python production and development dependencies install on Python 3.12.10.
- [ ] Formatting, linting, strict type checks, tests, and production builds pass.
- [ ] Terraform formatting and validation pass with backend initialization disabled.
- [ ] Docker Compose configuration validates.
- [ ] Fresh PostgreSQL migration upgrade, downgrade, and re-upgrade succeed.
- [ ] Web, API, PostgreSQL, and Redis containers are healthy.
- [ ] Homepage, Swagger, liveness, readiness, and metrics respond from the host.
- [ ] Readiness reports PostgreSQL and Redis healthy.
- [ ] Secret scanning finds no real credentials or private data.
- [ ] Dependency and container vulnerability scans have been reviewed.
- [ ] Database backup/restore and rollback procedures match the release.

## CI and deployment controls

- Pull requests may lint, test, build, scan, and validate Terraform; they must never apply it.
- AWS deployment is manual and must target a protected GitHub environment with required reviewers.
- GitHub OIDC roles must be environment- and repository-scoped with least-privilege policies.
- Production images use immutable commit-SHA tags and are promoted rather than rebuilt.
- Database migrations run as a one-off task and must succeed before service rollout.
- Vercel and AWS configuration must use their secret stores, never repository environment files.

## Production configuration

The API refuses production startup when debug mode, local database/cache URLs, local or wildcard
CORS origins, unsafe trusted hosts, or missing Clerk endpoints are detected. Swagger, ReDoc, and
the OpenAPI document are disabled in production. Stripe webhook handling remains unavailable until
a valid webhook secret is supplied and every request must pass signature verification.

## Known gates after the Milestone 1 audit

The audit report is authoritative. Any criterion marked blocked or failed there must be rerun and
recorded before the milestone can be promoted. In particular, an offline Alembic pass cannot
replace real PostgreSQL execution, and a valid Compose file cannot replace starting healthy
containers.

Milestone 3 does not approve a production market-data provider, entitlement, exchange licence,
redistribution right, service-level objective, freshness policy, commercial quota, corporate
action process, or real-time claim. The deterministic provider is private-development test data.
Production remains prohibited under the existing governance decisions.

## Current milestone governance status

- Milestone 3 technical status: **Conditional Pass — Private Development Controls Only**.
- Milestone 4 private development: authorised under committed
  [`milestone-4-governance.md`](milestone-4-governance.md) and
  [ADR 0009](adr/0009-milestone-4-private-development-authorisation.md).
- Production readiness: prohibited.
- Public readiness: prohibited.
- Live-provider readiness: prohibited.
- Real-money readiness: prohibited.
- Milestone 5: not authorised.

Milestone 4 authority is limited to simulated portfolio accounting and read-only descriptive
analytics. It does not satisfy a production checklist item or weaken an existing exception.

## Milestone 4 technical evidence required

- [ ] Revision `20260728_0006` upgrades from and downgrades to `20260727_0005`.
- [ ] Fresh PostgreSQL migration and Alembic drift check pass.
- [ ] Monetary journals balance per currency and posted history is append-only.
- [ ] Independent-session duplicate, overspend, oversell, and reversal tests pass.
- [ ] Cross-tenant objects are concealed and permissions match the central matrix.
- [ ] Stale, missing, unavailable, simulated, and unconverted values remain explicit.
- [ ] Python coverage is at least 80%; frontend tests and production build pass.
- [ ] Compose services are healthy with non-root/read-only/no-new-privileges controls.
- [ ] Governed dependency findings remain owned, reviewed, unexpired, and development-only.
- [ ] An independent Milestone 4 audit reviews the implementation and report.

Milestone 4 completion by itself does not authorise production, public access, real money,
trading, orders, custody, advice, customer funds, live providers, deployment, or Milestone 5.
Milestone 5 authority comes only from the separate governance decision below.

## Milestone 5 governance status

- Milestone 4 audit: **Conditional Pass — Private Development Only**.
- Milestone 5 private development: authorised only after
  [`milestone-5-governance.md`](milestone-5-governance.md) and
  [ADR 0014](adr/0014-milestone-5-private-development-authorisation.md) are committed.
- Scope: explainable strategy research, historical backtesting, and simulation using stored Atlas
  data or deterministic fixtures.
- Production/public/live-trading/real-money/advisory/autonomous-action readiness: prohibited.
- Risk owner: Adebayo Olaegbe.
- Review: 2026-08-27.
- Expiry: 2026-10-27.
- Milestone 6: prohibited.

Milestone 5 completion will not satisfy a production checklist item. A future implementation must
be independently audited for look-ahead bias, leakage, reproducibility, provenance, model risk,
tenant isolation, fixed precision, append-only results, non-advisory language, and the absence of
execution capability.
