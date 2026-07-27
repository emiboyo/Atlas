# Atlas AI Milestone 2 Report

> **Final status: CONDITIONAL PASS**
>
> The identity and access-management implementation, native quality gates, PostgreSQL
> migrations, security tests, integration tests, Docker image builds, and healthy four-service
> Compose-stack validation pass. The status remains conditional because the two temporary,
> development-only Milestone 1 security risk exceptions remain active.
>
> This report does not authorise production deployment, public customer access, live trading,
> custody, investment management, or handling real customer funds. Milestone 1 governance
> restrictions remain in force.

## 1. Executive summary

Milestone 2 adds the private-development identity foundation for Atlas AI. Clerk remains the
external authentication provider, while Atlas PostgreSQL is authoritative for local user
lifecycle, profiles, onboarding, workspaces, memberships, platform roles, organisation roles,
permissions, and audit records.

The implementation includes cryptographic server-side token verification, fail-closed protected
routes, signed and idempotent Clerk webhooks, one personal workspace per provisioned user,
central permission evaluation, object-level tenant isolation, final-owner database protection,
safe account deactivation, identity-only protected web screens, and CI integration.

All executed application gates pass: 44 Python tests at 81.91% coverage, 8 JavaScript tests,
formatting, linting, strict typing, builds, dependency consistency, production Python dependency
audit, real PostgreSQL integration, reversible migrations, Docker builds, Compose health, and
runtime endpoint checks. The authoritative outcome is `CONDITIONAL PASS` under the existing
development-only risk decisions.

## 2. Architecture implemented

The request path is:

1. FastAPI extracts a bearer token.
2. The Clerk verifier resolves a cached JWKS signing key and verifies RS256 signature, issuer,
   optional audience, expiry, not-before, issued-at, subject, session ID, and authorised party.
3. The verified Clerk subject resolves to an active Atlas user.
4. Atlas loads the target organisation membership by internal immutable IDs.
5. The central authorisation service evaluates the required permission.
6. A service applies domain rules and an explicit transaction.
7. Sensitive state changes append a safe identity audit event.

Routes do not expose SQLAlchemy entities directly. Pydantic request and response models form the
API boundary; repositories contain persistence queries; services own identity and organisation
rules; dependencies derive trusted server-side identity.

## 3. Existing architecture preserved

- Existing Next.js, FastAPI, PostgreSQL, Redis, SQLAlchemy, Alembic, Clerk, Stripe, Docker,
  metrics, health, error, request-ID, logging, and security-header foundations remain.
- Historical revisions `20260724_0001` and `20260724_0002` were not rewritten.
- Existing financial, ledger, billing, and webhook-inbox models remain intact.
- No Milestone 3, trading, portfolio, recommendation, market-data, brokerage, custody, payment
  execution, AI-agent, Terraform apply, or deployment work was performed.
- ADR 0007 explicitly supersedes only ADR 0002's proposed Clerk-organisation authority.
  ADR 0002 continues to govern Clerk authentication and internal tenant keys.

## 4. Database changes

The existing `users`, `tenants`, and `memberships` tables were extended without replacing their
immutable Atlas IDs:

- users: lifecycle status, controlled platform role, deactivation timestamp;
- tenants: personal/team type, creator reference, archived lifecycle state;
- memberships: typed owner/admin/member/viewer roles and tenant/status/role index;
- user profiles: minimal application profile and server-persisted onboarding state;
- identity audit events: append-only security and access history;
- Clerk webhook events: idempotency key, safe digest, status, timestamps, and bounded failure
  classification without raw payload storage.

Foreign keys, uniqueness, check constraints, query indexes, timezone-aware timestamps, an
append-only audit trigger, and a transaction-scoped final-owner trigger are present.

## 5. Migration revision

- Previous head: `20260724_0002`
- Milestone 2 head: `20260727_0003`
- File: `packages/database/alembic/versions/20260727_0003_identity_access_foundation.py`

Verified against PostgreSQL 16:

- previous head to new head: passed;
- new head down to previous head: passed;
- re-upgrade to new head: passed;
- empty database through all revisions: passed;
- model/migration drift with `alembic check`: none;
- final database revision: `20260727_0003 (head)`;
- expected new tables: 3/3;
- sampled required indexes: 4/4.

## 6. Identity model

