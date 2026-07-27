# Milestone 3 Independent Audit — Instruments, Watchlists and Read-Only Market Data

> **FINAL STATUS: FAIL**
>
> The implemented private-development paths are stable, tenant isolation passed, all native
> quality gates passed after audit corrections, PostgreSQL migrations are reversible, and Docker
> is healthy. The milestone nevertheless cannot receive PASS or CONDITIONAL PASS because several
> explicitly required technical capabilities and tests remain absent without an approved
> exception. In particular, the provider contract is incomplete, provider data-quality controls
> do not cover future timestamps or currency/provider-symbol mismatches, provider health is not
> cached, development seeding does not create the required audit event, and frontend role-based
> mutation visibility is not implemented. The Milestone 3 report's statement that all technical
> acceptance gates were validated is therefore unsupported.
>
> **This audit does not authorise production deployment, public access, live trading, custody,
> investment management, advice, or handling real customer funds. Milestone 4 private development
> is not permitted until the unresolved Milestone 3 findings are remediated and re-audited.**

## 1. Audit title

Atlas AI Milestone 3 Independent Audit — Instruments, Watchlists and Read-Only Market Data.

## 2. Audit date

2026-07-27.

## 3. Repository

`C:\Dev\Atlas`

## 4. Branch

`chore/milestone-3-audit`

## 5. Commit audited

- Merge commit: `8946b421b8fe335d52c37a29d635fb268a7da0c1`
- Milestone 3 implementation commit: `d977111`
- Milestone 2 baseline merge: `1819459`

The pre-audit worktree was clean.

## 6. Auditor role

Independent Security Auditor, Software Architect, Data Integrity Reviewer, and Release-Gate
Reviewer.

## 7. Executive conclusion

Atlas has a credible read-only development foundation. UUID-based identity, listing separation,
fixed precision, simulated labeling, tenant-scoped authorisation, reversible PostgreSQL
migrations, deterministic fixtures, safe unauthenticated denial, and hardened containers were
verified.

The independent review also disproved the milestone report's blanket completion claim. Required
provider-neutral capabilities and several specified integrity/test paths were not implemented.
These are not suitable for silent audit-time expansion. Six bounded repository defects were
corrected; broader missing capabilities remain release-gate blockers.

## 8. Final status

**FAIL**

- Technical implementation: partially complete; validated implemented paths are stable.
- Private-development permission: existing Milestone 1–2 governance remains, but Milestone 3 is
  not independently accepted as complete.
- Production readiness: prohibited.

## 9. Scope

Exchange, instrument, listing and provider-mapping identity; quotes; candles; deterministic
fixtures; providers; Redis; market APIs; watchlists; tenant isolation; authorisation; frontend;
data quality; audit/metrics; migrations; dependencies; CI; Docker; runtime; and governance.

## 10. Out-of-scope items

Trading, orders, broker/exchange connectivity, wallets, custody, deposits, withdrawals, real
money, recommendations, signals, optimisation, suitability, advice, live-provider selection,
deployment, and Terraform application.

## 11. Governance restrictions

The approved exceptions in [`security-risk-exceptions.md`](security-risk-exceptions.md) and
[ADR 0006](adr/0006-milestone-1-security-risk-decision.md) remain unchanged:

- Risk owner: Adebayo Olaegbe.
- Review: 2026-08-27.
- Expiry: 2026-10-27.
- Private development and internal testing only.
- Production, public access, live trading, real-money activity, and customer-fund handling remain
  prohibited.

This audit created no new risk exception and did not broaden either existing decision.

## 12. Milestone-report claim-to-evidence matrix

