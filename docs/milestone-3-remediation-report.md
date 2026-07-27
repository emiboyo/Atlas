# Milestone 3 Audit Remediation — Provider Contract, Data Quality, Operations,

# Frontend Permissions and Test Coverage

## 1. Remediation title

Atlas AI Milestone 3 Audit Remediation.

## 2. Date

2026-07-27.

## 3. Branch

`fix/milestone-3-remediation`.

## 4. Baseline commit

`1c4d379` (`merge: record Milestone 3 audit findings and hardening`). The independently audited
implementation was commit `61e5654`; the authoritative audit result remains **FAIL** until a
separate focused re-audit changes it.

## 5. Audit findings addressed

| Finding    | Severity | Remediation state             |
| ---------- | -------- | ----------------------------- |
| M3-AUD-001 | High     | Remediated; re-audit required |
| M3-AUD-002 | Medium   | Remediated; re-audit required |
| M3-AUD-003 | Medium   | Remediated; re-audit required |
| M3-AUD-004 | Medium   | Remediated; re-audit required |
| M3-AUD-005 | Medium   | Remediated; re-audit required |

## 6. Executive summary

The five blocking findings have corrective code and executable test evidence. Atlas now has a
complete immutable provider-neutral read contract, bounded provider execution, central provider
quality validation, bounded health and stale-quote caching, transactionally controlled
development ingestion with audit events, server-derived watchlist permissions, explicit frontend
market-data states, and the missing backend/frontend test coverage.

**This report records remediation work only. It does not change the independent Milestone 3 audit
result from FAIL. Only a separate focused re-audit may change Milestone 3 acceptance.**

## 7. Files created

- `apps/api/src/market/administration.py`
- `apps/api/src/market/execution.py`
- `apps/api/src/market/ingestion.py`
- `apps/api/src/market/quality.py`
- `apps/api/tests/test_market_remediation.py`
- `apps/web/src/components/market-data-state.tsx`
- `docs/milestone-3-remediation-report.md`

## 8. Files modified

Configuration examples, API market services/routes/schemas/providers/repositories/fixtures/CLI,
market and integration tests, web market/watchlist components and tests, README, and the Milestone
3 architecture, provider, quality, threat-model, authorisation, watchlist, testing, local
development, security, release-readiness, audit, and historical report documents were updated.
No historical migration was modified.

## 9. Provider contract changes

`MarketDataProvider` now exposes typed capabilities for instrument search, instrument detail,
venue reference data, latest quote, historical candles, health, and rate-limit status.
`ProviderInstrument`, `ProviderVenue`, `ProviderListingContext`, `ProviderQuote`,
`ProviderCandleBatch`, `ProviderHealth`, and `ProviderRateLimitStatus` are immutable Pydantic
models that reject unexpected fields. Both the deterministic simulated adapter and disabled
adapter implement the full contract. Provider choice remains server-controlled and no live SDK,
credential, or network adapter was introduced.

## 10. Provider error model

Stable API-safe errors cover `provider_unavailable`, `provider_timeout`,
`provider_rate_limited`, `provider_authentication_failed`, `provider_response_invalid`,
`provider_symbol_not_found`, `unsupported_interval`, `unsupported_capability`,
`provider_currency_mismatch`, `provider_symbol_mismatch`, and
`provider_timestamp_invalid`. Messages contain no raw payload or secret; internal exceptions are
chained. Tests parameterise every stable code, unexpected fields, and retry-after.

## 11. Timeout and rate-limit controls

`ProviderExecutor` applies a configurable `asyncio.timeout`, at most three configured retries,
deterministic bounded backoff, cancellation-safe execution, latency metrics, and failure metrics.
Only timeout and connection failures retry. Authentication, invalid data, unsupported capability,
and rate-limit failures do not retry, preventing rate-limit retry storms.

## 12. Data-quality validation

