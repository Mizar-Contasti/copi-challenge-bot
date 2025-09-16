# Makefile for Debate Bot API
# Provides commands for development, testing, and deployment

.PHONY: help install test test-verbose lint format clean build run run-dev stop logs deploy health

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"
	@echo "  clean        - Clean up temporary files"
	@echo "  build        - Build Docker image"
	@echo "  run          - Run production container"
	@echo "  run-dev      - Run development container with hot reload"
	@echo "  stop         - Stop all containers"
	@echo "  logs         - Show container logs"
	@echo "  deploy       - Deploy to production"
	@echo "  health       - Check application health"

# Development setup
install:
	pip install -r requirements.txt

# Testing
test:
	python -m pytest tests/ -v --tb=short

test-verbose:
	python -m pytest tests/ -v --tb=long --capture=no

test-coverage:
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
	mypy app/ --ignore-missing-imports

format:
	black app/ tests/ --line-length=100
	isort app/ tests/ --profile=black

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Docker operations
build:
	docker-compose build

run:
	docker-compose up -d debate-bot

run-dev:
	docker-compose --profile dev up -d debate-bot-dev

stop:
	docker-compose down

logs:
	docker-compose logs -f

logs-dev:
	docker-compose logs -f debate-bot-dev

# Deployment
deploy: build
	docker-compose up -d debate-bot
	@echo "Waiting for service to start..."
	@sleep 10
	@make health

# Health check
health:
	@echo "Checking application health..."
	@curl -f http://localhost:8000/health || echo "Health check failed"

health-dev:
	@echo "Checking development application health..."
	@curl -f http://localhost:8001/health || echo "Health check failed"

# Database operations
db-reset:
	rm -f data/debate_bot.db
	@echo "Database reset complete"

# Development helpers
dev-setup: install
	@echo "Setting up development environment..."
	@mkdir -p data
	@echo "Development setup complete"

# Production helpers
prod-setup:
	@echo "Setting up production environment..."
	@mkdir -p data
	@echo "Production setup complete"

# Quick development workflow
dev: clean install test run-dev
	@echo "Development environment ready at http://localhost:8001"
	@echo "API docs available at http://localhost:8001/docs"

# Production deployment workflow
prod: clean test build run
	@echo "Production environment ready at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
