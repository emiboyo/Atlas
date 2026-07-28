# Descriptive simulated portfolio analytics

Atlas provides descriptive allocation by listing and asset class, concentration/largest
positions, realised and unrealised simulated P&L, value history, percentage change, historical
volatility, maximum drawdown, benchmark comparison, currency exposure, and data completeness.

Volatility is sample standard deviation of consecutive available snapshot returns. Maximum
drawdown is the worst peak-to-subsequent-value percentage decline. Responses state the time
range, snapshot frequency, observation count, missing-data policy, simulation status, and
informational-only disclaimer. Fewer than the required observations returns `null`.

Benchmark comparison uses a server-resolved Atlas listing, persisted daily Milestone 3 candles,
and dates aligned with portfolio snapshots. Missing dates and source status counts remain
visible. Atlas draws no conclusion about which investment is better.

These outputs do not provide a recommendation, quality score, expected return, optimisation,
target allocation, suitability decision, prediction, guarantee, or advice. Sharpe ratio, VaR,
CVaR, and predictive models are not implemented.
