# Atlas AI Milestone 5 Implementation Report

> **Current status: CONDITIONAL PASS — PRIVATE DEVELOPMENT ONLY**
>
> This status applies only to the Milestone 5 technical foundation. It does not authorise
> production deployment, public access, live trading, custody, investment management,
> personalised advice, autonomous financial action, external AI integration, or handling real
> customer funds.

## 1. Executive summary

Atlas now has a tenant-isolated historical strategy-research foundation: immutable strategy
versions, a deterministic Decimal backtest engine, append-only simulated evidence, descriptive
results and benchmarks, optional local explanations, protected APIs, protected responsive screens,
auditing, observability, PostgreSQL integrity controls, tests, and documentation.

The technical gates passed. The status remains conditional because the existing governed
development-only security exceptions remain active. No production approval is implied.

## 2. Governance authority

- Authority: `docs/milestone-5-governance.md` and ADR 0014.
- Risk owner: Adebayo Olaegbe.
- Review: 2026-08-27.
- Expiry: 2026-10-27.
- Permitted: private Milestone 5 development and local/CI testing.
- Prohibited: production, public users, real money, execution, custody, advice, autonomous
  financial action, external AI, and Milestone 6.

## 3. Architecture implemented

`/api/v1/research` uses thin FastAPI routes, strict schemas, an authorization/orchestration
service, tenant-aware repositories, a pure deterministic engine, SQLAlchemy models, and PostgreSQL
constraints/triggers. The protected Next.js route tree presents the same non-executing boundary.

## 4. Existing architecture preserved

Clerk authentication, Atlas tenancy, central permissions, request IDs, stable error envelopes,
market-data ownership, portfolio accounting, Redis, metrics, Docker hardening, and the Alembic
chain remain intact. Research does not mutate Milestone 4 portfolio or ledger records.

## 5. Strategy model

Strategies have immutable Atlas UUIDs, tenant, name, description, research purpose, active/archive
status, current-version pointer, creator, timestamps, and an optimistic-lock version.

## 6. Strategy-version model

Versions are append-only and carry a monotonically increasing number, typed configuration,
canonical fingerprint, idempotency evidence, explicit currency, optional benchmark, author, and
timestamp. Changes require a new version.

## 7. Rule model

The initial allow-listed rule is `sma_crossover` schema version 1. Short and long windows are
bounded and ordered; unknown request fields fail validation.

## 8. Backtest-run model

Runs bind the exact tenant, strategy version, listing, dates, starting virtual capital, execution,
fee, slippage, sizing, missing-data assumptions, engine/software versions, fingerprints, status,
actor, and timestamps.

## 9. Simulated-event model

Entry/exit events are explicitly simulated and ordered. Each records decision/execution time,
Decimal price/quantity/value/costs, cash and position before/after, triggered rule IDs, and source
observation IDs.

## 10. Result model

One immutable result per run stores capital, ending value, simulated P&L, historical percentage
change, event/trade counts, drawdown, volatility, turnover, benchmark change, quality counts,
completeness, and checksum.

## 11. Explanation model

Explanations are local deterministic descriptions with engine/template versions, input/output
fingerprints, limitations, idempotency, author, status, and time. They are append-only.

## 12. Tenant-isolation design

Every aggregate is resolved server-side. Membership is checked through the parent strategy;
foreign resources are concealed. Composite tenant/parent foreign keys prevent cross-tenant child
records.

## 13. Authorisation matrix

Owners/admins have all research permissions. Members can create/update strategies, create versions
and runs, read/compare, and request explanations. Viewers are read-only. Archive and audit access
are restricted to owner/admin. API checks are authoritative.

## 14. Backtest workflow

The service locks the strategy, validates the immutable version, resolves server-owned simulated
candles, creates requested/started audits, executes synchronously, derives events/equity/result,
marks completion, writes the completion audit, and commits once. Failure rolls back the aggregate.

## 15. Look-ahead prevention

Signals use observations through the decision index only. Next-open/next-close policies execute at
the next observation. Same-close is explicitly labelled as an assumption.

Focused regression evidence:

- Future-candle injection did not change any earlier rule-derived decision.
- Out-of-order inputs produced the same events, equity series, and checksum after canonical
  ordering.
- Every rule-derived next-open event used `execution_index == decision_index + 1`.
- Every persisted decision/execution relationship was chronological; no decision timestamp
  consumed a later observation.

## 16. Leakage prevention

