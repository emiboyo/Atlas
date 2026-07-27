# Market-data architecture

Milestone 3 is a provider-neutral, read-only catalogue and observation system. Every market route
requires the Milestone 2 active-user dependency. Reference data is shared across authenticated
users; watchlists require an active tenant membership and central permission.

An instrument UUID identifies an economic object. A listing UUID identifies one venue, symbol,
and currency representation. Observations attach to listings. Provider mappings translate a
listing into a vendor namespace without exposing credentials or changing canonical identity.

`MarketService` calls the typed provider, validates results, derives freshness server-side, and
returns Atlas contracts. No provider-native payload reaches routes or browser code. The
deterministic fixture provider is enabled for private development; the external boundary returns
a stable unavailable error without network access.

PostgreSQL stores exchanges, instruments, listings, mappings, immutable quotes/candles, and
tenant watchlists. Values are decimal, timestamps are UTC, and venue timezone remains reference
metadata. Redis keys use `atlas:market:v1`, provider/listing identity, and bounded TTLs. Cache
failure is a safe miss. Tokens, secrets, unrestricted wildcard invalidation, and background
loops inside web processes are prohibited.

Development seeding is explicit, idempotent, and disabled in production:

```powershell
python -m apps.api.src.market.cli seed-development-data
```
