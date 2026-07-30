# Milestone 5 Focused Frontend Re-audit — M5-AUD-004

## 1–7. Audit identity

| Field | Value |
| --- | --- |
| Date | 2026-07-30 |
| Repository | `C:\Dev\Atlas` |
| Branch | `chore/milestone-5-frontend-reaudit` |
| Commit audited | `76fd978295e48ac1de25243f04313749156d5585` |
| Remediation commits | `e82002e`, `b44d0b5`, merge `76fd978` |
| Auditor role | Independent frontend, Next.js, API-integration, accessibility, authentication, and release-gate reviewer |

## 8–9. Executive conclusion and final status

> **FOCUSED RE-AUDIT STATUS: CONDITIONAL PASS**
>
> **M5-AUD-004 DECISION: RESOLVED**

The static-shell defect has been resolved. Strategy, version, run, event,
analytics, explanation, audit, and comparison screens now make genuine
authenticated API requests, consume dynamic identifiers, expose safe
loading/empty/error states, and use server-derived capabilities for
object-level mutation controls.

Independent review found and corrected four narrow defects: malformed
permission responses did not fail closed, run creation did not consume
`can_create_backtest`, strategy creation lacked a duplicate-submit guard, and
Docker did not carry Clerk variables through the correct build/runtime
boundaries. Final native and Docker gates pass.

The status is conditional because full authenticated browser E2E evidence is
not available, tenant-level strategy-create capability has no presentation
endpoint, and backtest pages currently select the first authorised
organisation rather than exposing an organisation switch. These are
private-development limitations, not unresolved Critical or High frontend
defects.

## 10. Scope

The re-audit covered the focused remediation diff, complete research route
tree, research links and controls, API contracts, effective permissions,
authentication/tenant/error states, accessibility, governed language, tests,
native gates, Docker security, route availability, Clerk variable boundaries,
and secret-marker checks.

## 11. Out-of-scope findings

M5-AUD-005 through M5-AUD-009 remain open and were not remediated. This audit
did not deploy, use live providers, add production credentials, weaken Clerk,
change migration 0007, modify financial accounting, or begin Milestone 6.

## 12. Baseline M5-AUD-004

The original High finding stated that most Milestone 5 research workflows were
static route shells rather than API-backed, permission-aware workflows. The
baseline `ResearchScreen` contained dead `type="button"` controls and static
result panels. The current implementation replaces those shells with genuine
request and mutation flows.

## 13. Claim-to-evidence matrix

| Claim | Independent evidence | Conclusion |
| --- | --- | --- |
| Intended routes exist | Source tree, Next.js production manifest, HTTP checks | Supported |
| No placeholder research links | Full web-source search and focused DOM test | Supported; homepage fragment links are legitimate in-page anchors |
| No active dead research control | Handler/form inventory and tests | Supported after correction |
| Strategy workflows API-backed | GET/POST/PATCH/archive requests match OpenAPI | Supported |
| Version workflows API-backed | List/create endpoints, typed form, idempotency | Supported |
| Run workflows API-backed | List/create/detail and returned-UUID redirect | Supported |
| Events/analytics/explanations/audit API-backed | Existing FastAPI endpoints verified from live OpenAPI | Supported |
| Comparison API-backed | Completed-run selection and compare POST | Supported |
| Dynamic UUID navigation | Route params and server-returned IDs used | Supported |
| Permissions server-derived | Effective-permissions endpoint and runtime normalization | Supported after correction |
| Safe auth/error/empty states | Code, stable API client, synthetic tests, unauthenticated Docker routes | Supported with E2E limitation |
| Unsupported missing policies absent | UI contains only disabled `fail_run`; test passes | Supported |
| Accessibility improved | Semantic controls/tables/live region/focus test | Supported at development level |
| 39 package tests | Independent final run: 40 tests | Claim superseded upward |
| All native gates | Executed independently | Passed |
| Docker Clerk wiring | Initially absent; correction and Docker rebuild verified | Resolved |

## 14. Route inventory

