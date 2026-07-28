# Simulated portfolio threat model

| Threat                                  | Control                                                                 |
| --------------------------------------- | ----------------------------------------------------------------------- |
| Cross-tenant IDOR or guessed UUID       | Active local membership, object concealment, composite tenant FKs       |
| Browser role/tenant/status manipulation | Central server permissions, forbidden extra fields, server resolution   |
| Duplicate financial effects             | Required idempotency, fingerprint, unique constraint, portfolio lock    |
| Concurrent overspend or oversell        | PostgreSQL portfolio/position row locks and transactional rechecks      |
| Destructive correction                  | Compensating reversal, unique original link, append-only triggers       |
| Unbalanced accounting                   | Central posting rules and deferred per-currency balance triggers        |
| Floating-point corruption               | Decimal and `NUMERIC(38,18)`                                            |
| False current or complete valuation     | Explicit stale/missing/unavailable/unconverted states                   |
| Silent FX conversion                    | Original-currency subledgers; absent incomplete base total              |
| Real execution boundary confusion       | No broker/order/payment ports; simulated-only contracts and UI language |
| Confidential data leakage               | Bounded audit metadata; no bodies, notes, holdings, tokens in logs      |
| Unbounded labels/ranges                 | Bounded metrics, pagination, snapshot history, and analytics limits     |

Stop work for an authentication/tenancy bypass, duplicate effects, ledger imbalance, negative
cash/quantity, unsafe reversal, stale-as-current, simulated-as-real, silent conversion, real
connectivity, secret exposure, or an ungoverned Critical/High vulnerability.

Residual risks include private-development authentication fixtures, absence of production RLS,
no browser E2E suite, governed dependency advisories, and no independent Milestone 4 audit.
Production and public access remain prohibited.
