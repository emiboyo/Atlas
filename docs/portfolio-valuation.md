# Simulated portfolio valuation

Valuation resolves holdings and the configured Milestone 3 provider server-side. Each line
retains listing/instrument/venue identity, quantity, weighted-average cost, listing currency,
price when available, provider, provider timestamp, receipt timestamp, status, staleness, market
value, realised P&L, and unrealised P&L.

The response includes virtual cash and subtotals by currency, optional genuine base-currency
total, completeness, missing/stale/unavailable listing IDs, unconverted currencies, bounded
status counts, and sources.

- A missing price is `null`, never zero.
- Unavailable P&L remains `null`.
- Stale/cached/delayed/simulated states are not promoted to current/live.
- Non-base values are not converted or added to a base total.
- Transaction, provider, receipt, valuation, and snapshot timestamps remain distinct.

Snapshots are created only by an explicit idempotent operation. Reads do not write. Snapshot
lines are append-only and preserve provenance. See ADR 0013.
