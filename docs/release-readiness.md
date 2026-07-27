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

Milestone 3 remediation is implementation evidence only. The independent audit remains FAIL until
a separate re-audit verifies M3-AUD-001 through M3-AUD-005. Milestone 4 and production promotion
remain blocked pending that decision.