| Report claim                                         | Code evidence                                    | Test/runtime evidence                                                    | Conclusion                         |
| ---------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------ | ---------------------------------- |
| Instruments and listings have separate UUID identity | SQLAlchemy models and `0004` migration           | Model tests; duplicate `NOVA` integration result                         | Verified                           |
| Duplicate symbols across venues are supported        | Unique venue/symbol constraint                   | `NOVA` on `XDEV` and `XDEM`                                              | Verified                           |
| Financial persistence uses fixed precision           | `Numeric(38,18)` models/migrations               | Metadata tests; PostgreSQL schema                                        | Verified after `0005` hardening    |
| Simulated data is explicit                           | provider schemas, fixtures, UI warning           | quote/candle integration tests                                           | Verified                           |
| Tenant isolation is enforced                         | membership-backed watchlist service              | cross-tenant and viewer denial tests                                     | Verified                           |
| Cache keys are collision-resistant                   | original colon replacement                       | targeted `a:b` versus `a_b` test                                         | False before audit; corrected      |
| Malformed cache degrades safely                      | original JSON-only handling                      | targeted schema-invalid cache test                                       | Incomplete before audit; corrected |
| CI contains repository quality gates                 | original workflow ran tests only                 | workflow inspection                                                      | False before audit; corrected      |
| All technical acceptance gates were validated        | milestone report section 31                      | missing capabilities/tests listed in findings                            | Unsupported                        |
| Provider-neutral architecture is complete            | provider interface has quote/candles/health only | no reference/search/rate-limit contract tests                            | Partially supported                |
| Data-quality controls are complete                   | basic numeric/OHLC/range checks                  | no future timestamp, currency mismatch, or provider-symbol mismatch path | Partially supported                |
| Frontend implements role-based controls              | server authorisation exists                      | controls render without role-aware visibility                            | Not implemented                    |

## 13. Architecture findings

Routes are generally thin; repositories own SQL; services own search, freshness and watchlist
rules; providers expose typed Atlas objects; cache logic is isolated; transaction boundaries are
explicit. No global mutable session, uncontrolled retry loop, hidden provider call, or new
infrastructure service was found.

The provider boundary and ingestion surface remain narrower than the required architecture. See
`M3-AUD-001`.

## 14. Instrument-identity findings

Instrument and listing UUIDs come from Atlas/database mixins. Ticker and name are not primary keys.
Nullable ISIN/CUSIP/SEDOL values are not fabricated. Lifecycle enums preserve inactive,
suspended, and delisted states. No application hard-delete path for instruments was found.

## 15. Listing and venue findings

Listings reference exchanges separately and preserve currency and status. Venue plus symbol is
unique, allowing identical symbols on different venues. Acronym is not unique. MIC is unique.
Provider exchange codes remain separate.

Database checks validate code lengths, but full ISO currency/country and IANA timezone validation
is not implemented for a future write path. There is currently no public exchange mutation API;
this remains part of `M3-AUD-002`.

## 16. Provider-mapping findings

Provider mappings have their own UUID, provider namespace, provider symbol, venue code, status and
verification timestamp. Uniqueness is scoped by provider. Public responses do not expose mapping
records or secrets.

No reconciliation command or provider-symbol mismatch validation service exists.

## 17. Numeric-integrity findings

No SQLAlchemy `Float`, SQL `REAL`/`DOUBLE PRECISION`, `parseFloat`, or financial `Number(...)`
conversion was found in Milestone 3 paths. Prices use `Decimal` and `NUMERIC(38,18)`; volume uses
integer types.

The original schema omitted non-negative checks for quote sizes, OHLC/previous close, delay, and
candle adjusted close. Audit migration `20260727_0005` adds those constraints plus explicit
currency-length checks without rewriting `0004`.

## 18. Quote findings

Stored fixture observations preserve listing, provider, provider timestamp, received timestamp,
market session, price, currency, status and source reference. Runtime responses preserve those
distinctions for the deterministic provider and never infer bid/ask.

The current provider result has no provider currency or source-reference field, so runtime
currency mismatch and provenance validation cannot be performed generically. Live, delayed,
cached, future-timestamp and stale-fallback provider paths are not implemented/tested end to end.

## 19. Historical-candle findings

Database and Pydantic checks reject negative OHLC, invalid period order, high below low, and
open/close outside range. Provider/listing/interval/period uniqueness is deterministic. Fixture
candles are generated directly at supported 1d/1w intervals; there is no interpolation.

Adjusted-close negativity was unconstrained before `0005` and is now corrected. Generic currency
mismatch and duplicate upsert behavior outside deterministic seeding remain unimplemented.

## 20. Simulated-data findings

Fixture UUIDs, timestamps, prices and candles are deterministic. API responses use `simulated`,
`is_stale=false`, a fixed provider timestamp and a non-advisory disclaimer. Frontend instrument,
listing and search screens visibly state “Simulated development data.” No fixture is presented as
a current market price.

The disabled-provider catalogue originally still defaulted listing availability to simulated.
This was corrected to return `unavailable`.

## 21. Provider-abstraction findings

