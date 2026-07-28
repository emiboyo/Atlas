# Milestone 4 Independent Audit — Simulated Portfolio Accounting and Read-Only Portfolio Analytics

## 1. Audit title

Atlas AI Milestone 4 Independent Financial-Systems, Security, Database-Integrity,
and Release-Gate Audit.

## 2. Audit date

2026-07-28.

## 3. Repository

`C:\Dev\Atlas`

## 4. Branch

`chore/milestone-4-audit`

## 5. Commit audited

`a1f659000d5d122126d28e372e646787514124dc` —
`merge: complete Milestone 4 simulated portfolios`.

## 6. Auditor role

Independent Financial-Systems Auditor, Security Auditor, Database-Integrity
Reviewer, and Release-Gate Reviewer.

## 7. Executive conclusion

The audit independently inspected the implementation rather than accepting
`docs/milestone-4-report.md` as proof. The governed eight-type simulated
transaction model exists, including independently implemented
`virtual_withdrawal` and standalone `simulated_fee`. PostgreSQL evidence
confirmed fixed-precision storage, tenant-bound foreign keys, unique
idempotency/reversal/position constraints, restrictive deletion behavior, and
append-only triggers. Direct service exercises confirmed withdrawal and fee
cash effects, balanced journals, fee reversal restoration, and safe audit
creation.

The native quality gates, real-PostgreSQL tests, reversible migration, fresh
database migration, Docker build/health checks, runtime probes, and dependency
governance checks passed. The independently observed Python result was 86 tests
at 84.77% coverage; the implementation report's 84.85% figure was not
reproduced, but the acceptance threshold remains satisfied.

No new Critical or High technical vulnerability and no real-money, broker,
order, custody, wallet, payment, or execution path was found. The two existing
time-bounded development exceptions remain governed and continue to prohibit
production.

## 8. Final status

**CONDITIONAL PASS — PRIVATE DEVELOPMENT ONLY**

- Milestone 4 technical status: pass
- Private-development permission: permitted under existing governance
- Production readiness: prohibited
- Public/customer use: prohibited
- Milestone 5: not permitted

## 9. Governance context

- Risk owner: Adebayo Olaegbe
- Review date: 2026-08-27
- Expiry date: 2026-10-27
- Authority: `docs/milestone-4-governance.md` and ADR 0009
- Existing exception decision: ADR 0006 and
  `docs/security-risk-exceptions.md`

The audit does not extend any date or scope.

## 10. Scope

The audit covered the portfolio API/domain, schemas, services, repositories,
metrics, central authorization, existing ledger, SQLAlchemy models, migration
0006, PostgreSQL constraints/triggers, frontend portfolio routes/components,
tests, CI, Docker, runtime endpoints, documentation, and ADRs 0010–0013.

## 11. Out-of-scope items

Production deployment, live providers, real money, banking, payments, custody,
wallets, brokerage, orders, execution, settlement, clearing, advice,
recommendations, AI-controlled transactions, customer funds, Terraform apply,
and Milestone 5 were not authorized or exercised.

## 12. Claim-to-evidence matrix

