.PHONY: help setup dev stop clean migrate seed docker-up docker-down test lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup
	@bash setup.sh

dev: ## Start development servers
	@echo "Starting backend..."
	@cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	@cd frontend && npm run dev

stop: ## Stop all running services
	@pkill -f "uvicorn app.main" || true
	@pkill -f "vite" || true

clean: ## Clean generated files
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

migrate: ## Run database migrations
	@cd backend && alembic upgrade head

seed: ## Seed database with initial data
	@cd backend && python seed.py

docker-up: ## Start all services with Docker
	@docker-compose up -d

docker-down: ## Stop all Docker services
	@docker-compose down

docker-logs: ## View Docker logs
	@docker-compose logs -f

test: ## Run tests
	@cd backend && pytest -v

lint: ## Run linter
	@cd backend && ruff check .
	@cd backend && ruff format .

install-backend: ## Install backend dependencies
	@cd backend && pip install poetry && poetry install

install-frontend: ## Install frontend dependencies
	@cd frontend && npm install

install: install-backend install-frontend ## Install all dependencies
