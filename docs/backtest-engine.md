# Deterministic Backtest Engine

The Milestone 5 engine evaluates a bounded, long-only simple-moving-average crossover over ordered daily historical observations.

Signals are calculated from data available at the decision index. `next_open` and `next_close` execute on the following observation; `same_close` executes at the current close as an explicit research assumption. No future observation contributes to a past signal. End-of-period liquidation is deterministic.

All price, quantity, cash, fee, slippage, return, drawdown, turnover, and volatility calculations use Python `Decimal`; PostgreSQL uses `numeric(38,18)`. The engine supports zero or fixed/percentage fees, zero or fixed-basis-point slippage, and fixed-cash, cash-percentage, or fixed-quantity sizing. Cash and positions cannot become negative.

Canonical JSON fingerprints cover configuration and input observations. The result checksum covers derived events, equity points, and metrics. Engine and software versions are stored on every run. Identical inputs therefore produce the same ordered evidence without network calls, current-time input, randomness, or unordered iteration.

Initial scope deliberately excludes stop-loss, take-profit, shorting, leverage, multi-asset strategies, and portfolio rebalancing. These are not silently approximated.
