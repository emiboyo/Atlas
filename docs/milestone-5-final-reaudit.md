# Atlas AI Milestone 5 Final Independent Re-audit

## 1. Audit title

Atlas AI Milestone 5 Final Independent Re-audit.

## 2. Date

2026-07-31.

## 3. Repository

`C:\Dev\Atlas`.

## 4. Branch

`chore/milestone-5-final-reaudit`.

## 5. Commit audited

`6671e7ac2769248b64c913a100583616ce8f2055`, including final evidence
implementation `8628cd4`.

## 6. Auditor role

Final independent security, PostgreSQL-integrity, transaction-safety,
quantitative-system, observability, accessibility, supply-chain, and
release-gate reviewer.

## 7. Executive conclusion

All Milestone 5 technical findings are resolved. The final evidence change is
limited to tests and documentation. Database parent coherence, fail-closed
migrations, atomic rollback, retry-after-fault idempotency, bounded metrics,
API-backed research UI, accessibility automation, deterministic research
integrity, tenant isolation, migrations, builds, containers, and runtime gates
pass independently.

## 8. Final status

> **CONDITIONAL PASS — technically accepted for private development only.**
>
> Existing governed development dependency exceptions and documented
> development limitations remain. Production, public access, financial
> execution, external production AI, advice, real money, and Milestone 6 are
> prohibited.

## 9. Governance context

Risk owner Adebayo Olaegbe; review 2026-08-27; exception expiry 2026-10-27.
This audit changes no date, exception, or permission.

## 10. Scope

Findings M5-AUD-004 through M5-AUD-009 and M5-RF-001 through M5-RF-002,
including code, migrations, PostgreSQL, frontend, tests, CI, dependencies,
Docker, and runtime.

## 11. Out-of-scope items

No deployment, production credential, public access, live provider, external
AI, trading, execution, brokerage, payment, custody, advice, real-money,
Terraform apply, or Milestone 6 work occurred.

## 12. Finding history

| Finding    | Final decision |
| ---------- | -------------- |
| M5-AUD-004 | RESOLVED       |
| M5-AUD-005 | RESOLVED       |
| M5-AUD-006 | RESOLVED       |
| M5-AUD-007 | RESOLVED       |
| M5-AUD-008 | RESOLVED       |
| M5-AUD-009 | RESOLVED       |
| M5-RF-001  | RESOLVED       |
| M5-RF-002  | RESOLVED       |

## 13. Final claim-to-evidence matrix

| Claim                    | Independent evidence                                  | Conclusion |
| ------------------------ | ----------------------------------------------------- | ---------- |
| API-backed research UI   | component/API review, 49 web tests, route build       | supported  |
| Server permissions       | permission endpoints and fail-closed frontend tests   | supported  |
| Parent/audit coherence   | migration, ORM, catalog, SQLSTATE tests               | supported  |
| RESTRICT/append-only     | catalog delete action and trigger rejection           | supported  |
| Only `fail_run`          | Pydantic, OpenAPI const, DB check, negative tests     | supported  |
| Malformed 0007 upgrades  | eight disposable PostgreSQL cases                     | supported  |
| Atomic rollback          | 15 boundary classes, separate sessions                | supported  |
| Retry after fault        | version, early/late run, explanation; repeated        | supported  |
| Bounded metrics          | six families, bounded labels, replay regression       | supported  |
| Accessibility isolation  | Vite-only shim, production image review               | supported  |
| Meaningful browser tests | 32 Chromium desktop/mobile tests and negative control | supported  |
| Deterministic integrity  | engine/reconstruction/leakage suites                  | supported  |
| No prohibited path       | source/dependency/runtime review                      | supported  |
| Migration/runtime        | 0008, clean migrations, healthy stack                 | supported  |

## 14. Change-scope review

`d0170a6..6671e7a` changes only
`apps/api/tests/test_research_integration.py`,
`apps/api/tests/test_research_migration_evidence.py`, and
`docs/milestone-5-final-audit-evidence-remediation.md`. Migration 0008,
production code, governance, frontend, infrastructure, dependencies, and CI
are unchanged.

## 15. Frontend final result

Research overview, strategies, immutable versions, backtests, run evidence,
analytics, explanations, audit, and comparison use dynamic IDs and API calls.
Server-derived permissions gate mutations; malformed permission responses fail
closed. No placeholder href, clickable div, dead trade/advice control, or
prohibited action was found. Required disclaimers remain.

