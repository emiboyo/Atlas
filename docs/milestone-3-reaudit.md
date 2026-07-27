# Milestone 3 Focused Independent Re-Audit — Instruments, Watchlists and Read-Only Market Data

## 1. Re-audit title

Atlas AI Milestone 3 Focused Independent Re-Audit.

## 2. Date

2026-07-27.

## 3. Repository

`C:\Dev\Atlas`.

## 4. Branch

`chore/milestone-3-reaudit`.

## 5. Commit audited

The re-audit began at clean commit `bf4a0e31c3e127d957788cfee9e551f50b2389bd`. The final
decision covers that commit plus the six source/test corrections recorded in section 36 and this
report. Those corrections were deliberately left visible in the re-audit worktree.

## 6. Previous audit result

**FAIL**, recorded by `docs/milestone-3-audit.md`.

## 7. Remediation commit or merge

- Remediation implementation: `1d85fe7`
- Remediation merge: `bf4a0e3`

## 8. Auditor role

Independent Re-Auditor, Security Reviewer, Market-Data Architect, and Release-Gate Reviewer.
Code, executable tests, PostgreSQL, runtime responses, container configuration, logs, and
dependency output were treated as authoritative. The remediation report's conclusion was not
accepted without verification.

## 9. Executive conclusion

The remediation substantially implemented the missing provider, quality, operational,
permission, frontend-state, and test controls. Independent review nevertheless found three
bounded defects: invalid provider data could incorrectly trigger stale fallback, quote
`is_stale` used cache TTL rather than the configured freshness threshold, and central reference
validation did not fully validate provider-instrument identity and retrieval timestamps.

Those defects were corrected during re-audit and regression-tested. After correction,
M3-AUD-001 through M3-AUD-005 are Closed. All native gates, fresh PostgreSQL validation, Docker
health, runtime checks, tenant-isolation checks, and the 80% coverage gate pass.

The two pre-existing time-bounded Milestone 1 security exceptions remain. They prohibit
production/public use and therefore prevent an unconditional PASS.

## 10. Final status

**CONDITIONAL PASS — PRIVATE DEVELOPMENT CONTROLS ONLY**

- Milestone 3 technical status: **Conditional Pass**
- Original Milestone 3 findings: **all Closed after recorded re-audit corrections**
- Production readiness: **Prohibited**
- Public customer access: **Prohibited**
- Milestone 4 private-development decision: **Not yet authorised by the current risk decisions**

## 11. Scope

Provider-neutral instruments, exchanges, listings, mappings, quotes, candles, provider
execution, validation, caching, development ingestion/commands, audit events, watchlists,
effective permissions, frontend states/accessibility, tests, PostgreSQL migrations, Docker,
runtime behavior, logs, and dependency governance.

Trading, order execution, brokerage, custody, deposits, withdrawals, real money,
recommendations, AI signals, portfolio optimisation, live providers, deployment, and Terraform
application remained out of scope and were not added.

## 12. Governance restrictions

The existing exceptions in `docs/security-risk-exceptions.md` and ADR 0006 have:

- Owner: Adebayo Olaegbe
- Next review: 2026-08-27
- Expiry: 2026-10-27
- Scope: private local development, tests/CI, internal Compose, and explicitly Milestone 2 work
- Prohibitions: production, public access, live trading, real money, custody/funds, untrusted
  brace patterns through lint tooling, and Perl execution

This re-audit did not create or broaden a risk exception. Because the recorded decisions name
Milestone 2 rather than Milestone 4, this report cannot independently authorise Milestone 4.

## 13. Claim-to-evidence matrix

| Finding    | Remediation claim                                    | Code evidence                                             | Test/PostgreSQL evidence                                                                     | Runtime evidence                                      | Discrepancy and disposition                                   | Resolution |
| ---------- | ---------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------- | ---------- |
| M3-AUD-001 | Complete provider contract and bounded execution     | `providers.py`, `execution.py`, `services.py`             | Capability, immutable-model, unexpected-field, safe-error, timeout/retry tests pass          | Direct deterministic runtime contract and rebuilt API | No contract gap found                                         | Closed     |
| M3-AUD-002 | Central quality validation and safe ingestion        | `quality.py`, `ingestion.py`, provider models             | Timestamp/currency/symbol/venue/provenance/reference/candle/conflict tests; fresh PostgreSQL | Simulated quote/candle ASGI paths                     | Instrument validation and freshness inconsistency corrected   | Closed     |
| M3-AUD-003 | Health cache, stale fallback, commands, audit events | `cache.py`, `administration.py`, `cli.py`, `ingestion.py` | Expiry/outage/collision/stale-shadow/audit/rollback tests pass                               | Redis and API healthy; CLI exercised with PostgreSQL  | Invalid-data stale fallback corrected                         | Closed     |
| M3-AUD-004 | Server permissions and frontend states               | permission route/service and web components               | Four-role matrix, owner/admin/viewer UI, state and navigation tests pass                     | ASGI owner/viewer/cross-tenant flows                  | Responsive/admin evidence strengthened                        | Closed     |
| M3-AUD-005 | Complete executable matrix                           | market remediation/integration/web tests                  | 75 Python tests, 84.22%; 21 JS package tests                                                 | Host public checks plus synthetic-auth ASGI runtime   | Search/provider manipulation and reference cases strengthened | Closed     |

