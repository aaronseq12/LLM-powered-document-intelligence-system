# Makefile for LLM Document Intelligence System
# 50+ development & deployment commands for comprehensive project management

.PHONY: help setup install clean test lint format security build deploy monitor logs backup restore

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := llm-document-intelligence
VENV_NAME := venv
NODE := node
NPM := npm

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# ================================
# Help and Information
# ================================

help: ## Show this help message
	@echo "$(CYAN)LLM Document Intelligence System - Makefile Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Command categories:$(RESET)"
	@echo "  $(BLUE)Setup & Installation:$(RESET) setup, install, install-dev, install-frontend"
	@echo "  $(BLUE)Development:$(RESET) dev, dev-backend, dev-frontend, dev-full"
	@echo "  $(BLUE)Testing:$(RESET) test, test-backend, test-frontend, test-coverage"
	@echo "  $(BLUE)Quality:$(RESET) lint, format, security, type-check"
	@echo "  $(BLUE)Building:$(RESET) build, build-backend, build-frontend, build-prod"
	@echo "  $(BLUE)Deployment:$(RESET) deploy, deploy-dev, deploy-staging, deploy-prod"
	@echo "  $(BLUE)Database:$(RESET) db-init, db-migrate, db-upgrade, db-seed"
	@echo "  $(BLUE)Docker:$(RESET) docker-build, docker-run, docker-stop, docker-clean"
	@echo "  $(BLUE)Monitoring:$(RESET) logs, monitor, health-check, metrics"

version: ## Show version information
	@echo "$(CYAN)LLM Document Intelligence System v1.0.0$(RESET)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Node.js: $(shell $(NODE) --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker: $(shell $(DOCKER) --version 2>/dev/null || echo 'Not installed')"

# ================================
# Setup and Installation
# ================================

setup: ## Complete project setup (dependencies, database, etc.)
	@echo "$(GREEN)Setting up LLM Document Intelligence System...$(RESET)"
	$(MAKE) install-backend
	$(MAKE) install-frontend
	$(MAKE) create-env
	$(MAKE) db-setup
	@echo "$(GREEN)Setup completed! Run 'make dev' to start development.$(RESET)"

install: install-backend ## Install all dependencies (alias for install-backend)

install-backend: ## Install Python backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(RESET)"
	$(PYTHON) -m venv $(VENV_NAME)
	./$(VENV_NAME)/bin/pip install --upgrade pip setuptools wheel
	./$(VENV_NAME)/bin/pip install -r requirements.txt
	@echo "$(GREEN)Backend dependencies installed!$(RESET)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	./$(VENV_NAME)/bin/pip install pytest pytest-asyncio pytest-mock black isort flake8 mypy
	@echo "$(GREEN)Development dependencies installed!$(RESET)"

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	cd frontend && $(NPM) install
	@echo "$(GREEN)Frontend dependencies installed!$(RESET)"

create-env: ## Create .env file from template
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Creating .env file from template...$(RESET)"; \
		cp .env.example .env; \
		echo "$(YELLOW)Please update .env file with your configuration$(RESET)"; \
	else \
		echo "$(YELLOW).env file already exists$(RESET)"; \
	fi

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(RESET)"
	./$(VENV_NAME)/bin/pip install --upgrade -r requirements.txt
	cd frontend && $(NPM) update
	@echo "$(GREEN)Dependencies updated!$(RESET)"

# ================================
# Development
# ================================

dev: dev-full ## Start full development environment (alias for dev-full)

dev-backend: ## Start backend development server
	@echo "$(GREEN)Starting backend development server...$(RESET)"
	./$(VENV_NAME)/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start frontend development server
	@echo "$(GREEN)Starting frontend development server...$(RESET)"
	cd frontend && $(NPM) run dev

