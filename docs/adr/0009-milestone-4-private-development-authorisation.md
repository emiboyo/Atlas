# ADR 0009: Milestone 4 Private-Development Authorisation

- **Status:** Accepted for private development only
- **Decision owner:** Adebayo Olaegbe
- **Decision date:** 2026-07-28
- **Review date:** 2026-08-27
- **Expiry date:** 2026-10-27
- **Production approval:** Not granted

## Context

The Milestone 3 focused re-audit Closed all original findings with a Conditional Pass under
private-development controls. Existing security decisions did not explicitly cover Milestone 4,
so a bounded owner decision is required.

## Decision

Authorise private development of **Milestone 4 — Simulated Portfolio Accounting and Read-Only
Portfolio Analytics**, subject to
[`docs/milestone-4-governance.md`](../milestone-4-governance.md). This extends
private-development scope only and grants no production, public, regulatory, or real-money
authority.

## Permitted scope

- Tenant-scoped simulated portfolios, virtual cash, holdings, positions, and append-only paper
  transactions.
- Simulated valuation using explicitly classified market data.
- Descriptive allocation, concentration, profit/loss, historical value, volatility, drawdown,
  benchmark, and currency-exposure analytics.
- Audit events, provenance, permission-aware UI, neutral charts, and explicit simulated/stale/
  unavailable states.
- Local development, testing, CI, and internal Compose validation.

## Explicit exclusions

Production, public access, live providers/credentials, real money, payments, banking, money
transmission, custody, wallets, brokerage, exchanges, orders, execution, settlement, clearing,
live/copy/social trading, rebalancing, AI transactions, recommendations, advice, suitability,
guarantees, KYC/regulatory approval, tax advice, customer funds, Terraform deployment, and
Milestone 5.

## Security conditions

Fail-closed authentication, active users/memberships, central server-side portfolio permissions,
tenant concealment, request IDs, safe errors/logs, server-controlled providers, non-root/read-only
containers, `no-new-privileges`, CI gates, and at least 80% Python coverage are mandatory.

## Financial-integrity conditions

Use immutable IDs, fixed-precision decimals, explicit currencies, deterministic ordering,
idempotency, constraints, explicit transactions, append-only history, safe reversals, timestamp
separation, provenance, freshness, reversible PostgreSQL migrations, and no hard deletion or
silent conversion.

## Existing exception linkage

GHSA-mh99-v99m-4gvg / CVE-2026-14257 and CVE-2026-12087 remain unresolved. Their development
scope extends only to bounded Milestone 4. Owner Adebayo Olaegbe, review 2026-08-27, expiry
2026-10-27, controls, and production prohibitions remain unchanged.

## Consequences

Milestone 4 private development may begin after commit. The work must be independently auditable
and cannot be represented as a production or regulated financial service. Live, advisory,
money, execution, production, or public scope requires another decision.

## Stop-work triggers

Stop for authentication/tenant bypass, unauthorised access, simulated shown real, stale shown
current, floating-point persistence, duplicates, destructive history editing, real connectivity,
secret exposure, a new unresolved Critical or High production-path vulnerability,
migration/constraint failure, coverage below 80%, failed build/Docker health, missed review,
expiry, or scope expansion.

## Review requirements

The owner must review this decision and linked exceptions by 2026-08-27, reassessing advisories,
control effectiveness, scope, and evidence. Expiry is 2026-10-27 and is not extended here.

## Supersession rules

Only a dated, owner-approved governance record with explicit scope, controls, prohibitions,
review, and expiry may supersede this ADR. It does not supersede technical ADRs 0001–0008 and
does not authorise Milestone 5.