The interface types latest quote, historical candles and health. The deterministic and disabled
implementations do not perform network I/O, so CI uses no external credentials.

Missing required contract capabilities include provider-neutral search, instrument/reference-data
retrieval, venue reference data, and rate-limit status. Timeout/authentication/rate-limit error
behavior is not represented by executable adapters or tests. See `M3-AUD-001`.

## 22. Redis and cache findings

TTLs are bounded and configurable. Quote/candle keys include provider, listing, interval and
range. Watchlists and tokens are not cached. Redis exceptions degrade to source loading.

The original normalization was collision-prone and schema-invalid cached JSON could produce an
application validation error. Keys now hash a canonical length-preserving JSON representation and
typed cache reads discard malformed schemas. Targeted tests pass.

Provider health is not cached and no stampede/single-flight control exists. Health caching was an
explicit milestone requirement and remains open.

## 23. Instrument-search findings

Search normalizes whitespace, enforces 2–100 characters, escapes SQL wildcard metacharacters,
uses SQLAlchemy parameterisation, bounds page size, ranks exact symbols first, returns exchange
and currency, and distinguishes duplicate venue symbols. Page numbers are now bounded to 10,000.

Tests cover exact symbol, duplicate venues, cache hit, and normal operation. Explicit SQL
injection, Unicode, wildcard-only, exact-name, mixed-case, empty, and maximum-page tests are not
all present.

## 24. Watchlist tenant-isolation findings

Watchlists reference a tenant; verified Atlas users and active memberships are resolved
server-side. Foreign-tenant and guessed IDs are concealed. Viewer mutation is denied. Duplicate
listings and positions are constrained. Archival rejects subsequent mutation. Names/notes are
bounded and React renders them as text.

The integration suite executed owner, viewer, outsider, manipulated tenant, duplicate item, and
archived mutation scenarios successfully.

## 25. Authorisation findings

All six watchlist permissions are centralized in `AuthorisationService`; routes contain no role
string comparisons. Active user, active membership, and active tenant checks are inherited from
Milestone 2. Audit tests now evaluate every watchlist permission for every membership role.

Member update permission is tenant-wide, not creator-only. This matches the documented simple
matrix.

## 26. API findings

All expected market and watchlist paths are present under `/api/v1`, authenticated, typed and
documented in OpenAPI. Watchlist routes enforce tenant authorisation. Request IDs are added by
middleware and stable errors are used. No SQLAlchemy model, provider secret, recommendation,
confidence score or expected-return field appears in response schemas.

Bounded pagination was strengthened during the audit. Several specified malformed-input and
provider-state scenarios still lack executable contract tests.

## 27. Frontend findings

Protected screens exist for search, instrument details, listings, watchlists and watchlist detail.
They show exchange, currency, timestamp, provider/data status, simulated warnings, loading/empty
states, accessible labels and responsive layouts. No order-placement or trading control exists.

Watchlist mutation controls are not hidden for viewers; the API remains authoritative and denies
the action, so this is a UX/acceptance gap rather than an authorisation bypass. No specific
delayed/unavailable/provider-error presentation or keyboard-navigation test exists.

## 28. Advisory-language findings

No buy/sell recommendation, target, expected return, confidence, opportunity, undervalued,
overvalued or guarantee language was found in Milestone 3 market paths. “Real-time” appears only
inside factual disclaimers saying the data is not real-time. “Order” in a watchlist error refers
to list ordering, not a financial order.

## 29. Database-migration findings

- Milestone 2 head: `20260727_0003`.
- Implementation migration: `20260727_0004`.
- Audit hardening migration: `20260727_0005`.
- Current head: `20260727_0005`.

Real PostgreSQL validation passed:

1. Existing database current check.
2. Downgrade from `0005` through `0004` to `0003`.
3. Upgrade to `0005`.
4. `alembic check` with no drift.
5. Fresh `atlas_m3_audit` database upgraded through all revisions.
6. Expected tables, constraints and indexes inspected.
7. Temporary database removed.
8. Audit and Compose databases left at `0005`.

## 30. Data-quality findings

Implemented: fixed precision, non-negative financial constraints, OHLC shape, deterministic
uniqueness, interval allowlist, range bounds, timezone-aware request ranges, query normalization,
status/provenance fields, and simulated/unavailable distinction.

