# Milestone 4 Governance Decision — Simulated Portfolio Accounting and Read-Only Portfolio Analytics

## 1. Title

Atlas AI Milestone 4 Private-Development Governance Authorisation.

## 2. Decision date

2026-07-28.

## 3. Risk owner

Adebayo Olaegbe, Founder and Project Owner.

## 4. Repository

`C:\Dev\Atlas`.

## 5. Branch

`chore/milestone-4-governance`.

## 6. Baseline commit

`415b268` — `merge: accept Milestone 3 conditional re-audit`.

## 7. Background

Atlas completed the platform, identity/tenancy, and read-only market-data foundations in
Milestones 1–3. The next bounded stage is a private simulated portfolio-accounting environment
that exercises financial-integrity engineering without real money, brokers, exchanges, payment
systems, production credentials, or public users.

## 8. Milestone 3 re-audit outcome

The focused independent Milestone 3 re-audit concluded **CONDITIONAL PASS — PRIVATE DEVELOPMENT
CONTROLS ONLY** and Closed M3-AUD-001 through M3-AUD-005. It prohibited production/public use and
required an explicit risk-owner decision before Milestone 4.

## 9. Governance problem

The temporary security decisions name Milestone 2 and do not expressly cover Milestone 4.
Starting work without a bounded decision would silently broaden accepted risk. This decision
closes that gap without changing the owner, review, expiry, controls, or production prohibition.

## 10. Proposed Milestone 4 scope

**Milestone 4 — Simulated Portfolio Accounting and Read-Only Portfolio Analytics.**

Scope is limited to private local development, tests, CI, and internal Docker Compose validation
of simulated portfolios, virtual balances, simulated positions/transactions, simulated
valuation, descriptive analytics, auditability, and their frontend.

## 11. Permitted activities

- Personal and organisation-scoped paper portfolios with immutable Atlas IDs, tenant ownership,
  names/descriptions, explicit base currency, and active/archived lifecycle.
- Virtual cash balances with no monetary value and no payment, transmission, or custody effect.
- Simulated holdings attached to Atlas listings, with fixed-precision quantities, average cost,
  book value, simulated valuation, realised/unrealised simulated profit and loss, and history.
- Virtual deposit/withdrawal, simulated buy/sell/dividend/fee/split-adjustment records.
- Valuation from existing simulated, delayed, cached, or stale market data with timestamp,
  provenance, freshness, currency, and missing-price handling.
- Descriptive total value, cash, allocation, concentration, profit/loss, historical value,
  volatility, maximum drawdown, benchmark, and currency-exposure analytics without silent
  conversion.
- Append-only portfolio audit events and transaction provenance.
- Portfolio list/detail, holdings, simulated transaction forms, valuation summary, neutral
  charts, allocation visualisation, descriptive explanations, and simulated/stale/unavailable
  states.

Every transaction, balance, holding, valuation, chart, and analytic result must be visibly and
semantically classified as simulated.

## 12. Prohibited activities

- Production deployment or public customer access.
- Real-money investing, deposits, withdrawals, payments, cards, bank transfers, open banking,
  money transmission, custody, wallets, settlement, or clearing.
- Brokerage, exchange connectivity, order routing, real order placement/execution, live trading,
  copy/social trading, or automatic rebalancing.
- AI-controlled transactions or autonomous trading agents.
- Personalised buy/sell recommendations, price targets, expected-return promises, guarantees,
  suitability, KYC/regulatory approval, tax advice, financial advice, or investment advice.
- Handling customer funds or storing real bank, card, payment, tax, passport, brokerage, or
  production credential data.
- Production Clerk/market-data credentials, live providers, Terraform deployment, or
  `terraform apply`.
- Milestone 5.

## 13. Non-advisory boundary

Analytics may describe a simulated portfolio's composition, historical behavior, data source, or
freshness. They must not tell a user to buy/sell, rank a portfolio as best/safe, recommend an
allocation, promise a return, or predict an outcome.

Analytics do not constitute investment advice, financial advice, suitability assessment,
recommendation, solicitation, guarantee, or prediction.

## 14. Simulated-finance boundary

Virtual deposits/withdrawals and simulated buys/sells are accounting records only. They cannot
reserve real funds, submit orders, contact brokers, exchanges, banks, card networks, processors,
wallets, or custodians, or represent legal customer assets/liabilities. UI/API language must
never make simulated activity appear real.

## 15. Financial-integrity requirements

- Immutable Atlas IDs and explicit currencies.
- Fixed-precision decimal persistence; no binary floating point.
- Transaction idempotency, deterministic ordering, and explicit transaction boundaries.
- Append-only financial/audit history; safe reversal rather than destructive editing.
- No hard deletion of financial-history records.
- Database constraints plus application validation.
- Source provenance and valuation freshness.
- Separate transaction, market-data, valuation, and receipt timestamps.
- No silent currency conversion.
- Reversible PostgreSQL migrations and real PostgreSQL validation.

## 16. Authentication and authorisation requirements

Clerk token verification, fail-closed authentication, active users, Atlas memberships, central
permission evaluation, object concealment, and safe errors remain mandatory. Planned permissions:

- `portfolio:read`
- `portfolio:create`
- `portfolio:update`
- `portfolio:archive`
- `portfolio:transaction:create`
- `portfolio:transaction:read`
- `portfolio:analytics:read`
- `portfolio:audit:read`

They must be evaluated centrally and server-side. Browser roles, permissions, tenant/portfolio
ownership, provider, transaction status, or simulation values are never authorities.

## 17. Tenant-isolation requirements

Every tenant portfolio, holding, transaction, valuation, analytic snapshot, and audit event must
carry or derive an Atlas tenant boundary. Cross-tenant references must fail at application and
database layers where practicable. Foreign/guessed objects must be concealed. Tests must cover
roles, suspended memberships, deactivated users, foreign tenants, and client manipulation.

## 18. Data-quality requirements

Quantities, values, currencies, timestamps, listing references, provenance, and freshness must be
validated before persistence or presentation. Missing stays missing, stale stays stale, and
simulated stays simulated. Cached data cannot be promoted to live. Currency conversion requires a
separately approved, provenanced design.

## 19. Audit and observability requirements

Successful mutations require append-only audit events with request, actor, tenant where
applicable, target, type, timestamp, and bounded safe metadata. Replays must not duplicate
financial/audit effects. Logs/metrics must exclude tokens, credentials, unrestricted notes,
payment data, raw provider payloads, and sensitive portfolio contents.

## 20. Testing requirements

Tests must cover cross-tenant IDOR, roles, unauthenticated access, mass assignment, idempotency,
duplicates, deterministic order, reversal, rollback, fixed precision, database constraints,
simulated labels, non-advisory language, stale/unavailable/missing valuations, provenance,
timestamp separation, audit events, frontend permissions/accessibility, and responsive states.
Python coverage remains at least 80%.

## 21. CI requirements

Required gates:

```text
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
python -m ruff format --check apps packages/database
python -m ruff check apps packages/database
python -m mypy apps/api/src packages/database/atlas_database
python -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
python -m pip check
python -m pip_audit -r apps/api/requirements.txt
```

CI must not deploy, use production credentials, contact live financial services, or weaken gates.

## 22. Docker and runtime restrictions

Run Compose configuration, build, `up --detach --wait`, and `ps`; PostgreSQL, Redis, API, and web
must be healthy. API/web remain non-root, read-only, and `no-new-privileges`. Compose is private
development only. PostgreSQL validation covers upgrade, downgrade, re-upgrade, fresh database,
Alembic check, constraints, and indexes.

## 23. Existing exceptions

This decision acknowledges but does not resolve:

1. GHSA-mh99-v99m-4gvg / CVE-2026-14257 in development ESLint/minimatch.
2. CVE-2026-12087 in unused Perl inherited from the Python slim image.

Their private-development scope extends only to this bounded Milestone 4 via
[ADR 0009](adr/0009-milestone-4-private-development-authorisation.md). Owner, review, expiry,
controls, revocation conditions, unresolved status, and production prohibitions are unchanged.

## 24. Compensating controls

- ESLint remains outside runtime; untrusted brace/glob patterns cannot reach lint.
- Atlas does not invoke Perl.
- Containers remain non-root, read-only, without host binds, and `no-new-privileges`.
- Only deterministic simulated/disabled market providers are allowed.
- Authentication, memberships, permissions, tenant isolation, quality/dependency/container gates,
  and secret scanning continue.
- Production, public access, live connectivity, and real money remain prohibited.

## 25. Stop conditions

Stop and return to governance review for authentication/tenant bypass, unauthorised access,
simulated activity shown as real, stale shown current, floating-point financial persistence,
duplicates, destructive history editing, real-money/payment/broker/exchange/custody/wallet/order/
execution/live-provider connection, secret exposure, a new unresolved Critical or High
production-path vulnerability, migration/constraint failure, coverage below 80%, failed build or
Docker health, missed review, expiry, or scope expansion.

## 26. Review date

2026-08-27. Unchanged.

## 27. Expiry date

2026-10-27. Unchanged; authorisation expires automatically absent a new recorded decision.

## 28. Production blockers

Production remains blocked by unresolved exceptions, production identity/perimeter controls,
independent security/regulatory/privacy review, market-data licensing/entitlements, operational
resilience evidence, and explicit approval for live financial capabilities.

## 29. Decision

**AUTHORISED FOR PRIVATE DEVELOPMENT ONLY.**

This bounded scope may begin after this decision and ADR 0009 are committed.

## 30. Next permitted activity

After commit, planning and implementation may begin only for **Milestone 4 — Simulated Portfolio
Accounting and Read-Only Portfolio Analytics** under these controls. Milestone 5 and all
production, public, live-provider, real-money, or execution work remain prohibited.

## 31. Approval statement

**Risk owner Adebayo Olaegbe authorises Atlas AI Milestone 4 private development for simulated
portfolio accounting and read-only portfolio analytics, subject to the controls, prohibitions,
review date and expiry recorded in this document.**

**This decision does not authorise production deployment, public customer access, live trading,
real-money investing, custody, money movement, investment advice, handling customer funds or
Milestone 5.**