dev-full: ## Start full development environment (backend + frontend + services)
	@echo "$(GREEN)Starting full development environment...$(RESET)"
	$(DOCKER_COMPOSE) --profile dev up -d postgres redis
	sleep 5
	$(MAKE) db-upgrade
	@echo "$(YELLOW)Starting backend and frontend servers...$(RESET)"
	@echo "$(CYAN)Backend: http://localhost:8000$(RESET)"
	@echo "$(CYAN)Frontend: http://localhost:3000$(RESET)"
	$(DOCKER_COMPOSE) --profile dev up app-dev

dev-services: ## Start development services (database, redis, etc.)
	@echo "$(GREEN)Starting development services...$(RESET)"
	$(DOCKER_COMPOSE) --profile dev up -d postgres redis

stop-dev: ## Stop development environment
	@echo "$(RED)Stopping development environment...$(RESET)"
	$(DOCKER_COMPOSE) --profile dev down

restart-dev: ## Restart development environment
	$(MAKE) stop-dev
	$(MAKE) dev-services
	sleep 5
	$(MAKE) dev-full

# ================================
# Testing
# ================================

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(RESET)"
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(RESET)"
	./$(VENV_NAME)/bin/python -m pytest tests/ -v --tb=short

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(RESET)"
	cd frontend && $(NPM) run test

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	./$(VENV_NAME)/bin/python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yml up --build --abort-on-container-exit
	$(DOCKER_COMPOSE) -f docker-compose.test.yml down

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	./$(VENV_NAME)/bin/python -m pytest tests/ --tb=short -f

test-parallel: ## Run tests in parallel
	@echo "$(BLUE)Running tests in parallel...$(RESET)"
	./$(VENV_NAME)/bin/python -m pytest tests/ -v -n auto

# ================================
# Code Quality
# ================================

lint: ## Run all linting checks
	@echo "$(GREEN)Running linting checks...$(RESET)"
	$(MAKE) lint-backend
	$(MAKE) lint-frontend

lint-backend: ## Lint Python code
	@echo "$(BLUE)Linting backend code...$(RESET)"
	./$(VENV_NAME)/bin/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	./$(VENV_NAME)/bin/flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

lint-frontend: ## Lint TypeScript/React code
	@echo "$(BLUE)Linting frontend code...$(RESET)"
	cd frontend && $(NPM) run lint

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(RESET)"
	./$(VENV_NAME)/bin/black .
	./$(VENV_NAME)/bin/isort .
	cd frontend && $(NPM) run lint:fix

format: ## Format code (backend + frontend)
	@echo "$(GREEN)Formatting code...$(RESET)"
	$(MAKE) format-backend
	$(MAKE) format-frontend

format-backend: ## Format Python code
	@echo "$(BLUE)Formatting backend code...$(RESET)"
	./$(VENV_NAME)/bin/black .
	./$(VENV_NAME)/bin/isort .

format-frontend: ## Format TypeScript/React code
	@echo "$(BLUE)Formatting frontend code...$(RESET)"
	cd frontend && $(NPM) run format

type-check: ## Run type checking
	@echo "$(BLUE)Running type checks...$(RESET)"
	./$(VENV_NAME)/bin/mypy . --ignore-missing-imports
	cd frontend && $(NPM) run type-check

security: ## Run security scans
	@echo "$(GREEN)Running security scans...$(RESET)"
	./$(VENV_NAME)/bin/pip install safety bandit
	./$(VENV_NAME)/bin/safety check
	./$(VENV_NAME)/bin/bandit -r . -f json -o security-report.json
	cd frontend && $(NPM) audit

# ================================
# Building
# ================================

build: ## Build all components
	@echo "$(GREEN)Building all components...$(RESET)"
	$(MAKE) build-backend
	$(MAKE) build-frontend

build-backend: ## Build backend Docker image
	@echo "$(BLUE)Building backend Docker image...$(RESET)"
	$(DOCKER) build -t $(PROJECT_NAME)-backend:latest --target production .

build-frontend: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(RESET)"
	cd frontend && $(NPM) run build

build-dev: ## Build development Docker images
	@echo "$(BLUE)Building development Docker images...$(RESET)"
	$(DOCKER_COMPOSE) --profile dev build