| Claim                                 | Independent evidence                                                                          | Conclusion                            | Discrepancy                        |
| ------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------- |
| Tenant-scoped UUID portfolios         | UUID model defaults, mandatory tenant columns, composite FKs, tenant-qualified services/tests | Verified                              | None                               |
| Append-only transactions              | migration trigger plus direct UPDATE/DELETE rejection                                         | Verified                              | None                               |
| Balanced journals                     | signed-entry code, deferred ledger controls, PostgreSQL journal sums                          | Verified                              | None                               |
| Weighted-average cost                 | Decimal service formulas and deterministic integration expectations                           | Verified                              | None                               |
| Safe reversals                        | compensating rows/journals, unique original link, reversal tests                              | Verified within long-only delta model | No destructive correction found    |
| Fixed precision                       | 18 inspected `NUMERIC(38,18)` columns; no REAL/DOUBLE portfolio persistence                   | Verified                              | None                               |
| Idempotency                           | required header/schema, SHA-256 fingerprint, unique constraints, sequential/concurrent tests  | Verified                              | None                               |
| PostgreSQL concurrency                | portfolio `FOR UPDATE`, position locks, separate-session tests                                | Verified                              | None                               |
| Valuation provenance                  | provider/timestamps/status/source fields in schemas/models/snapshots                          | Verified                              | None                               |
| Stale/missing/multi-currency states   | explicit response lists/null totals and tests                                                 | Verified                              | None                               |
| Descriptive analytics                 | deterministic Decimal history/statistics/benchmark code                                       | Verified                              | None                               |
| Central authorization                 | central `Permission` enum/matrix and shared service                                           | Verified                              | None                               |
| 86 Python tests                       | native execution                                                                              | Verified                              | None                               |
| 84.85% coverage                       | native execution produced 84.77%                                                              | Threshold verified                    | Exact report number not reproduced |
| 26 JS/package tests                   | 23 web + 2 UI + 1 shared                                                                      | Verified                              | None                               |
| Migration head 0006 and reversibility | downgrade/re-upgrade/fresh database/check                                                     | Verified                              | None                               |
| Healthy four-service Compose stack    | build, wait, ps, host probes                                                                  | Verified                              | None                               |
| No financial connectivity             | source/dependency/runtime inspection                                                          | Verified                              | None                               |

## 13. Architecture findings

Routes are transport-oriented; services own accounting and authorization;
repositories own parameterized persistence queries. The portfolio domain
extends the existing identity, tenancy, market-data, and ledger architecture.
No duplicate auth/tenant/ledger, mutable global database session, hidden
background loop, broker adapter, wallet, or payment abstraction was found.

## 14. Portfolio-model findings

Portfolios use server-generated UUIDs, mandatory tenants, retained creator,
bounded name/description, explicit supported base currency, active/archived
status, versioned updates, and server-resolved benchmark listing. Ordinary
archived mutations are rejected. There is no portfolio hard-delete API.
Composite foreign keys prevent cross-tenant children.

## 15. Transaction-type findings

All eight authorized types exist in the enum, strict schema, service,
migration constraint, API transport, and frontend selection:

1. `virtual_deposit`
2. `virtual_withdrawal`
3. `simulated_buy`
4. `simulated_sell`
5. `simulated_dividend`
6. `simulated_fee`
7. `simulated_split_adjustment`
8. `reversal`

The implementation report's transaction-model summary omitted withdrawal and
fee even though both are implemented. Finding M4-AUD-001 records this
reporting discrepancy.

## 16. Virtual-withdrawal findings

Withdrawal is a distinct transaction type, not a negative deposit. It requires
a positive amount, checks ledger-derived cash, posts negative virtual cash and
positive simulated capital, creates audit events, supports compensation, and
is exposed as “Record virtual withdrawal.” Concurrent-withdrawal tests prove
that only one oversubscribing request succeeds.

## 17. Standalone-fee findings

Standalone fee is independent of buy/sell fee fields. It requires a positive
amount, rejects insufficient cash, debits the virtual-cash signed balance,
offsets simulated fee expense, creates audit events, and supports reversal.
An independent PostgreSQL exercise produced:

```text
cash_after withdrawal_and_fee = 70.000000000000000000
all_balanced = True
cash_after_fee_reversal = 75.000000000000000000
```

## 18. Fixed-precision findings

Money, prices, quantity, fee, gross/net, cost, P&L, position, and valuation
columns use `NUMERIC(38,18)`. Services use `Decimal`, a fixed quantum,
half-even rounding, and a bounded absolute value. The browser sends decimal
strings rather than deriving persisted values with JavaScript arithmetic.
No portfolio financial `REAL`, `DOUBLE PRECISION`, SQLAlchemy `Float`,
`parseFloat`, or `Number(...)` persistence path was found.

## 19. Ledger-integrity findings

Each monetary posting creates one existing-ledger transaction and signed
entries in one currency. Deposit, withdrawal, buy, sell, dividend, and fee
rules balance exactly. Split adjustments produce no fabricated cash journal.
Sell gain/loss and fee treatment algebraically balance and matched PostgreSQL
tests. The existing deferred ledger trigger remains the commit-time backstop.

