# Milestone 5 Governance Decision — Explainable AI Strategy Research, Historical Backtesting and Simulation

## 1. Title

Atlas AI Milestone 5 Private-Development Governance Authorisation.

## 2. Decision date

2026-07-28.

## 3. Risk owner

Adebayo Olaegbe, Founder and Project Owner.

## 4. Repository

`C:\Dev\Atlas`.

## 5. Branch

`chore/milestone-5-governance`.

## 6. Baseline commit

`2792148` — `merge: accept Milestone 4 conditional audit`.

## 7. Background

Atlas completed and independently audited its private simulated-portfolio
foundation through Milestone 4. The next bounded research stage is an
explainable, reproducible environment for testing user-defined strategy
hypotheses against historical or deterministic Atlas data. It is not a live
trading, advisory, or production capability.

## 8. Milestone 4 audit outcome

Milestone 4 received **CONDITIONAL PASS — PRIVATE DEVELOPMENT ONLY**. The audit
verified tenant-scoped portfolios, virtual cash, simulated transactions,
balanced accounting, append-only history, weighted-average cost, compensating
reversals, valuation provenance, descriptive analytics, fixed precision,
tenant isolation, central authorisation, and PostgreSQL concurrency controls.
Production and public use remain prohibited.

## 9. Governance problem

Existing authority ends at Milestone 4. Strategy research, backtesting, and AI
explanation introduce model-risk, overfitting, data-leakage, reproducibility,
and advisory-boundary risks not covered by that decision. A specific,
time-bounded authorization is required before any Milestone 5 implementation.

## 10. Proposed Milestone 5 scope

**Milestone 5 — Explainable AI Strategy Research, Historical Backtesting and
Simulation.**

Scope is limited to private local development, automated tests, CI, and
internal Docker Compose validation of tenant-isolated, historical, simulated,
reproducible, explainable, auditable, non-executing, and non-advisory research.

## 11. Permitted activities

### Research strategies

- Tenant-scoped personal and organisation-owned research strategies with
  immutable Atlas IDs.
- Bounded names, descriptions, purposes, tags, classifications, templates, and
  deterministic parameters.
- Explicit versions and append-only version history.
- Active, archived, and superseded lifecycle states.
- Server-controlled ownership and tenant relationships.
- User-created rule-based hypotheses.

### Historical backtesting

- Backtests using stored Atlas candles/quotes or approved deterministic
  fixtures.
- Explicit date range, starting simulated capital, position sizing, benchmark,
  fees, slippage, and execution-price assumptions.
- Historical simulated entries, exits, stop-losses, take-profits, and bounded
  rebalance intervals.
- Deterministic event ordering, immutable run configuration, reproducible runs,
  and append-only results.
- Long-only simulation unless separately governed.

### Strategy rules

Permitted bounded rule categories include moving averages, price crossovers,
momentum, volatility, reliable volume, position sizing, entry, exit, simulated
stop-loss/take-profit, maximum exposure, cooldown, and simulation-only
rebalance intervals. Rules cannot create real orders or live instructions.

### Backtest outputs

Permitted descriptive results include simulated starting/ending value,
historical simulated P&L/return, trade/win/loss counts, win rate, average
simulated gain/loss, volatility, drawdown, exposure, turnover, benchmark
comparison, completeness, missing/stale counts, assumptions, period, and
observation count. Outputs must be labelled historical, simulated, and
non-predictive.

### Explainable AI research assistance

AI may explain a user-defined strategy or historical result, identify which
rules caused a historical simulated event, describe historical strengths and
weaknesses neutrally, identify missing/stale data, flag possible look-ahead
bias/leakage/parameter sensitivity, explain assumptions, compare two
historical runs neutrally, generate non-actionable research questions, and
propose generic templates for further simulation.

### Research provenance

Retain strategy/version/rules/parameters, actor, tenant, Atlas listing,
data/provider source, observation and receipt timestamps, quality state,
benchmark, fee/slippage/execution assumptions, random seed, model/explainer and
prompt/template versions, software version, run timestamps, request ID, and
audit linkage.

### Research frontend

Private-development screens may cover strategy lists, creation, version
history/editor, backtest configuration/history/detail, simulated trade history,
historical performance/drawdown/benchmark charts, parameters, data quality,
explanation, audit history, and explicit loading/empty/stale/missing/
unavailable/failure states.

Every relevant screen must state:

> Historical simulation only — not investment advice and not a prediction of
> future performance.

### AI provider restrictions

Deterministic mock providers and local deterministic explanation engines are
permitted. A provider abstraction may be designed. Production AI credentials,
external transmission of portfolio/personal information, external training or
fine-tuning on real customer financial data, autonomous agents, and
execution-capable tool calls are prohibited. AI is never authoritative for
accounting, identity, permissions, financial state, or execution.

## 12. Prohibited activities

- Production deployment, production deployment configuration, or public
  customer access.
- Real money, deposits, withdrawals, payments, cards, bank transfers, open
  banking, money transmission, custody, wallets, or customer funds.
