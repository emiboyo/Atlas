# Milestone 5 Final Audit-Evidence Remediation

## 1. Title

Final remediation of M5-RF-001 and M5-RF-002.

## 2. Date

2026-07-31.

## 3. Repository

`C:\Dev\Atlas`.

## 4. Branch

`test/milestone-5-final-audit-evidence`.

## 5. Baseline commit

`d0170a6` (`merge: record remaining Milestone 5 re-audit findings`).

## 6. Scope

Test and evidence remediation only for malformed pre-0008 migration handling
and retry-after-rollback idempotency.

## 7. Governance boundary

Private development, local testing, CI, audit, and remediation only. No
production, public access, external AI, trading, execution, advice, real
money, custody, payments, or Milestone 6 authority is granted.

## 8. M5-RF-001 baseline

Migration 0008 contained fail-closed validation and parent constraints, but
the previous audit lacked the complete controlled malformed-0007 database
matrix and exact direct PostgreSQL rejection evidence.

## 9. Malformed 0007 database harness

Each parameter creates a uniquely named PostgreSQL database, migrates it only
to `20260728_0007`, creates deterministic valid research parents, introduces
one controlled malformed relationship, snapshots exact run/audit identifiers
and values, attempts migration to head, verifies failure, revision retention,
unchanged snapshots, absence of the new run-parent constraint, and `SELECT 1`,
then removes the database in `finally`.

The cross-tenant run fixture explicitly removes the old 0007
version-and-tenant FK inside its disposable database because that old FK
otherwise prevents constructing the historical corruption. No repository
migration is changed.

## 10. Each malformed upgrade case

All eight required cases passed:

1. Same-tenant run references another strategy's version.
2. Cross-tenant run references another tenant's version.
3. Same-tenant strategy current version belongs to another strategy.
4. Cross-tenant strategy current version belongs to another tenant.
5. Audit strategy/version mismatch.
6. Audit run parent mismatch with an otherwise valid version parent.
7. Run audit has no strategy version.
8. Persisted `skip_event` missing-data policy.

## 11. Upgrade failure evidence

Every `alembic upgrade head` from malformed revision 0007 returned non-zero
and contained the applicable migration message: malformed backtest run,
malformed current version, malformed audit parent, or unsupported historical
missing-data policy.

## 12. Revision-retention evidence

After every failed upgrade, `alembic_version.version_num` remained
`20260728_0007`.

## 13. No-silent-repair evidence

Ordered snapshots include run ID, strategy ID, version ID, and policy, plus
audit ID, strategy ID, version ID, and run ID. Before and after snapshots are
equal. No valid or malformed row is converted, repaired, or deleted. The new
0008 run-parent constraint is absent after failure.

## 14. Direct 0008 PostgreSQL rejection matrix

| Operation                                     | Result                            |
| --------------------------------------------- | --------------------------------- |
| Same-tenant wrong-strategy run/version        | rejected                          |
| Cross-tenant run/version                      | rejected                          |
| Same-tenant wrong current version             | rejected at commit                |
| Cross-tenant current version                  | rejected at commit                |
| Audit strategy/version mismatch               | rejected                          |
| Audit run mismatch                            | rejected                          |
| Run audit without version                     | rejected                          |
| Delete strategy version                       | rejected by append-only trigger   |
| Delete completed run                          | rejected by immutable-run trigger |
| Valid staged strategy/version/current version | committed                         |

Every failed direct transaction is rolled back and followed by successful
`SELECT 1`.

## 15. SQLSTATE evidence

- Composite parent FK violations: `23503`.
- Run-audit-without-version check: `23514`.
- Append-only/immutable delete triggers: `23000`.

## 16. Constraint-name evidence

- `fk_backtest_runs_version_parent`
- `fk_research_audit_version_parent`
- `fk_research_audit_run_parent`
- `fk_research_strategy_current_version_parent`
- `ck_research_audit_events_ck_research_audit_events_resea_6150`

