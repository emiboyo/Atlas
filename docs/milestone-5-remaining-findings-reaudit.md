# Milestone 5 Remaining Findings Independent Re-audit

## 1. Audit title

Milestone 5 Remaining Findings Independent Re-audit — M5-AUD-005 through
M5-AUD-009.

## 2. Date

2026-07-30.

## 3. Repository

`C:\Dev\Atlas`.

## 4. Branch

`chore/milestone-5-remaining-findings-reaudit`.

## 5. Commit audited

Baseline `189bd7f6c651e6e0b5562d7eab071dd56d8125f3`, with the narrow uncommitted
re-audit corrections listed in section 48.

## 6. Relevant remediation commits

`6b5d69c`, `33c5347`, and merge `189bd7f` are present.

## 7. Auditor role

Independent PostgreSQL-integrity, transaction-safety, observability,
accessibility, security, and release-gate reviewer.

## 8. Executive conclusion

The database parent constraints, single missing-data policy, rollback matrix,
bounded metrics, isolated browser harness, build, and runtime are materially
improved and passed the evidence that was executed. Two acceptance claims are
not yet independently complete: controlled malformed pre-0008 upgrades were
not exercised, and the injected-fault suite does not retry version, run, and
explanation operations with identical and conflicting payloads after rollback.

## 9. Final status

> **FAIL**
>
> M5-AUD-007 remains partially resolved and the pre-0008 malformed-data claims
> lack required execution evidence. Under the mandated status rules, a
> materially unsupported acceptance claim prevents PASS or CONDITIONAL PASS.

## 10. Governance context

Risk owner: Adebayo Olaegbe. Review: 2026-08-27. Exception expiry:
2026-10-27. Private development and audit are permitted. Production, public
access, external production AI, trading, execution, advice, real money, and
Milestone 6 remain prohibited.

## 11. Scope

Only M5-AUD-005 through M5-AUD-009, their implementation, tests, migrations,
CI, dependencies, containers, and runtime evidence were reviewed.

## 12. Out-of-scope work

No deployment, production credential, live provider, external AI, broker,
payment, custody, execution, Terraform apply, or Milestone 6 work occurred.

## 13. Baseline findings

| Finding    | Decision                                |
| ---------- | --------------------------------------- |
| M5-AUD-005 | PARTIALLY RESOLVED                      |
| M5-AUD-006 | RESOLVED                                |
| M5-AUD-007 | PARTIALLY RESOLVED                      |
| M5-AUD-008 | RESOLVED after correction M5-RF-COR-001 |
| M5-AUD-009 | RESOLVED after correction M5-RF-COR-002 |

## 14. Claim-to-evidence matrix

| Claim                        | Code/migration/metadata                    | PostgreSQL/test/runtime/CI evidence                                               | Discrepancy                                                 | Conclusion                            |
| ---------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------- |
| Head 0008                    | revision/down-revision inspected           | current, downgrade/re-upgrade, fresh upgrade pass                                 | none                                                        | supported                             |
| Composite parent identity    | migration and ORM inspected                | catalog shows both unique constraints and three composite FKs                     | malformed pre-0008 fixtures not run                         | partially supported                   |
| Current-version coherence    | deferred composite FK                      | catalog: deferrable and initially deferred                                        | malformed pre-0008 fixture not run                          | partially supported                   |
| Audit coherence and RESTRICT | composite FKs inspected                    | catalog and focused PostgreSQL test pass                                          | all requested malformed/delete cases not directly attempted | partially supported                   |
| Only `fail_run`              | Literal, model check, service inspected    | OpenAPI const/default; API/schema and direct INSERT regression pass               | none                                                        | supported                             |
| Atomic rollback              | test-only monkeypatch boundaries inspected | 22 focused PostgreSQL tests passed twice                                          | no same-key retry after injected fault                      | partially supported                   |
| Six bounded metric families  | metrics and call sites inspected           | registry and `/metrics` expose all six                                            | version replay was counted as success                       | corrected                             |
| Browser isolation            | Vite-only aliases and CI inspected         | production build/image search found no shim, fixture UUID, key, or browser binary | no negative control                                         | corrected                             |
| 30 browser tests             | Playwright suite                           | baseline 30 passed                                                                | correction increases final total to 32                      | superseded                            |
| 52 package tests             | workspace suites                           | 49 web + 2 UI + 1 shared, 7 files                                                 | React `act` warnings                                        | supported with warnings               |
| 127 Python tests / 85.55%    | suite                                      | 127 passed, 6 warnings, **85.49%**                                                | reported percentage did not reproduce                       | total supported; percentage corrected |
| Healthy Docker/runtime       | Compose/Docker reviewed                    | four healthy services and endpoint checks                                         | governed advisories remain                                  | supported for private development     |

