# ADR 0003: Tenant-safe financial records and double-entry ledger

- Status: Accepted
- Date: 2026-07-24

## Context

Atlas requires precise, auditable financial state across multiple asset classes and currencies.
Mutable balances and application-only tenant filters would create unacceptable reconciliation
and isolation risks.

## Decision

Use PostgreSQL `NUMERIC(38,18)` for financial quantities and signed double-entry journal postings
as the durable accounting source. Position records are immutable derived snapshots. Every
tenant-owned relationship uses a composite foreign key containing `tenant_id`. Ledger entries
are append-only, and deferred database triggers require posted transactions to contain at least
two entries and balance independently per currency.

Corrections use reversing transactions. External ingestion uses tenant-scoped idempotency keys.

## Consequences

Financial history is reproducible and cross-tenant references fail even if application checks
are defective. Writes require atomic multi-row transactions. Multi-currency activity must use
explicit clearing or valuation accounts so each currency balances. Database triggers are
PostgreSQL-specific and require integration testing against the real engine.
