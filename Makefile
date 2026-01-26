.PHONY: help install install-dev test lint format clean run docker-build docker-run

# Default target
help:
	@echo "Personal Agent - Available commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make install-dev  - Install with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linter (ruff)"
	@echo "  make format       - Format code (ruff)"
	@echo "  make typecheck    - Run type checker (mypy)"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make run          - Run the agent CLI"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run in Docker"
	@echo ""

# Installation (using uv for speed)
install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

install-all:
	uv pip install -e ".[all]"

# Sync dependencies from pyproject.toml
sync:
	uv pip sync pyproject.toml

# Create virtual environment
venv:
	uv venv .venv
	@echo "Run 'source .venv/bin/activate' to activate"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Code quality
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

check: lint typecheck test
	@echo "All checks passed!"

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Running
run:
	python -m src.cli

run-legacy:
	python lg_agent_demo.py

# Docker
docker-build:
	docker build -t personal-agent:latest -f docker/Dockerfile .

docker-run:
	docker run -it --rm \
		--env-file .env \
		-v $(PWD)/data:/app/data \
		personal-agent:latest

docker-compose-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-compose-down:
	docker-compose -f docker/docker-compose.yml down

# Development
dev-setup: venv install-dev
	pre-commit install
	@echo "Development environment ready!"

# Database
db-migrate:
	@echo "Database migrations not yet implemented"

# Documentation
docs:
	@echo "Documentation generation not yet implemented"