## 20. Account-balance findings

Virtual cash is computed as the sum of immutable ledger entries for the
portfolio/currency cash role. No mutable portfolio balance column exists.
Cash checks occur after the portfolio row is locked. Browser data cannot set
cash or ledger entries.

## 21. Position findings

One position exists per portfolio/listing. Quantity and cost cannot be
negative. Projection updates occur while the portfolio and existing position
are locked. Quantity, cost, average cost, realised P&L, state, and last
transaction sequence are deterministic.

## 22. Cost-basis findings

Weighted-average cost is implemented with Decimal. Buys add gross acquisition
value; separately expensed fees do not increase cost. Sells release average
cost proportionally and recognize net realised P&L. Dividends and standalone
fees do not change holding cost. Splits preserve total cost and recompute
per-unit cost. Closed positions have zero average cost.

## 23. Idempotency findings

Financial mutation keys are required and bounded to 8–128 characters. Scope is
portfolio-specific under tenant-bound data. Canonical Pydantic JSON is hashed
with SHA-256. Identical retry returns the original record; changed content
returns `409 idempotency_conflict`. Database uniqueness is authoritative.
Separate portfolios/tenants may safely reuse a key.

Snapshot creation has no client financial payload beyond the operation/key and
uses a portfolio/key unique constraint. A concurrent two-session audit
exercise returned the same snapshot ID twice.

## 24. Concurrency findings

PostgreSQL row locks, not process memory, serialize portfolio mutations.
Existing separate-session tests verify duplicate posts, overspend, and
oversell. The independently executed focused suite passed 11 tests. Unique
sequence, idempotency, position, ledger, snapshot, and reversal constraints
provide final race protection.

## 25. Reversal findings

Reversal creates a new transaction and opposing ledger entries. The original
record and journal entries remain. Position quantity/cost/realised deltas are
opposed. One unique original link prevents double reversal; reversal of a
reversal is rejected. Tenant/portfolio lookup is scoped, active portfolio is
required, and failure rolls back.

## 26. Append-only findings

Direct PostgreSQL attempts independently confirmed rejection of:

- UPDATE and DELETE on posted portfolio transactions
- UPDATE and DELETE on ledger entries
- UPDATE and DELETE on portfolio audit events
- UPDATE and DELETE on valuation snapshots

Valuation lines have the same append-only trigger. Foreign-key delete actions
on Milestone 4 history are `RESTRICT`. The only permitted posted-transaction
change is the narrowly checked posted-to-reversed status transition after a
valid compensating row exists.

## 27. Atomicity findings

The posting service commits transaction, journal, entries, projection, and
audit events together. Integration tests confirm an insufficient-cash failure
leaves no portfolio transaction or success event. Database errors trigger
rollback and a bounded concurrency error. No broad exception swallowing was
found in posting.

## 28. Authorisation findings

All eight portfolio permissions are centralized in `AuthorisationService`.
Routes require the existing active Atlas user dependency. Tenant membership is
resolved server-side. Owners/admins receive governed administrative rights;
members cannot archive or read portfolio audit history; viewers cannot mutate;
outsiders are concealed.

## 29. Tenant-isolation findings

Repository/service access is portfolio- and membership-scoped. Cross-tenant
objects are concealed as not found. Composite tenant foreign keys cover
portfolio accounts, transactions, positions, snapshots, and audit events.
Foreign-tenant and viewer integration tests passed. Client-supplied tenant,
role, permission, owner, and child linkage do not establish authority.

## 30. Schema and mass-assignment findings

Strict Pydantic models forbid extra fields. Clients cannot set status,
`is_simulated`, ledger transaction, P&L, balance, average cost, cost basis,
valuation provenance/status, actor, sequence, or arbitrary audit fields.
Dedicated reversal transport prevents clients from posting a reversal type
directly.

## 31. Valuation findings

Valuation lines retain Atlas listing/instrument identity, quantity, cost,
currency, price, provider, provider timestamp, receipt timestamp, status,
staleness, market value, and unrealised P&L. Provider choice remains
server-side. Missing prices are null, unavailable is explicit, stale remains
stale, and snapshots preserve source reference.