Unimplemented or unproven: full ISO/IANA validation, future-provider timestamp tolerance,
provider currency mismatch, provider-symbol mismatch, generic controlled quote/candle upsert,
live/delayed/cached classification, and stale-cache fallback.

## 31. Security-test findings

Executed tests verify unauthenticated denial, disabled Clerk behavior, cross-tenant IDOR denial,
viewer mutation denial, client tenant manipulation denial, duplicate insertion, archived
mutation, malicious markup as inert text data, mass assignment, malformed provider price/candle,
unsupported interval, cache failure, malformed cache and cache collision.

Missing executable cases include provider selection manipulation, timeout, rate limiting,
unexpected external-provider fields, future timestamp, currency mismatch, guessed item removal,
and explicit member escalation.

## 32. Observability findings

Request logs contain request IDs, route templates, status and duration. Metrics exist for market
requests, provider latency/errors, cache hits/misses, stale responses and development ingestion.
Labels are bounded and do not contain raw queries, tokens, profile data or provider responses.

Development seeding increments a metric but does not write the specified durable identity audit
event. Provider mapping changes have no command/audit path.

## 33. Dependency findings

### DEP-001 — brace-expansion advisory

- Severity: High.
- Advisory: GHSA-mh99-v99m-4gvg / CVE-2026-14257.
- Package: `brace-expansion <=5.0.7`.
- Paths observed: ESLint/minimatch development chains in `packages/eslint-config` and `apps/web`.
- Scope: development/CI lint tooling; not application runtime.
- Exploitability: requires untrusted brace patterns reaching lint tooling.
- Fix: `>=5.0.8`; previously incompatible forced upgrades were not retained.
- Decision: existing temporary development-only approval, owner/review/expiry unchanged.

### DEP-002 — Python dependencies

`pip check` reported no broken requirements. `pip-audit` reported no known vulnerabilities.

### DEP-003 — API base-image advisory

The existing CVE-2026-12087 Perl/base-image exception remains in force. Docker Scout could not
produce a fresh result because the local Scout service required Docker authentication. No
credential was introduced during the audit.

No external market-data SDK or chart library was added.

## 34. Quality-gate results

| Gate                        | Result                                        |
| --------------------------- | --------------------------------------------- |
| Frozen pnpm install         | PASS                                          |
| Prettier                    | PASS                                          |
| ESLint                      | PASS                                          |
| TypeScript                  | PASS                                          |
| TypeScript/shared/web tests | PASS — 10 tests                               |
| Next.js production build    | PASS                                          |
| Ruff format                 | PASS after correction                         |
| Ruff lint                   | PASS                                          |
| Strict mypy                 | PASS after correction                         |
| Python tests                | PASS — 53 tests                               |
| pip check                   | PASS                                          |
| pip-audit                   | PASS                                          |
| git diff check              | PASS                                          |
| pnpm dependency audit       | Expected governed failure — one High advisory |

## 35. Coverage results

Final Python coverage: **80.18%**, above the unchanged 80% threshold. An earlier post-correction
run measured 80.92%; the lower final figure reflects the deterministic seed paths already existing
in the reused integration database. The final, lower result is authoritative.

The test run emitted four Starlette deprecation warnings; they did not alter behavior or the gate
result.

## 36. Docker results

`docker compose config --quiet`, both image builds, `up --detach --wait`, and `ps` passed.

- PostgreSQL: healthy.
- Redis: healthy.
- FastAPI: healthy.
- Next.js: healthy.
- API user: `atlas`.
- Web user: `nextjs`.
- API and web root filesystems: read-only.
- API and web: `no-new-privileges:true`.
- Container database: `20260727_0005 (head)`.

## 37. Runtime results

- `/`: HTTP 200.
- `/app/markets`: HTTP 200.
- `/health/live`: HTTP 200.
- `/health/ready`: HTTP 200 with PostgreSQL and Redis healthy.
- `/metrics`: HTTP 200.
- `/openapi.json`: HTTP 200.
- Unauthenticated `/api/v1/market/status`: HTTP 401.
- Unauthenticated search: HTTP 401.

Authenticated market, quote, candle, cache, watchlist, viewer and cross-tenant behavior passed
through the safe ASGI/PostgreSQL integration suite. No real Clerk/provider credential was used.

## 38. Corrective changes made

### COR-001 — collision-safe cache keys

