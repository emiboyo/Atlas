# Atlas AI Milestone 4 Implementation Report

> **CURRENT STATUS — CONDITIONAL PASS**
>
> Milestone 4's simulated-portfolio technical gates pass. Private development and
> an independent Milestone 4 audit may proceed under the existing governance
> decision. Production deployment, public access, live trading, real-money
> investing, custody, and movement of customer funds remain prohibited.
>
> Risk owner: **Adebayo Olaegbe**  
> Review date: **2026-08-27**  
> Exception expiry: **2026-10-27**

Validation date: 2026-07-28  
Repository: `C:\Dev\Atlas`  
Branch: `feat/milestone-4-simulated-portfolios`  
Milestone 3 head: `20260727_0005`  
Milestone 4 head: `20260728_0006`

## 1. Executive summary

Atlas now has a tenant-scoped, simulated-only portfolio accounting foundation
with immutable transaction history, balanced ledger postings, deterministic
weighted-average cost, explicit reversals, fixed-precision holdings, valuation
provenance, and descriptive analytics. The API, protected web experience,
database migration, tests, documentation, CI controls, and operational checks
were implemented without adding broker, execution, payment, custody, or
real-money functionality.

The implementation passed the JavaScript/TypeScript, Python, PostgreSQL,
Docker, runtime, repository, and governed dependency gates. The final status is
conditional because the two previously approved development-only security
exceptions remain. This report does not authorize production use.

## 2. Governance authority

- Risk owner: Adebayo Olaegbe, Founder and Project Owner
- Security reviewer: independent security review required before production
- Approved scope: local/private development, automated testing, CI, and
  Milestone 4 development
- Prohibited scope: production, public customers, live trading, real money,
  custody, and customer-fund movement
- Decision reference:
  [`docs/adr/0006-milestone-1-security-risk-decision.md`](adr/0006-milestone-1-security-risk-decision.md)
- Risk register:
  [`docs/security-risk-exceptions.md`](security-risk-exceptions.md)

## 3. Architecture implemented

The feature is a vertical FastAPI portfolio domain backed by PostgreSQL and the
existing identity, tenancy, market-data, and ledger foundations. Route handlers
validate transport contracts and delegate to services. Services own
authorization and atomic accounting rules. Repositories isolate SQL access.
PostgreSQL constraints, row locks, and append-only triggers provide the final
integrity boundary. The Next.js routes provide a permission-aware,
simulation-labelled user experience.

Material design decisions are recorded in:

- [ADR 0010](adr/0010-simulated-portfolio-accounting-architecture.md)
- [ADR 0011](adr/0011-weighted-average-simulated-cost.md)
- [ADR 0012](adr/0012-append-only-reversal-and-concurrency.md)
- [ADR 0013](adr/0013-multi-currency-valuation-policy.md)

## 4. Existing architecture preserved

Milestone 4 reuses the existing Clerk-derived authentication context, central
tenant membership model, server-side permission system, provider-neutral
instrument/listing model, market-data service, signed balanced ledger, error
envelope, structured logging, metrics endpoint, and Alembic chain. It does not
create competing authentication, tenant, market, or ledger systems.

## 5. Portfolio model

Portfolios use server-generated UUID Atlas IDs and are always scoped by
`tenant_id`. They include immutable ownership scope, base currency, lifecycle
status, optional descriptive benchmark listing, and creation provenance.
Archiving is a lifecycle transition, not deletion. A database-level composite
tenant foreign-key pattern prevents cross-tenant references.

## 6. Portfolio account model

Each portfolio currency has seven explicit internal account roles:

- simulated cash
- position cost
- realised gain
- realised loss
- dividend income
- fee expense
- capital contribution

Portfolio accounts map one-to-one to existing ledger accounts. The
portfolio/currency/role combination is unique. Currency codes are validated
against a bounded ISO-style allow-list and persisted explicitly.

## 7. Transaction model

Supported simulated transaction types are virtual deposit, simulated buy,
simulated sell, simulated dividend, simulated split, and reversal. Transactions
record an immutable sequence, effective time, currency, optional listing,
quantity, unit price, fee, derived gross/net amounts, position deltas, realised
P&L delta, idempotency key, request fingerprint, actor, and linked ledger
transaction where monetary.

