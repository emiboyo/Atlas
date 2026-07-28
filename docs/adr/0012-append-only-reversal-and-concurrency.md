# ADR 0012: Append-only reversal, idempotency, and concurrency

- **Status:** Accepted for Milestone 4 private development
- **Date:** 2026-07-28

## Decision

Every financial mutation requires a bounded `Idempotency-Key`. Atlas stores a SHA-256 request
fingerprint under a tenant/portfolio/key unique constraint. An identical replay returns the
original result; changed content returns `409 idempotency_conflict`.

The posting workflow locks the portfolio row before checking idempotency, cash, sequence, and
position state. Listing positions are also loaded `FOR UPDATE`. This serialises mutations within
one portfolio, prevents duplicate sequence allocation, overspend, oversell, and duplicate
reversal, and remains effective across processes because it uses PostgreSQL rather than memory.

Posted corrections are compensating `reversal` transactions. Original transactions and ledger
entries remain. A unique reversal link permits one reversal only. Database triggers prohibit
transaction deletion and any posted-field update other than the controlled `posted → reversed`
status change after the compensating record exists. Valuation lines, snapshots, and audit events
are append-only.

Deadlock, integrity, and database concurrency failures return a bounded `409
concurrency_conflict`; the whole database transaction rolls back.

## Consequences

The locking scope favours financial correctness over maximum write concurrency. Independent
portfolios remain concurrent. Higher-volume sharding or event streaming is deferred and cannot
weaken these invariants.
