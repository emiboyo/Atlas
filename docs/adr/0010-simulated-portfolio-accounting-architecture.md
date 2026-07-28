# ADR 0010: Simulated portfolio accounting architecture

- **Status:** Accepted for Milestone 4 private development
- **Date:** 2026-07-28
- **Governance:** `docs/milestone-4-governance.md`

## Context

Atlas already has tenant-scoped portfolios and a signed double-entry ledger with deferred
PostgreSQL balance triggers. Milestone 4 needs paper portfolios without implying brokerage,
custody, deposits, legal assets, or money movement.

## Decision

Extend the existing portfolio and ledger tables. A simulated portfolio owns explicit
currency-specific links to seven internal ledger account roles: virtual cash, simulated
investment cost, simulated capital, simulated dividend income, simulated fee expense, simulated
realised gain, and simulated realised loss.

`portfolio_transactions` is the immutable operation record and links one accounting journal.
Monetary journals contain at least two signed movements that sum to zero per currency. Positive
and negative signed movements are not negative debit/credit columns; Atlas does not persist
separate debit or credit values. Non-monetary split adjustments have no fabricated cash journal.

`portfolio_positions` is a lock-protected query projection. Immutable transactions remain the
rebuild authority. Portfolio, transaction, ledger, position, and audit changes share one
PostgreSQL transaction.

## Consequences

- No second authentication, tenancy, portfolio, or ledger architecture exists.
- No mutable cash balance is authoritative; cash derives from journal entries.
- The projection can be rebuilt and checked against transaction sequence.
- No broker account, order, venue, settlement, payment, or customer-fund concept is introduced.
- Production/public use remains prohibited.
