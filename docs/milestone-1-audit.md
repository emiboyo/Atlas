# Milestone 1 Foundation Audit

> **CURRENT STATUS — CONDITIONAL PASS**
>
> Atlas AI's Milestone 1 technical foundation passed its functional, quality, migration, and
> Docker Compose acceptance gates on 2026-07-25.
>
> This status is conditional on continued compliance with the scope, controls, review dates, and
> expiry dates of the two temporary development-only decisions recorded in
> [`docs/security-risk-exceptions.md`](security-risk-exceptions.md).
>
> **This conditional pass applies only to the Milestone 1 technical foundation.
> It does not authorise production deployment, live trading, custody,
> investment management, or handling real customer funds.**

Initial audit date: 2026-07-24
Latest revalidation: 2026-07-25
Report revised: 2026-07-27
Repository: `C:\Dev\Atlas`
Branch: `chore/milestone-1-audit`
Scope: foundation audit and stabilisation only; no Milestone 2 or investment business logic

## Milestone 1 Governance Status

- Technical status: **CONDITIONAL PASS**
- Risk owner: Adebayo Olaegbe
- Security risk decision: Temporarily approved for private development
- Decision reference:
  [`docs/adr/0006-milestone-1-security-risk-decision.md`](adr/0006-milestone-1-security-risk-decision.md)
- Milestone 2 private development: **Permitted**
- Production deployment: **Prohibited**
- Public customer access: **Prohibited**
- Live trading and real-money investing: **Prohibited**
- Exception expiry date: 2026-10-27
- Independent security review required before production

## Executive Summary

The Milestone 1 foundation is operationally validated. A clean Docker Compose environment was
built without cache and started successfully on Docker Desktop's Linux engine. Web, API,
PostgreSQL, and Redis reached healthy state. Container networking, SQLAlchemy and Redis
connectivity, Alembic upgrade/downgrade/re-upgrade, ledger integrity controls, readiness
degradation and recovery, public foundation endpoints, structured errors, and container security
controls were exercised against the running stack.

The full non-container gate was rerun after the Docker repairs. Frozen installation, formatting,
linting, TypeScript checking, five JavaScript tests, the Next.js production build, Ruff, strict
mypy, 27 Python tests, the 80% coverage gate, Python dependency auditing, Terraform formatting and
validation, workflow YAML parsing, Compose rendering, Alembic head verification, and
`git diff --check` passed. Python coverage was 87.43%.

Two security findings are tracked under formal risk ownership:

1. GHSA-mh99-v99m-4gvg / CVE-2026-14257 affects `brace-expansion` 1.1.16 through the
   ESLint/minimatch development-tool chain. It is not present in the Atlas web runtime path.
2. CVE-2026-12087 affects an unused Perl component in the official Python 3.12.13 slim base image.
   Docker Scout reported no fixed Debian package at validation time. Atlas does not invoke Perl.

Neither finding is silently accepted. Their reachability analysis, compensating controls,
prohibited uses, owners, review dates, expiry dates, and remediation triggers are recorded in
[`docs/security-risk-exceptions.md`](security-risk-exceptions.md). GHSA-mh99-v99m-4gvg /
CVE-2026-14257 was approved temporarily for development-only use by Adebayo Olaegbe on 2026-07-27,
with review due 2026-08-27 and expiry on 2026-10-27. CVE-2026-12087 was approved temporarily for
development-only use by Adebayo Olaegbe on 2026-07-27, with the same review and expiry dates.

No Terraform apply, deployment, cloud resource creation, real credential use, or external request
to Clerk, Stripe, AWS, a broker, an exchange, or a market-data provider was performed.

## Docker Revalidation Evidence

### Preflight

| Command                              | Outcome                                            |
| ------------------------------------ | -------------------------------------------------- |
| `git branch --show-current`          | `chore/milestone-1-audit`                          |
| `git status --short`                 | Existing audit worktree changes preserved          |
| `docker version`                     | Client 29.6.2; Docker Desktop 4.83.0 server 29.6.2 |
| `docker info --format '{{.OSType}}'` | `linux`                                            |
| `docker compose version`             | Docker Compose 5.3.1                               |
| `docker compose config --quiet`      | Exit 0                                             |
| `docker compose ps`                  | Compose service state inspected successfully       |

The required repository paths were confirmed under `C:\Dev\Atlas`. The obsolete OneDrive
repository path was not searched or used.

### Clean build and startup

The following commands were executed from `C:\Dev\Atlas`:

```powershell
docker compose down --volumes --remove-orphans
docker compose build --no-cache
docker compose up --detach --wait
docker compose ps
```

Outcomes:

- The previous containers, networks, and disposable local volumes were removed.
- API and web images built successfully without cache.
- `web`, `api`, `postgres`, and `redis` started and reported healthy.
- Web published host port 3000; API published host port 8000.
- PostgreSQL and Redis were attached only to the internal backend network at runtime.
- Web and API shared the frontend network; API, PostgreSQL, and Redis shared the backend network.
- The final stack was left running and healthy.

After security remediation changed the runtime bases, the affected images were rebuilt without
cache and their services were force-recreated:

```powershell
docker compose build --no-cache api web
docker compose up --detach --force-recreate api web --wait
docker compose ps
```

This completed successfully with all four services healthy.

### Networking and host binding decision

Web and API are intentionally bound by local Compose to `0.0.0.0` inside their containers and
published on host ports 3000 and 8000. This permits browser access from the Docker host and normal
container ingress during local foundation testing. It is an intentional **local-development
decision**, not approval of direct public internet exposure.

Production deployment must place the services behind the approved Vercel/AWS ingress, TLS,
authentication, WAF/rate-limiting, trusted-host, CORS, network-security, and observability
boundaries. The application containers must not be exposed directly to the public internet.

PostgreSQL and Redis use Compose service DNS on the internal backend network. Their local Compose
port declarations are loopback-restricted, and runtime inspection showed no general host
publication. They are not intended for remote access.

### PostgreSQL and Alembic

Commands and checks included:

```powershell
docker compose exec -T postgres pg_isready -U atlas -d atlas
docker compose exec -T api alembic -c packages/database/alembic.ini upgrade head
docker compose exec -T api alembic -c packages/database/alembic.ini current
docker compose exec -T api alembic -c packages/database/alembic.ini downgrade base
docker compose exec -T api alembic -c packages/database/alembic.ini upgrade head
docker compose exec -T api alembic -c packages/database/alembic.ini current
```

Outcomes:

- PostgreSQL accepted connections through the Compose service.
- An API-side SQLAlchemy connection returned database `atlas` and user `atlas`.
- Empty-database upgrade, downgrade to base, and re-upgrade passed.
- Final revision was `20260724_0002 (head)`.
- Catalog inspection found 16 tables, 20 foreign keys, 26 unique constraints, and 54 indexes.
- Ledger amounts use `numeric(38,18)`.
- Audit timestamps use `timestamp with time zone`.
- Balanced ledger insertion and deferred balance validation passed.
- Database triggers rejected ledger-entry update and delete attempts.
- The integrity test transaction was rolled back; no audit rows remained.

### Redis

Commands and checks included:

```powershell
docker compose exec -T redis redis-cli ping
docker compose exec -T redis redis-cli CONFIG GET bind protected-mode port tls-port requirepass
```

An API-container Python check resolved `redis`, connected using the configured Redis URL, issued
`PING`, and queried `DBSIZE`.

Outcomes:

- `redis-cli ping` returned `PONG`.
- The API Redis client returned `True`.
- Redis service-name DNS resolution passed.
- `DBSIZE` returned zero; no business data was stored.
- Redis peer-container access was repaired by disabling protected mode within the isolated backend
  network. Host access remains constrained by the Compose network/loopback boundary.

### Readiness degradation and recovery

The following sequence was executed:

```powershell
docker compose stop redis
docker compose start redis
docker compose stop postgres
docker compose start postgres
docker compose exec -T api alembic -c packages/database/alembic.ini current
docker compose ps
```

HTTP probes were made before, during, and after each dependency interruption.

| State                            | Readiness | Liveness |
| -------------------------------- | --------: | -------: |
| Both dependencies healthy        |       200 |      200 |
| Redis stopped                    |       503 |      200 |
| Redis restarted and healthy      |       200 |      200 |
| PostgreSQL stopped               |       503 |      200 |
| PostgreSQL restarted and healthy |       200 |      200 |

After recovery, Alembic remained at `20260724_0002 (head)`.

### Endpoint matrix

| Endpoint/check                                   | Outcome                                  |
| ------------------------------------------------ | ---------------------------------------- |
| `GET http://localhost:3000/`                     | 200                                      |
| `GET /api/v1/`                                   | 200                                      |
| `GET /health/live`                               | 200                                      |
| `GET /health/ready`                              | 200 with dependencies healthy            |
| `GET /metrics`                                   | 200                                      |
| `GET /docs`                                      | 200 in development                       |
| `GET /openapi.json`                              | 200 in development                       |
| `GET /api/v1/auth/context` without a token       | 401, `authentication_required`           |
| `POST /api/v1/webhooks/stripe` without signature | 400, `missing_webhook_signature`         |
| Unknown API route                                | Structured 404, `not_found`              |
| Local CORS preflight                             | 200 with `http://localhost:3000` allowed |
| API response request IDs                         | Present                                  |