The database enforces `is_simulated = true`. No transaction can route an order
or move real money.

## 8. Ledger integration

Monetary portfolio transactions create entries in the existing signed ledger
inside the same database transaction. Entry amounts sum to exactly zero for
each currency. A posting failure rolls back the portfolio transaction, ledger
transaction, entries, position, and audit event together.

A split is non-monetary. It changes simulated quantity and average unit cost
without fabricating cash or a monetary ledger balance.

## 9. Debit and credit rules

Atlas preserves the existing signed-entry convention rather than introducing
parallel debit and credit columns. Asset increases and decreases are offset by
the appropriate contribution, position-cost, income, expense, or realised
gain/loss accounts. Every monetary journal is currency-homogeneous and must
sum to zero. Buy fees are expensed separately; sell realised P&L is calculated
net of fees while the journal remains balanced.

## 10. Position model

There is at most one position per portfolio and listing. Quantity, cost basis,
average cost per unit, and cumulative realised P&L use PostgreSQL
`NUMERIC(38,18)`. Quantity and cost cannot be negative. Positions are
projections of immutable posted history and are updated atomically under the
portfolio lock.

## 11. Cost-basis method

Atlas uses deterministic weighted-average cost:

- buys add acquisition value to cost basis
- partial sells release proportional average cost
- splits preserve total cost basis and recalculate per-unit cost
- realised P&L is sell proceeds less released cost and fees
- quantities and amounts use `Decimal`; financial persistence does not use
  binary floating point

## 12. Idempotency design

Posting and snapshot commands require a bounded idempotency key. The key is
unique in its tenant/portfolio operation scope and is stored with a canonical
request fingerprint. Exact retries return the original result. Reuse with a
different payload returns a conflict. Database uniqueness is the final
duplicate-effect guard.

## 13. Concurrency design

Posting locks the portfolio row before reading cash, positions, or transaction
state. This serializes competing mutations for a portfolio. Unique constraints
resolve same-key races. PostgreSQL integration tests prove that concurrent
duplicate requests create one effect and concurrent buys/sells cannot
overspend or oversell.

## 14. Reversal design

Posted transactions are not edited or deleted. Reversal creates a compensating
transaction, opposing ledger entries where monetary, opposing position
effects, and a new audit event. A unique `reversal_of_transaction_id` permits
only one reversal of an original. Reversals cannot themselves be reversed.
Database triggers restrict posted-record mutation to the narrowly defined
status transition performed by the reversal workflow.

## 15. Currency policy

Transaction currency must match its listing currency. No implicit FX conversion
occurs. Each currency receives its own internal accounts and balanced ledger.
Base-currency totals are `null` when non-base cash or holdings cannot be
converted. Multi-currency incompleteness is returned explicitly.

## 16. Valuation model

Valuation is read-only and uses persisted Milestone 3 quotes. Each line records
listing, quantity, cost basis, price, provider, observed timestamp, market
value, unrealised P&L, and quality status. Optional snapshots persist the
calculation with an as-of time and idempotency protection.

## 17. Market-data provenance

Valuations consume the existing provider-neutral market service and persisted
listing identifiers. Provider and observation time are retained per valuation
line. Milestone 4 does not contact a live market-data provider during tests or
runtime validation.

## 18. Stale and missing data handling

Fresh, stale, missing, unavailable, and unconverted states are distinct.
Stale quotes retain their original timestamp and remain visibly stale. Missing
quotes do not become zero. Incomplete or unconverted portfolios do not receive
a fabricated base-currency total.

## 19. Analytics implemented

The read-only analytics surface provides allocation, persisted valuation
history, simple historical return statistics, annualized descriptive
volatility, maximum drawdown, and date-aligned benchmark comparison. Benchmark
gaps and insufficient history are explicit. Analytics describe recorded
simulation history and do not predict returns.

## 20. Non-advisory boundary

The UI and API use “Simulated portfolio — no real money or orders” and
non-advisory language. There are no recommendations, signals, expected-return
claims, order controls, broker connections, or execution paths. Analytics are
descriptive only and are not investment advice.

## 21. Authorisation matrix