`ProviderDataQualityService` is the single validation boundary before API use or persistence. It
validates timestamps, currency, listing/provider identity, venue identity, provenance, MIC,
country, timezone, asset class, listing status, venue status, candles, and freshness. It never
silently converts currencies, remaps listings, fabricates missing values, or substitutes a
receipt timestamp for provider time.

## 13. Timestamp tolerance

Provider and received timestamps must be timezone-aware. Provider timestamps beyond
`ATLAS_MARKET_PROVIDER_FUTURE_TIMESTAMP_TOLERANCE_SECONDS` are rejected. Quote and candle
freshness thresholds are separately configurable and calculated server-side. CLI candle ranges
also reject naïve or reversed timestamps before provider execution.

## 14. Currency mismatch handling

Ordinary currencies must be uppercase three-letter codes. Provider currency is compared with the
server-owned listing context. A mismatch raises `provider_currency_mismatch`; the browser cannot
override currency and Atlas performs no silent conversion.

## 15. Provider-symbol mismatch handling

Provider symbol and venue code must match the stored provider mapping. A mismatch raises
`provider_symbol_mismatch`; source provenance remains attached and a provider result cannot
silently remap an Atlas listing.

## 16. Ingestion and upsert controls

Development-only services support reference synchronisation, listing reconciliation, quote
refresh, candle refresh, and provider-mapping upsert. Controlled unique keys make identical
observations idempotent and reject conflicting observations. Quote, candle, and mapping mutation
entry points own rollback on failure. A partial candle batch conflict is tested to prove the
earlier insert and audit event are rolled back.

## 17. Provider-health caching

Health uses typed, provider-scoped SHA-256 Redis keys and a short configurable TTL. Malformed
payloads become misses; Redis failure falls back to a bounded direct provider check; provider
failure becomes safe unavailable status. Tests cover hit, miss, injected-clock expiry, malformed
payload, Redis outage, provider separation, and provider failure behavior.

Quotes use a separately keyed, bounded stale shadow. It is consulted only after provider failure,
is always returned with `data_status=stale` and `is_stale=true`, and is rejected after its own
expiry. It cannot present an old value as current.

## 18. Development commands

The non-production CLI supports `seed-development-data`, `sync-reference-data`,
`reconcile-listings`, `refresh-quote`, `refresh-candles`, and
`upsert-provider-mapping`. Commands require operation identifiers where mutations occur, reject
production execution, use only the configured server-side provider, and expose no HTTP
administration route.

## 19. Audit-event behaviour

Successful mutations append bounded metadata under `market_data.development_seeded`,
`market_data.reference_data_synced`, `market_data.quote_refreshed`,
`market_data.candles_refreshed`, `market_data.provider_mapping_created`, or
`market_data.provider_mapping_updated`. The operation UUID is the audit-event primary key,
providing exactly-once seed audit behavior. Metadata excludes credentials, tokens, raw provider
payloads, and PII. Tests prove seed idempotency, command events, mapping events, successful
ingestion events, and absence of events after conflicts.

## 20. Effective permissions

`GET /api/v1/watchlists/effective-permissions?tenant_id=...` returns bounded booleans derived from
the active tenant membership and central permission matrix. Owner, admin, member, and viewer
permissions are tested. Browser-supplied role or permission values are ignored; suspended,
deactivated, or cross-tenant actors fail through existing membership checks.

## 21. Frontend state handling

The shared `MarketDataState` component explicitly renders simulated, delayed, cached, stale,
unavailable, provider-error, rate-limited, and unsupported-interval states. Simulated data says
“Simulated development data”; stale/unavailable states do not imply freshness; messages contain
no internal detail, advice, trading controls, predictions, or buy/sell semantics.

## 22. Accessibility changes

Watchlist controls have programmatic labels and native keyboard-operable elements. Tests verify
label lookup, focus order, keyboard focus, viewer read-only rendering, owner mutation controls,
and all required market-data messages. Desktop and horizontally scrollable mobile navigation
remain separate labelled navigation regions with valid internal targets.