## 32. Multi-currency findings

Currency subledgers are explicit. Listing and transaction currencies must
match. Atlas performs no implicit conversion. Non-base exposure makes the base
total null and lists unconverted currencies. Integration evidence verified a
GBP/USD portfolio as incomplete.

## 33. Analytics findings

Allocation, asset-class concentration, realised/unrealised P&L, currency
exposure, history, percentage change, sample volatility, maximum drawdown, and
date-aligned benchmark comparison are descriptive. Time ranges and history are
bounded. Missing benchmark dates are explicit. Small deterministic history
tests independently passed; no prediction, expected-return, optimizer, target
allocation, recommendation, or quality score exists.

## 34. Frontend findings

Protected portfolio list/create/detail/transaction/holding/analytics/audit
routes build successfully. The transaction form exposes all seven
non-reversal activities with explicit “Record virtual/simulated” language.
No trade, order, broker, bank-connection, or real-funds control was found.
Permission booleans hide controls for viewers but are not the security
boundary.

## 35. Non-advisory-language findings

The portfolio UI and API state “Simulated portfolio — no real money or
orders.” Explanatory uses of broker/payment/recommendation terms are negations,
not product capabilities. Analytics disclaim advice and do not use
recommendation, guarantee, expected-return, target-price, or suitability
language.

## 36. Accessibility findings

Forms use labels, native inputs, bounded validation, focusable alert feedback,
and visible disabled state. Tables use captions and headers. Status is textual
rather than color-only. Allocation has a table/text representation.
Responsive layouts and theme-compatible classes are present. No browser E2E
or automated WCAG conformance run exists; this remains a development
limitation.

## 37. Observability findings

Portfolio counters use bounded operation, outcome, transaction type,
completeness, metric, and invariant-code labels. No user/portfolio/transaction
ID, name, note, amount, token, cookie, credential, or raw payload label exists.
Existing request IDs and structured logging remain in use. Portfolio services
do not log full holdings or unrestricted notes.

## 38. Migration findings

- Milestone 3 head: `20260727_0005`
- Milestone 4 head: `20260728_0006`
- current → 0005 downgrade: pass
- 0005 → 0006 re-upgrade: pass
- Alembic drift check: pass
- fresh database through all six revisions: pass
- seven portfolio tables: present
- 18 inspected financial columns: all `NUMERIC(38,18)`
- six relevant append-only triggers: present
- 67 portfolio constraints: inspected
- foreign-key delete policy: restrictive
- disposable database: removed
- development database: left at 0006

No changes to revisions 0001–0005 were introduced by the Milestone 4 merge.

## 39. Reconstruction findings

Transactions persist immutable quantity, cost, and realised-P&L deltas with a
unique deterministic sequence. Applying those deltas in sequence reconstructs
the stored position model. The representative integration sequence
deposit/buy/sell/dividend/split/reversal matched its asserted stored position
and ledger totals. The independent withdrawal/fee/reversal exercise matched
ledger-derived cash. No reconstruction mismatch was found.

## 40. Security-test findings

Unauthenticated runtime access returned 401. Existing tests independently
passed active-user, role, tenant concealment, insufficient cash/quantity,
duplicate/conflicting requests, concurrent overspend/oversell, duplicate
reversal, archived mutation, mass assignment, invalid values, and audit
behavior. No SQL string interpolation was found in portfolio repositories.

## 41. Quality-gate results

| Gate                             | Result                               |
| -------------------------------- | ------------------------------------ |
| `pnpm install --frozen-lockfile` | Pass                                 |
| `pnpm format:check`              | Pass                                 |
| `pnpm lint`                      | Pass                                 |
| `pnpm typecheck`                 | Pass                                 |
| `pnpm test`                      | Pass, 26 tests                       |
| `pnpm build`                     | Pass                                 |
| Ruff format                      | Pass, 74 files                       |
| Ruff check                       | Pass                                 |
| strict mypy                      | Pass, 55 source files                |
| pytest with coverage             | Pass                                 |
| pip check                        | Pass                                 |
| pip-audit                        | Pass, no known vulnerabilities       |
| governed pnpm audits             | Pass                                 |
| raw pnpm audits                  | Expected non-zero, one governed High |
| `git diff --check`               | Pass                                 |

