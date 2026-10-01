.PHONY: install lint format typecheck test check up down migrate logs assets

install:
	python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"

lint:
	.venv/bin/ruff check app tests scripts alembic

format:
	.venv/bin/ruff format app tests scripts alembic && .venv/bin/ruff check --fix app tests scripts alembic

typecheck:
	.venv/bin/mypy app

test:
	.venv/bin/pytest -q

check: lint typecheck test

assets:
	.venv/bin/python scripts/generate_assets.py

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	docker compose run --rm migrate

logs:
	docker compose logs -f bot worker