## 14. M3-AUD-001 verification

**Original severity:** High.

The abstract interface exposes search, detail, exchange reference data, quote, candles, health,
and rate-limit status. Both simulated and disabled adapters implement the same interface. Models
are frozen and forbid extra fields. Routes never accept raw provider payloads or a provider
selector. A supplied `provider=attacker-controlled` query did not change the server-selected
`atlas_simulated` provider.

Provider execution uses configurable timeout, bounded retry count, deterministic backoff,
latency/error metrics, and no retry for authentication, rate-limit, invalid-data, or unsupported
errors. `CancelledError` is not swallowed. No live SDK or provider credential exists.

**Independent result:** capability/error/executor tests pass; direct runtime returned one search
result, `NOVA.XDEV` detail, one venue, healthy status, and `not_applicable` rate limit.

**Resolution:** Closed.

## 15. M3-AUD-002 verification

**Original severity:** Medium.

Central validation now covers provider/received timestamp awareness and future tolerance,
freshness, currency, listing ID, provider symbol, provider venue, source provenance, MIC,
country, IANA timezone, provider-instrument identity/retrieval time, enum-backed asset/listing
status, candle time/shape, and received time. Invalid data is rejected before persistence.

No currency conversion, listing remap, provider-time substitution, binary float persistence, or
unverified fallback occurs. Stale and simulated classifications remain explicit.

**Independent result:** data-quality, malformed-model, ingestion conflict/rollback, and database
constraint tests pass.

**Resolution:** Closed after audit corrections.

## 16. M3-AUD-003 verification

**Original severity:** Medium.

Health caching uses provider-scoped SHA-256 keys, typed reads, configurable short TTL, safe
malformed-payload misses, Redis-outage direct checks, and bounded hit/miss metrics. Quote stale
fallback uses a distinct shadow key and bounded TTL.

The corrected fallback is reachable only for unavailable, timeout, or rate-limit errors. Invalid
provider results propagate as errors and cannot be hidden behind old data. A returned shadow is
always `stale` with `is_stale=true` and expires independently.

All required development-only commands exist, reject production, use server-configured provider
selection, and are absent from HTTP routes. Operation UUIDs provide audit idempotency. Failed
transactions create no success event.

**Independent result:** cache time-injection, malformed Redis, outage, separation, stale expiry,
CLI, idempotency, mapping-audit, conflict, and partial rollback tests pass.

**Resolution:** Closed after audit correction.

## 17. M3-AUD-004 verification

**Original severity:** Medium.

Effective permissions are derived from active server-side tenant membership. The API accepts
only a tenant ID and never a client role or permission set. The central role matrix verifies
owner, admin, member, and viewer permissions. Integration tests verify owner/viewer endpoint
behavior and outsider denial.

Viewer create/update/delete/add/remove/reorder controls are hidden while server enforcement
remains authoritative. Owner/admin rendering uses the effective permission response. Explicit
simulated, delayed, cached, stale, unavailable, provider-error, rate-limited, and
unsupported-interval states render without trading or advisory semantics.

Programmatic labels, focus order, native form/button semantics, owner/admin/viewer states, and
labelled desktop/mobile navigation contracts are executable. Native buttons/links preserve
browser keyboard activation.

**Resolution:** Closed.

## 18. M3-AUD-005 verification

**Original severity:** Medium.

The executed matrix covers provider timeouts/connections/auth/rate-limit/retry-after/unsupported
capability/unexpected fields/malformed data/provider selection; timestamp/currency/symbol/venue/
provenance and data classifications; search injection/wildcards/Unicode/case/exact values/bounds;
watchlist IDOR/roles/mutation/mass-assignment/archive/duplicates/malicious text; and ingestion
idempotency/conflict/partial rollback/provenance/audit behavior.

