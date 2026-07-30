# Milestone 5 Remaining Findings Remediation

> **Current status: CONDITIONAL PASS — all five focused technical findings are
> resolved and independently re-auditable. Private-development governance and
> documented security exceptions remain; production is prohibited.**

Date: 2026-07-30

Repository: `C:\Dev\Atlas`

Branch: `fix/milestone-5-remaining-audit-findings`

Baseline: `1512bbd5e2e6d4bd93990bf76cd8678a5c802287`

## Scope and governance boundary

This work addresses only M5-AUD-005 through M5-AUD-009. Risk owner: Adebayo
Olaegbe. Review: 2026-08-27. Expiry: 2026-10-27. Private development only.
Production, public access, execution, external AI, advice, custody, real money,
customer funds, and Milestone 6 remain prohibited.

## Baseline findings and decisions

| Finding                          | Decision             | Evidence                                                           |
| -------------------------------- | -------------------- | ------------------------------------------------------------------ |
| M5-AUD-005 parent coherence      | Resolved technically | Migration 0008, metadata parity, direct PostgreSQL rejection tests |
| M5-AUD-006 missing-data policies | Resolved technically | Request/OpenAPI/database permit only `fail_run`                    |
| M5-AUD-007 fault injection       | Resolved technically | Repeatable real-PostgreSQL boundary matrix                         |
| M5-AUD-008 research metrics      | Resolved technically | Bounded instrumentation, registry tests, `/metrics` scrape         |
| M5-AUD-009 accessibility         | Resolved technically | 12 jsdom scans and 30 Chromium desktop/mobile browser tests pass   |

## M5-AUD-005 remediation and parent-coherence design

Revision `20260730_0008` validates existing data before DDL. It adds:

- unique version identity `(tenant_id, strategy_id, id)`;
- run FK `(tenant_id, strategy_id, strategy_version_id)` to that identity;
- deferred nullable current-version FK for
  `(tenant_id, strategy_id, current_version_id)`;
- unique run parent identity for audit references;
- audit version and run composite FKs plus a run-requires-version check;
- `RESTRICT` deletion throughout, preserving completed evidence.

The current-version constraint is `DEFERRABLE INITIALLY DEFERRED`, so strategy
creation, version insertion, and staged current-version assignment do not form an
unresolvable immediate cycle. SQLAlchemy metadata matches the migration.

### PostgreSQL evidence

The focused PostgreSQL suite directly rejects:

- a same-tenant version from the wrong strategy in a run;
- a current version from another strategy;
- an unsupported persisted missing-data policy.

Each rejected transaction is rolled back and `SELECT 1` then succeeds. Completed
result immutability remains covered. Focused research result: **41 passed**; full
result: **127 passed**.

## M5-AUD-006 remediation and policy decision

`BacktestCreate.missing_data_policy` is now `Literal["fail_run"]` with the safe
default `fail_run`. PostgreSQL enforces
`missing_data_policy = 'fail_run'`. There is no silent conversion. Validation tests
reject `skip_event`, `skip_observation`, and arbitrary strings. The live OpenAPI
property is:

```json
{ "type": "string", "const": "fail_run", "title": "Missing Data Policy", "default": "fail_run" }
```

Unavailable observations still roll back the entire request; no run or audit row is
left and no observation is fabricated. The fingerprint continues to include the
policy through the complete request serialization.

## M5-AUD-007 fault-injection and atomicity evidence

Faults are introduced only by pytest monkeypatching service/session methods. No
production switch or endpoint exists.

The real-PostgreSQL matrix covers, with every backtest boundary repeated twice:

1. after run flush;
2. after requested audit;
3. after started audit;
4. after first event;
5. after an equity point;
6. immediately before result add;
7. after result add;
8. before completed audit;
9. during final commit;
10. after strategy-version flush;
11. after explanation flush;
12. before explanation audit;
13. during explanation commit;
14. during archive commit;
15. during optimistic update commit.

