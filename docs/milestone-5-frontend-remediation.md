# Milestone 5 Frontend Remediation

## 1. Remediation scope

This focused remediation addresses M5-AUD-004 on
`fix/milestone-5-frontend-links`. It connects the authorised historical
research routes to the existing authenticated API without changing migration
0007, backend accounting, governance, or historical reports.

## 2. Baseline finding

The independent audit rated M5-AUD-004 High because only strategy list/create
was materially API-backed. Version, run, event, analytics, explanation, audit,
and comparison routes were static shells with active-looking dead buttons.

## 3. Routes inspected

The following routes exist in the Next.js production route manifest, built
successfully, and returned HTTP 200 from the local production container:

- `/app`, `/app/portfolios`, and `/app/research`
- `/app/research/strategies` and `/app/research/strategies/new`
- `/app/research/strategies/[strategyId]`
- `/app/research/strategies/[strategyId]/versions`
- `/app/research/strategies/[strategyId]/versions/new`
- `/app/research/backtests` and `/app/research/backtests/new`
- `/app/research/backtests/[runId]`
- `/app/research/backtests/[runId]/events`
- `/app/research/backtests/[runId]/analytics`
- `/app/research/backtests/[runId]/explanations`
- `/app/research/backtests/[runId]/audit`
- `/app/research/compare`

## 4. Navigation inventory

| Source/control                  | Destination/action                          | Authentication and permission       | Final behaviour                   |
| ------------------------------- | ------------------------------------------- | ----------------------------------- | --------------------------------- |
| Account desktop/mobile Research | `/app/research`                             | Protected app layout                | Valid route                       |
| Research cards                  | strategies, backtests, compare              | Authenticated user                  | Valid routes                      |
| Research section navigation     | home, strategies, runs, compare             | Authenticated user                  | Valid routes                      |
| Dynamic strategy card           | strategy detail                             | Strategy read                       | Uses API UUID                     |
| Strategy Versions               | version history                             | Strategy read                       | Uses strategy UUID                |
| Create immutable version        | version form                                | Server `can_create_version`         | Hidden when denied                |
| Dynamic run card                | run detail                                  | Backtest read                       | Uses run UUID                     |
| Run navigation                  | run, events, analytics, explanations, audit | Corresponding server permission/API | Uses run UUID                     |
| Create historical run           | run form                                    | API remains authoritative           | Redirects to returned run UUID    |
| Generate explanation            | explanation POST                            | Server `can_explain`                | Hidden/disabled state when denied |
| Archive strategy                | archive POST                                | Server `can_archive`                | Confirmation and refresh          |
| Update strategy                 | PATCH                                       | Server `can_update`                 | Optimistic revision submitted     |

No `href="#"`, empty `href`, stale route name, malformed synthetic dynamic
link, or router redirect was found in the research route/component inventory.

## 5. Broken links found

No link targeted a nonexistent filesystem route. The material defects were
semantic: static buttons implied version creation, run execution, and
comparison without submitting anything. Dynamic route shells loaded but did
not retrieve their identified resources.

## 6. Static buttons found

The prior `Save immutable version`, `Run historical simulation`, and
`Compare historical results` buttons used `type="button"` without handlers.
They are now real form submissions. Explanation generation, update, and
archive have bounded handlers, duplicate-submission guards, and API errors.
No active-looking dead control remains in `research-screen.tsx`.

## 7. API integrations implemented

- Strategy detail, effective permissions, bounded update, and confirmed archive
- Immutable version history and typed SMA-crossover version creation
- Tenant run list and historical run creation
- Run detail and immutable assumption display
- Deterministic simulated-event retrieval
- Result, equity, drawdown, benchmark, and data-quality retrieval
- Local explanation list and generation
- Append-only research audit retrieval
- Neutral completed-run comparison

Idempotency keys are browser-generated for version, run, and explanation POST
requests. The API remains authoritative for resource IDs, tenant membership,
permissions, conflicts, and validation.

## 8. Permission handling

Strategy and run screens retrieve
`/effective-permissions`. Update, archive, version creation, explanation
generation, and audit presentation use server-returned capability booleans;
no role-name matrix was duplicated in the component. Hiding a control is not
treated as authorisation: every action still calls a centrally authorised API.

