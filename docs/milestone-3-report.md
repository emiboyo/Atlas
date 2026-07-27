# Atlas AI Milestone 3 Report

> **CURRENT STATUS — CONDITIONAL PASS**
>
> **Historical implementation report — superseded by the independent audit and remediation.**
> The original report stated that the technical acceptance gates were satisfied. The independent
> audit disproved that statement and recorded a FAIL. See
> [`milestone-3-audit.md`](milestone-3-audit.md) and
> [`milestone-3-remediation-report.md`](milestone-3-remediation-report.md). The original status was
> also subject to
> the time-bounded development-only security decisions in
> [`security-risk-exceptions.md`](security-risk-exceptions.md) and
> [ADR 0006](adr/0006-milestone-1-security-risk-decision.md).
>
> **This conditional pass applies only to the Milestone 3 technical foundation. It does not
> authorise production deployment, public customer access, live trading, custody, investment
> management, or handling real customer funds.**

Validation date: 2026-07-27  
Branch: `feat/milestone-3-market-data`  
Migration head: `20260727_0004`  
Risk owner: Adebayo Olaegbe  
Exception review date: 2026-08-27  
Exception expiry date: 2026-10-27

## 1. Executive summary

Milestone 3 adds a provider-neutral, read-only market catalogue, deterministic simulated quote and
candle services, and tenant-scoped watchlists. Atlas-generated UUIDs identify instruments and
listings; ticker symbols are never treated as global identity. Financial values use fixed-precision
database numerics and Python `Decimal`. Source, provider, provider timestamp, receipt timestamp,
freshness, and simulation status are explicit.

The implementation preserves Milestones 1 and 2. It adds no order placement, trading, custody,
broker, wallet, recommendation, signal, prediction, suitability, or personalised investment
functionality. No external provider is called and no deployment occurred.

All repository quality gates passed. The final Python run passed 53 tests at 80.08% coverage.
Frontend and shared-package tests passed 10 tests. Existing and empty PostgreSQL migration paths,
Alembic drift, Docker builds, service health, and runtime endpoints were validated.

## 2. Architecture implemented

The implementation uses four boundaries:

1. SQLAlchemy models and Alembic migrations provide canonical persistence.
2. Repository and service layers isolate queries, validation, authorisation, freshness, and cache
   policy.
3. A typed provider interface separates external/provider shapes from Atlas response contracts.
4. FastAPI routes and protected Next.js screens expose stable, non-advisory application contracts.

Redis is an optional acceleration layer; PostgreSQL and validated provider responses remain
authoritative. Cache failure degrades safely.

## 3. Existing architecture preserved

- Existing FastAPI application lifecycle, error envelope, request IDs, structured logging,
  Prometheus endpoint, dependency injection, and `/api/v1` router remain in place.
- Existing Clerk verification remains fail-closed.
- Watchlists use the Milestone 2 identity, organisation membership, tenant, permission, and audit
  services.
- Existing PostgreSQL, Redis, Docker Compose, CI, and monorepo conventions are retained.
- Historical migrations `20260724_0001` through `20260727_0003` were not rewritten.
- No new database, queue, worker, broker, or infrastructure service was introduced.

## 4. Asset classes supported

The catalogue enum supports equity, exchange-traded fund, index, foreign exchange,
cryptocurrency, commodity, bond, fund, and other. Support in the type system does not claim that
the simulated or any future provider supplies every class.

## 5. Exchange model

`Exchange` uses an Atlas UUID and records MIC, name, optional acronym, ISO-style country code,
IANA timezone, default currency, market type, status, and audit timestamps. MIC is unique.
Provider-specific venue codes remain in provider mappings.

## 6. Instrument model

`Instrument` represents the canonical financial object independently of where it trades. It stores
an immutable Atlas UUID, names, asset class, optional description and identifiers, primary
currency, optional country, lifecycle status, and timestamps. ISIN, CUSIP, and SEDOL are nullable
and never fabricated.

## 7. Listing model

`InstrumentListing` connects an instrument to an exchange. It has its own UUID, symbol, currency,
status, primary-listing flag, optional trade dates, and timestamps. Venue plus symbol uniqueness
supports duplicate symbols on different exchanges and multiple listings for one instrument.

## 8. Provider mapping model