build-prod: ## Build production Docker images
	@echo "$(BLUE)Building production Docker images...$(RESET)"
	$(DOCKER_COMPOSE) build app celery-worker celery-beat

build-clean: ## Clean build artifacts
	@echo "$(RED)Cleaning build artifacts...$(RESET)"
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.cache
	$(DOCKER) system prune -f

# ================================
# Database Management
# ================================

db-setup: ## Setup database and run migrations
	@echo "$(GREEN)Setting up database...$(RESET)"
	$(MAKE) db-init
	$(MAKE) db-upgrade
	$(MAKE) db-seed

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(RESET)"
	./$(VENV_NAME)/bin/python -c "import asyncio; from database import create_tables; asyncio.run(create_tables())"

db-migrate: ## Generate new migration
	@echo "$(BLUE)Generating database migration...$(RESET)"
	./$(VENV_NAME)/bin/alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	./$(VENV_NAME)/bin/alembic upgrade head

db-downgrade: ## Downgrade database by one migration
	@echo "$(RED)Downgrading database...$(RESET)"
	./$(VENV_NAME)/bin/alembic downgrade -1

db-reset: ## Reset database (drop all tables and recreate)
	@echo "$(RED)Resetting database...$(RESET)"
	./$(VENV_NAME)/bin/python -c "import asyncio; from database import drop_tables, create_tables; asyncio.run(drop_tables()); asyncio.run(create_tables())"

db-seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(RESET)"
	./$(VENV_NAME)/bin/python scripts/seed_database.py

db-shell: ## Open database shell
	@echo "$(BLUE)Opening database shell...$(RESET)"
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d document_intelligence

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(RESET)"
	$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres document_intelligence > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from backup
	@echo "$(BLUE)Restoring database...$(RESET)"
	$(DOCKER_COMPOSE) exec -T postgres psql -U postgres document_intelligence < $(file)

# ================================
# Docker Management
# ================================

docker-build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(RESET)"
	$(DOCKER_COMPOSE) build

docker-up: ## Start all services with Docker
	@echo "$(GREEN)Starting all services...$(RESET)"
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop all services
	@echo "$(RED)Stopping all services...$(RESET)"
	$(DOCKER_COMPOSE) down

docker-restart: ## Restart all services
	$(MAKE) docker-down
	$(MAKE) docker-up

docker-logs: ## Show Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-clean: ## Clean Docker system
	@echo "$(RED)Cleaning Docker system...$(RESET)"
	$(DOCKER) system prune -f
	$(DOCKER) volume prune -f
	$(DOCKER) network prune -f

docker-reset: ## Reset Docker environment
	@echo "$(RED)Resetting Docker environment...$(RESET)"
	$(DOCKER_COMPOSE) down -v
	$(DOCKER) system prune -af
	$(MAKE) docker-build

# ================================
# Deployment
# ================================

deploy: deploy-staging ## Deploy to staging (default)

deploy-dev: ## Deploy to development environment
	@echo "$(GREEN)Deploying to development...$(RESET)"
	$(DOCKER_COMPOSE) --profile dev up -d --build

deploy-staging: ## Deploy to staging environment
	@echo "$(GREEN)Deploying to staging...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.staging.yml up -d --build

deploy-prod: ## Deploy to production environment
	@echo "$(GREEN)Deploying to production...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d --build

deploy-rollback: ## Rollback deployment
	@echo "$(RED)Rolling back deployment...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d --no-deps app

# ================================
# Monitoring and Logs
# ================================

logs: ## Show application logs
	$(DOCKER_COMPOSE) logs -f app

logs-all: ## Show logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Show backend logs
	$(DOCKER_COMPOSE) logs -f app celery-worker

logs-db: ## Show database logs
	$(DOCKER_COMPOSE) logs -f postgres

logs-redis: ## Show Redis logs
	$(DOCKER_COMPOSE) logs -f redis