## 15. Remediation diff review

The `1512bbd..189bd7f` diff is confined to the database-integrity migration and
metadata, research schema/service/metrics/tests, isolated browser harness,
research UI accessibility changes, CI/package configuration, and
documentation. Migration 0007 is unchanged. Playwright and axe are
development dependencies. No financial connectivity, live provider,
production auth bypass, or Milestone 6 code was found.

## 16. M5-AUD-005 decision

**PARTIALLY RESOLVED.** Database-enforced same-parent constraints are present
and the same-tenant run/version mismatch is rejected. The exhaustive direct
attempt matrix and controlled malformed pre-0008 upgrade matrix required by
this re-audit were not fully implemented.

## 17. Parent-coherence design review

Versions have `(tenant_id, strategy_id, id)` identity. Runs reference that
identity and expose `(tenant_id, strategy_id, strategy_version_id, id)` for
audit linkage. `current_version_id` is nullable, composite, deferred, and
initially deferred, avoiding an insertion cycle. Delete action is RESTRICT.
ORM metadata expresses the same relationships.

## 18. Direct PostgreSQL evidence

`test_postgresql_rejects_malformed_research_parents_and_policy` rejects a
same-tenant wrong-strategy run/version link, a wrong-strategy current version,
and `skip_event`, with a reusable session after rollback. Catalog inspection
confirmed:

- `fk_backtest_runs_version_parent`;
- `fk_research_strategy_current_version_parent` (deferred);
- `fk_research_audit_version_parent`;
- `fk_research_audit_run_parent`;
- both parent identity unique constraints.

The existing test does not record exact SQLSTATE/constraint names and does not
directly attempt every cross-tenant, malformed-audit, and delete case required
by the mandate. No remaining malformed relationship was demonstrated, but
the evidence is incomplete.

## 19. Migration data-validation evidence

Clean development downgrade 0008→0007 and re-upgrade passed. A disposable
empty database upgraded through all revisions to 0008 and was removed.
`alembic check` reported no new operations. Migration SQL fails before DDL for
malformed runs, current versions, audit parents, and unsupported policies.
Controlled populated 0007 databases for each malformed condition were not
executed; this is an open evidence finding.

## 20. M5-AUD-006 decision

**RESOLVED.**

## 21. Schema/OpenAPI policy evidence

`BacktestCreate.missing_data_policy` is `Literal["fail_run"]` with default
`fail_run`. OpenAPI exposes `type: string`, `const: fail_run`, and the same
default. Unit tests reject `skip_event`, `skip_observation`, and arbitrary
values. No unsupported frontend choice exists.

## 22. Database-policy evidence

PostgreSQL has a check requiring `missing_data_policy = 'fail_run'`. Direct
`skip_event` insertion fails. The engine fails unavailable data atomically,
does not fill missing observations from future data, and retains stale status
in result quality evidence.

## 23. M5-AUD-007 decision

**PARTIALLY RESOLVED.**

## 24. Backtest atomicity evidence

Nine persistence boundaries are injected twice against PostgreSQL: after run
flush, requested audit, started audit, first event, equity, before result,
after result, before completed audit, and final commit. Separate sessions
verify zero run and audit effects and a usable database. The focused file
passed 22 tests twice (4.98 s and 5.08 s).

## 25. Version/explanation/archive/update atomicity

PostgreSQL tests inject after-version-flush, after-explanation-flush,
before-explanation-audit, explanation commit, archive commit, and optimistic
update commit. Separate sessions verify no partial version/explanation and no
archive or revision change.

## 26. Idempotency-after-fault evidence

Concurrency and ordinary replay tests prove one effect and stable conflicts.
The injected-fault tests prove rollback, but do not then reuse each failed
key with identical and conflicting payloads for version, run, and explanation.
This missing matrix keeps M5-AUD-007 open.

## 27. M5-AUD-008 decision

**RESOLVED after M5-RF-COR-001.**

## 28. Metrics inventory