The engine has no network, clock, external model, portfolio, broker, or provider-selection input.
Source observations are ordered and fingerprinted. Explicit regressions changed only the final
future value and proved earlier events unchanged, proving that no full-series normalization is
used. Changing high, low, adjusted close, and volume while retaining the close series did not alter
rule events or equity, proving that target-derived fields do not enter rule features. Removing an
observation shortened the equity series without fabrication or future-aware filling.

## 17. Execution assumptions

Allow-listed policies are next open, same close, and next close. They describe historical
simulation prices and cannot submit an order.

## 18. Fee model

Zero fee, fixed amount per event, and bounded percentage of gross simulated value are explicit and
persisted.

## 19. Slippage model

Zero or bounded fixed basis points are explicit, persisted, and included in Decimal calculations.

## 20. Position-sizing model

Fixed simulated cash, bounded percentage of available simulated cash, and fixed quantity are
supported. The engine is long-only and prevents negative cash/positions.

## 21. Currency policy

Currency is explicit. Listing and benchmark quote currencies must equal the version base currency.
No silent conversion occurs.

## 22. Data-quality policy

Only stored `atlas_simulated` daily candles are resolved server-side. Stale input marks results
incomplete. Quality counts and the data fingerprint are exposed separately.

## 23. Missing-data policy

The selected policy is retained immutably. Insufficient observations fail explicitly. No
fabrication, interpolation, forward fill, or relabelling occurs.

## 24. Deterministic replay

The pure Decimal engine has no random, wall-clock, network, or unordered-iteration dependency.
Identical inputs produced identical events and result checksums in tests.

## 25. Result checksum

Canonical SHA-256 fingerprints identify configuration and source data; SHA-256 result evidence
covers ordered derived events, equity, and metrics.

## 26. Historical metrics

Ending value, simulated P&L, historical return, event/trade count, maximum drawdown, rolling
volatility, turnover, and quality counts are descriptive and non-advisory.

## 27. Benchmark comparison

An optional same-currency benchmark produces descriptive buy-and-hold historical change over the
run period. Multi-run comparison flags period/currency mismatches and performs no normalization.

## 28. Explainable AI design

No external AI is used. A versioned local template describes stored evidence and can be disabled
with `ATLAS_RESEARCH_EXPLANATIONS_ENABLED=false`.

## 29. AI restrictions

Explanation output cannot create/modify strategies, versions, events, portfolios, or transactions;
trigger tools; make recommendations; assess suitability; or predict performance.

## 30. Model/prompt provenance

Engine, engine version, template version, fingerprints, type, author, and timestamp are persisted.
Full definitions, prompts, outputs, tokens, credentials, and raw payloads are excluded from logs.

## 31. Audit events

Append-only events cover strategy create/update/archive, version creation, backtest
requested/started/completed, and explanation generation with bounded identifiers and metadata.

## 32. API endpoints

Versioned authenticated endpoints cover strategy CRUD/archive/permissions, versions, runs, events,
equity, result, data quality, bounded `POST` comparison, explanations, and strategy/run audits.
Mutations use idempotency headers; request validation and errors are stable.

## 33. Frontend routes and screens

Protected routes exist for research overview, strategies, creation/detail/version history/version
definition, run history/configuration/detail/events/analytics/explanations/audit, and comparison.
Every research screen presents the historical/non-advisory boundary and no trading controls.

## 34. Accessibility

Forms have labels and fieldsets, Decimal/date inputs are explicit, tables have captions, status is
not color-only, charts have text alternatives, focusable status output is present, and navigation
is keyboard-accessible and responsive.

## 35. Observability

Bounded Prometheus counters cover strategy/backtest/conflict/explanation outcomes. Existing request
IDs, structured errors, logging, health, readiness, and metrics remain active.

## 36. Security controls

Strict schemas, central permissions, object concealment, tenant-qualified foreign keys, row locks,
idempotency fingerprints, append-only triggers, bounded inputs, non-root containers, read-only root
filesystems, no-new-privileges, and no host mounts were validated.

## 37. Tests added

Unit/integration coverage includes schemas, indicators, fingerprints, deterministic replay,
changed assumptions, six explicit causal/leakage regressions, full PostgreSQL workflow,
tenant/viewer denial, idempotency, separate-session run and explanation races, archive races,
duplicate-effect checks, concurrent version creation, audit creation, and append-only rejection.
Frontend tests cover boundary, assumptions, rules, data quality, alternatives, explanations, audit
state, and absent execution controls.