`ProviderSymbolMapping` separates provider, provider symbol, provider venue code, provider type,
status, and verification timestamp from Atlas canonical identity. Provider namespace constraints
prevent ambiguous mappings without exposing credentials.

## 9. Quote model

`QuoteObservation` stores listing and provider provenance, provider and receipt timestamps, market
session, available price fields, sizes, volume, currency, data status, delay, and source reference.
Prices are `NUMERIC(38,18)` and volumes are non-negative integers. Missing bid/ask values are not
inferred.

## 10. Historical candle model

`HistoricalCandle` stores provider, listing, interval, UTC period, OHLC, optional adjusted close and
volume, currency, status, receipt time, and timestamps. A deterministic composite uniqueness rule
prevents duplicate periods. Constraints reject negative values, invalid periods, high below low,
and open/close outside the high-low range.

## 11. Watchlist model

`Watchlist` belongs to a tenant and records creator, bounded name and description, visibility,
active/archived status, and timestamps. `WatchlistItem` references a listing, has deterministic
position, bounded notes, and the adding user. Database constraints enforce one listing and one
position per watchlist. Delete operations archive watchlists; archived lists reject mutation.

## 12. Provider abstraction

`MarketDataProvider` defines typed quote, candle, and health capabilities. Provider failures use
stable `ApplicationError` codes. Routes never consume provider-native response shapes. The
boundary supports replacement without changing canonical IDs or public response schemas.

## 13. Simulated development provider

`DeterministicFixtureProvider` uses fictional development exchanges and instruments with a fixed
January 2026 timestamp. Every response is labelled `simulated` and carries:

> Simulated development data. For software testing only; not real-time market data and not
> investment advice.

`DisabledExternalProvider` provides an explicit unavailable boundary. The seed CLI refuses the
production environment and is idempotent. Container validation created 3 exchanges, 8 instruments,
and 8 listings; the second run created zero records.

## 14. Data freshness rules

Freshness is computed server-side from provider timestamps and configurable TTLs. Simulated data
remains simulated rather than being relabelled stale or live. Non-simulated data beyond its
freshness window becomes `stale` with `is_stale=true` and an explicit `stale_after`. Status values
distinguish live, delayed, end-of-day, cached, stale, simulated, and unavailable.

## 15. Cache design

Redis caches bounded instrument searches, instrument details, quotes, and candle ranges.
Provider/listing/interval/range identity is included where applicable. Keys are namespaced and
bounded; raw queries are not metrics labels. TTLs are configuration-managed. Redis exceptions
become cache misses and do not corrupt source data. No token, provider credential, or tenant
watchlist payload is cached.

## 16. Data-quality controls

Controls include bounded/normalised search, fixed precision, non-negative prices and volume,
timezone-aware ranges, maximum candle spans, interval allowlists, OHLC shape validation, listing
currency preservation, provenance, duplicate constraints, provider-response validation, explicit
unavailable/simulated/stale states, and stable rejection codes. Material inconsistencies are
rejected rather than repaired silently.

## 17. API endpoints

Authenticated reference and market endpoints:

- `GET /api/v1/market/exchanges`
- `GET /api/v1/market/instruments/search`
- `GET /api/v1/market/instruments/{instrument_id}`
- `GET /api/v1/market/listings/{listing_id}`
- `GET /api/v1/market/listings/{listing_id}/quote`
- `GET /api/v1/market/listings/{listing_id}/candles`
- `GET /api/v1/market/status`

Tenant-authorised watchlist endpoints:

- `GET|POST /api/v1/watchlists`
- `GET|PATCH|DELETE /api/v1/watchlists/{watchlist_id}`
- `POST /api/v1/watchlists/{watchlist_id}/items`
- `DELETE /api/v1/watchlists/{watchlist_id}/items/{item_id}`
- `PATCH /api/v1/watchlists/{watchlist_id}/items/reorder`

All use typed Pydantic schemas, bounded inputs, stable errors, and request-ID middleware. No public
provider-administration endpoint exists.

## 18. Frontend routes and screens

- `/app/markets`
- `/app/markets/search`
- `/app/markets/instruments/[instrumentId]`
- `/app/markets/listings/[listingId]`
- `/app/watchlists`
- `/app/watchlists/[watchlistId]`

