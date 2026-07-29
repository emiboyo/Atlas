# ADR 0016: Immutable Research Evidence

- Status: Accepted for private development
- Date: 2026-07-28

## Decision

Strategy versions and derived backtest evidence are append-only. PostgreSQL triggers reject updates and deletes, completed runs are immutable, and tenant-qualified foreign keys plus unique sequence and idempotency constraints enforce integrity.

## Consequences

Corrections require a new strategy version or run. Storage grows monotonically and requires a governed retention design before production.
