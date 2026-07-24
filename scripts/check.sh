#!/usr/bin/env sh
set -eu

pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
.venv/bin/python -m ruff format --check apps packages/database
.venv/bin/python -m ruff check apps packages/database
.venv/bin/python -m mypy apps/api/src packages/database/atlas_database
.venv/bin/python -m pytest