| Capability                                     | Owner/Admin |                        Member |                  Viewer | Outsider |
| ---------------------------------------------- | ----------: | ----------------------------: | ----------------------: | -------: |
| View portfolio, holdings, valuation, analytics |       Allow |                         Allow |                   Allow |     Deny |
| Create/update portfolio                        |       Allow | Allow where centrally granted |                    Deny |     Deny |
| Post/reverse simulated transaction             |       Allow | Allow where centrally granted |                    Deny |     Deny |
| Archive portfolio                              |       Allow |                          Deny |                    Deny |     Deny |
| View audit history                             |       Allow | Allow where centrally granted | Read-only where granted |     Deny |

All decisions are made server-side through the central permission model. UI
visibility is only an additional usability control.

## 22. Tenant-isolation evidence

Composite tenant foreign keys bind portfolios and all child records to the same
tenant. Every repository query is tenant-qualified. Integration tests cover
same-tenant viewer denial for mutation and cross-tenant concealment/denial.
No client-supplied tenant ID is trusted as authorization.

## 23. API endpoints

All routes are below `/api/v1/portfolios`:

- list, create, read, update, and archive portfolios
- effective permissions
- list, read, post, and reverse transactions
- list holdings
- calculate valuation
- create and list valuation snapshots
- combined analytics, allocation, history, statistics, and benchmark
- audit history

The generated OpenAPI document exposes the concrete request/response schemas.

## 24. Frontend routes and screens

- `/app/portfolios`
- `/app/portfolios/new`
- `/app/portfolios/[portfolioId]`
- `/app/portfolios/[portfolioId]/transactions`
- `/app/portfolios/[portfolioId]/transactions/new`
- `/app/portfolios/[portfolioId]/holdings`
- `/app/portfolios/[portfolioId]/analytics`
- `/app/portfolios/[portfolioId]/audit`

The screens include permission-aware actions, explicit simulation notices,
loading/empty/error states, responsive tables, valuation-quality labels,
archival state, and reversal controls.

## 25. Accessibility

Forms use labels, descriptions, fieldsets, native controls, and actionable
errors. Tables include captions and semantic headers. Status is conveyed by
text as well as color. Allocation has a textual/table alternative; keyboard
operation does not depend on a chart.

## 26. Audit events

Portfolio creation, update, archive, transaction posting, reversal, and
valuation snapshot operations create actor-, tenant-, portfolio-, request-,
and timestamp-aware events. Portfolio audit events are append-only at the
database layer.

## 27. Observability

Portfolio requests, postings, reversals, idempotent replays, conflicts, and
failures feed bounded in-process counters exposed through the existing metrics
endpoint. Existing structured logging and request IDs remain in force. Logs do
not include credentials or unbounded financial payloads.

## 28. Security controls

- Clerk-derived authentication context and active-user enforcement
- central server-side permissions
- tenant-qualified queries and composite tenant foreign keys
- strict Pydantic schemas with forbidden extra fields
- fixed-precision financial values
- idempotency fingerprints and uniqueness
- PostgreSQL row locking
- append-only triggers and compensating reversals
- non-root containers, read-only root filesystems, `no-new-privileges`
- no API/web host bind mounts
- no committed production credentials detected

Web and API bind to `0.0.0.0` inside their containers intentionally so Docker
can publish them to the local host. This is a local Compose requirement, not
approval for internet exposure or production deployment.

## 29. Tests added

Backend tests cover schemas, OpenAPI, permissions, mass-assignment rejection,
Decimal behavior, full accounting sequences, balance, reversals, atomic
rollback, insufficient cash/quantity, idempotency, conflicts, concurrency,
archiving, tenant isolation, multi-currency incompleteness, snapshots,
statistics, and aligned benchmarks. Frontend tests cover notices,
permission-aware actions, transaction language, valuation states, and
non-advisory presentation.

## 30. Python tests and coverage

Authoritative result:

```text
86 passed, 6 warnings in 5.70s
Total coverage: 84.85%
Required coverage: 80%
```

Ruff format, Ruff lint, and strict mypy passed. `pip check` reported no broken
requirements. `pip-audit` reported no known Python dependency vulnerabilities.
The remaining warnings are pre-existing Starlette status-name deprecations in
identity and market tests/code; the new portfolio occurrence was corrected.

