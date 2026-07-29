# Historical Strategy Research Architecture

Atlas Milestone 5 is a private-development, tenant-scoped historical research subsystem. It is not an order-management system, portfolio controller, advisory service, or production release.

## Boundary

Authenticated users create research strategy metadata and immutable versions containing a validated `sma_crossover` rule. A synchronous application service resolves Atlas-owned simulated daily candles, executes the pure deterministic engine, and atomically persists the run, simulated events, equity series, result, and audit event. API responses use explicit schemas rather than ORM models.

The browser never supplies roles, status, results, provider identity, provenance, or audit fields. Central permissions and tenant membership are checked for every resource. Cross-tenant absence is concealed as not found.

## Components

- `apps/api/src/research/engine.py`: side-effect-free Decimal calculations.
- `services.py`: authorization, idempotency, locking, orchestration, atomic persistence.
- `repositories.py`: bounded SQLAlchemy queries and server-controlled market-data source.
- `routes.py` and `schemas.py`: `/api/v1/research` HTTP contract.
- `packages/database/.../research.py`: tenant-qualified relational integrity.
- `apps/web/src/app/app/research`: protected research screens.

Only `atlas_simulated` daily observations are eligible. Currency must match explicitly; Atlas performs no silent conversion. The implementation has no broker, exchange, custody, deposit, withdrawal, live-data, or external-model connector.

## Lifecycle and isolation

Strategies may be active or archived. Versions are append-only. Runs move to completed only after every derived record is ready in the same transaction. Completed runs and all evidence tables are protected by PostgreSQL triggers. Strategy row locks serialize version and run creation, while unique idempotency constraints prevent duplicate effects.

See [backtest integrity](backtest-integrity.md), [threat model](research-threat-model.md), and [ADR 0014](adr/0014-milestone-5-private-development-authorisation.md).