## 16. M5-AUD-004 decision

**RESOLVED.**

## 17. Database-integrity result

Composite version/run/audit parents enforce tenant and strategy coherence.
The nullable current-version FK is deferrable and initially deferred. Direct
same/cross-tenant violations return `23503`; run-audit-without-version returns
`23514`; immutable deletion triggers return `23000`. Rollback and subsequent
`SELECT 1` succeed. Valid staged creation commits.

## 18. M5-AUD-005 decision

**RESOLVED.**

## 19. Malformed-upgrade matrix

Eight isolated databases at 0007 cover same/cross-tenant run mismatch,
same/cross-tenant current-version mismatch, audit version mismatch, audit run
mismatch, run audit without version, and `skip_event`. Every upgrade fails in
the expected category, stays at 0007, retains identical row snapshots, leaves
no partial 0008 constraint, remains queryable, and is removed.

## 20. M5-RF-001 decision

**RESOLVED.**

## 21. Missing-data-policy result

Pydantic and OpenAPI permit/default only `fail_run`; the PostgreSQL check
enforces it. Unsupported values fail without coercion. Unavailable data aborts
atomically, missing data is not fabricated, and stale evidence remains marked.

## 22. M5-AUD-006 decision

**RESOLVED.**

## 23. Atomicity result

Real PostgreSQL tests cover nine backtest boundaries plus version,
explanation, archive, and optimistic-update faults. Separate sessions verify
no partial aggregate, child, audit, revision, archive, or poisoned key.
Fault injection is monkeypatch-only and has no production switch.

## 24. Idempotency-after-fault result

Version, early run-flush, late run-commit, and explanation failures roll back.
Identical same-key retry creates exactly one aggregate; replay returns its ID;
changed valid payload returns stable `idempotency_conflict`. Counts are one
version/one audit, one run/one result/one event-equity sequence/three lifecycle
audits, and one explanation/one audit.

## 25. M5-AUD-007 decision

**RESOLVED.**

## 26. M5-RF-002 decision

**RESOLVED.**

## 27. Metrics result

Six Prometheus families cover strategy operations, backtests, duration,
conflicts, explanations, and data quality. Labels are bounded operation/outcome
values and contain no identity, name, amount, request, error text, prompt, or
content. Version replay increments replay without success. `/metrics` returns
200 and exposes the families.

## 28. M5-AUD-008 decision

**RESOLVED.**

## 29. Accessibility-harness security

Clerk and Link shims are Vite E2E aliases only. No production activation
variable, fixture identity, Clerk secret, test shim, or browser binary was
found in production routes/assets. Playwright/axe are development-only.

## 30. Accessibility result

Thirteen representative routes plus keyboard and validation behavior pass in
Desktop Chrome and Pixel 7. Tests enforce headings, disclaimer, semantics,
focus, overflow, axe serious/critical absence, and navigation. The negative
control detects unnamed-button and unlabelled-input defects.

## 31. M5-AUD-009 decision

**RESOLVED.**

## 32. Quantitative-integrity regression

Decimal determinism, look-ahead/leakage prevention, fingerprints/checksums,
explicit assumptions, long-only/non-negative invariants, append-only evidence,
deterministic replay, neutral benchmark, and local deterministic explanations
pass. No external AI, currency-conversion, portfolio-mutation, broker, or order
path exists within the Milestone 5 research runtime.

## 33. Tenant/authorisation regression

Authentication, active tenancy, membership, central permissions, foreign
resource concealment, viewer denial, client-claim rejection, composite tenant
FKs, and bounded explanation/audit permissions remain tested and intact.

## 34. Python test result

139 passed; 0 failed, skipped, or xfailed; 6 Starlette deprecation warnings.
Focused evidence passed twice: 33/33 in 62.41 seconds and 33/33 in 61.26
seconds. Ruff passes; mypy reports no issues in 63 source files; pip check and
pip-audit pass.

## 35. Coverage result

86.05% over 4,853 statements; required threshold is 80%.

## 36. Package test result

52 passed across 7 files: web 49/5 files, UI 2/1, shared 1/1. Existing React
`act` warnings are development-test warnings.

## 37. Browser test result

32 passed: 16 Chromium desktop and 16 Pixel 7, zero failures/retries.