After every failure, verification uses a separate `AsyncSession`. No false completed
run, result, event, equity point, explanation, completed audit, or idempotency effect
remains. The strategy/version source is unchanged and the PostgreSQL session remains
usable after explicit rollback.

## M5-AUD-008 metrics inventory and cardinality review

The authoritative inventory is in [observability.md](observability.md). Strategy
methods use a shared bounded decorator. Backtest and explanation decorators record
request and exception outcomes; success, replay, conflict, disabled, data-quality,
and invariant paths are recorded at the decision point. Duration uses fixed buckets:
`0.01`, `0.05`, `0.1`, `0.25`, `0.5`, `1`, `2.5`, `5`, `10`, and `30` seconds.

Allowed labels are only `operation` and `outcome`. No tenant, user, aggregate,
request, text, date, amount, or exception labels exist. Registry tests inspect label
names and metric exposure. Runtime `/metrics` returned 200 and exposed all six
research metric families.

## M5-AUD-009 accessibility automation

`axe-core`, `@playwright/test`, and `@axe-core/playwright` are development-only.
The existing Vitest/jsdom suite retains 12 semantic scans. A separate Vite harness
imports the real research components and aliases Clerk only inside the test bundle;
it cannot bypass the production Next.js/Clerk boundary. All API responses are
deterministic browser-local fixtures, and no Clerk key or live provider is used.

Chromium 151.0.7922.34 tests every required route: research overview; strategy list,
creation, detail, and version creation; backtest list, creation, detail, events,
analytics, explanations, and audit; and comparison. The same routes run under
Desktop Chrome and Pixel 7 mobile emulation.

Result: **30/30 browser tests pass**. Each route has exactly one page heading,
historical-simulation disclosure, no prohibited execution/advice controls, no
clickable-div control, no page-level horizontal overflow, visible keyboard focus,
and zero serious/critical axe findings. Axe rendered color-contrast checks remain
enabled. Dedicated tests prove Enter link activation, Space button activation, and
browser focus transfer to the validation summary.

The initial browser run failed before rendering because Vite needed an explicit
test-only API environment definition. After correction, 29/30 passed and exposed a
serious keyboard-access finding on the mobile event table. The scrollable evidence
region was made focusable and programmatically labeled; the final rerun passed
30/30.

This is not a claim of complete WCAG conformance. Firefox, WebKit, physical mobile
devices, and screen-reader testing remain future independent assurance work.

## Tests, coverage, and quality gates

| Gate                             | Result                                                             |
| -------------------------------- | ------------------------------------------------------------------ |
| `pnpm install --frozen-lockfile` | PASS                                                               |
| JavaScript tests                 | PASS — 52 total: web 49, UI 2, shared 1                            |
| Focused research UI tests        | PASS — 26, including 12 axe scans                                  |
| Chromium accessibility tests     | PASS — 30: 15 desktop and 15 mobile                                |
| ESLint                           | PASS                                                               |
| TypeScript                       | PASS                                                               |
| Next.js/workspace build          | PASS                                                               |
| Ruff format/check                | PASS                                                               |
| mypy                             | PASS — 63 source files                                             |
| Python/PostgreSQL tests          | PASS — 127                                                         |
| Coverage                         | PASS — 85.55%, threshold 80%                                       |
| `pip check`                      | PASS                                                               |
| `pip-audit`                      | PASS — no known Python vulnerabilities                             |
| `git diff --check`               | PASS                                                               |
| `pnpm format:check`              | PASS after separately authorised historical formatting-only commit |

## Migration validation

- baseline current: `20260728_0007`;
- upgrade: `20260730_0008 (head)`;
- downgrade to 0007: PASS;
- re-upgrade: PASS;
- `alembic check`: `No new upgrade operations detected`;
- disposable database upgrade through revisions 0001–0008: PASS;
- disposable database removed;
- development database left at 0008.