- Brokerage/exchange integration, order routing/submission, execution,
  clearing, settlement, live trading, or paper-to-live conversion.
- Copy/social trading, automatic rebalancing, autonomous trading agents, or
  AI-controlled portfolio transactions.
- Any AI-triggered or AI-controlled portfolio transaction or simulated-portfolio
  transaction, with or without user confirmation. AI may propose research
  templates or explain historical results, but only the deterministic backtest
  engine may generate historical simulated events from an explicitly
  user-approved, immutable backtest configuration.
- Live signals; current buy/sell recommendations; personalised asset,
  allocation, entry, stop-loss, or take-profit recommendations.
- Expected/guaranteed return claims, suitability, investment/financial/tax
  advice, or KYC/regulatory approval claims.
- Production Clerk, market-data, or AI-provider credentials and live financial
  providers.
- Terraform apply, Milestone 6, or any later milestone.

## 13. Non-advisory boundary

Historical research describes what occurred under explicit simulated
assumptions. It does not tell a person what to do now.

Permitted examples include:

- “This historical simulation produced a maximum drawdown of 11.4% during the
  selected period.”
- “The simulated rule triggered 18 historical entries.”
- “Results changed materially when the lookback period changed.”
- “Historical performance does not predict future performance.”
- “This result is incomplete because market data is missing.”

Prohibited examples include “You should buy this asset,” “Buy at this price,”
“Set your live stop loss here,” “This strategy will make money,” “This is a
safe investment,” “This is the best strategy for you,” “Atlas recommends this
portfolio,” and suitability claims.

## 14. Historical-simulation boundary

Backtests operate only on historical stored Atlas data or approved
deterministic fixtures. Simulated events have no monetary, legal, brokerage,
custody, or execution effect. Historical results cannot be represented as
current signals, live performance, predicted outcomes, or guarantees.

## 15. AI-assistance boundary

AI output is optional research commentary, never executable authority. It
cannot alter strategy/run provenance, accounting records, permissions,
portfolio state, simulated transactions, or results. Users must be able to
disable it; provider failure must leave deterministic research available with
a safe unavailable state.

## 16. Backtest-integrity requirements

- No look-ahead bias, future candles in decisions, target leakage, or hidden
  training/evaluation leakage.
- No silent survivorship bias or omission of delisted/unavailable instruments.
- No fabricated observations or interpolation presented as observed data.
- Stale/cached data cannot be presented as contemporaneous/live.
- Explicit missing-data, execution-price, fee, slippage, position-sizing, and
  benchmark policies.
- Deterministic ordering and timezone-aware timestamps.
- Reproducible immutable input configuration and append-only results.
- Explicit strategy/software versions and bounded parameters.
- No unlimited optimization or automatic “best” selection without overfitting
  warnings.
- Training, validation, and holdout separation where fitting occurs.
- Reproducible random seeds whenever randomness is used.

## 17. Model-risk requirements

Record model/algorithm identity and version, features and provenance, training
boundaries where applicable, validation method, limitations, confidence
limitations, and deterministic replay where possible. Explanations cannot be
fabricated, conceal future data, assert unsupported causality, or use guarantee
language. Human review is required for interpretation. The explainer must be
disableable and fail safely. Model output cannot bypass permissions or trigger
financial action.

## 18. Financial-integrity requirements

- Fixed-precision Decimal calculations for persisted money and quantities.
- Explicit currencies and no silent FX conversion.
- Server-controlled market-data provenance.
- Append-only runs/results and immutable configuration after execution.
- Deterministic simulated trades with explicit fees/slippage.
- Controlled supersession rather than destructive editing.
- Request/result idempotency.
- Database constraints and application validation.
- Reversible migrations and real PostgreSQL validation.

## 19. Authentication and authorisation requirements

Candidate central permissions include `strategy:read`, `strategy:create`,
`strategy:update`, `strategy:archive`, `strategy:version:create`,
`backtest:create`, `backtest:read`, `backtest:compare`, `backtest:explain`, and
`backtest:audit:read`. Exact names may be refined, but evaluation must be
central, server-side, tenant-scoped, object-aware, and fail-closed.

Require authenticated active users, active tenants/memberships, server-derived
effective permissions, and object concealment. Browser role, permission,
tenant, ownership, model/provider version, and result status are never
authorities.

## 20. Tenant-isolation requirements

Strategies, versions, parameters, runs, configuration, simulated trades,
results, explanations, model outputs, comparisons, and audit events must carry
or derive an Atlas tenant boundary. Application queries must require tenant
context; composite database constraints must reject cross-tenant references
where practicable.

## 21. Data-quality requirements

Validate listing identity, intervals, timestamps, ordering, currencies,
parameters, observations, data status, provenance, and completeness before use.
Missing remains missing, stale remains stale, unavailable remains unavailable,
simulated remains simulated, and cached cannot become live. Results must
explain excluded/missing observations and assumptions.

## 22. Data-classification requirements