- Defect: colon replacement allowed distinct inputs to share a key.
- Files: `market/cache.py`, `test_market.py`.
- Correction: SHA-256 of canonical JSON-encoded parts.
- Evidence: `a:b` and `a_b`, plus Unicode distinction tests pass.

### COR-002 — typed malformed-cache degradation

- Defect: syntactically valid but schema-invalid cached payloads could raise validation errors.
- Files: `market/cache.py`, `market/services.py`, tests.
- Correction: typed cache model validation returns a miss on invalid schema.
- Evidence: malformed model payload test and full integration suite pass.

### COR-003 — persisted numeric hardening

- Defect: several quote/candle numeric fields lacked non-negative database checks.
- Files: instrument models, model tests, migration `20260727_0005`.
- Correction: reversible checks for quote sizes/OHLC/previous close/delay, adjusted close and
  currency length.
- Evidence: model tests, upgrade/downgrade/re-upgrade, fresh PostgreSQL and drift checks pass.

### COR-004 — bounded page offsets

- Defect: page size was bounded but page number was unbounded.
- File: market routes.
- Correction: page limited to 10,000 for exchanges, search and watchlists.
- Evidence: FastAPI schema/type/tests/build pass.

### COR-005 — disabled-provider availability

- Defect: listing responses defaulted to simulated availability even when the provider was
  disabled.
- Files: market service and tests.
- Correction: disabled provider now exposes unavailable listing data.
- Evidence: unit test and full suite pass.

### COR-006 — CI gate completeness

- Defect: CI ran tests but omitted stated format/lint/type/build/drift/config gates.
- File: `.github/workflows/test.yml`.
- Correction: added web and Python quality gates, Alembic drift, pip integrity and Compose config.
- Evidence: all equivalent native commands pass; hosted GitHub execution remains a manual check.

### COR-007 — complete watchlist permission matrix test

- Defect: only selected role/permission pairs were tested.
- File: `test_market.py`.
- Correction: every watchlist permission is tested for every membership role.
- Evidence: final 53-test suite passes.

## 39. Unresolved findings

### M3-AUD-001 — incomplete provider-neutral contract

- Severity: **High**.
- Affected area: provider architecture and release claims.
- Evidence: `MarketDataProvider` exposes only quote, candles and health; required
  search/instrument/reference/rate-limit capabilities and their errors/tests are absent.
- Risk: a real adapter cannot be introduced while preserving the documented contract and safety
  controls; the report's completion claim is false.
- Recommendation: complete typed provider capabilities, dependency injection, bounded timeout and
  rate-limit behavior with mocked tests.
- Resolution: **Open**.

### M3-AUD-002 — incomplete provider data-quality enforcement

- Severity: **Medium**.
- Affected area: quotes, candles, mappings and reference data.
- Evidence: no generic future timestamp tolerance, provider currency mismatch,
  provider-symbol mismatch, or full ISO/IANA validation path.
- Risk: a future adapter could admit inconsistent provenance or reference data.
- Recommendation: introduce typed provider results containing currency/source identity and a
  quarantine/rejection validation service before any external adapter.
- Resolution: **Open**.

### M3-AUD-003 — missing required operational controls

- Severity: **Medium**.
- Affected area: caching, ingestion and audit.
- Evidence: provider health is not cached; no generic controlled refresh/upsert path; seeding
  creates a metric but no durable audit event; provider mapping changes have no audited command.
- Risk: incomplete operational traceability and repeated provider-health work.
- Recommendation: add bounded health caching and explicit audited development administration
  services.
- Resolution: **Open**.

### M3-AUD-004 — frontend role/state acceptance gaps

- Severity: **Medium**.
- Affected area: protected web application.
- Evidence: viewer mutation controls remain visible; delayed/unavailable/provider-error states and
  keyboard navigation are not specifically tested.
- Risk: confusing UX and incomplete accessibility/state evidence, though server authorisation
  remains effective.
- Recommendation: return effective permissions with the workspace/watchlist contract, render
  controls accordingly, and add accessibility/state tests.
- Resolution: **Open**.

### M3-AUD-005 — specified test matrix incomplete

- Severity: **Medium**.
- Affected area: release evidence.
- Evidence: no executable coverage for provider timeout/rate limit/authentication, future
  timestamps, currency/provider-symbol mismatch, live/delayed/cached classification, stale-cache
  fallback, guessed item removal, or complete frontend workflows.
