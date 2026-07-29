# Milestone 5 Independent Audit

## 1. Audit title

**Milestone 5 Independent Audit — Explainable AI Strategy Research,
Historical Backtesting and Simulation**

## 2–6. Audit identity

| Field          | Value                                                                                                                                |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Audit date     | 2026-07-29                                                                                                                           |
| Repository     | `C:\Dev\Atlas`                                                                                                                       |
| Branch         | `chore/milestone-5-audit`                                                                                                            |
| Commit audited | `2ed61938bc74930ebb703569f7f6b6009a7d7057`                                                                                           |
| Auditor role   | Independent quantitative-systems, model-risk, security, database-integrity, backtest-integrity, AI-safety, and release-gate reviewer |

The implementation merge `2ed6193` and feature commit `ef926c3` were present.
Pre-audit status was clean. The changes listed in section 51 are audit
corrections made after that baseline.

## 7–8. Executive conclusion and final status

> **FINAL STATUS: FAIL**
>
> The deterministic backend foundation is substantially sound after three
> audit corrections, and all final automated, migration, build, and container
> gates pass. Milestone 5 nevertheless fails acceptance because the research
> frontend materially overstates implemented workflows: most research screens
> are static route shells rather than API-backed, permission-aware workflows.
> Database parent-child integrity, declared missing-data policies, atomic
> fault-injection evidence, and research observability also remain incomplete.

No unresolved look-ahead, leakage, deterministic-replay, concurrency,
append-only, authentication-bypass, cross-tenant, or fixed-precision failure
was reproduced after correction. The open frontend discrepancy is a
materially unsupported implementation claim and therefore invokes the
mandatory `FAIL` rule.

## 9. Governance context

| Decision                                       | State                                                             |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| Risk owner                                     | Adebayo Olaegbe                                                   |
| Review date                                    | 2026-08-27                                                        |
| Exception expiry                               | 2026-10-27                                                        |
| Private development                            | Previously authorised, but this audit does not accept Milestone 5 |
| Production/public use                          | Prohibited                                                        |
| External production AI                         | Prohibited                                                        |
| Live trading, execution, advice, or real money | Prohibited                                                        |
| Milestone 6                                    | Prohibited                                                        |

This audit does not extend dates, create an exception, or authorise production.
The decisions in ADR 0014 and `docs/security-risk-exceptions.md` remain
controlling.

## 10–11. Scope and out-of-scope items

The audit covered research code, PostgreSQL models and migration 0007, APIs,
tests, frontend routes, CI, supply chain, Docker, runtime endpoints, and the
authoritative governance and architecture records. It did not deploy, contact
live financial or AI providers, use production Clerk credentials, run
Terraform, add trading or payment capability, or begin Milestone 6.

## 12. Claim-to-evidence matrix

| Claim                                            | Independent evidence                                                                                            | Conclusion                                                |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Tenant-scoped strategies and central permissions | Service/repository inspection; real-PostgreSQL workflow and foreign-tenant tests                                | Supported at service/API boundary                         |
| Immutable versions and completed history         | Migration triggers plus direct rejected `UPDATE`/`DELETE` attempts                                              | Supported, subject to parent-integrity finding M5-AUD-005 |
| Allow-listed SMA crossover                       | Strict discriminated schemas and adversarial unit tests                                                         | Supported                                                 |
| Decimal deterministic engine                     | Decimal-only engine, 27 `NUMERIC(38,18)` columns, reconstruction test                                           | Supported after corrections 001 and 003                   |
| Explicit assumptions                             | Immutable version/run configuration contains capital, fee, slippage, sizing, execution, currency, and benchmark | Supported                                                 |
| Append-only events/results/explanations/audits   | PostgreSQL triggers and direct mutation rejection                                                               | Supported                                                 |
| Deterministic replay and fingerprints            | Unit regressions, real-PostgreSQL reconstruction, expanded data/result checksums                                | Supported after correction 003                            |
| Look-ahead/leakage prevention                    | Future mutation, ordering, target-field, missing-data, and timestamp regressions                                | Supported after correction 001                            |
| Missing/stale/unavailable handling               | Stale evidence exists; unavailable now fails closed; declared skip policies are not implemented                 | Partially supported; M5-AUD-006 open                      |
| No external AI or live provider                  | Static import/dependency/network review and runtime inspection                                                  | Supported                                                 |
| PostgreSQL concurrency                           | Separate `AsyncSession` races for run, conflict, execution, explanation, archive/version                        | Supported                                                 |
| Migration head/reversibility                     | Fresh upgrade, 0007 downgrade/upgrade, `alembic check`                                                          | Supported                                                 |
| Python totals                                    | 111 passed; 85.27% coverage                                                                                     | Original 102/84.93% superseded                            |
| JavaScript/package totals                        | 29 passed across 7 files                                                                                        | Supported                                                 |
| Eight research tables and numeric schema         | Metadata/migration/catalog inspection; 27 numeric columns                                                       | Supported                                                 |
| Healthy Compose stack                            | Rebuilt images; PostgreSQL, Redis, API, and web healthy                                                         | Supported                                                 |
| Functional research frontend                     | Only strategy list/create is materially API-backed; most workflows are static                                   | Not supported; release-blocking                           |