Strategy creation and initial tenant run listing remain protected by their
existing API permissions. A browser-supplied organisation ID is only a query
selector and is not authoritative.

## 9. Authentication and tenant handling

Missing Clerk tokens produce an explicit sign-in/session state. API 401, 403,
concealed 404, and service failures have distinct safe messages. Users without
an organisation see a safe organisation-selection state. Foreign and inactive
identity/membership handling remains server-controlled. No production Clerk
credential was added.

## 10. Empty, loading, and error states

Every API-backed view has a live loading/status region. Strategy/version/run
lists, events, results, explanations, and audit views have explicit empty
states. Failed runs expose only their stable failure code. API errors include
the safe request reference when supplied and never expose response bodies or
credentials.

## 11. Accessibility corrections

- Semantic navigation, links, buttons, forms, fieldsets, legends, labels, and
  tables
- Live, focusable loading/error/validation status
- Validation-summary focus for cross-field SMA validation
- Table captions for event, equity/drawdown, and audit evidence
- Text/table alternative for equity and drawdown
- Text status in addition to colour
- Native keyboard-operable controls and existing visible-focus styling
- Existing responsive desktop/mobile application navigation
- No clickable `div` controls

No formal WCAG conformance or browser assistive-technology certification is
claimed.

## 12. Tests added

The focused research tests cover:

- governed language and prohibited-control absence;
- valid static links and placeholder-link absence;
- dynamic strategy and run links;
- strategy success plus 401, 403, 404, and unavailable states;
- server-derived mutation controls;
- immutable version history;
- supported backtest assumptions;
- removal of unsupported skip policies;
- SMA bound/cross-field validation and status focus;
- API-backed analytics and accessible table alternative;
- explanation-disabled and audit-restricted states;
- active-button/dead-control regression.

Tests use synthetic Clerk tokens and deterministic API responses. They do not
use snapshots as acceptance proof.

## 13. JavaScript/package test total

**39 tests passed** across seven files:

- Web: 36 tests, including 13 focused research tests
- UI: 2 tests
- Shared: 1 test

## 14. Build result

ESLint, TypeScript, all package tests, the Next.js production build, and the
web Docker image build passed. All intended static and dynamic research routes
were present in the production route manifest.

The repository-wide formatting gate passed after a separately committed,
explicitly authorised Prettier-only correction to the historical audit record.

## 15. Manual route verification

The local production Docker image was rebuilt and started healthy. All 16
listed representative routes returned HTTP 200, including dynamic strategy
and run routes with UUID-shaped identifiers. Web container logs for the
verification window contained no hydration failure, uncaught exception,
invalid-href warning, duplicate-key warning, or request loop.

Authenticated content, permission, API error, empty-tenant, and dynamic-data
behaviour was verified through deterministic component integration tests with
synthetic authentication. No production identity or live provider was used.

## 16. Remaining placeholders

No active placeholder link or button remains in the research screen.
Production data entry still requires valid Atlas listing UUIDs; a searchable
listing picker was not added because that would broaden this focused
remediation. Version detail has no separate route in the authorised route set,
so history presents immutable version evidence inline.

## 17. Remaining limitations

- Historical simulation only; no live data, execution, prediction, advice, or
  external AI
- Strategy creation visibility cannot be pre-evaluated without a dedicated
  tenant-level effective-permissions endpoint; the existing server-authorised
  POST fails closed
- Browser E2E infrastructure is not present, so deterministic component
  integration and production-route HTTP checks were used
- M5-AUD-005 through M5-AUD-009 are outside this focused M5-AUD-004 change

## 18. Files created

- `docs/milestone-5-frontend-remediation.md`

## 19. Files modified

- `apps/web/src/components/research-screen.tsx`
- `apps/web/src/test/research.test.tsx`

Historical audit and implementation reports, governance, backend logic,
migrations, infrastructure, and dependencies were not modified.

## 20. Final remediation status

**PASS — M5-AUD-004 frontend remediation is technically complete and ready for
focused independent re-audit. All navigation, API integration, permission,
test, formatting, typecheck, and build gates pass.**

Milestone 6 remains prohibited.
