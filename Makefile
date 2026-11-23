.PHONY: dev db migrate server client test lint types seed install

install:
	cd server && uv sync
	cd client && npm install

db:
	docker compose up -d --wait db

migrate:
	cd server && uv run alembic upgrade head

server:
	cd server && uv run uvicorn app.main:app --reload --port 8000

client:
	cd client && npm run dev

dev: db migrate
	$(MAKE) -j2 server client

test: db
	cd server && TEST_DATABASE_URL=postgresql+asyncpg://haq:haq@localhost:5432/haq_test uv run pytest
	cd client && npm run test

lint:
	cd server && uv run ruff check . && uv run ruff format --check . && uv run mypy app
	cd client && npm run lint && npm run typecheck

types:
	cd server && uv run python -m app.export_openapi ../client/openapi.json
	cd client && npm run types

seed: migrate
	cd server && uv run python -m app.seed
