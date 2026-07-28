# ADR 0014: Milestone 5 Private-Development Authorisation

- **Status:** Accepted for private development only
- **Decision owner:** Adebayo Olaegbe
- **Decision date:** 2026-07-28
- **Review date:** 2026-08-27
- **Expiry date:** 2026-10-27
- **Production approval:** Not granted

## Context

Milestone 4 received a Conditional Pass under private-development controls.
Explainable strategy research and historical backtesting introduce model-risk,
look-ahead, leakage, overfitting, reproducibility, provenance, and
advisory-boundary risks that require a new bounded decision.

## Decision

Authorise private development of **Milestone 5 — Explainable AI Strategy
Research, Historical Backtesting and Simulation**, subject to
[`docs/milestone-5-governance.md`](../milestone-5-governance.md). Work may
begin only after this ADR and the governance record are committed.

## Permitted scope

- Tenant-scoped, versioned, append-only research strategy hypotheses.
- Reproducible historical backtests using stored Atlas data or deterministic
  fixtures.
- Long-only simulated rules, entries/exits, stop/take-profit scenarios,
  position sizing, fees, slippage, benchmarks, and descriptive outputs.
- Optional deterministic/local explanations and neutral historical comparison.
- Private UI, auditability, tests, CI, and internal Compose validation.

Every result is historical, simulated, non-predictive, non-advisory, and
non-executing.

## Explicit exclusions

Production/public use; real money/payments/banking/custody/wallets; brokers,
exchanges, orders, execution, settlement, clearing, live/copy/social trading,
automatic rebalancing of portfolios or live holdings, except deterministic
simulation-only rebalance events inside an explicitly configured historical
backtest; live signals; recommendations/advice/suitability/guarantees;
production credentials/providers; customer funds; Terraform apply; and
Milestone 6.

- Any autonomous, AI-triggered, or AI-controlled portfolio transaction or
  simulated-portfolio transaction, with or without user confirmation. AI may
  explain historical results or propose research templates, but it cannot
  create, modify, approve, or submit portfolio transactions.

## Backtest-integrity conditions

Prevent look-ahead, target/data leakage, fabricated observations,
stale-as-current presentation, hidden survivorship bias, silent exclusions,
and unbounded optimization. Record missing-data, execution-price, fee,
slippage, sizing, benchmark, timezone, strategy/software version, random seed,
and training/validation/holdout boundaries where applicable. Inputs are
immutable, results append-only, ordering deterministic, and replay
reproducible.

## AI and model-risk conditions

Record model/algorithm/version, features/provenance, data boundaries,
validation, limitations, confidence limitations, and explainer/template
version. Explanations cannot fabricate facts, claim causality without support,
use future data, guarantee results, bypass permissions, alter authoritative
state, or trigger execution. Human review, disablement, and safe unavailable
fallback are mandatory.

Only the deterministic backtest engine may generate historical simulated
events from an explicitly user-approved, immutable backtest configuration. AI
output cannot directly create or modify those events.

## Security conditions

Fail-closed authentication, active users/memberships, central server
permissions, object concealment, strict schemas, request IDs, safe
errors/logging, bounded metrics, dependency/security gates, non-root/read-only
containers, and `no-new-privileges` remain mandatory. Production credentials
and external transmission of tenant financial/research data are prohibited.

## Tenant conditions

Strategies, versions, parameters, runs, trades, results, explanations,
comparisons, model outputs, and audit records carry or derive an Atlas tenant
boundary. Browser tenant/role/ownership/provider/model/result fields are not
authorities. Cross-tenant references fail in application logic and database
constraints where practicable.

## Data-quality and financial-integrity conditions

Use fixed-precision Decimal persistence, explicit currencies, no silent FX,
server-controlled provenance, explicit data status and assumptions,
idempotency, deterministic simulated events, append-only completed runs,
controlled supersession, constraints, reversible migrations, and real
PostgreSQL validation. Missing/stale/unavailable/simulated classifications
cannot be promoted.

## Existing exception linkage

GHSA-mh99-v99m-4gvg / CVE-2026-14257 and CVE-2026-12087 remain unresolved.
Their development-only scope extends solely to bounded Milestone 5. Owner
Adebayo Olaegbe, review 2026-08-27, expiry 2026-10-27, compensating controls,
revocation conditions, and all production/public/live/real-money prohibitions
remain unchanged. This ADR does not rewrite historical decisions.

## Stop-work triggers

Stop for authentication/tenant bypass, cross-tenant disclosure, real financial
connectivity, production credentials, advice/live recommendation,
AI-triggered/autonomous action, look-ahead or material leakage, fabricated
data, stale/simulated misrepresentation, silent conversion, false
reproducibility, destructive results, secrets, failed constraints, a new
unresolved Critical/High production-path vulnerability, coverage below 80%,
migration/build/Docker failure, missed review, expiry, scope expansion, or
Milestone 6 commencement.

## Consequences

Milestone 5 private development may begin after commit. Historical simulations
cannot be represented as production investments, live trading, advice,
predictions, guarantees, or regulated financial services. Additional controls
increase implementation and test effort but make research reproducible and
auditable.

## Review requirements

The owner must review this decision and linked exceptions by 2026-08-27,
including advisory status, model/provider/data scope, control effectiveness,
and any attempted expansion. Authority expires on 2026-10-27 unless a new
dated decision supersedes it.

## Supersession rules

Only a committed, dated, owner-approved governance decision with explicit
scope, controls, prohibitions, review, and expiry may supersede this ADR. It
does not supersede prior technical or historical governance decisions.

## Milestone 6

Milestone 6 remains unauthorised.
