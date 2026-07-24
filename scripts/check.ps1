$ErrorActionPreference = "Stop"

pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
& .\.venv\Scripts\python.exe -m ruff format --check apps packages/database
& .\.venv\Scripts\python.exe -m ruff check apps packages/database
& .\.venv\Scripts\python.exe -m mypy apps/api/src packages/database/atlas_database
& .\.venv\Scripts\python.exe -m pytest
