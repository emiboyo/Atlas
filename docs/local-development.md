# Local development

## Milestone 2 identity configuration

Copy the environment examples and use development-only Clerk values. The API requires issuer and
JWKS URLs for token verification and a separate `whsec_` Svix signing secret for webhook tests.
Only the Clerk publishable key may use a `NEXT_PUBLIC_` variable. Never place a Clerk secret key,
webhook secret, session token, or JWT in the web environment.

Without Clerk configuration, public routes remain available while protected web and API access
fails closed. There is no local authentication bypass. Automated tests use locally generated
signing keys and synthetic webhook signatures and make no Clerk network calls.

## Prerequisites

- Git
- Node.js 22.14.0
- pnpm 10.12.1
- Python 3.12.10
- Docker Engine with Docker Compose v2

Version managers can read `.nvmrc`, `.node-version`, and `.python-version`. On Windows, Corepack
may require an elevated terminal to create shims under `C:\Program Files\nodejs`. If that is not
available, install the pinned pnpm version for the current user and ensure its directory is on
`PATH`.

## First-time setup

```powershell
corepack prepare pnpm@10.12.1 --activate
pnpm install --frozen-lockfile
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r apps/api/requirements-dev.txt
Copy-Item .env.example .env
Copy-Item apps/api/.env.example apps/api/.env
Copy-Item apps/web/.env.example apps/web/.env.local
```

The templates contain local-only credentials and keep Clerk and Stripe disabled. Never replace
them with production credentials on a developer machine or commit any copied environment file.

## Run the complete stack

Start the Docker daemon, then run:

```powershell
docker compose config --quiet
docker compose up --build --wait
```

Apply the schema to the empty local database:

```powershell
.\.venv\Scripts\alembic.exe -c packages/database/alembic.ini upgrade head
```

The services are available at:

- Web: <http://localhost:3000>
- API: <http://localhost:8000/api/v1/>
- Swagger: <http://localhost:8000/docs>
- Liveness: <http://localhost:8000/health/live>
- Readiness: <http://localhost:8000/health/ready>
- Metrics: <http://localhost:8000/metrics>

`health/live` only proves the process is responsive. `health/ready` must return `200` and report
both PostgreSQL and Redis as healthy before the stack is ready.

## Run applications natively

Keep dependencies in Compose:

```powershell
docker compose up --detach --wait postgres redis
```

In one terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn apps.api.src.main:app --reload --host 127.0.0.1 --port 8000
```

In another:

```powershell
pnpm --filter @atlas/web dev
```

The root `.env` uses hostnames appropriate for native execution. Compose overrides them with
container-network service names.

## Migrations

Verify both directions against a disposable local database:

```powershell
.\.venv\Scripts\alembic.exe -c packages/database/alembic.ini upgrade head
.\.venv\Scripts\alembic.exe -c packages/database/alembic.ini downgrade base
.\.venv\Scripts\alembic.exe -c packages/database/alembic.ini upgrade head
```

Never run downgrade against shared or production data without an approved recovery plan.

## Stop and clean

```powershell
docker compose down
```

To deliberately delete local PostgreSQL and Redis data:

```powershell
docker compose down --volumes
```

The second command is destructive and should only be used for disposable local data.

## Simulated market data

```powershell
python -m alembic -c packages/database/alembic.ini upgrade head
python -m apps.api.src.market.cli seed-development-data
```

Seeding is idempotent, performs no network requests, and refuses production mode. Use
`ATLAS_MARKET_DATA_PROVIDER=simulated`; `disabled` exercises the unavailable-provider boundary.
Every value is a deterministic fixture and must remain visibly labelled simulated.
