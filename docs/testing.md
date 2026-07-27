# Testing and quality gates

Identity tests cover local JWT verification, registered-claim failures, unknown keys, disabled
Clerk fail-closed behavior, webhook signature/timestamp validation, request mass-assignment,
profile validation, user lifecycle rejection, recent-authentication deactivation, permission
matrix behavior, identity schema constraints, protected frontend fallback, and identity-only
dashboard contracts.

Migration acceptance requires PostgreSQL:

```powershell
python -m alembic -c packages/database/alembic.ini upgrade 20260727_0003
python -m alembic -c packages/database/alembic.ini downgrade 20260724_0002
python -m alembic -c packages/database/alembic.ini upgrade 20260727_0003
```

CI uses a disposable PostgreSQL service and synthetic credentials. No test may contact Clerk,
Stripe, AWS, a broker, an exchange, or another external provider.

Run commands from the repository root with Node.js 22.14.0, pnpm 10.12.1, and an activated Python
3.12.10 virtual environment.

## JavaScript and TypeScript

```powershell
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

The web test verifies rendered homepage behavior. The shared-package test verifies its public
contract. The UI package tests its variant and caller-class contracts.

## Python

```powershell
python -m ruff format --check apps packages/database
python -m ruff check apps packages/database
python -m mypy apps/api/src packages/database/atlas_database
python -m pytest --cov=apps.api.src --cov=packages.database.atlas_database --cov-report=term-missing --cov-fail-under=80
```

The suite uses in-process fakes and mocks. It must not call Clerk, Stripe, AWS, brokers, exchanges,
or market-data services. Tests cover endpoint health, degraded readiness, request IDs, structured
errors, authentication verification, webhook signature handling and idempotency, configuration
safety, and database metadata invariants.

## Infrastructure and containers

```powershell
terraform -chdir=infrastructure/aws fmt -check -recursive
terraform -chdir=infrastructure/aws init -backend=false -input=false
terraform -chdir=infrastructure/aws validate
docker compose config --quiet
docker compose up --build --wait
```

`terraform validate` does not create resources. Do not run `terraform apply` as part of a pull
request or local foundation audit.

## Database integration

With Compose healthy:

```powershell
python -m alembic -c packages/database/alembic.ini upgrade head
python -m alembic -c packages/database/alembic.ini downgrade base
python -m alembic -c packages/database/alembic.ini upgrade head
```

An offline Alembic SQL generation pass is useful but does not replace executing migrations on
PostgreSQL because functions, triggers, constraints, and downgrade behavior require the real
database engine.

## Test-writing standard

- Assert externally observable behavior or a meaningful invariant.
- Use deterministic clocks, identifiers, and provider fakes.
- Never use `assert True` or tests that only duplicate implementation statements.
- Verify tenant boundaries, monetary precision, idempotency, and append-only behavior at the
  database level when those concerns are changed.
- Add regression coverage with every repair.