`User` uses an Atlas UUID primary key and a unique Clerk subject. It stores no password, session
token, cookie, refresh token, or authentication secret. Lifecycle values are `pending`, `active`,
`suspended`, and `deactivated`. The default platform role is `user`; public profile inputs cannot
change it. Deactivated and suspended users fail the active-user dependency.

## 7. Profile model

`UserProfile` is one-to-one with `User` and contains only display name, optional first/last name,
locale, IANA timezone, optional two-letter country, three-letter base currency, onboarding state,
and timestamps. It deliberately excludes birth date, tax ID, passport, bank, KYC, suitability,
and trading-eligibility data.

## 8. Organisation model

`Tenant` is the preserved internal organisation/workspace entity. It supports `personal` and
`team` types and active, suspended, archived, and closed states. Slugs and external mapping keys
are unique. The creator is retained by immutable Atlas user ID. Ordinary access mutations require
an active organisation.

## 9. Membership model

A membership joins one Atlas user to one organisation and has an Atlas UUID, lifecycle status,
and owner/admin/member/viewer role. The existing tenant/user unique constraint prevents duplicate
membership rows. Services prevent duplicate active access. The database final-owner trigger uses
a tenant-scoped PostgreSQL advisory transaction lock before an owner demotion or removal, closing
the concurrent-request race that an application-only count would leave open.

## 10. Role and permission matrix

| Permission          | Owner | Admin | Member | Viewer |
| ------------------- | ----: | ----: | -----: | -----: |
| organisation:read   |   yes |   yes |    yes |    yes |
| organisation:update |   yes |   yes |     no |     no |
| membership:read     |   yes |   yes |    yes |    yes |
| membership:invite   |   yes |   yes |     no |     no |
| membership:update   |   yes |   yes |     no |     no |
| membership:remove   |   yes |   yes |     no |     no |
| ownership:transfer  |   yes |    no |     no |     no |
| audit:read          |   yes |   yes |     no |     no |
| profile:read:self   |   yes |   yes |    yes |    yes |
| profile:update:self |   yes |   yes |    yes |    yes |

The matrix lives in one `AuthorisationService`. Owner assignment and ownership transfer require
an existing owner. Platform roles are separate and are not public self-service fields.

## 11. Clerk verification design

- RS256 is the only accepted algorithm.
- Signature keys resolve from configured Clerk JWKS with caching, bounded lifetime, network
  timeout, and key-rotation support from `PyJWKClient`.
- Issuer, optional audience, expiry, not-before, issued-at, subject, session, and authorised
  party are validated.
- Malformed, expired, wrong-issuer, wrong-audience, and unknown-key tokens are rejected.
- JWKS connection failures return a stable safe `503`; verification failures return `401`.
- Missing Clerk configuration uses an unavailable verifier. Protected APIs and the protected web
  layout fail closed; no development bypass exists.
- Claims are not used before cryptographic verification, and tokens are neither persisted nor
  logged.

## 12. Webhook synchronisation and idempotency

`POST /api/v1/webhooks/clerk` preserves the raw request body and validates Svix ID, timestamp,
signature, replay tolerance, and payload size. HMAC comparison is constant-time. Only
`user.created`, `user.updated`, and `user.deleted` are acted upon.

The inbox has a unique Svix ID, SHA-256 payload digest, status, event type, subject, timestamps,
and safe failure reason. It stores no full webhook payload. Repeated delivery is a no-op;
failed events may be retried; deletion tombstones/deactivates the local user; provisioning is
idempotent and creates one personal workspace.

## 13. Onboarding flow

The server persists `profile_required`, `workspace_required`, and `completed` state. Profile data
can be saved and refreshed before completion. Completion is idempotent and requires a profile and
personal workspace. It does not represent KYC, suitability, investment approval, eligibility to
trade, or regulatory approval. No consent model existed to extend in this milestone.

## 14. Account-deactivation behaviour

Deactivation requires the exact confirmation text and a recently issued verified identity. It
changes the Atlas user lifecycle and appends an audit event. Subsequent normal protected access
is denied even if the Clerk session remains cryptographically valid. Users, memberships,
organisations, ledger records, and audit history are retained. This is not deletion or GDPR
erasure; a separate privacy workflow remains deferred.

## 15. API endpoints

All endpoints are versioned under `/api/v1`.