- Risk: the blanket statement that every technical gate was validated cannot be substantiated.
- Recommendation: add behavior-focused tests without lowering the coverage threshold or using a
  live provider.
- Resolution: **Open**.

### M3-AUD-006 — existing supply-chain exceptions

- Severity: **High, governed**.
- Affected area: development lint tooling and API base image.
- Evidence: `pnpm audit`; existing CVE documentation.
- Risk: denial of service in development tooling and an unused vulnerable base-image component.
- Recommendation: retain compensating controls and review compatible fixes by the approved dates.
- Resolution: **Temporarily accepted for private development only**; not production-approved.

## 40. Known limitations

Only deterministic simulated data is supported. There is no licensed/live provider, corporate
actions engine, production entitlement/quota system, full ingestion scheduler, currency
conversion, tax calculation, recommendation, trading, order, custody, or money movement.

## 41. Manual checks still required

- Hosted GitHub Actions execution of the corrected workflow.
- Authenticated Docker Scout image scan.
- Independent security review before production.
- Browser/assistive-technology accessibility review.
- Provider licensing and contractual review before selecting any external source.

## 42. Production blockers

All unresolved findings, both existing security exceptions, absent real-provider governance,
missing production authentication/secrets, lack of external security review, simulated-only data,
and explicit release-readiness prohibitions block production.

## 43. Decision

Milestone 3 does **not** pass the independent release gate. The current development stack may
remain running for remediation and testing, but the milestone report must not be used as evidence
of complete technical acceptance.

## 44. Next permitted activity

Only Milestone 3 remediation, documentation correction, testing, and re-audit are permitted.
Milestone 4 private development may **not** begin on this audit result.

## 45. Appendix of exact commands

Executed commands included:

```text
git branch --show-current
git status
git log --oneline --graph --decorate -12
git diff --check
git ls-files | findstr /I ".env"
git rev-parse HEAD
python --version
node --version
pnpm --version
docker version --format "{{.Server.Version}}"
python -m alembic -c packages/database/alembic.ini heads
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
python -m ruff format --check apps packages/database
python -m ruff check apps packages/database
python -m mypy apps/api/src packages/database/atlas_database
python -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
python -m pip check
python -m pip_audit -r apps/api/requirements.txt
pnpm audit --prod
pnpm audit
python -m alembic -c packages/database/alembic.ini current
python -m alembic -c packages/database/alembic.ini downgrade 20260727_0003
python -m alembic -c packages/database/alembic.ini upgrade head
python -m alembic -c packages/database/alembic.ini check
createdb atlas_m3_audit
dropdb atlas_m3_audit
docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose ps
docker inspect atlas-ai-api-1
docker inspect atlas-ai-web-1
docker scout cves atlas-ai-api:latest --only-severity critical,high
docker scout cves atlas-ai-web:latest --only-severity critical,high
```

### Failed command record A — first post-correction Python gate

- Exact commands:
  `python -m ruff format --check apps packages/database` and
  `python -m mypy apps/api/src packages/database/atlas_database`.
- Relevant output: one model file required formatting; four `unused-ignore` typing errors.
- Root cause: audit constraint edits changed formatting and installed Redis typing no longer
  required prior compatibility ignores.
- Correction: formatted the model and removed only the now-unused ignore comments; no strictness
  was disabled.
- Rerun: Ruff formatting/lint and strict mypy passed.
- Final resolution: **Resolved**.

### Failed command record B — pnpm audits

- Exact commands: `pnpm audit --prod` and `pnpm audit`.
- Relevant output: one High `brace-expansion` advisory through ESLint/minimatch.
- Root cause: existing development dependency documented by
  GHSA-mh99-v99m-4gvg / CVE-2026-14257.
- Correction attempted: no unsafe forced upgrade; scope and existing decision were reconciled.
- Rerun: not expected to pass until a compatible patched chain is adopted.
- Final resolution: **Open under existing temporary development-only approval**.

### Failed command record C — Docker Scout

- Exact commands: both API and web `docker scout cves ... --only-severity critical,high`.
- Relevant output: Docker Scout requested Docker ID authentication.
- Root cause: unauthenticated local Scout session.
- Correction attempted: none; introducing credentials was outside the audit.
- Rerun: not performed.
- Final resolution: **Manual authenticated scan required**.
