# ADR 0015: Deterministic Historical Backtest Engine

- Status: Accepted for private development
- Date: 2026-07-28

## Decision

Use a pure, synchronous Python engine with Decimal arithmetic, ordered Atlas-owned simulated candles, explicit execution/fee/slippage/sizing assumptions, immutable inputs, and canonical fingerprints. Persist all derived evidence atomically.

## Consequences

Replays are inspectable and independent of network, wall-clock time, randomness, brokers, portfolios, and external models. Throughput is intentionally limited; distributed execution is deferred and not authorised.