## 38. Python tests and coverage

`pytest` passed **102 tests**. Combined API/database coverage was **84.93%**, above the 80% gate.
The focused research evidence comprises 9 unit/regression tests and 7 real-PostgreSQL integration
tests. Ruff format/lint and strict mypy passed.

## 39. Frontend tests

The JavaScript/package suite passed **29 tests total**:

- Web: 26 tests across 5 files.
- Shared package: 1 test across 1 file.
- UI package: 2 tests across 1 file.

ESLint, TypeScript, and the Next.js production build passed.

## 40. PostgreSQL migration revision

Milestone 5 head: `20260728_0007`; parent: Milestone 4 head `20260728_0006`.

## 41. Migration validation

Upgrade, downgrade to 0006, re-upgrade, and Alembic drift check passed. A disposable empty database
was migrated through every revision to 0007 and removed. The development and Compose databases
were left at 0007.

Schema inspection confirmed eight research/backtest tables, 27 financial `numeric(38,18)` columns,
parent/tenant and idempotency constraints, unique event/equity sequences, indexes, and append-only
triggers.

## 42. Reproducibility evidence

Two identical pure-engine executions returned identical ordered events and checksum. Idempotent API
replay returned the original run. A changed fee changed the checksum.

## 43. Concurrency evidence

All database concurrency evidence used real PostgreSQL with a separate `AsyncSession` per
contender:

- Two identical backtest-run requests using one idempotency key returned the same run ID and
  produced exactly one run, one result, one event sequence, and the three expected run lifecycle
  audits.
- Two simultaneous execution attempts are represented by the synchronous atomic `create_run`
  boundary; the same race produced one completed event set and one result.
- Concurrent reuse of one run idempotency key with different starting capital produced one success
  and one stable `409 idempotency_conflict`, with exactly one run stored.
- Two identical explanation requests returned the same explanation ID and produced exactly one
  explanation and one `research.explanation.generated` audit. The service now locks the run before
  its idempotency check.
- Archive versus run creation and archive versus version creation were serialized on the strategy
  row. Archive always completed; the child either completed before archive or failed closed with
  `strategy_archived`. No partial or duplicate child evidence remained.
- Grouped event-sequence inspection found no duplicates. Unique run/result/explanation constraints
  and exact audit counts confirmed no duplicate results, explanations, or lifecycle audit records.
- Concurrent identical strategy-version requests continued to converge on one immutable version.

Strategy/run row locks, unique idempotency constraints, unique event sequences, one-result-per-run,
and a single database transaction are the serialization and integrity strategy.

## 44. Docker validation

`docker compose config --quiet`, builds, forced recreation, and health checks passed. PostgreSQL,
Redis, API, and web are healthy. API user is `atlas`; web user is `nextjs`; both are non-root,
read-only, no-new-privileges, and have no mounts.

## 45. Runtime validation

Homepage, liveness, readiness, metrics, and OpenAPI returned 200. OpenAPI contains research routes.
Unauthenticated strategy listing returned 401. Authenticated workflows, replay, denials,
append-only behavior, explanation generation, and audits passed against PostgreSQL integration
tests using synthetic identities and local fixtures.

## 46. Dependency findings

- `pip check`: passed.
- `pip-audit`: no known Python vulnerabilities.
- Governed Node audits: passed under the existing exception.
- Raw Node audits: expected High finding `GHSA-mh99-v99m-4gvg` /
  `CVE-2026-14257` in the ESLint/minimatch development chain. The temporary development-only
  decision in `docs/security-risk-exceptions.md` expires 2026-10-27.
- Existing base-image exception `CVE-2026-12087` remains governed for development only.
- Docker Scout could not re-scan because Docker Desktop required Docker Hub authentication. This
  did not replace or widen either existing exception.

## 47. Files created

- Backend research package and two research test modules.
- Research SQLAlchemy model and Alembic revision 0007.
- Complete protected `/app/research` route tree, three research components, and frontend tests.
- Eight architecture/risk documents and ADRs 0015–0017.
- This report.

## 48. Files modified

API v1 routing, central authorization, configuration, API env template, database model exports and
enums, application navigation/styles, one now-unnecessary typed-route assertion, README,
authorization documentation, and CI migration downgrade target.

## 49. Corrective changes made during implementation