| Route | Source type | Authentication/API/state conclusion |
| --- | --- | --- |
| `/` | Static page | Public, no research API |
| `/sign-in`, `/sign-up` | Clerk catch-all dynamic routes | Safe configured/unconfigured Clerk state |
| `/app` | Protected app page | Server auth boundary |
| `/app/portfolios` | Protected page | Outside focused workflow |
| `/app/research` | Protected static navigation | Valid research destinations and disclaimer |
| `/app/research/strategies` | Protected client workflow | Organisations and tenant-filtered strategies; loading/empty/error |
| `/app/research/strategies/new` | Protected client form | Organisation resolution and authorised POST |
| `/app/research/strategies/[strategyId]` | Dynamic | Uses supplied ID for strategy and permissions; denied/missing/error states |
| `/app/research/strategies/[strategyId]/versions` | Dynamic | Uses supplied ID for strategy, versions, and permissions |
| `/app/research/strategies/[strategyId]/versions/new` | Dynamic | Uses supplied ID for typed version POST |
| `/app/research/backtests` | Protected client workflow | Tenant run GET and dynamic run links |
| `/app/research/backtests/new` | Protected client form | Strategy/version resolution, permissions, genuine run POST |
| `/app/research/backtests/[runId]` | Dynamic | Uses supplied run ID; result loaded only when complete |
| `/app/research/backtests/[runId]/events` | Dynamic | API event sequence and empty/error state |
| `/app/research/backtests/[runId]/analytics` | Dynamic | Result/equity/quality API requests and text table |
| `/app/research/backtests/[runId]/explanations` | Dynamic | List/generate, disabled/denied/empty/error |
| `/app/research/backtests/[runId]/audit` | Dynamic | Permission-restricted append-only API history |
| `/app/research/compare` | Protected client workflow | Completed-run selection and genuine comparison POST |

All routes were present in the production route manifest. Representative
unauthenticated requests returned safe HTML rather than a route 404.

## 15. Link and control findings

No research `href="#"`, empty `href`, clickable `div`, nonexistent
destination, or active-looking dead button remains. Dynamic strategy and run
links use API or route IDs. Every active mutation has a form action or click
handler, busy protection, an API request, and safe error output.

Occurrences of `href="#..."` are limited to public homepage section anchors
(`features`, `architecture`, and `roadmap`) and are not placeholder research
navigation.

## 16. Strategy workflow findings

The strategy list resolves authorised organisations, sends the selected tenant
as a query selector, displays server results, and creates dynamic links.
Creation submits bounded name/purpose fields and a tenant identifier that the
API re-authorises against active membership. Correction M5-FR-COR-003 prevents
duplicate submission.

Detail retrieves the route UUID and displays authoritative name, description,
purpose, status, revision, current version, and timestamps. Update sends only
name, description, purpose, and optimistic revision. Archive requires browser
confirmation. Both refresh authoritative data through the common mutation
path.

The UI cannot pre-hide strategy creation for a viewer because no tenant-level
effective-permissions endpoint exists. The POST remains centrally authorised
and returns 403, so this is a presentation limitation rather than an
authorisation bypass.

## 17. Version workflow findings

Version history is API-backed and presents number, label, fingerprint,
currency, benchmark, timestamp, and immutable ID. Creation supports only a
typed `sma_crossover` rule with bounded integer windows and cross-field
validation. It submits currency, listing, optional benchmark, typed rule, and
an idempotency header. Arbitrary code and unknown request fields are not
available.

Execution, fee, slippage, sizing, and starting capital are correctly run-level
assumptions in the actual FastAPI schema rather than version fields.

## 18. Backtest workflow findings

The list retrieves tenant-scoped runs and links to server-returned run IDs.
Creation selects an immutable version, uses only supported `fail_run`, and
submits the OpenAPI-defined date, capital, execution, fee, slippage, and sizing
fields with an idempotency header. Listing and benchmark derive from the
immutable version server-side.

Correction M5-FR-COR-002 now retrieves effective permissions for the selected
strategy and enables submission only when `can_create_backtest` is exactly
true. The API repeats authoritative authorisation.

Run detail displays status, period, capital/currency, all run assumptions,
engine version, configuration/data fingerprints, safe failure code, result
summary, and valid links to subsidiary evidence.

## 19. Event findings

Events are retrieved from the run endpoint and displayed in deterministic
sequence with event type, decision time, simulated execution time, listing,
price, quantity, fee, slippage, cash before/after, position before/after, and
triggered rules. Correction M5-FR-COR-003 added the previously omitted before
values. The caption and each event explicitly identify historical simulation.

## 20. Analytics findings

Result, equity, and data-quality requests are API-backed. The view shows ending
simulated value, P&L, historical percentage change, event/trade counts,
drawdown, volatility, turnover, benchmark history, completeness, and
missing/stale/unavailable/excluded counts. The chronological equity/drawdown
table is an accessible chart alternative. No predictive expected return,
ranking, winner, or recommendation is generated.

## 21. Explanation findings

Explanation list and generation use genuine endpoints and an idempotency
header. Generation requires `can_explain`. The UI displays explanation type,
text, limitations, local engine identifier/version, template version, status,
and timestamp. No external provider, tool, portfolio mutation, advice, or
execution path exists.

## 22. Audit-history findings

Audit events are retrieved from the run audit endpoint only when the server
returns `can_read_audit`. Timestamp, event type, bounded actor, and target are
presented in a captioned table with empty, denied, loading, and error states.

