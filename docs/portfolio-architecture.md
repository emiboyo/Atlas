# Simulated portfolio architecture

## Boundary

Milestone 4 is private-development paper accounting only. Every response and protected screen is
classified as simulated. Virtual cash has no monetary value; transactions cannot reserve funds,
submit orders, contact external services, or represent legal assets or liabilities.

```text
protected /api/v1 route
  -> active Atlas user
  -> active tenant membership + central portfolio permission
  -> portfolio row lock + idempotency check
  -> Decimal invariant calculation
  -> immutable portfolio transaction
  -> balanced existing-ledger journal
  -> deterministic position projection
  -> append-only portfolio audit event
  -> one PostgreSQL commit
```

## Aggregate and storage

- `portfolios`: tenant reporting boundary, explicit base currency, optimistic version, active or
  archived lifecycle.
- `portfolio_accounts`: portfolio/currency/account-role link to the existing `ledger_accounts`.
- `portfolio_transactions`: ordered immutable simulated operation and request fingerprint.
- `ledger_transactions` and `ledger_entries`: existing accounting source; deferred triggers
  enforce per-currency balance.
- `portfolio_positions`: lock-protected weighted-average projection by listing.
- `portfolio_valuation_snapshots` and lines: explicit, idempotent, append-only observations.
- `portfolio_audit_events`: bounded append-only operation evidence.

Cross-tenant composite foreign keys backstop application checks. Posted history uses `RESTRICT`,
not cascading deletion. There is no public delete endpoint.

## Service boundaries

Routes contain HTTP translation only. Repositories own parameterised SQL. `PortfolioService`
owns lifecycle, `TransactionPostingService` owns financial invariants and reversals,
`PortfolioQueryService` owns valuation and descriptive analytics, and `PortfolioAuthorisation`
integrates the existing central permission service.

## Concurrency

The portfolio row is the aggregate serialization lock. Position rows receive additional
`FOR UPDATE` protection. Unique idempotency, sequence, ledger, reversal, and position constraints
are database backstops. See ADR 0012.