## 13. Architecture findings

Routes are generally thin, services own rules, repositories own common
queries, and the deterministic engine has no transport or network dependency.
No arbitrary strategy-code executor, broker adapter, worker loop, duplicate
identity model, or portfolio mutation path was found. Some persistence queries
remain in the service and research metrics are declared without use, but these
do not invalidate engine determinism.

## 14. Strategy-model findings

Strategies use server-generated UUIDs, mandatory tenant/creator fields,
bounded strict schemas, lifecycle controls, optimistic locking, archive
controls, and audit events. No hard-delete or real-account identifier is
exposed. Client attempts to submit tenant, creator, ownership, or status fields
are rejected by strict schemas.

## 15. Strategy-version findings

Version numbering and fingerprints are server-controlled. Published versions
are protected by append-only triggers and completed runs retain the exact
version identifier. Concurrent version creation is serialized. The database
does not, however, prove that a same-tenant run's `strategy_version_id`
belongs to its `strategy_id`; see M5-AUD-005.

## 16. Rule-model findings

Only typed `sma_crossover` rules are accepted. Window bounds and
`short_window < long_window` are enforced. Unknown, nested unexpected,
executable, SQL-like, and mass-assignment fields fail closed. No Python,
JavaScript, SQL, URL, or natural-language execution path exists.

## 17. Fixed-precision findings

Research persistence contains 27 `NUMERIC(38,18)` columns. Financial
calculation uses `Decimal`; no SQLAlchemy `Float`, SQL floating type, or
JavaScript-derived authoritative financial persistence was found. API decimal
serialization is string-safe. No silent currency conversion path exists.

## 18. Market-data provenance findings

Listing and provider resolution are server-controlled and use stored
`atlas_simulated` observations. Provider, interval, observation identity,
period bounds, receipt timestamp, currency, and data status are now included
in the data fingerprint. Browser-supplied prices/providers are rejected.
Unavailable observations now abort atomically.

## 19. Look-ahead findings

Future-candle injection and future-field mutation do not change earlier
decisions. SMA evaluation consumes only the prefix through the decision
observation. `next_open`, `next_close`, and `same_close` use the documented
source fields. Correction 001 fixed stored execution timestamps so
`simulated_at` represents the consumed open/close and never precedes
`decision_at`.

## 20. Leakage findings

Regression evidence covers future mutation, out-of-order canonical sorting,
full-series-normalisation absence, target-derived-field isolation,
future-aware-fill absence, and decision timestamp bounds. No fitting,
normalisation, backward-fill, forward-fill, training, wall-clock, external
provider, or cross-run model-cache path exists.

## 21. Execution-assumption findings

`next_open` records the next observation's open timestamp and price.
`next_close` records the next observation's period end and close.
`same_close` records the decision observation's period end and close.
There is no order book, fill-quality, partial-fill, venue, settlement, stop, or
take-profit claim.

## 22. Fee findings