| Family                                     | Type      | Labels             | Meaning                             |
| ------------------------------------------ | --------- | ------------------ | ----------------------------------- |
| `atlas_research_strategy_operations_total` | counter   | operation, outcome | bounded strategy lifecycle outcomes |
| `atlas_research_backtests_total`           | counter   | outcome            | request/execution outcomes          |
| `atlas_research_backtest_duration_seconds` | histogram | none               | request duration                    |
| `atlas_research_conflicts_total`           | counter   | operation          | bounded conflict source             |
| `atlas_research_explanations_total`        | counter   | outcome            | explanation outcomes                |
| `atlas_research_data_quality_total`        | counter   | outcome            | bounded quality result              |

Histogram buckets are `0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30`,
plus Prometheus `+Inf`.

## 29. Metric cardinality review

No tenant, user, strategy, version, run, explanation, request, name, listing,
currency, amount, date, exception, prompt, or content label exists. Labels
are fixed operation/outcome classifications only.

## 30. Metric exactly-once evidence

Review found that `create_version` replay returned through the generic
strategy decorator and incremented `success`. M5-RF-COR-001 adds a
request-context-local bounded replay outcome and a regression proving replay
increments once without incrementing success. Backtest and explanation
services emit explicit completed/generated/replay/conflict outcomes only at
their documented boundaries.

## 31. Runtime metric evidence

`GET /metrics` returned 200 and exposed all six families and finite histogram
buckets. No object identity or content was present in metric labels.

## 32. M5-AUD-009 decision

**RESOLVED after M5-RF-COR-002.**

## 33. Accessibility harness security

The Clerk and Next Link shims are Vite aliases confined to `apps/web/e2e`.
Production code has no shim import or activation environment variable.
Production image search found no shim name, fixture UUID, Clerk test/live
secret, or Playwright/axe browser binary. Generic occurrences of the word
“synthetic” were Next.js framework internals, not Atlas identities or bypasses.

## 34. Route/browser coverage

Thirteen representative research routes cover overview, strategies,
creation/detail/version creation, backtests, run detail, events, analytics,
explanations, audit, and comparison. Tests assert one `h1`, disclaimer,
absence of prohibited controls/clickable divs, no page overflow, focus
visibility, and no serious/critical axe result.

## 35. Desktop/mobile accessibility evidence

Chromium Desktop Chrome and Pixel 7 projects both pass all route, keyboard
link, keyboard button/validation-focus, and negative-control checks.

## 36. Accessibility negative control

M5-RF-COR-002 creates an isolated in-memory page containing an unnamed button
and unlabelled input. Axe reports `button-name` and `label`; both desktop and
mobile negative controls pass by proving those defects are detected.

## 37. Accessibility limitations

This is not full WCAG conformance. Firefox, WebKit, physical devices,
screen-reader/manual assistive-technology testing, and broad human UX review
remain private-development limitations.

## 38. CI findings

CI installs pinned pnpm/Node/Python, installs Chromium with system
dependencies, runs accessibility with failure propagation, retains format,
lint, type, package, build, governed audit, PostgreSQL migration, 80% coverage,
and Alembic checks. No Clerk secret or live provider is required.

## 39. Python tests and coverage

Baseline full run: 127 passed at 85.49%. Final post-correction run: 128 passed,
0 failed/skipped/xfailed, 6 deprecation warnings, 85.47% across 4,853
statements. Ruff format/check, mypy (63 source files), pip check, and pip-audit
pass.

## 40. JavaScript/package tests

52 passed across 7 files: web 49/5, UI 2/1, shared 1/1. React `act` warnings in
research unit tests are non-failing test-harness warnings.

## 41. Browser test result

Baseline 30/30 passed. Final corrected focused run: 32/32, 16 per Chromium
desktop/mobile project, zero failures/retries. Trace retention is configured
for failure; none was produced.

## 42. Lint/typecheck/build result

Final Prettier, ESLint, TypeScript, package-test, Next.js build, Ruff, mypy,
browser, and `git diff --check` gates pass. The Next.js manifest contains all
research routes. A Ruff import-order failure introduced during correction was
fixed and its final rerun passed.

## 43. Migration result

Current 0008, downgrade to 0007, re-upgrade to head, Alembic check, and fresh
all-revisions database pass. Append-only triggers remain on versions, runs,
events, equity, results, explanations, and audit records.

## 44. Dependency findings

`pip-audit` found no Python vulnerability. Governed Node scripts pass.
Raw development audit reports GHSA-mh99-v99m-4gvg / CVE-2026-14257 in the
ESLint/minimatch development chain; the documented exception expires
2026-10-27. Production Node audit passes. The inherited
CVE-2026-12087 base-image exception remains governed and production remains
prohibited. No live-provider SDK was added.