The audit added explicit cases where evidence was previously indirect: provider-selector
manipulation, exact-name/max-page/page-size/search-length bounds, reference instrument/venue
validation, classification retention, invalid-data stale fallback, admin UI, and responsive
navigation.

**Resolution:** Closed after evidence corrections.

## 19. Provider contract findings

Provider-specific payloads remain adapter-local. The deterministic fixture is explicitly
simulated and bounded to 500 candles. Disabled behavior is safe and typed. Unsupported interval
and symbol-not-found codes are stable. Unknown rate-limit values remain null.

## 20. Provider execution findings

Timeout is configurable from 1–30 seconds; retry count is 0–3. Only timeout and
connection/OS errors retry. Tests prove two attempts with retry count one and deterministic
50 ms backoff. Authentication, rate-limit, malformed response, and unsupported capability have
one attempt. Metrics use bounded provider/operation/code labels and logs contain no payload.

## 21. Data-quality findings

Provider timestamps remain distinct from receipt timestamps and are normalised to UTC only after
validation. Ordinary currencies require three alphabetic characters. Symbols/venues are compared
to server-owned mappings. Pydantic rejects negative quote/candle values and invalid enum values;
quality checks provenance and reference identity.

## 22. Ingestion findings

Reference sync, listing reconciliation, quotes, candles, and mapping upserts are bounded
callable services. Quote/candle/mapping mutations own rollback on exceptions. Identical
observations are deterministic duplicates; conflicts do not overwrite valid data. The partial
candle test proves an earlier batch insert is rolled back when a later candle conflicts.

## 23. Cache findings

Cache keys hash canonical JSON parts, preventing delimiter/Unicode collisions. Typed malformed
payloads become misses. No wildcard invalidation or secret caching exists. Health and stale
shadow TTLs are bounded. Cache failure does not bypass source validation.

## 24. Operational command findings

Commands present: `seed-development-data`, `sync-reference-data`, `reconcile-listings`,
`refresh-quote`, `refresh-candles`, and `upsert-provider-mapping`. No public admin route or
background infinite loop exists. Candle ranges, search limits, retries, and operation metadata
are bounded.

## 25. Audit-event findings

Required event types are represented for seed, reference sync, quote refresh, candle refresh,
mapping creation, and mapping update. Event ID equals operation ID; duplicate seed operations
reuse the recorded counts. Metadata contains provider, command, timestamps, counts, and bounded
listing IDs—not credentials or provider payloads. Rollback tests prove no success event after
failure.

## 26. Permission findings

Tenant membership, tenant status, user status, and role are server-side. Foreign tenant and
guessed object access are concealed. Viewer mutation is denied; member lacks delete but retains
documented create/update/item permissions. No client mass assignment of ownership/role succeeds.

## 27. Frontend state findings

All eight required states render stable non-alarming text. Simulated content says “Simulated
development data.” Delay seconds render when known. Instrument views show timestamps and stale
labels; unavailable state does not fabricate a current value. No buy/sell color semantics,
prediction, order, recommendation, or investment-advice control was found.

## 28. Accessibility findings

Search, workspace, watchlist name, and navigation regions have programmatic names. Tests prove
document focus order and focusability. Mutation actions use native labelled buttons/forms.
Desktop and mobile application navigation have distinct labels and responsive classes.

## 29. Security-test findings

Executed evidence covers unauthenticated denial, disabled Clerk, tenant IDOR, guessed item,
viewer denial, member role limits, tenant/provider manipulation, mass assignment, SQL injection,
oversized input/ranges, cache collision/malformed cache, stale/simulated classification,
provider mismatch/future/malformed/extra fields, and safe error schemas.

Representative API logs contain request IDs, route, status, and duration only. Automated scans
of recent logs found no bearer token, API key, session token, private key, or credential pattern.
Repository signature scanning found no real key patterns. Error responses did not include raw
provider payloads or credential URLs.

## 30. PostgreSQL findings

A fresh disposable PostgreSQL 16.9 database upgraded through every revision to
`20260727_0005`. `alembic current` and `heads` both reported `0005 (head)`;
`alembic check` found no pending operations.

All nine relevant tables were present. Quote/candle price columns are `NUMERIC(38,18)`.
Observation uniqueness, non-negative/OHLC/currency checks, and provider/quote/candle/watchlist
indexes were inspected in PostgreSQL. Audit-event persistence was exercised by integration tests.
No migration `0006` is required because the corrections are validation/service behavior and use
existing persisted provenance/audit fields. The disposable container was removed; Compose remains
at `0005`.

