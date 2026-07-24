#!/usr/bin/env sh
set -eu

corepack enable
corepack prepare pnpm@10.12.1 --activate
pnpm install
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r apps/api/requirements-dev.txt

echo "Atlas development environment is ready."