- Identity: `GET /auth/context`, `GET /me`, `PATCH /me/profile`, `POST /me/deactivate`
- Onboarding: `GET /onboarding`, `PATCH /onboarding/profile`, `POST /onboarding/complete`
- Organisations: `GET/POST /organisations`,
  `GET/PATCH /organisations/{organisation_id}`
- Memberships: `GET/POST /organisations/{organisation_id}/members`,
  `PATCH/DELETE /organisations/{organisation_id}/members/{membership_id}`
- Ownership: `POST /organisations/{organisation_id}/transfer-ownership`
- Audit: `GET /organisations/{organisation_id}/audit-events`
- Clerk webhook: `POST /webhooks/clerk`

List endpoints use bounded pagination. Protected endpoint identities come from verified tokens.
Unrelated tenant objects return `404`; missing identity returns `401`; disallowed permissions
return `403`; stable error bodies include request IDs.

## 16. Frontend routes and screens

- `/sign-in/[[...sign-in]]`
- `/sign-up/[[...sign-up]]`
- `/app`
- `/app/onboarding`
- `/app/profile`
- `/app/organisations`
- `/app/organisations/[organisationId]`

The protected layout performs a server-side Clerk check when public Clerk configuration exists
and otherwise shows a fail-closed unavailable state. The responsive identity-only dashboard has
authenticated navigation, profile/sign-out control, loading/error/empty states, profile and
onboarding forms, workspace listing/creation, role-sensitive membership controls, deactivation,
and dark/light theme support. Server APIs remain authoritative even where controls are hidden.

## 17. Security controls

- cryptographic Clerk verification and fail-closed disabled mode;
- server-authoritative user, membership, tenant, role, and permission resolution;
- object-level tenant isolation with existence concealment;
- no email-based authorisation;
- no token persistence, browser local-storage token handling, or token logging;
- request body limits, replay tolerance, constant-time webhook verification, and idempotency;
- Pydantic `extra=forbid` mass-assignment protection;
- local platform roles excluded from profile updates;
- IANA timezone and ISO-style country/currency validation;
- database role/lifecycle constraints, foreign keys, uniqueness, append-only audit trigger, and
  concurrent final-owner protection;
- recent authentication plus explicit confirmation for deactivation;
- existing CSP, clickjacking, trusted-host, CORS, structured-error, and request-ID controls
  preserved.

Browser mutations use Clerk bearer tokens and do not rely on ambient application cookies.
User-supplied names are rendered as React text. No redirect parameter or open-redirect mechanism
was introduced.

## 18. Tenant-isolation evidence

Executed PostgreSQL-backed integration tests demonstrate:

- a verified principal reaches `/api/v1/me`;
- a user from Organisation A receives concealed `404` for Organisation B;
- an owner can add a member and transfer ownership;
- a viewer receives `403` when attempting organisation mutation;
- final-owner demotion receives `409` from database-enforced integrity protection;
- audit history records ownership transfer;
- deactivation causes subsequent protected access to receive `403`.

## 19. Tests added

Backend and database coverage includes token success/failure claims, wrong issuer/audience,
expiry, unknown key, JWKS failure, fail-closed mode, active-user lifecycle, profile validation,
mass assignment, permission matrix, recent authentication, valid/invalid/stale webhooks,
oversized webhook declarations, idempotent provisioning, exactly-one personal workspace,
onboarding persistence, cross-tenant IDOR, viewer role escalation denial, final-owner protection,
ownership transfer, audit creation, and deactivation.

Frontend coverage includes sign-in/sign-up routes, protected-layout fail-closed behaviour, and
the identity-only dashboard contract, alongside existing homepage and shared/UI tests.

External providers were not called; tests use generated local keys, dependency overrides, and an
isolated local PostgreSQL cluster.

## 20. Commands executed

Successful final gates:

```text
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
python -m ruff format --check apps packages/database
python -m ruff check apps packages/database
python -m mypy apps/api/src packages/database/atlas_database
pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
python -m pip check
python -m pip_audit -r apps/api/requirements.txt
alembic -c packages/database/alembic.ini downgrade 20260724_0002
alembic -c packages/database/alembic.ini upgrade head
alembic -c packages/database/alembic.ini check
docker compose config --quiet
git diff --check
```

Migration validation also created a fresh isolated database, ran `alembic upgrade head`, verified
`20260727_0003 (head)`, and removed that temporary database.

Commands with governed advisory findings:

```text
pnpm audit --prod
pnpm audit
```

