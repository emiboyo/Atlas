# Backtest Integrity

Completed historical evidence is immutable and reproducible.

- Strategy versions, events, equity points, results, explanations, and research audits reject update and delete operations at the database layer.
- Completed runs reject mutation and deletion.
- Tenant-qualified foreign keys prevent a child record from crossing tenant boundaries.
- Unique sequence constraints preserve event and equity ordering.
- A run, its events, equity series, result, and completion audit commit atomically.
- Idempotency keys are scoped to the strategy or run and bound to request fingerprints.
- Configuration, data, input, output, and result fingerprints provide reconstruction evidence.

Strategy rows are locked during version and run creation. Concurrent identical idempotent requests converge on one effect; conflicting reuse returns a stable conflict. PostgreSQL, not SQLite, is the authority for these guarantees.

Historical simulation cannot modify Milestone 4 portfolios. There is no foreign key or service call from the research engine to portfolio transactions, ledgers, positions, brokers, or payment systems.
