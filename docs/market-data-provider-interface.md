# Market-data provider interface

Providers expose immutable typed contracts for instrument search/detail, venue reference data,
quotes, candles, health, and rate-limit state. Provider-specific payloads remain inside adapters.

The deterministic provider uses UUID-derived decimal values and fixed January 2026 timestamps.
It supports daily and weekly candles. Every response is `simulated` and states:

> Simulated development data. For software testing only; not real-time market data and not
> investment advice.

The disabled adapter returns `provider_unavailable`. Stable codes include
`provider_timeout`, `provider_rate_limited`, `provider_authentication_failed`,
`provider_response_invalid`, `provider_symbol_not_found`, `unsupported_interval`,
`unsupported_capability`, `provider_currency_mismatch`, `provider_symbol_mismatch`, and
`provider_timestamp_invalid`.

Adapters must validate types/ranges, use bounded timeouts/retries, avoid retry storms, never log
keys or secret-bearing URLs, and never silently switch providers. Credentials remain server-side.
Calls pass through a configurable bounded timeout with at most three retries. Authentication,
rate-limit and invalid-data failures are never retried. Connection failures and timeouts use
deterministic bounded backoff. CI uses fixtures and mocks only.