## 31. Quality-gate results

| Gate                             | Result                          |
| -------------------------------- | ------------------------------- |
| `pnpm install --frozen-lockfile` | PASS                            |
| `pnpm format:check`              | PASS                            |
| `pnpm lint`                      | PASS                            |
| `pnpm typecheck`                 | PASS                            |
| `pnpm test`                      | PASS                            |
| `pnpm build`                     | PASS                            |
| Ruff format/check                | PASS                            |
| strict mypy                      | PASS — 49 source files          |
| pytest coverage                  | PASS                            |
| `pip check`                      | PASS                            |
| `pip-audit`                      | PASS — no known vulnerabilities |
| `git diff --check`               | PASS                            |
| `pnpm audit --prod`              | Expected governed finding       |
| `pnpm audit`                     | Expected governed finding       |

## 32. Coverage result

**75 Python tests passed; 84.22% coverage.** The 80% gate was not changed. Six Starlette
deprecation warnings are non-blocking and should be removed during maintenance.

JavaScript workspace tests also passed: web 18, UI 2, shared 1.

## 33. Docker result

`docker compose config --quiet`, full API/web builds, and
`docker compose up --detach --wait` passed. PostgreSQL, Redis, API, and web are healthy.

- API user: `atlas`, UID 1001
- Web user: `nextjs`
- API/web root filesystems: read-only
- Security option: `no-new-privileges:true`
- Host bind mounts: none
- API command: direct Uvicorn; no Perl invocation
- ESLint in web runtime: absent
- Compose migration: `20260727_0005`

Binding API/web to `0.0.0.0` inside containers is intentional for local Docker port publication;
it is not production ingress approval.

## 34. Runtime result

Host checks:

- Homepage: 200
- Liveness: 200
- Readiness: 200
- Metrics: 200
- OpenAPI: 200
- Unauthenticated search: 401
- Unauthenticated market status: 401

Direct deterministic runtime verified search, detail, venue reference, health, and rate-limit
capabilities. Synthetic-auth ASGI/PostgreSQL integration verified instrument/listing/quote/candle
flows, health cache, provider failures, stale fallback, mismatch rejection, permissions,
viewer/owner mutation, cross-tenant denial, audited seed, and mapping audit. No live Clerk or
market provider was contacted.

## 35. Dependency findings

Python requirements are consistent and have no known vulnerability from `pip-audit`.

Both pnpm audit commands return one High `brace-expansion <=5.0.7` finding through the
ESLint/minimatch development chain: GHSA-mh99-v99m-4gvg / CVE-2026-14257. ESLint is absent from
the web runtime, untrusted brace patterns are prohibited, and the time-bounded development-only
decision remains in `docs/security-risk-exceptions.md`.

Docker Scout required Docker ID authentication and was not bypassed. CVE-2026-12087 therefore
remains governed by the existing private-development-only exception. Perl is present in the base
image but Atlas starts Uvicorn directly and does not invoke it. No new High/Critical finding or
new exception was introduced.

## 36. Corrections made during re-audit

1. **Invalid provider data could trigger stale fallback**
   - Files: `services.py`, `test_market_remediation.py`
   - Fix: allow stale shadow only for unavailable, timeout, or rate-limit errors.
   - Evidence: invalid provider response now propagates; unavailable fallback and expiry still
     pass.
2. **Freshness response used cache TTL**
   - Files: `services.py`, `test_market_remediation.py`
   - Fix: use `market_quote_stale_after_seconds`; make `is_stale` consistent with validated stale
     status.
   - Evidence: deliberately divergent cache/freshness settings return stale/true.
3. **Provider-instrument reference validation was incomplete**
   - Files: `quality.py`, `ingestion.py`, `test_market_remediation.py`
   - Fix: central identity, currency, country, retrieval timestamp, and provenance validation;
     reconciliation now uses it.
   - Evidence: valid reference accepted; malformed identity/country/currency/time rejected.
4. **Several remediation claims had only indirect test evidence**
   - Files: `test_market_integration.py`, `test_market_remediation.py`,
     `apps/web/src/test/market.test.tsx`
   - Fix: explicit classification, search-bound, provider-manipulation, admin UI, reference-data,
     and responsive navigation tests.
   - Evidence: final Python/web suites pass.

No migration, dependency, public endpoint, provider integration, or product feature was added.

## 37. Remaining limitations