## 42. Coverage result

```text
86 passed, 6 warnings in 5.58s
Total coverage: 84.77%
Required minimum: 80%
```

The warnings are existing Starlette status-name deprecations in identity and
market code/tests, not test failures.

## 43. Dependency findings

### M4-AUD-004 — Governed Node development advisory

- Severity: High
- Advisory: GHSA-mh99-v99m-4gvg / CVE-2026-14257
- Package/path: `brace-expansion` through ESLint/minimatch
- Scope: development lint tooling; absent from runtime images
- Fix: patched package exists, but forced incompatible major resolution is not
  approved
- State: Governed until 2026-10-27; review 2026-08-27

### M4-AUD-005 — Governed Python-image operating-system advisory

- Severity: Critical
- Advisory: CVE-2026-12087
- Component: Perl inherited from `python:3.12.13-slim`
- Scope: present but not invoked; Uvicorn is PID workload
- Controls: non-root, read-only, `no-new-privileges`, no host bind mounts
- State: Governed until 2026-10-27; production prohibited

No new Node or Python application dependency was introduced by Milestone 4.
No chart, financial-math, broker, payment, wallet, or execution SDK was added.
Docker Scout was not attempted because Docker Desktop was not authenticated;
the audit did not request or store credentials.

## 44. Docker results

Compose configuration, API/web builds, `up --detach --wait`, and service status
passed. PostgreSQL, Redis, API, and web were healthy. API and web run as UID
1001, with read-only root filesystems, `no-new-privileges`, and no host bind
mounts. API runs Uvicorn directly. Perl is present in the base layer but is not
the running process. ESLint is absent from the API runtime.

Container `0.0.0.0` binding is intentional for local Docker port publishing.
It is not production or public-access approval.

## 45. Runtime results

| Runtime check                          | Result                                          |
| -------------------------------------- | ----------------------------------------------- |
| Homepage                               | 200                                             |
| Liveness                               | 200                                             |
| Readiness                              | 200                                             |
| Metrics                                | 200                                             |
| OpenAPI                                | 200                                             |
| Unauthenticated portfolios             | 401                                             |
| Migration in built API image           | 0006 head                                       |
| Authenticated accounting flows         | Passed using synthetic auth and real PostgreSQL |
| Stale/missing/multi-currency analytics | Passed in integration suite                     |

No production Clerk or provider credential and no live provider was used.

## 46. Corrective changes

No application or migration correction was made. Independent evidence did not
justify changing financial logic, constraints, authorization, or tests.

The only repository change produced by this audit is this audit report.
Reporting discrepancies are preserved in the original implementation report
and explicitly identified here rather than rewriting historical evidence.

## 47. Unresolved findings

| ID         | Title                                                                                                       | Severity      | State                           |
| ---------- | ----------------------------------------------------------------------------------------------------------- | ------------- | ------------------------------- |
| M4-AUD-001 | Implementation report transaction summary omits withdrawal and standalone fee although code implements both | Informational | Open documentation discrepancy  |
| M4-AUD-002 | Implementation report cites ADR 0006 as its decision reference instead of primary Milestone 4 ADR 0009      | Low           | Open documentation discrepancy  |
| M4-AUD-003 | Reported 84.85% coverage was not reproduced; audit observed 84.77%                                          | Informational | Accepted; threshold passes      |
| M4-AUD-004 | `brace-expansion` advisory in lint chain                                                                    | High          | Governed                        |
| M4-AUD-005 | Perl base-image advisory                                                                                    | Critical      | Governed                        |
| M4-AUD-006 | No browser E2E/WCAG conformance run or real Clerk runtime exercise                                          | Low           | Accepted development limitation |

M4-AUD-001 does not indicate missing functionality: code, migration, frontend,
and direct PostgreSQL evidence prove both required types. M4-AUD-002 and
M4-AUD-003 do not weaken technical controls. The only High/Critical items are
the two pre-existing governed exceptions.

## 48. Known limitations