Zero, fixed, and bounded percentage models are explicit and validated.
Negative/excessive fees fail validation; fees are applied deterministically
with Decimal arithmetic and retained in events and fingerprints.

## 23. Slippage findings

Zero and bounded basis-point slippage are explicit. Negative and excessive
values fail validation. Entry/exit calculations and result fingerprints are
deterministic; there is no broker-specific claim.

## 24. Position-sizing findings

Fixed simulated cash, bounded cash percentage, and fixed quantity are typed.
The engine is long-only and has no leverage, margin, borrowing, shorting,
derivatives, or AI-controlled sizing. Insufficient cash prevents entry and
cash/position invariants are enforced.

## 25. Engine findings

The engine orders observations canonically, checks lookback, evaluates a typed
rule, applies explicit execution/fee/slippage/sizing assumptions, emits
deterministic events and equity points, and calculates bounded Decimal
analytics. It contains no network, AI, persistence, or portfolio-state
mutation.

## 26. Result-calculation findings

An independent reconstruction matched event sequence/types, equity totals,
P&L, return, drawdown, volatility, turnover, benchmark result, and the wrapped
result checksum. Correction 003 added benchmark and data-quality evidence to
the persisted checksum.

## 27. Equity and drawdown findings

Equity is cash plus marked long-only position value at each observation.
Drawdown uses the running peak, not future peaks. Equity history is
append-only. Reconstruction matched the stored series and maximum drawdown.

## 28. Benchmark findings

Benchmark comparison is descriptive and uses the configured stored series.
It does not rank, recommend, predict, or silently convert currency. Benchmark
return is now checksum-covered. Calendar and corporate-action completeness
remain documented limitations.

## 29. Reproducibility findings

Identical immutable configuration and stored observations reproduce identical
events, equity, results, and checksums. Changed rule/configuration or source
data changes the corresponding fingerprint. All material observation fields
are now fingerprinted.

## 30. Idempotency findings

Identical version/run/explanation retries return one effect. Reusing an
idempotency key with a conflicting payload returns 409. Uniqueness constraints
and locked service transactions provide the authoritative guarantee.

## 31. Concurrency findings

Real PostgreSQL tests use separate sessions and independently verify:

- identical run requests create exactly one run;
- concurrent execution creates one event set and one result;
- conflicting idempotency reuse yields one success and one 409;
- explanation generation creates one explanation and one audit effect;
- archive-versus-run and archive-versus-version races fail closed;
- no duplicate result, event sequence, explanation, or lifecycle audit appears.

The focused integration suite passed twice consecutively: `11 passed` in
6.60 seconds and `11 passed` in 6.58 seconds.

## 32. Append-only findings

Direct PostgreSQL attempts to update/delete published versions, events,
equity, results, explanations, and audit records were rejected with
`research history is append-only`. Completed run update/delete attempts were
rejected with `completed backtest runs are immutable`.

## 33. Atomicity findings

Unavailable-data execution now rolls back the requested run and audit and
leaves no false result. Concurrency tests also check orphan/duplicate evidence.
The implementation does not yet contain a comprehensive injected-failure
matrix for every enumerated persistence boundary; see M5-AUD-007.

## 34. Authorisation findings

Research permissions are defined centrally. Authenticated active identity,
tenant, and membership are required. Viewer mutation, suspended/deactivated
identity, foreign resources, and client-supplied role/permission claims are
denied or concealed. The runtime unauthenticated strategies request returned 401.

## 35. Tenant-isolation findings

API/service tests cover foreign strategies, runs, results, explanations, and
guessed identifiers. Composite tenant constraints prevent cross-tenant child
linkage. The remaining same-tenant strategy/version parent mismatch is a
database-integrity gap, not a reproduced cross-tenant disclosure.

## 36. Schema and mass-assignment findings

Strict Pydantic schemas reject protected run, result, event, provider,
explanation, audit, executable, and ownership fields. New parameterised tests
cover all four request families and nested rules. The eight-table schema,
uniqueness, checks, indexes, and append-only triggers were inspected.

## 37. Explainable-AI findings

