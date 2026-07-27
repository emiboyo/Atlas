# Market-data quality

Supported labels are `live`, `delayed`, `end_of_day`, `cached`, `stale`, `simulated`, and
`unavailable`. Caching cannot make data live. The server computes `stale_after`; an older
non-simulated observation becomes stale. Fixture data remains simulated regardless of age.
Provider and receipt timestamps are retained. Unknown bid, ask, delay, or other values remain
absent. Atlas performs no currency conversion or interpolation.

Pydantic and database controls reject negative prices/volume, reversed periods, high below low,
open/close outside the range, duplicates, unsupported intervals, timezone-naive or abusive
ranges, currency mismatch where established, and malformed provider data. Trimming whitespace is
the only material input normalisation.

Fixtures use fictional catalogue names and venues, deterministic values, and fixed timestamps.
They do not imitate current prices. Production accuracy, entitlement, licensing, and
redistribution remain unresolved and production use is prohibited.