### Container security

- API runs as user `atlas`; web runs as user `nextjs`.
- Application containers are non-privileged, use read-only root filesystems, and set
  `no-new-privileges`.
- API and web images contain no root `.env` or application environment files.
- Application containers have no host bind mounts.
- All services define runtime health checks and `unless-stopped` restart policies.
- API and web runtime bases were refreshed to Python 3.12.13 and Node 22.23.1.
- npm/corepack package-manager tooling was removed from the standalone web runtime.
- Trivy, Grype, and Hadolint were unavailable and are not represented as executed.
- Docker Scout 1.23.1 was available and used.

## Security Advisory Evidence

### GHSA-mh99-v99m-4gvg / CVE-2026-14257

Evidence commands:

```powershell
pnpm audit --prod
pnpm why brace-expansion
pnpm list brace-expansion --recursive
pnpm audit --prod --json
```

Observed dependency path:

```text
packages/eslint-config > eslint > minimatch > brace-expansion@1.1.16
```

The advisory concerns denial of service through unbounded brace expansion. The affected package
is reached by lint tooling, not an Atlas production request path. A forced upgrade to
`brace-expansion` 5.0.8 broke minimatch 3's expected CommonJS API, and an ESLint 10 trial broke the
currently compatible React lint-plugin chain. Neither unsafe change was retained.

Evidence references:

- [GitHub Advisory GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg)
- [CVE-2026-14257 in the NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-14257)
- [Atlas security risk-exception recommendation](security-risk-exceptions.md#ghsa-mh99-v99m-4gvg--cve-2026-14257)

### CVE-2026-12087

Evidence command:

```powershell
docker scout cves atlas-ai-api:latest --only-severity critical --format only-packages
```

Docker Scout found one critical finding in Perl 5.40.1 in the official
`python:3.12.13-slim` base. It reported the affected range as greater than zero and no fixed
version. Atlas starts Uvicorn directly and does not invoke Perl. The API additionally runs
non-root with a read-only root filesystem and `no-new-privileges`.

Evidence references:

- [Docker Scout CVE-2026-12087 record](https://scout.docker.com/v/CVE-2026-12087)
- [CVE-2026-12087 in the NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-12087)
- [Atlas security risk-exception recommendation](security-risk-exceptions.md#cve-2026-12087)

The web critical scan was rerun with:

```powershell
docker scout cves atlas-ai-web:latest --only-severity critical --format only-packages
```

It reported no vulnerable package at critical severity after the runtime refresh and removal of
unused package-manager tooling.

## Non-Container Quality and Infrastructure Gates

| Gate                               | Outcome                  |
| ---------------------------------- | ------------------------ |
| `pnpm install --frozen-lockfile`   | Pass                     |
| `pnpm format:check`                | Pass                     |
| `pnpm lint`                        | Pass                     |
| `pnpm typecheck`                   | Pass                     |
| `pnpm test`                        | Pass: five tests         |
| `pnpm build`                       | Pass: Next.js 16.2.11    |
| Ruff format and lint               | Pass                     |
| Strict mypy                        | Pass: 27 source files    |
| Pytest                             | Pass: 27 tests           |
| Python coverage                    | 87.43%; 80% gate passed  |
| Python production dependency audit | No known vulnerabilities |
| Terraform format/init/validate     | Pass; backend disabled   |
| GitHub workflow YAML parsing       | Pass                     |
| `docker compose config --quiet`    | Pass                     |
| Alembic final revision             | `20260724_0002 (head)`   |
| `git diff --check`                 | Pass                     |

No test made a real external request or used real credentials.

## Repairs Applied During Final Revalidation

- Corrected Redis protected-mode behavior so the API can connect over the isolated Compose backend
  network.
- Refreshed the API runtime from Python 3.12.10 slim to Python 3.12.13 slim.
- Refreshed the web runtime from Node 22.14.0 Alpine to Node 22.23.1 Alpine.
- Removed npm, npx, Corepack, pnpm, pnpx, Yarn, and Yarnpkg tooling from the web runtime image.
- Applied Prettier formatting to the rendered Compose source.
- Added formal, time-bounded security risk-exception recommendations.

## Current Limitations and Required Decisions

1. Both development-only decisions in
   [`docs/security-risk-exceptions.md`](security-risk-exceptions.md) are temporary, must be
   reviewed by 2026-08-27, and expire on 2026-10-27. Neither decision permits production
   promotion.
2. This audit does not approve application-level rate limiting as complete. The documented
   production WAF/ALB and rate-limiting boundary must be implemented and validated before public
   exposure.
3. GitHub deployment environments and required reviewers must be configured before any deployment
   workflow is enabled.
4. A production deployment requires a separate release, security, privacy, compliance, financial
   controls, and operational-readiness review.
5. The approved GHSA-mh99-v99m-4gvg exception includes Milestone 2 development work. This report
   does not validate any Milestone 2 deliverable and grants no production or public-use authority.

## Current Conclusion

**CONDITIONAL PASS — MILESTONE 1 TECHNICAL FOUNDATION ONLY**

All required functional Docker, database, cache, health, endpoint, quality, build, and
infrastructure validation gates completed successfully. The status remains conditional because
both temporary security decisions remain within their approved scope, controls, and validity
period.

**This conditional pass applies only to the Milestone 1 technical foundation. It does not
authorise production deployment, live trading, custody, investment management, or handling real
customer funds.**

---

## Appendix A — Superseded Historical Results

This appendix preserves the audit trail. Every `FAIL` result below predates the successful Docker
revalidation and is superseded by the authoritative Current Status at the beginning of this
report.

### Historical revalidation result on 2026-07-25

Before Docker Desktop was available, the non-container gate passed, but
`docker compose up --detach --build --wait` could not connect to
`npipe:////./pipe/docker_engine`. Redis integration, container builds, and complete readiness
could not be executed. The audit therefore reported **FAIL**.

That result is superseded: Docker Desktop's Linux engine subsequently became available, the clean
Compose build and startup passed, Redis integration passed, degradation/recovery passed, and the
stack was left healthy.

### Historical executive summary

The initial audit found a substantially stabilised repository but withheld a pass because the host
had a Docker CLI without a daemon. Complete Compose startup, image builds, container health, and
real Redis connectivity were unverified. The lint-tool advisory also remained open.

That conclusion is superseded by the current Docker-validated Executive Summary. The lint-tool
advisory remains governed by the linked security recommendation.

### Historical blocked tests

The following tests were originally recorded as blocked:

- Complete Docker Compose startup and container health.
- Redis connectivity.
- API readiness with PostgreSQL and Redis healthy.
- Docker image builds and runtime health checks.

All four items were subsequently executed and passed.

### Historical Docker and Redis failures

Initial Docker command:

```powershell
docker-compose --env-file .env -f docker-compose.yml up --detach --build
```

Historical result: connection to `npipe:////./pipe/docker_engine` failed because no Docker daemon
was running.

Initial Redis package-install attempt:

```powershell
winget install --id Redis.Redis --exact --scope user
```

Historical result: no compatible user-scoped installer was available, so Redis integration could
not be reproduced without Docker.

Both blockers are superseded by the successful Docker Compose validation.

### Historical manual actions

The earlier report required installation of an approved Linux-container Docker daemon, clean
Compose startup, four-service health confirmation, Compose PostgreSQL migration testing, Redis
readiness verification, and image scanning.

Those technical actions are complete. The current outstanding actions are limited to the
decisions and controls listed under Current Limitations and Required Decisions.

### Historical final status

> **FAIL — SUPERSEDED**
>
> The initial status failed because Docker/Redis acceptance criteria were unmet and the
> development dependency advisory remained open.

The Docker/Redis criteria now pass. The authoritative status is **CONDITIONAL PASS** because the
both temporary development-only security decisions remain in force and production remains
prohibited.

## Appendix B — Earlier Audit Repairs and Discoveries

The audit also repaired or documented:

- production configuration validation and fail-closed defaults;
- Clerk authentication and Stripe webhook safety boundaries;
- structured errors, request IDs, trusted hosts, CORS, CSP, and security headers;
- dependency, typing, formatting, Windows build, test-coverage, and CI version drift;
- local credential consistency and ignored environment files;
- database/cache network exposure;
- container non-root execution and health checks;
- database ledger constraints and append-only triggers;
- developer, testing, troubleshooting, security, and release-readiness documentation;
- Terraform validation without apply or cloud mutation.

The exact worktree changes remain available through `git diff` on
`chore/milestone-1-audit`.
