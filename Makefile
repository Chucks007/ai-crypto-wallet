.PHONY: dev api web test fmt lint
API_PORT ?= 8000

dev: ## run backend and frontend in parallel
( cd fastapi && uvicorn app.main:app --reload --host 0.0.0.0 --port $(API_PORT) ) & \
( cd web && npm run dev ) || true

api: ## run backend only
cd fastapi && uvicorn app.main:app --reload --host 0.0.0.0 --port $(API_PORT)

web: ## run frontend only
cd web && npm run dev

test:
cd fastapi && pytest -q

fmt:
cd fastapi && ruff format .

lint:
cd fastapi && ruff check .