## 45. Docker findings

Images build. PostgreSQL, Redis, API, and web are healthy. API user `atlas`
and web user `nextjs` are non-root; both have read-only roots,
`no-new-privileges`, and zero mounts. No test credential or E2E route was
found in runtime content.

## 46. Runtime findings

Homepage, liveness, readiness, metrics, and OpenAPI return 200. An
unauthenticated research strategy request returns 401. OpenAPI advertises only
`fail_run`. Compose database remains at 0008.

## 47. Security regression review

No production auth bypass, hardcoded production identity/permission, external
AI/network provider, broker/payment/order execution path, arbitrary metric
label, or unsupported missing policy was introduced. Existing deterministic,
tenant, permission, append-only, idempotency, and container controls remain.

## 48. Re-audit corrections

- **M5-RF-COR-001 — Medium, resolved:** version replay was double-classified as
  a new success. Changed research metrics/service and added a regression test.
- **M5-RF-COR-002 — Low, resolved:** no axe negative control. Added an isolated
  browser regression that detects two deliberate violations.

## 49. Unresolved findings

- **M5-RF-001 — Medium, Open:** no executed controlled malformed pre-0008
  upgrade matrix or exact SQLSTATE/constraint evidence for every requested
  parent case.
- **M5-RF-002 — Medium, Open:** no same-key identical/conflicting retry matrix
  after injected rollback for version, run, and explanation.

## 50. Accepted limitations

Browser engines and assistive technologies beyond Chromium desktop/mobile are
not covered. Governed dependency exceptions remain development-only. React
test warnings remain. These do not authorize production.

## 51. Production blockers

Open audit evidence, independent security review, governed advisories,
production credentials/operations controls, and all existing governance
prohibitions block production.

## 52. Overall Milestone 5 impact

Milestone 5 is not technically accepted by this re-audit because M5-AUD-005
and M5-AUD-007 remain partially resolved. Private development remains governed
by ADR 0014; this report grants no new authority.

## 53. Milestone 6 decision

**Milestone 6 may not begin.**

## 54. Exact command appendix

Passed commands included:

```powershell
pnpm install --frozen-lockfile
pnpm --dir apps/web exec playwright install chromium
pnpm test:a11y
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
.\.venv312\Scripts\python.exe -m ruff format --check apps packages/database
.\.venv312\Scripts\python.exe -m ruff check apps packages/database
.\.venv312\Scripts\python.exe -m mypy apps/api/src packages/database/atlas_database
.\.venv312\Scripts\python.exe -m pip check
.\.venv312\Scripts\python.exe -m pip_audit -r apps/api/requirements.txt
docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose exec -T api alembic -c packages/database/alembic.ini downgrade 20260728_0007
docker compose exec -T api alembic -c packages/database/alembic.ini upgrade head
docker compose exec -T api alembic -c packages/database/alembic.ini check
```

The final full PostgreSQL test command used the Compose API image, the source
mount, the existing test dependency volume, Python 3.12, and
`ATLAS_TEST_DATABASE_URL=$ATLAS_DATABASE_URL`; it passed 128 tests at 85.47%.

Failed commands:

1. Combined native Python gate command timed out after 124 seconds without
   returning subprocess output. Root cause: too many environment/audit
   operations were combined under a short tool timeout. Correction: split the
   commands and rerun with 180-second limits. Final state: Ruff, mypy, pip
   check, and pip-audit passed.
2. A Windows `rg` command used Unix-style wildcard arguments
   (`apps/api/tests/test_research*` and migration `*`). Root cause: PowerShell
   passed invalid wildcard paths to ripgrep. Correction: inspect explicit
   files/directories. Final state: source and tests inspected.
3. The first post-correction Ruff check reported import block `I001` in
   `services.py`. Root cause: the new import was not alphabetically placed.
   Correction: `python -m ruff check --fix
apps/api/src/research/services.py`. Focused rerun passed.
4. Raw `pnpm audit` exited 1 for the governed development-only
   brace-expansion advisory. `pnpm audit:governed` and
   `pnpm audit:governed:prod` passed, and `pnpm audit --prod` passed. No forced
   upgrade was made; the exception and production prohibition remain.

No commit, deployment, governance extension, or Milestone 6 work was
performed.