Trigger-raised deletion exceptions do not provide a constraint name; their
stable SQLSTATE and message are asserted.

## 17. RESTRICT deletion evidence

The PostgreSQL catalog reports `confdeltype = b"r"` for all four new parent
FKs. Direct deletion is additionally blocked by existing append-only and
completed-run triggers, preserving historical evidence.

## 18. Deferred-constraint evidence

The current-version FK accepts the update statement while deferred, then
rejects both same-tenant and cross-tenant mismatch at commit with SQLSTATE
`23503` and the exact current-version constraint name. A valid
strategy/version/current-version aggregate created through the service
commits successfully.

## 19. M5-RF-001 decision

**RESOLVED.**

## 20. M5-RF-002 baseline

Previous fault tests proved rollback but did not prove that failed
idempotency keys remained safely reusable with identical and conflicting
payloads.

## 21. Version retry-after-fault evidence

A test-only replacement commit fails after version persistence and audit
staging. Explicit rollback is followed by a separate-session zero version and
zero audit check. Identical retry creates one immutable version, replay returns
its ID, and a changed label returns `idempotency_conflict`.

## 22. Run retry-after-fault evidence

The complete workflow is parameterized over an early failure after run flush
and a late failure at final commit. Each rolls back explicitly. Separate
sessions prove zero run and lifecycle audit. Identical retry creates one
completed run; replay returns it; changed capital returns
`idempotency_conflict`.

## 23. Explanation retry-after-fault evidence

A test-only commit replacement fails after explanation and audit staging.
Separate-session checks prove zero explanation and zero audit. Identical retry
creates one explanation, replay returns it, and a changed valid explanation
type returns `idempotency_conflict`.

## 24. Identical replay evidence

Version, run, and explanation replay IDs exactly equal the original successful
retry IDs. Aggregate counts remain one.

## 25. Conflicting replay evidence

Each conflicting retry raises `ApplicationError` with stable code
`idempotency_conflict` (HTTP mapping 409).

## 26. Aggregate/audit counts

- Version: one version and one creation audit; no duplicate version number.
- Run: one completed run, one result, a non-empty single event/equity
  sequence, and exactly requested/started/completed audits (three).
- Explanation: one explanation and one generated audit.
- Every failed-key pre-retry check reports zero aggregate and zero audit.
- The verification session remains usable.

## 27. Repeatability result

Both focused files ran twice consecutively:

- run 1: 33 passed in 37.38 seconds;
- run 2: 33 passed in 37.52 seconds.

The version and explanation workflow and both early/late run boundaries are
therefore each exercised twice.

## 28. Focused test totals

- Migration evidence file: 9 passed.
- Research integration file: 24 passed.
- Combined focused total: 33 passed, repeated twice.

## 29. Full Python test total

139 passed, 0 failed, 0 skipped, 0 xfailed, with 6 Starlette deprecation
warnings.

## 30. Coverage

86.05% over 4,853 measured statements. The 80% gate passed.

## 31. JavaScript/browser test results

- Package tests: 52 passed across 7 files (49 web, 2 UI, 1 shared).
- Accessibility: 32 Chromium tests passed (16 desktop, 16 Pixel 7).
- Prettier, ESLint, TypeScript, and Next.js production build passed.
- Existing React `act` warnings remain non-failing development-test warnings.

## 32. Migration validation

The normal database began at 0008, downgraded to 0007, re-upgraded to 0008,
and passed `alembic check`. A clean disposable database upgraded through every
revision to 0008 and was removed. The normal database was left at
`20260730_0008 (head)`. No `atlas_m5_%` disposable database remains.

## 33. Docker/runtime state where checked

Real PostgreSQL 16 in the existing healthy Compose stack provided all database
evidence. PostgreSQL and Redis dependency health checks passed for every
containerized test invocation. This remediation did not rebuild or deploy
application images because it changes only tests and documentation.

## 34. Files created