## 23. Tests added

Executable coverage includes provider capability/error/timeout/retry behavior; timestamps,
currency, symbol, venue and provenance; health cache and stale fallback; search abuse inputs;
watchlist tenant and mutation attacks; effective permission roles; idempotent/conflicting
ingestion, partial rollback and audit events; and frontend permissions, accessibility, and all
eight data states. Automated tests perform no external provider calls.

## 24. Python test and coverage result

Command:

```powershell
python -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
```

Final result: **73 passed**, 6 deprecation warnings, **82.98% coverage**. Ruff format/check and
strict mypy also pass; mypy checked 49 source files.

## 25. Frontend test result

`pnpm test`: all workspace test tasks passed. Web: **16 passed** across 3 files; UI: 2 passed;
shared: 1 passed. `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, and `pnpm build` pass.
Next.js compiled and generated all expected static/dynamic routes.

## 26. Migration result

No migration `0006` was needed: existing immutable observation fields and the audit-event UUID
primary key support the remediation. A fresh PostgreSQL 16.9 database upgraded through every
migration to `20260727_0005`; `alembic current` reported `20260727_0005 (head)` and
`alembic check` reported no new upgrade operations. The Compose database also reports
`20260727_0005`.

## 27. Docker result

`docker compose config --quiet`, full web/API image builds, and
`docker compose up --detach --wait` passed. PostgreSQL, Redis, FastAPI, and Next.js are healthy.
The API runs as `atlas` UID 1001 and web as `nextjs`; both use read-only root filesystems and
`no-new-privileges:true`.

Web/API binding to `0.0.0.0` **is intentional inside their containers** so Docker can publish
their ports for local development. This is not production network authorisation; production
ingress, firewall, TLS, and private-service policy remain future deployment controls.

## 28. Runtime result

Rebuilt Compose runtime checks returned: homepage 200, liveness 200, readiness 200, metrics 200,
OpenAPI 200, and unauthenticated market status 401. Migration head is `0005`; API root is
non-writable. Authenticated deterministic search/detail/quotes/candles, provider errors,
health-cache behavior, future/currency/symbol rejection, permissions, cross-tenant denial,
stale-cache fallback, and audited seeding ran through the local ASGI application against fresh
PostgreSQL with synthetic authentication in the passing integration suite. No live credential or
external provider was used.

## 29. Dependency findings

`python -m pip check` passed and `pip-audit -r apps/api/requirements.txt` reported no known Python
vulnerabilities. `pnpm audit --prod` and `pnpm audit` both report the governed
`GHSA-mh99-v99m-4gvg` / `CVE-2026-14257` `brace-expansion` advisory through the
ESLint/minimatch development chain. The approved private-development exception and controls are
authoritative in [security-risk-exceptions.md](security-risk-exceptions.md) and expire
2026-10-27.

Docker Scout could not scan because Docker Desktop requires Docker ID authentication. The
existing governed `CVE-2026-12087` exception for the unused Perl component inherited from the
official Python slim image therefore remains in force and must be revalidated before production.

## 30. Remaining limitations

- Only deterministic simulated and disabled providers exist; no live provider is approved.
- No provider entitlements, licensing, redistribution, production freshness SLA, or production
  stampede/single-flight strategy is approved.
- Runtime authenticated checks rely on synthetic local authentication, not Clerk production
  credentials.
- Docker Scout requires an authenticated independent rerun.
- Starlette emits six non-blocking deprecation warnings that should be removed in maintenance.
- An independent security review and independent Milestone 3 re-audit remain outstanding.

## 31. Production blockers

Production deployment, public customer access, live trading, real-money investing, custody,
movement of funds, investment management, and handling real customer funds remain prohibited.
The two governed security exceptions, production identity configuration, infrastructure
hardening, market-data licensing/entitlements, operational runbooks, external security review,
and independent milestone acceptance must be resolved first.

## 32. Re-audit readiness

The repository is technically ready for a focused independent Milestone 3 re-audit. The reviewer
must independently rerun the quality, PostgreSQL, Docker, runtime, and dependency checks and
decide whether M3-AUD-001 through M3-AUD-005 can be closed.

### Finding evidence

| Finding    | Corrective implementation                                                     | Code evidence                                               | Test evidence                                                    | Runtime evidence                                               | State                         |
| ---------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------- | ----------------------------- |
| M3-AUD-001 | Complete immutable provider contract, typed safe errors, bounded executor     | `providers.py`, `execution.py`                              | `test_market.py`, `test_market_remediation.py`                   | Rebuilt healthy API; ASGI provider flows                       | Remediated; re-audit required |
| M3-AUD-002 | Central quality boundary, tolerance, identity/currency/provenance enforcement | `quality.py`, `services.py`, `ingestion.py`                 | Quality and integration conflict/rollback tests                  | Simulated quote/candle ASGI flows                              | Remediated; re-audit required |
| M3-AUD-003 | Provider health cache, stale shadow, audited development commands             | `cache.py`, `administration.py`, `ingestion.py`, `cli.py`   | Injected expiry, outage, stale fallback, audit/idempotency tests | Redis/PostgreSQL healthy; seed command exercised in ASGI suite | Remediated; re-audit required |
| M3-AUD-004 | Server-derived effective permissions and explicit data states                 | `services.py`, `routes.py`, watchlist and market components | Role matrix, viewer/owner UI, state/accessibility tests          | Cross-tenant and permission ASGI flows                         | Remediated; re-audit required |
| M3-AUD-005 | Expanded executable security/integration/frontend matrix                      | remediation and integration test files                      | 73 Python tests at 82.98%; 19 workspace frontend/package tests   | Docker/public endpoints and ASGI authenticated runtime         | Remediated; re-audit required |

### Failed-command record

| Command                                                             | Error and root cause                                             | Correction                                                                          | Rerun/final state                                                   |
| ------------------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| System `python -m ruff ...` / `python -m pytest ...`                | System Python lacked repository dev tools                        | Used `.venv312\Scripts\python.exe`                                                  | Targeted and full Python gates pass                                 |
| Combined `pnpm install; format:check; lint; typecheck; test; build` | Two watchlist files needed Prettier; chained Turbo run timed out | Scoped Prettier write; reran gates separately                                       | Every pnpm gate passes                                              |
| PostgreSQL tests at `127.0.0.1:5432`                                | Connected to unrelated local PostgreSQL with different password  | Inspected Compose and avoided altering data                                         | Superseded                                                          |
| PostgreSQL tests at configured Compose host port                    | Docker Desktop did not expose the internal-network service port  | Used a fresh disposable PostgreSQL 16.9 container on a verified free localhost port | 73 passed; 82.98%; Alembic clean                                    |
| First disposable PostgreSQL bind on 55433                           | Port already occupied; container never started                   | Removed only failed temporary container and used verified-free 55439                | Fresh database validation passed                                    |
| `pnpm audit --prod`; `pnpm audit`                                   | Governed `brace-expansion` advisory                              | No unsafe forced upgrade; retained approved development-only exception              | Expected non-zero; production remains prohibited                    |
| `docker scout cves atlas-ai-api:latest ...`                         | Docker ID login required                                         | No credential prompt or bypass attempted                                            | Not validated; governed exception and production prohibition remain |

## 33. Final remediation status

**REMEDIATION COMPLETE — READY FOR INDEPENDENT RE-AUDIT.**

All five remediation findings have corrective implementation and executable evidence. This is
not an independent acceptance decision and does not authorise Milestone 4.

**This conditional technical result applies only to the Milestone 3 read-only market-data and
watchlist foundation. It does not authorise production deployment, public customer access, live
trading, custody, investment management, real-money investing, or handling real customer funds.**