## 31. Frontend tests

All 26 workspace tests passed: 23 web, 2 UI, and 1 shared. Formatting, ESLint,
TypeScript, and the Next.js production build passed. The build includes all
eight protected portfolio route patterns.

## 32. PostgreSQL migration revision

`20260728_0006_simulated_portfolio_accounting.py` advances Milestone 3 head
`20260727_0005` to Milestone 4 head `20260728_0006`. It adds portfolio lifecycle
fields plus accounts, transactions, positions, valuation snapshots, valuation
lines, and audit events with constraints, indexes, foreign keys, and
append-only protections.

## 33. Migration validation

- upgrade from Milestone 3 head: pass
- downgrade to Milestone 3 head: pass
- re-upgrade to Milestone 4 head: pass
- `alembic check`: no new operations detected
- fresh disposable database through every revision: pass
- expected portfolio tables: 7
- inspected portfolio constraints: 67
- inspected portfolio indexes: 28
- inspected financial numeric columns: 18, all `NUMERIC(38,18)`
- idempotency, reversal uniqueness, position uniqueness, tenant foreign keys,
  and ledger links present
- disposable database removed
- development databases left at `20260728_0006`

## 34. Docker validation

`docker compose config --quiet`, image builds, `up --detach --wait`, and
`docker compose ps` passed. PostgreSQL, Redis, API, and web were healthy.
The API runs as UID/GID 1001 (`atlas`) and web as `nextjs`; both have read-only
root filesystems, `no-new-privileges`, and no host bind mounts. ESLint is absent
from the API runtime image.

## 35. Runtime validation

| Check                                                                  | Result                                                       |
| ---------------------------------------------------------------------- | ------------------------------------------------------------ |
| Homepage                                                               | 200                                                          |
| Liveness                                                               | 200                                                          |
| Readiness                                                              | 200                                                          |
| Metrics                                                                | 200                                                          |
| OpenAPI                                                                | 200                                                          |
| Unauthenticated portfolio request                                      | 401                                                          |
| Authenticated create/deposit/buy/valuation/holdings/analytics/reversal | Passed by synthetic ASGI + real PostgreSQL integration tests |
| Retry/conflict/viewer/cross-tenant/archive denial                      | Passed by integration tests                                  |
| Stale/missing/multi-currency/audit behavior                            | Passed by integration tests                                  |

No production credentials were used. Clerk is intentionally disabled in the
local Compose runtime, so authenticated workflows were validated with
synthetic safe authentication against real PostgreSQL rather than real Clerk.

## 36. Dependency findings

`audit:governed` and `audit:governed:prod` pass only while the exact approved
`brace-expansion` development-toolchain advisory
GHSA-mh99-v99m-4gvg / CVE-2026-14257 remains on its known ESLint/minimatch
paths and before 2026-10-27. New, changed, or expired advisories fail the gate.

Docker Scout is installed, but the final image re-scan could not run because
Docker Desktop requires Docker Hub authentication. The previously documented
CVE-2026-12087 in Perl inherited from `python:3.12.13-slim` therefore remains
governed rather than independently cleared. Atlas does not invoke Perl.
See [security risk exceptions](security-risk-exceptions.md).

## 37. Files created

- `apps/api/src/portfolio/{__init__,metrics,repositories,routes,schemas,services}.py`
- `apps/api/tests/test_portfolio.py`
- `apps/api/tests/test_portfolio_integration.py`
- portfolio Next.js pages below `apps/web/src/app/app/portfolios/`
- `apps/web/src/components/portfolio-{browser,notice,transaction-form,workspace}.tsx`
- `apps/web/src/test/portfolio.test.tsx`
- `packages/database/alembic/versions/20260728_0006_simulated_portfolio_accounting.py`
- ADRs 0010–0013
- `docs/portfolio-{analytics,architecture,threat-model,transaction-model,valuation}.md`
- `docs/simulated-portfolio-accounting.md`
- `scripts/verify-governed-node-audit.mjs`
- this report

## 38. Files modified

