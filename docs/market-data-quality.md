# Market-data quality

Provider results pass through one central quality service before API use or persistence.
Timestamps must be timezone-aware and within the configured future tolerance. Currency must be
an uppercase three-letter code matching the listing. Provider symbol and venue must match the
stored mapping. Missing provenance, identity mismatches and invalid timestamps are rejected;
values are never silently converted or remapped.

Supported labels are `live`, `delayed`, `end_of_day`, `cached`, `stale`, `simulated`, and
`unavailable`. Caching cannot make data live. The server computes `stale_after`; an older
non-simulated observation becomes stale. Fixture data remains simulated regardless of age.
Provider and receipt timestamps are retained. Unknown bid, ask, delay, or other values remain
absent. Atlas performs no currency conversion or interpolation.

A previously validated quote may be used after provider failure only while its separately keyed
stale shadow remains within `ATLAS_MARKET_QUOTE_STALE_FALLBACK_TTL_SECONDS`. Atlas marks that
response `stale` with `is_stale=true`; after shadow expiry, it returns the provider error.

Pydantic and database controls reject negative prices/volume, reversed periods, high below low,
open/close outside the range, duplicates, unsupported intervals, timezone-naive or abusive
ranges, currency mismatch where established, and malformed provider data. Trimming whitespace is
the only material input normalisation.

Fixtures use fictional catalogue names and venues, deterministic values, and fixed timestamps.
They do not imitate current prices. Production accuracy, entitlement, licensing, and
redistribution remain unresolved and production use is prohibited.