## 38. Migration result

Current 0008, downgrade to 0007, re-upgrade to 0008, Alembic check, and fresh
all-revision upgrade pass. The disposable database was removed; the normal
database remains `20260730_0008 (head)`.

## 39. CI result

CI retains frozen dependency installation, formatting, lint, typecheck,
package tests, deterministic Chromium installation, accessibility, build,
Python/PostgreSQL tests, coverage ≥80%, migrations, Alembic check, and governed
audits. No production Clerk secret or live provider is required.

## 40. Dependency findings

Raw development `pnpm audit` reports high
GHSA-mh99-v99m-4gvg/CVE-2026-14257 through ESLint/minimatch/brace-expansion.
Governed and production audits pass; the development exception expires
2026-10-27. CVE-2026-12087 remains inherited from the Python base image under
its existing development-only exception. Python audit found no known
vulnerability. No prohibited SDK was added.

## 41. Docker result

Images build. PostgreSQL, Redis, API, and web are healthy. API `atlas` and web
`nextjs` users are non-root; both roots are read-only with
`no-new-privileges` and zero host bind mounts. No E2E route or prohibited
process exists.

## 42. Runtime result

Homepage, liveness, readiness, metrics, and OpenAPI return 200. Protected
research API returns 401 unauthenticated. OpenAPI exposes only `fail_run`.
Migration is 0008 and no sensitive test marker is exposed.

## 43. Security regression review

Search results for fake/synthetic identities, unsupported policies, financial
terms, and external integrations are confined to tests, fixtures,
documentation, prohibitions, or rejected inputs. No production bypass or
prohibited runtime capability was found.

## 44. Audit corrections

No correction was required on the final re-audit branch.

## 45. Unresolved findings

No unresolved Milestone 5 technical finding remains.

## 46. Accepted limitations

Existing governed dependency exceptions; Chromium-only automated browser
coverage; no physical-device/screen-reader conformance claim; framework
deprecation and React test warnings. These are private-development limitations.

## 47. Production blockers

Governance prohibition, dependency exceptions, independent production
security review, operational/regulatory controls, and production-readiness
work remain blockers.

## 48. Final Milestone 5 technical decision

**Technically accepted for private development.**

## 49. Private-development decision

**Permitted within ADR 0014 and existing exception dates.**

## 50. Production-readiness decision

**Not production ready; production and public access are prohibited.**

## 51. External-AI decision

**External production AI is prohibited.**

## 52. Live-trading/execution decision

**Live trading, brokerage, routing, and execution are prohibited.**

## 53. Advice/real-money decision

**Advice, recommendations, suitability, real money, and customer funds are
prohibited.**

## 54. Milestone 6 decision

**Milestone 6 may not begin without separate explicit governance approval.**

## 55. Exact command appendix

Executed gates included:

```powershell
git branch --show-current
git status
git log --oneline --graph --decorate -20
git diff --check
git rev-parse HEAD
git ls-files | findstr /I ".env"

pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm test:a11y
pnpm build
pnpm audit:governed
pnpm audit:governed:prod
pnpm audit --prod
pnpm audit

python -m pytest apps/api/tests/test_research_migration_evidence.py `
  apps/api/tests/test_research_integration.py -q
python -m pytest --cov=apps.api.src `
  --cov=packages.database.atlas_database `
  --cov-report=term --cov-fail-under=80
python -m ruff format --check apps packages/database
python -m ruff check apps packages/database
python -m mypy apps/api/src packages/database/atlas_database
python -m pip check
python -m pip_audit -r apps/api/requirements.txt

docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose ps
docker compose exec -T api alembic -c packages/database/alembic.ini current
docker compose exec -T api alembic -c packages/database/alembic.ini downgrade 20260728_0007
docker compose exec -T api alembic -c packages/database/alembic.ini upgrade head
docker compose exec -T api alembic -c packages/database/alembic.ini check
```

Failed command: raw `pnpm audit` returned exit 1 for the governed
brace-expansion development advisory. Root cause is the documented
ESLint/minimatch development chain. No unsafe upgrade was forced.
`pnpm audit:governed`, `pnpm audit:governed:prod`, and `pnpm audit --prod`
passed. Final state: governed private-development exception active; production
prohibited.

No commit, merge, deployment, governance change, or Milestone 6 work was
performed.
