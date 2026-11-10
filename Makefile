.PHONY: install dev lint format typecheck test

install:
	@echo "Installing backend and frontend dependencies..."
	cd apps/api && uv sync
	cd apps/dashboard && npm install

dev:
	@echo "Starting development servers..."
	@echo "Run 'cd apps/api && uv run uvicorn nammakam_api.main:app --reload' for API"
	@echo "Run 'cd apps/dashboard && npm run dev' for Dashboard"

lint:
	@echo "Running lint checks..."
	cd apps/api && uv run ruff check .

format:
	@echo "Formatting code..."
	cd apps/api && uv run ruff format .

typecheck:
	@echo "Running type checks..."
	cd apps/api && uv run mypy src

test:
	@echo "Running tests..."
	cd apps/api && uv run pytest