- private deterministic provider data only
- no production authentication/perimeter validation
- no PostgreSQL RLS defense-in-depth
- long-only weighted-average simulated accounting, not tax-lot accounting
- no FX conversion
- no browser end-to-end or formal WCAG automation
- no production load, failover, backup/restore, or disaster-recovery exercise
- Docker Scout requires authentication and was not rerun

## 49. Production blockers

Production remains blocked by the two unresolved governed advisories,
independent production security/regulatory/privacy review, production
identity/perimeter/rate-limit validation, market-data licensing, operational
resilience evidence, secrets/IAM review, and explicit approval for any live
financial capability.

## 50. Final decision

**CONDITIONAL PASS — PRIVATE DEVELOPMENT ONLY**

Milestone 4's simulated-portfolio technical foundation satisfies its audited
acceptance criteria. Private development and remediation of audit findings may
continue within the existing time-bounded authority.

This decision does not authorize production deployment, public customer
access, live trading, real-money investing, banking, payment processing,
custody, brokerage, order routing, clearing, settlement, investment advice,
personalized recommendations, AI-controlled transactions, or customer funds.

## 51. Milestone 5 decision

**Milestone 5 may not begin.**

A separate explicit governance decision is required. This audit neither grants
nor implies that permission.

## 52. Appendix of exact commands

### Preflight

```powershell
git branch --show-current
git status
git log --oneline --graph --decorate -15
git diff --check
git rev-parse HEAD
git ls-files | findstr /I ".env"
.\.venv312\Scripts\python.exe --version
node --version
pnpm --version
docker version --format "client={{.Client.Version}} server={{.Server.Version}}"
```

### Native gates

```powershell
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

pnpm audit:governed
pnpm audit:governed:prod
pnpm audit --prod
pnpm audit
git diff --check
```

Raw `pnpm audit` commands returned exit 1 because they report the known High
advisory. Root cause: the governed ESLint/minimatch development path.
Correction: none forced; the approved fail-closed wrappers were run and passed.
Final state: governed for private development, production prohibited.

### Migration and PostgreSQL

```powershell
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini current
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini downgrade 20260727_0005
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini upgrade 20260728_0006
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini check

docker exec atlas-m4-development-postgres psql -U atlas_m4 -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE atlas_m4_audit_fresh;"
$env:ATLAS_DATABASE_URL='postgresql+asyncpg://atlas_m4:<local-only>@127.0.0.1:55442/atlas_m4_audit_fresh'
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini upgrade head
docker exec atlas-m4-development-postgres psql -U atlas_m4 -d atlas_m4_audit_fresh ...
docker exec atlas-m4-development-postgres psql -U atlas_m4 -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE atlas_m4_audit_fresh WITH (FORCE);"
```

The first append-only `DO` block invocation used `DO \$\$` through PowerShell
and failed with PostgreSQL syntax error at `\`. Root cause: shell quoting, not a
database control failure. Correction: pass the psql command in a PowerShell
single-quoted argument with literal `$$`. Rerun result: all eight UPDATE/DELETE
tampering attempts were rejected. Final state: append-only controls pass.

### Docker and runtime

```powershell
docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose ps
docker compose run --rm api alembic -c packages/database/alembic.ini upgrade head
docker compose run --rm api alembic -c packages/database/alembic.ini current
docker inspect atlas-ai-api-1 atlas-ai-web-1 --format "{{.Name}} user={{.Config.User}} readonly={{.HostConfig.ReadonlyRootfs}} security={{json .HostConfig.SecurityOpt}} binds={{json .HostConfig.Binds}}"
docker top atlas-ai-api-1 -eo pid,user,args
docker top atlas-ai-web-1 -eo pid,user,args
curl.exe --silent --show-error --output NUL --write-out "%{http_code}" <local-url>
```

An initial combined container inspection invoked
`python -c "import sys; print(sys.version)"` through nested shell quotes and
produced a Python `SyntaxError` at `import`. Root cause: validation-command
quoting. Correction: reran as `docker compose exec -T api python --version`.
Rerun result: Python 3.12.13. Final state: runtime inspection passes.