## 23. Comparison findings

The page lists completed runs and submits exactly two run IDs to the genuine
comparison endpoint. It displays the server comparison basis and an explicit
period/currency comparability warning. Results are presented neutrally without
selecting a winner or describing a best/recommended strategy.

## 24. Authentication findings

The protected app layout uses Clerk server authentication and redirects when
configured. Client API requests require `getToken`; missing tokens fail with a
safe authentication message. No development authentication bypass or
production credential is committed.

The local ignored `.env.local` has both required Clerk keys configured. Only
configuration booleans and lengths were inspected. No key value was printed.

## 25. Tenant findings

The browser's tenant selection is a query/request field, not authority.
FastAPI resolves active membership for every list, create, strategy, version,
run, explanation, comparison, and audit operation. Foreign object errors
remain concealed server-side.

Strategy pages support organisation selection. Backtest list/create/compare
currently use the first authorised organisation and do not expose an
organisation switch; see M5-FR-003.

## 26. Permission findings

Capability booleans originate from the strategy effective-permissions API; no
owner/admin/member/viewer matrix exists in frontend code. Missing permission
fields were already falsy. M5-FR-COR-001 now validates that every field is a
literal boolean and replaces any missing/malformed response with an all-denied
capability object. A regression test proves `"true"` cannot render archive or
version controls.

Hidden/disabled controls never replace API-side permission checks.

## 27. Loading, empty, and error findings

API-backed screens use a focusable polite live status. Lists and evidence
panels have explicit empty states. `AtlasApiError` distinguishes 401, 403,
concealed 404, and other stable errors and includes a bounded request
reference. 409, 422, 500, and network failures use the same safe envelope
without raw body, stack, token, or credential exposure. There is no automatic
retry loop.

Permission responses now have runtime fail-closed validation. Other successful
200 response bodies rely on the internal typed FastAPI contract; see
M5-FR-004.

## 28. Accessibility findings

Research uses semantic navigation, headings, native links/buttons, labelled
inputs, fieldsets/legends, captioned tables, live status output, validation
focus, text plus colour statuses, and an equity/drawdown text table. Desktop
and mobile application navigation are present. No clickable `div` was found.

No formal WCAG conformance is claimed. Full keyboard/screen-reader browser
automation is absent.

## 29. Governed-language findings

Every research screen renders:

> Historical simulation only — not investment advice and not a prediction of
> future performance.

Relevant recommendation/trading terms occur only in prohibitions, tests, and
the statement that Atlas cannot place orders or connect a broker. No live,
broker, bank, order, advice, suitability, guarantee, or expected-return
control exists.

## 30. Test review

The tests exercise component logic with synthetic Clerk tokens and realistic
API envelopes rather than snapshots. They cover navigation, placeholder
absence, dynamic IDs, strategy success, 401/403/404/unavailable, permissions,
malformed-permission denial, versions, typed validation, assumptions,
unsupported-policy absence, analytics/table alternative, explanation denial,
audit restriction, dead-control absence, disclaimer, and prohibited-control
absence.

Coverage is not exhaustive browser E2E. Dedicated form tests for every 409/422
mutation and every organisation-switch sequence remain desirable.

## 31. JavaScript/package test result

Independent final result: **40 passed across seven files**.

- Web: 37 tests across five files, including 14 focused research tests
- UI: 2 tests
- Shared: 1 test

## 32. Lint result

`pnpm lint`: passed, three workspace lint tasks successful with zero warnings.

## 33. Typecheck result

`pnpm typecheck`: passed for web, UI, and shared workspaces.

## 34. Production build result

`pnpm build`: passed. Next.js 16.2.11 compiled, typechecked, generated 18
static pages, and listed every intended static/dynamic research route.

## 35. Docker result

Compose configuration, web build, and `up --detach --wait` passed. PostgreSQL,
Redis, API, and web were healthy. Web runs as non-root `nextjs`, has a
read-only root filesystem, `no-new-privileges`, and no mounts.

M5-FR-COR-004 wires only the public Clerk key into the build and keeps
`CLERK_SECRET_KEY` runtime-only. `.env.local` remains outside Docker context.
Native and container browser-static scans found **zero** Clerk secret markers.

## 36. Route validation

`/`, `/app`, `/app/research`, strategy list/create, backtest list/create, and
compare each returned HTTP 200 `text/html` from the healthy local production
container. Protected pages rendered a safe authentication/Clerk state. HTTP
200 is treated only as route-existence evidence, not workflow proof.

## 37. Authenticated/manual validation

Local Clerk development keys are configured, but this audit environment cannot
operate an interactive browser or complete a human Clerk session. No
authenticated browser success, console, or network trace is claimed.
Authenticated application behaviour is supported by deterministic component
integration tests and the independently verified API/OpenAPI contracts.

