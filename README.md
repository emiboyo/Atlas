# Atlas AI

Milestone 3 has a Conditional Pass under private-development controls. Milestone 4 private
development is authorised only for simulated portfolio accounting and read-only descriptive
analytics under `docs/milestone-4-governance.md` and ADR 0009. Production, public access, live
providers, real money, trading, custody, advice, customer funds, and Milestone 5 remain
prohibited.

> The Intelligent Investment Operating System.

Atlas AI is a production-oriented foundation for a global investment platform. This repository
contains independently deployable web and API applications, shared packages, local infrastructure,
cloud foundations, tests, and delivery automation. Its financial behavior is limited to governed
simulated portfolio accounting and descriptive read-only analytics.

## Architecture

Identity and tenancy are split across Clerk and Atlas. Clerk authenticates users and signs
sessions; FastAPI verifies those tokens and authorises access using the local Atlas user,
workspace, membership, and permission model. See `docs/identity-architecture.md`,
`docs/authorisation-model.md`, and `docs/onboarding.md`.

```text
                         ┌──────────────────────────────┐
                         │ Next.js / Vercel             │
                         │ Web, SSR, Clerk, Stripe UI   │
                         └──────────────┬───────────────┘
                                        │ HTTPS / JSON
                         ┌──────────────▼───────────────┐
                         │ FastAPI / AWS                │
                         │ /api/v1, DI, errors, logs    │
                         └──────────┬──────────┬────────┘
                                    │          │
                         ┌──────────▼───┐  ┌───▼──────────┐
                         │ PostgreSQL   │  │ Redis         │
                         │ SQLAlchemy   │  │ Cache/coord.  │
                         └──────────────┘  └──────────────┘
```

The repository begins as a modular monolith with hard package boundaries. This preserves
transactional consistency and delivery speed without preventing later service extraction.
The frontend and backend already have separate build and deployment units.

Key platform decisions:

- **Next.js App Router** provides server rendering, modern React, and first-class Vercel delivery.
- **FastAPI + async SQLAlchemy** provides typed OpenAPI contracts and non-blocking data access.
- **PostgreSQL** is the durable system of record; **Redis** is ephemeral cache and coordination.
- **Clerk** and **Stripe** are represented as configuration boundaries only; flows come later.
- **JSON logs, request IDs, Prometheus metrics, liveness, and readiness** are foundational.
- **pnpm + Turborepo** provides reproducible workspace installs and dependency-aware task caching.
- **Docker Compose** is for local integration; managed AWS services are the production target.

More detail: [architecture](docs/architecture.md), [security](docs/security.md), and
[authentication and authorization](docs/authentication-and-authorization.md).

The persistence contract is documented in the
[financial domain model](docs/financial-domain-model.md) and
[data classification](docs/data-classification.md).
Stripe integration boundaries are described in
[payments architecture](docs/payments-architecture.md).

Milestone 4 adds tenant-isolated simulated accounting on the existing ledger:
currency-specific virtual cash, immutable paper transactions, weighted-average long-only
positions, compensating reversals, explicit valuation provenance/completeness, and descriptive
non-advisory analytics. See [portfolio architecture](docs/portfolio-architecture.md),
[accounting rules](docs/simulated-portfolio-accounting.md), and
[portfolio threat model](docs/portfolio-threat-model.md).

## Prerequisites

- Node.js 22.14.0 (see `.nvmrc` and `.node-version`)
- pnpm 10.12.1 through Corepack
- Python 3.12.10 (see `.python-version`)
- Docker Engine with Compose v2
- Git

## Install

### Automated

Windows PowerShell:

```powershell
.\scripts\bootstrap.ps1
```

macOS or Linux:

```sh
./scripts/bootstrap.sh
```

### Manual

```sh
corepack enable
corepack prepare pnpm@10.12.1 --activate
pnpm install --frozen-lockfile
python -m venv .venv
```

Activate the virtual environment, then install the pinned Python dependencies:

```sh
# macOS/Linux
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r apps/api/requirements-dev.txt
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r apps/api/requirements-dev.txt
```

Copy the templates before running outside Compose:

```sh
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
```

Replace example secrets. Never use the Compose password or test credentials in shared or
production environments.