`pnpm audit` reports the already governed `GHSA-mh99-v99m-4gvg / CVE-2026-14257`
`brace-expansion` development-toolchain advisory. No incompatible forced override was retained.
The risk decision, scope, controls, owner, and expiry are authoritative in
`docs/security-risk-exceptions.md` and
`docs/adr/0006-milestone-1-security-risk-decision.md`. This did not cause a quality gate failure
because the existing temporary development-only governance decision explicitly permits
Milestone 2 private development.

The first Docker attempt failed because the Docker Desktop Linux engine was unavailable. After
Docker Desktop started, the exact Docker sequence was rerun successfully. Both application
images built, all four services became healthy, the Compose database was migrated from
`20260724_0002` to `20260727_0003`, downgraded, re-upgraded, and left at the Milestone 2 head.
The initial environmental failure is resolved.

Docker Scout was also retried:

```text
docker scout cves atlas-ai-api:latest --only-severity critical,high
docker scout cves atlas-ai-web:latest --only-severity critical,high
```

Both commands exited `1` because Docker Scout requires a Docker ID login on this workstation.
No login or credential change was attempted, and no fresh Scout result is claimed. The existing
advisory evidence and manual decisions remain documented in `docs/security-risk-exceptions.md`,
`docs/adr/0006-milestone-1-security-risk-decision.md`, and `docs/milestone-1-audit.md`. This is a
manual tooling limitation rather than an application runtime, build, or Compose-health failure.

## 21. Test and coverage results

- Python: 44 passed; 81.91% combined API/database coverage; 80% gate passed.
- Web: 5 passed.
- Shared package: 1 passed.
- UI package: 2 passed.
- JavaScript/TypeScript total: 8 passed.
- Ruff format/lint: passed.
- strict mypy: passed, 35 source files.
- Prettier, ESLint, TypeScript, and production build: passed.
- `pip check`: no broken requirements.
- production Python `pip-audit`: no known vulnerabilities.
- Next.js production build: passed for all public, protected, onboarding, profile,
  organisation, and Clerk routes.

An earlier coverage run failed at 77.77% after the initial implementation. Integration and
security tests were added for the previously uncovered identity paths; final coverage is 81.91%.
The failure is resolved.

An initial PostgreSQL integration run exposed uppercase SQLAlchemy enum names against lowercase
migration constraints. Enum persistence was corrected to use enum values, the migration was
aligned, and downgrade/re-upgrade plus drift and integration tests passed. The failure is
resolved.

## 22. Docker validation result

- `docker compose config --quiet`: PASS
- `docker compose build`: PASS; `atlas-ai-api` and `atlas-ai-web` built
- `docker compose up --detach --wait`: PASS
- `docker compose ps`: PASS
- PostgreSQL 16.9 Alpine: healthy
- Redis 7.4.5 Alpine: healthy
- FastAPI: healthy on port 8000
- Next.js: healthy on port 3000
- API runtime: non-root `atlas`, read-only root filesystem, `no-new-privileges`
- Web runtime: non-root `nextjs`, read-only root filesystem, `no-new-privileges`
- Compose database final revision: `20260727_0003 (head)`
- Web homepage: HTTP 200
- Liveness: HTTP 200
- Readiness: HTTP 200 with PostgreSQL and Redis healthy
- Metrics: HTTP 200
- Development OpenAPI: HTTP 200
- Unauthenticated auth context, identity, onboarding, and organisation routes: HTTP 401 with
  stable error codes and request IDs

Docker and runtime endpoint acceptance gates pass.

## 23. Files created

