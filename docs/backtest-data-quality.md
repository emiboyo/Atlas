# Backtest Data Quality

The engine consumes server-resolved `atlas_simulated` daily candles only. Observations are ordered by period and stable identifier and included in a data fingerprint.

The result records missing, stale, unavailable, excluded, and completeness fields. Stale source observations make the result incomplete. An insufficient series fails explicitly; Atlas does not fabricate, interpolate, forward-fill, or relabel observations. The configured missing-data policy is persisted with the immutable run, although the initial runner fails insufficient datasets rather than synthesizing alternative histories.

Benchmark return is descriptive buy-and-hold change over the selected historical period when at least two benchmark observations are available. The benchmark must use the same explicit currency. Comparison responses flag differing periods or currencies as not directly comparable and do not normalize them.

Cached or stale data is never described as live or contemporaneous.