## 38. Clerk/CAPTCHA environmental notes

No CAPTCHA result was observed. Clerk attack protection was not disabled.
Browser extension, Cloudflare Turnstile, and clean-browser behaviour remain
untested environmental factors rather than Atlas defects.

## 39. API-contract findings

Live FastAPI OpenAPI confirms every method/path used by the research frontend:
strategy list/create/detail/update/archive/permissions, version list/create,
run list/create/detail/events/equity/result/quality, explanation list/create,
audit history, and comparison.

Request field names and enums match. Version/run/explanation mutations include
`Idempotency-Key`. Financial form values remain strings; the only `Number`
conversion is for bounded non-financial SMA window integers. The frontend
offers only `fail_run` and does not expose backend `skip_event` or
`skip_observation`.

## 40. Corrective changes

| ID | Finding and correction | Evidence | Status |
| --- | --- | --- | --- |
| M5-FR-COR-001 | Malformed truthy effective-permission fields could render controls. Added exact runtime boolean normalization with all-denied fallback. | New malformed-permission regression; 40-test suite | Resolved |
| M5-FR-COR-002 | Run creation did not consume `can_create_backtest`. Fetch selected strategy permissions and disable unless exactly true. | Code/contract inspection; full gates | Resolved |
| M5-FR-COR-003 | Strategy creation could double-submit and event table omitted before-state evidence. Added busy guard and cash/position before/after columns. | Code review, lint/type/build/tests | Resolved |
| M5-FR-COR-004 | Docker did not wire Clerk keys. Added publishable build argument and runtime-only secret environment variable. | Clean Docker rebuild; zero browser secret markers | Resolved |

Files changed by re-audit corrections:

- `apps/web/src/components/research-screen.tsx`
- `apps/web/src/components/research-browser.tsx`
- `apps/web/src/test/research.test.tsx`
- `apps/web/Dockerfile`
- `docker-compose.yml`
- this report

No backend, migration, financial, governance, or historical report changed.

## 41. Remaining limitations and findings

| ID | Severity | Finding | Status |
| --- | --- | --- | --- |
| M5-FR-001 | Medium | No tenant-level effective-permissions endpoint exists to pre-hide strategy creation for viewers; server POST denies safely | Accepted development limitation |
| M5-FR-002 | Medium | No authenticated browser E2E/assistive-technology evidence | Accepted development limitation |
| M5-FR-003 | Medium | Backtest list/create/compare auto-select the first organisation rather than exposing organisation switching | Open private-development limitation |
| M5-FR-004 | Low | Non-permission successful API bodies rely on FastAPI's internal response contract rather than client runtime schemas | Accepted development limitation |
| M5-FR-005 | Low | Mutation-specific 409/422 UI tests are not comprehensive | Accepted development limitation |

No unresolved Critical or High frontend finding remains.

## 42. M5-AUD-004 resolution decision

**RESOLVED.** The primary workflows are no longer static shells, and the
remaining limitations do not recreate the original High finding.

## 43. Impact on overall Milestone 5 status

Resolving M5-AUD-004 removes the focused High frontend blocker. It does not
change overall Milestone 5 to PASS: M5-AUD-005 through M5-AUD-009 remain open,
the existing security exceptions remain governed for private development
only, and production remains prohibited.

## 44. Milestone 6 decision

**Milestone 6 may not begin.**

## 45. Exact command appendix

Principal successful commands:

```powershell
git branch --show-current
git status
git log --oneline --graph --decorate -15
git diff --check
git rev-parse HEAD
git ls-files | findstr /I ".env"
git show --stat b44d0b5
git show --name-status b44d0b5

pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
git diff --check

docker compose config --quiet
docker compose build web
docker compose up --detach --wait
docker compose ps
```

Additional independent checks included full research link/control/language
searches, live OpenAPI method/path and schema inspection, representative HTTP
route requests, container security inspection, ignored-file verification, and
native/container browser-static secret-marker scans.

Failed or corrected command record:

1. Preflight found `apps/web/next-env.d.ts` changed only from production to
   development route-type reference by Next.js. The earlier dev process was no
   longer running; the generated file was restored and the baseline became
   clean.
2. The first PowerShell route/secret summary used a direct pipe after
   `foreach`, producing `An empty pipe element is not allowed`. It returned no
   evidence. The command was rerun with an explicit results collection and
   passed.
3. The first multi-file correction patch did not apply because Prettier had
   changed the expected context. No partial change was applied. Corrections
   were split into verified narrow patches, formatted, and retested.

This conditional pass applies only to focused private-development frontend
remediation evidence. It does not authorise production, public access,
external AI, advice, live trading, execution, real money, customer funds, or
Milestone 6.