## Run

### Entire stack with Docker

```sh
docker compose up --build
```

| Service            | URL                                |
| ------------------ | ---------------------------------- |
| Web                | http://localhost:3000              |
| API v1             | http://localhost:8000/api/v1/      |
| Swagger UI         | http://localhost:8000/docs         |
| ReDoc              | http://localhost:8000/redoc        |
| OpenAPI schema     | http://localhost:8000/openapi.json |
| Liveness           | http://localhost:8000/health/live  |
| Readiness          | http://localhost:8000/health/ready |
| Prometheus metrics | http://localhost:8000/metrics      |

Protected simulated portfolio UI: `http://localhost:3000/app/portfolios`.

Stop services with `docker compose down`. Add `--volumes` only when you intentionally want to
delete local PostgreSQL and Redis data.

### Native development

Start PostgreSQL and Redis through Compose, then run the applications with reload:

```sh
docker compose up postgres redis
pnpm dev
```

The root `dev` task runs the Next.js development server. Start the API in another terminal:

```sh
pnpm api:dev
```

The application examples use `localhost` for native development. Compose injects the internal
service names `postgres` and `redis` into the API container.

## Test and verify

```sh
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build

ruff format --check apps packages/database
ruff check apps packages/database
mypy apps/api/src packages/database/atlas_database
pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing
docker compose config --quiet
```

The cross-platform `scripts/check.*` scripts run the standard local quality gate. GitHub Actions
runs independent lint, test, application build, and container build workflows on pull requests
and pushes to `main`.

## Database migrations

Schema ownership lives in `packages/database`.

```sh
alembic -c packages/database/alembic.ini revision --autogenerate -m "describe change"
alembic -c packages/database/alembic.ini upgrade head
alembic -c packages/database/alembic.ini downgrade -1
```

Every migration must be reviewed for locks, data loss, backward compatibility, and rollback
behavior. Deploy expand-and-contract schema changes for zero-downtime releases.

## Deployment

### Web on Vercel

Import the repository, select `apps/web` as the project root, and configure variables from
`apps/web/.env.example`. Use separate Clerk and Stripe instances per environment. Vercel uses its
native Next.js output; the Docker build explicitly enables standalone output for its runtime image.

### API and data on AWS

The validated Terraform stack under `infrastructure/aws` establishes:

- FastAPI container in ECS Fargate behind ALB and AWS WAF
- Amazon RDS for PostgreSQL with Multi-AZ, encryption, PITR, and connection pooling
- Amazon ElastiCache for Redis with encryption and automatic failover
- ECR for immutable container images
- Secrets Manager and KMS for credentials and encryption keys
- CloudWatch logs, WAF/ALB access logs, metrics, alarms, and dashboards
- Encrypted AWS Backup vaults with cross-region recovery copies
- GitHub OIDC deployment with immutable images and pre-deployment migrations

Cloud resources must be promoted by a protected CI environment using short-lived OIDC
credentials. Compose is never a production deployment mechanism. See
[deployment guidance](docs/deployment.md).

## Coding standards

- Keep application layers pointed inward: routes → use cases → domain; adapters implement ports.
- Use strict types. `any`, broad exception suppression, and unsafe casts require written rationale.
- Inject databases, caches, clocks, and external providers. Domain behavior remains deterministic.
- Return stable, machine-readable error codes; never expose stack traces or internal details.
- Write structured events, not prose logs. Never log credentials, payment data, tokens, or PII.
- Tests accompany behavior and contract changes; critical financial calculations require property
  and invariant tests when introduced.
- UI must meet WCAG 2.2 AA, support keyboard navigation, responsive layouts, and both themes.
- All database changes require migrations; all configuration requires documented templates.

See [coding standards](docs/coding-standards.md).

## Git workflow

1. Branch from an up-to-date `main` using `feat/`, `fix/`, `chore/`, or `docs/`.
2. Make small, cohesive commits using Conventional Commits.
3. Open a pull request with risk, validation, migration, and rollback notes.
4. Require CODEOWNERS review and all GitHub Actions checks.
5. Squash merge after approval; never force-push or commit directly to protected `main`.
6. Release immutable artifacts once, then promote the same artifact through environments.

## Folder structure

