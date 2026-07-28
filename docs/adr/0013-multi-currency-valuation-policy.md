# ADR 0013: Multi-currency valuation and snapshot policy

- **Status:** Accepted for Milestone 4 private development
- **Date:** 2026-07-28

## Decision

Portfolio base currency, transaction currency, listing currency, account currency, and valuation
line currency are explicit. Atlas creates an internal currency sub-ledger only after a valid
simulated transaction requests that supported ISO currency. Listing currency must exactly match a
simulated holding transaction.

Atlas never assumes parity and performs no implicit FX conversion. Virtual cash, holding value,
allocation, and exposure remain grouped by original currency. If any non-base currency has value,
`base_currency_total` is absent, completeness is `incomplete`, and unconverted currencies are
listed.

Valuation uses the server-selected Milestone 3 provider and retains provider timestamp, receipt
timestamp, data status, source reference, and valuation timestamp. Missing stays missing; stale
stays stale. Explicit snapshot creation requires idempotency and creates append-only snapshots and
lines. Page reads do not create unbounded snapshots.

## Consequences

Cross-currency portfolios remain useful without false totals. A future provenanced FX conversion
service requires separate authorisation and must not overwrite original-currency values.
