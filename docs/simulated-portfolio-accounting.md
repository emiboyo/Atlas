# Simulated portfolio accounting

## Account roles and journal rules

| Simulated event    | Positive signed movement                         | Offset movement                                      |
| ------------------ | ------------------------------------------------ | ---------------------------------------------------- |
| Virtual deposit    | Virtual cash                                     | Simulated capital                                    |
| Virtual withdrawal | Simulated capital                                | Virtual cash                                         |
| Simulated buy      | Simulated investment cost; simulated fee expense | Virtual cash                                         |
| Simulated sell     | Virtual cash; simulated fee/loss where relevant  | Investment cost; simulated realised gain if relevant |
| Dividend           | Virtual cash                                     | Simulated dividend income                            |
| Fee                | Simulated fee expense                            | Virtual cash                                         |
| Split              | No monetary journal                              | Quantity-only append-only adjustment                 |
| Reversal           | Exact opposite original journal movements        | Exact opposite position effects                      |

Signed movements sum to zero independently per currency. Atlas does not store negative debit or
credit columns. Posted cash is the sum of virtual-cash ledger entries, never a manually editable
balance.

## Invariants

Buys/sells require positive quantity; amounts/fees are non-negative; withdrawals and buys cannot
overspend; sells cannot oversell; long-only positions cannot become negative; split ratios are
positive; transaction/listing currencies must match; future timestamps are bounded; archived
portfolios reject mutations; journals balance; idempotency and one-reversal constraints hold.

Any failure rolls back transaction, journal, position, and success audit event together.

## Cost policy

Weighted-average simulated cost excludes separately expensed fees. This is not tax cost basis.
See ADR 0011.

## Rebuild

Apply posted transactions in `(sequence, id)` order. Add stored position quantity, cost, and
realised-P&L deltas, including opposite reversal deltas. The rebuilt projection must match
`portfolio_positions.last_transaction_sequence`; discrepancies are material and are not silently
repaired.
