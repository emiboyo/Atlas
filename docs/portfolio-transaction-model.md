# Simulated portfolio transaction model

Permitted types are `virtual_deposit`, `virtual_withdrawal`, `simulated_buy`, `simulated_sell`,
`simulated_dividend`, `simulated_fee`, `simulated_split_adjustment`, and `reversal`. Status is
server-assigned `posted` or controlled `reversed`; there is no pending order lifecycle.

Each record retains immutable Atlas and tenant/portfolio IDs, deterministic sequence,
idempotency key, request fingerprint, explicit currency, optional Atlas listing, fixed-precision
quantity/price/amounts, separate effective/recorded/created timestamps, actor, linked ledger
journal, safe reason/metadata, simulation flag, and optional original-reversal link.

Clients cannot provide status, tenant ownership, realised P&L, account balance, market-data state,
ledger entries, broker identifiers, execution venues, payment credentials, or settlement data.
Extra Pydantic fields are forbidden and PostgreSQL constraints independently enforce the durable
shape.

Corrections never edit economics or delete history. See ADR 0012.
