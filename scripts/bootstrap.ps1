$ErrorActionPreference = "Stop"

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    corepack enable
    corepack prepare pnpm@10.12.1 --activate
}

pnpm install
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r apps/api/requirements-dev.txt

Write-Host "Atlas development environment is ready."