- API v1 router and central authorization
- database enums, ledger mappings, portfolio models, and model exports
- web account navigation
- CI workflow and package scripts
- README and authorization, financial-domain, data-classification, security,
  testing, local-development, and release-readiness documentation

The final `git status --short` intentionally shows these uncommitted Milestone 4
changes. No unrelated user changes were discarded.

## 39. Corrective changes made during implementation

Every failed command or check is recorded below.

1. **Initial combined JavaScript baseline**
   - Command: `pnpm install --frozen-lockfile; pnpm format:check; pnpm lint; pnpm typecheck; pnpm test; pnpm build`
   - Error: execution tool timed out after one second after install completed.
   - Root cause: validation runner timeout, not a project failure.
   - Correction: reran with an appropriate timeout.
   - Result/final state: all six gates pass.

2. **Initial Python baseline**
   - Command: `.venv312\Scripts\python.exe -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80`
   - Error: six integration failures and 72.17% observed coverage.
   - Root cause: the test URL targeted an unrelated local PostgreSQL
     instance/password on port 5432.
   - Correction: used the isolated Milestone 4 PostgreSQL container/port.
   - Result/final state: superseded by 86 passes and 84.85% coverage.

3. **First Milestone 4 migration**
   - Command: `python -m alembic -c packages/database/alembic.ini upgrade head`
   - Error: PostgreSQL rejected an explicit foreign-key identifier longer
     than 63 characters.
   - Root cause: overlong human-readable constraint name.
   - Correction: shortened explicit identifiers; transactional DDL had rolled
     back safely.
   - Result/final state: upgrade passes.

4. **First drift check**
   - Command: `python -m alembic -c packages/database/alembic.ini check`
   - Error: proposed missing `ix_portfolios_tenant_status`.
   - Root cause: migration index was absent from SQLAlchemy metadata.
   - Correction: added the corresponding model index.
   - Result/final state: no new upgrade operations detected.

5. **First real PostgreSQL model insertion**
   - Command: focused portfolio PostgreSQL tests.
   - Error: PostgreSQL enum rejected uppercase Python enum names.
   - Root cause: legacy SQLAlchemy enum mappings emitted member names while
     migrations persisted lowercase values.
   - Correction: configured value-based enum serialization in the affected
     existing portfolio and ledger mappings.
   - Result/final state: integration tests pass.

6. **First ledger posting**
   - Command: focused complete accounting workflow test.
   - Error: ledger code exceeded the existing 64-character database bound.
   - Root cause: composite human-readable code was too long.
   - Correction: replaced it with a bounded deterministic code.
   - Result/final state: all postings pass.

7. **Viewer denial assertion**
   - Command: focused authorization integration test.
   - Error: test expected 403 but received concealed 404.
   - Root cause: the existing authorization policy intentionally conceals
     inaccessible tenant resources.
   - Correction: aligned the test with the central concealment policy.
   - Result/final state: viewer and outsider denial tests pass.

8. **First frontend portfolio test**
   - Command: `pnpm --filter @atlas/web test`
   - Error: a single-text query matched two intentional “not investment
     advice” notices.
   - Root cause: the assertion assumed unique text.
   - Correction: asserted all intended occurrences.
   - Result/final state: 23 web tests pass.

9. **First governed audit script on Windows**
   - Command: `pnpm audit:governed`
   - Error: `spawnSync pnpm.cmd EINVAL`.
   - Root cause: Windows process invocation incompatibility.
   - Correction: invoke pnpm through the Node executable and
     `npm_execpath`.
   - Result/final state: governed full and production audits pass.

10. **First production governed-audit path check**
    - Command: `pnpm audit:governed:prod`
    - Error: the same advisory resolved through an alternate known workspace
      ESLint/minimatch path.
    - Root cause: pnpm's production selector reported a different workspace
      traversal for the same dev-only package.
    - Correction: allow-listed only the two observed exact lint-tool paths,
      not arbitrary dependency paths.
    - Result/final state: both governed gates pass and fail closed on change.

