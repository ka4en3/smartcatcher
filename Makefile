# Makefile

.PHONY: help build up down logs shell test lint format clean dev install migration upgrade

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	@echo "Installing dependencies..."
	uv venv
	uv pip install -e ".[dev]"
	pre-commit install

dev: ## Start development environment
	@echo "Starting development environment..."
	docker-compose up --build -d

build: ## Build all Docker images
	@echo "Building Docker images..."
	docker-compose build

up: ## Start all services
	@echo "Starting all services..."
	docker-compose up -d

down: ## Stop all services
	@echo "Stopping all services..."
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-bot: ## Show bot logs
	docker-compose logs -f bot

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-worker: ## Open shell in worker container
	docker-compose exec worker /bin/bash

shell-postgres: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U smartcatcher -d smartcatcher

test: ## Run tests
	@echo "Running tests..."
	pytest --cov=app --cov=bot --cov=worker --cov-report=term-missing

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	pytest tests/ -v --ignore=tests/integration/

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	pytest tests/integration/ -v

coverage: ## Generate coverage report
	@echo "Generating coverage report..."
	pytest --cov=app --cov=bot --cov=worker --cov-report=html
	@echo "Coverage report generated in htmlcov/"

lint: ## Run linters
	@echo "Running linters..."
	ruff check .
	black --check .
	isort --check-only .
	mypy app/ bot/ worker/

format: ## Format code
	@echo "Formatting code..."
	black .
	isort .
	ruff check --fix .

migration: ## Create new migration
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

upgrade: ## Apply migrations
	@echo "Applying migrations..."
	docker-compose exec backend alembic upgrade head

downgrade: ## Rollback last migration
	@echo "Rolling back last migration..."
	docker-compose exec backend alembic downgrade -1

seed: ## Seed database with test data
	@echo "Seeding database..."
	docker-compose exec backend python -m app.seeds.initial_data

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: ## Clean everything including images
	@echo "Cleaning everything..."
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af

restart: ## Restart all services
	@echo "Restarting services..."
	docker-compose restart

restart-backend: ## Restart backend service
	docker-compose restart backend

restart-worker: ## Restart worker service
	docker-compose restart worker

restart-bot: ## Restart bot service
	docker-compose restart bot

healthcheck: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps
	@echo "\nBackend health:"
	@curl -s http://localhost:8000/health || echo "Backend not healthy"
	@echo "\nRedis health:"
	@docker-compose exec redis redis-cli ping || echo "Redis not healthy"
	@echo "\nPostgreSQL health:"
	@docker-compose exec postgres pg_isready -U smartcatcher || echo "PostgreSQL not healthy"

production: ## Deploy to production
	@echo "Deploying to production..."
	@echo "Make sure to set ENVIRONMENT=production in .env"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build