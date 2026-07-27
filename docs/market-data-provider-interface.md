# Market-data provider interface

Providers expose typed quote retrieval, candle retrieval, and health checks. Future adapters may
add reference search and rate-limit state without leaking vendor payloads.

The deterministic provider uses UUID-derived decimal values and fixed January 2026 timestamps.
It supports daily and weekly candles. Every response is `simulated` and states:

> Simulated development data. For software testing only; not real-time market data and not
> investment advice.

The disabled adapter returns `provider_unavailable`. Stable future codes include
`provider_timeout`, `provider_rate_limited`, `provider_authentication_failed`,
`symbol_not_found`, `unsupported_interval`, and `malformed_provider_response`.

Adapters must validate types/ranges, use bounded timeouts/retries, avoid retry storms, never log
keys or secret-bearing URLs, and never silently switch providers. Credentials remain server-side.
CI uses fixtures and mocks only.
