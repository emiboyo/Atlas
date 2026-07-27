# Market-data threat model

Remediation controls provider impersonation and poisoning through server-owned provider selection,
stored symbol/venue mappings, currency equality, timezone-aware future tolerance, mandatory source
references, immutable typed results, bounded execution, collision-resistant cache keys and typed
cache validation. Rate-limit, authentication and invalid-response failures are never retried.

| Threat                          | Control                                                            |
| ------------------------------- | ------------------------------------------------------------------ |
| Ticker collision                | Separate instrument/listing UUIDs and venue-symbol uniqueness      |
| Watchlist IDOR                  | Verified user, local membership, central permission, concealed 404 |
| Client role/tenant manipulation | PostgreSQL membership authority                                    |
| Provider-key disclosure         | Server-only configuration; no keys in browser                      |
| Search injection                | Bounded query, escaped wildcards, SQLAlchemy parameters            |
| Invalid provider values         | Typed parsing plus decimal/range/database constraints              |
| Simulated/stale shown live      | Explicit status and server freshness                               |
| Cache collision/poisoning       | Versioned provider/listing-aware keys                              |
| Cache outage                    | Safe miss; authoritative source remains                            |
| Provider outage/rate limit      | Stable errors and bounded future retries                           |
| Duplicate observations          | Deterministic uniqueness; no silent overwrite                      |
| XSS in names/notes              | Bounded strings rendered as React text                             |
| Search/range abuse              | Query, page, range, list, item, and provider-call caps             |
| Advice inference                | Neutral language; no rankings, signals, targets, or trade controls |

Residual risks include vendor licensing, entitlements, correctness, corporate actions,
production rate plans, and multi-provider reconciliation. They remain deferred.