```text
atlas-ai/
├── .github/
│   ├── workflows/          # Lint, test, and build pipelines
│   ├── CODEOWNERS
│   └── pull_request_template.md
├── apps/
│   ├── web/                # Next.js application and homepage
│   └── api/                # FastAPI application and tests
├── packages/
│   ├── ui/                 # Shared Shadcn-style React components
│   ├── config/             # Shared Tailwind configuration
│   ├── shared/             # Stable TypeScript contracts and constants
│   ├── database/           # SQLAlchemy base, sessions, Alembic
│   ├── eslint-config/      # Shared flat ESLint configurations
│   └── typescript-config/  # Strict shared TypeScript configurations
├── infrastructure/
│   └── aws/                # Terraform AWS network foundation
├── docker/
│   ├── postgres/           # Local PostgreSQL initialization
│   └── redis/              # Local Redis runtime configuration
├── docs/
│   ├── adr/                # Architecture decision records
│   ├── architecture.md
│   ├── coding-standards.md
│   ├── deployment.md
│   └── security.md
├── scripts/                # Bootstrap and quality-gate scripts
├── docker-compose.yml
├── package.json
├── pnpm-workspace.yaml
├── pyproject.toml
├── requirements.txt
└── turbo.json
```

## Operational endpoints

- `GET /health/live` proves the API event loop is responsive.
- `GET /health/ready` checks PostgreSQL and Redis and returns `503` when unavailable.
- `GET /metrics` exposes Prometheus-format process and request metrics.
- Every API response carries `X-Request-ID`; inbound IDs are preserved for distributed tracing.
- Swagger and ReDoc derive from the same OpenAPI contract used by clients.

## Developer guides

- [Local development](docs/local-development.md)
- [Testing](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release readiness](docs/release-readiness.md)
- [Milestone 1 foundation audit](docs/milestone-1-audit.md)

## License

Proprietary. Copyright © 2026 Atlas AI.

## Next steps — approval required

These are intentionally not implemented:

1. Introduce end-to-end OpenTelemetry tracing and approved service-level objectives.
2. Add image signing, SBOMs, dependency scanning, and supply-chain attestations.
3. Define market-data provider contracts, licensing controls, and event architecture.
4. Implement the durable Stripe inbox worker only after commercial and accounting rules are approved.
5. Define KYC, AML, sanctions, suitability, and jurisdictional control boundaries.
6. Execute load, failover, backup-restore, and disaster-recovery exercises.

No business logic should begin until the relevant domain, security, regulatory, and data
architecture decisions are reviewed and approved.

## Read-only market-data foundation

Milestone 3 adds authenticated instrument discovery and tenant watchlists. Instruments, venue
listings, provider mappings, quote observations, and candles use immutable Atlas IDs and
fixed-precision values. The included provider is deterministic simulated development data only.
No trading, orders, recommendations, or real-time claims exist.

```powershell
python -m apps.api.src.market.cli seed-development-data
```

See `docs/market-data-architecture.md`, `docs/instrument-model.md`, and `docs/watchlists.md`.

## Milestone 4 governance boundary

After the Milestone 4 governance decision is committed, private development may cover
tenant-isolated paper portfolios, virtual cash, simulated holdings/transactions, simulated
valuation, append-only auditability, and descriptive read-only analytics. Every financial value
and action must remain explicitly simulated, fixed-precision, idempotent, reversible through
append-only corrections, and separated from real financial connectivity.

This authority does not include production deployment, public users, live market providers,
payments, banking, brokerage, orders, execution, custody, money movement, personalised
recommendations, financial advice, customer funds, or Milestone 5. See
[`docs/milestone-4-governance.md`](docs/milestone-4-governance.md) and
[`ADR 0009`](docs/adr/0009-milestone-4-private-development-authorisation.md).

### Simulated portfolio API

Routes under `/api/v1/portfolios` provide lifecycle/effective permissions, immutable transaction
history/posting/reversal, holdings, explicit valuation snapshots, descriptive
analytics/history/allocation/volatility/drawdown/benchmark, and append-only audit history.
Mutations require active membership, central permission, and idempotency. No arbitrary-ledger,
broker, order, payment, or execution endpoint exists.