monitor: ## Start monitoring stack
	@echo "$(GREEN)Starting monitoring stack...$(RESET)"
	$(DOCKER_COMPOSE) --profile monitoring up -d prometheus grafana node-exporter

monitor-down: ## Stop monitoring stack
	$(DOCKER_COMPOSE) --profile monitoring down

health-check: ## Check system health
	@echo "$(BLUE)Checking system health...$(RESET)"
	curl -f http://localhost:8000/health || echo "$(RED)Backend health check failed$(RESET)"
	$(DOCKER) ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

metrics: ## Show system metrics
	@echo "$(BLUE)System metrics:$(RESET)"
	$(DOCKER) stats --no-stream

# ================================
# Maintenance
# ================================

clean: ## Clean all build artifacts and caches
	@echo "$(RED)Cleaning project...$(RESET)"
	$(MAKE) clean-python
	$(MAKE) clean-frontend
	$(MAKE) clean-docker

clean-python: ## Clean Python artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache

clean-frontend: ## Clean frontend artifacts
	rm -rf frontend/node_modules/.cache
	rm -rf frontend/dist
	rm -rf frontend/.vite

clean-docker: ## Clean Docker artifacts
	$(DOCKER) system prune -f

backup: ## Create full system backup
	@echo "$(BLUE)Creating system backup...$(RESET)"
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	$(MAKE) db-backup
	$(DOCKER_COMPOSE) exec app tar -czf /tmp/uploads_backup.tar.gz /tmp/uploads
	$(DOCKER) cp $(shell $(DOCKER_COMPOSE) ps -q app):/tmp/uploads_backup.tar.gz backups/$(shell date +%Y%m%d_%H%M%S)/

restore: ## Restore from backup
	@echo "$(BLUE)Restoring from backup...$(RESET)"
	@echo "$(YELLOW)Please specify backup directory: make restore dir=backups/20240101_120000$(RESET)"

# ================================
# Utilities
# ================================

shell: ## Open Python shell in application context
	./$(VENV_NAME)/bin/python -i -c "from main import app; import asyncio"

shell-docker: ## Open shell in Docker container
	$(DOCKER_COMPOSE) exec app bash

redis-cli: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli -a password

download-models: ## Download required ML models
	@echo "$(BLUE)Downloading ML models...$(RESET)"
	./$(VENV_NAME)/bin/python -m spacy download en_core_web_sm

generate-docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	cd docs && make html

serve-docs: ## Serve documentation
	cd docs/_build/html && python -m http.server 8080

update: ## Update project dependencies and rebuild
	$(MAKE) update-deps
	$(MAKE) build
	$(MAKE) test

status: ## Show project status
	@echo "$(CYAN)LLM Document Intelligence System Status$(RESET)"
	@echo "$(GREEN)Services:$(RESET)"
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(GREEN)Health Checks:$(RESET)"
	$(MAKE) health-check

info: ## Show system information
	@echo "$(CYAN)System Information$(RESET)"
	@echo "OS: $(shell uname -s)"
	@echo "Architecture: $(shell uname -m)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Node.js: $(shell $(NODE) --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker: $(shell $(DOCKER) --version 2>/dev/null || echo 'Not installed')"
	@echo "Available Memory: $(shell free -h 2>/dev/null | grep Mem | awk '{print $$2}' || echo 'N/A')"
	@echo "Available Disk: $(shell df -h . | tail -1 | awk '{print $$4}' || echo 'N/A')"

# ================================
# Quick Commands
# ================================

quick-start: ## Quick start for first-time setup
	@echo "$(GREEN)Quick start setup...$(RESET)"
	$(MAKE) setup
	$(MAKE) dev-services
	sleep 10
	@echo "$(CYAN)Setup complete! Access the application at:$(RESET)"
	@echo "$(YELLOW)Backend API: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(RESET)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(RESET)"

quick-reset: ## Quick reset of development environment
	$(MAKE) docker-down
	$(MAKE) clean
	$(MAKE) db-reset
	$(MAKE) docker-up