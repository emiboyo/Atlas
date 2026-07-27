# Troubleshooting

## Windows: Corepack cannot create pnpm

If `corepack enable` reports `EPERM` under `C:\Program Files\nodejs`, either use an elevated
terminal or install the pinned pnpm version for the current user:

```powershell
npm install --global pnpm@10.12.1 --prefix "$env:LOCALAPPDATA\pnpm-bin"
$env:Path = "$env:LOCALAPPDATA\pnpm-bin;$env:Path"
pnpm --version
```

Persist the user-level path through Windows Environment Variables before opening a new terminal.

## Windows: symlink permission during Next.js builds

Native builds intentionally use standard Next.js output. The Docker build sets
`NEXT_OUTPUT_MODE=standalone`, where Linux supports the required traced-file links. Do not set that
variable for a native Windows build unless Developer Mode or equivalent symlink privileges are
enabled.

## Docker named-pipe errors

An error mentioning `//./pipe/docker_engine` means the CLI is installed but the Docker daemon is
not running. Start an approved Docker Engine/Desktop installation, wait for it to become healthy,
then run:

```powershell
docker version
docker compose config --quiet
docker compose up --build --wait
```

## Paths containing spaces

Quote absolute paths in PowerShell:

```powershell
Set-Location -LiteralPath "C:\Path With Spaces\Atlas"
```

Prefer running project scripts from the repository root so Python imports, Alembic paths, and
workspace resolution remain stable.

## OneDrive locking and sync conflicts

Do not run the repository from a synced OneDrive folder. Build tools create many temporary files,
hard links, and rename operations that sync clients can lock or duplicate. Use a local path such as
`C:\Dev\Atlas`. If a repository was moved, close editors and development servers first, reopen the
new folder, and recreate virtual environments rather than moving them.

## PostgreSQL or Redis ports are occupied

Set unused host ports in `.env`:

```dotenv
POSTGRES_PORT=55432
REDIS_PORT=56379
```

Container-to-container URLs remain `postgres:5432` and `redis:6379`; only host mappings change.

## Readiness returns 503

Inspect the JSON dependency states, then:

```powershell
docker compose ps
docker compose logs postgres redis api
```

Liveness can remain healthy while readiness is `503`; that is intentional fail-safe behavior.

## Pytest cache access denied

Antivirus, an interrupted process, or a prior elevated run can leave `.pytest_cache` inaccessible.
Close Python processes and remove only that cache directory from an appropriately privileged
terminal. The cache is disposable and ignored by Git.