The explanation implementation is optional, local, deterministic, versioned,
non-networked, non-executing, provenance-aware, and non-advisory. It cannot
alter strategy, run, event, result, or portfolio state and has no tool or
external-provider interface. Concurrent generation is serialized.

## 38. Advisory-language findings

Relevant live/advice terms occur in prohibitions, test inputs, or explanatory
limitations. Research screens display historical-simulation/non-advice
language and no broker, bank, live-deployment, or trade control was found.
Static buttons still risk implying functionality that does not exist; this is
included in M5-AUD-004.

## 39. Frontend findings

The route set exists and builds responsively with dark/light styles and the
required disclaimer. Strategy list/create has genuine API interaction.
Version creation, typed rule editing, backtest configuration/execution,
history, event/equity/drawdown/benchmark/data-quality views, explanations,
audit, and comparison are predominantly static panels or `type="button"`
controls with no authoritative API action. Permission-aware and lifecycle
states are consequently not demonstrated end to end.

## 40. Accessibility findings

Basic semantic headings, labels, tables, and responsive styling exist.
Formal keyboard, focus, error-summary, chart-alternative, reduced-motion, and
WCAG browser automation is absent for the static research workflows. No
formal accessibility conformance can be claimed.

## 41. Observability findings

Metrics and structured logging infrastructure is bounded and avoids
high-cardinality research identifiers. However, declared
`STRATEGY_OPERATIONS` and `BACKTEST_DURATION` metrics are not instrumented,
and bounded failure, replay, conflict, invariant, data-quality, and explanation
metrics are incomplete. See M5-AUD-008.

## 42. Migration findings

Migration `20260728_0007` upgrades from `20260728_0006`, creates the research
schema, fixed-precision columns, constraints, indexes, and triggers, and
downgrades cleanly. Evidence:

- fresh PostgreSQL 16.9 upgrade through every revision: passed;
- current revision: `20260728_0007 (head)`;
- downgrade to 0006 and re-upgrade to head: passed;
- `alembic check`: `No new upgrade operations detected`;
- development Compose database remained at head.

## 43. Reconstruction findings

A new real-PostgreSQL test reconstructs a representative completed run using
its immutable version, run assumptions, and ordered observations. Event types
and sequence, equity, P&L, return, drawdown, volatility, turnover, benchmark,
and checksum match stored evidence.

## 44. Security-test findings

Authentication, tenant concealment, schema rejection, invalid rules and
assumptions, future/leakage manipulation, ordering, unavailable data,
concurrency, append-only mutation, explanation boundaries, and unauthenticated
runtime access were exercised. No broker, payment, custody, wallet, order,
external AI, or execution path was introduced by Milestone 5.

## 45. Quality-gate results

| Gate                             | Final result                           |
| -------------------------------- | -------------------------------------- |
| `pnpm install --frozen-lockfile` | Passed                                 |
| Prettier                         | Passed                                 |
| ESLint                           | Passed                                 |
| TypeScript                       | Passed                                 |
| JavaScript/package tests         | Passed                                 |
| Next.js/package build            | Passed                                 |
| Ruff format/check                | Passed                                 |
| strict mypy                      | Passed, 63 source files                |
| Python tests and coverage        | Passed                                 |
| `pip check`                      | No broken requirements                 |
| `pip_audit`                      | No known vulnerabilities               |
| Governed Node audits             | Passed                                 |
| Raw Node audits                  | One governed High development advisory |
| `git diff --check`               | Passed                                 |

## 46. Coverage result

`111 passed, 6 warnings`; total coverage **85.27%** (4,765 statements, 702
missed), exceeding the required 80%.

## 47. JavaScript/package test result

**29 tests passed** across seven files: web 26, UI 2, shared 1. The count is
unchanged from the implementation report.

## 48. Dependency findings

- `GHSA-mh99-v99m-4gvg` / `CVE-2026-14257`, High,
  `brace-expansion <=5.0.7`, is reachable through ESLint/minimatch development
  tooling. Raw `pnpm audit` reports it; governed audits pass under the
  development-only exception expiring 2026-10-27. ESLint is absent from the
  web runtime image.