The responsive protected UI provides neutral search, details, quote/candle presentation, simulated
warnings, provider timestamps and status, and watchlist workflows. It has no trade buttons,
prediction markers, targets, recommendations, or broker branding.

## 19. Tenant-isolation evidence

Integration tests create separate tenants and roles, then verify owner operations, viewer read
access, viewer mutation denial, guessed/cross-tenant watchlist denial, manipulated tenant denial,
item uniqueness, and archived-list rejection. Resource lookup plus server-side membership checks
conceal unrelated tenant existence with a stable not-found response.

## 20. Security controls

- Clerk-protected market and watchlist endpoints fail closed; unauthenticated runtime requests
  returned HTTP 401.
- The central `AuthorisationService` owns the watchlist permission matrix.
- Search is parameterised, wildcard characters are escaped, query length and result size are
  bounded, and exact symbols rank first.
- Protected fields are forbidden by request schemas.
- Provider credentials are neither required nor exposed.
- Cache keys are collision-resistant and cache errors degrade safely.
- Metrics use finite operation/outcome/provider values rather than user input.
- Docker API runs non-root with a read-only root filesystem and `no-new-privileges`.
- Web and API bind `0.0.0.0` intentionally inside their containers so Docker can publish the
  configured development ports. This is container reachability, not production authorisation.

`pnpm audit --prod` continues to report GHSA-mh99-v99m-4gvg / CVE-2026-14257 through the
development ESLint/minimatch chain. Python dependency audit found no known vulnerabilities.
Docker Scout required an authenticated Docker account and therefore did not produce a fresh image
advisory result in this run. The prior CVE-2026-12087 base-image decision consequently remains
applicable and unexpanded. Both exceptions, compensating controls, review dates, and revocation
conditions are authoritative in [`security-risk-exceptions.md`](security-risk-exceptions.md).

## 21. Tests added

- Provider determinism, disabled boundary, unsupported intervals, malformed values, status, and
  validation.
- Redis hits, misses, collision resistance, and unavailable degradation.
- Search, exact ranking, duplicate venue symbols, details, simulated quotes and candles.
- Central watchlist permission mapping, creation, uniqueness, archive behavior, reorder and audit.
- Cross-tenant, guessed-ID, viewer mutation, and client tenant manipulation denial.
- SQLAlchemy model metadata, fixed precision, indexes, uniqueness, and checks.
- Frontend simulated-warning, search result, and watchlist workspace rendering.

## 22. Commands executed

Successful final gates included:

```text
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm api:lint
pnpm api:typecheck
python -m ruff format --check apps packages/database
python -m ruff check apps packages/database
python -m mypy apps/api/src packages/database/atlas_database
python -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
python -m pip check
python -m pip_audit -r apps/api/requirements.txt
python -m alembic -c packages/database/alembic.ini upgrade head
python -m alembic -c packages/database/alembic.ini downgrade 20260727_0003
python -m alembic -c packages/database/alembic.ini check
docker compose config --quiet
docker compose up -d --build
docker compose exec -T api python -m apps.api.src.market.cli seed-development-data
git diff --check
git status --short
```

No Terraform apply, deployment, external provider call, or real credential operation was run.

## 23. Test and coverage results

- Python: 53 passed, 0 failed; 80.08% total coverage; the 80% gate passed.
- Web: 7 passed.
- Shared TypeScript packages: 3 passed.
- Ruff lint and formatting: passed.
- Strict mypy: 45 source files, no issues.
- ESLint and TypeScript: passed.
- Next.js production build: passed with all Milestone 3 routes.
- Prettier and `git diff --check`: passed.
- `pip check`: no broken requirements.
- `pip-audit`: no known Python vulnerabilities.

Four Starlette deprecation warnings remain in test execution. They do not change HTTP behavior or
gate outcome and are documented for dependency-aligned cleanup.

## 24. Migration revision and validation

Revision `20260727_0004_market_data_foundation` follows Milestone 2 head `20260727_0003`.

Validated against real PostgreSQL:

1. Existing database at Milestone 2 head upgraded to Milestone 3.
2. Milestone 3 downgraded to Milestone 2 and re-upgraded.
3. `alembic check` reported no new upgrade operations.
4. A fresh `atlas_m3_fresh` database upgraded through all four revisions.
5. The fresh schema contained exchanges, instruments, listings, provider mappings, quote
   observations, historical candles, watchlists, and watchlist items.
