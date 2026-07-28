# ADR 0011: Weighted-average simulated cost

- **Status:** Accepted for Milestone 4 private development
- **Date:** 2026-07-28

## Decision

Milestone 4 uses deterministic weighted-average simulated cost by listing and currency.

- A simulated buy adds quantity and gross simulated acquisition value.
- Its separately recorded simulated fee is expensed and excluded from average cost.
- A partial sell removes `average_cost_per_unit × quantity`.
- Realised simulated P&L is net simulated proceeds after fee minus removed cost.
- A complete sale closes quantity, cost, and average cost at zero.
- A split changes quantity and average unit cost proportionally while preserving total cost.
- A compensating reversal applies the stored opposite quantity, cost, and realised-P&L deltas.

All values use `Decimal` and PostgreSQL `NUMERIC(38,18)` with half-even quantisation. The method is
informational paper accounting, not tax cost basis, tax advice, or a jurisdictional method.

## Consequences

Fees are visible and deterministic; they are not silently capitalised. Fractional residual,
jurisdictional tax-lot, wash-sale, and tax reporting rules remain out of scope.