11. **Python validation with unsupported driver URL**
    - Command: `$env:ATLAS_TEST_DATABASE_URL='postgresql+psycopg://...'; python -m pytest ...`
    - Error: `ModuleNotFoundError: No module named 'psycopg'`; ten integration
      tests could not connect and coverage was 65.58%.
    - Root cause: the project pins `asyncpg`, not psycopg.
    - Correction: changed the URL scheme to `postgresql+asyncpg`.
    - Rerun result: reached the database, then exposed the separate password
      typo described next.
    - Final state: correct driver used; 86 tests pass.

12. **Python validation with mistyped disposable password**
    - Command: `$env:ATLAS_TEST_DATABASE_URL='postgresql+asyncpg://atlas_m4:atlas_m4_local_only@127.0.0.1:55442/atlas_m4'; python -m pytest ...`
    - Error: `InvalidPasswordError`; ten integration tests could not connect.
    - Root cause: underscore was supplied where the inspected container used a
      hyphen (`atlas-m4-local-only`).
    - Correction: inspected the exact disposable container configuration and
      used its local-only password.
    - Result/final state: 86 tests pass, 84.85% coverage.

13. **First PowerShell runtime probe**
    - Command: `Invoke-WebRequest ... -SkipHttpErrorCheck`
    - Error: this Windows PowerShell version does not implement that parameter.
    - Root cause: PowerShell-version incompatibility in the validation command.
    - Correction: reran probes with `curl.exe`.
    - Result/final state: expected 200/401 statuses confirmed.

14. **Docker Scout image revalidation**
    - Command: `docker scout cves atlas-ai-api:latest --only-severity critical,high`
    - Error: Docker Scout requested Docker ID authentication.
    - Root cause: Docker Desktop is not authenticated to Docker Hub.
    - Correction attempted: confirmed Scout v1.23.1 is installed; no
      credential was created or requested because production/external
      credentials are outside this milestone.
    - Rerun result: not possible without manual authentication.
    - Final state: CVE-2026-12087 remains an explicit governed production
      blocker; it is not represented as cleared.

## 40. Known limitations

- private development only; no production approval
- deterministic simulated fixtures; no live provider validation
- long-only simulated positions
- weighted-average cost only; no tax-lot accounting
- no FX conversion; multi-currency totals may be incomplete
- bounded supported-currency set
- benchmark statistics require aligned persisted daily observations
- no browser end-to-end suite; UI components and production build are tested
- local Compose has Clerk disabled; authenticated API paths use synthetic auth
- Docker Scout needs manual Docker Hub authentication for a fresh image scan
- existing Starlette deprecation warnings remain outside the new domain

## 41. Deferred work

Independent Milestone 4 audit, broader property-based accounting tests, browser
E2E coverage, base-image refresh/re-scan, compatible lint dependency upgrade,
and production threat-model review are deferred. Milestone 5 has not begun.
No broker, order, payment, custody, advice, or real-money work is authorized.

## 42. Manual configuration

- Copy application `.env.example` files for local development.
- Provide development-only Clerk values only when testing real local sign-in.
- Keep all provider behavior deterministic/offline for milestone validation.
- Authenticate Docker Desktop manually before rerunning Docker Scout:
  `docker scout cves atlas-ai-api:latest --only-severity critical,high`.
- Do not place credentials in tracked files.

## 43. Production blockers

- independent security review not complete
- governance exceptions remain active and development-only
- GHSA-mh99-v99m-4gvg / CVE-2026-14257 remains in lint tooling
- CVE-2026-12087 remains governed in the Python base image and was not freshly
  cleared by Docker Scout
- no production identity, secrets, network, deployment, operational,
  regulatory, custody, or financial-control approval
- exception expires 2026-10-27 unless formally renewed or remediated

## 44. Final status: CONDITIONAL PASS

All Milestone 4 technical acceptance gates are satisfied. Only the existing
approved development exceptions remain. Private development and independent
audit may continue. Production and public use remain prohibited.

**This conditional pass applies only to the Milestone 4 simulated-portfolio
technical foundation. It does not authorise production deployment, public
customer access, live trading, custody, investment management, investment
advice, or handling real customer funds.**

## 45. Next permitted activity

An independent Milestone 4 audit may begin. Remediation of audit findings and
continued private development within the approved scope are permitted.
Milestone 5 must not begin without explicit approval after the Milestone 4
audit/governance decision.