- Only deterministic simulated and disabled providers exist.
- No market-data licensing, entitlement, commercial quota, production SLA, or redistribution
  approval exists.
- No live Clerk/provider runtime was tested or claimed.
- Docker Scout needs an already-authenticated independent rerun.
- Six framework deprecation warnings remain.
- No browser E2E suite proves native keyboard behavior across real browsers.
- The existing governance documents do not explicitly include Milestone 4 in approved scope.

## 38. Production blockers

Production/public use remains blocked by the two security exceptions, required independent
production security review, production identity/perimeter controls, market-data licensing and
entitlements, operational readiness/backup/rollback evidence, authenticated image scanning, and
an explicit production risk decision.

This result does not authorise live trading, real-money investing, custody, investment
management, advice, or handling customer funds.

## 39. Final decision

**CONDITIONAL PASS.**

M3-AUD-001 through M3-AUD-005 are Closed after the recorded audit corrections. No unresolved new
Critical or High technical finding remains. The only accepted High/Critical findings are the two
existing owned, controlled, reviewed, and expiring private-development exceptions.

## 40. Milestone 4 private-development decision

**Not authorised by this re-audit.**

The Milestone 3 technical gate is closed, but the current exception register and ADR explicitly
approve “Milestone 2 development work,” not Milestone 4. The risk owner must record a deliberate
scope decision—without weakening production prohibitions—before Milestone 4 private development
begins. This is a governance-scope blocker, not an open Milestone 3 technical finding.

## 41. Appendix of exact commands

```powershell
git branch --show-current
git status
git log --oneline --graph --decorate -12
git diff --check
git rev-parse HEAD
git ls-files | findstr /I ".env"

.\.venv312\Scripts\python.exe --version
node --version
pnpm --version
docker version
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini heads

pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build

.\.venv312\Scripts\python.exe -m ruff format --check apps packages/database
.\.venv312\Scripts\python.exe -m ruff check apps packages/database
.\.venv312\Scripts\python.exe -m mypy apps/api/src packages/database/atlas_database
.\.venv312\Scripts\python.exe -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
.\.venv312\Scripts\python.exe -m pip check
.\.venv312\Scripts\python.exe -m pip_audit -r apps/api/requirements.txt

pnpm audit --prod
pnpm audit

docker run --detach --name atlas-m3-reaudit-postgres --publish 127.0.0.1:55441:5432 --env POSTGRES_DB=atlas_reaudit --env POSTGRES_USER=atlas_reaudit --env POSTGRES_PASSWORD=atlas-reaudit-only postgres:16.9-alpine
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini upgrade head
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini current
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini heads
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini check
docker exec atlas-m3-reaudit-postgres psql -U atlas_reaudit -d atlas_reaudit
docker rm --force atlas-m3-reaudit-postgres

docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose ps
docker compose exec -T postgres psql -U atlas -d atlas -tAc "select version_num from alembic_version;"
docker compose logs --no-color --tail 80 api web
docker scout cves atlas-ai-api:latest --only-severity critical,high
```

### Failed commands and final state

| Command                                  | Error                                                | Root cause                                                                        | Correction and rerun                                           | Final state                                                     |
| ---------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------- |
| Initial disposable `pg_isready` loop     | First final probe reported “rejecting connections”   | PostgreSQL was still starting and the first PowerShell loop did not wait reliably | Re-ran a bounded readiness loop; database accepted connections | Resolved                                                        |
| Parallel focused Python/web validation   | Wrapper timed out without returning child output     | Concurrent Windows/Turbo execution exceeded wrapper timeout                       | Re-ran backend and web tests separately                        | Resolved: 20 focused backend and 18 web tests passed            |
| One-line provider runtime Python command | `SyntaxError` at inline `async def`                  | Compound async function definition is invalid after a semicolon                   | Used separate `asyncio.run` expressions                        | Resolved: all five direct capabilities returned expected values |
| Initial constraint count query           | Count was 2 rather than the anticipated combined set | Alembic naming convention prefixes/truncates check names                          | Inspected every actual constraint name and type directly       | Resolved: expected unique/check constraints present             |
| `pnpm audit --prod`; `pnpm audit`        | Exit 1, one High `brace-expansion` advisory          | Governed ESLint/minimatch development chain                                       | Verified runtime exclusion and retained existing controls      | Accepted only under existing exception                          |
| Docker Scout                             | Docker ID login required                             | Scout is not authenticated                                                        | No credential was requested or stored                          | Not freshly scanned; existing exception remains                 |
