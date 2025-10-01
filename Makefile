.PHONY: help install dev test lint format clean build up down logs shell migrate

# Default target
help:
	@echo "SmartCatcher - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies with UV"
	@echo "  dev         Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  up          Start all services with docker-compose"
	@echo "  down        Stop all services"
	@echo "  logs        Show logs for all services"
	@echo "  shell       Open shell in backend container"
	@echo ""
	@echo "Database:"
	@echo "  migrate     Run database migrations"
	@echo "  reset-db    Reset database (WARNING: destroys data)"
	@echo ""
	@echo "Code Quality:"
	@echo "  test        Run all tests"
	@echo "  test-cov    Run tests with coverage report"
	@echo "  lint        Run linting (ruff)"
	@echo "  format      Format code (black + isort)"
	@echo "  type-check  Run mypy type checking"
	@echo ""
	@echo "Docker:"
	@echo "  build       Build all Docker images"
	@echo "  clean       Clean up Docker resources"

# Installation
install:
	uv sync

dev: install
	uv sync --dev
	pre-commit install

# Development
up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec backend bash

# Database
migrate:
	docker-compose exec backend alembic upgrade head

reset-db:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	docker-compose exec backend alembic upgrade head

# Code quality
test:
	pytest

test-cov:
	pytest --cov=backend --cov=bot --cov=worker --cov-report=html --cov-report=term

lint:
	ruff check .
	mypy backend bot worker

format:
	black .
	isort .
	ruff check --fix .

type-check:
	mypy backend bot worker

# Docker
build:
	docker-compose build --no-cache

clean:
	docker system prune -f
	docker volume prune -f

# Production
prod-up:
	docker-compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Utility
check-env:
	@echo "Checking environment variables..."
	@test -f .env || (echo "Error: .env file not found. Copy .env.example to .env" && exit 1)
	@echo "✅ Environment file found"

setup: check-env dev
	@echo "🚀 Setting up SmartCatcher development environment..."
	@echo "1. Installing dependencies..."
	@make install
	@echo "2. Setting up pre-commit hooks..."
	@pre-commit install
	@echo "3. Starting services..."
	@make up
	@echo "✅ Setup complete! Services are starting up..."
	@echo "   - Backend API: http://localhost:8000"
	@echo "   - API Docs: http://localhost:8000/docs"
	@echo "   - PostgreSQL: localhost:5432"
	@echo "   - Redis: localhost:6379"