- `apps/api/src/core/clerk_webhooks.py`
- `apps/api/src/identity/__init__.py`
- `apps/api/src/identity/authorization.py`
- `apps/api/src/identity/dependencies.py`
- `apps/api/src/identity/repositories.py`
- `apps/api/src/identity/routes.py`
- `apps/api/src/identity/schemas.py`
- `apps/api/src/identity/services.py`
- `apps/api/tests/test_identity.py`
- `apps/api/tests/test_identity_integration.py`
- `apps/web/src/app/app/layout.tsx`
- `apps/web/src/app/app/page.tsx`
- `apps/web/src/app/app/onboarding/page.tsx`
- `apps/web/src/app/app/profile/page.tsx`
- `apps/web/src/app/app/organisations/page.tsx`
- `apps/web/src/app/app/organisations/[organisationId]/page.tsx`
- `apps/web/src/app/sign-in/[[...sign-in]]/page.tsx`
- `apps/web/src/app/sign-up/[[...sign-up]]/page.tsx`
- `apps/web/src/components/account-navigation.tsx`
- `apps/web/src/components/deactivation-panel.tsx`
- `apps/web/src/components/onboarding-panel.tsx`
- `apps/web/src/components/organisation-list.tsx`
- `apps/web/src/components/organisation-panel.tsx`
- `apps/web/src/components/profile-form.tsx`
- `apps/web/src/lib/api-client.ts`
- `apps/web/src/test/identity.test.tsx`
- `packages/database/alembic/versions/20260727_0003_identity_access_foundation.py`
- `docs/adr/0007-local-tenancy-and-authorisation.md`
- `docs/identity-architecture.md`
- `docs/authorisation-model.md`
- `docs/onboarding.md`
- `docs/identity-threat-model.md`
- `docs/milestone-2-report.md`

## 24. Files modified

- `.env.example`
- `.github/workflows/test.yml`
- `README.md`
- `apps/api/.env.example`
- `apps/api/requirements.txt`
- `apps/api/src/api/v1/router.py`
- `apps/api/src/api/v1/webhooks.py`
- `apps/api/src/core/config.py`
- `apps/api/src/core/security.py`
- `apps/api/tests/test_security.py`
- `apps/web/.env.example`
- `apps/web/src/app/globals.css`
- `docs/authentication-and-authorization.md`
- `docs/data-classification.md`
- `docs/local-development.md`
- `docs/release-readiness.md`
- `docs/security.md`
- `docs/testing.md`
- `packages/database/atlas_database/models/__init__.py`
- `packages/database/atlas_database/models/enums.py`
- `packages/database/atlas_database/models/identity.py`
- `packages/database/atlas_database/models/ledger.py`
- `packages/database/tests/test_models.py`

The worktree also contains understood Milestone 1 audit/stabilisation changes that predated this
milestone. They were preserved and not discarded.

## 25. Known limitations

- Real Clerk-hosted sign-in and webhook delivery require private developer configuration and
  were intentionally not exercised with real credentials.
- The UI supports adding an already-provisioned Atlas user by immutable Atlas user ID; it does
  not pretend to implement email invitation.
- Clerk session revocation is not called during deactivation. Atlas access is nevertheless
  denied immediately by the local active-user check.
- No privacy erasure, KYC, compliance verification, enterprise tenancy, platform-admin UI, or
  Clerk Organisation synchronisation exists.
- The existing governed JavaScript development-toolchain advisory remains until a compatible
  patched dependency chain is available.

## 26. Deferred work

Deferred beyond Milestone 2: email invitation, consent versioning, privacy erasure workflow,
external KYC, enterprise tenancy, privileged operational UI, synchronised Clerk Organisations,
provider-level session revocation, and all investment/trading/portfolio/market/AI functionality.
These are not authorised by this report.

## 27. Manual configuration still required

For private local development only:

1. Copy application `.env.example` files to their local ignored equivalents.
2. Use Clerk development-instance values only:
   `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `ATLAS_CLERK_ISSUER_URL`,
   `ATLAS_CLERK_JWKS_URL`, optional audience, authorised parties, and a development webhook
   signing secret.
3. Do not put `CLERK_SECRET_KEY` or any server secret in a `NEXT_PUBLIC_*` variable.
4. Configure Clerk redirect URLs for local `/sign-in`, `/sign-up`, and `/app`.
5. Repeat Docker builds, service health checks, dependency audits, and image scans after
   dependency or base-image changes.
6. Preserve the Milestone 1 risk-exception review and expiry controls.

No production credentials, deployment, public access, or real-money use is permitted.

## 28. Final status

**CONDITIONAL PASS**

All technical Milestone 2 acceptance gates pass, including Docker image builds, healthy Compose
services, migrations, runtime endpoints, cryptographic authentication tests, authorisation,
tenant isolation, frontend build, and coverage. The result is conditional solely because the
temporary development-only security decisions for
`GHSA-mh99-v99m-4gvg / CVE-2026-14257` and `CVE-2026-12087` remain in force.

This conditional pass applies only to the Milestone 2 technical identity foundation. It does not
authorise production deployment, public customer access, live trading, custody, investment
management, real-money investing, or handling real customer funds.