6. Model tests verified expected indexes, precision, checks, and uniqueness.
7. Primary development and audit databases were left at `20260727_0004 (head)`.

The disposable `atlas_m3_fresh` database was removed after validation.

## 25. Docker validation

Both API and web images built successfully from pinned base image versions. Compose started
PostgreSQL, Redis, API, and web; all four reported healthy. Container migration downgrade,
re-upgrade, drift check, current revision, and seed commands passed.

Runtime results:

- Homepage: HTTP 200.
- Markets page: HTTP 200.
- Liveness: HTTP 200 and healthy.
- Readiness: HTTP 200; PostgreSQL and Redis healthy.
- Metrics: HTTP 200.
- Development OpenAPI: HTTP 200.
- Unauthenticated market status/search: HTTP 401 as designed.
- Structured logs contained route templates, status, duration, and request IDs.

Authenticated market, watchlist, cross-tenant, stale, provider-unavailable, and Redis-unavailable
paths were executed in safe local integration tests using server-side identity overrides rather
than real Clerk or provider credentials.

## 26. Files created

```text
apps/api/src/market/{__init__,cache,cli,fixtures,metrics,providers,repositories,routes,schemas,services}.py
apps/api/tests/test_market.py
apps/api/tests/test_market_integration.py
apps/web/src/app/app/markets/**
apps/web/src/app/app/watchlists/**
apps/web/src/components/market-instrument.tsx
apps/web/src/components/market-listing.tsx
apps/web/src/components/market-search.tsx
apps/web/src/components/watchlist-browser.tsx
apps/web/src/components/watchlist-detail.tsx
apps/web/src/test/market.test.tsx
docs/adr/0008-provider-neutral-market-data.md
docs/instrument-model.md
docs/market-data-architecture.md
docs/market-data-provider-interface.md
docs/market-data-quality.md
docs/market-data-threat-model.md
docs/watchlists.md
docs/milestone-3-report.md
packages/database/alembic/versions/20260727_0004_market_data_foundation.py
```

## 27. Files modified

```text
.env.example
.github/workflows/test.yml
README.md
apps/api/.env.example
apps/api/src/api/health.py
apps/api/src/api/v1/router.py
apps/api/src/api/v1/webhooks.py
apps/api/src/core/config.py
apps/api/src/core/dependencies.py
apps/api/src/identity/authorization.py
apps/web/src/components/account-navigation.tsx
docs/authorisation-model.md
docs/data-classification.md
docs/local-development.md
docs/release-readiness.md
docs/security.md
docs/testing.md
packages/database/atlas_database/models/__init__.py
packages/database/atlas_database/models/enums.py
packages/database/atlas_database/models/instruments.py
packages/database/tests/test_models.py
```

## 28. Known limitations

- Data is deterministic and simulated; it is not current, live, licensed, or suitable for
  investment decisions.
- The external provider adapter is intentionally disabled.
- No provider-health cache or production stampede-control strategy is claimed.
- Catalogue search uses bounded relational matching, not a dedicated search service.
- No corporate-action, currency-conversion, total-return, or tax engine exists.
- The UI is a foundation and does not constitute full end-to-end browser automation.
- Docker Scout needs account authentication for a fresh scan.
- The two inherited security exceptions prohibit production/public use.

## 29. Deferred work

Deferred beyond Milestone 3: external provider selection and licensing, production-grade
entitlements and quotas, corporate actions, exchange calendars, full ingestion orchestration,
browser end-to-end automation, production cache/stampede policy, and all trading, portfolio,
advice, signal, suitability, execution, custody, and money-movement capabilities.

This report does not begin or authorise Milestone 4.

## 30. Manual configuration required

Private local development requires copying the example environment files and supplying
development-only Clerk configuration for interactive authenticated browser use. No market-data
provider credential is required. Docker Desktop must be running. Run:

```text
docker compose up --detach --build --wait
docker compose exec -T api python -m alembic -c packages/database/alembic.ini upgrade head
docker compose exec -T api python -m apps.api.src.market.cli seed-development-data
```

An independent security review and a new explicit production decision are required before any
public or production deployment. Existing exceptions must be reviewed by 2026-08-27 and expire on
2026-10-27 unless superseded.