## Docker and runtime results

`docker compose config --quiet`, full image build, and
`docker compose up --detach --wait` pass. PostgreSQL, Redis, API, and web are healthy.
API runs as `atlas`; web as `nextjs`. Both application root filesystems are
read-only, both use `no-new-privileges`, and both have zero mounts.

Runtime status:

- homepage 200;
- liveness 200;
- readiness 200;
- metrics 200;
- OpenAPI 200;
- unauthenticated protected research route 401;
- migration head 0008.

No external AI, broker, payment execution, custody, or live-provider functionality
was introduced. Clerk secret handling was not changed.

## Dependency findings

Python audit: no known vulnerabilities. The governed Node audit passes and continues
to report the approved development-only `brace-expansion`
GHSA-mh99-v99m-4gvg / CVE-2026-14257 exception, expiring 2026-10-27. Raw
`pnpm audit` and `pnpm audit --prod` exit 1 for that same High advisory. Production
remains prohibited under [security-risk-exceptions.md](security-risk-exceptions.md).

## Files created

- `apps/web/e2e/harness/clerk-test-shim.tsx`
- `apps/web/e2e/harness/index.html`
- `apps/web/e2e/harness/main.tsx`
- `apps/web/e2e/harness/next-link-test-shim.tsx`
- `apps/web/e2e/playwright.config.ts`
- `apps/web/e2e/tests/research-accessibility.spec.ts`
- `apps/web/e2e/vite.config.ts`
- `docs/milestone-5-remaining-findings-remediation.md`
- `docs/observability.md`
- `packages/database/alembic/versions/20260730_0008_harden_research_parent_integrity.py`

## Files modified

- `.github/workflows/test.yml`
- `.gitignore`
- `apps/api/src/research/metrics.py`
- `apps/api/src/research/schemas.py`
- `apps/api/src/research/services.py`
- `apps/api/tests/test_research.py`
- `apps/api/tests/test_research_integration.py`
- `apps/web/package.json`
- `apps/web/src/components/research-browser.tsx`
- `apps/web/src/components/research-screen.tsx`
- `apps/web/src/test/research.test.tsx`
- `apps/web/vitest.config.ts`
- `package.json`
- `packages/database/atlas_database/models/research.py`
- `pnpm-lock.yaml`

Separately committed formatting-only path:

- `docs/milestone-5-frontend-reaudit.md` in commit `6b5d69c`

Historical audit wording was not modified; the separately authorised Prettier-only
normalisation is commit `6b5d69c`. No governance date, migration 0007,
infrastructure implementation, or Milestone 6 file was modified.

## Corrective changes and remaining limitations

An initial container test inherited Compose's `development` environment and trusted
host list, causing 10 unrelated configuration/host failures. The corrective rerun
set the documented local test environment and explicit test hosts; 127/127 then
passed. A combined dependency command timed out and was rerun as bounded individual
commands. Browser-test corrections are recorded in the accessibility section.

Remaining limitations:

- Firefox, WebKit, physical-device, and assistive-technology checks are not yet
  automated;
- the governed Node advisory remains development-only;
- production and public access remain prohibited.

## Final remediation status and re-audit readiness

**CONDITIONAL PASS.** M5-AUD-005 through M5-AUD-009 are technically ready for
independent re-audit. The condition reflects private-development governance,
governed dependency exceptions, and the remaining cross-browser/manual
accessibility assurance limitations. It does not authorise production.

Milestone 6 **may not begin**.

## Exact command appendix

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

pnpm audit:governed
pnpm audit:governed:prod
pnpm audit --prod
pnpm audit
git diff --check

docker compose config --quiet
docker compose build
docker compose up --detach --wait
docker compose ps
docker compose run --rm api alembic -c packages/database/alembic.ini current
docker compose run --rm api alembic -c packages/database/alembic.ini check
```