| Failed command                            | Relevant error/root cause                                                                             | Correction and rerun                                                                                          |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Research PostgreSQL tests                 | Case-sensitive wording assertion; duplicate deterministic candle fixture                              | Corrected assertion and made fixture seeding idempotent; 2/2 integration tests passed, then full 91/91 passed |
| `ruff check` / `mypy`                     | Unused imports, broad exception assertion, sorted exports, optional benchmark prices, import ordering | Used precise DB exception, fallback close values, sorted imports/exports; Ruff and mypy passed                |
| `pnpm lint`                               | Eight typed-route assertions became unnecessary after routes were generated                           | Removed only redundant assertions; lint passed                                                                |
| `docker compose exec ... alembic current` | Persistent Compose database was at 0006                                                               | Applied checked upgrade; current is 0007                                                                      |
| Runtime PowerShell status command         | Attempted `$home`, a protected case-insensitive system variable                                       | Renamed to `$homepageStatus`; all five runtime endpoints returned 200                                         |
| `pnpm audit --prod` and `pnpm audit`      | Existing governed brace-expansion High advisory                                                       | No unsafe override; governed audit passed and existing exception remains                                      |
| `docker scout cves ...`                   | Docker Hub login required                                                                             | No credentials requested or bypass attempted; recorded as a manual re-scan requirement                        |

An early Prettier invocation included Python paths and reported that it could not infer a parser;
Python formatting was rerun with Ruff and passed. An initial patch context mismatch made no change;
the edit was split into verified patches.

Focused-remediation command evidence:

- `.\.venv312\Scripts\python.exe -m pytest apps/api/tests/test_research.py -vv -x` passed
  9/9 regression tests.
- `ATLAS_TEST_DATABASE_URL=... pytest apps/api/tests/test_research_integration.py -vv -x`
  passed 7/7 real-PostgreSQL integration tests.
- The first combined Ruff/mypy/unit-test command reached its 120-second wrapper timeout after Ruff
  and mypy passed but before pytest returned. Running the unit suite independently completed in
  5 seconds with 9/9 passing; no control or timeout setting was weakened.
- The first focused `pnpm format:check` identified only Markdown wrapping in this report. Running
  `pnpm exec prettier --write docs/milestone-5-report.md` followed by `pnpm format:check` passed.
- Full rerun: 102/102 Python tests passed at 84.93% coverage; all 29 JavaScript/package tests,
  lint, typecheck, builds, migrations, Docker health, and runtime endpoints passed.
- Raw `pnpm audit --prod` and `pnpm audit` continued to return the existing governed
  `GHSA-mh99-v99m-4gvg` finding. Both governed audit commands passed; no unsafe upgrade was forced.

## 50. Known limitations

The initial runner executes one SMA-crossover rule and one listing; it is synchronous and
long-only. Stop-loss, take-profit, multi-asset logic, deterministic rebalance, calendar-aware gap
counts, corporate-action adjustments beyond stored adjusted close, sophisticated benchmark
alignment, distributed workers, retention, and production-scale performance are absent. Several
detail screens establish governed accessible route contracts but require richer API-backed
visualisation in a future authorised milestone. Docker Scout requires authenticated revalidation.

## 51. Deferred work

Independent security/model-risk review, base-image and Node advisory remediation, full concurrency
fault-injection matrix, richer historical calendars/quality, worker orchestration, retention,
performance/load testing, expanded rule types, and production operating controls are deferred.
None is authorised implicitly.

## 52. Manual configuration

Set only private-development values from application `.env.example` files. The API setting
`ATLAS_RESEARCH_EXPLANATIONS_ENABLED` controls local explanations. Clerk remains required for the
protected browser. Do not add production, broker, payment, live-provider, or external-AI
credentials.

## 53. Production blockers

Governance prohibition, both temporary security exceptions, independent review, authenticated
image scanning, limited data-quality/calendar semantics, synchronous scale, incomplete operational
hardening, and absence of production authorization all block production/public use.

## 54. Final status

**CONDITIONAL PASS — MILESTONE 5 TECHNICAL FOUNDATION, PRIVATE DEVELOPMENT ONLY.**

All validated technical gates pass; only existing governed private-development exceptions remain.
No new exception was created. Production, public, live, advisory, executing, real-money, custody,
external-AI, and Milestone 6 activity remains prohibited.

## 55. Next permitted activity

The next permitted activity is independent Milestone 5 audit and remediation of documented
limitations within private development. Do not commit, merge, deploy, begin Milestone 6, or widen
scope without explicit approval.