Product governance documentation may be Public after approval; internal
templates are Internal. Tenant strategy definitions, parameters, inputs,
results, explanations, simulated-portfolio references, and audit records are
Confidential. Prompts and model responses are Confidential unless a stricter
classification applies. Secrets/credentials are Restricted. Real financial,
bank, card, brokerage, KYC, tax, identity, or customer-fund information is
prohibited from this milestone.

## 23. Audit and observability requirements

Successful changes/runs/explanations require append-only events with bounded
actor, tenant, target, operation, version, timestamp, request, and provenance
metadata. Metrics use bounded operation/type/status/result labels. Logs and
metrics must exclude raw strategy source, portfolio names, user IDs, tokens,
credentials, complete definitions, unrestricted prompts, full model responses,
sensitive holdings, and raw provider payloads.

## 24. Testing requirements

Tests must cover authentication/inactive identities, memberships/roles,
tenant isolation/guessed IDs/manipulation, idempotency/conflicts/concurrency,
deterministic replay/order, precision/currency/fees/slippage, missing/stale/
unavailable data/provenance, look-ahead/leakage prevention, parameter bounds,
immutable versions/runs, audit/explanation provenance, non-advisory language,
absence of execution controls, safe provider failure, frontend permissions/
accessibility/responsive states, reversible PostgreSQL migrations, and at
least 80% Python coverage.

## 25. CI requirements

CI must retain frozen installation, formatting, linting, strict typing, tests,
at least 80% Python coverage, production builds, dependency audits, PostgreSQL
migration/drift validation, and Compose configuration validation. CI must use
deterministic local fixtures, no production credentials/providers, no
deployment, and no Terraform apply.

## 26. Docker and runtime restrictions

Compose is private development only. PostgreSQL, Redis, API, and web must be
healthy. API/web remain non-root, read-only, `no-new-privileges`, and without
host bind mounts. Runtime validation uses synthetic authentication,
deterministic data/AI, and no external financial or production AI service.

## 27. Existing exceptions

The following remain unresolved:

1. GHSA-mh99-v99m-4gvg / CVE-2026-14257 in development
   ESLint/minimatch tooling.
2. CVE-2026-12087 in unused Perl inherited from the Python slim image.

Their development-only scope extends solely to bounded Milestone 5 through ADR 0014. Owner Adebayo Olaegbe, review 2026-08-27, expiry 2026-10-27, controls,
revocation conditions, and production/public/live/real-money prohibitions are
unchanged. The exceptions remain unresolved and expire automatically.

## 28. Compensating controls

- ESLint remains outside runtime and does not process untrusted customer input.
- Atlas does not invoke Perl.
- Runtime containers remain non-root/read-only, use `no-new-privileges`, and
  have no host binds.
- Only stored/deterministic historical data and deterministic/local AI are
  permitted.
- External transmission and production credentials are prohibited.
- Authentication, tenant isolation, immutable provenance, quality gates,
  dependency audits, and secret checks continue.
- Production, public access, live connectivity, real money, and execution
  remain prohibited.

## 29. Stop conditions

Stop and return to governance review for authentication/tenant bypass,
cross-tenant disclosure, real-money/payment/custody/broker/exchange/order/
execution capability, production credentials, live providers, current trade
recommendation, personalised advice, AI-triggered/autonomous action,
look-ahead bias, material leakage, fabricated data, stale-as-current,
simulated-as-real, historical-as-prediction, silent FX, claimed but
non-reproducible runs, destructive result editing, secret exposure, failed
constraints, new unresolved Critical/High production-path vulnerability,
coverage below 80%, migration/build/Docker failure, missed review, expiry,
scope expansion, or commencement of Milestone 6.

## 30. Review date

2026-08-27. Unchanged.

## 31. Expiry date

2026-10-27. Unchanged. Authority expires automatically absent a new recorded
decision.

## 32. Production blockers

Production remains blocked by existing unresolved exceptions, independent
security/model-risk/regulatory/privacy review, production identity/perimeter
controls, market-data licensing, AI-provider/privacy approval, operational
resilience, monitoring and incident response, and explicit authorization for
any live financial capability.

## 33. Decision

**AUTHORISED FOR PRIVATE DEVELOPMENT ONLY.**

Work may begin only after this governance record and ADR 0014 are committed.

## 34. Next permitted activity

After commit, planning and implementation may begin only for bounded Milestone
5 explainable strategy research, historical backtesting, and simulation under
these controls. Production, public use, live/advisory/executing scope,
Milestone 6, and later milestones remain prohibited.

## 35. Approval statement

**Risk owner Adebayo Olaegbe authorises Atlas AI Milestone 5 private
development for explainable AI strategy research, historical backtesting and
simulation, subject to the controls, prohibitions, review date and expiry
recorded in this document.**

**This decision does not authorise production deployment, public customer
access, live trading, real-money investing, brokerage, execution, custody,
money movement, investment advice, personalised recommendations, autonomous
financial actions, handling customer funds or Milestone 6.**