- `CVE-2026-12087` remains inherited through Perl in the official Python
  3.12.13 slim base. Perl exists at `/usr/bin/perl`, but Atlas starts Uvicorn
  directly and no Atlas code invokes Perl. The documented private-development
  exception remains controlling; production is prohibited.
- Python audit found no known requirement vulnerability. No external AI,
  broker, wallet, execution, technical-analysis, or new mathematical SDK was
  added.

Docker Scout was attempted but required login. In accordance with the audit
rules, no credential was requested, created, or stored.

## 49. Docker results

Compose configuration, image builds, and `up --detach --wait` passed.
PostgreSQL 16.9, Redis 7.4.5, FastAPI, and Next.js were healthy. API runs as
`atlas` UID 1001 and web as `nextjs` UID 1001; both have read-only root
filesystems, `no-new-privileges`, and no mounts. Web/API host binding to
`0.0.0.0` is intentional for local Docker port publication, not production
authorisation.

## 50. Runtime results

| Check                                     | Result |
| ----------------------------------------- | ------ |
| Homepage                                  | 200    |
| `/health/live`                            | 200    |
| `/health/ready`                           | 200    |
| `/metrics`                                | 200    |
| `/openapi.json`                           | 200    |
| Unauthenticated research strategy request | 401    |

Authenticated workflow, role, tenancy, concurrency, data-quality, replay, and
explanation behaviour was exercised through application services/API test
clients against real PostgreSQL using synthetic identities. No production
Clerk or external provider was used.

## 51. Corrective changes

| ID             | Defect and smallest safe correction                                                                                                                            | Files                                              | Verification                                           |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------ |
| M5-AUD-COR-001 | Close-based events were persisted at `period_start`, potentially preceding their decision. Persist next-open at period start and close policies at period end. | `services.py`, integration tests                   | same/next-close timestamp tests; full suite passed     |
| M5-AUD-COR-002 | `UNAVAILABLE` candles could enter simulation and were counted as zero unavailable. Fail atomically before engine execution.                                    | `services.py`, integration tests                   | no run/result/audit after 422; repeatable real-PG test |
| M5-AUD-COR-003 | Data fingerprint omitted material OHLCV/provenance fields and result checksum omitted benchmark/quality. Expand canonical evidence and wrap result checksum.   | `engine.py`, `services.py`, unit/integration tests | field mutation and full reconstruction passed          |
| M5-AUD-COR-004 | New unavailable-data fixture collided on repeated suite execution. Delete only its exact five-row fixture window before reseeding.                             | integration test                                   | integration suite passed twice consecutively           |
| M5-AUD-COR-005 | Protected-field coverage was incomplete. Add strict mass-assignment matrices.                                                                                  | unit tests                                         | 14 research unit tests passed                          |

## 52. Unresolved findings

| ID         | Severity | Finding                                                                                                                            | Risk and recommendation                                                                                                                            | State |
| ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| M5-AUD-004 | High     | Most research frontend workflows are static shells                                                                                 | Materially unsupported acceptance claim; implement API-backed, permission-aware workflows and E2E evidence on a new authorised remediation branch  | Open  |
| M5-AUD-005 | Medium   | Run/version/strategy parent coherence is not fully enforced by PostgreSQL; `current_version_id` and some audit references lack FKs | Same-tenant malformed linkage can bypass service invariants; add non-cyclic composite integrity or validated constraint design and migration tests | Open  |
| M5-AUD-006 | Medium   | Declared `skip_event`/`skip_observation` missing-data policies and calendar-gap counts are not implemented                         | UI/configuration can imply unsupported handling; implement deterministically or remove from accepted schemas/UI and document                       | Open  |
| M5-AUD-007 | Medium   | Atomic failure injection does not cover every enumerated persistence boundary                                                      | Partial-state regressions may escape current tests; add transaction fault hooks/tests without weakening rollback                                   | Open  |
| M5-AUD-008 | Medium   | Research metrics are declared but largely unused                                                                                   | Failures, conflicts, quality outcomes, and invariant breaches lack operational evidence; instrument bounded labels                                 | Open  |
| M5-AUD-009 | Low      | Research accessibility has no browser/WCAG automation                                                                              | Accessibility regressions may be missed; add keyboard/focus/semantic automated evidence when workflows are implemented                             | Open  |