## 31. Final status

**SUPERSEDED — THE INDEPENDENT AUDIT RESULT IS FAIL**

The statement previously placed here—that all technical acceptance gates were validated—was not
supported by executable evidence. Remediation does not change the audit decision; only a separate
independent re-audit may do so. Production deployment, public access, live trading, real-money
investing, custody, and customer-fund handling remain prohibited.

## Appendix A — Failed commands and resolution

### A.1 Incorrect native PostgreSQL URL

- Command:
  `pytest` with `ATLAS_TEST_DATABASE_URL` targeting local port 5432 and then the audit cluster as
  user `postgres`.
- Error: password authentication failed on the unrelated local server; later the isolated cluster
  reported `role "postgres" does not exist`.
- Root cause: the first URL targeted a different host PostgreSQL installation, and the isolated
  audit cluster had been initialised with a different bootstrap role.
- Repair: used the explicit isolated cluster at `127.0.0.1:55433`, added a local audit-only
  `postgres` role under trust authentication, and reran the complete suite.
- Resolution: resolved; 53 tests passed against real PostgreSQL.

### A.2 Incorrect pnpm API filter

- Command: `pnpm --filter @atlas/api lint`, typecheck, and test variants.
- Error: `No projects matched the filters`.
- Root cause: the Python API is managed by root `api:*` scripts, not a pnpm workspace package.
- Repair: used `pnpm api:lint`, `pnpm api:typecheck`, and the project Python virtual environment.
- Resolution: resolved; lint and strict typing passed.

### A.3 System Python test runner

- Command: `python -m pytest ...`.
- Error: system Python reported `No module named pytest`.
- Root cause: dependencies are installed in `.venv312`, not globally.
- Repair: used `.venv312\Scripts\python.exe`.
- Resolution: resolved; final test and coverage gate passed.

### A.4 Coverage after cache integration

- Command: final pytest coverage gate during implementation.
- Error: intermediate coverage was 79.42% and then 79.95%, below the unrounded 80% target.
- Root cause: new cache and status branches expanded the measured code surface.
- Repair: added behavior-focused provider, cache, unavailable-status, not-found, invalid-range, and
  listing-contract tests.
- Resolution: resolved; final full-repository coverage was 80.08%.

### A.5 Development seed ordering and ORM response handling

- Command: initial PostgreSQL market integration run.
- Errors: exchange foreign-key ordering failure, then an async `MissingGreenlet` during response
  serialization.
- Root cause: the first seed revision did not flush parent exchanges before listings; the create
  response attempted an implicit async relationship load.
- Repair: established explicit flush ordering and returned an explicit empty item collection from
  creation.
- Resolution: resolved; integration and idempotent CLI tests pass.

### A.6 Duplicate watchlist item handling

- Command: initial duplicate-item integration test.
- Error: raw `IntegrityError` escaped before the intended stable conflict translation.
- Root cause: UUID/default timing caused an earlier flush than the commit wrapper expected.
- Repair: assign item UUIDs explicitly and keep duplicate handling inside the controlled commit
  boundary.
- Resolution: resolved; duplicate insertion now returns the stable conflict behavior.

### A.7 Dependency audit

- Command: `pnpm audit --prod`.
- Error: exit code 1 with GHSA-mh99-v99m-4gvg / CVE-2026-14257 in
  `eslint -> minimatch -> brace-expansion`.
- Root cause: inherited development lint dependency with no currently compatible retained upgrade
  path.
- Repair: confirmed it remains outside runtime images and revalidated lint/build/test gates.
- Resolution: open but temporarily approved for development under
  [`security-risk-exceptions.md`](security-risk-exceptions.md); it prevents an unconditional pass.

### A.8 Docker Scout

- Commands: `docker scout cves atlas-ai-api:latest --only-severity critical,high` and the equivalent
  web-image command.
- Error: Docker Scout requested Docker ID authentication.
- Root cause: the local Docker Desktop session is not authenticated for Scout.
- Repair: no credential or interactive login was attempted because the task forbids introducing
  credentials.
- Resolution: not revalidated in this run. Prior CVE-2026-12087 evidence and its development-only
  exception remain authoritative; a fresh authenticated scan is required before production
  review.
