.PHONY: install dev test lint build up down

install:
	pnpm install
	python -m pip install -r requirements.txt

dev:
	pnpm dev

test:
	pnpm test
	pytest apps/api/tests

lint:
	pnpm lint
	ruff check apps packages/database
	mypy apps/api/src packages/database/atlas_database

build:
	pnpm build

up:
	docker compose up --build

down:
	docker compose down
