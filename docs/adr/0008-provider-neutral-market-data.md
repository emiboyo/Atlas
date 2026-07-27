# ADR 0008: Provider-neutral listing-based market data

- Status: Accepted
- Date: 2026-07-27

## Context

Ticker symbols are neither immutable nor globally unique. Vendors use incompatible symbols,
venue codes, interval support, licensing terms, timestamps, and response shapes. Atlas must not
bind durable identity to one vendor or misrepresent fixtures as live information.

## Decision

Atlas instruments and listings use separate immutable UUIDs. An instrument describes the
economic object; a listing binds it to an exchange, symbol, and currency. Provider mappings are
separate. Quotes and candles attach to listings and preserve provider, provider timestamp,
receipt timestamp, currency, and explicit data status.

Services depend on a typed `MarketDataProvider`. The only enabled adapter is deterministic
`atlas_simulated`; the external boundary fails safely as unavailable. Financial values use
`NUMERIC(38,18)` or safe integers. Observations have deterministic uniqueness. Redis is an
optional bounded cache; provenance remains authoritative.

## Consequences

- Identical symbols can exist on multiple venues.
- Vendors can be replaced without changing Atlas IDs or API contracts.
- Currency conversion, interpolation, advice, and silent provider fallback are absent.
- Fixtures always retain simulated and non-advisory labelling.
- Production provider licensing and selection remain future decisions.