## 53. Known limitations

Research is historical simulation only. Fixtures are local simulated data;
calendar completeness, corporate actions, FX conversion, tax, venue fills,
liquidity, partial fills, live data, prediction, suitability, optimisation,
arbitrary rules, and external generative AI are not implemented or authorised.
The warning set includes six Starlette deprecations.

## 54. Production blockers

Production is blocked by this audit failure, the open frontend and integrity
findings, development-only security exceptions, absent independent production
security review, simulated-only data, incomplete accessibility/observability,
and the standing governance prohibition. Nothing in this report authorises
public access, advice, execution, custody, payments, or customer funds.

## 55. Final decision

| Decision                          | Result                                                                 |
| --------------------------------- | ---------------------------------------------------------------------- |
| Milestone 5 technical status      | **FAIL**                                                               |
| Private-development permission    | Existing governance remains, but Milestone 5 acceptance is not granted |
| Production readiness              | **PROHIBITED / NOT READY**                                             |
| External-AI permission            | **PROHIBITED**                                                         |
| Live-trading/execution permission | **PROHIBITED**                                                         |
| Real-money/advice permission      | **PROHIBITED**                                                         |

## 56. Milestone 6 decision

**Milestone 6 may not begin.** Resolve and independently re-audit the Milestone
5 release-blocking finding under explicit governance before seeking approval.

## 57. Appendix — exact commands and failed-command record

Successful final commands included:

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
$env:ATLAS_TEST_DATABASE_URL = 'postgresql+asyncpg://atlas_audit:***@127.0.0.1:55450/atlas_audit'
.\.venv312\Scripts\python.exe -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term --cov-fail-under=80
.\.venv312\Scripts\python.exe -m pip check
.\.venv312\Scripts\python.exe -m pip_audit -r apps/api/requirements.txt

pnpm audit:governed
pnpm audit:governed:prod
pnpm audit --prod
pnpm audit

.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini current
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini downgrade 20260728_0006
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini upgrade head
.\.venv312\Scripts\python.exe -m alembic -c packages/database/alembic.ini check

docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose ps
git diff --check
```

Failed or non-passing commands:

1. The first broad static search used Bash brace syntax in PowerShell.
   PowerShell did not expand it as intended. The search was rerun with
   PowerShell-compatible `rg` arguments and completed. Final state: resolved.
2. A combined Ruff/mypy/focused-pytest command exceeded its 184-second tool
   timeout before buffered test output was returned. Each gate was rerun
   separately and passed. Final state: resolved.
3. The first focused integration rerun used
   `ATLAS_TEST_DATABASE_URL=...localhost:5433...`; all 11 tests failed with
   `ConnectionRefusedError [WinError 1225]`. Compose PostgreSQL was internal
   only. An isolated PostgreSQL 16.9 container was bound to
   `127.0.0.1:55450`, migrated to head, and the rerun passed 11/11. Final
   state: resolved environmental error.
4. The first migration attempt set `DATABASE_URL` rather than the configured
   `ATLAS_DATABASE_URL`; Alembic used the default `atlas` account and failed
   authentication. The prefixed variable was set and fresh migration passed.
   Final state: resolved environmental error.
5. The first full Python suite against the reused audit database passed 110
   tests but the new unavailable-data test collided with its own prior candle
   fixtures on `uq_candle_observation`. Correction M5-AUD-COR-004 made the
   fixture repeatable. The integration suite passed twice and the full suite
   then passed 111/111 at 85.27%. Final state: resolved.
6. Raw `pnpm audit` and `pnpm audit --prod` report one High
   `brace-expansion` advisory. This is not corrected; it is governed for
   private development only through 2026-10-27. Production remains
   prohibited.
7. Docker Scout returned `Log in with your Docker ID or email address to use
docker scout`. No authentication was already available, so the scan was
   stopped without requesting or storing credentials. Final state: not run,
   governed evidence retained.
