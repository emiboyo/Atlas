# Architecture

## System context

Atlas is a modular monolith at the application boundary, with explicit package
boundaries that allow high-load or independently governed capabilities to become
services when operational evidence justifies it.

```text
Browser → Vercel / Next.js → FastAPI on AWS → PostgreSQL
                                 │          ↘ Redis
                                 ├─ Clerk (identity)
                                 └─ Stripe (payments)
```

## Boundaries

- `apps/web` owns presentation, server rendering, and browser-facing composition.
- `apps/api` owns HTTP contracts, orchestration, authorization enforcement, and use cases.
- `packages/ui` owns reusable, accessible Shadcn-style components.
- `packages/shared` owns stable cross-application TypeScript contracts.
- `packages/database` owns persistence primitives and schema migrations.
- `infrastructure` owns declarative cloud resources; `docker` owns local runtime configuration.

## Design decisions

1. **Versioned API from day one.** `/api/v1` protects clients from breaking contract changes.
2. **Async I/O.** FastAPI, SQLAlchemy, asyncpg, and Redis share a non-blocking request path.
3. **Typed configuration.** Invalid settings fail during startup and secrets are redacted.
4. **Observability as a platform concern.** JSON logs, request correlation, Prometheus metrics,
   liveness, and dependency-aware readiness exist before business features.
5. **Portable containers.** Images run as non-root users with immutable filesystems in Compose.
6. **Managed production services.** Vercel hosts Next.js; AWS should use ECS/Fargate, RDS
   PostgreSQL, ElastiCache Redis, Secrets Manager, ALB, WAF, and CloudWatch/OpenTelemetry.

## Financial persistence

Tenant-owned relationships are protected with composite tenant foreign keys. Financial amounts
use fixed-precision decimals, positions are immutable snapshots, and the journal uses append-only
double-entry postings with deferred database-enforced balance validation. See
[financial domain model](financial-domain-model.md) and [data classification](data-classification.md).

Stripe is isolated behind a verified webhook inbox. Customer and subscription records are
projections, while financial effects remain in the Atlas double-entry ledger. See
[payments architecture](payments-architecture.md).