- `apps/api/tests/test_research_migration_evidence.py`
- `docs/milestone-5-final-audit-evidence-remediation.md`

## 35. Files modified

- `apps/api/tests/test_research_integration.py`

No production, migration, governance, frontend, infrastructure, or dependency
file changed.

## 36. Failed commands and corrections

During development of the preserved work:

1. The first retry test used invalid fixture value `data_quality`. Pydantic
   rejected it before the conflict path. It was corrected to the allowed
   `data_quality_explanation`; rerun passed.
2. The first exact-audit assertion expected one audit for a completed run.
   The correct lifecycle is requested, started, completed (three). The
   aggregate and exact per-workflow audit expectations were separated; rerun
   passed.
3. The first deletion SQLSTATE expectation was `P0001`; the existing triggers
   deliberately raise integrity-constraint-violation `23000`. The exact
   observed state and messages are now asserted; rerun passed.
4. A strengthened RESTRICT catalog assertion expected text `"r"`;
   asyncpg returns PostgreSQL internal `char` as `b"r"`. The exact driver value
   is now asserted; rerun passed.
5. Strengthening snapshots made `func` and `BacktestRun` imports unused. Ruff
   identified both; they were removed and Ruff passed.
6. The original audit-run migration fixture simultaneously had a wrong
   version and run. It was refined to a valid version plus invalid run so the
   run-parent case is isolated; the expanded nine-test migration suite passed.

No production defect or migration weakening was introduced to make a test
pass.

## 37. Remaining limitations

The governed Node development advisory and inherited base-image advisory
remain subject to their existing exceptions. Browser coverage remains
Chromium desktop/mobile rather than full multi-engine, physical-device, or
screen-reader conformance. Six framework deprecation warnings and existing
React test warnings remain. Production remains prohibited.

## 38. Final remediation status

> **PASS — M5-RF-001 and M5-RF-002 are technically resolved.**

All evidence-remediation acceptance gates passed. This is a remediation
result, not the independent re-audit decision and not production approval.

## 39. Independent re-audit readiness

The focused evidence remediation is ready for final independent re-audit.

## 40. Milestone 6 decision

**Milestone 6 remains prohibited** until this remediation is independently
reviewed and explicit governance approval is granted.

## 41. Exact command appendix

Core commands executed:

```powershell
.\.venv312\Scripts\python.exe -m ruff format --check `
  apps/api/tests/test_research_integration.py `
  apps/api/tests/test_research_migration_evidence.py
.\.venv312\Scripts\python.exe -m ruff check `
  apps/api/tests/test_research_integration.py `
  apps/api/tests/test_research_migration_evidence.py

# Executed with the documented real PostgreSQL URL in the Compose test runtime:
python -m pytest apps/api/tests/test_research_migration_evidence.py -vv -x
python -m pytest apps/api/tests/test_research_integration.py -vv -x
python -m pytest apps/api/tests/test_research_migration_evidence.py `
  apps/api/tests/test_research_integration.py -q

python -m pytest --cov=apps.api.src `
  --cov=packages.database.atlas_database `
  --cov-report=term-missing --cov-fail-under=80

.\.venv312\Scripts\python.exe -m ruff format --check apps packages/database
.\.venv312\Scripts\python.exe -m ruff check apps packages/database
.\.venv312\Scripts\python.exe -m mypy apps/api/src packages/database/atlas_database
.\.venv312\Scripts\python.exe -m pip check
.\.venv312\Scripts\python.exe -m pip_audit -r apps/api/requirements.txt

pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm test:a11y
pnpm build
git diff --check

docker compose exec -T api alembic -c packages/database/alembic.ini current
docker compose exec -T api alembic -c packages/database/alembic.ini downgrade 20260728_0007
docker compose exec -T api alembic -c packages/database/alembic.ini upgrade head
docker compose exec -T api alembic -c packages/database/alembic.ini check
```

No files were staged or committed, no deployment occurred, and no Milestone 6
work began.
